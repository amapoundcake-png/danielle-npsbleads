"""
email_templates.py — Profile-based email templates for Danni Adams outreach.

Profiles: warmup | nonprofit | speaker | creator | brand | talent
"""

import random
from datetime import datetime, timezone, timedelta

EASTERN = timezone(timedelta(hours=-4))


def _nonprofit_cta() -> str:
    """Return a day-appropriate call-to-action for nonprofit emails."""
    day = datetime.now(tz=timezone.utc).astimezone(EASTERN).weekday()
    # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    if day in (3, 4, 5, 6):  # Thu/Fri/Sat/Sun -- suggest next week
        return "Do you have any availability next week for a quick call? I can work around your schedule."
    else:  # Mon/Tue/Wed -- suggest later this week
        return "Do you have any availability later this week for a quick call? I can work around your schedule."


from config import (
    SENDER_NAME,
    SENDER_EMAIL_HELLO,
    SENDER_EMAIL_SPEAKING,
    SENDER_EMAIL_PARTNERSHIPS,
    SENDER_CALENDLY,
    SENDER_INSTAGRAM,
    SENDER_LINKEDIN,
    NONPROFIT_SUBJECTS, NONPROFIT_BODY,
    POLITICAL_SUBJECTS, POLITICAL_BODY,
    SPEAKER_SUBJECTS, SPEAKER_BODY,
    CREATOR_SUBJECTS, CREATOR_BODY,
    BRAND_SUBJECTS, BRAND_BODY,
    TALENT_SUBJECTS, TALENT_BODY,
    WARMUP_BODY,
)


def _first_name(full_name: str) -> str:
    if not full_name or not full_name.strip():
        return "there"
    return full_name.strip().split()[0]


def _signature(profile: str) -> str:
    linkedin = f"<a href='{SENDER_LINKEDIN}'>LinkedIn</a>" if SENDER_LINKEDIN else ""

    if profile in ("nonprofit", "political"):
        # Consulting context — professional, no Instagram
        parts = [f"<strong>{SENDER_NAME}</strong>", SENDER_EMAIL_HELLO]
        if linkedin:
            parts.append(linkedin)
        return "<br>".join(parts)

    elif profile in ("speaker", "creator"):
        # Speaker context — professional, no Instagram
        parts = [f"<strong>{SENDER_NAME}</strong>", SENDER_EMAIL_SPEAKING]
        if linkedin:
            parts.append(linkedin)
        return "<br>".join(parts)

    elif profile in ("brand", "talent"):
        # Brand/talent — clean signature, @amapoundcake handle already in email body
        parts = [f"<strong>{SENDER_NAME}</strong>", "@amapoundcake", SENDER_EMAIL_PARTNERSHIPS]
        if linkedin:
            parts.append(linkedin)
        return "<br>".join(parts)

    else:
        return f"<strong>{SENDER_NAME}</strong><br>{SENDER_EMAIL_HELLO}"


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
        body_copy = NONPROFIT_BODY.format(org=org, cta=_nonprofit_cta())
        cta = ""
    elif profile == "political":
        subject = random.choice(POLITICAL_SUBJECTS).format(org=org)
        body_copy = POLITICAL_BODY.format(org=org, cta=_nonprofit_cta())
        cta = ""
    elif profile == "speaker":
        subject = random.choice(SPEAKER_SUBJECTS).format(org=org)
        body_copy = SPEAKER_BODY.format(org=org)
        cta = ""
    elif profile == "creator":
        subject = random.choice(CREATOR_SUBJECTS).format(org=org)
        body_copy = CREATOR_BODY.format(org=org)
        cta = "Worth a quick conversation? Just reply and we can go from there."
    elif profile == "brand":
        subject = random.choice(BRAND_SUBJECTS).format(org=org)
        # Pull personalization reason from notes field
        notes = lead.get("notes", "").strip()
        industry = lead.get("industry", "").strip()
        # Use notes to build a specific reason; fall back to industry
        reason_text = notes.split("-")[0].strip() if notes else industry
        if reason_text and len(reason_text) > 5:
            reason = f", particularly given your {reason_text.lower()} audience and presence"
        else:
            reason = ""
        body_copy = BRAND_BODY.format(org=org, reason=reason)
        cta = ""
    elif profile == "talent":
        subject = random.choice(TALENT_SUBJECTS).format(org=org)
        body_copy = TALENT_BODY.format(org=org)
        cta = "Happy to send my full reel and resume. Just reply here."
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
    elif profile == "brand":
        followup_note = (
            f"Just wanted to circle back on my note below.<br><br>"
            f"I'd still love to explore whether an Orlando creator experience could make sense "
            f"for <strong>{org}</strong> this holiday season.<br><br>"
            f"If Q4 activations are handled by someone else on your team, I'd appreciate being "
            f"pointed in the right direction."
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

    reconnect = "Just checking back in. If anything has shifted and you'd like to connect, just reply here."

    body = (
        f"{greeting}<br><br>"
        f"I reached out about a month ago about <strong>{org}</strong>. "
        f"Totally understand if the timing was not right then.<br><br>"
        f"{reconnect}<br><br>"
        f"{_signature(profile)}"
    )

    return {
        "to": lead["email"],
        "subject": f"Re: {original_subject}",
        "body": body,
        "profile": profile,
        "is_html": True,
    }
