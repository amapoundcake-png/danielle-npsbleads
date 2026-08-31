"""
notion_pipeline.py — Lead Pipeline database integration for the new DISCOVER → QUALIFY → STAGE workflow.

Manages the "Lead Pipeline" Notion database — separate from the existing outreach log in notion_logger.py.
This file handles pre-send lead staging; notion_logger.py handles post-send tracking.

Schema enforced here:
  Identity:         Organization, Domain, Source URL, City, State
  Scoring:          Lead Score (A/B/C/Disqualified), Primary Lane, Secondary Lane, Lane Reasoning, Profile
  Org Details:      Venue Type, Estimated Size, Independent, Programming Evidence
  Contact:          Contact Name, Contact Title, Contact Email, Email Source, Verification Status, Last Verified Date
  Why Danni:        Why Danni Fits, Evidence Source
  Pipeline:         Status, Disqualification Reason, Approval Notes, Approved By,
                    Discovered Date, Sent Date, Last Contact Date, Touch Count, Response,
                    Last Delivery Event, Bounce Type, Website Check Status, Website Check Date

Status flow:
  Qualified → [human review] → Approved / Rejected
  Approved → [email lookup] → Email Found → [verification] → Verified → [pre-send check] → Send Ready
  Any stage → Disqualified (with reason)
"""

import logging
import os
from datetime import date, datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_VERSION = "2022-06-28"
PIPELINE_DATABASE_ID = os.getenv("NOTION_PIPELINE_DATABASE_ID", "")  # separate from outreach log DB

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

# ---------------------------------------------------------------------------
# Notion HTTP helpers
# ---------------------------------------------------------------------------

def _notion_request(method: str, endpoint: str, payload: dict = None) -> Optional[dict]:
    url = f"https://api.notion.com/v1/{endpoint}"
    try:
        resp = requests.request(method, url, headers=HEADERS, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.error("Notion API error [%s %s]: %s", method, endpoint, exc)
        return None


# ---------------------------------------------------------------------------
# Database creation
# ---------------------------------------------------------------------------

def create_pipeline_database(parent_page_id: str) -> Optional[str]:
    """
    Create the Lead Pipeline database under a given Notion page.
    Returns the new database ID, or None on failure.

    Call once manually; after creation store the returned ID in
    NOTION_PIPELINE_DATABASE_ID env var on Railway.
    """
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "Lead Pipeline"}}],
        "properties": {
            # -- Identity --
            "Organization": {"title": {}},
            "Domain": {"rich_text": {}},
            "Source URL": {"url": {}},
            "City": {"rich_text": {}},
            "State": {"rich_text": {}},

            # -- Scoring --
            "Lead Score": {"select": {"options": [
                {"name": "A", "color": "green"},
                {"name": "B", "color": "yellow"},
                {"name": "C", "color": "gray"},
                {"name": "Disqualified", "color": "red"},
            ]}},
            "Primary Lane": {"select": {"options": [
                {"name": "nonprofit_consulting"},
                {"name": "nonprofit_speaking"},
                {"name": "youth_speaking"},
                {"name": "universities"},
                {"name": "venue_hosting"},
                {"name": "brand_partnerships"},
                {"name": "talent_representation"},
            ]}},
            "Secondary Lane": {"rich_text": {}},
            "Lane Reasoning": {"rich_text": {}},
            "Profile": {"select": {"options": [
                {"name": "nonprofit"},
                {"name": "nonprofit_speaker"},
                {"name": "speaker"},
                {"name": "venue_host"},
                {"name": "brand"},
                {"name": "talent"},
            ]}},

            # -- Org Details --
            "Venue Type": {"rich_text": {}},
            "Estimated Size": {"select": {"options": [
                {"name": "Small"},
                {"name": "Mid"},
                {"name": "Large"},
                {"name": "Unknown"},
            ]}},
            "Independent": {"select": {"options": [
                {"name": "Yes"},
                {"name": "No"},
                {"name": "Unknown"},
            ]}},
            "Programming Evidence": {"rich_text": {}},

            # -- Contact --
            "Contact Name": {"rich_text": {}},
            "Contact Title": {"rich_text": {}},
            "Contact Email": {"email": {}},
            "Email Source": {"rich_text": {}},
            "Verification Status": {"select": {"options": [
                {"name": "Not Started"},
                {"name": "Verified"},
                {"name": "Failed"},
                {"name": "Bounced"},
            ]}},
            "Last Verified Date": {"date": {}},

            # -- Why Danni --
            "Why Danni Fits": {"rich_text": {}},
            "Evidence Source": {"rich_text": {}},

            # -- Pipeline --
            "Status": {"select": {"options": [
                {"name": "Qualified"},
                {"name": "Approved"},
                {"name": "Rejected"},
                {"name": "Email Found"},
                {"name": "Verified"},
                {"name": "Send Ready"},
                {"name": "Sent"},
                {"name": "Disqualified"},
                {"name": "Soft Bounce Hold"},
                {"name": "Website Hold"},
            ]}},
            "Disqualification Reason": {"rich_text": {}},
            "Approval Notes": {"rich_text": {}},
            "Approved By": {"rich_text": {}},
            "Discovered Date": {"date": {}},
            "Sent Date": {"date": {}},
            "Last Contact Date": {"date": {}},
            "Touch Count": {"number": {}},
            "Response": {"rich_text": {}},
            "Last Delivery Event": {"rich_text": {}},
            "Bounce Type": {"rich_text": {}},
            "Website Check Status": {"select": {"options": [
                {"name": "Not Checked"},
                {"name": "OK"},
                {"name": "Hold"},
                {"name": "Flagged"},
            ]}},
            "Website Check Date": {"date": {}},
        },
    }

    result = _notion_request("POST", "databases", payload)
    if result:
        db_id = result.get("id", "")
        logger.info("Created Lead Pipeline database: %s", db_id)
        return db_id
    return None


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def is_duplicate(domain: str, email: str = "") -> bool:
    """Check whether a domain or email already exists in the pipeline database."""
    if not PIPELINE_DATABASE_ID:
        return False

    # Check by domain first
    if domain:
        payload = {
            "filter": {"property": "Domain", "rich_text": {"equals": domain.lower().strip()}},
            "page_size": 1,
        }
        result = _notion_request("POST", f"databases/{PIPELINE_DATABASE_ID}/query", payload)
        if result and result.get("results"):
            logger.debug("Duplicate domain found: %s", domain)
            return True

    # Check by email if provided
    if email and email.strip():
        payload = {
            "filter": {"property": "Contact Email", "email": {"equals": email.lower().strip()}},
            "page_size": 1,
        }
        result = _notion_request("POST", f"databases/{PIPELINE_DATABASE_ID}/query", payload)
        if result and result.get("results"):
            logger.debug("Duplicate email found: %s", email)
            return True

    return False


# ---------------------------------------------------------------------------
# Write lead to pipeline database
# ---------------------------------------------------------------------------

def _rich_text(value: str) -> list:
    """Build a Notion rich_text block from a plain string."""
    content = str(value or "")[:2000]  # Notion limit
    return [{"type": "text", "text": {"content": content}}]


def _select(value: str) -> dict:
    """Build a Notion select block."""
    return {"name": str(value or "Unknown")}


def stage_lead(lead: dict) -> Optional[str]:
    """
    Write a qualified (or disqualified) lead to the Lead Pipeline Notion database.

    `lead` must follow the schema returned by qualify_lead() in lead_qualifier.py.
    Returns the Notion page ID on success, or None on failure.

    Skips duplicates silently (logs at DEBUG level).
    """
    if not PIPELINE_DATABASE_ID:
        logger.warning("NOTION_PIPELINE_DATABASE_ID not set -- skipping pipeline stage.")
        return None

    domain = lead.get("domain", "").lower().strip()
    email = lead.get("email", "").lower().strip()

    if is_duplicate(domain, email):
        logger.debug("Skipping duplicate: %s (%s)", lead.get("org_name", ""), domain)
        return None

    today = date.today().isoformat()

    # Estimated size must be one of the select options; default Unknown
    size_raw = lead.get("estimated_size", "Unknown")
    size = size_raw if size_raw in ("Small", "Mid", "Large", "Unknown") else "Unknown"

    # Independent must be Yes/No/Unknown
    independent_raw = lead.get("independent", "Unknown")
    independent = independent_raw if independent_raw in ("Yes", "No", "Unknown") else "Unknown"

    # Lead score must be A/B/C/Disqualified
    score_raw = lead.get("lead_score", "C")
    score = score_raw if score_raw in ("A", "B", "C", "Disqualified") else "C"

    # Status
    status = "Disqualified" if score == "Disqualified" else "Qualified"

    # Website check status
    website_status_raw = lead.get("website_check_status", "Not Checked")
    website_status = website_status_raw if website_status_raw in ("Not Checked", "OK", "Hold", "Flagged") else "Not Checked"

    properties = {
        # Identity
        "Organization": {"title": [{"type": "text", "text": {"content": str(lead.get("org_name", "Unknown"))[:255]}}]},
        "Domain": {"rich_text": _rich_text(domain)},
        "City": {"rich_text": _rich_text(lead.get("city", ""))},
        "State": {"rich_text": _rich_text(lead.get("state", ""))},

        # Scoring
        "Lead Score": {"select": _select(score)},
        "Primary Lane": {"select": _select(lead.get("primary_lane", ""))},
        "Lane Reasoning": {"rich_text": _rich_text(lead.get("lane_reasoning", ""))},
        "Profile": {"select": _select(lead.get("profile", "nonprofit"))},

        # Org details
        "Estimated Size": {"select": _select(size)},
        "Independent": {"select": _select(independent)},
        "Programming Evidence": {"rich_text": _rich_text(lead.get("programming_evidence", ""))},

        # Contact
        "Verification Status": {"select": _select(lead.get("verification_status", "Not Started"))},

        # Why Danni
        "Why Danni Fits": {"rich_text": _rich_text(lead.get("why_danni_fits", ""))},
        "Evidence Source": {"rich_text": _rich_text(lead.get("evidence_source", ""))},

        # Pipeline
        "Status": {"select": _select(status)},
        "Disqualification Reason": {"rich_text": _rich_text(lead.get("disqualification_reason", ""))},
        "Discovered Date": {"date": {"start": today}},
        "Touch Count": {"number": lead.get("touch_count", 0)},
        "Website Check Status": {"select": _select(website_status)},
    }

    # Optional fields — only set if non-empty to avoid Notion validation errors

    source_url = lead.get("source_url", "")
    if source_url and source_url.startswith("http"):
        properties["Source URL"] = {"url": source_url}

    secondary_lane = lead.get("secondary_lane", "")
    if secondary_lane:
        properties["Secondary Lane"] = {"rich_text": _rich_text(secondary_lane)}

    venue_type = lead.get("venue_type", "")
    if venue_type:
        properties["Venue Type"] = {"rich_text": _rich_text(venue_type)}

    contact_name = lead.get("contact_name", "")
    if contact_name:
        properties["Contact Name"] = {"rich_text": _rich_text(contact_name)}

    contact_title = lead.get("contact_title", "")
    if contact_title:
        properties["Contact Title"] = {"rich_text": _rich_text(contact_title)}

    email_val = lead.get("email", "")
    if email_val and "@" in email_val:
        properties["Contact Email"] = {"email": email_val.lower().strip()}

    email_source = lead.get("email_source", "")
    if email_source:
        properties["Email Source"] = {"rich_text": _rich_text(email_source)}

    response_val = lead.get("response", "")
    if response_val:
        properties["Response"] = {"rich_text": _rich_text(response_val)}

    payload = {
        "parent": {"database_id": PIPELINE_DATABASE_ID},
        "properties": properties,
    }

    result = _notion_request("POST", "pages", payload)
    if result:
        page_id = result.get("id", "")
        logger.info(
            "Staged lead [%s] %s (%s) → %s",
            score, lead.get("org_name", ""), domain, page_id
        )
        return page_id
    return None


# ---------------------------------------------------------------------------
# Bulk stage
# ---------------------------------------------------------------------------

def stage_leads_batch(leads: list[dict]) -> dict:
    """
    Write a list of leads to the Lead Pipeline database.

    Returns a summary: {"staged": N, "skipped_duplicate": N, "failed": N}
    """
    staged = 0
    skipped = 0
    failed = 0

    for lead in leads:
        domain = lead.get("domain", "").lower().strip()
        email = lead.get("email", "").lower().strip()

        if is_duplicate(domain, email):
            skipped += 1
            continue

        result = stage_lead(lead)
        if result:
            staged += 1
        else:
            # stage_lead returns None for both skipped duplicates (caught above) and failures
            failed += 1

    logger.info("Batch complete: staged=%d skipped=%d failed=%d", staged, skipped, failed)
    return {"staged": staged, "skipped_duplicate": skipped, "failed": failed}


# ---------------------------------------------------------------------------
# Status queries (for approval workflow)
# ---------------------------------------------------------------------------

def get_leads_by_status(status: str, limit: int = 50) -> list[dict]:
    """
    Return leads in the pipeline database matching a given status.

    Useful for pulling the approval queue:
        get_leads_by_status("Qualified")  → A-tier leads awaiting review
    """
    if not PIPELINE_DATABASE_ID:
        return []

    payload = {
        "filter": {"property": "Status", "select": {"equals": status}},
        "sorts": [{"property": "Discovered Date", "direction": "descending"}],
        "page_size": min(limit, 100),
    }

    result = _notion_request("POST", f"databases/{PIPELINE_DATABASE_ID}/query", payload)
    if not result:
        return []

    leads = []
    for page in result.get("results", []):
        props = page.get("properties", {})

        def _get_title(prop):
            blocks = props.get(prop, {}).get("title", [])
            return blocks[0].get("text", {}).get("content", "") if blocks else ""

        def _get_rich(prop):
            blocks = props.get(prop, {}).get("rich_text", [])
            return blocks[0].get("text", {}).get("content", "") if blocks else ""

        def _get_select(prop):
            sel = props.get(prop, {}).get("select")
            return sel.get("name", "") if sel else ""

        leads.append({
            "page_id": page["id"],
            "org_name": _get_title("Organization"),
            "domain": _get_rich("Domain"),
            "lead_score": _get_select("Lead Score"),
            "primary_lane": _get_select("Primary Lane"),
            "profile": _get_select("Profile"),
            "status": _get_select("Status"),
            "why_danni_fits": _get_rich("Why Danni Fits"),
            "estimated_size": _get_select("Estimated Size"),
            "independent": _get_select("Independent"),
            "programming_evidence": _get_rich("Programming Evidence"),
            "city": _get_rich("City"),
            "state": _get_rich("State"),
            "source_url": props.get("Source URL", {}).get("url", ""),
            "disqualification_reason": _get_rich("Disqualification Reason"),
            "contact_name": _get_rich("Contact Name"),
            "contact_title": _get_rich("Contact Title"),
            "industry": _get_rich("Venue Type"),
            "notes": _get_rich("Why Danni Fits"),
        })

    return leads


def get_approval_queue() -> list[dict]:
    """Return all A-tier qualified leads awaiting human approval."""
    all_qualified = get_leads_by_status("Qualified", limit=100)
    return [l for l in all_qualified if l.get("lead_score") == "A"]


def get_approved_leads(limit: int = 50) -> list[dict]:
    """Return all leads marked Approved in Notion, ready for email lookup + send."""
    return get_leads_by_status("Approved", limit=limit)


# ---------------------------------------------------------------------------
# Status updates
# ---------------------------------------------------------------------------

def update_lead_status(page_id: str, new_status: str, extra_properties: dict = None) -> bool:
    """
    Update a lead's Status field and optionally other properties.

    Common usage:
        update_lead_status(page_id, "Approved", {"Approved By": "Danni"})
        update_lead_status(page_id, "Rejected", {"Approval Notes": "Not a fit"})
        update_lead_status(page_id, "Email Found", {"Contact Email": "x@y.com", "Email Source": "LinkedIn"})
        update_lead_status(page_id, "Verified")
        update_lead_status(page_id, "Send Ready")
    """
    properties = {"Status": {"select": {"name": new_status}}}

    if extra_properties:
        for key, value in extra_properties.items():
            if key == "Contact Email" and isinstance(value, str):
                properties[key] = {"email": value.lower().strip()}
            elif key in ("Touch Count",) and isinstance(value, (int, float)):
                properties[key] = {"number": value}
            elif key in ("Sent Date", "Last Contact Date", "Last Verified Date", "Website Check Date"):
                properties[key] = {"date": {"start": value}}
            elif key in ("Lead Score", "Verification Status", "Independent", "Estimated Size",
                         "Website Check Status", "Primary Lane", "Profile", "Bounce Type"):
                properties[key] = {"select": {"name": str(value)}}
            else:
                # default: rich_text
                properties[key] = {"rich_text": _rich_text(str(value))}

    result = _notion_request("PATCH", f"pages/{page_id}", {"properties": properties})
    if result:
        logger.info("Updated page %s → Status: %s", page_id, new_status)
        return True
    return False


def mark_approved(page_id: str, approved_by: str = "Danni") -> bool:
    return update_lead_status(page_id, "Approved", {"Approved By": approved_by})


def mark_rejected(page_id: str, reason: str = "") -> bool:
    extras = {"Disqualification Reason": reason} if reason else {}
    return update_lead_status(page_id, "Rejected", extras)


def mark_email_found(page_id: str, email: str, source: str) -> bool:
    return update_lead_status(page_id, "Email Found", {
        "Contact Email": email,
        "Email Source": source,
        "Verification Status": "Not Started",
    })


def mark_verified(page_id: str) -> bool:
    today = date.today().isoformat()
    return update_lead_status(page_id, "Verified", {
        "Verification Status": "Verified",
        "Last Verified Date": today,
    })


def mark_send_ready(page_id: str) -> bool:
    """
    Mark a lead as Send Ready.

    IMPORTANT: Send Ready does NOT trigger an email send.
    All sending requires explicit human approval at the send step.
    SENDS_PAUSED must be checked at the send layer before any email goes out.
    """
    return update_lead_status(page_id, "Send Ready")


def mark_sent(page_id: str) -> bool:
    today = date.today().isoformat()
    return update_lead_status(page_id, "Sent", {
        "Sent Date": today,
        "Last Contact Date": today,
    })


def increment_touch_count(page_id: str, current_count: int) -> bool:
    return update_lead_status(page_id, "Sent", {"Touch Count": current_count + 1})


def mark_soft_bounce_hold(page_id: str, bounce_type: str = "Soft") -> bool:
    return update_lead_status(page_id, "Soft Bounce Hold", {
        "Bounce Type": bounce_type,
        "Last Delivery Event": f"Soft bounce — hold started {date.today().isoformat()}",
    })


def mark_website_hold(page_id: str, reason: str = "") -> bool:
    today = date.today().isoformat()
    extras = {"Website Check Status": "Hold", "Website Check Date": today}
    if reason:
        extras["Disqualification Reason"] = reason
    return update_lead_status(page_id, "Website Hold", extras)


# ---------------------------------------------------------------------------
# Pipeline summary
# ---------------------------------------------------------------------------

def get_pipeline_summary() -> dict:
    """Return a count of leads by status and score tier."""
    if not PIPELINE_DATABASE_ID:
        return {"total": 0, "by_status": {}, "by_score": {}, "approval_queue": 0}

    result = _notion_request("POST", f"databases/{PIPELINE_DATABASE_ID}/query", {"page_size": 100})
    if not result:
        return {"total": 0, "by_status": {}, "by_score": {}, "approval_queue": 0}

    pages = result.get("results", [])
    total = len(pages)
    by_status: dict = {}
    by_score: dict = {}
    approval_queue = 0

    for page in pages:
        props = page.get("properties", {})

        status_sel = props.get("Status", {}).get("select")
        status = status_sel.get("name", "Unknown") if status_sel else "Unknown"
        by_status[status] = by_status.get(status, 0) + 1

        score_sel = props.get("Lead Score", {}).get("select")
        score = score_sel.get("name", "Unknown") if score_sel else "Unknown"
        by_score[score] = by_score.get(score, 0) + 1

        if status == "Qualified" and score == "A":
            approval_queue += 1

    return {
        "total": total,
        "by_status": by_status,
        "by_score": by_score,
        "approval_queue": approval_queue,
    }
