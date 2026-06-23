"""
email_templates.py — Email templates for Danielle Adams outreach sequence.

Personalization rules:
- Always reference a real program, event, partnership, or initiative from the org's notes.
- Never use generic compliments.
- Keep every email under 150 words.
- Write like a human. No sales language, no mention of automation or AI.
- Focus on visibility, community engagement, partnerships, and organizational growth.
"""

from config import (
    SENDER_NAME,
    SENDER_TITLE,
    SENDER_DISPLAY_EMAIL,
    SENDER_CALENDLY,
    SENDER_LINKEDIN,
)


# ---------------------------------------------------------------------------
# Signature
# ---------------------------------------------------------------------------

SIGNATURE = (
    f"<strong>{SENDER_NAME}</strong><br>"
    f"{SENDER_TITLE}<br>"
    f"{SENDER_DISPLAY_EMAIL}<br>"
    f"<a href='{SENDER_LINKEDIN}'>LinkedIn</a>"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first_name(full_name: str) -> str:
    if not full_name or not full_name.strip():
        return "there"
    return full_name.strip().split()[0]


def _personalized_observation(org: str, notes: str) -> str:
    """
    Build one sentence referencing a real detail about the org.
    Falls back to a neutral line if no notes are available.
    """
    notes = (notes or "").strip().rstrip(".")
    if notes:
        return f"I came across <strong>{org}</strong> and was impressed by {notes.lower()}."
    return f"I came across <strong>{org}</strong> and wanted to reach out directly."


# ---------------------------------------------------------------------------
# Email 1: Initial outreach
# ---------------------------------------------------------------------------

def build_initial_email(lead: dict) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")
    notes = lead.get("notes", "")
    observation = _personalized_observation(org, notes)

    subject = f"Quick idea for {org}"

    body = (
        f"Hi {first},<br><br>"
        f"{observation}<br><br>"
        f"<strong>Danielle Adams</strong> is a former Senior Director of Strategic Campaigns and Partnerships "
        f"who helps nonprofits strengthen community engagement, build strategic partnerships, and increase visibility.<br><br>"
        f"I believe there may be opportunities to support {org}'s outreach goals through stronger engagement "
        f"and relationship-building systems based on the work your team is already doing.<br><br>"
        f"Would you be open to a brief 15-minute conversation?<br><br>"
        f"Here's my calendar: <a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a><br><br>"
        f"Best,<br>{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body, "is_html": True}


# ---------------------------------------------------------------------------
# Email 2: Follow-up (4-7 days later)
# ---------------------------------------------------------------------------

def build_followup_email(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")

    subject = "Following up"

    body = (
        f"Hi {first},<br><br>"
        f"I wanted to follow up on my previous email in case it got buried.<br><br>"
        f"After reviewing <strong>{org}</strong>, I continue to believe there may be opportunities to expand awareness, "
        f"strengthen community engagement, and build on the great work your team is already doing.<br><br>"
        f"I'd be happy to share a few observations specific to your organization and learn more about your current goals.<br><br>"
        f"Would a brief 15-minute conversation make sense?<br><br>"
        f"You can schedule a time here: <a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a><br><br>"
        f"Thank you again for your time and consideration.<br><br>"
        f"Best,<br>{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body, "is_html": True}


# ---------------------------------------------------------------------------
# Email 3: Final check-in (21-30 days later)
# ---------------------------------------------------------------------------

def build_checkin_email(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")

    subject = "Checking back in"

    body = (
        f"Hi {first},<br><br>"
        f"I wanted to circle back one last time regarding <strong>{org}</strong>.<br><br>"
        f"When I reviewed your organization, I identified several opportunities that could potentially support "
        f"your outreach, visibility, partnerships, and community engagement efforts. I know priorities shift "
        f"throughout the year, so I wanted to check in to see if this might be a better time to connect.<br><br>"
        f"If you'd like to exchange ideas and explore whether I can be a resource, I'd be happy to schedule "
        f"a brief conversation.<br><br>"
        f"Here's my calendar: <a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a><br><br>"
        f"Either way, I appreciate the work your organization is doing and wish you continued success.<br><br>"
        f"Best,<br>{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body, "is_html": True}
