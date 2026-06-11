"""
email_sender.py — Gmail SMTP sender with App Password auth.

Features:
- Plain-text email sending via smtplib + STARTTLS
- Retry logic (up to 3 attempts with exponential backoff)
- Rate limiting: enforces a random 8-25 minute gap between sends
- Daily send window: 9 AM – 5 PM local time (no sends outside that window)
"""

import logging
import random
import smtplib
import time
from datetime import datetime, time as dtime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")

from config import (
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    SENDER_NAME,
    EMAIL_SPACING_MIN_SECONDS,
    EMAIL_SPACING_MAX_SECONDS,
    SEND_WINDOW_START_HOUR,
    SEND_WINDOW_END_HOUR,
)

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
MAX_RETRIES = 3

# Module-level tracking of when the last email was sent (epoch seconds)
_last_send_time: float = 0.0


def _now_eastern() -> datetime:
    """Return current time in US Eastern (EDT or EST, DST-aware)."""
    return datetime.now(tz=EASTERN)


def _in_send_window() -> bool:
    """Return True if the current Eastern time is within the 9 AM–5 PM send window."""
    now = _now_eastern().time()
    window_start = dtime(SEND_WINDOW_START_HOUR, 0)
    window_end = dtime(SEND_WINDOW_END_HOUR, 0)
    return window_start <= now < window_end


def get_next_send_time() -> Optional[datetime]:
    """
    Return the earliest datetime when the next email can be sent.

    Accounts for both the minimum spacing gap and the daily send window.
    Returns None if it cannot be determined (e.g. outside today's window and
    next window is tomorrow — caller should reschedule).
    """
    global _last_send_time
    now = time.time()
    spacing = random.randint(EMAIL_SPACING_MIN_SECONDS, EMAIL_SPACING_MAX_SECONDS)
    earliest_by_spacing = _last_send_time + spacing

    # Convert to datetime for window check (in Eastern time)
    earliest_dt = datetime.fromtimestamp(max(now, earliest_by_spacing), tz=timezone.utc).astimezone(EASTERN)

    window_start = earliest_dt.replace(
        hour=SEND_WINDOW_START_HOUR, minute=0, second=0, microsecond=0
    )
    window_end = earliest_dt.replace(
        hour=SEND_WINDOW_END_HOUR, minute=0, second=0, microsecond=0
    )

    if earliest_dt < window_start:
        return window_start
    if earliest_dt >= window_end:
        # Next window is tomorrow morning
        tomorrow_start = (earliest_dt + timedelta(days=1)).replace(
            hour=SEND_WINDOW_START_HOUR, minute=0, second=0, microsecond=0
        )
        return tomorrow_start
    return earliest_dt


def _wait_for_send_slot() -> None:
    """Block until we are allowed to send (window + spacing respected)."""
    global _last_send_time
    while True:
        if not _in_send_window():
            now_dt = _now_eastern()
            window_start = now_dt.replace(
                hour=SEND_WINDOW_START_HOUR, minute=0, second=0, microsecond=0
            )
            if now_dt.time() < dtime(SEND_WINDOW_START_HOUR, 0):
                wait_seconds = (window_start - now_dt).total_seconds()
            else:
                tomorrow = (now_dt + timedelta(days=1)).replace(
                    hour=SEND_WINDOW_START_HOUR, minute=0, second=0, microsecond=0
                )
                wait_seconds = (tomorrow - now_dt).total_seconds()
            logger.info(
                "Outside send window. Waiting %.0f minutes until %s.",
                wait_seconds / 60,
                datetime.fromtimestamp(time.time() + wait_seconds).strftime("%H:%M"),
            )
            time.sleep(wait_seconds)
            continue

        now = time.time()
        spacing = random.randint(EMAIL_SPACING_MIN_SECONDS, EMAIL_SPACING_MAX_SECONDS)
        elapsed = now - _last_send_time
        if elapsed < spacing:
            wait = spacing - elapsed
            logger.info(
                "Rate limiting: waiting %.1f minutes before next send.", wait / 60
            )
            time.sleep(wait)
            continue

        break  # All clear


def _build_message(
    to_address: str,
    subject: str,
    body: str,
    is_html: bool = False,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{SENDER_NAME} <{GMAIL_ADDRESS}>"
    msg["To"] = to_address
    msg["Subject"] = subject
    content_type = "html" if is_html else "plain"
    msg.attach(MIMEText(body, content_type, "utf-8"))
    return msg


def send_email(
    to_address: str,
    subject: str,
    body: str,
    is_html: bool = False,
    respect_rate_limit: bool = True,
) -> bool:
    """
    Send an email via Gmail SMTP.

    Args:
        to_address: recipient email address
        subject: email subject line
        body: email body (plain text or HTML)
        is_html: set True if body contains HTML
        respect_rate_limit: set False to skip spacing/window checks (e.g. for testing)

    Returns:
        True if sent successfully, False otherwise.
    """
    global _last_send_time

    if respect_rate_limit:
        _wait_for_send_slot()

    msg = _build_message(to_address, subject, body, is_html)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                server.sendmail(GMAIL_ADDRESS, to_address, msg.as_string())

            _last_send_time = time.time()
            logger.info("Email sent to %s (attempt %d): %s", to_address, attempt, subject)
            return True

        except smtplib.SMTPAuthenticationError as exc:
            logger.error("SMTP authentication failed — check GMAIL_APP_PASSWORD: %s", exc)
            return False  # No point retrying auth errors

        except (smtplib.SMTPException, OSError) as exc:
            backoff = 2 ** attempt
            logger.warning(
                "Send attempt %d/%d failed for %s: %s. Retrying in %ds.",
                attempt,
                MAX_RETRIES,
                to_address,
                exc,
                backoff,
            )
            if attempt < MAX_RETRIES:
                time.sleep(backoff)

    logger.error("All %d send attempts failed for %s.", MAX_RETRIES, to_address)
    return False
