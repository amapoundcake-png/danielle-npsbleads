"""
email_templates.py -- Two-profile outreach templates for Danni Adams.

Profile "speaker"  -> universities, conferences, corporate DEI, nonprofits
Profile "brand"    -> brands, PR firms, talent agencies, partnerships
Profile "press"    -> journalists, editors, producers, media contacts

Voice: Direct. Human. No corporate filler. Keke Palmer energy.
No em dashes. No AI-coded phrases.
"""

import random
import os
from config import (
    SENDER_NAME,
    SENDER_TITLE_SPEAKER,
    SENDER_TITLE_BRAND,
    SENDER_LOCATION,
    SENDER_CALENDLY,
    SENDER_LINKEDIN,
    SENDER_INSTAGRAM,
    GMAIL_ADDRESS,
    SPEAKER_KIT_URL,
    BRAND_KIT_URL,
)


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def _first_name(full_name: str) -> str:
    if not full_name or not full_name.strip():
        return "there"
    return full_name.strip().split()[0]


def _sig(profile: str) -> str:
    if profile == "speaker":
        return (
            f"--\n"
            f"{SENDER_NAME}\n"
            f"{SENDER_TITLE_SPEAKER}\n"
            f"{GMAIL_ADDRESS}\n"
            f"LinkedIn: {SENDER_LINKEDIN}"
        )
    return (
        f"--\n"
        f"{SENDER_NAME} | {SENDER_INSTAGRAM}\n"
        f"{SENDER_TITLE_BRAND}\n"
        f"{GMAIL_ADDRESS}\n"
        f"LinkedIn: {SENDER_LINKEDIN}"
    )


# ---------------------------------------------------------------------------
# SPEAKER PROFILE
# ---------------------------------------------------------------------------

SPEAKER_SUBJECTS = [
    "Speaking inquiry for {org}",
    "Keynote inquiry | Danni Adams",
    "{org} -- speaker inquiry",
    "Quick note about speaking at {org}",
    "Workshop or keynote for {org}",
]


def build_speaker_email(lead: dict) -> dict:
    """
    Initial outreach to universities, conferences, nonprofits, youth centers.
    No DEI language -- pivot to leadership, storytelling, community, media literacy.

    lead keys: name, org, email, notes (optional), event_type (optional),
               dept (optional -- department name for university pitches)
    """
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")
    notes = (lead.get("notes", "") or "").strip()
    event_type = (lead.get("event_type", "") or "").strip()
    dept = (lead.get("dept", "") or "").strip()

    subject = random.choice(SPEAKER_SUBJECTS).format(org=org)

    if notes:
        notes_clean = notes.rstrip(".")
        opener = f"I came across {org} and was really drawn to what you all are building -- {notes_clean.lower()}."
    elif dept:
        opener = f"I am reaching out to the {dept} at {org} about a potential speaking engagement."
    else:
        opener = f"I came across {org} and wanted to reach out directly."

    event_line = f"I noticed you have {event_type} coming up and thought this might be a good fit.\n\n" if event_type else ""

    kit_line = f"\nYou can see my full speaker one-sheet here: {SPEAKER_KIT_URL}\n" if SPEAKER_KIT_URL else ""
    cal_line = f"\nIf you want to hop on a call, here is my calendar: {SENDER_CALENDLY}\n" if SENDER_CALENDLY else ""

    body = (
        f"Hi {first},\n\n"
        f"{opener}\n\n"
        f"{event_line}"
        f"I'm Danni Adams, a speaker based in Orlando, FL. I have a Master's in Public "
        f"Administration from the University of North Florida and a background in sociology, "
        f"and I have spoken at Harvard University, the University of Ottawa, Full Sail University, "
        f"Bethune-Cookman, and the Seminole Leadership Conference. I also do ongoing talks at "
        f"women's shelters and girls' mentoring programs. The rooms look different but the "
        f"conversation is the same -- how do you build something real when nobody is coming "
        f"to save you.\n\n"
        f"My topics include social media and storytelling, body image and media literacy, "
        f"representation and identity, and personal resilience. I can deliver a keynote, "
        f"a workshop, or a panel, depending on what works for your audience.\n\n"
        f"I have been featured on NPR, the Jennifer Hudson Show, Tamron Hall, TLC, and in Vogue, "
        f"and I am the Co-Creator of the Institute for Body Image, which trains medical "
        f"professionals in inclusive care. This is not just a stage for me -- it is the "
        f"actual work I do."
        f"{kit_line}"
        f"\nWould it make sense to connect for 20 minutes? Happy to work around your schedule."
        f"{cal_line}"
        f"\nBest,\n{_sig('speaker')}"
    )

    return {"to": lead["email"], "subject": subject, "body": body}


def build_speaker_followup(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")

    body = (
        f"Hi {first},\n\n"
        f"Following up in case my last note got buried.\n\n"
        f"I know your inbox is real. I just wanted to make sure you had a chance to see it "
        f"before I moved on.\n\n"
        f"If the timing is off or {org} is not booking speakers right now, totally understand. "
        f"But if there is any chance it could be a fit, even a 15-minute conversation would "
        f"be worth it.\n\n"
        f"No pressure either way.\n\n"
        f"Best,\n{_sig('speaker')}"
    )

    return {"to": lead["email"], "subject": f"Re: {original_subject}", "body": body}


def build_speaker_checkin(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")

    kit_line = f"\nSpeaker one-sheet: {SPEAKER_KIT_URL}\n" if SPEAKER_KIT_URL else ""
    cal_line = f"\nCalendar: {SENDER_CALENDLY}\n" if SENDER_CALENDLY else ""

    body = (
        f"Hi {first},\n\n"
        f"I reached out about a month ago about a potential speaking engagement with {org}. "
        f"Totally understand if the timing was not right.\n\n"
        f"Just checking back in. If anything has shifted and a speaker conversation makes "
        f"sense, I am still available and would love to connect."
        f"{kit_line}"
        f"\nWorth a quick 20 minutes?"
        f"{cal_line}"
        f"\nBest,\n{_sig('speaker')}"
    )

    return {"to": lead["email"], "subject": f"Re: {original_subject}", "body": body}


# ---------------------------------------------------------------------------
# BRAND PROFILE
# ---------------------------------------------------------------------------

BRAND_SUBJECTS = [
    "Partnership inquiry | @amapoundcake",
    "Creator partnership | Danni Adams x {org}",
    "{org} -- collaboration idea",
    "Quick note about a potential collab with {org}",
    "Content partnership | @amapoundcake",
]


def build_brand_email(lead: dict) -> dict:
    """
    Initial outreach to brands for influencer deals, ambassador programs,
    event partnerships, or content collaborations.

    lead keys: name, org, email, partnership_angle (optional), notes (optional)
    """
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your brand")
    notes = (lead.get("notes", "") or "").strip()
    angle = (lead.get("partnership_angle", "") or "").strip()

    subject = random.choice(BRAND_SUBJECTS).format(org=org)

    if notes:
        opener = f"I have been following {org} for a while and genuinely love what you are doing -- {notes.rstrip('.').lower()}."
    else:
        opener = f"I have been following {org} for a while and wanted to reach out directly."

    angle_line = f"\n{angle}\n" if angle else ""
    kit_line = f"\nYou can see my full brand kit here: {BRAND_KIT_URL}\n" if BRAND_KIT_URL else ""

    body = (
        f"Hi {first},\n\n"
        f"{opener}\n\n"
        f"I'm Danni Adams, the creator behind @amapoundcake. I have built a community of "
        f"over 52,000 people across Instagram and TikTok with a 4% engagement rate -- "
        f"nearly five times the industry average. My audience is 74% women, ages 25 to 54, "
        f"based in Orlando, Atlanta, Miami, and New York.\n\n"
        f"I do not just reach them. They trust me. That is the thing most brands are actually "
        f"trying to buy and cannot manufacture."
        f"{angle_line}"
        f"\nI have worked with T-Mobile, Hilton Hotels, Sixt, YITTY by Lizzo/Fabletics, "
        f"Morphe Beauty, and others. I am also the Co-Creator of the Institute for Body Image "
        f"and I have been featured in Vogue and appeared on NPR, TLC, the Jennifer Hudson Show, "
        f"and Tamron Hall."
        f"{kit_line}"
        f"\nWould love to explore what a partnership could look like. Even a 15-minute call "
        f"to start the conversation would be great.\n\n"
        f"Best,\n{_sig('brand')}"
    )

    return {"to": lead["email"], "subject": subject, "body": body}


def build_brand_followup(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your brand")

    body = (
        f"Hi {first},\n\n"
        f"Just circling back in case my last note got buried.\n\n"
        f"I think there is a real opportunity for {org} here and I would love to explore it. "
        f"My audience is not passive -- they act on what I recommend, and I only recommend "
        f"things I actually believe in. That is what makes the engagement rate real.\n\n"
        f"If the timing is off, no problem. But if there is any interest, I would love to "
        f"connect for a quick call.\n\n"
        f"Best,\n{_sig('brand')}"
    )

    return {"to": lead["email"], "subject": f"Re: {original_subject}", "body": body}


# ---------------------------------------------------------------------------
# PRESS PROFILE (media pitches for coverage)
# ---------------------------------------------------------------------------

PRESS_SUBJECTS = [
    "Story pitch | Danni Adams",
    "Pitch: The influencer who speaks at Harvard and women's shelters",
    "Quick pitch | Danni Adams | @amapoundcake",
    "Story pitch -- body image, Harvard, and women's shelters",
    "Pitch: A different kind of influencer story",
]


def build_press_pitch(lead: dict) -> dict:
    """
    Press pitch to journalists and editors for feature coverage or quotes.

    lead keys: name, org (outlet), email, beat (optional), notes (optional)
    """
    first = _first_name(lead.get("name", ""))
    beat = (lead.get("beat", "") or "").strip()
    notes = (lead.get("notes", "") or "").strip()

    subject = random.choice(PRESS_SUBJECTS)

    beat_line = f"I read your work on {beat} and thought this would land right in your lane.\n\n" if beat else ""
    kit_line = f"\nFull background: {BRAND_KIT_URL}\n" if BRAND_KIT_URL else ""

    body = (
        f"Hi {first},\n\n"
        f"{beat_line}"
        f"I want to pitch you a story about Danni Adams, the creator behind @amapoundcake.\n\n"
        f"Here is the thing that is hard to explain in a bio: she has spoken at Harvard "
        f"University and she has walked into women's shelters and girls' mentoring programs "
        f"and delivered the same talk about not giving up. Different rooms, same conversation. "
        f"That combination -- Vogue editorial, national TV, Harvard, women's shelters -- is "
        f"genuinely rare and it is not a brand strategy. It is just who she is.\n\n"
        f"She has been featured in Vogue, appeared on NPR, TLC, the Jennifer Hudson Show, "
        f"Tamron Hall, and Fox News. She is the Co-Creator of the Institute for Body Image, "
        f"which trains medical professionals in inclusive care. And she has 52,000 followers "
        f"with a 4% engagement rate -- which means her audience is not just scrolling past her."
        f"{kit_line}"
        f"\nHappy to set up a call or send over more materials. What would be most helpful?"
        f"\n\nBest,\n{_sig('brand')}"
    )

    return {"to": lead["email"], "subject": subject, "body": body}


# ---------------------------------------------------------------------------
# CONFERENCE PROFILE (fireside chat / moderator / panel pitch)
# ---------------------------------------------------------------------------

CONFERENCE_SUBJECTS = [
    "Fireside chat or moderator inquiry | Danni Adams",
    "Speaker + moderator inquiry for {org}",
    "{org} -- session host or fireside guest",
    "Quick note about your {org} program",
    "Moderator / on-stage host inquiry | Danni Adams",
]


def build_conference_pitch(lead: dict) -> dict:
    """
    Pitch to conference organizers for fireside chat, moderator, or panel host roles.
    Different from the speaker pitch -- leads with hosting/interviewing credentials
    and positions her as someone who drives conversation, not just delivers one.

    lead keys: name, org (conference name), email, event_type (optional),
               conference_theme (optional), notes (optional)
    """
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your conference")
    event_type = (lead.get("event_type", "") or "").strip()
    theme = (lead.get("conference_theme", "") or "").strip()
    notes = (lead.get("notes", "") or "").strip()

    subject = random.choice(CONFERENCE_SUBJECTS).format(org=org)

    if theme:
        opener = f"I came across {org} and the focus on {theme.lower()} caught my attention."
    elif notes:
        opener = f"I came across {org} -- {notes.rstrip('.').lower()} -- and wanted to reach out."
    else:
        opener = f"I came across {org} and wanted to reach out about your program."

    role_line = f"I saw you have {event_type} on the program and thought this could be a fit.\n\n" if event_type else ""
    kit_line = f"\nFull background: {SPEAKER_KIT_URL}\n" if SPEAKER_KIT_URL else ""
    cal_line = f"\nCalendar: {SENDER_CALENDLY}\n" if SENDER_CALENDLY else ""

    body = (
        f"Hi {first},\n\n"
        f"{opener}\n\n"
        f"{role_line}"
        f"I am Danni Adams, a speaker and on-camera host based in Orlando, FL. I have hosted "
        f"the Social Icon Influencer Conference and the BET Beauty Brunch, and I have delivered "
        f"keynotes at Harvard University, Bethune-Cookman, and the Seminole Leadership Conference. "
        f"I also appear regularly on NPR, the Jennifer Hudson Show, Tamron Hall, and TLC -- so "
        f"I know how to hold a room and I know how to hold a conversation on camera or on stage.\n\n"
        f"I am reaching out specifically about a fireside chat or moderator role. I ask real "
        f"questions. I do not read from a script. And I have enough of my own credibility that "
        f"your guests will take the conversation seriously.\n\n"
        f"My background spans social media and storytelling, media literacy, community building, "
        f"and personal resilience. I have a Master's in Public Administration from the University "
        f"of North Florida and a background in sociology -- so I can hold my own in rooms that "
        f"expect substance, not just stage presence."
        f"{kit_line}"
        f"\nWould it be worth a 15-minute conversation about your program?"
        f"{cal_line}"
        f"\nBest,\n{_sig('speaker')}"
    )

    return {"to": lead["email"], "subject": subject, "body": body}


def build_conference_followup(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your conference")

    body = (
        f"Hi {first},\n\n"
        f"Following up on my note about {org}.\n\n"
        f"I know program planning moves fast and inboxes fill up. I just wanted to make sure "
        f"you had a chance to see it before your lineup is locked.\n\n"
        f"If there is a session, panel, or fireside slot where a host or conversation partner "
        f"would add value, I would love to talk. If the timing is off, totally understand.\n\n"
        f"Best,\n{_sig('speaker')}"
    )

    return {"to": lead["email"], "subject": f"Re: {original_subject}", "body": body}


# ---------------------------------------------------------------------------
# PODCAST PROFILE (guest pitch to podcast hosts and producers)
# ---------------------------------------------------------------------------

PODCAST_SUBJECTS = [
    "Guest pitch | Danni Adams",
    "Pitch: Harvard keynote. Women's shelters. Same talk.",
    "Guest pitch -- Danni Adams | @amapoundcake",
    "Pitch: A different kind of creator story for {podcast}",
    "Guest idea | Danni Adams | body image, representation, resilience",
]


def build_podcast_pitch(lead: dict) -> dict:
    """
    Guest pitch to podcast hosts, producers, and booking contacts.

    lead keys: name, org (podcast name), email, show_angle (optional),
               beat (optional topic/theme the show covers), notes (optional)
    """
    first = _first_name(lead.get("name", ""))
    podcast = lead.get("org", "your show")
    show_angle = (lead.get("show_angle", "") or "").strip()
    beat = (lead.get("beat", "") or "").strip()
    notes = (lead.get("notes", "") or "").strip()

    subject = random.choice(PODCAST_SUBJECTS).format(podcast=podcast)

    if beat:
        opener = f"I listen to {podcast} and your episodes on {beat} are exactly the kind of conversation I have been wanting to be part of."
    else:
        opener = f"I have been a listener of {podcast} and wanted to reach out directly about being a guest."

    angle_block = f"\n{show_angle}\n" if show_angle else ""

    if notes:
        notes_line = f"\n{notes.rstrip('.')}\n"
    else:
        notes_line = ""

    body = (
        f"Hi {first},\n\n"
        f"{opener}\n\n"
        f"Here is the thing that is hard to explain in a standard pitch: I have spoken at Harvard "
        f"University and I have walked into women's shelters and girls' mentoring programs and "
        f"delivered the same talk. Different rooms, same conversation -- how do you build something "
        f"real when nobody is coming to save you.\n\n"
        f"I am Danni Adams. I am an Orlando-based creator (@amapoundcake, 52K Instagram, 4% "
        f"engagement -- about five times the industry average), a speaker, and the Co-Creator of "
        f"the Institute for Body Image, which trains medical professionals in inclusive, "
        f"body-positive care. I have been featured in Vogue, appeared on NPR, the Jennifer Hudson "
        f"Show, Tamron Hall, and TLC, and I have spoken at Harvard, Bethune-Cookman, Full Sail, "
        f"and ongoing programs at women's shelters."
        f"{angle_block}"
        f"{notes_line}"
        f"\nThe topics I bring to a conversation: body image and media literacy, social media and "
        f"storytelling, representation and identity, building a brand or a career without "
        f"permission, and resilience -- the version that does not skip the hard parts.\n\n"
        f"I am a practiced guest. I know how to hold a conversation, not just talk at people.\n\n"
        f"Would you be open to having me on? Happy to send a one-sheet or hop on a quick call "
        f"first if that is easier.\n\n"
        f"Best,\n{_sig('brand')}"
    )

    return {"to": lead["email"], "subject": subject, "body": body}


def build_podcast_followup(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    podcast = lead.get("org", "your show")

    body = (
        f"Hi {first},\n\n"
        f"Just circling back on my guest pitch in case it got buried.\n\n"
        f"I know you get a lot of these. I am not following up because I think you missed it -- "
        f"I am following up because I genuinely think the conversation would be worth it for "
        f"your audience.\n\n"
        f"Harvard keynote to women's shelter, same talk. Body image advocate who also trained "
        f"doctors. Creator with a 4% engagement rate in a world full of inflated numbers. "
        f"There is a real story in there and I know how to tell it.\n\n"
        f"If the timing is wrong for {podcast} right now, no problem at all. But if there is "
        f"any interest, I would love to connect.\n\n"
        f"Best,\n{_sig('brand')}"
    )

    return {"to": lead["email"], "subject": f"Re: {original_subject}", "body": body}


# ---------------------------------------------------------------------------
# Dispatch: build any email by profile
# ---------------------------------------------------------------------------

def build_initial_email(lead: dict, profile: str = "speaker") -> dict:
    """Route to the correct initial email builder based on profile."""
    if profile == "brand":
        return build_brand_email(lead)
    elif profile == "press":
        return build_press_pitch(lead)
    elif profile == "podcast":
        return build_podcast_pitch(lead)
    elif profile == "conference":
        return build_conference_pitch(lead)
    return build_speaker_email(lead)


def build_followup_email(lead: dict, original_subject: str, profile: str = "speaker") -> dict:
    """Route to the correct follow-up builder based on profile."""
    if profile == "brand":
        return build_brand_followup(lead, original_subject)
    elif profile == "podcast":
        return build_podcast_followup(lead, original_subject)
    elif profile == "conference":
        return build_conference_followup(lead, original_subject)
    return build_speaker_followup(lead, original_subject)


def build_checkin_email(lead: dict, original_subject: str, profile: str = "speaker") -> dict:
    """30-day check-in (speaker profile only for now)."""
    return build_speaker_checkin(lead, original_subject)
