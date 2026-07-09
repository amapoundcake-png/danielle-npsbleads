"""
wednesday_personal_sends.py — Personal follow-ups to July 3 and July 6 Calendly clickers.

Sends Wednesday July 8, 2026 at 9 AM ET.
"""

import logging
import sys
from email_sender import send_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s -- %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

SENDER_SIG = (
    "<strong>Danielle Adams</strong><br>"
    "hello@danniadams.me"
)

CALENDLY = "https://calendly.com/danielleadamsfl/15min"

PERSONAL_EMAILS = [
    {
        "to": "info@cftampabay.org",
        "org": "Community Foundation of Tampa Bay",
        "profile": "nonprofit",
        "subject": "Re: A few ideas for Community Foundation of Tampa Bay",
        "body": (
            "Hi,<br><br>"
            "I saw you looked at my calendar earlier this week and wanted to follow up personally. "
            "I have a few specific ideas for Community Foundation of Tampa Bay around visibility and "
            "community storytelling that I think would be worth 20 minutes.<br><br>"
            "Would Wednesday or Thursday work for a quick call? I can work around your schedule.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "info@dawningfamilyservices.org",
        "org": "Dawning Family Services",
        "profile": "nonprofit",
        "subject": "Re: Outreach and visibility for Dawning Family Services",
        "body": (
            "Hi,<br><br>"
            "Just following up on my note from last week. I have a few specific ideas for "
            "Dawning Family Services around outreach and community visibility that I would love to share.<br><br>"
            "Would Wednesday or Thursday work for a quick call? Happy to keep it to 20 minutes.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "info@habitathillsborough.org",
        "org": "Habitat for Humanity of Hillsborough County",
        "profile": "nonprofit",
        "subject": "Re: Quick idea for Habitat for Humanity of Hillsborough County",
        "body": (
            "Hi,<br><br>"
            "Following up on my note from last week. You checked out my calendar and I wanted to "
            "reach back out personally in case the timing just was not right in that moment.<br><br>"
            "I have specific ideas for Habitat around outreach and supporter visibility that I think "
            "would be genuinely useful. Would Wednesday or Thursday work for a 20-minute call?<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "info@bbbstampabay.org",
        "org": "Big Brothers Big Sisters of Tampa Bay",
        "profile": "nonprofit",
        "subject": "Re: A few ideas for Big Brothers Big Sisters of Tampa Bay",
        "body": (
            "Hi,<br><br>"
            "I wanted to follow up on my note from last week. I have a few specific ideas for "
            "Big Brothers Big Sisters around community engagement and outreach that I would love to "
            "walk through with you.<br><br>"
            "Would Wednesday or Thursday work for a quick 20-minute call? I can work around your schedule.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
]


def run():
    logger.info("=== WEDNESDAY PERSONAL SENDS: %d emails ===", len(PERSONAL_EMAILS))
    sent = 0
    failed = 0
    for item in PERSONAL_EMAILS:
        success = send_email(
            to_address=item["to"],
            subject=item["subject"],
            body=item["body"],
            profile=item["profile"],
            is_html=True,
            respect_rate_limit=True,
            org=item["org"],
        )
        if success:
            logger.info("Sent to %s (%s)", item["org"], item["to"])
            sent += 1
        else:
            logger.error("Failed: %s (%s)", item["org"], item["to"])
            failed += 1

    logger.info("=== DONE: sent %d, failed %d ===", sent, failed)


if __name__ == "__main__":
    run()
