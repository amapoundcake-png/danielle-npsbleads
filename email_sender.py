"""
email_sender.py — Brevo SMTP sender with profile-based inbox routing.

Profiles:
  warmup       -> hello@danniadams.me
  nonprofit    -> speaking@danniadams.me
  speaker      -> speaking@danniadams.me
  brand        -> partnerships@danniadams.me
  talent       -> partnerships@danniadams.me

Rate limiting: 30-90 second random delay between sends.
Send window: 9 AM - 5 PM Eastern.
"""

import logging
import random
import smtplib
import time
from datetime import datetime, time as dtime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EASTERN = timezone(timedelta(hours=-4))

from config import (
    BREVO_SMTP_HOST,
    BREVO_SMTP_PORT,
    BREVO_SMTP_LOGIN,
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

logger = logging.getLogger(__name__)

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


def _wait_for_send_slot() -> None:
    global _last_send_time
    while True:
        if not _in_send_window():
            now_dt = _now_eastern()
            window_start = now_dt.replace(hour=SEND_WINDOW_START_HOUR, minute=0, second=0, microsecond=0)
            if now_dt.time() < dtime(SEND_WINDOW_START_HOUR, 0):
                wait_seconds = (window_start - now_dt).total_seconds()
            else:
                tomorrow = (now_dt + timedelta(days=1)).replace(
                    hour=SEND_WINDOW_START_HOUR, minute=0, second=0, microsecond=0
                )
                wait_seconds = (tomorrow - now_dt).total_seconds()
            logger.info("Outside send window. Waiting %.0f minutes.", wait_seconds / 60)
            time.sleep(wait_seconds)
            continue

        now = time.time()
        spacing = random.randint(EMAIL_SPACING_MIN_SECONDS, EMAIL_SPACING_MAX_SECONDS)
        elapsed = now - _last_send_time
        if elapsed < spacing:
            wait = spacing - elapsed
            logger.info("Rate limiting: waiting %.0f seconds before next send.", wait)
            time.sleep(wait)
            continue

        break


def send_email(
    to_address: str,
    subject: str,
    body: str,
    profile: str = "warmup",
    is_html: bool = True,
    respect_rate_limit: bool = True,
) -> bool:
    """
    Send an email via Brevo SMTP.

    Args:
        to_address: recipient email
        subject: email subject
        body: email body (HTML by default)
        profile: one of warmup / nonprofit / speaker / brand / talent
        is_html: True if body is HTML
        respect_rate_limit: False for testing only

    Returns:
        True if sent, False otherwise.
    """
    global _last_send_time

    from_address = PROFILE_INBOXES.get(profile, SENDER_EMAIL_HELLO)

    if respect_rate_limit:
        _wait_for_send_slot()

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{SENDER_NAME} <{from_address}>"
    msg["To"] = to_address
    msg["Subject"] = subject
    msg["Reply-To"] = from_address
    content_type = "html" if is_html else "plain"
    msg.attach(MIMEText(body, content_type, "utf-8"))

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with smtplib.SMTP(BREVO_SMTP_HOST, BREVO_SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(BREVO_SMTP_LOGIN, BREVO_SMTP_KEY)
                server.sendmail(from_address, to_address, msg.as_string())

            _last_send_time = time.time()
            logger.info("Sent [%s] to %s: %s", profile, to_address, subject)
            return True

        except smtplib.SMTPAuthenticationError as exc:
            logger.error("Brevo auth failed -- check BREVO_SMTP_KEY: %s", exc)
            return False

        except (smtplib.SMTPException, OSError) as exc:
            backoff = 2 ** attempt
            logger.warning("Attempt %d/%d failed for %s: %s. Retrying in %ds.", attempt, MAX_RETRIES, to_address, exc, backoff)
            if attempt < MAX_RETRIES:
                time.sleep(backoff)

    logger.error("All %d attempts failed for %s.", MAX_RETRIES, to_address)
    return False
