"""
email_sender.py — Brevo API sender with profile-based inbox routing.

Switched from SMTP to Brevo HTTP API (port 443) to avoid Railway port 587 block.

Profiles:
  warmup       -> hello@danniadams.me
  nonprofit    -> hello@danniadams.me
  speaker      -> speaking@danniadams.me
  brand        -> partnerships@danniadams.me
  talent       -> partnerships@danniadams.me

Rate limiting: 45-90 minute random delay between sends.
Send window: 9 AM - 5 PM Eastern.
"""

import logging
import os
import random
import time
import requests
from datetime import datetime, time as dtime, timezone, timedelta

EASTERN = timezone(timedelta(hours=-4))

from config import (
    BREVO_SMTP_KEY,
    SENDER_NAME,
    SENDER_EMAIL_HELLO,
    SENDER_EMAIL_SPEAKING,
    SENDER_EMAIL_PARTNERSHIPS,
    EMAIL_SPACING_MIN_SECONDS,
    EMAIL_SPACING_MAX_SECONDS,
    SEND_WINDOW_START_HOUR,
    SEND_WINDOW_END_HOUR,
)

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "") or BREVO_SMTP_KEY

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
MAX_RETRIES = 3
_last_send_time: float = 0.0

PROFILE_INBOXES = {
    "warmup": SENDER_EMAIL_HELLO,
    "nonprofit": SENDER_EMAIL_HELLO,
    "speaker": SENDER_EMAIL_SPEAKING,
    "brand": SENDER_EMAIL_PARTNERSHIPS,
    "talent": SENDER_EMAIL_PARTNERSHIPS,
}


def _now_eastern() -> datetime:
    return datetime.now(tz=timezone.utc).astimezone(EASTERN)


def _in_send_window() -> bool:
    now = _now_eastern().time()
    return dtime(SEND_WINDOW_START_HOUR, 0) <= now < dtime(SEND_WINDOW_END_HOUR, 0)


def _wait_for_send_window() -> None:
    """Block until we're inside the 9 AM - 5 PM ET send window."""
    while not _in_send_window():
        now_et = _now_eastern()
        logger.info("Outside send window (%s ET). Sleeping 5 minutes.", now_et.strftime("%H:%M"))
        time.sleep(300)


def _wait_for_rate_limit() -> None:
    global _last_send_time
    now = time.time()
    spacing = random.randint(EMAIL_SPACING_MIN_SECONDS, EMAIL_SPACING_MAX_SECONDS)
    elapsed = now - _last_send_time
    if elapsed < spacing:
        wait = spacing - elapsed
        logger.info("Rate limiting: waiting %.0f seconds before next send.", wait)
        time.sleep(wait)


def send_email(
    to_address: str,
    subject: str,
    body: str,
    profile: str = "warmup",
    is_html: bool = True,
    respect_rate_limit: bool = True,
) -> bool:
    global _last_send_time

    from_address = PROFILE_INBOXES.get(profile, SENDER_EMAIL_HELLO)

    if respect_rate_limit:
        _wait_for_send_window()
        _wait_for_rate_limit()

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {"name": SENDER_NAME, "email": from_address},
        "to": [{"email": to_address}],
        "replyTo": {"email": from_address},
        "subject": subject,
    }

    if is_html:
        payload["htmlContent"] = body
    else:
        payload["textContent"] = body

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(BREVO_API_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                _last_send_time = time.time()
                logger.info("Sent [%s] to %s: %s", profile, to_address, subject)
                return True
            elif resp.status_code == 401:
                logger.error("Brevo auth failed -- check BREVO_SMTP_KEY: %s", resp.text)
                return False
            else:
                logger.warning(
                    "Attempt %d/%d failed for %s: HTTP %d %s. Retrying in %ds.",
                    attempt, MAX_RETRIES, to_address, resp.status_code, resp.text, 2 ** attempt
                )
        except requests.RequestException as exc:
            logger.warning(
                "Attempt %d/%d failed for %s: %s. Retrying in %ds.",
                attempt, MAX_RETRIES, to_address, exc, 2 ** attempt
            )

        if attempt < MAX_RETRIES:
            time.sleep(2 ** attempt)

    logger.error("All %d attempts failed for %s.", MAX_RETRIES, to_address)
    return False
