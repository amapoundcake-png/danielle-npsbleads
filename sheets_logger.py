"""
sheets_logger.py — Google Sheets integration via gspread + service account.

Sheet columns (in order):
  ID | Name | Org | Email | Industry | Source | Date Contacted |
  Follow-up Due | Follow-up Sent | Status | Notes
"""

import logging
import uuid
from datetime import date, timedelta, datetime
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config import (
    GOOGLE_SHEETS_ID,
    GOOGLE_SERVICE_ACCOUNT_JSON,
    SHEET_NAME,
    SHEET_COLUMNS,
    FOLLOW_UP_DAYS_MIN,
    FOLLOW_UP_DAYS_MAX,
)

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DATE_FMT = "%Y-%m-%d"

# Column index helpers (1-based for gspread)
COL = {name: idx + 1 for idx, name in enumerate(SHEET_COLUMNS)}


def _get_client() -> gspread.Client:
    creds = Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_JSON, scopes=SCOPES
    )
    return gspread.authorize(creds)


def _get_worksheet() -> gspread.Worksheet:
    client = _get_client()
    spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
    try:
        ws = spreadsheet.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = _create_sheet(spreadsheet)
    return ws


def _create_sheet(spreadsheet: gspread.Spreadsheet) -> gspread.Worksheet:
    """Add the Leads sheet with header row."""
    ws = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(SHEET_COLUMNS))
    ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
    logger.info("Created '%s' sheet with headers.", SHEET_NAME)
    return ws


def create_sheet_if_missing() -> None:
    """Public helper — ensure the sheet and header row exist."""
    _get_worksheet()  # side-effect: creates if missing
    logger.info("Sheet ready.")


def _followup_due_date() -> str:
    """Return a follow-up due date string, randomised within the configured window."""
    import random
    delta = random.randint(FOLLOW_UP_DAYS_MIN, FOLLOW_UP_DAYS_MAX)
    return (date.today() + timedelta(days=delta)).strftime(DATE_FMT)


def log_new_lead(lead: dict) -> None:
    """
    Append a new row for a freshly contacted lead.

    lead dict keys: name, org, email, industry, source, notes (all optional except email)
    """
    ws = _get_worksheet()
    lead_id = str(uuid.uuid4())[:8].upper()
    row = [
        lead_id,
        lead.get("name", ""),
        lead.get("org", ""),
        lead.get("email", ""),
        lead.get("industry", ""),
        lead.get("source", ""),
        date.today().strftime(DATE_FMT),   # Date Contacted
        _followup_due_date(),              # Follow-up Due
        "",                                # Follow-up Sent
        "Contacted",                       # Status
        lead.get("notes", ""),
    ]
    ws.append_row(row, value_input_option="RAW")
    logger.info("Logged lead: %s <%s>", lead.get("org", ""), lead.get("email", ""))


def _find_row_by_email(ws: gspread.Worksheet, email: str) -> Optional[int]:
    """Return the 1-based row index for the first match, or None."""
    email_lower = email.strip().lower()
    col_values = ws.col_values(COL["Email"])
    for idx, cell in enumerate(col_values):
        if cell.strip().lower() == email_lower:
            return idx + 1  # 1-based
    return None


def mark_replied(email: str) -> bool:
    """Set Status='Replied' and clear Follow-up Due for the given email."""
    ws = _get_worksheet()
    row = _find_row_by_email(ws, email)
    if row is None:
        logger.warning("mark_replied: email not found — %s", email)
        return False
    ws.update_cell(row, COL["Status"], "Replied")
    ws.update_cell(row, COL["Follow-up Due"], "")
    logger.info("Marked replied: %s", email)
    return True


def get_leads_needing_followup() -> list[dict]:
    """
    Return rows where:
      - Follow-up Due <= today
      - Follow-up Sent is empty
      - Status == 'Contacted'
    """
    ws = _get_worksheet()
    rows = ws.get_all_records()
    today = date.today()
    results = []
    for row in rows:
        if row.get("Status") != "Contacted":
            continue
        if row.get("Follow-up Sent"):
            continue
        due_str = row.get("Follow-up Due", "")
        if not due_str:
            continue
        try:
            due_date = datetime.strptime(due_str, DATE_FMT).date()
        except ValueError:
            continue
        if due_date <= today:
            results.append(row)
    logger.info("Leads needing follow-up: %d", len(results))
    return results


def mark_followup_sent(email: str) -> bool:
    """Set Follow-up Sent to today's date for the given email."""
    ws = _get_worksheet()
    row = _find_row_by_email(ws, email)
    if row is None:
        logger.warning("mark_followup_sent: email not found — %s", email)
        return False
    ws.update_cell(row, COL["Follow-up Sent"], date.today().strftime(DATE_FMT))
    ws.update_cell(row, COL["Status"], "Followed Up")
    logger.info("Marked follow-up sent: %s", email)
    return True


def is_already_contacted(email: str) -> bool:
    """Return True if this email already appears in the sheet."""
    ws = _get_worksheet()
    row = _find_row_by_email(ws, email)
    return row is not None


def get_summary() -> dict:
    """Return aggregate stats for the status command."""
    ws = _get_worksheet()
    rows = ws.get_all_records()
    total = len(rows)
    by_status: dict[str, int] = {}
    for row in rows:
        status = row.get("Status", "Unknown")
        by_status[status] = by_status.get(status, 0) + 1
    today = date.today()
    pending_followup = 0
    for row in rows:
        if row.get("Status") != "Contacted":
            continue
        if row.get("Follow-up Sent"):
            continue
        due_str = row.get("Follow-up Due", "")
        if not due_str:
            continue
        try:
            due_date = datetime.strptime(due_str, DATE_FMT).date()
            if due_date <= today:
                pending_followup += 1
        except ValueError:
            pass
    return {
        "total": total,
        "by_status": by_status,
        "pending_followup": pending_followup,
    }
