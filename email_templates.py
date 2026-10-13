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
    CORP_EVENT_PLANNER_SUBJECTS, CORP_EVENT_PLANNER_BODY,
    HOTEL_VENUE_SUBJECTS, HOTEL_VENUE_BODY,
    EVENT_AGENCY_SUBJECTS, EVENT_AGENCY_BODY,
    ASSOC_ERG_SUBJECTS, ASSOC_ERG_BODY,
    CONFERENCE_MODERATOR_SUBJECTS, CONFERENCE_MODERATOR_BODY,
    MEDIA_LOCAL_SUBJECTS, MEDIA_LOCAL_BODY,
    PODCAST_SUBJECTS, PODCAST_BODY,
    BRAND_BEAUTY_SUBJECTS, BRAND_BEAUTY_BODY,
    BRAND_FASHION_SUBJECTS, BRAND_FASHION_BODY,
)


def _first_name(full_name: str) -> str:
    if not full_name or not full_name.strip():
        return "there"
    return full_name.strip().split()[0]


def _signature(profile: str) -> str:
    linkedin = f"<a href='{SENDER_LINKEDIN}'>LinkedIn</a>" if SENDER_LINKEDIN else ""

    if profile in ("nonprofit", "political", "media_local", "podcast"):
        # Consulting / media context — professional, no Instagram
        parts = [f"<strong>{SENDER_NAME}</strong>", SENDER_EMAIL_HELLO]
        if linkedin:
            parts.append(linkedin)
        return "<br>".join(parts)

    elif profile in ("nonprofit_speaker", "speaker", "creator",
                     "assoc_erg", "conference_moderator"):
        # Speaker context — professional, no Instagram
        parts = [f"<strong>{SENDER_NAME}</strong>", SENDER_EMAIL_SPEAKING]
        if linkedin:
            parts.append(linkedin)
        return "<br>".join(parts)

    elif profile in ("brand", "talent", "venue_host",
                     "corp_event_planner", "hotel_venue", "event_agency",
                     "brand_beauty", "brand_fashion"):
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
        cta_text = (
            f"<a href='{SENDER_CALENDLY}'>Grab time here</a> or simply reply, and we can figure out what makes sense."
        )
        body_copy = NONPROFIT_SPEAKER_BODY.format(org=org, cta=cta_text)
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
    elif profile == "corp_event_planner":
        subject = random.choice(CORP_EVENT_PLANNER_SUBJECTS).format(org=org)
        body_copy = CORP_EVENT_PLANNER_BODY.format(org=org, calendly=SENDER_CALENDLY)
        cta = ""
    elif profile == "hotel_venue":
        subject = random.choice(HOTEL_VENUE_SUBJECTS).format(org=org)
        body_copy = HOTEL_VENUE_BODY.format(org=org, calendly=SENDER_CALENDLY)
        cta = ""
    elif profile == "event_agency":
        subject = random.choice(EVENT_AGENCY_SUBJECTS).format(org=org)
        body_copy = EVENT_AGENCY_BODY.format(org=org, calendly=SENDER_CALENDLY)
        cta = ""
    elif profile == "assoc_erg":
        subject = random.choice(ASSOC_ERG_SUBJECTS).format(org=org)
        body_copy = ASSOC_ERG_BODY.format(org=org, calendly=SENDER_CALENDLY)
        cta = ""
    elif profile == "conference_moderator":
        subject = random.choice(CONFERENCE_MODERATOR_SUBJECTS).format(org=org)
        body_copy = CONFERENCE_MODERATOR_BODY.format(org=org, calendly=SENDER_CALENDLY)
        cta = ""
    elif profile == "media_local":
        subject = random.choice(MEDIA_LOCAL_SUBJECTS).format(org=org)
        body_copy = MEDIA_LOCAL_BODY.format(org=org, calendly=SENDER_CALENDLY)
        cta = ""
    elif profile == "podcast":
        subject = random.choice(PODCAST_SUBJECTS).format(org=org)
        notes = lead.get("notes", "").strip()
        episode_ref = notes if notes and "[" not in notes else "[EPISODE_REFERENCE — must be filled before sending]"
        body_copy = PODCAST_BODY.format(org=org, episode_reference=episode_ref, calendly=SENDER_CALENDLY)
        cta = ""
    elif profile == "brand_beauty":
        subject = random.choice(BRAND_BEAUTY_SUBJECTS).format(org=org)
        body_copy = BRAND_BEAUTY_BODY.format(org=org, calendly=SENDER_CALENDLY)
        cta = ""
    elif profile == "brand_fashion":
        subject = random.choice(BRAND_FASHION_SUBJECTS).format(org=org)
        body_copy = BRAND_FASHION_BODY.format(org=org, calendly=SENDER_CALENDLY)
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
        # Original pitch: Institute for Body Image + City of Sanford + MPA + fractional positioning.
        # Hero moment: built outreach systems from scratch with limited resources.
        followup_note = (
            f"I reached out a few weeks back with some ideas for <strong>{org}</strong>.<br><br>"
            f"The credential I'd most want you to remember: I co-created the "
            f"<strong>Institute for Body Image</strong> from scratch with no marketing budget, "
            f"and led the <strong>City of Sanford Influencer Program</strong>, building donor visibility "
            f"and digital campaigns for an organization that needed to reach people without a large team behind it. "
            f"That is the same situation most nonprofits are in, and it is the work I know how to do.<br><br>"
            f"I have specific ideas for <strong>{org}</strong>. Worth a 20-minute call? "
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

        if any(w in combined for w in ("literacy", "reading", "writing", "education",
                                        "tutoring", "learning", "adult ed", "esl",
                                        "english", "workforce development")):
            hero = (
                f"I speak on storytelling, voice, and what it means to use your words to "
                f"build a life and a career. I have delivered that message at "
                f"<strong>Harvard University, the University of Ottawa, and Bethune-Cookman University</strong>, "
                f"and I take it into women's shelters and mentoring programs where people are "
                f"working to rewrite their own stories. For <strong>{org}</strong>'s community, "
                f"that is not a metaphor. That is the actual work."
            )
        elif any(w in combined for w in ("shelter", "domestic", "survivor", "violence",
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
                f"What I most want you to take from my first note: I have spoken at "
                f"<strong>Harvard University</strong> and the "
                f"<strong>Seminole Leadership Conference</strong>, and I also go into women's "
                f"shelters and mentoring programs regularly — not as a booking, as an ongoing "
                f"commitment. I show up the same way in every room. I think there is something "
                f"real I could bring to <strong>{org}</strong>'s community."
            )

        followup_note = (
            f"I reached out a few weeks back about a speaking opportunity for "
            f"<strong>{org}</strong> and wanted to follow up.<br><br>"
            f"{hero}<br><br>"
            f"Worth a 20-minute call to see if there is a fit? "
            f"<a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "political":
        followup_note = (
            f"I reached out a few weeks back with some ideas for <strong>{org}</strong>.<br><br>"
            f"What I'd most want you to carry from my first note: I hold an MPA from UNF, "
            f"led the <strong>City of Sanford Influencer Program</strong> building community outreach "
            f"and digital campaigns, and co-created the <strong>Institute for Body Image</strong> "
            f"from scratch with no marketing budget. "
            f"With the election timeline moving fast, I work as a fractional "
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
            f"<strong>BET Beauty Brunch</strong> and have spoken at "
            f"<strong>Harvard University</strong>. I have national TV credits on "
            f"TLC, The Jennifer Hudson Show, and Tamron Hall. I built all of it without an "
            f"agent, a PR team, or a budget. For a creator-economy audience, that "
            f"is not a backstory. That is the talk.<br><br>"
            f"Happy to send my speaker kit or find time to connect. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "brand":
        # Original pitch led with: @amapoundcake + 74% women 25-54 audience +
        # T-Mobile / YITTY / Hilton partnerships + personalized reason.
        followup_note = (
            f"I sent a note a few weeks back about a creator partnership with <strong>{org}</strong> and wanted to follow up.<br><br>"
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

    elif profile == "corp_event_planner":
        followup_note = (
            f"I sent a note a few weeks back about hosting and emcee work for events your clients run, and wanted to follow up.<br><br>"
            f"Quick recap: I hosted the <strong>BET Beauty Brunch</strong> and the "
            f"<strong>Social Icon Influencer Conference</strong>. I have national TV credits on "
            f"<strong>TLC, The Jennifer Hudson Show, and Tamron Hall</strong>. "
            f"I am Orlando-based and do not create extra logistics for your team.<br><br>"
            f"If you have an upcoming event where a host or emcee would be useful, I would love to be on your radar. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "hotel_venue":
        followup_note = (
            f"I sent a note a few weeks back about hosting and emcee opportunities and wanted to follow up.<br><br>"
            f"I hosted the <strong>BET Beauty Brunch</strong> and the "
            f"<strong>Social Icon Influencer Conference</strong>, and I have national TV credits on "
            f"<strong>TLC, The Jennifer Hudson Show, and Tamron Hall</strong>. "
            f"I am local, prepared, and do not need a long runway.<br><br>"
            f"If there is an upcoming gala, awards night, or corporate event where a host could be useful, "
            f"I would love to be considered. <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "event_agency":
        followup_note = (
            f"I reached out a few weeks back about representation and wanted to follow up.<br><br>"
            f"My current credits: <strong>BET Beauty Brunch host, Social Icon Influencer Conference host, "
            f"Sixt national commercial (principal), TLC, The Jennifer Hudson Show, Tamron Hall</strong>. "
            f"I also have a <strong>Vogue editorial feature</strong> and a Harvard speaker credit. "
            f"75,000 followers across Instagram, TikTok, and Facebook.<br><br>"
            f"Happy to send my full materials. <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "assoc_erg":
        followup_note = (
            f"I reached out a few weeks back about a speaking opportunity for "
            f"<strong>{org}</strong> and wanted to follow up.<br><br>"
            f"I have spoken at <strong>Harvard University, the University of Ottawa, Full Sail, and Bethune-Cookman</strong>, "
            f"and delivered the keynote at the <strong>Seminole Leadership Conference</strong>. "
            f"I also co-founded the <strong>Institute for Body Image</strong>, "
            f"a program that trains medical professionals in inclusive, body-positive care.<br><br>"
            f"Worth a 20-minute call? <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "conference_moderator":
        followup_note = (
            f"I reached out a few weeks back about a moderating or speaking role at "
            f"<strong>{org}</strong> and wanted to follow up.<br><br>"
            f"I have hosted the <strong>BET Beauty Brunch</strong> and the "
            f"<strong>Social Icon Influencer Conference</strong>, spoken at "
            f"<strong>Harvard University</strong>, and appeared on "
            f"<strong>The Jennifer Hudson Show and Tamron Hall</strong>. "
            f"I know how to hold a room and keep a conversation moving.<br><br>"
            f"Happy to send my speaker kit. <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "media_local":
        followup_note = (
            f"I reached out a few weeks back and wanted to follow up.<br><br>"
            f"Quick recap on why I think there is a story here: I co-founded the "
            f"<strong>Institute for Body Image</strong> (training medical providers in inclusive care), "
            f"I have been featured in <strong>Vogue and The Cut</strong>, "
            f"and I have national TV credits on <strong>TLC, The Jennifer Hudson Show, and Tamron Hall</strong>. "
            f"I am also Orlando-based and actively working in the community.<br><br>"
            f"Happy to connect on a story or segment. <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "podcast":
        followup_note = (
            f"I reached out a few weeks back about being a guest on your show and wanted to follow up.<br><br>"
            f"I co-founded the <strong>Institute for Body Image</strong>, have spoken at "
            f"<strong>Harvard University</strong>, appeared on <strong>The Jennifer Hudson Show "
            f"and Tamron Hall</strong>, and have been featured in <strong>Vogue and The Cut</strong>. "
            f"75,000 followers across platforms. I have real things to say and I know how to say them.<br><br>"
            f"Happy to connect. <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "brand_beauty":
        followup_note = (
            f"I sent a note a few weeks back about a creator partnership with <strong>{org}</strong> and wanted to follow up.<br><br>"
            f"My audience is 75,000 across Instagram, TikTok, and Facebook, with a 4% engagement rate "
            f"(the industry average is 1-3%). I have worked with "
            f"<strong>T-Mobile, YITTY by Lizzo, Morphe Beauty, BH Cosmetics, and Hilton Hotels</strong>. "
            f"If there is a campaign, launch, or UGC opportunity coming up, I would love to be in the conversation.<br><br>"
            f"Happy to send my full media kit. <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )

    elif profile == "brand_fashion":
        followup_note = (
            f"I sent a note a few weeks back about a creator partnership with <strong>{org}</strong> and wanted to follow up.<br><br>"
            f"My audience is 75,000 across Instagram, TikTok, and Facebook, with a 4% engagement rate. "
            f"I have worn and partnered with <strong>YITTY by Lizzo, ELOQUII, Fashion to Figure, "
            f"Chromat, and Alpine Butterfly Swim</strong>. "
            f"If you have a campaign, launch, or UGC project coming up, I would love to talk about what that could look like.<br><br>"
            f"Happy to send my full media kit. <a href='{SENDER_CALENDLY}'>Grab time here.</a>"
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
            f"I co-created the <strong>Institute for Body Image</strong> and led the "
            f"<strong>City of Sanford Influencer Program</strong> — both required building community "
            f"awareness and outreach systems from scratch with limited resources. "
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

    if profile in ("nonprofit", "political"):
        reconnect = (
            f"I reached out about a month ago about <strong>{org}</strong>. "
            f"The work I do with nonprofits on community engagement, partnerships, and outreach systems is the same regardless of budget size or team capacity. "
            f"If Q4 planning is on your radar and you want an outside perspective, I am available. "
            f"<a href='{SENDER_CALENDLY}'>Grab 20 minutes here</a> or just reply."
        )
    elif profile in ("speaker", "nonprofit_speaker", "creator"):
        reconnect = (
            f"I reached out about a month ago about a speaking opportunity at <strong>{org}</strong>. "
            f"If you are still building out your programming calendar, I would love to be on the shortlist. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here</a> or just reply and I can send my full speaker kit."
        )
    elif profile == "brand":
        reconnect = (
            f"I reached out about a month ago about a creator partnership with <strong>{org}</strong>. "
            f"If you have anything on the horizon, I would love to hear about it. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here</a> or reply and I can send my full media kit."
        )
    elif profile in ("venue_host", "talent", "corp_event_planner", "hotel_venue", "event_agency"):
        reconnect = (
            f"I reached out about a month ago about working with <strong>{org}</strong>. "
            f"If timing is better now, I would love to connect. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here.</a>"
        )
    elif profile in ("assoc_erg", "conference_moderator"):
        reconnect = (
            f"I reached out about a month ago about a speaking or moderating opportunity at <strong>{org}</strong>. "
            f"If you are still building out your programming calendar, I would love to be on the shortlist. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here</a> or just reply and I can send my speaker kit."
        )
    elif profile in ("media_local", "podcast"):
        reconnect = (
            f"I reached out about a month ago and wanted to circle back. "
            f"If the timing is better now for a story, segment, or guest spot, I am available. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here</a> or just reply."
        )
    elif profile in ("brand_beauty", "brand_fashion"):
        reconnect = (
            f"I reached out about a month ago about a creator partnership with <strong>{org}</strong>. "
            f"If you have anything on the horizon, I would love to hear about it. "
            f"<a href='{SENDER_CALENDLY}'>Grab time here</a> or reply and I can send my full media kit."
        )
    else:
        reconnect = (
            f"I reached out about a month ago about <strong>{org}</strong>. "
            f"If the timing is better now, I would love to connect. "
            f"<a href='{SENDER_CALENDLY}'>Grab 20 minutes here</a> or just reply."
        )

    body = (
        f"{greeting}<br><br>"
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
