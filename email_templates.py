"""
email_templates.py — Profile-based email templates for Danni Adams outreach.

Profiles: warmup | nonprofit | speaker | brand | talent
"""

import random
from config import (
    SENDER_NAME,
    SENDER_EMAIL_HELLO,
    SENDER_EMAIL_SPEAKING,
    SENDER_EMAIL_PARTNERSHIPS,
    SENDER_CALENDLY,
    SENDER_INSTAGRAM,
    NONPROFIT_SUBJECTS, NONPROFIT_BODY,
    SPEAKER_SUBJECTS, SPEAKER_BODY,
    BRAND_SUBJECTS, BRAND_BODY,
    TALENT_SUBJECTS, TALENT_BODY,
    WARMUP_BODY,
)


def _first_name(full_name: str) -> str:
    if not full_name or not full_name.strip():
        return "there"
    return full_name.strip().split()[0]


def _signature(profile: str) -> str:
    if profile == "nonprofit":
        email = SENDER_EMAIL_HELLO
        return (
            f"<strong>{SENDER_NAME}</strong><br>"
            f"{email}"
        )
    elif profile == "speaker":
        email = SENDER_EMAIL_SPEAKING
    elif profile in ("brand", "talent"):
        email = SENDER_EMAIL_PARTNERSHIPS
    else:
        email = SENDER_EMAIL_HELLO

    return (
        f"<strong>{SENDER_NAME}</strong><br>"
        f"{email}<br>"
        f"<a href='{SENDER_INSTAGRAM}'>@amapoundcake</a>"
    )


def build_warmup_email(to_address: str) -> dict:
    subject = "New email, heads up"
    body = (
        f"Hey,<br><br>"
        f"{WARMUP_BODY.replace(chr(10), '<br>')}<br><br>"
        f"{_signature('warmup')}"
    )
    return {"to": to_address, "subject": subject, "body": body, "profile": "warmup", "is_html": True}


def build_initial_email(lead: dict) -> dict:
    profile = lead.get("profile", "nonprofit")
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")

    if profile == "nonprofit":
        subject = random.choice(NONPROFIT_SUBJECTS).format(org=org)
        body_copy = NONPROFIT_BODY.format(org=org, calendly=SENDER_CALENDLY)
        cta = ""
    elif profile == "speaker":
        subject = random.choice(SPEAKER_SUBJECTS).format(org=org)
        body_copy = SPEAKER_BODY.format(org=org)
        cta = f"Worth a quick conversation? Here's my calendar: <a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a>"
    elif profile == "brand":
        subject = random.choice(BRAND_SUBJECTS).format(org=org)
        body_copy = BRAND_BODY.format(org=org)
        cta = f"It's a quick conversation. Here's my calendar: <a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a>"
    elif profile == "talent":
        subject = random.choice(TALENT_SUBJECTS).format(org=org)
        body_copy = TALENT_BODY.format(org=org)
        cta = f"Happy to send my full reel and resume. Here's my calendar if it's easier: <a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a>"
    else:
        subject = f"Reaching out about {org}"
        body_copy = NONPROFIT_BODY.format(org=org)
        cta = f"Worth a 20-minute call? <a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a>"

    greeting = f"Hi {first}," if first != "there" else "Hi,"

    cta_block = f"{cta}<br><br>" if cta else ""
    body = (
        f"{greeting}<br><br>"
        f"{body_copy}<br><br>"
        f"{cta_block}"
        f"{_signature(profile)}"
    )

    return {
        "to": lead["email"],
        "subject": subject,
        "body": body,
        "profile": profile,
        "is_html": True,
    }


def build_followup_email(lead: dict, original_subject: str) -> dict:
    profile = lead.get("profile", "nonprofit")
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")
    greeting = f"Hi {first}," if first != "there" else "Hi,"

    if profile == "nonprofit":
        followup_note = (
            f"Just following up in case my last note got buried.<br><br>"
            f"I had a few specific ideas for <strong>{org}</strong> around outreach and visibility that I'd love to share. "
            f"Even a <strong>15-minute call</strong> would be worth it. I can show you exactly what I'm thinking.<br><br>"
            f"Happy to work around your schedule. No pressure either way."
        )
    else:
        followup_note = (
            f"Just wanted to follow up in case my last note got buried.<br><br>"
            f"I had a few specific ideas for <strong>{org}</strong> I'd still love to share. "
            f"Even a <strong>15-minute call</strong> would be worth it. "
            f"Happy to work around your schedule.<br><br>"
            f"No pressure either way."
        )

    body = (
        f"{greeting}<br><br>"
        f"{followup_note}<br><br>"
        f"{_signature(profile)}"
    )

    return {
        "to": lead["email"],
        "subject": f"Re: {original_subject}",
        "body": body,
        "profile": profile,
        "is_html": True,
    }


def build_checkin_email(lead: dict, original_subject: str) -> dict:
    profile = lead.get("profile", "nonprofit")
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")
    greeting = f"Hi {first}," if first != "there" else "Hi,"

    body = (
        f"{greeting}<br><br>"
        f"I reached out about a month ago about <strong>{org}</strong>. "
        f"Totally understand if the timing was not right then.<br><br>"
        f"Just checking back in. If anything has shifted and you'd like to connect, "
        f"I'm here.<br><br>"
        f"<a href='{SENDER_CALENDLY}'>{SENDER_CALENDLY}</a><br><br>"
        f"{_signature(profile)}"
    )

    return {
        "to": lead["email"],
        "subject": f"Re: {original_subject}",
        "body": body,
        "profile": profile,
        "is_html": True,
    }
