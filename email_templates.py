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
                "I've done ongoing work with women's shelters on resilience and confidence, "
                f"helping women find their voice again after hard seasons. I would love to bring that work to "
                f"<strong>{org}</strong> and the women you serve."
            )
        elif any(w in combined for w in ("youth", "teen", "girl", "mentor", "student", "after school", "kids")):
            hook = (
                "I've worked with youth programs on sessions around social media, digital safety, and self-esteem, "
                "helping young people understand what these platforms are actually built to do and how to protect "
                "themselves from it. I also talk about confidence and not letting a screen decide how you feel about yourself. "
                f"I would love to bring that conversation to <strong>{org}</strong>."
            )
        elif any(w in combined for w in ("media", "journalism", "communication", "creator", "digital", "storytell")):
            hook = (
                "My work sits at the intersection of storytelling, social media, and representation, "
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
            reason = "[NEEDS PERSONALIZATION - do not send without a real reason]"
        else:
            reason = notes.strip()
        if is_creator_pitch:
            subject = random.choice(BRAND_CREATOR_SUBJECTS).format(org=org)
            body_copy = BRAND_CREATOR_BODY.format(org=org, reason=reason)
        else:
            subject = random.choice(BRAND_SUBJECTS).format(org=org)
            body_copy = BRAND_ACTIVATION_BODY.format(org=org, reason=reason)
        cta = ""
    elif profile == "senior_living":
        subject = random.choice([
            "Entertainment idea for {org}",
            "Speaker idea for your residents at {org}",
            "Programming idea for {org}",
        ]).format(org=org)
        body_copy = (
            f"I wanted to reach out to whoever handles programming and activities at "
            f"<strong>{org}</strong>.<br><br>"
            f"My name is Danni Adams. I am an Orlando-based speaker, actress, and community advocate. "
            f"I have spoken at universities, women's organizations, and mentoring programs on topics "
            f"including confidence, self-worth, and storytelling. I also do ongoing workshop-style "
            f"visits with community groups, and I would love to bring that energy to your residents.<br><br>"
            f"I am easy to work with, flexible on format, and happy to tailor the visit to what your "
            f"community would enjoy most, whether that is a talk, an interactive session, or just "
            f"good conversation. I am also local, so travel is never a barrier.<br><br>"
            f"Would it make sense to connect? Just reply here or "
            f"<a href='{SENDER_CALENDLY}'>grab a quick 20 minutes.</a>"
        )
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
            event_hook = "[NEEDS PERSONALIZATION - add event type before sending]"
        body_copy = VENUE_HOST_BODY.format(org=org, event_hook=event_hook)
        cta = ""
    else:
        subject = f"Reaching out about {org}"
        body_copy = NONPROFIT_BODY.format(org=org)
        cta = f"Worth a 20-minute call? <a href='{SENDER_CALENDLY}'>Grab time here.</a>"

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
    """
    Follow-up email — second persuasive touchpoint, not a reminder.

    Each version mirrors its original pitch and surfaces the single strongest
    hero moment from it. The goal is: remind them why they should care about
    a conversation with Danni specifically, not that she exists.

    Formula:
    1. One sentence acknowledging the previous outreach.
    2. The single strongest hero moment from the original pitch, stated
       confidently as a callback — not meta-commentary ("the case I made was")
       but the credential itself, framed around why it is specific to this org.
    3. A clear reason to take the call.
    4. Calendly CTA.
    """
    profile = lead.get("profile", "nonprofit")
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")
    greeting = f"Hi {first}," if first != "there" else "Hi,"

    if profile == "nonprofit":
        # Original pitch led with: City of Sanford Influencer Program + Institute
        # for Body Image + MPA + fractional strategic partner positioning.
        # Hero moment: City of Sanford Influencer Program — most concrete proof
        # that she has done this exact work for an org with limited resources.
        followup_note = (
            f"I reached out a few weeks back with some ideas for <strong>{org}</strong>.<br><br>"
            f"The thing I most want you to take from my first note: I managed the "
            f"<strong>City of Sanford Influencer Program</strong>, building community outreach "
            f"and digital visibility for a civic organization that needed to reach people "
            f"authentically without a large team behind it. That is the same challenge "
            f"most nonprofits face, and it is the work I know how to do.<br><br>"
            f"I have specific ideas for <strong>{org}</strong> around storytelling, visibility, "
            f"and outreach. Worth a 20-minute call? "
            f"<a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "nonprofit_speaker":
        # Original pitch led with a personalized hook (shelter / youth / women's /
        # arts / health / media) then Harvard + U Ottawa + Bethune-Cookman + Seminole.
        # Hero moment: the ongoing shelter / mentoring work — because that is what
        # distinguishes Danni from every other speaker with a Harvard credit.
        # For orgs that are not shelter-adjacent, the Harvard stack is the hero.
        notes = (lead.get("notes", "") or "").lower()
        industry = (lead.get("industry", "") or "").lower()
        combined = notes + " " + industry

        if any(w in combined for w in ("shelter", "domestic", "survivor", "violence",
                                        "refuge", "youth", "teen", "girl", "mentor",
                                        "student", "after school", "kids")):
            hero = (
                f"I go into women's shelters and girls' mentoring programs regularly, "
                f"not as a speaking booking but as an ongoing commitment. I deliver my talk "
                f"on not giving up, rebuilding confidence, and dreaming bigger than your current "
                f"circumstances in those rooms because I believe they are the rooms that "
                f"matter most. I am also a <strong>Harvard speaker and Seminole Leadership "
                f"Conference keynote speaker</strong>. Same presence, every room."
            )
        elif any(w in combined for w in ("health", "wellness", "body", "medical",
                                          "care", "mental", "lgbtq", "pride", "queer")):
            hero = (
                f"I co-founded the <strong>Institute for Body Image</strong>, a program "
                f"that trains medical professionals in inclusive, body-positive, affirming care. "
                f"I built that infrastructure because the gap was real. I also speak at "
                f"<strong>Harvard University</strong> and the Seminole Leadership Conference. "
                f"For <strong>{org}</strong>'s community, this is not performed allyship. "
                f"This is my actual work."
            )
        elif any(w in combined for w in ("women", "female", "gender", "empower", "leadership")):
            hero = (
                f"I delivered the keynote at the <strong>Seminole Leadership Conference</strong> "
                f"and I do ongoing community work with women's organizations and mentoring programs. "
                f"The leadership credential says I belong on your stage, and the community work "
                f"says I belong in your organization. I am also a <strong>Harvard speaker</strong>. "
                f"That combination is rare."
            )
        elif any(w in combined for w in ("media", "creator", "digital", "storytell",
                                          "arts", "culture", "museum", "theater")):
            hero = (
                f"I have a <strong>Vogue editorial feature</strong>, a Harvard speaker credit, "
                f"and 52,500 Instagram followers at a 4% engagement rate, built without a "
                f"publicist or a brand cosign. For <strong>{org}</strong>'s audience, I "
                f"understand this space from the inside, not as an outside observer."
            )
        else:
            hero = (
                f"I have spoken at <strong>Harvard University, the University of Ottawa, "
                f"Bethune-Cookman University, and the Seminole Leadership Conference</strong>. "
                f"I also do ongoing community work with women's organizations, shelters, and "
                f"mentoring programs. I show up with the same presence in every room."
            )

        followup_note = (
            f"I reached out a few weeks back about a speaking opportunity for "
            f"<strong>{org}</strong> and wanted to follow up.<br><br>"
            f"{hero}<br><br>"
            f"Worth a 20-minute call to see if there is a fit? "
            f"<a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "political":
        # Original pitch led with: City of Sanford + Florida For All + MPA + fractional.
        followup_note = (
            f"I reached out a few weeks back with some ideas for <strong>{org}</strong>.<br><br>"
            f"The <strong>City of Sanford Influencer Program</strong> is what I'd most want you "
            f"to carry from my first note: I built community outreach and digital campaigns "
            f"for a civic organization that needed to reach people fast, with limited resources. "
            f"I also have an MPA from UNF and spent years in strategic partnerships and civic "
            f"engagement. With the election timeline moving fast, I work as a fractional "
            f"partner. I plug in quickly and focus on the work that moves people.<br><br>"
            f"Happy to talk. <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "speaker":
        # Original pitch led with: Institute for Body Image + Harvard + Jennifer Hudson
        # Show + Tamron Hall + creator economy framing.
        # Hero moment: Institute for Body Image — most distinctive credential,
        # separates Danni from every other speaker with TV credits.
        followup_note = (
            f"I reached out a few weeks back about a speaking opportunity at "
            f"<strong>{org}</strong> and wanted to follow up.<br><br>"
            f"I co-founded the <strong>Institute for Body Image</strong>, a professional "
            f"development program that trains medical providers in inclusive, body-positive care. "
            f"I built that from scratch. I have also spoken at "
            f"<strong>Harvard University, the University of Ottawa, Full Sail, and "
            f"Bethune-Cookman</strong>, and have been featured on "
            f"<strong>The Jennifer Hudson Show and Tamron Hall</strong>.<br><br>"
            f"Happy to send my full speaker kit, or just find time to talk. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "creator":
        followup_note = (
            f"I reached out a few weeks back about a speaking opportunity at "
            f"<strong>{org}</strong> and wanted to follow up.<br><br>"
            f"I hosted the <strong>Social Icon Influencer Conference</strong> and "
            f"<strong>BET Beauty Brunch</strong>, managed the "
            f"<strong>City of Sanford Influencer Program</strong>, and have spoken at "
            f"<strong>Harvard University</strong>. I built all of it without an "
            f"agent, a PR team, or a budget. For a creator-economy audience, that "
            f"is not a backstory. That is the talk.<br><br>"
            f"Happy to send my speaker kit or find time to connect. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "brand":
        # Original pitch led with: @amapoundcake + 74% women 25-54 audience +
        # T-Mobile / YITTY / Hilton partnerships + personalized reason.
        followup_note = (
            f"I wanted to circle back on my note about <strong>{org}</strong>.<br><br>"
            f"My audience is 74% women, ages 25-54, with a 4% engagement rate "
            f"(the industry average is 1-3%). I have worked with "
            f"<strong>T-Mobile, YITTY by Lizzo, and Hilton Hotels</strong>. "
            f"If there is a fit for a creator partnership or Orlando activation, "
            f"I would love to talk through what that looks like.<br><br>"
            f"Happy to send my full media kit. Just reply here or "
            f"<a href='{SENDER_CALENDLY}'>grab time here.</a>"
        )

    elif profile == "venue_host":
        # Original pitch led with: Social Icon + BET Beauty Brunch + TLC/JHS/Tamron
        # + "local, prepared, don't need a long runway."
        # Hero moment: BET Beauty Brunch + Social Icon + "local" — specificity
        # about the hosting credits and not being a flight risk.
        followup_note = (
            f"I sent a hosting inquiry a few weeks back and wanted to follow up.<br><br>"
            f"I hosted the <strong>BET Beauty Brunch</strong> and the "
            f"<strong>Social Icon Influencer Conference</strong>, and I have national TV "
            f"experience on TLC, The Jennifer Hudson Show, and Tamron Hall. "
            f"I am also Orlando-based. I do not need a long runway to be good in "
            f"the room, and I do not create extra work for your team.<br><br>"
            f"If there is an upcoming event where a host could be useful, I would love "
            f"to be considered. <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "senior_living":
        followup_note = (
            f"I reached out a few weeks back about programming at <strong>{org}</strong> "
            f"and wanted to follow up.<br><br>"
            f"I am a speaker and community advocate based in Orlando. I do ongoing visits "
            f"with community groups around confidence, self-worth, and storytelling, and I "
            f"would love to bring that work to your residents. I am flexible on format and "
            f"happy to tailor to whatever would be most meaningful for your community.<br><br>"
            f"Worth a quick call? <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "talent":
        followup_note = (
            f"I reached out a few weeks back about representation and wanted to follow up.<br><br>"
            f"My current credits: <strong>Sixt (principal, national commercial), "
            f"TLC (Cracked Addicts, 2024), The Jennifer Hudson Show, Tamron Hall</strong>, "
            f"and an upcoming stage role at Lake Nona Arts. I have also been featured in "
            f"<strong>Vogue</strong> and <strong>The Cut</strong>, "
            f"and hosted the BET Beauty Brunch and Social Icon Influencer Conference.<br><br>"
            f"Happy to send my full reel and materials. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    else:
        followup_note = (
            f"I reached out a few weeks back about <strong>{org}</strong> and wanted to follow up.<br><br>"
            f"I managed the <strong>City of Sanford Influencer Program</strong> and "
            f"co-created the <strong>Institute for Body Image</strong>. Both required "
            f"building community awareness and outreach systems from scratch with limited resources. "
            f"I have specific ideas for your organization and would love to share them.<br><br>"
            f"Worth a 20-minute call? <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
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
