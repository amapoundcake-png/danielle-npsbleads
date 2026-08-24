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
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

RESEARCH_CSV = os.path.join(os.path.dirname(__file__), "central_fl_research.csv")

RESEARCH_CSV_COLUMNS = [
    "date_found", "bucket", "category", "title", "source", "published",
    "location_hint", "link", "snippet", "contact_email",
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
# Contact email enrichment
# ---------------------------------------------------------------------------
#
# Google News RSS links point at a Google redirect page that only resolves
# client-side (JS), so there's no cheap way to reach the original article
# URL. Instead, each result's headline is used as a search query to find
# the organization/brand's own website, and that site's contact/about page
# is scraped for a plausible email -- same approach lead_finder.py already
# uses for local business leads.

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
IGNORED_EMAIL_PREFIXES = ("noreply", "no-reply", "info@example", "test@", "webmaster")

# Domains that are never the organization behind a story -- news outlets,
# social platforms, search engines, and directory/listing/entertainment sites.
SEARCH_SKIP_DOMAINS = (
    "google.com", "bing.com", "msn.com", "youtube.com", "facebook.com",
    "instagram.com", "twitter.com", "x.com", "linkedin.com", "tiktok.com",
    "wikipedia.org", "yelp.com", "imdb.com", "rottentomatoes.com", "amazon.com",
    "primevideo.com", "orlandosentinel.com", "clickorlando.com", "mynews13.com",
    "wesh.com", "fox35orlando.com", "wftv.com", "baynews9.com", "orlandoweekly.com",
    "bizjournals.com", "patch.com", "news.google.com", "justwatch.com",
    "themoviedb.org", "netflix.com", "hulu.com", "disneyplus.com", "rotoworld.com",
)


def _decode_bing_redirect(href: str) -> str:
    """Bing wraps organic result links in a /ck/a redirect with the real URL
    base64-encoded (prefixed 'a1') in the 'u' query param. Decode it back."""
    import base64
    from urllib.parse import parse_qs

    parsed = urlparse(href)
    if parsed.netloc.endswith("bing.com") and parsed.path == "/ck/a":
        u = parse_qs(parsed.query).get("u", [None])[0]
        if u and u.startswith("a1"):
            b64 = u[2:]
            b64 += "=" * (-len(b64) % 4)
            try:
                return base64.urlsafe_b64decode(b64).decode("utf-8", errors="ignore")
            except Exception:
                pass
    return href


def _extract_emails_from_html(text: str) -> list[str]:
    found = EMAIL_RE.findall(text)
    clean = []
    for e in found:
        e_lower = e.lower()
        if any(e_lower.startswith(p) for p in IGNORED_EMAIL_PREFIXES):
            continue
        if e_lower.endswith((".png", ".jpg", ".gif", ".css", ".js")):
            continue
        clean.append(e.lower())
    return list(dict.fromkeys(clean))


def _clean_title_for_search(title: str, source: str) -> str:
    """Strip the trailing ' - Source Name' Google News appends to headlines."""
    if source and title.endswith(source):
        title = title[: -len(source)]
    return re.sub(r"[\s\-|]+$", "", title).strip()


# Words too generic to count as evidence a domain matches the organization
# named in a headline (verbs, connectors, and headline filler). Deliberately
# includes Central Florida place names ("Orlando", "Sanford", ...) -- they're
# legitimate parts of real org names ("Orlando Health") but too generic to
# confirm a match on their own, since nearly every local domain contains one.
_TITLE_STOPWORDS = {
    "the", "a", "an", "to", "in", "on", "at", "for", "of", "and", "or", "with",
    "who", "hosts", "host", "opens", "open", "opening", "launches", "launch",
    "launching", "announces", "announce", "announced", "celebrate",
    "celebrates", "where", "free", "new", "brings", "bring", "how",
    "orlando", "florida", "central", "sanford", "kissimmee", "apopka",
    "oviedo", "maitland", "casselberry", "longwood", "ocoee", "clermont",
    "deland", "windermere",
}

# Connector words short enough to bridge two halves of a real org name
# ("Habitat _for_ Humanity", "Girls _Who_ Code") without breaking the phrase
# early -- only when immediately followed by another capitalized word.
_BRIDGE_WORDS = {"for", "of", "and", "the", "a", "an", "&"}


def _leading_org_phrase(title: str) -> list[str]:
    """Grab the run of capitalized/acronym words at the start of a headline,
    bridging short connectors so multi-word org names aren't cut off after
    their first word -- a rough guess at the organization the headline names."""
    tokens = title.split()
    words = []
    i = 0
    while i < len(tokens):
        bare = re.sub(r"[^A-Za-z]", "", tokens[i])
        if not bare:
            break
        if bare[0].isupper():
            words.append(bare)
            i += 1
            continue
        if bare.lower() in _BRIDGE_WORDS and i + 1 < len(tokens):
            next_bare = re.sub(r"[^A-Za-z]", "", tokens[i + 1])
            if next_bare and next_bare[0].isupper():
                words.append(bare)
                i += 1
                continue
        break
    return words


def _domain_matches_org(domain: str, org_words: list[str]) -> bool:
    """Require real evidence the candidate domain is the organization named
    in the headline: at least 2 distinct meaningful words from the headline
    must appear in the domain. A single word is never enough on its own --
    testing against the live dataset found single-word matches (a Black
    History Month piece matching myheritage.com on "Heritage", a events
    calendar matching print-a-calendar.com on "Calendar") were wrong more
    often than right.
    """
    domain_norm = re.sub(r"[^a-z0-9]", "", domain.lower())
    meaningful = [
        w for w in org_words
        if len(w) >= 3 and w.lower() not in _TITLE_STOPWORDS
    ]
    matched = [w for w in meaningful if w.lower() in domain_norm]
    return len(matched) >= 2


def _search_organization_site(query: str, org_words: list[str]) -> Optional[str]:
    """Bing web search for the organization/brand website behind a headline.
    Only returns a candidate whose domain actually matches a word from the
    headline -- an unrelated top result is treated as no match at all."""
    search_url = f"https://www.bing.com/search?q={quote(query)}"
    resp = _get(search_url)
    if resp is None:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    for result in soup.find_all("li", class_="b_algo"):
        a = result.find("a", href=True)
        if not a:
            continue
        href = _decode_bing_redirect(a["href"].strip())
        if not href.startswith("http"):
            continue
        domain = urlparse(href).netloc.replace("www.", "")
        if not domain or any(skip in domain for skip in SEARCH_SKIP_DOMAINS):
            continue
        if not _domain_matches_org(domain, org_words):
            continue
        return href
    return None


def _find_contact_email_on_site(base_url: str) -> Optional[str]:
    """Check /contact, /contact-us, /about, then the homepage for an embedded email."""
    from urllib.parse import urljoin
    candidates = [
        urljoin(base_url, "/contact"),
        urljoin(base_url, "/contact-us"),
        urljoin(base_url, "/about"),
        base_url,
    ]
    for url in candidates:
        resp = _get(url)
        if resp is None:
            continue
        emails = _extract_emails_from_html(resp.text)
        if emails:
            return emails[0]
        _polite_delay()
    return None


# Headlines that round up multiple events/organizations ("Where to celebrate...",
# "5 things to do...") have no single organization to attribute an email to --
# skip enrichment for those rather than guess and risk a wrong contact.
_ROUNDUP_PATTERN = re.compile(
    r"^\s*(\d+\s+(things|events|ways|places)|where to|best\s|top\s)", re.IGNORECASE
)


def enrich_email(row: dict) -> str:
    """Best-effort contact email lookup for a single research row. Returns '' if none found."""
    query = _clean_title_for_search(row.get("title", ""), row.get("source", ""))
    if not query or _ROUNDUP_PATTERN.match(query):
        return ""

    org_words = _leading_org_phrase(query)
    if not org_words:
        return ""

    # Search on the extracted org phrase alone, not the full noisy headline --
    # a short, focused query ranks the organization's own site far more
    # reliably than the whole title text does.
    org_phrase = " ".join(org_words[:4])
    try:
        site = _search_organization_site(f'"{org_phrase}" official website', org_words)
        if not site:
            return ""
        _polite_delay()
        return _find_contact_email_on_site(site) or ""
    except Exception as exc:
        logger.warning("Email enrichment failed for '%s': %s", query, exc)
        return ""


def enrich_new_rows(rows: list[dict]) -> None:
    """Mutate rows in place, filling in contact_email for any row missing one."""
    total = len(rows)
    for i, row in enumerate(rows, 1):
        if row.get("contact_email"):
            continue
        logger.info("[%d/%d] Looking up contact email for: %s", i, total, row.get("title", "")[:70])
        row["contact_email"] = enrich_email(row)
        if row["contact_email"]:
            logger.info("  -> found: %s", row["contact_email"])
        _polite_delay()


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def save_to_csv(
    results: list[dict], filepath: str = RESEARCH_CSV, append: bool = True, enrich: bool = True
) -> int:
    """
    Write results to CSV. Appends to an existing file and skips any link
    already logged, so re-running the scan builds up a running research
    log instead of duplicating rows. Returns the number of new rows written.

    Only genuinely new rows get a contact-email lookup (enrich=True, the
    default) -- rows already in the CSV are never re-enriched, so a daily
    run only pays the lookup cost for that day's new results.
    """
    existing_links: set = set()
    file_exists = os.path.exists(filepath)

    if append and file_exists:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_links.add(row.get("link", ""))

    new_rows = [r for r in results if r.get("link") not in existing_links]

    if enrich and new_rows:
        logger.info("Enriching %d new row(s) with contact emails...", len(new_rows))
        enrich_new_rows(new_rows)

    mode = "a" if append and file_exists else "w"
    with open(filepath, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESEARCH_CSV_COLUMNS)
        if mode == "w":
            writer.writeheader()
        for r in new_rows:
            writer.writerow({col: r.get(col, "") for col in RESEARCH_CSV_COLUMNS})

    logger.info("Wrote %d new row(s) to %s", len(new_rows), filepath)
    return len(new_rows)


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
