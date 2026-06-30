"""
config.py — Central configuration for Danni Adams outreach system.
All secrets are loaded from .env — nothing is hardcoded here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Brevo SMTP
# ---------------------------------------------------------------------------
BREVO_SMTP_HOST = "smtp-relay.brevo.com"
BREVO_SMTP_PORT = 587
BREVO_SMTP_LOGIN = os.getenv("BREVO_LOGIN", "hello@danniadams.me")
BREVO_SMTP_KEY = os.getenv("BREVO_SMTP_KEY", "")

# ---------------------------------------------------------------------------
# Sender inboxes
# ---------------------------------------------------------------------------
SENDER_NAME = "Danni Adams"
SENDER_EMAIL_HELLO = os.getenv("SENDER_EMAIL_HELLO", "hello@danniadams.me")
SENDER_EMAIL_SPEAKING = os.getenv("SENDER_EMAIL_SPEAKING", "speaking@danniadams.me")
SENDER_EMAIL_PARTNERSHIPS = os.getenv("SENDER_EMAIL_PARTNERSHIPS", "partnerships@danniadams.me")

SENDER_LOCATION = "Orlando, FL"
SENDER_CALENDLY = "https://calendly.com/danielleadamsfl/15min"
SENDER_INSTAGRAM = "https://instagram.com/amapoundcake"

# ---------------------------------------------------------------------------
# Profile: WARMUP
# Used for: sends to own inboxes and warm personal contacts
# Sends from: hello@danniadams.me
# ---------------------------------------------------------------------------
WARMUP_BODY = (
    "Just a heads up, I'm officially moving everything over to hello@danniadams.me going forward. "
    "Same person, cleaner setup. Update your records if you need to.\n\n"
    "Talk soon,\nDanni"
)

# ---------------------------------------------------------------------------
# Profile: NONPROFIT / SPEAKING (nonprofits, shelters, mentoring programs)
# Used for: community orgs, women's shelters, youth programs
# Sends from: speaking@danniadams.me
# ---------------------------------------------------------------------------
NONPROFIT_SUBJECTS = [
    "A few ideas for {org}",
    "Outreach help for {org}",
    "Quick idea for {org}",
    "Outreach and visibility for {org}",
]

NONPROFIT_BODY = (
    "I'm <strong>Danni Adams</strong>, an Orlando-based communications consultant with an MPA from UNF. "
    "Most recently I served as Senior Project Manager and Strategic Partnerships, where I led statewide "
    "communications campaigns, managed stakeholder and creator partnerships, and oversaw content strategy "
    "across multiple initiatives.<br><br>"
    "I managed the <strong>City of Sanford Influencer Program</strong>, overseeing creator coordination, "
    "deliverables, and stakeholder communication end to end. "
    "I also co-created the <strong>Institute for Body Image</strong>, a program that trained medical providers in "
    "inclusive, body-positive care, built from scratch with no marketing budget. "
    "I've done donor visibility work, led speaker outreach, and run digital campaigns for mission-driven "
    "organizations. I know what it takes to reach people when you don't have a big team behind you.<br><br>"
    "I now work with nonprofits as a fractional strategic partner, helping them grow their supporter base, "
    "build the community relationships that funders actually care about, and create outreach systems that "
    "keep the organization visible without adding to staff load.<br><br>"
    "I came across <strong>{org}</strong> and have a few specific ideas I'd love to share "
    "around storytelling, visibility, and outreach.<br><br>"
    "Worth a 20-minute call? <a href='{calendly}'>Grab time here.</a>"
)

# ---------------------------------------------------------------------------
# Profile: SPEAKER (universities, conferences, DEI, corporate)
# Sends from: speaking@danniadams.me
# ---------------------------------------------------------------------------
SPEAKER_SUBJECTS = [
    "Speaker inquiry for {org}",
    "Danni Adams | Speaker inquiry",
    "Reaching out about a speaker opportunity at {org}",
    "{org} + Danni Adams | Speaking",
]

SPEAKER_BODY = (
    "I'm <strong>Danni Adams</strong>, a speaker, media personality, and Co-Creator of the "
    "<strong>Institute for Body Image</strong>, a professional development program training medical "
    "providers in inclusive, body-positive care.<br><br>"
    "I've spoken at <strong>Harvard University, the University of Ottawa, Full Sail University, "
    "Bethune-Cookman University, and the Seminole Leadership Conference</strong>, and I've been "
    "featured on <strong>The Jennifer Hudson Show and Tamron Hall</strong>. My sessions cover "
    "media literacy, digital safety, body image, the creator economy, and what it actually takes "
    "to build a platform and a career with intention. I work with audiences who want to leave "
    "with something they can actually use.<br><br>"
    "I'd love to talk about what a session could look like for <strong>{org}</strong> this term or "
    "next season. Happy to send my full speaker kit if that's helpful."
)

# ---------------------------------------------------------------------------
# Profile: CREATOR (creator conferences, chambers, incubators, biz accelerators)
# Sends from: speaking@danniadams.me
# ---------------------------------------------------------------------------
CREATOR_SUBJECTS = [
    "Speaker inquiry, Danni Adams",
    "Danni Adams | Creator economy speaker",
    "Speaking opportunity at {org}, Danni Adams",
    "{org} + Danni Adams | Speaker",
]

CREATOR_BODY = (
    "I'm <strong>Danni Adams</strong>, actress, media personality, and creator behind "
    "<strong>@amapoundcake</strong> (52K followers, 4% engagement). I've appeared on "
    "<strong>TLC, The Jennifer Hudson Show, and Tamron Hall</strong>, been featured in "
    "<strong>Vogue</strong>, and built brand partnerships with T-Mobile, YITTY by Lizzo, "
    "and Hilton Hotels.<br><br>"
    "I managed the <strong>City of Sanford Influencer Program</strong>, hosted the "
    "<strong>Social Icon Influencer Conference</strong> and <strong>BET Beauty Brunch</strong>, "
    "and I've spoken at Harvard University, the University of Ottawa, and the Seminole "
    "Leadership Conference. I built all of it without an agent, a PR team, or a budget.<br><br>"
    "My sessions cover the creator economy, personal brand building, media literacy, digital "
    "safety, and what it actually takes to build real influence. I speak to audiences who are "
    "ready to stop waiting for permission.<br><br>"
    "I'd love to talk about what a session could look like for <strong>{org}</strong>. "
    "Happy to send my speaker kit."
)

# ---------------------------------------------------------------------------
# Profile: BRAND / PARTNERSHIPS (brands, PR firms, UGC, campaigns)
# Sends from: partnerships@danniadams.me
# ---------------------------------------------------------------------------
BRAND_SUBJECTS = [
    "{org} + Danni Adams, a quick idea",
    "Reaching out about {org} x @amapoundcake",
    "Partnership idea for {org}",
    "{org} | Danni Adams",
]

BRAND_BODY = (
    "I'm <strong>Danni Adams</strong>, an actress, media personality, and UGC creator behind "
    "<strong>@amapoundcake</strong>. I create content that feels like a real person talking, because it is. "
    "Vogue, TLC, The Jennifer Hudson Show, Tamron Hall, T-Mobile, YITTY by Lizzo, Hilton Hotels. "
    "I've been in those rooms, and I bring that same energy to every brand I work with.<br><br>"
    "My audience is real and they show up. 74% women, ages 25-54, top markets Orlando, Atlanta, Miami, and NYC. "
    "They trust me. That's what I bring to a partnership.<br><br>"
    "I have a specific idea for <strong>{org}</strong> I'd love to share. It's a quick conversation."
)

# ---------------------------------------------------------------------------
# Profile: ENTERTAINMENT / TALENT (agencies, casting directors)
# Sends from: partnerships@danniadams.me
# ---------------------------------------------------------------------------
TALENT_SUBJECTS = [
    "Actress and Host, Danni Adams",
    "Danni Adams | Actress, Model, Talent",
    "Danni Adams | Actress inquiry",
    "Talent inquiry, Danni Adams",
]

TALENT_BODY = (
    "I'm <strong>Danni Adams</strong>, an actress, model, host, and media personality based in Orlando, FL, "
    "available nationally and internationally.<br><br>"
    "Recent credits include <strong>TLC (Cracked Addicts, 2024)</strong>, The Jennifer Hudson Show, "
    "Tamron Hall, Fox News, The People's Court, a Vogue editorial feature, The Cut, Miami Swim Week, "
    "and principal roles in national commercials for <strong>Sixt</strong> and regional spots for "
    "Leach Law Firm. On stage, I have an upcoming role as Sam in <em>Stage Struck</em> at Lake Nona Arts "
    "and I've performed with American Immersive Theater.<br><br>"
    "I'm actively seeking representation. Happy to send my full reel, headshots, and resume."
)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ---------------------------------------------------------------------------
# Notion logging
# ---------------------------------------------------------------------------
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# ---------------------------------------------------------------------------
# Follow-up timing
# ---------------------------------------------------------------------------
FOLLOW_UP_DAYS_MIN = int(os.getenv("FOLLOW_UP_DAYS_MIN", 4))
FOLLOW_UP_DAYS_MAX = int(os.getenv("FOLLOW_UP_DAYS_MAX", 6))

# ---------------------------------------------------------------------------
# Email send-rate / scheduling
# ---------------------------------------------------------------------------
EMAIL_SPACING_MIN_SECONDS = 45 * 60   # 45 minutes
EMAIL_SPACING_MAX_SECONDS = 90 * 60   # 90 minutes

SEND_WINDOW_START_HOUR = 9
SEND_WINDOW_END_HOUR = 17

DAILY_LEAD_TARGET = int(os.getenv("DAILY_LEAD_TARGET", 12))

# ---------------------------------------------------------------------------
# Scraping behaviour
# ---------------------------------------------------------------------------
REQUEST_DELAY_SECONDS = 2.5
REQUEST_TIMEOUT = 15

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": BROWSER_USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TARGET_LOCATIONS = [
    "Orlando, FL", "Tampa, FL", "Jacksonville, FL", "Miami, FL",
    "Atlanta, GA", "Charlotte, NC", "Nashville, TN", "New York, NY",
]

MANUAL_LEADS_CSV = "leads_manual.csv"
