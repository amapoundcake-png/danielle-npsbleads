"""
test_inboxes.py — Send one test email from speaking@ and one from partnerships@.

Run once manually: python test_inboxes.py
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

TEST_TO = "amapoundcake@gmail.com"

TESTS = [
    {
        "profile": "speaker",
        "subject": "TEST — speaking@ inbox check",
        "body": (
            "This is a test email sent from speaking@danniadams.me.<br><br>"
            "If you received this, the speaking inbox is working correctly."
        ),
    },
    {
        "profile": "brand",
        "subject": "TEST — partnerships@ inbox check",
        "body": (
            "This is a test email sent from partnerships@danniadams.me.<br><br>"
            "If you received this, the partnerships inbox is working correctly."
        ),
    },
]


def run():
    logger.info("=== INBOX TEST: sending %d emails ===", len(TESTS))
    for t in TESTS:
        success = send_email(
            to_address=TEST_TO,
            subject=t["subject"],
            body=t["body"],
            profile=t["profile"],
            is_html=True,
            respect_rate_limit=False,  # bypass window + delay for testing
        )
        status = "OK" if success else "FAILED"
        logger.info("[%s] profile=%s -> %s", status, t["profile"], TEST_TO)
    logger.info("=== TEST COMPLETE ===")


if __name__ == "__main__":
    run()
