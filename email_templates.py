"""
email_templates.py — Template-based email personalization.

Templates are used for initial outreach and follow-up emails.
A commented stub at the bottom shows how to swap in Claude API for
AI-generated personalization once an Anthropic API key is available.
"""

import random
import os
from config import (
    SENDER_NAME,
    SENDER_TITLE,
    SENDER_LOCATION,
    SENDER_LINKEDIN,
    SENDER_WEBSITE,
    GMAIL_ADDRESS,
    NONPROFIT_SERVICES_BLURB,
    SMALL_BIZ_SERVICES_BLURB,
    SERVICES_BLURB,
)

# ---------------------------------------------------------------------------
# Subject line pools
# ---------------------------------------------------------------------------

NONPROFIT_SUBJECTS = [
    "Quick idea for {org}'s outreach",
    "Marketing automation for nonprofits in Orlando",
    "Helping {org} reach more people",
    "A thought on {org}'s campaigns",
    "Campaign operations support for {org}",
]

SMALL_BIZ_SUBJECTS = [
    "Quick idea for {org}",
    "Marketing automation for Orlando businesses",
    "Helping {org} grow through smarter campaigns",
    "A thought on {org}'s marketing",
    "Campaign strategy for {org}",
]

GENERIC_SUBJECTS = [
    "Quick idea for {org}",
    "Marketing support for {org}",
    "Connecting with {org}",
    "A thought on {org}'s outreach",
    "Campaign strategy for {org}",
]


def _pick_subject(org: str, industry: str) -> str:
    """Return a randomized subject line appropriate for the lead's industry."""
    industry_lower = (industry or "").lower()
    if any(word in industry_lower for word in ("nonprofit", "non-profit", "charity", "foundation", "association")):
        pool = NONPROFIT_SUBJECTS
    elif any(word in industry_lower for word in ("business", "retail", "restaurant", "service", "tech", "agency")):
        pool = SMALL_BIZ_SUBJECTS
    else:
        pool = GENERIC_SUBJECTS
    return random.choice(pool).format(org=org)


def _services_blurb(industry: str) -> str:
    """Return the most appropriate services blurb for the lead."""
    industry_lower = (industry or "").lower()
    if any(word in industry_lower for word in ("nonprofit", "non-profit", "charity", "foundation", "association")):
        return NONPROFIT_SERVICES_BLURB
    elif any(word in industry_lower for word in ("business", "retail", "restaurant", "service", "tech", "agency")):
        return SMALL_BIZ_SERVICES_BLURB
    return SERVICES_BLURB


def _first_name(full_name: str) -> str:
    """Extract first name, falling back to 'there' if blank."""
    if not full_name or not full_name.strip():
        return "there"
    return full_name.strip().split()[0]


def _org_type_label(industry: str) -> str:
    """Return 'nonprofit' or 'business' for use in body copy."""
    industry_lower = (industry or "").lower()
    if any(word in industry_lower for word in ("nonprofit", "non-profit", "charity", "foundation", "association")):
        return "nonprofit"
    return "business"


# ---------------------------------------------------------------------------
# Signature block
# ---------------------------------------------------------------------------

SIGNATURE = (
    f"--\n"
    f"{SENDER_NAME}\n"
    f"{SENDER_TITLE} | {SENDER_LOCATION}\n"
    f"{GMAIL_ADDRESS}\n"
    f"LinkedIn: {SENDER_LINKEDIN}\n"
    f"Web: {SENDER_WEBSITE}"
)


# ---------------------------------------------------------------------------
# Initial outreach template
# ---------------------------------------------------------------------------

def build_initial_email(lead: dict) -> dict:
    """
    Build the initial outreach email for a lead.

    Args:
        lead: dict with keys — name, org, email, industry, notes (optional)

    Returns:
        dict with keys — to, subject, body
    """
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")
    industry = lead.get("industry", "")
    org_type = _org_type_label(industry)
    blurb = _services_blurb(industry)

    # Build one contextual observation from available metadata.
    notes = (lead.get("notes") or "").strip()
    if notes:
        observation = notes
    else:
        observation = f"I came across {org} while researching Orlando {org_type}s"

    subject = _pick_subject(org, industry)

    body = (
        f"Hi {first},\n\n"
        f"{observation}. Really interesting work you're doing.\n\n"
        f"I'm a marketing and campaign operations consultant based in Orlando. "
        f"{blurb}\n\n"
        f"Would it make sense to connect for a quick 20-minute call? "
        f"I'd love to share a few specific ideas for {org}. No pitch, just a conversation.\n\n"
        f"Best,\n{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body}


# ---------------------------------------------------------------------------
# Follow-up template
# ---------------------------------------------------------------------------

def build_followup_email(lead: dict, original_subject: str) -> dict:
    """
    Build a soft follow-up email (sent 4-6 days after initial outreach).

    Args:
        lead: same lead dict
        original_subject: the subject used in the first email

    Returns:
        dict with keys — to, subject, body
    """
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")

    subject = f"Re: {original_subject}"

    body = (
        f"Hi {first},\n\n"
        f"Just wanted to follow up in case my last note got buried. "
        f"Totally understand if the timing isn't right.\n\n"
        f"I had a couple of ideas specific to {org} that I think could save your team "
        f"real time on the marketing side. Even a 15-minute chat would be worth it. "
        f"Happy to work around your schedule.\n\n"
        f"No pressure either way!\n\n"
        f"Best,\n{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body}


# ---------------------------------------------------------------------------
# Stub: AI-personalized emails via Claude API
# ---------------------------------------------------------------------------
# To activate, set ANTHROPIC_API_KEY in .env and uncomment the block below.
# Replace calls to build_initial_email() / build_followup_email() in main.py
# with calls to build_initial_email_ai() / build_followup_email_ai().
#
# import anthropic
#
# def build_initial_email_ai(lead: dict) -> dict:
#     """Generate a highly personalized cold email using Claude."""
#     client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
#     first = _first_name(lead.get("name", ""))
#     org = lead.get("org", "the organization")
#     industry = lead.get("industry", "")
#     notes = lead.get("notes", "")
#     blurb = _services_blurb(industry)
#
#     prompt = (
#         f"Write a short, warm cold outreach email from {SENDER_NAME}, a marketing "
#         f"consultant in Orlando, to {first} at {org} ({industry}). "
#         f"Context about the org: {notes}. "
#         f"Services offered: {blurb}. "
#         f"Keep it to 3-4 sentences. End with a soft CTA for a 20-minute call. "
#         f"Do NOT use hollow phrases like 'I hope this finds you well'. "
#         f"Return ONLY the email body text — no subject line, no sign-off."
#     )
#
#     message = client.messages.create(
#         model="claude-opus-4-5",
#         max_tokens=300,
#         messages=[{"role": "user", "content": prompt}],
#     )
#     ai_body = message.content[0].text.strip()
#     subject = _pick_subject(org, industry)
#     body = f"Hi {first},\n\n{ai_body}\n\nBest,\n{SIGNATURE}"
#     return {"to": lead["email"], "subject": subject, "body": body}
