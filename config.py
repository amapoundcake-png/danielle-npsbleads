"""
config.py — Central configuration for Danielle's lead gen + outreach system.
All secrets are loaded from .env — nothing is hardcoded here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Sender identity
# ---------------------------------------------------------------------------
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "danniadamsprojects@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

SENDER_NAME = "Danielle Adams"
SENDER_TITLE = "Marketing and Donor Pipeline Consultant"
SENDER_LOCATION = "Orlando, FL"
SENDER_CALENDLY = "https://calendly.com/danniadamsprojects/30min"
SENDER_LINKEDIN = "https://www.linkedin.com/in/danielle1208adams/"

# ---------------------------------------------------------------------------
# Email body copy (used in email templates)
# ---------------------------------------------------------------------------
NONPROFIT_BODY = (
    "I work with nonprofits that are doing important work but are stretched thin on staff capacity.\n\n"
    "I help organizations build donor pipelines that encourage consistent giving, re-engage past supporters, "
    "and strengthen community relationships through outreach and follow-up systems that run without adding "
    "work for your team.\n\n"
    "Over the past 10 years I have helped Central Florida organizations grow their donor base and run "
    "campaigns that convert. I have a few ideas specific to {org} that I think could make a real difference."
)

SMALL_BIZ_BODY = (
    "Most small businesses rely on referrals, word of mouth, and manual follow-up to bring in new customers. "
    "It works until things get busy and opportunities start slipping through the cracks.\n\n"
    "I help small businesses build lead generation and follow-up systems that keep prospects engaged, "
    "bring in more customers, and free up the time you are spending chasing leads.\n\n"
    "Over the past 10 years I have worked with businesses across Central Florida on exactly this. "
    "I have a few ideas specific to {org} that I think could make a real difference."
)

# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")
SHEET_NAME = "Leads"

SHEET_COLUMNS = [
    "ID",
    "Name",
    "Org",
    "Email",
    "Industry",
    "Source",
    "Date Contacted",
    "Follow-up Due",
    "Follow-up Sent",
    "Check-in Due",
    "Check-in Sent",
    "Status",
    "Notes",
]

# ---------------------------------------------------------------------------
# Follow-up timing
# ---------------------------------------------------------------------------
FOLLOW_UP_DAYS_MIN = int(os.getenv("FOLLOW_UP_DAYS_MIN", 4))
FOLLOW_UP_DAYS_MAX = int(os.getenv("FOLLOW_UP_DAYS_MAX", 6))

# ---------------------------------------------------------------------------
# Email send-rate / scheduling
# ---------------------------------------------------------------------------
# Seconds between emails (converted from minutes)
EMAIL_SPACING_MIN_MINUTES = 8
EMAIL_SPACING_MAX_MINUTES = 25

EMAIL_SPACING_MIN_SECONDS = EMAIL_SPACING_MIN_MINUTES * 60
EMAIL_SPACING_MAX_SECONDS = EMAIL_SPACING_MAX_MINUTES * 60

# Daily send window — do not send outside 9am–5pm local time
SEND_WINDOW_START_HOUR = 9   # 9:00 AM
SEND_WINDOW_END_HOUR = 17    # 5:00 PM

# Daily new-lead target
DAILY_LEAD_TARGET = int(os.getenv("DAILY_LEAD_TARGET", 12))

# ---------------------------------------------------------------------------
# Optional integrations
# ---------------------------------------------------------------------------
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ---------------------------------------------------------------------------
# Scraping behaviour
# ---------------------------------------------------------------------------
REQUEST_DELAY_SECONDS = 2.5   # polite delay between page fetches
REQUEST_TIMEOUT = 15           # seconds before a request gives up

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

# ---------------------------------------------------------------------------
# Target locations (in priority order)
# ---------------------------------------------------------------------------
TARGET_LOCATIONS = [
    # Florida first
    "Orlando, FL",
    "Tampa, FL",
    "Jacksonville, FL",
    "Miami, FL",
    "St. Petersburg, FL",
    "Fort Lauderdale, FL",
    "Tallahassee, FL",
    # Alabama
    "Birmingham, AL",
    "Montgomery, AL",
    "Huntsville, AL",
    "Mobile, AL",
    # Georgia
    "Atlanta, GA",
    "Savannah, GA",
    "Augusta, GA",
    "Columbus, GA",
    # North Carolina
    "Charlotte, NC",
    "Raleigh, NC",
    "Durham, NC",
    "Greensboro, NC",
    "Asheville, NC",
    # Rest of the US
    "Houston, TX",
    "Dallas, TX",
    "Nashville, TN",
    "Memphis, TN",
    "New Orleans, LA",
    "Atlanta, GA",
    "Columbia, SC",
    "Richmond, VA",
    "Baltimore, MD",
    "Philadelphia, PA",
    "New York, NY",
    "Chicago, IL",
    "Los Angeles, CA",
    "Phoenix, AZ",
    "Denver, CO",
    "Seattle, WA",
    "Portland, OR",
    "Minneapolis, MN",
    "Kansas City, MO",
    "Detroit, MI",
]

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------
MANUAL_LEADS_CSV = "leads_manual.csv"
