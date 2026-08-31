"""
brevo_events.py — Pull recent email engagement events from the Brevo API.

Used by run_slack_alerts() to detect opens/clicks and trigger Slack notifications,
and by run_pipeline_followups() to know which leads are hot vs cold.
"""

import logging
import os
from datetime import date, timedelta

import requests

logger = logging.getLogger(__name__)

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_EVENTS_URL = "https://api.brevo.com/v3/smtp/statistics/events"


def get_events_for_email(recipient_email: str, days_back: int = 14) -> list[dict]:
    """
    Fetch Brevo events (sent/delivered/opened/clicked/bounced) for a specific
    recipient email address over the past `days_back` days.

    Returns a list of event dicts: [{event, date, subject, messageId}, ...]
    """
    if not BREVO_API_KEY:
        logger.warning("BREVO_API_KEY not set — cannot fetch email events.")
        return []

    start = (date.today() - timedelta(days=days_back)).isoformat()
    end = date.today().isoformat()

    headers = {"api-key": BREVO_API_KEY, "Accept": "application/json"}
    params = {
        "email": recipient_email,
        "startDate": start,
        "endDate": end,
        "limit": 100,
        "offset": 0,
    }

    try:
        resp = requests.get(BREVO_EVENTS_URL, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("events", [])
    except Exception as exc:
        logger.warning("Brevo events fetch failed for %s: %s", recipient_email, exc)
        return []


def get_recent_events(days_back: int = 1) -> list[dict]:
    """
    Fetch ALL email events across all recipients for the past `days_back` days.

    Returns a list of event dicts: [{event, email, date, subject, messageId}, ...]
    Useful for sweeping all activity in the last 24 hours.
    """
    if not BREVO_API_KEY:
        logger.warning("BREVO_API_KEY not set — cannot fetch email events.")
        return []

    start = (date.today() - timedelta(days=days_back)).isoformat()
    end = date.today().isoformat()

    headers = {"api-key": BREVO_API_KEY, "Accept": "application/json"}
    all_events = []

    for event_type in ("opened", "clicks"):
        offset = 0
        while True:
            params = {
                "event": event_type,
                "startDate": start,
                "endDate": end,
                "limit": 100,
                "offset": offset,
            }
            try:
                resp = requests.get(BREVO_EVENTS_URL, headers=headers, params=params, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                batch = data.get("events", [])
                all_events.extend(batch)
                if len(batch) < 100:
                    break
                offset += 100
            except Exception as exc:
                logger.warning("Brevo events sweep failed (type=%s): %s", event_type, exc)
                break

    return all_events


def summarize_engagement(events: list[dict]) -> dict:
    """
    Summarize events by recipient email.

    Returns:
        {
          "info@example.org": {
            "opens": 3,
            "clicks": 1,
            "is_hot": True,   # opened 2+ times OR clicked anything
            "subjects": ["subject line 1"],
            "latest_event": "2026-08-31T14:00:00Z",
          },
          ...
        }
    """
    summary = {}

    for ev in events:
        email = ev.get("email", "").lower().strip()
        if not email:
            continue

        if email not in summary:
            summary[email] = {
                "opens": 0,
                "clicks": 0,
                "is_hot": False,
                "subjects": [],
                "latest_event": "",
            }

        ev_type = ev.get("event", "")
        if ev_type == "opened":
            summary[email]["opens"] += 1
        elif ev_type == "clicks":
            summary[email]["clicks"] += 1

        subject = ev.get("subject", "")
        if subject and subject not in summary[email]["subjects"]:
            summary[email]["subjects"].append(subject)

        ev_date = ev.get("date", "")
        if ev_date > summary[email]["latest_event"]:
            summary[email]["latest_event"] = ev_date

    # Mark hot leads
    for email, data in summary.items():
        if data["opens"] >= 2 or data["clicks"] >= 1:
            data["is_hot"] = True

    return summary
