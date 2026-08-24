"""
email_sender.py -- Privateemail (Namecheap) SMTP sender for danniadams.me.

SMTP host : mail.privateemail.com
Port      : 587 (STARTTLS)
Auth      : full email address + your Namecheap email account password

Features:
- Profile-based sender selection (speaking / partnerships / hello @danniadams.me)
- Retry logic (up to 3 attempts with exponential backoff)
- Rate limiting: random 8-25 minute gap between sends
- Daily send window: 9 AM to 5 PM Eastern -- no sends outside that window
"""

import logging
import random
import smtplib
import time
from datetime import datetime, time as dtime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

# US Eastern Time (UTC-4 EDT)
EASTERN = timezone(timedelta(hours=-4))

from config import (
    EMAIL_ADDRESS_SPEAKER,
    EMAIL_PASSWORD_SPEAKER,
    EMAIL_ADDRESS_BRAND,
    EMAIL_PASSWORD_BRAND,
    EMAIL_ADDRESS_GENERAL,
    EMAIL_PASSWORD_GENERAL,
    SMTP_HOST,
    SMTP_PORT,
    SENDER_NAME,
    EMAIL_SPACING_MIN_SECONDS,
    EMAIL_SPACING_MAX_SECONDS,
    SEND_WINDOW_START_HOUR,
    SEND_WINDOW_END_HOUR,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

# Map profile -> (from_address, password)
PROFILE_CREDENTIALS = {
    "speaker":    (EMAIL_ADDRESS_SPEAKER,  EMAIL_PASSWORD_SPEAKER),
    "conference": (EMAIL_ADDRESS_SPEAKER,  EMAIL_PASSWORD_SPEAKER),
    "fort_myers": (EMAIL_ADDRESS_SPEAKER,  EMAIL_PASSWORD_SPEAKER),
    "brand":      (EMAIL_ADDRESS_BRAND,    EMAIL_PASSWORD_BRAND),
    "press":      (EMAIL_ADDRESS_GENERAL,  EMAIL_PASSWORD_GENERAL),
    "podcast":    (EMAIL_ADDRESS_GENERAL,  EMAIL_PASSWORD_GENERAL),
    "general":    (EMAIL_ADDRESS_GENERAL,  EMAIL_PASSWORD_GENERAL),
}

# Module-level tracking of when the last email was sent (epoch seconds)
_last_send_time: float = 0.0


def _now_eastern() -> datetime:
    return datetime.now(tz=timezone.utc).astimezone(EASTERN)


def _in_send_window() -> bool:
    now = _now_eastern().time()
    return dtime(SEND_WINDOW_START_HOUR, 0) <= now < dtime(SEND_WINDOW_END_HOUR, 0)


def get_next_send_time() -> Optional[datetime]:
    """Return the earliest datetime when the next email can be sent."""
    global _last_send_time
    now = time.time()
    spacing = random.randint(EMAIL_SPACING_MIN_SECONDS, EMAIL_SPACING_MAX_SECONDS)
    earliest_by_spacing = _last_send_time + spacing
    earliest_dt = datetime.fromtimestamp(
        max(now, earliest_by_spacing), tz=timezone.utc
    ).astimezone(EASTERN)

    window_start = earliest_dt.replace(hour=SEND_WINDOW_START_HOUR, minute=0, second=0, microsecond=0)
    window_end   = earliest_dt.replace(hour=SEND_WINDOW_END_HOUR,   minute=0, second=0, microsecond=0)

    if earliest_dt < window_start:
        return window_start
    if earliest_dt >= window_end:
        return (earliest_dt + timedelta(days=1)).replace(
            hour=SEND_WINDOW_START_HOUR, minute=0, second=0, microsecond=0
        )
    return earliest_dt


def _wait_for_send_slot() -> None:
    """Block until inside the send window and past the minimum spacing gap."""
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

        spacing = random.randint(EMAIL_SPACING_MIN_SECONDS, EMAIL_SPACING_MAX_SECONDS)
        elapsed = time.time() - _last_send_time
        if elapsed < spacing:
            wait = spacing - elapsed
            logger.info("Rate limiting: waiting %.1f minutes before next send.", wait / 60)
            time.sleep(wait)
            continue

        break


def _build_message(
    to_address: str,
    subject: str,
    body: str,
    from_address: str,
    is_html: bool = False,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{SENDER_NAME} <{from_address}>"
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html" if is_html else "plain", "utf-8"))
    return msg


def send_email(
    to_address: str,
    subject: str,
    body: str,
    profile: str = "general",
    is_html: bool = False,
    respect_rate_limit: bool = True,
) -> bool:
    """
    Send an email from the correct @danniadams.me address for the given profile.

    profile options:
        "speaker"    -> speaking@danniadams.me
        "conference" -> speaking@danniadams.me
        "fort_myers" -> speaking@danniadams.me
        "brand"      -> partnerships@danniadams.me
        "press"      -> hello@danniadams.me
        "podcast"    -> hello@danniadams.me
        "general"    -> hello@danniadams.me  (default)

    Returns True if sent successfully, False otherwise.
    """
    global _last_send_time

    from_address, password = PROFILE_CREDENTIALS.get(
        profile, (EMAIL_ADDRESS_GENERAL, EMAIL_PASSWORD_GENERAL)
    )

    if not password:
        logger.error(
            "No password configured for '%s' (%s). "
            "Add EMAIL_PASSWORD_%s to your .env file.",
            profile, from_address, profile.upper(),
        )
        return False

    if respect_rate_limit:
        _wait_for_send_slot()

    msg = _build_message(to_address, subject, body, from_address, is_html)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(from_address, password)
                server.sendmail(from_address, to_address, msg.as_string())

            _last_send_time = time.time()
            logger.info("Sent to %s (attempt %d) [%s]: %s", to_address, attempt, from_address, subject)
            return True

        except smtplib.SMTPAuthenticationError as exc:
            logger.error(
                "Authentication failed for %s -- check EMAIL_PASSWORD_%s in .env: %s",
                from_address, profile.upper(), exc,
            )
            return False  # No point retrying auth errors

        except (smtplib.SMTPException, OSError) as exc:
            backoff = 2 ** attempt
            logger.warning(
                "Send attempt %d/%d failed for %s: %s. Retrying in %ds.",
                attempt, MAX_RETRIES, to_address, exc, backoff,
            )
            if attempt < MAX_RETRIES:
                time.sleep(backoff)

    logger.error("All %d send attempts failed for %s.", MAX_RETRIES, to_address)
    return False
