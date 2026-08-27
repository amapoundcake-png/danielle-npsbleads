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
    NONPROFIT_SPEAKER_SUBJECTS, NONPROFIT_SPEAKER_BODY,
    POLITICAL_SUBJECTS, POLITICAL_BODY,
    SPEAKER_SUBJECTS, SPEAKER_BODY,
    CREATOR_SUBJECTS, CREATOR_BODY,
    BRAND_SUBJECTS, BRAND_BODY,
    TALENT_SUBJECTS, TALENT_BODY,
    VENUE_HOST_SUBJECTS, VENUE_HOST_BODY,
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

    elif profile in ("nonprofit_speaker", "speaker", "creator"):
        # Speaker context — professional, no Instagram
        parts = [f"<strong>{SENDER_NAME}</strong>", SENDER_EMAIL_SPEAKING]
        if linkedin:
            parts.append(linkedin)
        return "<br>".join(parts)

    elif profile in ("brand", "talent", "venue_host"):
        # Brand/talent/venue — clean signature, @amapoundcake handle already in email body
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
    elif profile == "nonprofit_speaker":
        subject = random.choice(NONPROFIT_SPEAKER_SUBJECTS).format(org=org)
        notes = (lead.get("notes", "") or "").lower()
        industry = (lead.get("industry", "") or "").lower()
        combined = notes + " " + industry
        # Personalize opening hook based on org mission
        if any(w in combined for w in ("shelter", "domestic", "survivor", "violence", "refuge")):
            hook = (
                "I have done ongoing work with women's shelters on resilience and confidence — "
                "helping women find their voice again after hard seasons, and I would love to bring that work to "
                f"<strong>{org}</strong> and the women you serve."
            )
        elif any(w in combined for w in ("youth", "teen", "girl", "mentor", "student", "after school", "kids")):
            hook = (
                "With Meta just ordered to pay an $18 billion settlement over the harm their platforms caused to young people, "
                "this conversation has never been more urgent. I work with youth organizations on sessions covering "
                "<strong>social media, digital safety, and self-esteem</strong> — helping young people understand "
                "what these platforms are designed to do, protect their mental health, and build real confidence "
                "that does not depend on a screen. "
                f"The work <strong>{org}</strong> is doing is exactly the kind of room this conversation belongs in."
            )
        elif any(w in combined for w in ("media", "journalism", "communication", "creator", "digital", "storytell")):
            hook = (
                "My work sits at the intersection of storytelling, social media, and representation — "
                "and I think that conversation is one <strong>{org}</strong>'s community would get a lot from."
            ).format(org=org)
        elif any(w in combined for w in ("health", "wellness", "body", "medical", "care", "mental")):
            hook = (
                "I co-created the <strong>Institute for Body Image</strong>, a professional development program "
                "training medical providers in inclusive, body-positive care, "
                "and I speak on body image, representation, and well-being in ways that resonate across all kinds of audiences."
            )
        elif any(w in combined for w in ("women", "female", "gender", "empower", "leadership")):
            hook = (
                "I speak to women's organizations on confidence, visibility, and showing up before you feel ready. "
                f"The work <strong>{org}</strong> is doing is exactly the kind of mission I want to be connected to."
            )
        elif any(w in combined for w in ("arts", "culture", "creative", "museum", "theater", "film")):
            hook = (
                "I am an actress, speaker, and creator who has spent years building at the intersection of "
                "storytelling, representation, and community. "
                f"I think there is a real conversation to be had with <strong>{org}</strong>'s audience."
            )
        else:
            hook = (
                f"I have been following the work <strong>{org}</strong> is doing and think there is a real "
                "opportunity to bring something meaningful to your community this season."
            )
        cta_text = (
            f"Happy to talk through what makes sense. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here</a> or just reply and we can go from there."
        )
        body_copy = NONPROFIT_SPEAKER_BODY.format(org=org, hook=hook, cta=cta_text)
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
    elif profile == "venue_host":
        subject = random.choice(VENUE_HOST_SUBJECTS).format(org=org)
        body_copy = VENUE_HOST_BODY.format(org=org, calendly=SENDER_CALENDLY)
        cta = ""
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
    elif profile == "nonprofit_speaker":
        followup_note = (
            f"Just following up in case my first note got buried.<br><br>"
            f"With the holidays right around the corner, I wanted to circle back on whether there is a fit for "
            f"<strong>{org}</strong> — a keynote, a workshop, or help hosting an event. "
            f"Even a quick 15-minute call would be worth it.<br><br>"
            f"Happy to work around your schedule."
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
