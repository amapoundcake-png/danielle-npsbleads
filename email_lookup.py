"""
email_lookup.py — Find and score contact emails from org websites.

Used by the pipeline send step: after a lead is approved in Notion,
this module scrapes the org's site for the best contact email.

No third-party API required — pure scraping + scoring.
"""

import logging
import re
import time

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Email quality signals
# ---------------------------------------------------------------------------

# Skip these — they bounce or go nowhere useful
SKIP_LOCAL_PARTS = frozenset([
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "webmaster", "postmaster", "hostmaster", "bounce",
    "mailer-daemon", "spam", "abuse", "unsubscribe",
    "newsletter", "news", "list", "subscribe",
])

SKIP_DOMAINS = frozenset([
    "example.com", "test.com", "sentry.io", "wixpress.com",
    "squarespace.com", "weebly.com", "wordpress.com",
])

# These local parts score lower (generic) but are still usable
GENERIC_LOCAL_PARTS = frozenset([
    "info", "contact", "hello", "admin", "support",
    "mail", "office", "general", "inquiries", "inquiry",
    "help", "team", "service", "services",
])

# Nearby text signals that the email belongs to a decision-maker
LEADERSHIP_KEYWORDS = [
    "director", "executive", "president", "ceo", "founder", "coo", "cmo",
    "manager", "coordinator", "officer", "head", "chief", "lead",
    "development", "communications", "outreach", "programs", "community",
    "partnership", "partnerships", "engagement", "relations",
]

# Pages most likely to have contact emails, in priority order
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/about/contact",
    "/about",
    "/about-us",
    "/staff",
    "/our-team",
    "/team",
    "/leadership",
    "/people",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)


def _extract_emails(text: str) -> list[str]:
    """Pull all email-shaped strings from text, deduplicated."""
    found = EMAIL_REGEX.findall(text)
    seen = set()
    out = []
    for e in found:
        e = e.lower().strip().rstrip(".")
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def _is_usable(email: str) -> bool:
    """Return False for emails we should never send to."""
    local, _, domain = email.partition("@")
    if not domain:
        return False
    if local in SKIP_LOCAL_PARTS:
        return False
    if domain in SKIP_DOMAINS:
        return False
    # Must have a real TLD
    parts = domain.split(".")
    if len(parts) < 2 or len(parts[-1]) < 2:
        return False
    return True


def _score_email(email: str, surrounding_text: str = "") -> int:
    """
    Score an email candidate 0-10.
    Higher = more likely to be a real decision-maker contact.
    """
    local = email.split("@")[0].lower()
    ctx = surrounding_text.lower()
    score = 5  # baseline

    # Personal name pattern (first.last) → very good
    if re.match(r"^[a-z]+\.[a-z]{2,}$", local):
        score += 3

    # First name only → decent
    elif re.match(r"^[a-z]{3,}$", local) and local not in GENERIC_LOCAL_PARTS:
        score += 1

    # Generic → penalize
    if local in GENERIC_LOCAL_PARTS:
        score -= 2

    # Leadership keywords nearby → good context
    for kw in LEADERSHIP_KEYWORDS:
        if kw in ctx:
            score += 1
            break

    return max(0, score)


def _fetch_page_text(url: str) -> str:
    """Fetch a page and return visible text. Returns '' on failure."""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        if not resp.ok:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        # Also decode mailto: links which often escape regex
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("mailto:"):
                email_part = href[7:].split("?")[0].strip()
                if email_part:
                    # Inject into text so the extractor finds it
                    soup.append(BeautifulSoup(f" {email_part} ", "html.parser"))
        return soup.get_text(separator=" ", strip=True)
    except Exception as exc:
        logger.debug("Page fetch failed for %s: %s", url, exc)
        return ""


# ---------------------------------------------------------------------------
# Main lookup function
# ---------------------------------------------------------------------------

def find_contact_email(
    domain: str,
    page_texts: list[str] = None,
) -> tuple[str, str]:
    """
    Find the best contact email for an org given its domain.

    Args:
        domain:     e.g. "orlandoyouthalliance.org"
        page_texts: already-fetched page texts from discover step (optional)

    Returns:
        (email, source_description) — both empty strings if not found.
    """
    domain = domain.lower().strip().lstrip("www.")
    candidates: list[tuple[int, str, str]] = []  # (score, email, source)

    # 1. Mine already-fetched page texts
    if page_texts:
        for text in page_texts:
            for e in _extract_emails(text):
                if _is_usable(e) and domain.split(".")[0] not in e.split("@")[0]:
                    # Get surrounding context (200 chars around email)
                    idx = text.lower().find(e)
                    ctx = text[max(0, idx - 200): idx + 200] if idx >= 0 else ""
                    candidates.append((_score_email(e, ctx), e, f"{domain} (cached)"))

    # 2. Scrape contact/about/staff pages
    for path in CONTACT_PATHS:
        url = f"https://{domain}{path}"
        text = _fetch_page_text(url)
        if not text:
            time.sleep(0.5)
            continue

        found = _extract_emails(text)
        if found:
            logger.debug("Found %d email(s) at %s", len(found), url)
            for e in found:
                if not _is_usable(e):
                    continue
                # Skip emails from unrelated domains (e.g. partner links)
                e_domain = e.split("@")[1]
                if e_domain != domain and not domain.endswith("." + e_domain):
                    continue
                idx = text.lower().find(e)
                ctx = text[max(0, idx - 200): idx + 200] if idx >= 0 else ""
                candidates.append((_score_email(e, ctx), e, url))

        time.sleep(1)

        # Stop if we have a high-confidence candidate
        if candidates and max(c[0] for c in candidates) >= 8:
            break

    if not candidates:
        logger.info("No contact email found for %s", domain)
        return "", ""

    # Pick the highest-scoring candidate
    candidates.sort(key=lambda x: -x[0])
    best_score, best_email, best_source = candidates[0]

    logger.info(
        "Email found for %s: %s (score=%d, source=%s)",
        domain, best_email, best_score, best_source,
    )
    return best_email, best_source
