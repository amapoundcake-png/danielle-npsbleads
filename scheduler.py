"""
scheduler.py — Railway-hosted scheduler for Danni Adams outreach system.

Runs automatically on Railway 24/7. No laptop required.

Schedule:
  9:00 AM ET daily  — daily job runs in three parallel threads, one per inbox
  9:30 AM ET daily  — follow-up job
"""

import logging
import os
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


# Days to skip new outreach. Empty = send every day including weekends.
_SKIP_OUTREACH_DAYS: set = set()
_HOLIDAY_BLACKOUT = {date(2026, 7, 3), date(2026, 7, 4)}  # July 4th weekend


def _ok_to_send_outreach() -> bool:
    if os.getenv("SENDS_PAUSED", "").strip().lower() in ("1", "true", "yes"):
        logger.info("SENDS_PAUSED is set -- skipping all outreach.")
        return False
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

def run_discover_and_send():
    """
    Primary daily pipeline: discover fresh orgs, qualify, then send to all
    Qualified + Approved leads (up to 70/day). Runs at 9 AM ET.
    Target: 60+ emails/day -> 300/week.
    """
    if not _ok_to_send_outreach():
        return
    logger.info("=== SCHEDULER: discover+send pipeline at %s ===", _now_et())
    try:
        from main import run_discover as _discover
        _discover()
    except Exception as exc:
        logger.error("Discover+send pipeline failed: %s", exc)


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
    """
    Launch the discover+send pipeline (primary) and personal sends.
    The discover job chains into send_approved, pipeline_followups,
    old-sheet followups, and the health check automatically.
    Old per-inbox jobs (nonprofit/speaking/partnerships) still run
    in parallel as a backup for any leads already in the old pipeline.
    Target: 60+ emails/day = 300/week.
    """
    if not _ok_to_send_outreach():
        return
    # Primary: new pipeline (discover -> qualify -> send 70/day)
    _run_in_thread("discover-and-send", run_discover_and_send)
    # Backup: old per-inbox jobs drain any remaining old-pipeline leads
    _run_in_thread("nonprofit", run_nonprofit)
    _run_in_thread("speaking", run_speaking)
    _run_in_thread("partnerships", run_partnerships)
    _run_in_thread("monday-personals", run_monday_personals)
    _run_in_thread("wednesday-personals", run_wednesday_personals)


# Railway runs UTC -- 9 AM ET = 13:00 UTC (EDT, UTC-4)
schedule.every().day.at("13:00").do(fire_all_daily)
schedule.every().day.at("13:30").do(run_followup)

# One-time makeup run for speaking@ -- Aug 20 only (pipeline was empty at 9 AM)
# 1 PM ET = 17:00 UTC
_SPEAKING_MAKEUP_DATE = date(2026, 8, 20)
_speaking_makeup_sent = False

def _run_speaking_makeup():
    global _speaking_makeup_sent
    if _today_et() != _SPEAKING_MAKEUP_DATE or _speaking_makeup_sent:
        return
    _speaking_makeup_sent = True
    logger.info("=== SCHEDULER: speaking makeup run at %s ===", _now_et())
    _run_in_thread("speaking-makeup", run_speaking)

schedule.every().day.at("17:00").do(_run_speaking_makeup)

# One-time afternoon makeup run -- Sep 14 only (Brave API was down at 9 AM)
# 3 PM ET = 19:00 UTC
_SEP14_MAKEUP_DATE = date(2026, 9, 14)
_sep14_makeup_sent = False

def _run_sep14_makeup():
    global _sep14_makeup_sent
    if _today_et() != _SEP14_MAKEUP_DATE or _sep14_makeup_sent:
        return
    _sep14_makeup_sent = True
    logger.info("=== SCHEDULER: Sep 14 afternoon makeup run at %s ===", _now_et())
    _run_in_thread("sep14-discover-send", run_discover_and_send)

schedule.every().day.at("19:00").do(_run_sep14_makeup)

# One-time makeup run for Sept 15 — 9 AM cron missed due to Notion 429 crash
# 3 PM ET = 19:00 UTC
_SEP15_MAKEUP_DATE = date(2026, 9, 15)
_sep15_makeup_sent = False

def _run_sep15_makeup():
    global _sep15_makeup_sent
    if _today_et() != _SEP15_MAKEUP_DATE or _sep15_makeup_sent:
        return
    _sep15_makeup_sent = True
    logger.info("=== SCHEDULER: Sep 15 afternoon makeup run at %s ===", _now_et())
    _run_in_thread("sep15-discover-send", run_discover_and_send)

schedule.every().day.at("19:00").do(_run_sep15_makeup)

# One-time 5 PM ET makeup run for Sept 15 — fallback if 3 PM run was missed
# 5 PM ET = 21:00 UTC
_SEP15_5PM_DATE = date(2026, 9, 15)
_sep15_5pm_sent = False

def _run_sep15_5pm():
    global _sep15_5pm_sent
    if _today_et() != _SEP15_5PM_DATE or _sep15_5pm_sent:
        return
    _sep15_5pm_sent = True
    logger.info("=== SCHEDULER: Sep 15 5 PM makeup run at %s ===", _now_et())
    _run_in_thread("sep15-5pm-discover-send", run_discover_and_send)

schedule.every().day.at("21:00").do(_run_sep15_5pm)

# One-time afternoon makeup run — Sep 24 (pipeline was exhausted at 9 AM)
# 4 PM ET = 20:00 UTC
_SEP24_MAKEUP_DATE = date(2026, 9, 24)
_sep24_makeup_sent = False

def _run_sep24_makeup():
    global _sep24_makeup_sent
    if _today_et() != _SEP24_MAKEUP_DATE or _sep24_makeup_sent:
        return
    _sep24_makeup_sent = True
    logger.info("=== SCHEDULER: Sep 24 afternoon makeup run at %s ===", _now_et())
    _run_in_thread("sep24-discover-send", run_discover_and_send)
    _run_in_thread("sep24-nonprofit", run_nonprofit)
    _run_in_thread("sep24-speaking", run_speaking)
    _run_in_thread("sep24-partnerships", run_partnerships)

schedule.every().day.at("20:00").do(_run_sep24_makeup)

# ---------------------------------------------------------------------------
# One-time makeup run — Sep 26 2026 (Notion was down Sep 25, leads lost)
# 3 PM ET = 19:00 UTC
# ---------------------------------------------------------------------------
_SEP26_MAKEUP_DATE = date(2026, 9, 26)
_sep26_makeup_sent = False

def _run_sep26_makeup():
    global _sep26_makeup_sent
    if _today_et() != _SEP26_MAKEUP_DATE or _sep26_makeup_sent:
        return
    _sep26_makeup_sent = True
    logger.info("=== SCHEDULER: Sep 26 makeup run — refilling pipeline after Notion outage ===")
    _run_in_thread("sep26-discover-send", run_discover_and_send)
    _run_in_thread("sep26-nonprofit", run_nonprofit)
    _run_in_thread("sep26-speaking", run_speaking)
    _run_in_thread("sep26-partnerships", run_partnerships)

schedule.every().day.at("19:00").do(_run_sep26_makeup)

# NOTE: Sat Sep 27 and Mon Sep 28 through Sat Oct 3 are covered by the daily
# 13:00 UTC job above — _SKIP_OUTREACH_DAYS is empty so the system runs every day.
# No additional entries needed.

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
