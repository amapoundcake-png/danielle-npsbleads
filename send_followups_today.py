"""
One-time send: follow-up emails to all 60 engaged contacts from the
Brevo Aug 19 - Sep 10 campaign.

Source: full_followup_list artifact (333e148a-5936-4f89-916e-7f5ed687444b)
All em dashes and double dashes stripped before sending.
Calendly link active and direct (no Brevo click-tracking redirect).

Usage:
  DRY_RUN=true  python send_followups_today.py   # preview, no sends
  DRY_RUN=false python send_followups_today.py   # live send
"""

import os
import re
import sys
import time
import random
import logging
from html.parser import HTMLParser

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("followup_send")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ARTIFACT_HTML = os.path.join(
    os.path.dirname(__file__),
    "followup_contacts.html",
)
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() not in ("false", "0", "no")

SENDER_MAP = {
    "hello@danniadams.me":        ("Danielle Adams", "hello@danniadams.me"),
    "speaking@danniadams.me":     ("Danni Adams",    "speaking@danniadams.me"),
    "partnerships@danniadams.me": ("Danni Adams",    "partnerships@danniadams.me"),
}

# ---------------------------------------------------------------------------
# Em-dash / double-dash cleaner
# ---------------------------------------------------------------------------
def _clean_dashes(text: str) -> str:
    """Remove em dashes and double dashes. Context-aware replacements."""
    # Double dash first
    text = re.sub(r"\s*--\s*", ", ", text)
    # Em dash before coordinating conjunctions / pronouns / prepositions
    # -> replace with comma + space
    text = re.sub(
        r"\s*—\s*"
        r"(and|but|or|so|not|because|with|that|this|in|it|I|she|he|they|we|the|a|an)\b",
        r", \1",
        text,
    )
    # Em dash in subject lines: "Following up — Org Name" -> "Following up: Org Name"
    text = re.sub(r"\s*—\s*", ": ", text)
    return text


def _clean_html_body(html: str) -> str:
    """Strip em dashes from HTML body, preserving tags."""
    # Unescape HTML entities we might have picked up
    html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return _clean_dashes(html)


# ---------------------------------------------------------------------------
# Parse artifact HTML -> list of contact dicts
# ---------------------------------------------------------------------------
def parse_contacts(html: str) -> list[dict]:
    card_blocks = re.findall(
        r'<div class="card"[^>]*>.*?(?=<div class="card"|<script|\Z)',
        html,
        re.DOTALL,
    )

    contacts = []
    for block in card_blocks:
        org_m = re.search(r'<div class="org">([^<]+)', block)
        to_m  = re.search(r'<div class="email-addr">([^<]+)', block)
        metas = re.findall(r'<div class="meta-item"><span>([^<]+)</span>([^<]+)', block)
        body_m = re.search(
            r'<div class="email-block">(.*?)</div>\s*</div>\s*</div>',
            block, re.DOTALL,
        )

        meta = {k.strip().lower(): v.strip() for k, v in metas}

        if not (org_m and to_m and body_m):
            continue

        raw_body  = body_m.group(1).strip()
        # Convert newlines in body to <br> for HTML email, keep existing <a> tags
        html_body = _clean_html_body(raw_body).replace("\n", "<br>")

        contacts.append({
            "org":     org_m.group(1).strip().replace("&amp;", "&"),
            "to":      to_m.group(1).strip(),
            "from":    meta.get("send from", "hello@danniadams.me"),
            "subject": _clean_dashes(meta.get("subject", "Following up")),
            "body":    html_body,
        })

    return contacts


# ---------------------------------------------------------------------------
# Brevo send
# ---------------------------------------------------------------------------
def send_via_brevo(contact: dict) -> bool:
    from_addr = contact["from"]
    sender_name, sender_email = SENDER_MAP.get(from_addr, ("Danni Adams", from_addr))

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to":     [{"email": contact["to"]}],
        "subject": contact["subject"],
        "htmlContent": (
            f"<html><body style='font-family:Arial,sans-serif;font-size:14px;"
            f"line-height:1.6;color:#1a1a1a;max-width:600px'>"
            f"{contact['body']}"
            f"</body></html>"
        ),
        # No trackClicks, no trackOpens — prevents broken Calendly redirect
        "headers": {"X-Mailin-custom": "followup-batch-sep12"},
    }

    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        json=payload,
        headers={
            "api-key":      BREVO_API_KEY,
            "Content-Type": "application/json",
        },
        timeout=15,
    )

    if resp.status_code in (200, 201):
        logger.info("SENT     %-50s  -> %s", contact["org"][:50], contact["to"])
        return True
    else:
        logger.error(
            "FAILED   %-50s  -> %s  [%s] %s",
            contact["org"][:50], contact["to"],
            resp.status_code, resp.text[:200],
        )
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not os.path.exists(ARTIFACT_HTML):
        logger.error("Contact file not found: %s", ARTIFACT_HTML)
        logger.error("Run: python extract_contacts.py  first.")
        sys.exit(1)

    if not DRY_RUN and not BREVO_API_KEY:
        logger.error("BREVO_API_KEY not set. Cannot send.")
        sys.exit(1)

    with open(ARTIFACT_HTML) as f:
        html = f.read()

    all_contacts = parse_contacts(html)
    # Deduplicate by recipient email — keep first occurrence
    seen_emails: set[str] = set()
    contacts = []
    for c in all_contacts:
        if c["to"] not in seen_emails:
            seen_emails.add(c["to"])
            contacts.append(c)
    logger.info("Loaded %d contacts (%d dupes removed)", len(contacts), len(all_contacts) - len(contacts))

    if DRY_RUN:
        logger.info("=== DRY RUN — no emails will be sent ===")
        for i, c in enumerate(contacts, 1):
            logger.info(
                "[%2d] %-45s  from: %-30s  to: %s",
                i, c["org"][:45], c["from"], c["to"],
            )
            logger.info("     Subject: %s", c["subject"])
        logger.info("Set DRY_RUN=false to send.")
        return

    logger.info("=== LIVE SEND — %d emails ===", len(contacts))
    sent = failed = 0
    for c in contacts:
        ok = send_via_brevo(c)
        if ok:
            sent += 1
        else:
            failed += 1
        # Random delay 30-90 s (warm-up best practice)
        delay = random.randint(30, 90)
        logger.info("Waiting %ds before next send...", delay)
        time.sleep(delay)

    logger.info("=== DONE — sent: %d  failed: %d ===", sent, failed)


if __name__ == "__main__":
    main()
