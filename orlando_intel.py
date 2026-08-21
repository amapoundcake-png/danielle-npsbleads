"""
orlando_intel.py — "What's happening in Orlando?" research tool.

Monitors Orlando / Central Florida for the signal that feeds Danni's three
pipelines (nonprofit consulting, speaking, brand partnerships):

  - Events                     - Nonprofit opportunities
  - New businesses             - Conferences
  - Brand activations          - Cultural events
  - Creator / influencer events- Marketing & PR news
  - Networking events          - Local business openings

Two source types feed the digest:
  1. Direct RSS feeds from Orlando outlets (Bungalower, Orlando Weekly,
     ClickOrlando, WESH, Orlando Magazine) — classified into categories
     by keyword matching.
  2. Targeted Google News RSS searches, one or two per category, scoped
     to Orlando / Central Florida and a recency window — these arrive
     pre-categorized by the query itself.

Usage:
  python orlando_intel.py                 — build today's digest, save + print it
  python orlando_intel.py --days 14        — widen the lookback window
  python orlando_intel.py --category conferences   — only one category
  python orlando_intel.py --no-notion      — skip Notion logging even if configured

Output:
  - Markdown report written to ORLANDO_INTEL_REPORT_DIR
  - Console summary
  - Optional: top items logged to a Notion database if
    ORLANDO_INTEL_NOTION_DATABASE_ID is set (safe no-op otherwise)
"""

import argparse
import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from config import (
    DEFAULT_HEADERS,
    REQUEST_TIMEOUT,
    ORLANDO_INTEL_LOOKBACK_DAYS,
    ORLANDO_INTEL_MAX_PER_CATEGORY,
    ORLANDO_INTEL_REPORT_DIR,
    ORLANDO_INTEL_NOTION_DATABASE_ID,
)

logger = logging.getLogger(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_VERSION = "2022-06-28"

# ---------------------------------------------------------------------------
# Categories: label, targeted Google News queries, classifier keywords for
# direct-feed items, and the brand/pipeline angle from CLAUDE.md's decision
# tree (which name to use, what the item is worth to Danni).
# ---------------------------------------------------------------------------

CATEGORIES = {
    "nonprofit_opportunities": {
        "label": "Nonprofit Opportunities",
        "queries": [
            "Orlando nonprofit news",
            "Central Florida nonprofit partnership grant",
        ],
        "keywords": [
            "nonprofit", "non-profit", "501(c)(3)", "charity", "charities",
            "foundation", "philanthropy", "philanthropic",
        ],
        "brand_note": (
            "Danielle Adams / nonprofit consulting — the #1 money track. "
            "Flag as a possible fractional-partnership outreach target."
        ),
    },
    "conferences": {
        "label": "Conferences & Summits",
        "queries": [
            "Orlando conference 2026",
            "Orlando summit business conference",
        ],
        "keywords": ["conference", "summit", "convention", "symposium"],
        "brand_note": "Danni Adams — speaking inquiry opportunity (organizer, theme, date).",
    },
    "networking_events": {
        "label": "Networking Events",
        "queries": [
            "Orlando networking event business",
            "Orlando chamber of commerce mixer",
        ],
        "keywords": ["networking", "mixer", "chamber of commerce", "meetup", "meet-up"],
        "brand_note": "Danni Adams — visibility and relationship-building, possible sponsorship tie-in.",
    },
    "creator_events": {
        "label": "Creator & Influencer Events",
        "queries": [
            "Orlando creator economy event",
            "Orlando influencer event",
        ],
        "keywords": [
            "influencer", "content creator", "creator economy", "creator house",
            "tiktok house", "youtuber",
        ],
        "brand_note": "Amapoundcake / Danni Adams — attend, network, or pitch as a speaker/creator voice.",
    },
    "brand_activations": {
        "label": "Brand Activations & Pop-Ups",
        "queries": [
            "Orlando brand activation",
            "Orlando pop-up event brand",
        ],
        "keywords": ["activation", "pop-up", "popup", "brand experience", "immersive experience"],
        "brand_note": "Amapoundcake — brand partnership, event coverage, or UGC opportunity.",
    },
    "business_openings": {
        "label": "New Businesses & Local Openings",
        "queries": [
            "Orlando new business opening",
            '"coming soon" Orlando business',
        ],
        "keywords": [
            "now open", "opening soon", "new location", "grand opening",
            "coming and going", "new restaurant", "new shop", "storefront",
            "ribbon cutting",
        ],
        "brand_note": (
            "New local business = potential partner or sponsor. Amapoundcake for "
            "content/UGC, Danielle Adams for a community-partnership angle."
        ),
    },
    "cultural_events": {
        "label": "Cultural & Community Events",
        "queries": [
            "Orlando festival event",
            "Orlando cultural event community",
        ],
        "keywords": ["festival", "cultural", "heritage", "art walk", "parade", "exhibit"],
        "brand_note": "Danni Adams / Amapoundcake — appearance, hosting, or content opportunity.",
    },
    "marketing_news": {
        "label": "Marketing & PR News",
        "queries": [
            "Central Florida marketing agency news",
            "Orlando advertising PR news",
        ],
        "keywords": ["marketing", "advertising", "public relations", "pr agency", "ad campaign"],
        "brand_note": "Trend awareness — reference in outreach and content; possible agency partnership.",
    },
    "events": {
        "label": "General Events This Week",
        "queries": [
            "Orlando events this week",
        ],
        "keywords": ["this weekend", "event guide", "things to do"],
        "brand_note": "General visibility radar — cross-check against the other categories.",
    },
}

# Priority order used when classifying direct-feed items that could match
# more than one category's keywords (first match wins).
_CATEGORY_PRIORITY = [
    "nonprofit_opportunities", "conferences", "networking_events",
    "creator_events", "brand_activations", "business_openings",
    "cultural_events", "marketing_news", "events",
]

# ---------------------------------------------------------------------------
# Direct RSS feeds from Orlando outlets
# ---------------------------------------------------------------------------

DIRECT_FEEDS = [
    {"name": "Bungalower", "url": "https://bungalower.com/feed/"},
    {"name": "Orlando Weekly", "url": "https://www.orlandoweekly.com/orlando/Rss.xml"},
    {"name": "ClickOrlando (Business)", "url": "https://www.clickorlando.com/arc/outboundfeeds/rss/category/business/?outputType=xml"},
    {"name": "ClickOrlando (General)", "url": "https://www.clickorlando.com/arc/outboundfeeds/rss/?outputType=xml"},
    {"name": "WESH 2", "url": "https://www.wesh.com/topstories-rss"},
    {"name": "Orlando Magazine", "url": "https://www.orlandomagazine.com/feed/"},
]

GOOGLE_NEWS_SEARCH_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

# Google News matches loosely on the query text, so a search for "Orlando
# nonprofit news" can still surface stories from Space Coast, Treasure Coast,
# or other states. Require one of these terms in the title/summary/source
# before keeping a Google News result.
ORLANDO_AREA_TERMS = [
    "orlando", "central florida", "orange county", "seminole county",
    "winter park", "winter garden", "lake nona", "sanford", "kissimmee",
    "altamonte", "maitland", "apopka", "windermere", "ocoee", "oviedo",
    "casselberry", "longwood",
]


def _is_orlando_relevant(item: dict) -> bool:
    haystack = f"{item['title']} {item['summary']} {item['source']}".lower()
    return any(term in haystack for term in ORLANDO_AREA_TERMS)


# ---------------------------------------------------------------------------
# Fetch + parse
# ---------------------------------------------------------------------------

def _get(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.content
    except requests.RequestException as exc:
        logger.warning("Feed fetch failed for %s: %s", url, exc)
        return None


def _clean_text(raw: str) -> str:
    text = BeautifulSoup(raw or "", "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:280]


def _parse_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if dt is not None and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_rss_items(xml_bytes: bytes, default_source: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        logger.warning("Could not parse RSS from %s: %s", default_source, exc)
        return items

    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            continue
        description = item.findtext("description") or ""
        published = _parse_date(item.findtext("pubDate"))

        source_el = item.find("source")
        source_name = source_el.text.strip() if source_el is not None and source_el.text else default_source

        # Google News titles are suffixed " - Source Name"; prefer the
        # dedicated <source> tag and strip the duplicate suffix.
        if source_el is not None and source_name:
            suffix = f" - {source_name}"
            if title.endswith(suffix):
                title = title[: -len(suffix)].strip()

        items.append({
            "title": title,
            "link": link,
            "summary": _clean_text(description),
            "published": published,
            "source": source_name,
        })
    return items


def _fetch_direct_feed(feed: dict) -> list[dict]:
    content = _get(feed["url"])
    if not content:
        return []
    return _parse_rss_items(content, feed["name"])


def _fetch_google_news(query: str, lookback_days: int) -> list[dict]:
    scoped_query = f"{query} when:{lookback_days}d"
    url = GOOGLE_NEWS_SEARCH_URL.format(query=quote(scoped_query))
    content = _get(url)
    if not content:
        return []
    return _parse_rss_items(content, "Google News")


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def _classify(title: str, summary: str) -> Optional[str]:
    haystack = f"{title} {summary}".lower()
    for key in _CATEGORY_PRIORITY:
        for kw in CATEGORIES[key]["keywords"]:
            if kw in haystack:
                return key
    return None


def _dedupe_key(item: dict) -> str:
    return re.sub(r"[^a-z0-9]+", "", item["title"].lower())[:80]


# ---------------------------------------------------------------------------
# Digest builder
# ---------------------------------------------------------------------------

def gather_digest(lookback_days: int = None, only_category: str = None) -> dict:
    """
    Return {category_key: [items]}, newest first, capped per category,
    deduplicated across all sources.
    """
    lookback_days = lookback_days or ORLANDO_INTEL_LOOKBACK_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    category_keys = [only_category] if only_category else list(CATEGORIES.keys())

    seen = set()
    buckets = {key: [] for key in category_keys}

    # 1. Direct feeds, classified by keyword
    for feed in DIRECT_FEEDS:
        for item in _fetch_direct_feed(feed):
            if item["published"] and item["published"] < cutoff:
                continue
            key = _dedupe_key(item)
            if key in seen:
                continue
            category = _classify(item["title"], item["summary"])
            if category not in buckets:
                continue
            seen.add(key)
            item["category"] = category
            buckets[category].append(item)

    # 2. Targeted Google News searches, pre-categorized by query
    for category in category_keys:
        for query in CATEGORIES[category]["queries"]:
            for item in _fetch_google_news(query, lookback_days):
                if item["published"] and item["published"] < cutoff:
                    continue
                if not _is_orlando_relevant(item):
                    continue
                key = _dedupe_key(item)
                if key in seen:
                    continue
                seen.add(key)
                item["category"] = category
                buckets[category].append(item)

    # Sort newest-first (undated items sink to the bottom) and cap
    for category, items in buckets.items():
        items.sort(key=lambda i: i["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        buckets[category] = items[:ORLANDO_INTEL_MAX_PER_CATEGORY]

    return buckets


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_markdown(buckets: dict, lookback_days: int) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    total = sum(len(items) for items in buckets.values())

    lines = [
        "# Orlando Intelligence Digest",
        f"_Generated {today} — covering the last {lookback_days} day(s) — {total} item(s)_",
        "",
    ]

    for key, items in buckets.items():
        meta = CATEGORIES[key]
        lines.append(f"## {meta['label']} ({len(items)})")
        lines.append(f"_Angle: {meta['brand_note']}_")
        lines.append("")
        if not items:
            lines.append("_Nothing new this window._")
            lines.append("")
            continue
        for item in items:
            date_str = item["published"].strftime("%b %d") if item["published"] else "undated"
            lines.append(f"- **[{item['title']}]({item['link']})** — {item['source']}, {date_str}")
            if item["summary"]:
                lines.append(f"  {item['summary']}")
        lines.append("")

    return "\n".join(lines)


def save_report(markdown: str) -> str:
    os.makedirs(ORLANDO_INTEL_REPORT_DIR, exist_ok=True)
    filename = f"orlando_intel_{datetime.now().strftime('%Y-%m-%d')}.md"
    path = os.path.join(ORLANDO_INTEL_REPORT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return path


# ---------------------------------------------------------------------------
# Optional Notion logging
# ---------------------------------------------------------------------------

def log_to_notion(buckets: dict) -> int:
    """Log each item to the Orlando Intel Notion database, if configured. Returns count logged."""
    if not ORLANDO_INTEL_NOTION_DATABASE_ID or not NOTION_API_KEY:
        logger.info("Notion logging skipped (ORLANDO_INTEL_NOTION_DATABASE_ID or NOTION_API_KEY not set).")
        return 0

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    logged = 0
    for key, items in buckets.items():
        meta = CATEGORIES[key]
        for item in items:
            payload = {
                "parent": {"database_id": ORLANDO_INTEL_NOTION_DATABASE_ID},
                "properties": {
                    "Title": {"title": [{"text": {"content": item["title"][:200]}}]},
                    "Category": {"select": {"name": meta["label"]}},
                    "Source": {"rich_text": [{"text": {"content": item["source"]}}]},
                    "URL": {"url": item["link"]},
                    "Date": {"date": {"start": (item["published"] or datetime.now(timezone.utc)).date().isoformat()}},
                    "Brand Angle": {"rich_text": [{"text": {"content": meta["brand_note"]}}]},
                },
            }
            try:
                resp = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
                logged += 1
            except requests.RequestException as exc:
                logger.warning("Notion log failed for %s: %s", item["title"], exc)

    logger.info("Logged %d item(s) to Notion Orlando Intel database.", logged)
    return logged


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_intel(lookback_days: int = None, only_category: str = None, skip_notion: bool = False) -> str:
    lookback_days = lookback_days or ORLANDO_INTEL_LOOKBACK_DAYS
    logger.info("Gathering Orlando intelligence (lookback: %d day(s))...", lookback_days)

    buckets = gather_digest(lookback_days=lookback_days, only_category=only_category)
    markdown = render_markdown(buckets, lookback_days)
    path = save_report(markdown)

    total = sum(len(items) for items in buckets.values())
    logger.info("Digest built: %d item(s) across %d categories. Saved to %s", total, len(buckets), path)

    if not skip_notion:
        log_to_notion(buckets)

    print(markdown)
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Orlando / Central Florida intelligence digest")
    parser.add_argument("--days", type=int, default=None, help="Lookback window in days")
    parser.add_argument("--category", choices=list(CATEGORIES.keys()), default=None, help="Only gather one category")
    parser.add_argument("--no-notion", action="store_true", help="Skip Notion logging even if configured")
    args = parser.parse_args()

    run_intel(lookback_days=args.days, only_category=args.category, skip_notion=args.no_notion)
