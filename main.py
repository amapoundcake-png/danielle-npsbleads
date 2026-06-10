"""
main.py — Orchestrator for Danielle's lead gen + cold email outreach system.

Usage:
  python main.py daily     — find new leads and send initial outreach emails
  python main.py followup  — send follow-up emails to leads that haven't replied
  python main.py status    — print a summary from Google Sheets
"""

import logging
import sys
from datetime import datetime

from config import DAILY_LEAD_TARGET, GMAIL_APP_PASSWORD, GMAIL_ADDRESS
from email_templates import build_initial_email, build_followup_email
from email_sender import send_email
from lead_finder import gather_all_leads
from sheets_logger import (
    create_sheet_if_missing,
    log_new_lead,
    get_leads_needing_followup,
    mark_followup_sent,
    get_summary,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("outreach.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------

def _preflight() -> bool:
    """Validate that essential credentials are available before running."""
    ok = True
    if not GMAIL_APP_PASSWORD:
        logger.error("GMAIL_APP_PASSWORD is not set in .env")
        ok = False
    if not GMAIL_ADDRESS:
        logger.error("GMAIL_ADDRESS is not set in .env")
        ok = False
    return ok


# ---------------------------------------------------------------------------
# Daily job: find leads + send initial outreach
# ---------------------------------------------------------------------------

def run_daily() -> None:
    logger.info("=== DAILY JOB STARTED — %s ===", datetime.now().strftime("%Y-%m-%d %H:%M"))

    if not _preflight():
        logger.error("Preflight failed. Aborting daily job.")
        sys.exit(1)

    create_sheet_if_missing()

    # 1. Scrape leads
    logger.info("Gathering leads (target: %d)...", DAILY_LEAD_TARGET)
    leads = gather_all_leads(target=DAILY_LEAD_TARGET)

    if not leads:
        logger.warning("No new leads found today. Check sources or manual CSV.")
        return

    logger.info("Found %d new leads to contact.", len(leads))

    # 2. Send emails and log each one
    sent_count = 0
    failed_count = 0

    for lead in leads:
        try:
            email_data = build_initial_email(lead)
        except Exception as exc:
            logger.error(
                "Failed to build email for %s <%s>: %s",
                lead.get("org"),
                lead.get("email"),
                exc,
            )
            failed_count += 1
            continue

        success = send_email(
            to_address=email_data["to"],
            subject=email_data["subject"],
            body=email_data["body"],
            respect_rate_limit=True,
        )

        if success:
            try:
                log_new_lead(lead)
            except Exception as exc:
                logger.error(
                    "Email sent but failed to log %s to sheet: %s",
                    lead.get("email"),
                    exc,
                )
            sent_count += 1
        else:
            failed_count += 1

    logger.info(
        "=== DAILY JOB COMPLETE — sent: %d, failed: %d ===",
        sent_count,
        failed_count,
    )


# ---------------------------------------------------------------------------
# Follow-up job
# ---------------------------------------------------------------------------

def run_followup() -> None:
    logger.info("=== FOLLOW-UP JOB STARTED — %s ===", datetime.now().strftime("%Y-%m-%d %H:%M"))

    if not _preflight():
        logger.error("Preflight failed. Aborting follow-up job.")
        sys.exit(1)

    create_sheet_if_missing()

    # 1. Fetch leads needing follow-up
    leads = get_leads_needing_followup()

    if not leads:
        logger.info("No leads due for follow-up today.")
        return

    logger.info("%d lead(s) due for follow-up.", len(leads))

    sent_count = 0
    failed_count = 0

    for row in leads:
        lead = {
            "name": row.get("Name", ""),
            "org": row.get("Org", ""),
            "email": row.get("Email", ""),
            "industry": row.get("Industry", ""),
            "notes": row.get("Notes", ""),
        }

        if not lead["email"]:
            continue

        # Reconstruct the original subject from the Notes column if available,
        # otherwise fall back to a generic subject.
        original_subject = row.get("Notes", "") or f"Quick idea for {lead['org']}"

        try:
            email_data = build_followup_email(lead, original_subject)
        except Exception as exc:
            logger.error(
                "Failed to build follow-up for %s: %s", lead.get("email"), exc
            )
            failed_count += 1
            continue

        success = send_email(
            to_address=email_data["to"],
            subject=email_data["subject"],
            body=email_data["body"],
            respect_rate_limit=True,
        )

        if success:
            try:
                mark_followup_sent(lead["email"])
            except Exception as exc:
                logger.error(
                    "Follow-up sent but failed to update sheet for %s: %s",
                    lead["email"],
                    exc,
                )
            sent_count += 1
        else:
            failed_count += 1

    logger.info(
        "=== FOLLOW-UP JOB COMPLETE — sent: %d, failed: %d ===",
        sent_count,
        failed_count,
    )


# ---------------------------------------------------------------------------
# Status command
# ---------------------------------------------------------------------------

def run_status() -> None:
    create_sheet_if_missing()
    try:
        summary = get_summary()
    except Exception as exc:
        logger.error("Could not fetch summary from sheet: %s", exc)
        sys.exit(1)

    print("\n" + "=" * 50)
    print("  OUTREACH DASHBOARD")
    print("=" * 50)
    print(f"  Total leads in sheet : {summary['total']}")
    print()
    print("  Breakdown by status:")
    for status, count in sorted(summary["by_status"].items()):
        print(f"    {status:<20} {count}")
    print()
    print(f"  Follow-ups due today : {summary['pending_followup']}")
    print("=" * 50 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

COMMANDS = {
    "daily": run_daily,
    "followup": run_followup,
    "status": run_status,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python main.py [{' | '.join(COMMANDS)}]")
        sys.exit(1)

    command = sys.argv[1]
    logger.info("Running command: %s", command)
    COMMANDS[command]()
