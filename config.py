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
SENDER_LINKEDIN = "https://www.linkedin.com/in/danielle1208adams/"

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
# Profile: POLITICAL (social justice orgs, left-leaning PACs, voting rights)
# Used for: NAACP chapters, voting rights orgs, progressive PACs, civic orgs
# Sends from: hello@danniadams.me
# Timing: Primary in 3 weeks, election 9 weeks after
# ---------------------------------------------------------------------------
POLITICAL_SUBJECTS = [
    "Communications support for {org}",
    "Voter outreach ideas for {org}",
    "A few ideas for {org} this election season",
    "Community engagement strategy for {org}",
]

POLITICAL_BODY = (
    "I'm <strong>Danielle Adams</strong>, an Orlando-based communications consultant with an MPA from UNF. "
    "I've spent my career building outreach systems and community engagement strategies for organizations "
    "that need to move people fast and with limited resources.<br><br>"
    "I led statewide communications campaigns as Senior Strategic Director at Florida For All, "
    "managed the <strong>City of Sanford Influencer Program</strong>, and co-created the "
    "<strong>Institute for Body Image</strong> from scratch with no marketing budget. "
    "I know how to build visibility and community trust in ways that actually show up at the table.<br><br>"
    "With the primary three weeks out and the general nine weeks behind it, I know your team is in "
    "execution mode. I work as a fractional strategic partner, which means I plug in fast, "
    "don't need a long onboarding, and focus on the outreach and communications work that moves voters "
    "and builds lasting community relationships.<br><br>"
    "I came across <strong>{org}</strong> and have a few specific ideas around voter outreach, "
    "community messaging, and digital visibility I'd love to share.<br><br>"
    "{cta}"
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

# ---------------------------------------------------------------------------
# Profile: NONPROFIT_SPEAKER (nonprofits as speaking/hosting/workshop clients)
# Used for: women's shelters, youth programs, mentoring orgs, community centers
# Sends from: speaking@danniadams.me
# Pitch: speaker + workshop facilitator + event host — money left open
# ---------------------------------------------------------------------------
NONPROFIT_SPEAKER_SUBJECTS = [
    "A fall idea for {org}",
    "Speaking or workshop idea for {org}",
    "An idea for {org} this season",
    "Could I bring something to {org}?",
    "Reaching out about {org}",
]

# Body uses {org}, {hook}, and {cta} placeholders.
# {hook} is generated per-lead in email_templates.py based on org notes/industry.
NONPROFIT_SPEAKER_BODY = (
    "I'm <strong>Danni Adams</strong>, an Orlando-based speaker, host, and workshop facilitator.<br><br>"
    "{hook}<br><br>"
    "I've spoken at <strong>Harvard University, the University of Ottawa, Bethune-Cookman University, "
    "and the Seminole Leadership Conference</strong>. My sessions cover storytelling, social media, "
    "resilience, and how to build a career when no one is handing you a runway. "
    "I also lead workshops and have hosted community events, panels, and brand experiences.<br><br>"
    "I would love to talk about what I could bring to "
    "<strong>{org}</strong>: whether that is a keynote, a workshop, or hosting your next event.<br><br>"
    "{cta}"
)

NONPROFIT_BODY = (
    "I'm <strong>Danielle Adams</strong>, an Orlando-based communications consultant with an MPA from UNF. "
    "Most recently I served as Senior Strategic Director at Florida For All, where I led statewide "
    "communications campaigns, managed stakeholder and creator partnerships, and oversaw content strategy "
    "across multiple initiatives.<br><br>"
    "I managed the <strong>City of Sanford Influencer Program</strong>, overseeing creator coordination, "
    "deliverables, and stakeholder communication end to end. "
    "I also co-created the <strong>Institute for Body Image</strong>, a program that trained medical providers in "
    "inclusive, body-positive care, built from scratch with no marketing budget. "
    "I've done donor visibility work, led speaker outreach, and run digital campaigns for organizations "
    "that couldn't afford to waste a single send. I know what it takes to reach people when you don't "
    "have a big team behind you.<br><br>"
    "I work with nonprofits as a fractional strategic partner, helping them grow their supporter base, "
    "build the community relationships that funders actually care about, and create outreach systems that "
    "keep the organization visible without adding to staff load.<br><br>"
    "I looked at what <strong>{org}</strong> is doing and have a few specific ideas I'd love to share "
    "around storytelling, visibility, and outreach.<br><br>"
    "{cta}"
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
    "to build a career when no one hands you the blueprint. I work with audiences who want to leave "
    "with something they can actually use.<br><br>"
    "I'd love to talk about what a session could look like for <strong>{org}</strong> this term or "
    "next season. Happy to send my full speaker kit if that helps."
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
    "<strong>@amapoundcake</strong>. I've appeared on "
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
# Profile: BRAND / PARTNERSHIPS
# Sends from: partnerships@danniadams.me
# Two versions: BRAND_ACTIVATION_BODY (G-A) and BRAND_CREATOR_BODY (G-B)
# Personalization: {reason} must be pulled from lead's notes field — real, specific.
# If notes are empty, email_templates.py flags the lead as NEEDS_PERSONALIZATION.
# ---------------------------------------------------------------------------
BRAND_SUBJECTS = [
    "An Orlando idea for {org}",
    "{org} x Orlando, a quick idea",
    "A creator idea for {org} in Orlando",
    "An idea for {org} in Orlando, worth a look?",
]

BRAND_CREATOR_SUBJECTS = [
    "Creator partnership inquiry, Danni Adams",
    "Danni Adams x {org}, a quick idea",
    "@amapoundcake, partnership inquiry",
    "Reaching out about a creator partnership, {org}",
]

# G-A: Brand activation — for brands where an Orlando creator event/experience makes sense
BRAND_ACTIVATION_BODY = (
    "I'm Danni Adams (<strong>@amapoundcake</strong>), a Central Florida creator with a background "
    "in marketing, events, and partnerships.<br><br>"
    "{reason}<br><br>"
    "I have an idea for how <strong>{org}</strong> could show up in Orlando with local creators, "
    "and I wanted to see if you'd be open to taking a look at a one-page concept."
)

# G-B: Creator partnership — for brands that want a creator, host, or personality, no event required
BRAND_CREATOR_BODY = (
    "I'm Danni Adams (<strong>@amapoundcake</strong>), a Central Florida creator, host, and media personality.<br><br>"
    "{reason}<br><br>"
    "I work with brands on content, partnerships, and creator activations. "
    "My audience is 74% women, ages 25-54, primarily in Orlando, Atlanta, Miami, and NYC. "
    "I've worked with T-Mobile, YITTY by Lizzo, and Hilton Hotels.<br><br>"
    "Happy to share my full media kit."
)

# Legacy alias — kept so existing imports don't break during transition
BRAND_BODY = BRAND_ACTIVATION_BODY

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
    "I'm <strong>Danni Adams</strong>, an actress, host, and media personality based in Orlando, FL, "
    "available nationally and internationally. I'm seeking theatrical and commercial representation.<br><br>"
    "<strong>Television and On-Camera:</strong> TLC (Cracked Addicts, 2024), The Jennifer Hudson Show, "
    "Tamron Hall, Fox News, The People's Court<br><br>"
    "<strong>Commercial:</strong> Sixt (principal, national), Leach Law Firm (principal, regional), "
    "T-Mobile (national)<br><br>"
    "<strong>Theater:</strong> Stage Struck at Lake Nona Arts (upcoming, role of Sam), "
    "American Immersive Theater<br><br>"
    "<strong>Modeling and Editorial:</strong> Vogue editorial, The Cut editorial, Miami Swim Week<br><br>"
    "<strong>Hosting:</strong> Social Icon Influencer Conference, BET Beauty Brunch<br><br>"
    "I'm happy to send my full reel, headshots, resume, and additional materials."
)

# ---------------------------------------------------------------------------
# Profile: VENUE_HOST (clubs, lounges, theaters, event spaces — hosting pitch)
# Used for: Orlando/Tampa venues, clubs, theaters, hotel event teams, comedy clubs
# Sends from: partnerships@danniadams.me
# Pitch: are you looking for a host? Funny, witty, experienced, hungry, local
# ---------------------------------------------------------------------------
VENUE_HOST_SUBJECTS = [
    "Are you looking for a host? Danni Adams",
    "Host inquiry, Danni Adams",
    "Orlando host available for {org}",
    "Hosting inquiry for {org}",
    "Danni Adams | Host and Emcee inquiry",
    "Looking for a host for your next event?",
    "A hosting question for {org}",
]

VENUE_HOST_BODY = (
    "I'm <strong>Danni Adams</strong>, an Orlando-based host, actress, and TV personality.<br><br>"
    "I hosted the <strong>Social Icon Influencer Conference</strong> and "
    "<strong>BET Beauty Brunch</strong>, and I've appeared on "
    "<strong>TLC, The Jennifer Hudson Show, and Tamron Hall</strong>. "
    "I can host, emcee, moderate panels, conduct interviews, and keep programming moving. "
    "whatever a room needs.<br><br>"
    "{event_hook}<br><br>"
    "I'm local, I'm prepared, and I don't need a long runway to be good in the room. "
    "I'm funny, I move fast, and I show up without creating extra work for your team.<br><br>"
    "If there's an upcoming event where a host could be useful, I'd love to be considered. "
    "Happy to send my reel and hosting materials."
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
EMAIL_SPACING_MIN_SECONDS = 90    # 90 seconds minimum between sends per inbox
EMAIL_SPACING_MAX_SECONDS = 180   # 3 minutes maximum — 3 inboxes rotating = ~20-40/hour

SEND_WINDOW_START_HOUR = 9
SEND_WINDOW_END_HOUR = 19  # 7 PM ET

DAILY_LEAD_TARGET = int(os.getenv("DAILY_LEAD_TARGET", 120))

# Per-inbox daily targets — scaled to hit 100+ per day across all three inboxes
NONPROFIT_DAILY_TARGET = int(os.getenv("NONPROFIT_DAILY_TARGET", 50))
SPEAKING_DAILY_TARGET  = int(os.getenv("SPEAKING_DAILY_TARGET", 40))
PARTNERSHIPS_DAILY_TARGET = int(os.getenv("PARTNERSHIPS_DAILY_TARGET", 35))

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
    # Florida (home base)
    "Orlando, FL", "Tampa, FL", "Jacksonville, FL", "Miami, FL",
    "Kissimmee, FL", "Sanford, FL", "Daytona Beach, FL", "Fort Lauderdale, FL",

    # Atlanta metro (within 20 miles)
    "Atlanta, GA", "Decatur, GA", "Marietta, GA", "Sandy Springs, GA",
    "Roswell, GA", "Smyrna, GA", "Alpharetta, GA", "College Park, GA",

    # New York metro (within 20 miles)
    "New York, NY", "Brooklyn, NY", "Bronx, NY", "Newark, NJ",
    "Hoboken, NJ", "Jersey City, NJ", "Yonkers, NY", "White Plains, NY",

    # Chicago metro (within 20 miles)
    "Chicago, IL", "Evanston, IL", "Oak Park, IL", "Naperville, IL",
    "Schaumburg, IL", "Aurora, IL", "Joliet, IL", "Cicero, IL",

    # Los Angeles metro (within 20 miles)
    "Los Angeles, CA", "Pasadena, CA", "Santa Monica, CA", "Long Beach, CA",
    "Burbank, CA", "Glendale, CA", "Inglewood, CA", "Culver City, CA",

    # Dallas metro (within 20 miles)
    "Dallas, TX", "Fort Worth, TX", "Irving, TX", "Plano, TX",
    "Garland, TX", "Arlington, TX", "Frisco, TX", "Carrollton, TX",

    # Houston metro (within 20 miles)
    "Houston, TX", "Sugar Land, TX", "Pearland, TX", "Pasadena, TX",
    "Katy, TX", "Baytown, TX", "Missouri City, TX", "Humble, TX",

    # Other major markets
    "Charlotte, NC", "Nashville, TN", "Washington, DC",
    "Philadelphia, PA", "Detroit, MI", "Baltimore, MD",
]

MANUAL_LEADS_CSV = "leads_manual.csv"
