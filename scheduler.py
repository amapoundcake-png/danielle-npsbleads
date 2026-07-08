"""
scheduler.py — Railway-hosted scheduler for Danni Adams outreach system.

Runs automatically on Railway 24/7. No laptop required.

Schedule:
  9:00 AM ET daily  — daily job runs in three parallel threads, one per inbox
  9:30 AM ET daily  — follow-up job
"""

import logging
import schedule
import threading
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


def _today_et() -> date:
    return datetime.now(tz=timezone.utc).astimezone(EASTERN).date()


# Days to skip new outreach (0=Mon, 6=Sun). Follows are exempt.
_SKIP_OUTREACH_DAYS = {6}  # Sunday
_HOLIDAY_BLACKOUT = {date(2026, 7, 3), date(2026, 7, 4)}  # July 4th weekend


def _ok_to_send_outreach() -> bool:
    today = _today_et()
    if today in _HOLIDAY_BLACKOUT:
        logger.info("Holiday blackout (%s) -- skipping new outreach.", today)
        return False
    if today.weekday() in _SKIP_OUTREACH_DAYS:
        logger.info("Outreach paused on %s (weekday=%d) -- skipping.", today, today.weekday())
        return False
    return True


def _run_in_thread(name: str, fn):
    """Run fn in a daemon thread so all three inboxes send in parallel."""
    t = threading.Thread(target=fn, name=name, daemon=True)
    t.start()
    return t


def run_followup():
    logger.info("=== SCHEDULER: starting follow-up job at %s ===", _now_et())
    try:
        from main import run_followup as _followup
        _followup()
    except Exception as exc:
        logger.error("Follow-up job failed: %s", exc)


# ---------------------------------------------------------------------------
# One-time personal sends — keyed by date so they only fire once
# ---------------------------------------------------------------------------

_PERSONALS_SENT_DATES: set = set()


def _run_personal_sends(send_date: date, module_name: str, run_fn_name: str = "run"):
    global _PERSONALS_SENT_DATES
    if _today_et() != send_date or send_date in _PERSONALS_SENT_DATES:
        return
    _PERSONALS_SENT_DATES.add(send_date)
    logger.info("=== SCHEDULER: starting personal sends (%s) at %s ===", module_name, _now_et())
    try:
        import importlib
        mod = importlib.import_module(module_name)
        getattr(mod, run_fn_name)()
    except Exception as exc:
        logger.error("Personal sends (%s) failed: %s", module_name, exc)


def run_monday_personals():
    _run_personal_sends(date(2026, 7, 6), "monday_personal_sends")


def run_wednesday_personals():
    _run_personal_sends(date(2026, 7, 8), "wednesday_personal_sends")


# ---------------------------------------------------------------------------
# Scheduled jobs — daily job runs in parallel threads per inbox group
# ---------------------------------------------------------------------------

def run_nonprofit():
    if not _ok_to_send_outreach():
        return
    logger.info("=== SCHEDULER: starting nonprofit job at %s ===", _now_et())
    try:
        from main import run_nonprofit as _nonprofit
        _nonprofit()
    except Exception as exc:
        logger.error("Nonprofit job failed: %s", exc)


def run_speaking():
    if not _ok_to_send_outreach():
        return
    logger.info("=== SCHEDULER: starting speaking job at %s ===", _now_et())
    try:
        from main import run_speaking as _speaking
        _speaking()
    except Exception as exc:
        logger.error("Speaking job failed: %s", exc)


def run_partnerships():
    if not _ok_to_send_outreach():
        return
    logger.info("=== SCHEDULER: starting partnerships job at %s ===", _now_et())
    try:
        from main import run_partnerships as _partnerships
        _partnerships()
    except Exception as exc:
        logger.error("Partnerships job failed: %s", exc)


def fire_all_daily():
    """Launch all three inbox jobs and personal sends as parallel threads."""
    if not _ok_to_send_outreach():
        return
    _run_in_thread("nonprofit", run_nonprofit)
    _run_in_thread("speaking", run_speaking)
    _run_in_thread("partnerships", run_partnerships)
    _run_in_thread("monday-personals", run_monday_personals)
    _run_in_thread("wednesday-personals", run_wednesday_personals)


# Railway runs UTC -- 9 AM ET = 13:00 UTC (EDT, UTC-4)
schedule.every().day.at("13:00").do(fire_all_daily)
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
