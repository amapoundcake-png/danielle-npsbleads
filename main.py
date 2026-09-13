"""
main.py — Orchestrator for Danielle's lead gen + cold email outreach system.

Usage:
  python main.py daily     — find new leads and send initial outreach emails
  python main.py followup  — send follow-up emails to leads that haven't replied
  python main.py status    — print a summary from Notion
  python main.py discover  — DISCOVER → QUALIFY → STAGE IN NOTION only
                             (no email lookup, no verification, no sending)
"""

import logging
import os
import sys
from datetime import datetime

from config import DAILY_LEAD_TARGET, BREVO_SMTP_KEY, NONPROFIT_DAILY_TARGET, SPEAKING_DAILY_TARGET, PARTNERSHIPS_DAILY_TARGET
from email_templates import build_initial_email, build_followup_email, build_checkin_email
from email_sender import send_email
from lead_finder import gather_all_leads, gather_leads_for_profiles, discover_orgs_for_pipeline, _todays_venue_locations
from notion_logger import (
    create_sheet_if_missing,
    log_new_lead,
    get_leads_needing_followup,
    mark_followup_sent,
    get_leads_needing_checkin,
    mark_checkin_sent,
    get_summary,
)

# notion_pipeline and email_lookup are imported lazily inside run_discover / run_send_approved

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
    if not BREVO_SMTP_KEY:
        logger.error("BREVO_SMTP_KEY is not set in .env")
        ok = False
    return ok


# ---------------------------------------------------------------------------
# Daily job: find leads + send initial outreach
# ---------------------------------------------------------------------------

def _send_leads(leads: list, job_name: str) -> None:
    """Send a list of leads and log each one."""
    sent_count = 0
    failed_count = 0
    for lead in leads:
        try:
            email_data = build_initial_email(lead)
        except Exception as exc:
            logger.error("Failed to build email for %s <%s>: %s", lead.get("org"), lead.get("email"), exc)
            failed_count += 1
            continue
        success = send_email(
            to_address=email_data["to"],
            subject=email_data["subject"],
            body=email_data["body"],
            profile=email_data.get("profile", "nonprofit"),
            is_html=email_data.get("is_html", False),
            respect_rate_limit=True,
            org=lead.get("org", ""),
        )
        if success:
            try:
                log_new_lead(lead)
            except Exception as exc:
                logger.error("Email sent but failed to log %s: %s", lead.get("email"), exc)
            sent_count += 1
        else:
            failed_count += 1
    logger.info("=== %s COMPLETE — sent: %d, failed: %d ===", job_name, sent_count, failed_count)


def run_nonprofit() -> None:
    """12 emails from hello@danniadams.me to nonprofit leads."""
    logger.info("=== NONPROFIT JOB STARTED ===")
    if not _preflight():
        return
    create_sheet_if_missing()
    leads = gather_leads_for_profiles(["nonprofit"], target=NONPROFIT_DAILY_TARGET)
    if not leads:
        logger.warning("No nonprofit leads found today.")
        return
    logger.info("Nonprofit: %d leads to send.", len(leads))
    _send_leads(leads, "NONPROFIT")


def run_speaking() -> None:
    """12 emails from speaking@danniadams.me to speaker and creator leads."""
    logger.info("=== SPEAKING JOB STARTED ===")
    if not _preflight():
        return
    create_sheet_if_missing()
    leads = gather_leads_for_profiles(["speaker", "nonprofit_speaker"], target=SPEAKING_DAILY_TARGET)
    # creator profile paused — saved for last leg of outreach
    if not leads:
        logger.warning("No speaker/creator/nonprofit_speaker leads found today.")
        return
    logger.info("Speaking: %d leads to send.", len(leads))
    _send_leads(leads, "SPEAKING")


def run_partnerships() -> None:
    """12 emails from partnerships@danniadams.me to brand and talent leads."""
    logger.info("=== PARTNERSHIPS JOB STARTED ===")
    if not _preflight():
        return
    create_sheet_if_missing()
    leads = gather_leads_for_profiles(["brand", "talent", "venue_host"], target=PARTNERSHIPS_DAILY_TARGET)
    if not leads:
        logger.warning("No brand/talent/venue_host leads found today.")
        return
    logger.info("Partnerships: %d leads to send.", len(leads))
    _send_leads(leads, "PARTNERSHIPS")


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
            profile=email_data.get("profile", "nonprofit"),
            is_html=email_data.get("is_html", False),
            respect_rate_limit=True,
            org=lead.get("org", ""),
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
            is_html=email_data.get("is_html", False),
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

    # 2. Run 30-day check-ins in the same job
    checkin_leads = get_leads_needing_checkin()

    if not checkin_leads:
        logger.info("No leads due for 30-day check-in today.")
        return

    logger.info("%d lead(s) due for 30-day check-in.", len(checkin_leads))

    checkin_sent = 0
    checkin_failed = 0

    for row in checkin_leads:
        lead = {
            "name": row.get("Name", ""),
            "org": row.get("Org", ""),
            "email": row.get("Email", ""),
            "industry": row.get("Industry", ""),
            "notes": row.get("Notes", ""),
        }

        if not lead["email"]:
            continue

        original_subject = row.get("Notes", "") or f"Quick idea for {lead['org']}"

        try:
            email_data = build_checkin_email(lead, original_subject)
        except Exception as exc:
            logger.error("Failed to build check-in for %s: %s", lead.get("email"), exc)
            checkin_failed += 1
            continue

        success = send_email(
            to_address=email_data["to"],
            subject=email_data["subject"],
            body=email_data["body"],
            is_html=email_data.get("is_html", False),
            respect_rate_limit=True,
        )

        if success:
            try:
                mark_checkin_sent(lead["email"])
            except Exception as exc:
                logger.error(
                    "Check-in sent but failed to update sheet for %s: %s",
                    lead["email"],
                    exc,
                )
            checkin_sent += 1
        else:
            checkin_failed += 1

    logger.info(
        "=== CHECK-IN JOB COMPLETE — sent: %d, failed: %d ===",
        checkin_sent,
        checkin_failed,
    )


# ---------------------------------------------------------------------------
# Discover command: DISCOVER → QUALIFY → STAGE IN NOTION (no email, no send)
# ---------------------------------------------------------------------------

def run_discover() -> None:
    """
    Phase 1 of the new pipeline: DISCOVER → QUALIFY → STAGE IN NOTION.

    - Scrapes org pages without collecting email addresses
    - Scores each org against lane-specific rubrics (lead_qualifier.py)
    - Stages results (A, B, C, Disqualified) to the Lead Pipeline Notion database
    - SENDS_PAUSED state is irrelevant here — no email is sent at any point

    Run this to fill the approval queue. Check Notion afterward.
    Approve A-tier leads manually in Notion before any email lookup begins.
    """
    logger.info("=== DISCOVER JOB STARTED — %s ===", datetime.now().strftime("%Y-%m-%d %H:%M"))

    # SENDS_PAUSED guard removed — discover does not send email anyway.
    # Sending is gated inside run_send_approved() separately.

    try:
        from lead_qualifier import qualify_lead
        from notion_pipeline import stage_leads_batch, get_pipeline_summary, PIPELINE_DATABASE_ID
    except ImportError as exc:
        logger.critical("Missing module: %s", exc)
        sys.exit(1)

    if not PIPELINE_DATABASE_ID:
        logger.critical(
            "NOTION_PIPELINE_DATABASE_ID is not set. "
            "Create the Lead Pipeline database first:\n"
            "  from notion_pipeline import create_pipeline_database\n"
            "  db_id = create_pipeline_database('<your_notion_page_id>')\n"
            "Then set NOTION_PIPELINE_DATABASE_ID=<db_id> in Railway env vars."
        )
        sys.exit(1)

    # Which lanes to run today — can be overridden via CLI args
    # Default: all four primary lanes
    default_lanes = ["nonprofit_consulting", "nonprofit_speaking", "youth_speaking", "venue_hosting", "universities", "brand_partnerships", "talent_representation"]
    lanes = sys.argv[2:] if len(sys.argv) > 2 else default_lanes

    # Locations: full rotation
    locations = _todays_venue_locations()

    logger.info("Lanes: %s", lanes)
    logger.info("Locations: %s", locations)

    # Step 1: Discover organizations
    logger.info("Step 1: Discovering organizations...")
    discovered = discover_orgs_for_pipeline(
        lanes=lanes,
        locations=locations,
        max_per_lane=40,
    )
    logger.info("Discovered %d organizations.", len(discovered))

    if not discovered:
        logger.warning("No organizations discovered. Check scraper / network / DuckDuckGo access.")
        return

    # Step 2: Qualify each organization
    logger.info("Step 2: Qualifying organizations...")
    qualified_leads: list[dict] = []
    for org in discovered:
        try:
            result = qualify_lead(
                org_name=org["org_name"],
                domain=org["domain"],
                source_url=org["source_url"],
                city=org["city"],
                state=org["state"],
                query_industry=org["industry"],
                candidate_lanes=org["candidate_lanes"],
                page_texts=org.get("page_texts", []),
            )
            qualified_leads.append(result)
            logger.info(
                "  [%s] %s — %s (%s)",
                result.get("lead_score", "?"),
                result.get("org_name", org["org_name"]),
                result.get("primary_lane", "?"),
                result.get("disqualification_reason", ""),
            )
        except Exception as exc:
            logger.error("Qualification failed for %s: %s", org.get("org_name", org["domain"]), exc)

    logger.info("Qualification complete: %d leads scored.", len(qualified_leads))

    # Step 3: Stage to Notion
    logger.info("Step 3: Staging to Notion Lead Pipeline database...")
    summary = stage_leads_batch(qualified_leads)

    # Step 4: Print results
    tier_counts: dict = {}
    for lead in qualified_leads:
        score = lead.get("lead_score", "?")
        tier_counts[score] = tier_counts.get(score, 0) + 1

    print("\n" + "=" * 60)
    print("  DISCOVER RUN COMPLETE")
    print("=" * 60)
    print(f"  Organizations found   : {len(discovered)}")
    print(f"  Leads scored          : {len(qualified_leads)}")
    print()
    print("  Score breakdown:")
    for score in ["A", "B", "C", "Disqualified"]:
        print(f"    {score:<20} {tier_counts.get(score, 0)}")
    print()
    print("  Notion pipeline:")
    print(f"    Staged               : {summary.get('staged', 0)}")
    print(f"    Skipped (duplicate)  : {summary.get('skipped_duplicate', 0)}")
    print(f"    Failed               : {summary.get('failed', 0)}")
    print()

    # Approval queue count
    try:
        pipeline_summary = get_pipeline_summary()
        print(f"  Approval queue (A-tier, Qualified): {pipeline_summary.get('approval_queue', 0)}")
    except Exception:
        pass

    print()
    print("  Next step: review A-tier leads in Notion and mark Approved.")
    print("  No email has been looked up or sent.")
    print("=" * 60 + "\n")

    # Chain into send_approved → new pipeline follow-ups → old sheet follow-ups
    logger.info("Chaining into send_approved...")
    run_send_approved()

    logger.info("Chaining into pipeline_followups (new pipeline)...")
    run_pipeline_followups()

    logger.info("Chaining into followup (old sheet leads)...")
    run_followup()

    logger.info("Chaining into hot lead sweep...")
    run_slack_alerts()

    # Always check pipeline health at end of discover run
    run_health()


# ---------------------------------------------------------------------------
# Send-approved job: email lookup → send → mark sent in Notion
# ---------------------------------------------------------------------------

# Lane → email profile mapping
LANE_TO_PROFILE = {
    "nonprofit_consulting": "nonprofit",
    "nonprofit_speaking": "nonprofit_speaker",
    "youth_speaking": "speaker",
    "universities": "speaker",
    "venue_hosting": "venue_host",
    "brand_partnerships": "brand",
    "talent_representation": "talent",
}


def run_send_approved() -> None:
    """
    For every lead marked Approved in Notion:
      1. Look up contact email from org website
      2. Build outreach email using the right template + profile
      3. Send via Brevo
      4. Mark sent in Notion (Status → Sent, touch count +1)

    Run daily via cron after discover. No human action needed between
    approval and send — Danni approves once a week, system sends daily.
    """
    logger.info("=== SEND APPROVED JOB STARTED — %s ===", datetime.now().strftime("%Y-%m-%d %H:%M"))

    if not _preflight():
        logger.error("Preflight failed. Aborting.")
        sys.exit(1)

    sends_paused = os.getenv("SENDS_PAUSED", "false").lower()
    if sends_paused in ("true", "1", "yes"):
        logger.warning("SENDS_PAUSED=true — no emails will be sent. Set SENDS_PAUSED=false to enable.")
        return

    try:
        from notion_pipeline import get_approved_leads, update_lead_status, mark_sent
        from email_lookup import find_contact_email
    except ImportError as exc:
        logger.critical("Missing module: %s", exc)
        sys.exit(1)

    approved = get_approved_leads(limit=100)
    if not approved:
        logger.info("No approved leads to send today.")
        return

    logger.info("%d approved lead(s) to process.", len(approved))

    sent_count = 0
    skipped_count = 0
    failed_count = 0

    for lead in approved:
        org_name = lead.get("org_name", "")
        domain = lead.get("domain", "")
        page_id = lead.get("page_id", "")
        primary_lane = lead.get("primary_lane", "nonprofit_consulting")

        if not domain:
            logger.warning("Skipping %s — no domain.", org_name)
            skipped_count += 1
            continue

        # 1. Use stored email if already found; otherwise scrape from domain
        stored_email = lead.get("contact_email", "")
        if stored_email:
            email = stored_email
            email_source = lead.get("email_source", "Notion (pre-verified)")
            logger.info("Using stored email for %s: %s", org_name, email)
        else:
            logger.info("Looking up email for %s (%s)...", org_name, domain)
            email, email_source = find_contact_email(domain)

        if not email:
            logger.warning("No email found for %s — skipping.", org_name)
            update_lead_status(page_id, "Approved", {
                "Approval Notes": "Email lookup failed — no contact email found on site",
            })
            skipped_count += 1
            continue

        # 2. Update Notion with found email (no-op if already stored)
        update_lead_status(page_id, "Email Found", {
            "Contact Email": email,
            "Email Source": email_source,
        })

        # 3. Build lead dict for email template
        profile = LANE_TO_PROFILE.get(primary_lane, "nonprofit")
        send_lead = {
            "name": lead.get("contact_name", ""),
            "org": org_name,
            "email": email,
            "industry": lead.get("industry", ""),
            "city": lead.get("city", "Orlando"),
            "state": lead.get("state", "FL"),
            "profile": profile,
            "notes": lead.get("why_danni_fits", ""),
            "source_url": lead.get("source_url", ""),
        }

        # 4. Build email
        try:
            email_data = build_initial_email(send_lead)
        except Exception as exc:
            logger.error("Failed to build email for %s <%s>: %s", org_name, email, exc)
            failed_count += 1
            continue

        # 5. Send
        success = send_email(
            to_address=email_data["to"],
            subject=email_data["subject"],
            body=email_data["body"],
            profile=email_data.get("profile", profile),
            is_html=email_data.get("is_html", False),
            respect_rate_limit=True,
            org=org_name,
        )

        if success:
            # 6. Log to old outreach sheet + mark sent in Notion pipeline
            try:
                log_new_lead(send_lead)
            except Exception as exc:
                logger.warning("Email sent but outreach log failed for %s: %s", email, exc)

            update_lead_status(page_id, "Sent", {
                "Touch Count": 1,
            })
            sent_count += 1
            logger.info("Sent to %s <%s>", org_name, email)
        else:
            failed_count += 1

    logger.info(
        "=== SEND APPROVED COMPLETE — sent: %d, skipped: %d, failed: %d ===",
        sent_count, skipped_count, failed_count,
    )


# ---------------------------------------------------------------------------
# Slack alerts: mark hot leads in Notion (no message sent — Danni messages
# me when someone replies, and I give her a draft reply then)
# ---------------------------------------------------------------------------

def run_slack_alerts() -> None:
    """
    Sweep Brevo for opens/clicks and mark hot leads in Notion.
    Does NOT send Slack messages for routine engagement.
    Danni messages me when someone actually replies — I draft her reply then.
    """
    logger.info("=== HOT LEAD SWEEP STARTED ===")

    try:
        from brevo_events import get_recent_events, summarize_engagement
        from notion_pipeline import get_leads_by_status, mark_hot_lead
    except ImportError as exc:
        logger.warning("Hot lead sweep skipped — missing module: %s", exc)
        return

    events = get_recent_events(days_back=1)
    if not events:
        logger.info("No engagement events in last 24 hours.")
        return

    engagement = summarize_engagement(events)
    sent_leads = get_leads_by_status("Sent", limit=200)
    email_to_lead = {l.get("contact_email", "").lower(): l for l in sent_leads if l.get("contact_email")}

    hot_count = 0
    for email, data in engagement.items():
        if not data["is_hot"]:
            continue
        lead = email_to_lead.get(email.lower())
        if lead and lead.get("page_id"):
            mark_hot_lead(lead["page_id"])
            hot_count += 1
            logger.info("Marked hot: %s <%s> (opens=%d clicks=%d)", lead["org_name"], email, data["opens"], data["clicks"])

    logger.info("=== HOT LEAD SWEEP COMPLETE — %d leads marked hot ===", hot_count)


# ---------------------------------------------------------------------------
# Pipeline follow-ups: send follow-up emails to non-responders
# ---------------------------------------------------------------------------

def run_pipeline_followups() -> None:
    """
    Send follow-up emails to pipeline leads that haven't replied.

    Cadence:
      Hot leads (opened 2+ times or clicked): follow up after 3 days
      Standard leads: follow up after 7 days

    Max 2 follow-ups total per lead (touch_count check).
    Stops if Status=Replied.
    """
    logger.info("=== PIPELINE FOLLOWUPS JOB STARTED — %s ===", datetime.now().strftime("%Y-%m-%d %H:%M"))

    if not _preflight():
        return

    sends_paused = os.getenv("SENDS_PAUSED", "false").lower()
    if sends_paused in ("true", "1", "yes"):
        logger.warning("SENDS_PAUSED=true — follow-ups skipped.")
        return

    try:
        from notion_pipeline import get_sent_leads_needing_followup, mark_followup_sent_pipeline
    except ImportError as exc:
        logger.warning("Pipeline followups skipped — missing module: %s", exc)
        return

    # Hot leads first (3-day cadence), then standard (7-day cadence)
    hot_leads = get_sent_leads_needing_followup(hot=True)
    standard_leads = get_sent_leads_needing_followup(hot=False)

    # Deduplicate: hot leads are a subset of standard leads
    hot_page_ids = {l["page_id"] for l in hot_leads}
    standard_only = [l for l in standard_leads if l["page_id"] not in hot_page_ids]

    all_due = hot_leads + standard_only
    logger.info("%d lead(s) due for follow-up (%d hot, %d standard).", len(all_due), len(hot_leads), len(standard_only))

    if not all_due:
        logger.info("No follow-ups due today.")
        return

    sent_count = 0
    skipped_count = 0
    failed_count = 0

    for lead in all_due:
        touch = lead.get("touch_count", 1)
        if touch >= 3:
            # Already followed up twice — stop
            logger.info("Skipping %s — touch count %d, max reached.", lead["org_name"], touch)
            skipped_count += 1
            continue

        email = lead.get("contact_email", "")
        if not email:
            skipped_count += 1
            continue

        profile = LANE_TO_PROFILE.get(lead.get("primary_lane", ""), "nonprofit")

        send_lead = {
            "name": "",
            "org": lead["org_name"],
            "email": email,
            "industry": "",
            "city": lead.get("city", ""),
            "state": lead.get("state", ""),
            "profile": profile,
            "notes": lead.get("why_danni_fits", ""),
        }

        try:
            email_data = build_followup_email(send_lead, f"Re: {lead['org_name']}")
        except Exception as exc:
            logger.error("Failed to build follow-up for %s: %s", email, exc)
            failed_count += 1
            continue

        success = send_email(
            to_address=email_data["to"],
            subject=email_data["subject"],
            body=email_data["body"],
            profile=email_data.get("profile", profile),
            is_html=email_data.get("is_html", False),
            respect_rate_limit=True,
            org=lead["org_name"],
        )

        if success:
            mark_followup_sent_pipeline(lead["page_id"], touch + 1)
            sent_count += 1
            logger.info("Follow-up sent to %s <%s> (touch %d)", lead["org_name"], email, touch + 1)
        else:
            failed_count += 1

    logger.info(
        "=== PIPELINE FOLLOWUPS COMPLETE — sent: %d, skipped: %d, failed: %d ===",
        sent_count, skipped_count, failed_count,
    )


# ---------------------------------------------------------------------------
# Pipeline health check: alert when Qualified leads drop below 150
# ---------------------------------------------------------------------------

PIPELINE_LOW_THRESHOLD = 150


def _get_qualified_lead_count() -> int:
    """Query the Notion Lead Pipeline for leads in a sendable state."""
    try:
        import requests as _requests
        notion_key = os.getenv("NOTION_API_KEY", "")
        if not notion_key:
            logger.warning("NOTION_API_KEY not set — cannot check pipeline count.")
            return -1

        # Query the Lead Pipeline database for Qualified + Approved + Send Ready counts
        db_id = "325ed050-6fa7-41c0-982c-02e004c8c536"
        headers = {
            "Authorization": f"Bearer {notion_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        body = {
            "filter": {
                "or": [
                    {"property": "Status", "select": {"equals": "Qualified"}},
                    {"property": "Status", "select": {"equals": "Approved"}},
                    {"property": "Status", "select": {"equals": "Send Ready"}},
                ]
            },
            "page_size": 1,
        }
        resp = _requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            json=body,
            headers=headers,
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning("Notion pipeline count failed: %s %s", resp.status_code, resp.text[:200])
            return -1

        data = resp.json()
        # Notion returns total in has_more + results; we need full count via pagination
        # For just a threshold check, use a larger page_size
        body["page_size"] = 500
        resp2 = _requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            json=body,
            headers=headers,
            timeout=15,
        )
        if resp2.status_code == 200:
            return len(resp2.json().get("results", []))
        return len(data.get("results", []))
    except Exception as exc:
        logger.warning("Pipeline count check failed: %s", exc)
        return -1


def _send_slack_pipeline_alert(count: int) -> None:
    """Send a Slack message alerting that the pipeline is running low."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping Slack pipeline alert.")
        return

    try:
        import requests as _requests
        message = (
            f":warning: *Pipeline Alert* — Only *{count} sendable leads* remain in the Notion pipeline "
            f"(threshold: {PIPELINE_LOW_THRESHOLD}).\n\n"
            f"Run `python main.py discover` to queue fresh leads.\n"
            f"Check the Lead Pipeline in Notion: https://app.notion.com/p/01a1d05d80fb4c85953ca11b0fcf8e1b"
        )
        resp = _requests.post(webhook_url, json={"text": message}, timeout=10)
        if resp.status_code == 200:
            logger.info("Slack pipeline alert sent.")
        else:
            logger.warning("Slack alert failed: %s %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Slack alert failed: %s", exc)


def run_health() -> None:
    """
    Check pipeline lead count and alert via Slack if below 150.
    Runs automatically at end of run_discover(); also callable directly:
      python main.py health
    """
    logger.info("=== PIPELINE HEALTH CHECK ===")
    count = _get_qualified_lead_count()

    if count == -1:
        logger.warning("Could not determine pipeline count.")
        return

    logger.info("Sendable leads in pipeline (Qualified + Approved + Send Ready): %d", count)

    if count < PIPELINE_LOW_THRESHOLD:
        logger.warning(
            "PIPELINE LOW: %d leads remaining (threshold: %d) — alerting via Slack.",
            count, PIPELINE_LOW_THRESHOLD,
        )
        _send_slack_pipeline_alert(count)
    else:
        logger.info("Pipeline healthy: %d leads >= threshold of %d.", count, PIPELINE_LOW_THRESHOLD)


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
    "discover": run_discover,
    "send_approved": run_send_approved,
    "pipeline_followups": run_pipeline_followups,
    "slack_alerts": run_slack_alerts,
    "health": run_health,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python main.py [{' | '.join(COMMANDS)}]")
        sys.exit(1)

    command = sys.argv[1]
    logger.info("Running command: %s", command)
    COMMANDS[command]()
