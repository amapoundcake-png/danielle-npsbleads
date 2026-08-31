"""
slack_notifier.py — Send Slack alerts to Danni when leads engage.

Sends to the SLACK_WEBHOOK_URL Railway env var.
Messages include who engaged, what they did, and a suggested reply draft.
Danni replies herself — this module never sends the email.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


def _post(message: str) -> bool:
    """Post a plain text message to Slack."""
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set — Slack alert skipped.")
        return False
    try:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("Slack post failed: %s", exc)
        return False


def alert_hot_lead(
    org_name: str,
    contact_email: str,
    opens: int,
    clicks: int,
    subject: str,
    lane: str,
    suggested_reply: str,
) -> bool:
    """
    Alert Danni that a lead is hot — multiple opens or a Calendly click.
    Includes a suggested reply she can copy/paste and send herself.
    """
    activity = []
    if opens >= 1:
        activity.append(f"opened {opens}x")
    if clicks >= 1:
        activity.append(f"clicked {clicks}x")
    activity_str = " + ".join(activity)

    message = f"""
🔥 *HOT LEAD — {org_name}*

*Email:* {contact_email}
*Subject they opened:* {subject}
*Activity:* {activity_str}
*Lane:* {lane}

---

*Suggested reply (send from your own inbox):*

{suggested_reply}

---
Do NOT reply here — send from your email directly.
""".strip()

    return _post(message)


def alert_daily_summary(sent: int, followups: int, hot_leads: int) -> bool:
    """Post a quick daily summary to Slack after the cron run."""
    message = (
        f"📬 *Daily cron complete*\n"
        f"Emails sent today: {sent}\n"
        f"Follow-ups sent: {followups}\n"
        f"Hot leads flagged: {hot_leads}"
    )
    return _post(message)


def build_suggested_reply(org_name: str, lane: str, contact_email: str) -> str:
    """
    Build a short suggested reply draft based on lane type.
    Danni reads it, personalizes it, and sends from her own inbox.
    """
    lane_replies = {
        "nonprofit_consulting": (
            f"Hi,\n\n"
            f"Thanks for taking a look at my note about {org_name}. "
            f"I'd love to connect and hear what's on your plate right now. "
            f"Even 20 minutes would be helpful — I can come ready with a few specific ideas.\n\n"
            f"Would any time this week or next work for you?\n\n"
            f"Danielle"
        ),
        "nonprofit_speaking": (
            f"Hi,\n\n"
            f"I noticed you took a look — wanted to follow up and see if a speaking engagement at {org_name} might be something worth exploring. "
            f"Happy to share more about my topics and past engagements.\n\n"
            f"Would a quick call work?\n\n"
            f"Danni"
        ),
        "youth_speaking": (
            f"Hi,\n\n"
            f"Thanks for opening my note! I'd love the chance to bring something real to your students at {org_name}. "
            f"My talk on resilience and showing up before you feel ready has resonated a lot with young people.\n\n"
            f"Open to a quick conversation?\n\n"
            f"Danni"
        ),
        "universities": (
            f"Hi,\n\n"
            f"I saw you checked out my message — I'd love to connect about a potential speaking engagement at {org_name}. "
            f"I speak on personal branding, the creator economy, and career reinvention for students.\n\n"
            f"Can we set up a quick call?\n\n"
            f"Danni"
        ),
        "venue_hosting": (
            f"Hi,\n\n"
            f"Thanks for the peek! If {org_name} is ever looking for a host or emcee, I'd love to be on your radar. "
            f"Happy to share video reel and references.\n\n"
            f"Worth a quick conversation?\n\n"
            f"Danni"
        ),
        "brand_partnerships": (
            f"Hi,\n\n"
            f"I noticed you opened my note about a potential partnership. "
            f"I'd love to hear more about what {org_name} has coming up and see if there's a natural fit with my audience.\n\n"
            f"Open to a quick call?\n\n"
            f"Danni"
        ),
        "talent_representation": (
            f"Hi,\n\n"
            f"Thanks for taking a look. I'd welcome the chance to connect about representation — "
            f"happy to share my full reel, credits, and recent campaign work.\n\n"
            f"Would a brief call work for you?\n\n"
            f"Danni"
        ),
    }

    return lane_replies.get(lane, (
        f"Hi,\n\nThanks for opening my note about {org_name}. "
        f"I'd love to connect — would a quick call work?\n\nDanni"
    ))
