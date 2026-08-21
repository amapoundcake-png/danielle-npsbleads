"""
event_research.py — Central Florida event & business-signal research tool.

Scans Google News for two buckets of signals relevant to Danni's outreach
and booking pipelines:

  EVENTS (audience-facing, good for appearances / partnerships / content):
    - Black cultural events
    - Women's events
    - Creator events
    - Nonprofit programs
    - Community events
    - Holiday activations

  BUSINESS SIGNALS (partnership / outreach opportunities):
    - Brands announcing influencer campaigns
    - Companies opening Orlando/Central Florida locations
    - Brands launching products
    - Local businesses getting funding or opening
    - Nonprofits announcing campaigns/events

Google News RSS is used as the primary source because it returns clean,
static XML (title, link, source, publish date, snippet) without needing
a JS-rendering browser, and it aggregates local outlets, press releases,
and blogs. Results are filtered for Central Florida relevance, tagged
with a bucket/category, deduplicated, and appended to a CSV so the list
builds up over time instead of resetting on every run.

Usage:
    python event_research.py                        # full scan, all categories
    python event_research.py --category black_cultural
    python event_research.py --category new_location
"""

import csv
import html
import logging
import os
import re
import time
import random
from datetime import datetime
from typing import Optional
from urllib.parse import quote
import xml.etree.ElementTree as ET

import requests

from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

RESEARCH_CSV = os.path.join(os.path.dirname(__file__), "central_fl_research.csv")

RESEARCH_CSV_COLUMNS = [
    "date_found", "bucket", "category", "title", "source", "published",
    "location_hint", "link", "snippet",
]

# Used to confirm a result is actually about Central Florida, since Google
# News occasionally returns loosely-related national stories.
CENTRAL_FL_KEYWORDS = [
    "orlando", "central florida", "sanford", "winter park", "kissimmee",
    "altamonte springs", "lake nona", "apopka", "oviedo", "winter garden",
    "maitland", "casselberry", "longwood", "ocoee", "clermont",
    "orange county, fl", "seminole county", "osceola county", "volusia county",
    "polk county", "daytona beach", "deland", "windermere", "lake mary",
]

# ---------------------------------------------------------------------------
# Category -> search queries
# ---------------------------------------------------------------------------

EVENT_CATEGORIES = {
    "black_cultural": [
        "Black cultural event Orlando",
        "Black history celebration Central Florida",
        "African American festival Orlando",
        "Juneteenth event Orlando",
    ],
    "womens": [
        "women's event Orlando",
        "women's conference Central Florida",
        "women empowerment event Orlando",
        "women in business event Orlando",
    ],
    "creator": [
        "content creator event Orlando",
        "influencer meetup Orlando",
        "creator economy conference Florida",
        "social media conference Orlando",
    ],
    "nonprofit_programs": [
        "nonprofit program launch Orlando",
        "nonprofit new initiative Central Florida",
        "nonprofit workshop Orlando",
    ],
    "community": [
        "community event Orlando",
        "community festival Central Florida",
        "neighborhood event Orlando",
    ],
    "holiday_activation": [
        "holiday event Orlando",
        "holiday activation Central Florida",
        "holiday festival Orlando",
        "holiday pop-up Orlando",
    ],
}

BUSINESS_SIGNAL_CATEGORIES = {
    "influencer_campaign": [
        "brand announces influencer campaign Orlando",
        "influencer marketing campaign Florida brand",
        "brand partners with influencers Florida",
    ],
    "new_location": [
        "opens new location Orlando",
        "company opens Central Florida location",
        "expands to Orlando",
    ],
    "product_launch": [
        "brand launches new product Orlando",
        "new product launch Central Florida",
    ],
    "funding_opening": [
        "local business grant Orlando",
        "small business funding Central Florida",
        "business grand opening Orlando",
    ],
    "nonprofit_campaign": [
        "nonprofit announces campaign Orlando",
        "nonprofit launches initiative Central Florida",
        "nonprofit fundraising campaign Orlando",
    ],
}

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"


# ---------------------------------------------------------------------------
# HTTP helpers (same pattern as lead_finder.py)
# ---------------------------------------------------------------------------

def _get(url: str, **kwargs) -> Optional[requests.Response]:
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT, **kwargs)
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        logger.warning("GET failed for %s: %s", url, exc)
        return None


def _polite_delay() -> None:
    time.sleep(REQUEST_DELAY_SECONDS + random.uniform(0, 1))


def _is_central_florida(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in CENTRAL_FL_KEYWORDS)


def _search_google_news(query: str, max_results: int = 6) -> list[dict]:
    """Query Google News RSS and return parsed items (title, link, source, date, snippet)."""
    url = f"{GOOGLE_NEWS_RSS}?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
    resp = _get(url)
    if resp is None:
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        logger.warning("Failed to parse RSS for '%s': %s", query, exc)
        return []

    items = []
    for item in root.findall(".//item")[:max_results]:
        title = html.unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else ""

        clean_description = html.unescape(re.sub(r"<[^>]+>", "", description)).strip()

        if not title or not link:
            continue

        items.append({
            "title": title,
            "link": link,
            "published": pub_date,
            "snippet": clean_description[:300],
            "source": source,
        })

    return items


# ---------------------------------------------------------------------------
# Scan logic
# ---------------------------------------------------------------------------

def _run_category_scan(categories: dict, bucket: str, max_per_query: int = 6) -> list[dict]:
    """Run all queries for a bucket of categories, filter for CF relevance, tag results."""
    results = []
    for category, queries in categories.items():
        for query in queries:
            logger.info("[%s/%s] Searching: %s", bucket, category, query)
            try:
                items = _search_google_news(query, max_results=max_per_query)
            except Exception as exc:
                logger.error("Search failed for '%s': %s", query, exc)
                items = []

            for item in items:
                combined_text = f"{item['title']} {item['snippet']}"
                if not _is_central_florida(combined_text) and not _is_central_florida(query):
                    continue

                location_hint = next(
                    (kw.title() for kw in CENTRAL_FL_KEYWORDS if kw in combined_text.lower()),
                    "Central Florida",
                )

                results.append({
                    "date_found": datetime.now().strftime("%Y-%m-%d"),
                    "bucket": bucket,
                    "category": category,
                    "title": item["title"],
                    "source": item["source"],
                    "published": item["published"],
                    "location_hint": location_hint,
                    "link": item["link"],
                    "snippet": item["snippet"],
                })

            _polite_delay()

    return results


def _dedupe(results: list[dict]) -> list[dict]:
    """Remove duplicate results by link, falling back to normalized title."""
    seen_links: set = set()
    seen_titles: set = set()
    deduped = []
    for r in results:
        key_link = r.get("link", "")
        key_title = r.get("title", "").strip().lower()
        if key_link and key_link in seen_links:
            continue
        if key_title and key_title in seen_titles:
            continue
        seen_links.add(key_link)
        seen_titles.add(key_title)
        deduped.append(r)
    return deduped


def scan_events(max_per_query: int = 6) -> list[dict]:
    """Scan for the 6 audience-facing event categories."""
    return _dedupe(_run_category_scan(EVENT_CATEGORIES, "event", max_per_query))


def scan_business_signals(max_per_query: int = 6) -> list[dict]:
    """Scan for the 5 brand/business opportunity signal categories."""
    return _dedupe(_run_category_scan(BUSINESS_SIGNAL_CATEGORIES, "business_signal", max_per_query))


def run_full_research(max_per_query: int = 6) -> list[dict]:
    """Run both event and business-signal scans, combine, dedupe, return all results."""
    logger.info("=== Starting Central Florida research scan ===")
    events = scan_events(max_per_query)
    logger.info("Events found: %d", len(events))
    signals = scan_business_signals(max_per_query)
    logger.info("Business signals found: %d", len(signals))
    combined = _dedupe(events + signals)
    logger.info("Total unique results: %d", len(combined))
    return combined


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def save_to_csv(results: list[dict], filepath: str = RESEARCH_CSV, append: bool = True) -> int:
    """
    Write results to CSV. Appends to an existing file and skips any link
    already logged, so re-running the scan builds up a running research
    log instead of duplicating rows. Returns the number of new rows written.
    """
    existing_links: set = set()
    file_exists = os.path.exists(filepath)

    if append and file_exists:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_links.add(row.get("link", ""))

    mode = "a" if append and file_exists else "w"
    with open(filepath, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESEARCH_CSV_COLUMNS)
        if mode == "w":
            writer.writeheader()
        new_count = 0
        for r in results:
            if r.get("link") in existing_links:
                continue
            writer.writerow({col: r.get(col, "") for col in RESEARCH_CSV_COLUMNS})
            new_count += 1

    logger.info("Wrote %d new row(s) to %s", new_count, filepath)
    return new_count


def print_summary(results: list[dict]) -> None:
    from collections import Counter
    bucket_counts = Counter(r["bucket"] for r in results)
    category_counts = Counter(f"{r['bucket']}/{r['category']}" for r in results)

    print("\n" + "=" * 60)
    print("  CENTRAL FLORIDA RESEARCH SCAN")
    print("=" * 60)
    for bucket, count in bucket_counts.items():
        print(f"  {bucket:<20} {count}")
    print("-" * 60)
    for cat, count in sorted(category_counts.items()):
        print(f"    {cat:<35} {count}")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    category_filter = None
    if len(sys.argv) > 1 and sys.argv[1] == "--category":
        category_filter = sys.argv[2] if len(sys.argv) > 2 else None

    if category_filter:
        if category_filter in EVENT_CATEGORIES:
            scan_results = _dedupe(_run_category_scan({category_filter: EVENT_CATEGORIES[category_filter]}, "event"))
        elif category_filter in BUSINESS_SIGNAL_CATEGORIES:
            scan_results = _dedupe(_run_category_scan(
                {category_filter: BUSINESS_SIGNAL_CATEGORIES[category_filter]}, "business_signal"
            ))
        else:
            all_categories = list(EVENT_CATEGORIES) + list(BUSINESS_SIGNAL_CATEGORIES)
            print(f"Unknown category '{category_filter}'. Choose from: {', '.join(all_categories)}")
            sys.exit(1)
    else:
        scan_results = run_full_research()

    save_to_csv(scan_results)
    print_summary(scan_results)
