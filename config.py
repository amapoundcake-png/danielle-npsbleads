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
    "I led statewide communications campaigns as Senior Strategic Director at Florida For All "
    "and co-created the <strong>Institute for Body Image</strong> from scratch with no marketing budget. "
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
    "I've been following the work <strong>{org}</strong> is doing, and I'd love to explore how I could "
    "contribute to your community this season.<br><br>"
    "I've spoken at <strong>Harvard University, the University of Ottawa, Bethune-Cookman University, "
    "and the Seminole Leadership Conference</strong>. My sessions cover storytelling, social media, "
    "resilience, and building a career when no one is handing you a runway. "
    "I also facilitate workshops and host community events, panels, and brand experiences.<br><br>"
    "I'd love to discuss what I could bring to <strong>{org}</strong>, whether that's a keynote, "
    "workshop, or hosting your next event.<br><br>"
    "{cta}"
)

NONPROFIT_BODY = (
    "I'm <strong>Danielle Adams</strong>, an Orlando-based communications consultant with an MPA from UNF. "
    "Most recently I served as Senior Strategic Director at Florida For All, where I led statewide "
    "communications campaigns, managed stakeholder and creator partnerships, and oversaw content strategy "
    "across multiple initiatives.<br><br>"
    "I co-created the <strong>Institute for Body Image</strong>, a program that trained medical providers in "
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
    "I hosted the <strong>Social Icon Influencer Conference</strong> and <strong>BET Beauty Brunch</strong>, "
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
# Profile: CORP_EVENT_PLANNER
# Corporate event planners, producers, experiential marketing companies
# Sends from: partnerships@danniadams.me
# ---------------------------------------------------------------------------
CORP_EVENT_PLANNER_SUBJECTS = [
    "Host inquiry: Danni Adams",
    "Comedic host available: Danni Adams",
    "Host and emcee inquiry: Danni Adams",
    "Hosting inquiry for {org}",
]

CORP_EVENT_PLANNER_BODY = (
    "I'm <strong>Danni Adams</strong>, a comedic host and emcee based in Orlando. "
    "I work corporate events, conferences, galas, and brand activations. "
    "What I bring to a room is energy and timing that makes the program feel like it was actually "
    "designed to be enjoyable, not just executed on schedule.<br><br>"
    "On camera, I've done principal roles in national campaigns for <strong>T-Mobile and Sixt</strong>, "
    "and I've appeared on <strong>TLC, the Jennifer Hudson Show, and the Tamron Hall Show</strong>. "
    "Live events are where I feel most at home.<br><br>"
    "If you have something coming up that needs a host who can read the room and keep the energy "
    "where it needs to be, I'd love to hear about it."
)

# ---------------------------------------------------------------------------
# Profile: HOTEL_VENUE
# Hotel event coordinators, private venue managers, holiday programming
# Sends from: partnerships@danniadams.me
# ---------------------------------------------------------------------------
HOTEL_VENUE_SUBJECTS = [
    "Host availability: corporate and private events",
    "Hosting inquiry for {org}",
    "Host and emcee inquiry: Danni Adams",
    "Available host for upcoming events at {org}",
]

HOTEL_VENUE_BODY = (
    "I'm <strong>Danni Adams</strong>, a comedic host and emcee based in Orlando. "
    "I specialize in corporate events, holiday parties, galas, and private functions. "
    "I keep programs on time and on tone while making the room feel like a place people chose "
    "to be, not a meeting they sat through.<br><br>"
    "My background spans national commercial work with <strong>T-Mobile and Sixt</strong>, "
    "featured appearances on <strong>TLC, the Jennifer Hudson Show, and the Tamron Hall Show</strong>, "
    "and live event hosting for brand activations and conferences.<br><br>"
    "Holiday event season is close. If <strong>{org}</strong> has programming coming up that needs "
    "a host, I'd love to get on your list.<br><br>"
    "Would it make sense to connect this week?"
)

# ---------------------------------------------------------------------------
# Profile: EVENT_AGENCY
# Talent agencies, entertainment agencies, experiential marketing agencies
# Sends from: partnerships@danniadams.me
# ---------------------------------------------------------------------------
EVENT_AGENCY_SUBJECTS = [
    "Hosting and brand talent inquiry: Danni Adams",
    "Talent inquiry: Danni Adams",
    "Host and on-camera talent: Danni Adams",
    "Reaching out about representation: Danni Adams",
]

EVENT_AGENCY_BODY = (
    "I came across <strong>{org}</strong> and wanted to reach out directly.<br><br>"
    "I'm <strong>Danni Adams</strong>, an Orlando-based host, on-camera talent, and creator. "
    "I have principal roles in national campaigns for <strong>T-Mobile and Sixt</strong> and "
    "featured appearances on <strong>TLC, the Jennifer Hudson Show, and the Tamron Hall Show</strong>. "
    "On the live event side, I've hosted brand activations and conferences. "
    "I've also built a community of more than 75,000 people across Instagram, TikTok, and Facebook "
    "through my work in entertainment, fashion, beauty, and culture.<br><br>"
    "My experience spans commercial campaigns, live hosting, on-camera appearances, and digital content, "
    "giving me several ways to contribute to the right project. "
    "I'm looking for representation that can connect all of it to the right opportunities.<br><br>"
    "My media kit is attached. Would you be open to a conversation?"
)

# ---------------------------------------------------------------------------
# Profile: ASSOC_ERG
# Professional associations (FPRA, PRSA, AMA) and employee resource groups
# Sends from: speaking@danniadams.me
# ---------------------------------------------------------------------------
ASSOC_ERG_SUBJECTS = [
    "Speaker inquiry: Danni Adams for {org}",
    "Speaking inquiry for {org}: Danni Adams",
    "Professional development speaker: Danni Adams",
    "Danni Adams | Speaker inquiry for {org}",
]

ASSOC_ERG_BODY = (
    "I'm <strong>Danni Adams</strong>, a speaker and workshop facilitator based in Orlando. "
    "I work with professional associations and ERGs on sessions about personal branding, "
    "career visibility, building an audience for your work, and navigating career transitions "
    "with intention.<br><br>"
    "I approach these sessions as thoughtful, practical conversations that give participants room "
    "to engage, ask questions, and connect the material to their own professional experiences.<br><br>"
    "Past engagements include <strong>Harvard University, the University of Ottawa, "
    "Bethune-Cookman University, and the Seminole Leadership Conference</strong>.<br><br>"
    "If you're planning your 2026 or 2027 programming, I'd love to hear what your members are "
    "working through.<br><br>"
    "<a href='{calendly}'>Grab time here</a> or reply with what works for you."
)

# ---------------------------------------------------------------------------
# Profile: CONFERENCE_MODERATOR
# Conference organizers, summits, award ceremonies seeking panel moderators
# Sends from: speaking@danniadams.me
# ---------------------------------------------------------------------------
CONFERENCE_MODERATOR_SUBJECTS = [
    "Moderator inquiry: {org}",
    "Panel moderator inquiry: Danni Adams",
    "Host and moderator inquiry for {org}",
    "Danni Adams | Moderator inquiry",
]

CONFERENCE_MODERATOR_BODY = (
    "I'm <strong>Danni Adams</strong>, a host and moderator based in Orlando. "
    "I've moderated panels at conferences and events nationally and I've spoken at "
    "<strong>Harvard University, the University of Ottawa, and Bethune-Cookman University</strong>.<br><br>"
    "Good moderation is harder than it looks. The job is to ask questions the audience actually "
    "wants answered, not the ones that are safe, give panelists space to share insights beyond "
    "their prepared remarks, and keep the conversation moving without making it feel rushed. "
    "That's what I do.<br><br>"
    "If you're building your moderator roster for <strong>{org}</strong>, I'd love to see what "
    "you're putting together.<br><br>"
    "<a href='{calendly}'>Grab time here</a>"
)

# ---------------------------------------------------------------------------
# Profile: MEDIA_LOCAL
# Local TV, publications, regional outlets seeking guests or contributors
# Sends from: hello@danniadams.me
# ---------------------------------------------------------------------------
MEDIA_LOCAL_SUBJECTS = [
    "Guest contributor inquiry: Danni Adams",
    "Media guest inquiry: Danni Adams",
    "Guest segment inquiry for {org}",
    "Reaching out about a guest opportunity at {org}",
]

MEDIA_LOCAL_BODY = (
    "I'm <strong>Danni Adams</strong>, an Orlando-based media personality, speaker, and creator. "
    "I've appeared on <strong>TLC, the Jennifer Hudson Show, the Tamron Hall Show, ABC, and "
    "Fox News</strong>. My topics span body image and representation to the creator economy, "
    "career reinvention, and what it actually takes to build something in public.<br><br>"
    "I'm focusing more of my work locally and would love to explore whether there's a fit with "
    "<strong>{org}</strong>, whether that's a guest segment, on-air commentary, or an occasional "
    "contributor role. I'm comfortable thinking on my feet, bringing a clear point of view, and "
    "making complex or personal topics accessible to a broad audience.<br><br>"
    "Would it make sense to connect?"
)

# ---------------------------------------------------------------------------
# Profile: PODCAST
# Podcasts covering entrepreneurship, media, culture, career development
# Sends from: hello@danniadams.me
# NOTE: [EPISODE_REFERENCE] placeholder must be filled before sending.
# ---------------------------------------------------------------------------
PODCAST_SUBJECTS = [
    "Guest pitch: Danni Adams",
    "Guest inquiry: Danni Adams",
    "Reaching out about a guest spot: Danni Adams",
]

PODCAST_BODY = (
    "I've been listening to <strong>{org}</strong>, and [EPISODE_REFERENCE] is what made me want "
    "to reach out. I think my background would make for a solid conversation.<br><br>"
    "I'm <strong>Danni Adams</strong>, a host, speaker, and creator based in Orlando. "
    "I've appeared on <strong>TLC, the Jennifer Hudson Show, and the Tamron Hall Show</strong>. "
    "I speak at universities including <strong>Harvard and the University of Ottawa</strong>. "
    "I co-founded the <strong>Institute for Body Image</strong>, a program training medical "
    "providers in inclusive care. And I've built a community of more than 75,000 people across "
    "social platforms by being a person on the internet, not a brand.<br><br>"
    "The conversation I'm most interested in having is about what it looks like to build a career "
    "without the traditional path, and what you actually have to give up to do it. "
    "I don't have a tidy answer. That's kind of the point.<br><br>"
    "If it sounds like a fit, I'd love to be on."
)

# ---------------------------------------------------------------------------
# Profile: BRAND_BEAUTY
# Beauty, haircare, and wig brands
# Sends from: partnerships@danniadams.me
# ---------------------------------------------------------------------------
BRAND_BEAUTY_SUBJECTS = [
    "Creator partnership inquiry: Danni Adams x {org}",
    "Partnership inquiry: Danni Adams x {org}",
    "@amapoundcake x {org}: creator partnership",
    "Creator partnership inquiry from Danni Adams",
]

BRAND_BEAUTY_BODY = (
    "I'm <strong>Danni Adams</strong>, the creator behind <strong>@amapoundcake</strong>. "
    "Beauty and hair are where my content lives most naturally, not because I was assigned "
    "that lane but because it's genuinely part of how I show up.<br><br>"
    "I've built a community of more than 75,000 people across Instagram, TikTok, and Facebook. "
    "I've done paid content with <strong>Morphe Beauty and BH Cosmetics</strong>, and the "
    "through-line in all of it is the same: I connect a product to how someone feels wearing it, "
    "not just how it photographs.<br><br>"
    "I'd love to explore what a partnership with <strong>{org}</strong> could look like. "
    "My media kit is attached."
)

# ---------------------------------------------------------------------------
# Profile: BRAND_FASHION
# Plus-size and inclusive fashion brands
# Sends from: partnerships@danniadams.me
# ---------------------------------------------------------------------------
BRAND_FASHION_SUBJECTS = [
    "Creator partnership inquiry: Danni Adams x {org}",
    "Partnership inquiry: Danni Adams x {org}",
    "@amapoundcake x {org}: fashion partnership",
    "Creator partnership inquiry from Danni Adams",
]

BRAND_FASHION_BODY = (
    "I'm <strong>Danni Adams</strong>, the creator behind <strong>@amapoundcake</strong>. "
    "I create fashion content that treats getting dressed like it has stakes, because for a "
    "lot of women, it does.<br><br>"
    "I've built a community of more than 75,000 people across Instagram, TikTok, and Facebook, "
    "with a strong foundation in plus-size and inclusive fashion. I've done paid partnerships "
    "with <strong>YITTY by Lizzo/Fabletics, ELOQUII, Fashion to Figure, and Chromat</strong>. "
    "What those partnerships share is an approach rooted in real storytelling and a genuine "
    "relationship with my community.<br><br>"
    "I'd love to explore a collaboration with <strong>{org}</strong>. "
    "My media kit is attached."
)

# Updated brand_general body for the new approved voice
BRAND_GENERAL_NEW_BODY = (
    "I'm <strong>Danni Adams</strong>, the creator behind <strong>@amapoundcake</strong>. "
    "I've been doing this long enough to know what a content partnership looks like when it "
    "works and what it looks like when it doesn't. The ones that work are the ones where the "
    "brand and the creator are genuinely talking to the same person.<br><br>"
    "I've built a community of more than 75,000 people across Instagram, TikTok, and Facebook "
    "through entertainment, fashion, beauty, and culture. Long-term partnerships with "
    "<strong>YITTY by Lizzo/Fabletics, T-Mobile, Hilton Hotels, Morphe Beauty, and "
    "BH Cosmetics</strong> have come from that same foundation: an audience that trusts "
    "the source.<br><br>"
    "I'd love to explore what a paid partnership with <strong>{org}</strong> could look like. "
    "My media kit is attached."
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

SEND_WINDOW_START_HOUR = 0
SEND_WINDOW_END_HOUR = 24

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

    # Southeast
    "Birmingham, AL", "Huntsville, AL", "Montgomery, AL",
    "Memphis, TN", "Knoxville, TN", "Chattanooga, TN",
    "New Orleans, LA", "Baton Rouge, LA",
    "Savannah, GA", "Augusta, GA", "Columbus, GA",
    "Columbia, SC", "Charleston, SC", "Greenville, SC",
    "Raleigh, NC", "Durham, NC", "Greensboro, NC", "Winston-Salem, NC",
    "Richmond, VA", "Norfolk, VA",
    "Louisville, KY", "Lexington, KY",
    "Jackson, MS", "Hattiesburg, MS",

    # Texas expansion
    "Austin, TX", "San Antonio, TX", "El Paso, TX",
    "San Marcos, TX", "Waco, TX", "Lubbock, TX",

    # Midwest expansion
    "Indianapolis, IN", "Fort Wayne, IN",
    "Columbus, OH", "Cleveland, OH", "Cincinnati, OH", "Akron, OH",
    "Detroit, MI", "Grand Rapids, MI", "Lansing, MI",
    "Minneapolis, MN", "Saint Paul, MN",
    "St. Louis, MO", "Kansas City, MO",
    "Milwaukee, WI", "Madison, WI",
    "Omaha, NE", "Lincoln, NE",

    # Northeast expansion
    "Boston, MA", "Cambridge, MA", "Springfield, MA",
    "Providence, RI", "Hartford, CT", "New Haven, CT",
    "Buffalo, NY", "Rochester, NY", "Albany, NY",
    "Pittsburgh, PA", "Allentown, PA",

    # West
    "Denver, CO", "Aurora, CO", "Colorado Springs, CO",
    "Phoenix, AZ", "Tucson, AZ", "Mesa, AZ", "Tempe, AZ",
    "Las Vegas, NV", "Henderson, NV",
    "Salt Lake City, UT",
    "Seattle, WA", "Tacoma, WA", "Spokane, WA",
    "Portland, OR",
    "Sacramento, CA", "Fresno, CA", "Bakersfield, CA",
    "San Francisco, CA", "Oakland, CA", "San Jose, CA",
    "San Diego, CA", "Riverside, CA",
    "Albuquerque, NM",
    "Anchorage, AK",
]

MANUAL_LEADS_CSV = "leads_manual.csv"
