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

_HONORIFICS = {"dr.", "dr", "mr.", "mr", "ms.", "ms", "mrs.", "mrs", "prof.", "prof", "rev.", "rev"}

def _first_name(full_name: str) -> str:
    if not full_name or not full_name.strip():
        return "there"
    parts = full_name.strip().split()
    if len(parts) > 1 and parts[0].lower().rstrip(".") in _HONORIFICS:
        return parts[1]
    return parts[0]


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
    No DEI language. Academic credentials only included when lead has 'academic_hook' field.
    Fort Myers heritage only included when lead has 'fort_myers' field set to True.

    lead keys: name, org, email, notes (optional), event_type (optional),
               dept (optional), academic_hook (optional str -- custom credential line),
               fort_myers (optional bool)
    """
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")
    notes = (lead.get("notes", "") or "").strip()
    event_type = (lead.get("event_type", "") or "").strip()
    dept = (lead.get("dept", "") or "").strip()
    academic_hook = (lead.get("academic_hook", "") or "").strip()
    fort_myers = lead.get("fort_myers", False)

    subject = random.choice(SPEAKER_SUBJECTS).format(org=org)

    if notes:
        opener = f"I came across {org} and was really drawn to what you are building -- {notes.rstrip('.').lower()}."
    elif dept:
        opener = f"I am reaching out to the {dept} at {org} about a potential speaking engagement."
    else:
        opener = f"I came across {org} and wanted to reach out directly."

    event_line = f"I noticed you have {event_type} coming up and thought this might be a good fit.\n\n" if event_type else ""
    academic_line = f"\n{academic_hook}\n" if academic_hook else ""
    fort_myers_line = (
        f"\nI also have a personal connection to this region -- my great-great-great-grandfather, "
        f"Nelson Tillis, was the first Black settler in Fort Myers. He arrived on Christmas Day "
        f"1867, built a home on the Caloosahatchee, and constructed the first school for Black "
        f"children in Fort Myers on his property. This city is in my DNA.\n"
    ) if fort_myers else ""

    kit_line = f"\nSpeaker one-sheet: {SPEAKER_KIT_URL}\n" if SPEAKER_KIT_URL else ""
    cal_line = f"\nCalendar: {SENDER_CALENDLY}\n" if SENDER_CALENDLY else ""

    body = (
        f"Hi {first},\n\n"
        f"{opener}\n\n"
        f"{event_line}"
        f"I'm Danni Adams, a speaker based in Orlando, FL. I talk about the things students "
        f"are already thinking about but rarely hear addressed directly on a stage: how to "
        f"build a career and an identity in an era of information overload, economic "
        f"uncertainty, and constant noise about who you are supposed to be.\n\n"
        f"My topics include media literacy and the social media landscape, personal resilience "
        f"and self-determination, representation and identity, and storytelling as a professional "
        f"and civic skill. I can shape a keynote, a workshop, or a panel conversation depending "
        f"on what your audience needs most right now.\n\n"
        f"I have spoken at Harvard University, the University of Ottawa, Full Sail University, "
        f"Bethune-Cookman, and the Seminole Leadership Conference. I have been featured on NPR, "
        f"the Jennifer Hudson Show, Tamron Hall, TLC, and in Vogue. I am also the Co-Creator "
        f"of the Institute for Body Image, which trains medical professionals in inclusive care -- "
        f"so the work I do on stage is connected to real institutional change."
        f"{academic_line}"
        f"{fort_myers_line}"
        f"{kit_line}"
        f"\nWould it make sense to connect for 20 minutes?"
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
        context_line = f"I have been following {org} -- {notes.rstrip('.').lower()} -- and wanted to reach out directly.\n\n"
    else:
        context_line = ""

    angle_line = f"\n{angle}\n" if angle else ""
    kit_line = f"\nFull brand kit: {BRAND_KIT_URL}\n" if BRAND_KIT_URL else ""

    body = (
        f"Hi {first},\n\n"
        f"{context_line}"
        f"There is a woman {org} has been trying to reach. She is Black, she is plus-size, "
        f"she is 25 to 54, she lives in the South, and she does not trust brands that do not "
        f"see her. She has disposable income and she spends it with people she believes. "
        f"I am her. And I am also the person she listens to.\n\n"
        f"My name is Danni Adams. I am the creator behind @amapoundcake -- 52,000 followers "
        f"across Instagram and TikTok, audience concentrated in Orlando, Atlanta, Miami, and "
        f"New York. I have been featured in Vogue, appeared on NPR, the Jennifer Hudson Show, "
        f"Tamron Hall, and TLC. I have partnered with T-Mobile, Hilton Hotels, Sixt, YITTY "
        f"by Lizzo/Fabletics, and Morphe Beauty. I am also the Co-Creator of the Institute "
        f"for Body Image, which trains medical professionals in inclusive care -- because "
        f"representation is not a campaign for me, it is the actual work."
        f"{angle_line}"
        f"\nI am not pitching you a placement. I am telling you there is a conversation "
        f"happening in a room you have been trying to get into, and I am already in it."
        f"{kit_line}"
        f"\nWorth 15 minutes?\n\n"
        f"Best,\n{_sig('brand')}"
    )

    return {"to": lead["email"], "subject": subject, "body": body}


def build_brand_followup(lead: dict, original_subject: str) -> dict:
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your brand")

    body = (
        f"Hi {first},\n\n"
        f"Following up in case my first note got buried.\n\n"
        f"The short version: the woman {org} has been trying to reach already trusts me. "
        f"I am not asking you to build that -- I am inviting you into something that exists.\n\n"
        f"If the timing is off, no problem. But if there is any interest, even a 15-minute "
        f"call would be worth it.\n\n"
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
# FORT MYERS HERITAGE PITCH
# Use for: LCBHS, VisitFortMyers, WGCU, Gulfshore Life, FGCU, Fort Myers CRA
# The heritage is the LEAD here -- not the footnote.
# ---------------------------------------------------------------------------

FORT_MYERS_SUBJECTS = [
    "My great-great-great-grandfather built the first school for Black children in Fort Myers",
    "Nelson Tillis was the first Black settler in Fort Myers. He was my family.",
    "A conversation about Fort Myers, Nelson Tillis, and why I think we should talk",
    "Coming home | Danni Adams | descendant of Nelson Tillis",
]


def build_fort_myers_pitch(lead: dict) -> dict:
    """
    Heritage pitch specifically for Fort Myers organizations.
    The Tillis connection is the entire point -- leads with it.

    lead keys: name, org, email, org_angle (optional -- what specifically they do/care about)
    """
    first = _first_name(lead.get("name", ""))
    org = lead.get("org", "your organization")
    org_angle = (lead.get("org_angle", "") or "").strip()

    subject = random.choice(FORT_MYERS_SUBJECTS)

    angle_line = f"\n{org_angle}\n" if org_angle else ""
    kit_line = f"\nFull background: {SPEAKER_KIT_URL}\n" if SPEAKER_KIT_URL else ""
    cal_line = f"\nCalendar: {SENDER_CALENDLY}\n" if SENDER_CALENDLY else ""

    body = (
        f"Hi {first},\n\n"
        f"My name is Danni Adams. My great-great-great-grandfather, Nelson Tillis, was the "
        f"first Black settler in Fort Myers. He arrived on Christmas Day 1867, built 110 acres "
        f"on the north bank of the Caloosahatchee under the Homestead Act, hauled material for "
        f"the first Fort Myers Courthouse, and built the first school for Black children in Fort "
        f"Myers on his own property -- because no one else was going to do it. He fished with "
        f"Thomas Edison. His children played on the Edison estate. He is Mural 11 on the "
        f"Caloosahatchee. There is a street named after him.\n\n"
        f"I found out about this when I started researching my family history. I am based in "
        f"Orlando now, but Fort Myers is in my DNA.\n\n"
        f"I am a speaker, content creator, and body image advocate. I have spoken at Harvard "
        f"University, appeared on NPR, the Jennifer Hudson Show, Tamron Hall, and TLC, been "
        f"featured in Vogue, and built an audience of 52,000 people on Instagram with a 4% "
        f"engagement rate -- nearly five times the industry average. My audience is 74% women, "
        f"ages 25 to 54, based in Orlando, Atlanta, Miami, and New York."
        f"{angle_line}"
        f"\nI think there is a story worth telling together. A descendant of the first Black "
        f"settler in Fort Myers -- a man who built a school when the city would not -- comes "
        f"home with a platform, a credential, and a reason to show up. That story reaches "
        f"people and it belongs to Fort Myers."
        f"{kit_line}"
        f"\nI would love to find 20 minutes to talk about what that could look like."
        f"{cal_line}"
        f"\nBest,\n{_sig('speaker')}"
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
        f"of North Florida and a BA in Sociology from Florida State University -- so I can hold "
        f"my own in rooms that expect substance, not just stage presence."
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
    elif profile == "fort_myers":
        return build_fort_myers_pitch(lead)
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
