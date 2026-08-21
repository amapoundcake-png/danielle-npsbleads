"""
creator_tracker.py — Central Florida creator/influencer database.

A lightweight CRM for tracking creators discovered through event research,
brand-campaign news, or manual research, so they can be evaluated for
cross-promotion, event partnerships, or brand-fit matching alongside
Danni's own outreach.

Columns match the schema requested for this research pass:

  Name, Platform, Followers, Average Engagement, Content Category,
  Location, Email, Audience Demographics, Brand Partnerships,
  Previous Events, Estimated Creator Tier, Contact Status,
  Last Contacted, Response, Brand-Fit Categories

Data lives in creators_database.csv (created automatically). Records are
matched/deduped on (Name, Platform).

Usage:
    python creator_tracker.py list
    python creator_tracker.py summary
"""

import csv
import logging
import os
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

CREATOR_CSV = os.path.join(os.path.dirname(__file__), "creators_database.csv")

CREATOR_COLUMNS = [
    "Name",
    "Platform",
    "Followers",
    "Average Engagement",
    "Content Category",
    "Location",
    "Email",
    "Audience Demographics",
    "Brand Partnerships",
    "Previous Events",
    "Estimated Creator Tier",
    "Contact Status",
    "Last Contacted",
    "Response",
    "Brand-Fit Categories",
]

# Standard follower bands used to auto-fill "Estimated Creator Tier" when
# it isn't supplied directly.
TIER_BANDS = [
    (0, 10_000, "Nano"),
    (10_000, 50_000, "Micro"),
    (50_000, 250_000, "Mid-tier"),
    (250_000, 1_000_000, "Macro"),
    (1_000_000, float("inf"), "Mega"),
]

CONTACT_STATUSES = ["Not Contacted", "Researching", "Contacted", "Replied", "Booked", "Passed"]


def estimate_tier(followers) -> str:
    """Estimate creator tier from a raw follower count (accepts '12,400' or 12400)."""
    try:
        count = int(str(followers).replace(",", "").strip())
    except (ValueError, TypeError):
        return "Unknown"
    for low, high, label in TIER_BANDS:
        if low <= count < high:
            return label
    return "Unknown"


def _ensure_csv(filepath: str = CREATOR_CSV) -> None:
    if not os.path.exists(filepath):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CREATOR_COLUMNS)
            writer.writeheader()
        logger.info("Created new creator database at %s", filepath)


def load_creators(filepath: str = CREATOR_CSV) -> list[dict]:
    """Load all creator records from the CSV."""
    _ensure_csv(filepath)
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def save_creators(creators: list[dict], filepath: str = CREATOR_CSV) -> None:
    """Overwrite the CSV with the given list of creator records."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CREATOR_COLUMNS)
        writer.writeheader()
        for row in creators:
            writer.writerow({col: row.get(col, "") for col in CREATOR_COLUMNS})


def _key(record: dict) -> tuple:
    return (record.get("Name", "").strip().lower(), record.get("Platform", "").strip().lower())


def upsert_creator(record: dict, filepath: str = CREATOR_CSV) -> None:
    """
    Add a new creator or merge fields into an existing one, matched on
    (Name, Platform). Auto-fills Estimated Creator Tier from Followers and
    defaults Contact Status to 'Not Contacted' if not provided.
    """
    if not record.get("Name") or not record.get("Platform"):
        raise ValueError("upsert_creator requires at least Name and Platform")

    creators = load_creators(filepath)
    record = {col: record.get(col, "") for col in CREATOR_COLUMNS}

    if record.get("Followers") and not record.get("Estimated Creator Tier"):
        record["Estimated Creator Tier"] = estimate_tier(record["Followers"])
    if not record.get("Contact Status"):
        record["Contact Status"] = "Not Contacted"

    target_key = _key(record)
    for idx, existing in enumerate(creators):
        if _key(existing) == target_key:
            merged = {**existing, **{k: v for k, v in record.items() if v}}
            creators[idx] = merged
            save_creators(creators, filepath)
            logger.info("Updated creator: %s (%s)", record.get("Name"), record.get("Platform"))
            return

    creators.append(record)
    save_creators(creators, filepath)
    logger.info("Added new creator: %s (%s)", record.get("Name"), record.get("Platform"))


def mark_contacted(name: str, platform: str, filepath: str = CREATOR_CSV) -> bool:
    """Set Contact Status to 'Contacted' and stamp today's date."""
    creators = load_creators(filepath)
    for row in creators:
        if _key(row) == (name.strip().lower(), platform.strip().lower()):
            row["Contact Status"] = "Contacted"
            row["Last Contacted"] = date.today().isoformat()
            save_creators(creators, filepath)
            return True
    logger.warning("mark_contacted: no match for %s / %s", name, platform)
    return False


def record_response(name: str, platform: str, response: str, filepath: str = CREATOR_CSV) -> bool:
    """Log a reply and move status to 'Replied'."""
    creators = load_creators(filepath)
    for row in creators:
        if _key(row) == (name.strip().lower(), platform.strip().lower()):
            row["Response"] = response
            row["Contact Status"] = "Replied"
            save_creators(creators, filepath)
            return True
    logger.warning("record_response: no match for %s / %s", name, platform)
    return False


def find_by_brand_fit(category: str, filepath: str = CREATOR_CSV) -> list[dict]:
    """Return creators whose Brand-Fit Categories field contains the given category (case-insensitive)."""
    category_lower = category.strip().lower()
    return [
        c for c in load_creators(filepath)
        if category_lower in c.get("Brand-Fit Categories", "").lower()
    ]


def get_summary(filepath: str = CREATOR_CSV) -> dict:
    """Return counts by tier, content category, and contact status."""
    from collections import Counter
    creators = load_creators(filepath)
    return {
        "total": len(creators),
        "by_tier": dict(Counter(c.get("Estimated Creator Tier", "Unknown") or "Unknown" for c in creators)),
        "by_status": dict(Counter(c.get("Contact Status", "Not Contacted") or "Not Contacted" for c in creators)),
        "by_category": dict(Counter(c.get("Content Category", "Unknown") or "Unknown" for c in creators)),
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    _ensure_csv()

    command = sys.argv[1] if len(sys.argv) > 1 else "list"

    if command == "list":
        creators = load_creators()
        print(f"\n{len(creators)} creator(s) in database:\n")
        for c in creators:
            print(
                f"  {c.get('Name', '?'):<25} {c.get('Platform', ''):<12} "
                f"{c.get('Followers', ''):<10} {c.get('Estimated Creator Tier', ''):<10} "
                f"{c.get('Contact Status', '')}"
            )
        print()
    elif command == "summary":
        summary = get_summary()
        print(f"\nTotal creators : {summary['total']}")
        print(f"By tier        : {summary['by_tier']}")
        print(f"By status      : {summary['by_status']}")
        print(f"By category    : {summary['by_category']}\n")
    else:
        print("Usage: python creator_tracker.py [list|summary]")
