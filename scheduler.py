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
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s -- %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

EASTERN = timezone(timedelta(hours=-4))


def _now_et() -> str:
    return datetime.now(tz=timezone.utc).astimezone(EASTERN).strftime("%Y-%m-%d %H:%M ET")


def run_daily():
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

while True:
    schedule.run_pending()
    time.sleep(30)
