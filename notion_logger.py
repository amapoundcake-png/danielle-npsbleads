"""
notion_logger.py — Notion database logging for Danni Adams outreach system.

Replaces sheets_logger.py. Logs every send to the Notion outreach database
and provides helpers for follow-up tracking.
"""

import logging
import os
import requests
from datetime import date, timedelta, datetime
from typing import Optional

from config import FOLLOW_UP_DAYS_MIN, FOLLOW_UP_DAYS_MAX, NOTION_DATABASE_ID

logger = logging.getLogger(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_VERSION = "2022-06-28"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


def _notion_request(method: str, endpoint: str, payload: dict = None) -> Optional[dict]:
    url = f"https://api.notion.com/v1/{endpoint}"
    try:
        resp = requests.request(method, url, headers=HEADERS, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.error("Notion API error [%s %s]: %s", method, endpoint, exc)
        return None


def log_new_lead(lead: dict, subject: str = "") -> bool:
    """Log a newly sent email to the Notion outreach database."""
    if not NOTION_DATABASE_ID:
        logger.warning("NOTION_DATABASE_ID not set -- skipping Notion log.")
        return False

    today = date.today().isoformat()
    import random
    followup_days = random.randint(FOLLOW_UP_DAYS_MIN, FOLLOW_UP_DAYS_MAX)
    followup_date = (date.today() + timedelta(days=followup_days)).isoformat()
    checkin_date = (date.today() + timedelta(days=30)).isoformat()

    profile = lead.get("profile", "nonprofit")

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Organization": {"title": [{"text": {"content": lead.get("org", "Unknown")}}]},
            "Contact Email": {"email": lead.get("email", "")},
            "Profile": {"select": {"name": profile}},
            "Status": {"select": {"name": "Sent"}},
            "Date Sent": {"date": {"start": today}},
            "Follow-up Due": {"date": {"start": followup_date}},
            "Check-in Due": {"date": {"start": checkin_date}},
            "Notes": {"rich_text": [{"text": {"content": subject or lead.get("notes", "")}}]},
        },
    }

    result = _notion_request("POST", "pages", payload)
    if result:
        logger.info("Logged to Notion: %s <%s>", lead.get("org"), lead.get("email"))
        return True
    return False


def is_already_contacted(email: str) -> bool:
    """Check if an email address already exists in the Notion database."""
    if not NOTION_DATABASE_ID:
        return False

    payload = {
        "filter": {
            "property": "Contact Email",
            "email": {"equals": email},
        },
        "page_size": 1,
    }

    result = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", payload)
    if result and result.get("results"):
        return True
    return False


def get_leads_needing_followup() -> list[dict]:
    """Return leads where follow-up is due today and not yet sent."""
    if not NOTION_DATABASE_ID:
        return []

    today = date.today().isoformat()
    payload = {
        "filter": {
            "and": [
                {"property": "Follow-up Due", "date": {"on_or_before": today}},
                {"property": "Follow-up Sent", "checkbox": {"equals": False}},
                {"property": "Status", "select": {"equals": "Sent"}},
            ]
        }
    }

    result = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", payload)
    if not result:
        return []

    leads = []
    for page in result.get("results", []):
        props = page.get("properties", {})
        email_prop = props.get("Contact Email", {}).get("email", "")
        org_prop = props.get("Organization", {}).get("title", [{}])
        org = org_prop[0].get("text", {}).get("content", "") if org_prop else ""
        notes = props.get("Notes", {}).get("rich_text", [{}])
        subject = notes[0].get("text", {}).get("content", "") if notes else ""
        profile = props.get("Profile", {}).get("select", {}).get("name", "nonprofit")

        if email_prop:
            leads.append({
                "email": email_prop,
                "org": org,
                "profile": profile,
                "page_id": page["id"],
                "Notes": subject,
            })

    return leads


def mark_followup_sent(email: str) -> bool:
    """Mark follow-up as sent in Notion."""
    if not NOTION_DATABASE_ID:
        return False

    payload = {
        "filter": {"property": "Contact Email", "email": {"equals": email}},
        "page_size": 1,
    }
    result = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", payload)
    if not result or not result.get("results"):
        return False

    page_id = result["results"][0]["id"]
    update = {
        "properties": {
            "Follow-up Sent": {"checkbox": True},
            "Status": {"select": {"name": "Follow-up Sent"}},
        }
    }
    return bool(_notion_request("PATCH", f"pages/{page_id}", update))


def get_leads_needing_checkin() -> list[dict]:
    """Return leads where 30-day check-in is due and not yet sent."""
    if not NOTION_DATABASE_ID:
        return []

    today = date.today().isoformat()
    payload = {
        "filter": {
            "and": [
                {"property": "Check-in Due", "date": {"on_or_before": today}},
                {"property": "Check-in Sent", "checkbox": {"equals": False}},
            ]
        }
    }

    result = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", payload)
    if not result:
        return []

    leads = []
    for page in result.get("results", []):
        props = page.get("properties", {})
        email_prop = props.get("Contact Email", {}).get("email", "")
        org_prop = props.get("Organization", {}).get("title", [{}])
        org = org_prop[0].get("text", {}).get("content", "") if org_prop else ""
        profile = props.get("Profile", {}).get("select", {}).get("name", "nonprofit")
        notes = props.get("Notes", {}).get("rich_text", [{}])
        subject = notes[0].get("text", {}).get("content", "") if notes else ""

        if email_prop:
            leads.append({
                "email": email_prop,
                "org": org,
                "profile": profile,
                "page_id": page["id"],
                "Notes": subject,
            })

    return leads


def mark_checkin_sent(email: str) -> bool:
    """Mark 30-day check-in as sent in Notion."""
    if not NOTION_DATABASE_ID:
        return False

    payload = {
        "filter": {"property": "Contact Email", "email": {"equals": email}},
        "page_size": 1,
    }
    result = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", payload)
    if not result or not result.get("results"):
        return False

    page_id = result["results"][0]["id"]
    update = {
        "properties": {
            "Check-in Sent": {"checkbox": True},
            "Status": {"select": {"name": "Check-in Sent"}},
        }
    }
    return bool(_notion_request("PATCH", f"pages/{page_id}", update))


def get_summary() -> dict:
    """Return a summary of outreach activity from Notion."""
    if not NOTION_DATABASE_ID:
        return {"total": 0, "by_status": {}, "pending_followup": 0}

    result = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", {"page_size": 100})
    if not result:
        return {"total": 0, "by_status": {}, "pending_followup": 0}

    pages = result.get("results", [])
    total = len(pages)
    by_status = {}
    pending_followup = 0
    today = date.today().isoformat()

    for page in pages:
        props = page.get("properties", {})
        status = props.get("Status", {}).get("select", {})
        status_name = status.get("name", "Unknown") if status else "Unknown"
        by_status[status_name] = by_status.get(status_name, 0) + 1

        followup_due = props.get("Follow-up Due", {}).get("date", {})
        followup_sent = props.get("Follow-up Sent", {}).get("checkbox", False)
        if followup_due and followup_due.get("start", "") <= today and not followup_sent:
            pending_followup += 1

    return {"total": total, "by_status": by_status, "pending_followup": pending_followup}


def create_sheet_if_missing():
    """No-op -- Notion database already exists."""
    pass
