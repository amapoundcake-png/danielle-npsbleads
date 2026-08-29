"""
email_templates.py — Profile-based email templates for Danni Adams outreach.

Profiles: warmup | nonprofit | speaker | creator | brand | talent
"""

import logging
import random
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

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
    BRAND_SUBJECTS, BRAND_CREATOR_SUBJECTS,
    BRAND_ACTIVATION_BODY, BRAND_CREATOR_BODY,
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
                "I've done ongoing work with women's shelters on resilience and confidence — "
                f"helping women find their voice again after hard seasons. I would love to bring that work to "
                f"<strong>{org}</strong> and the women you serve."
            )
        elif any(w in combined for w in ("youth", "teen", "girl", "mentor", "student", "after school", "kids")):
            hook = (
                "I've worked with youth programs on sessions around social media, digital safety, and self-esteem "
                "— helping young people understand what these platforms are actually built to do and how to protect "
                "themselves from it. I also talk about confidence and not letting a screen decide how you feel about yourself. "
                f"I would love to bring that conversation to <strong>{org}</strong>."
            )
        elif any(w in combined for w in ("media", "journalism", "communication", "creator", "digital", "storytell")):
            hook = (
                "My work sits at the intersection of storytelling, social media, and representation — "
                f"and I think that conversation is one <strong>{org}</strong>'s community would get a lot from."
            )
        elif any(w in combined for w in ("health", "wellness", "body", "medical", "care", "mental")):
            hook = (
                "I co-created the <strong>Institute for Body Image</strong>, a professional development program "
                "training medical providers in inclusive, body-positive care, "
                "and I speak on body image, representation, and well-being in ways that resonate across all kinds of audiences."
            )
        elif any(w in combined for w in ("women", "female", "gender", "empower", "leadership")):
            hook = (
                "I speak to women's organizations on confidence, showing up before you feel ready, and what it "
                "actually takes to build a life and a career on your own terms. I've done this work with shelters, "
                "leadership programs, and civic organizations. Every time, the room tells me they needed that conversation. "
                f"I would love to bring it to <strong>{org}</strong>."
            )
        elif any(w in combined for w in ("arts", "culture", "creative", "museum", "theater", "film")):
            hook = (
                "I'm an actress, speaker, and creator who has spent years working at the intersection of "
                "storytelling, representation, and community. "
                f"I think there is a real conversation to be had with <strong>{org}</strong>'s audience."
            )
        else:
            hook = (
                f"I've been following the work <strong>{org}</strong> is doing. "
                "I think there is a real conversation I could bring to your community this season."
            )
        cta_text = (
            f"<a href='{SENDER_CALENDLY}'>Grab time here</a> or just reply and we can figure out what makes sense."
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
        # Determine version: brand_creator vs brand_activation
        # Check notes for creator/content signals; default to activation pitch
        notes = lead.get("notes", "").strip()
        industry = lead.get("industry", "").strip()
        notes_lower = notes.lower()
        is_creator_pitch = any(w in notes_lower for w in (
            "creator", "ugc", "content", "influencer", "social media partner"
        ))
        # Personalization reason must come from real notes — not generated filler
        # If notes are empty or too short, flag lead rather than inventing context
        if not notes or len(notes.strip()) < 10:
            logger.warning(
                "Brand lead %s <%s> has no personalization notes — flagging as NEEDS_PERSONALIZATION",
                org, lead.get("email", ""),
            )
            reason = "[NEEDS PERSONALIZATION — do not send without a real reason]"
        else:
            reason = notes.strip()
        if is_creator_pitch:
            subject = random.choice(BRAND_CREATOR_SUBJECTS).format(org=org)
            body_copy = BRAND_CREATOR_BODY.format(org=org, reason=reason)
        else:
            subject = random.choice(BRAND_SUBJECTS).format(org=org)
            body_copy = BRAND_ACTIVATION_BODY.format(org=org, reason=reason)
        cta = ""
    elif profile == "talent":
        subject = random.choice(TALENT_SUBJECTS).format(org=org)
        body_copy = TALENT_BODY
        cta = ""
    elif profile == "venue_host":
        subject = random.choice(VENUE_HOST_SUBJECTS).format(org=org)
        # Build event hook from lead's notes/industry — must be specific
        notes = lead.get("notes", "").strip()
        industry = lead.get("industry", "").strip()
        notes_lower = (notes + " " + industry).lower()
        if any(w in notes_lower for w in ("comedy", "stand-up", "standup", "improv")):
            event_hook = f"I noticed <strong>{org}</strong> runs comedy and live entertainment, and I wanted to reach out."
        elif any(w in notes_lower for w in ("jazz", "cabaret", "live music", "music venue")):
            event_hook = f"I noticed <strong>{org}</strong> hosts live music and events, and I wanted to reach out."
        elif any(w in notes_lower for w in ("theater", "theatre", "black box", "performing arts")):
            event_hook = f"I noticed <strong>{org}</strong> produces live performances and programming, and I wanted to reach out."
        elif any(w in notes_lower for w in ("panel", "conference", "networking", "fundraiser", "gala")):
            event_hook = f"I noticed <strong>{org}</strong> hosts panels and events, and I wanted to reach out."
        elif any(w in notes_lower for w in ("arts", "cultural", "gallery", "community")):
            event_hook = f"I noticed <strong>{org}</strong> runs community programming and events, and I wanted to reach out."
        elif industry:
            event_hook = f"I came across <strong>{org}</strong> and wanted to reach out about hosting opportunities."
        else:
            logger.warning(
                "Venue lead %s <%s> has no event type in notes — flagging as NEEDS_PERSONALIZATION",
                org, lead.get("email", ""),
            )
            event_hook = "[NEEDS PERSONALIZATION — add event type before sending]"
        body_copy = VENUE_HOST_BODY.format(org=org, event_hook=event_hook)
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
