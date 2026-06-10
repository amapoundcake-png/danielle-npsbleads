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
SENDER_TITLE = "Marketing & Campaign Operations Consultant"
SENDER_LOCATION = "Orlando, FL"
SENDER_LINKEDIN = "https://www.linkedin.com/in/danielleadams"   # update when live
SENDER_WEBSITE = "https://danielleadams.com"                    # update when live

# ---------------------------------------------------------------------------
# Services blurb (used in email templates)
# ---------------------------------------------------------------------------
SERVICES_BLURB = (
    "I help nonprofits and small businesses set up AI-powered marketing automations "
    "and build campaign strategies that actually convert."
)

NONPROFIT_SERVICES_BLURB = (
    "I help nonprofits set up AI-powered marketing automations including donor nurture sequences, "
    "volunteer recruitment campaigns, and impact reporting workflows so your team can "
    "focus on mission, not manual tasks."
)

SMALL_BIZ_SERVICES_BLURB = (
    "I help small businesses set up AI-powered marketing automations and build campaign "
    "strategies that drive real revenue, from lead-nurture sequences to social content "
    "pipelines and launch playbooks."
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
# File paths
# ---------------------------------------------------------------------------
MANUAL_LEADS_CSV = "leads_manual.csv"
