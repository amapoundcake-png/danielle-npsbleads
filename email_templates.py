"""
email_templates.py — Email templates for Danielle Adams outreach sequence.

Personalization rules:
- Always reference a real program, event, partnership, or initiative from the org's notes.
- Never use generic compliments.
- Keep every email under 150 words.
- Write like a human. No sales language, no mention of automation or AI. No em dashes, no double hyphens (--).
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

    subject = f"Partnership strategy for {org}"

    body = (
        f"Hi {first},<br><br>"
        f"{observation}<br><br>"
        f"I'm <strong>Danielle Adams</strong>, a former Senior Director of Strategic Campaigns and Partnerships. "
        f"I work with nonprofits to build the community trust, partnership pipelines, and outreach systems that "
        f"create real, lasting visibility and not just more content.<br><br>"
        f"I'd love to share a few specific ideas for <strong>{org}</strong>. Would a 15-minute conversation make sense?<br><br>"
        f"<a href='{SENDER_CALENDLY}'>Grab a time here.</a><br><br>"
        f"Best,<br>{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body, "is_html": True}


# ---------------------------------------------------------------------------
# Email 2: Follow-up (4-7 days later)
# ---------------------------------------------------------------------------

def build_followup_email(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")

    subject = f"Still thinking about {org}"

    body = (
        f"Hi {first},<br><br>"
        f"I sent a note last week and wanted to follow up with something more concrete.<br><br>"
        f"Most nonprofits I talk to are doing strong programmatic work but losing visibility because their "
        f"outreach systems and partnership pipelines aren't built to scale. That gap is fixable, and it "
        f"doesn't require a bigger team or a bigger budget.<br><br>"
        f"I'd welcome 15 minutes to share what I've seen work for organizations like <strong>{org}</strong>.<br><br>"
        f"<a href='{SENDER_CALENDLY}'>Here's my calendar</a> if that's useful.<br><br>"
        f"Best,<br>{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body, "is_html": True}


# ---------------------------------------------------------------------------
# Email 3: Final check-in (21-30 days later)
# ---------------------------------------------------------------------------

def build_checkin_email(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")

    subject = "Last note from me"

    body = (
        f"Hi {first},<br><br>"
        f"I don't want to keep showing up in your inbox, so this will be my last note.<br><br>"
        f"I genuinely believe <strong>{org}</strong> is doing work that deserves more visibility and stronger "
        f"community partnerships, and that's exactly what I help organizations build.<br><br>"
        f"If the timing is ever right, <a href='{SENDER_CALENDLY}'>my calendar is open</a>. "
        f"No pitch. Just a real conversation about what's working and what could work better.<br><br>"
        f"Wishing you and your team continued success.<br><br>"
        f"Best,<br>{SIGNATURE}"
    )

    return {"to": lead["email"], "subject": subject, "body": body, "is_html": True}
