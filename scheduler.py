"""
scheduler.py — Railway-hosted scheduler for Danni Adams outreach system.

Runs automatically on Railway 24/7. No laptop required.

Schedule:
  9:00 AM ET daily  — daily job (find leads + send initial outreach)
  9:30 AM ET daily  — follow-up job (send follow-ups and 30-day check-ins)
"""

import logging
import schedule
import time
from datetime import datetime, date, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s -- %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

EASTERN = timezone(timedelta(hours=-4))


def _now_et() -> str:
    return datetime.now(tz=timezone.utc).astimezone(EASTERN).strftime("%Y-%m-%d %H:%M ET")


# Days to skip new outreach (0=Mon, 6=Sun). Follows are exempt.
_SKIP_OUTREACH_DAYS = {6}  # Sunday
_HOLIDAY_BLACKOUT = {date(2026, 7, 4)}  # July 4th


def _ok_to_send_outreach() -> bool:
    today = datetime.now(tz=timezone.utc).astimezone(EASTERN).date()
    if today in _HOLIDAY_BLACKOUT:
        logger.info("Holiday blackout (%s) — skipping new outreach.", today)
        return False
    if today.weekday() in _SKIP_OUTREACH_DAYS:
        logger.info("Outreach paused on %s (weekday=%d) — skipping.", today, today.weekday())
        return False
    return True


def run_daily():
    if not _ok_to_send_outreach():
        return
    logger.info("=== SCHEDULER: starting daily job at %s ===", _now_et())
    try:
        from main import run_daily as _daily
        _daily()
    except Exception as exc:
        logger.error("Daily job failed: %s", exc)


def run_followup():
    logger.info("=== SCHEDULER: starting follow-up job at %s ===", _now_et())
    try:
        from main import run_followup as _followup
        _followup()
    except Exception as exc:
        logger.error("Follow-up job failed: %s", exc)


# Schedule in Eastern time
# Railway runs UTC -- 9 AM ET = 13:00 UTC (EDT, UTC-4)
schedule.every().day.at("13:00").do(run_daily)
schedule.every().day.at("13:30").do(run_followup)

logger.info("Scheduler started. Daily job at 9:00 AM ET, follow-ups at 9:30 AM ET.")
logger.info("Current time: %s", _now_et())

import os
api_key = os.getenv("BREVO_API_KEY", "")
smtp_key = os.getenv("BREVO_SMTP_KEY", "")
logger.info("BREVO_API_KEY set: %s", bool(api_key))
logger.info("BREVO_SMTP_KEY set: %s", bool(smtp_key))

logger.info("Waiting for scheduled run times. No startup blast.")

while True:
    schedule.run_pending()
    time.sleep(30)
