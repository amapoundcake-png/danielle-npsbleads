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
    SENDER_CALENDLY,
    SENDER_LINKEDIN,
    GMAIL_ADDRESS,
    NONPROFIT_BODY,
    SMALL_BIZ_BODY,
)

# ---------------------------------------------------------------------------
# Subject line pools
# ---------------------------------------------------------------------------

NONPROFIT_SUBJECTS = [
    "Quick idea for {org}'s donor outreach",
    "Growing {org}'s donor base",
    "{org} -- consistent giving",
    "Donor pipeline for {org}",
]

SMALL_BIZ_SUBJECTS = [
    "Quick idea for {org}'s lead pipeline",
    "Growing {org}'s customer base",
    "{org} -- consistent revenue",
    "Lead pipeline for {org}",
]

GENERIC_SUBJECTS = [
    "Quick idea for {org}'s outreach",
    "Growing {org}'s pipeline",
    "{org} -- consistent growth",
    "Pipeline idea for {org}",
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


def _body_copy(industry: str, org: str) -> str:
    """Return the correct body copy for the lead's industry."""
    industry_lower = (industry or "").lower()
    if any(word in industry_lower for word in ("nonprofit", "non-profit", "charity", "foundation", "association")):
        return NONPROFIT_BODY.format(org=org)
    return SMALL_BIZ_BODY.format(org=org)


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
    f"<strong>{SENDER_NAME}</strong><br>"
    f"{SENDER_TITLE} | {SENDER_LOCATION}<br>"
    f"{GMAIL_ADDRESS}<br>"
    f"<a href='{SENDER_LINKEDIN}'>LinkedIn</a>"
)


# ---------------------------------------------------------------------------
# Initial outreach template
# ---------------------------------------------------------------------------

def _personalized_opener(org: str, notes: str, industry: str) -> str:
    """
    Build a one-sentence personalized opener based on what we know about the org.
    Falls back to a generic line if notes are empty.
    """
    notes = (notes or "").strip()
    industry_lower = (industry or "").lower()
    is_nonprofit = any(w in industry_lower for w in ("nonprofit", "non-profit", "charity", "foundation", "association"))

    if notes and is_nonprofit:
        notes_clean = notes.rstrip(".")
        return f"I came across <strong>{org}</strong> and was really impressed by the work you are doing, {notes_clean.lower()}."
    elif is_nonprofit:
        return f"I came across <strong>{org}</strong> and wanted to reach out directly."
    else:
        return f"I came across <strong>{org}</strong> and wanted to share a quick idea."


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
    notes = lead.get("notes", "")
    body_copy = _body_copy(industry, org)
    subject = _pick_subject(org, industry)
    opener = _personalized_opener(org, notes, industry)

    body = (
        f"Hi {first},<br><br>"
        f"{opener}<br><br>"
        f"{body_copy}<br><br>"
        f"<strong>I'd love to set up 15 minutes.</strong> Here's my calendar: <a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a><br><br>"
        f"Best,<br>{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body, "is_html": True}


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
        f"Hi {first},<br><br>"
        f"Just wanted to follow up in case my last note got buried. "
        f"Totally understand if the timing is not right.<br><br>"
        f"I had a couple of ideas specific to <strong>{org}</strong> that I think could really move the needle "
        f"on your outreach and visibility. Even a <strong>15-minute chat</strong> would be worth it. "
        f"Happy to work around your schedule.<br><br>"
        f"No pressure either way!<br><br>"
        f"Best,<br>{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body, "is_html": True}


# ---------------------------------------------------------------------------
# 30-day check-in template
# ---------------------------------------------------------------------------

def build_checkin_email(lead: dict, original_subject: str) -> dict:
    """
    Build a 30-day check-in email for leads who never replied to either
    the initial outreach or the first follow-up.
    """
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")

    subject = f"Re: {original_subject}"

    body = (
        f"Hi {first},<br><br>"
        f"I reached out about a month ago about supporting <strong>{org}</strong> with communications and outreach. "
        f"Totally understand if the timing was not right then.<br><br>"
        f"Just checking back in. If anything has shifted and you would like to explore "
        f"what this could look like for your organization, I am happy to connect.<br><br>"
        f"<strong>Worth a quick 20 minutes?</strong> Here's my calendar: <a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a><br><br>"
        f"Best,<br>{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body, "is_html": True}


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
