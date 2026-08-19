"""
lead_finder.py — Multi-source lead scraper for Orlando nonprofits and small businesses.

Each source function returns a list of lead dicts:
  {name, org, email, industry, source_url, city, notes}

All scraping is done respectfully:
  - Real browser User-Agent header
  - 2-3 second delay between page requests
  - Errors are caught and logged so other sources continue
"""

import csv
import logging
import os
import re
import time
import random
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import (
    DEFAULT_HEADERS,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT,
    MANUAL_LEADS_CSV,
    GOOGLE_MAPS_API_KEY,
    TARGET_LOCATIONS,
)
from notion_logger import is_already_contacted, get_org_contact_count

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Blocklist — orgs to never contact
# ---------------------------------------------------------------------------
BLOCKED_ORGS = [
    "florida for all",
    "faith in florida",
    "dream defenders",
]

# Email addresses permanently blocked (hard bounces, unsubscribes)
BLOCKED_EMAILS = {
    "prmarketing@bgccf.org",           # hard bounce x2 (June 29 + June 30)
    "florida@godbelongsinmycity.com",  # hard bounce July 18
    "dallas@indivisible.org",          # hard bounce July 21
    "houston@indivisible.org",         # hard bounce July 21
    "chicago@indivisible.org",         # hard bounce July 21
    "atlanta@indivisible.org",         # hard bounce July 20
    "creator@bodyposipanda.com",       # hard bounce July 21
    "info@aclufl.org",                 # hard bounce July 21
    "info@txdemocrats.org",            # hard bounce July 21
    "info@georgiademocrats.org",       # hard bounce July 21
    "info@ildemocrats.org",            # hard bounce July 21
    "info@swingleft.org",              # hard bounce July 20
    "info@moveon.org",                 # hard bounce July 20
    "creator@instacart.com",           # hard bounce July 21
    "partnerships@visitorlando.com",   # hard bounce July 21
    # Hard bounces Aug 19
    "submissions@brevardtalentgroup.com",
    "submissions@stewarttalent.com",
    "info@blocagency.com",
    "submissions@wilhelminamodels.com",
    # Unsubscribe Aug 19
    "info@thebodypositive.org",
}

def _is_blocked(org: str) -> bool:
    org_lower = org.strip().lower()
    return any(blocked in org_lower for blocked in BLOCKED_ORGS)


def _todays_locations() -> list[str]:
    """
    Return the locations to target today.
    Always includes Orlando and Tampa, then rotates 6 more from the full list
    so every market gets covered regularly.
    """
    from datetime import date
    priority = ["Orlando, FL", "Tampa, FL"]
    rest = [loc for loc in TARGET_LOCATIONS if loc not in priority]
    day_index = date.today().timetuple().tm_yday
    extras = []
    for i in range(6):
        extras.append(rest[(day_index + i) % len(rest)])
    return priority + extras


# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------

def _get(url: str, **kwargs) -> Optional[requests.Response]:
    """GET with standard headers; returns None on any error."""
    try:
        resp = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        logger.warning("GET failed for %s: %s", url, exc)
        return None


def _polite_delay() -> None:
    """Sleep a random 2-3 seconds between requests to be a good citizen."""
    time.sleep(REQUEST_DELAY_SECONDS + random.uniform(0, 1))


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

IGNORED_EMAIL_PREFIXES = ("noreply", "no-reply", "info@example", "test@", "webmaster")


def _extract_emails_from_html(html: str) -> list[str]:
    """Find all email addresses in raw HTML, filtering obvious non-contact addresses."""
    found = EMAIL_RE.findall(html)
    clean = []
    for e in found:
        e_lower = e.lower()
        if any(e_lower.startswith(p) for p in IGNORED_EMAIL_PREFIXES):
            continue
        if e_lower.endswith((".png", ".jpg", ".gif", ".css", ".js")):
            continue
        clean.append(e.lower())
    return list(dict.fromkeys(clean))  # deduplicate, preserve order


def _find_contact_email(base_url: str) -> Optional[str]:
    """
    Visit a website's contact page (or home page) and return the first
    plausible contact email address found.
    """
    _polite_delay()
    # Try /contact, /contact-us, /about, then home
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


def _dedupe_and_filter(leads: list[dict]) -> list[dict]:
    """
    Remove leads with no email, deduplicate by email, and remove emails
    already contacted. Only allows active profiles for the current phase.
    """
    ACTIVE_PROFILES = {"nonprofit", "brand", "speaker", "creator", "talent"}

    seen_emails: set[str] = set()
    filtered = []
    for lead in leads:
        email = (lead.get("email") or "").strip().lower()
        if not email:
            continue
        if email in seen_emails:
            continue
        if _is_blocked(lead.get("org", "")):
            logger.info("Skipping blocked org: %s", lead.get("org"))
            continue
        if email in BLOCKED_EMAILS:
            logger.info("Skipping blocked email: %s", email)
            continue
        profile = (lead.get("profile") or "nonprofit").strip()
        if profile not in ACTIVE_PROFILES:
            logger.info("Skipping paused profile [%s]: %s", profile, lead.get("org"))
            continue
        seen_emails.add(email)
        try:
            already = is_already_contacted(email)
        except Exception as exc:
            logger.error("Notion check failed for %s — skipping to avoid duplicate: %s", email, exc)
            already = True  # conservative: skip rather than risk a duplicate
        if already:
            logger.info("Skipping already-contacted: %s", email)
            continue

        # Allow up to 2 contacts per org, block a 3rd
        org = lead.get("org", "")
        if org:
            try:
                org_count = get_org_contact_count(org)
                if org_count >= 2:
                    logger.info("Skipping %s — org already contacted %d times", org, org_count)
                    continue
            except Exception as exc:
                logger.warning("Could not check org count for %s: %s", org, exc)
        lead["email"] = email
        filtered.append(lead)
    return filtered


# ---------------------------------------------------------------------------
# Source 1: DuckDuckGo nonprofit search (replaces broken Idealist scraper)
# ---------------------------------------------------------------------------

NONPROFIT_SEARCH_QUERIES = [
    "nonprofit organization {city} contact email",
    "community foundation {city} contact",
    "social services organization {city} email",
    "youth program {city} nonprofit contact",
    "women's shelter {city} contact email",
    "food bank {city} contact",
    "mentoring program {city} nonprofit email",
    "community health center {city} contact",
]

NGO_CONFERENCE_QUERIES = [
    "NGO conference {city} contact email",
    "nonprofit conference {city} speaker inquiry",
    "social impact conference {city} contact",
    "community development conference {city}",
]


def find_leads_idealist(max_leads: int = 10, location: str = "Orlando, FL") -> list[dict]:
    """Search DuckDuckGo for nonprofit leads in a given location."""
    city = location.split(",")[0].strip()
    logger.info("Searching DuckDuckGo nonprofits for %s...", location)
    leads = []
    seen_domains: set[str] = set()

    queries = [q.format(city=city) for q in NONPROFIT_SEARCH_QUERIES]

    for query in queries:
        if len(leads) >= max_leads:
            break

        search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        _polite_delay()
        resp = _get(search_url)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        result_links = soup.find_all("a", class_="result__url")

        for link in result_links:
            if len(leads) >= max_leads:
                break

            href = link.get("href", "").strip()
            if not href.startswith("http"):
                href = "https://" + href

            parsed = urlparse(href)
            domain = parsed.netloc.replace("www.", "")
            if not domain or domain in seen_domains:
                continue

            skip_domains = (
                "yelp.com", "google.com", "facebook.com", "instagram.com",
                "yellowpages.com", "tripadvisor.com", "linkedin.com",
                "indeed.com", "glassdoor.com", "wikipedia.org", "guidestar.org",
                "idealist.org", "charity navigator.org", "reddit.com",
            )
            if any(s in domain for s in skip_domains):
                continue

            seen_domains.add(domain)
            _polite_delay()

            email = _find_contact_email(href)
            if not email:
                continue

            org_name = domain.split(".")[0].replace("-", " ").replace("_", " ").title()

            leads.append({
                "name": "",
                "org": org_name,
                "email": email,
                "industry": "Nonprofit",
                "profile": "nonprofit",
                "source_url": href,
                "city": location,
                "notes": f"DDG nonprofit search — {city}",
            })
            logger.info("DDG nonprofit found: %s <%s> [%s]", org_name, email, location)

    logger.info("DDG nonprofits: found %d leads for %s.", len(leads), location)
    return leads


# ---------------------------------------------------------------------------
# Source 2: Chamber of Commerce via DuckDuckGo (replaces hardcoded URL table)
# ---------------------------------------------------------------------------

CHAMBER_SEARCH_QUERIES = [
    "chamber of commerce member directory {city} contact email",
    "business association {city} member contact",
    "small business network {city} email contact",
]


def find_leads_chamber(max_leads: int = 10, location: str = "Orlando, FL") -> list[dict]:
    """Search DuckDuckGo for chamber/business association leads in a given location."""
    city = location.split(",")[0].strip()
    logger.info("Searching DuckDuckGo chamber leads for %s...", location)
    leads = []
    seen_domains: set[str] = set()

    queries = [q.format(city=city) for q in CHAMBER_SEARCH_QUERIES]

    for query in queries:
        if len(leads) >= max_leads:
            break

        search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        _polite_delay()
        resp = _get(search_url)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        result_links = soup.find_all("a", class_="result__url")

        for link in result_links:
            if len(leads) >= max_leads:
                break

            href = link.get("href", "").strip()
            if not href.startswith("http"):
                href = "https://" + href

            parsed = urlparse(href)
            domain = parsed.netloc.replace("www.", "")
            if not domain or domain in seen_domains:
                continue

            skip_domains = (
                "yelp.com", "google.com", "facebook.com", "instagram.com",
                "yellowpages.com", "tripadvisor.com", "linkedin.com",
                "indeed.com", "glassdoor.com", "wikipedia.org", "reddit.com",
                "bbb.org", "thumbtack.com",
            )
            if any(s in domain for s in skip_domains):
                continue

            seen_domains.add(domain)
            _polite_delay()

            email = _find_contact_email(href)
            if not email:
                continue

            org_name = domain.split(".")[0].replace("-", " ").replace("_", " ").title()

            leads.append({
                "name": "",
                "org": org_name,
                "email": email,
                "industry": "Small Business",
                "profile": "brand",
                "source_url": href,
                "city": location,
                "notes": f"Chamber/biz search — {city}",
            })
            logger.info("Chamber/biz found: %s <%s> [%s]", org_name, email, location)

    logger.info("Chamber/biz: found %d leads for %s.", len(leads), location)
    return leads


# ---------------------------------------------------------------------------
# Source 3: ProPublica Nonprofit Explorer API (replaces broken GuideStar)
# ---------------------------------------------------------------------------

PROPUBLICA_URL = "https://projects.propublica.org/nonprofits/api/v2/search.json"

STATE_ABBREVS = {
    "AL": "AL", "AK": "AK", "AZ": "AZ", "AR": "AR", "CA": "CA",
    "CO": "CO", "CT": "CT", "DE": "DE", "FL": "FL", "GA": "GA",
    "HI": "HI", "ID": "ID", "IL": "IL", "IN": "IN", "IA": "IA",
    "KS": "KS", "KY": "KY", "LA": "LA", "ME": "ME", "MD": "MD",
    "MA": "MA", "MI": "MI", "MN": "MN", "MS": "MS", "MO": "MO",
    "MT": "MT", "NE": "NE", "NV": "NV", "NH": "NH", "NJ": "NJ",
    "NM": "NM", "NY": "NY", "NC": "NC", "ND": "ND", "OH": "OH",
    "OK": "OK", "OR": "OR", "PA": "PA", "RI": "RI", "SC": "SC",
    "SD": "SD", "TN": "TN", "TX": "TX", "UT": "UT", "VT": "VT",
    "VA": "VA", "WA": "WA", "WV": "WV", "WI": "WI", "WY": "WY",
    "DC": "DC",
}


def find_leads_guidestar(max_leads: int = 10, location: str = "Orlando, FL") -> list[dict]:
    """
    Query ProPublica Nonprofit Explorer API for nonprofits in a given location.
    Free, no auth required.
    """
    import json
    parts = [p.strip() for p in location.split(",")]
    city = parts[0]
    state_raw = parts[1].strip() if len(parts) > 1 else ""
    state = STATE_ABBREVS.get(state_raw.upper(), state_raw.upper()) if state_raw else ""

    logger.info("Querying ProPublica Nonprofit Explorer for %s...", location)
    leads = []

    params = {"q": city, "page": 0}
    if state:
        params["state[id]"] = state

    try:
        resp = requests.get(PROPUBLICA_URL, params=params, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("ProPublica API failed for %s: %s", location, exc)
        return leads

    orgs = data.get("organizations", [])
    for org in orgs:
        if len(leads) >= max_leads:
            break

        org_name = org.get("name", "").strip()
        ntee_code = org.get("ntee_code", "")
        website = org.get("website", "") or ""

        if not org_name:
            continue

        email = None
        if website:
            _polite_delay()
            email = _find_contact_email(website)

        if not email:
            continue

        leads.append({
            "name": "",
            "org": org_name,
            "email": email,
            "industry": "Nonprofit",
            "profile": "nonprofit",
            "source_url": website or f"https://projects.propublica.org/nonprofits/organizations/{org.get('ein','')}",
            "city": location,
            "notes": f"ProPublica — NTEE {ntee_code}" if ntee_code else "ProPublica",
        })
        logger.info("ProPublica nonprofit: %s <%s> [%s]", org_name, email, location)

    logger.info("ProPublica: found %d leads with emails for %s.", len(leads), location)
    return leads


# ---------------------------------------------------------------------------
# Source 4: NGO / Conference leads (speaker booking targets)
# ---------------------------------------------------------------------------

def find_leads_ngo_conferences(max_leads: int = 10, location: str = "Orlando, FL") -> list[dict]:
    """
    Search DuckDuckGo for NGOs and conferences that might book Danni as a speaker
    or have budget to bring her in. Targets speaker booking contacts.
    """
    city = location.split(",")[0].strip()
    logger.info("Searching NGO/conference leads for %s...", location)
    leads = []
    seen_domains: set[str] = set()

    queries = [q.format(city=city) for q in NGO_CONFERENCE_QUERIES]

    for query in queries:
        if len(leads) >= max_leads:
            break

        search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        _polite_delay()
        resp = _get(search_url)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        result_links = soup.find_all("a", class_="result__url")

        for link in result_links:
            if len(leads) >= max_leads:
                break

            href = link.get("href", "").strip()
            if not href.startswith("http"):
                href = "https://" + href

            parsed = urlparse(href)
            domain = parsed.netloc.replace("www.", "")
            if not domain or domain in seen_domains:
                continue

            skip_domains = (
                "yelp.com", "google.com", "facebook.com", "instagram.com",
                "yellowpages.com", "tripadvisor.com", "linkedin.com",
                "indeed.com", "glassdoor.com", "wikipedia.org", "reddit.com",
                "eventbrite.com",
            )
            if any(s in domain for s in skip_domains):
                continue

            seen_domains.add(domain)
            _polite_delay()

            email = _find_contact_email(href)
            if not email:
                continue

            org_name = domain.split(".")[0].replace("-", " ").replace("_", " ").title()

            leads.append({
                "name": "",
                "org": org_name,
                "email": email,
                "industry": "Conference / NGO",
                "profile": "speaker",
                "source_url": href,
                "city": location,
                "notes": f"NGO/conference — {city}",
            })
            logger.info("NGO/conference found: %s <%s> [%s]", org_name, email, location)

    logger.info("NGO/conference: found %d leads for %s.", len(leads), location)
    return leads


# ---------------------------------------------------------------------------
# Source 5: Orlando Local Businesses (brand deal targets)
# ---------------------------------------------------------------------------

ORLANDO_BIZ_CATEGORIES = [
    # Spas & wellness
    ("boutique spa Orlando FL", "Spa"),
    ("day spa Orlando FL", "Spa"),
    ("massage studio Orlando FL", "Wellness"),
    ("float tank sensory deprivation Orlando FL", "Wellness"),
    ("sound bath meditation studio Orlando FL", "Wellness"),
    ("yoga studio Orlando FL", "Wellness"),
    ("pilates studio Orlando FL", "Wellness"),
    # Hotels & stays
    ("boutique hotel Orlando FL", "Boutique Hotel"),
    ("bed and breakfast Orlando FL", "Boutique Hotel"),
    ("vacation rental company Orlando FL", "Boutique Hotel"),
    ("boutique hotel Winter Park FL", "Boutique Hotel"),
    # Theaters & arts
    ("independent theater Orlando FL", "Theater"),
    ("dinner theater Orlando FL", "Dinner Theater"),
    ("improv comedy theater Orlando FL", "Theater"),
    ("black box theater Orlando FL", "Theater"),
    ("community theater Orlando FL", "Theater"),
    # Dinner shows & experiences
    ("dinner show Orlando FL", "Dinner Show"),
    ("immersive dining experience Orlando FL", "Dinner Show"),
    ("supper club Orlando FL", "Dinner Show"),
    ("chef's table experience Orlando FL", "Dining Experience"),
    # Creative & art studios
    ("paint and sip studio Orlando FL", "Creative Studio"),
    ("pottery studio Orlando FL", "Creative Studio"),
    ("art studio class Orlando FL", "Creative Studio"),
    ("photography studio Orlando FL", "Creative Studio"),
    ("dance studio Orlando FL", "Dance Studio"),
    # Cooking & food experiences
    ("cooking class Orlando FL", "Cooking Club"),
    ("culinary studio Orlando FL", "Cooking Club"),
    ("baking class Orlando FL", "Cooking Club"),
    ("food tour Orlando FL", "Food Experience"),
    # Fun & attraction spaces
    ("escape room Orlando FL", "Entertainment"),
    ("axe throwing Orlando FL", "Entertainment"),
    ("trampoline park Orlando FL", "Entertainment"),
    ("bowling alley boutique Orlando FL", "Entertainment"),
    ("mini golf Orlando FL", "Entertainment"),
    ("vintage arcade bar Orlando FL", "Entertainment"),
    ("laser tag Orlando FL", "Entertainment"),
    # Unique local spots
    ("rooftop bar Orlando FL", "Bar / Venue"),
    ("jazz club Orlando FL", "Music Venue"),
    ("live music venue small Orlando FL", "Music Venue"),
    ("comedy club Orlando FL", "Comedy Club"),
    ("speakeasy bar Orlando FL", "Bar / Venue"),
    ("cultural center Orlando FL", "Cultural Space"),
    ("gallery art space Orlando FL", "Art Gallery"),
]

SKIP_DOMAINS_LOCAL = (
    "yelp.com", "google.com", "facebook.com", "instagram.com",
    "yellowpages.com", "tripadvisor.com", "foursquare.com",
    "mapquest.com", "bbb.org", "thumbtack.com", "eventbrite.com",
    "groupon.com", "opentable.com", "mindbodyonline.com",
    "disney.com", "universalorlando.com", "seaworld.com",
    "visitorlando.com", "reddit.com", "wikipedia.org",
)


def find_leads_orlando_local(max_leads: int = 20) -> list[dict]:
    """
    Search DuckDuckGo for Orlando small businesses to target for brand partnerships.
    Targets boutique hotels, spas, theaters, dinner shows, creative studios,
    cooking clubs, and local attractions.
    """
    logger.info("Searching for Orlando small business brand partnership targets...")
    leads = []
    seen_domains: set[str] = set()

    for query, industry in ORLANDO_BIZ_CATEGORIES:
        if len(leads) >= max_leads:
            break

        search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        _polite_delay()
        resp = _get(search_url)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        result_links = soup.find_all("a", class_="result__url")

        for link in result_links:
            if len(leads) >= max_leads:
                break

            href = link.get("href", "").strip()
            if not href.startswith("http"):
                href = "https://" + href

            parsed = urlparse(href)
            domain = parsed.netloc.replace("www.", "")
            if not domain or domain in seen_domains:
                continue

            if any(s in domain for s in SKIP_DOMAINS_LOCAL):
                continue

            seen_domains.add(domain)
            _polite_delay()

            email = _find_contact_email(href)
            if not email:
                continue

            biz_name = domain.split(".")[0].replace("-", " ").replace("_", " ").title()

            leads.append({
                "name": "",
                "org": biz_name,
                "email": email,
                "industry": industry,
                "profile": "brand",
                "source_url": href,
                "city": "Orlando, FL",
                "notes": f"Orlando local — {industry}",
            })
            logger.info("Orlando local biz: %s <%s> [%s]", biz_name, email, industry)

    logger.info("Orlando local businesses: found %d leads.", len(leads))
    return leads


# ---------------------------------------------------------------------------
# Source 5: Manual CSV (LinkedIn / RFP board leads)
# ---------------------------------------------------------------------------

def find_leads_manual_csv(filepath: str = MANUAL_LEADS_CSV) -> list[dict]:
    """
    Load leads from a manually maintained CSV file.

    Expected columns: name, org, email, industry, notes
    All columns are optional except email.
    """
    if not os.path.exists(filepath):
        logger.info("No manual CSV found at %s — skipping.", filepath)
        return []

    logger.info("Loading manual leads from %s...", filepath)
    leads = []
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = (row.get("email") or "").strip()
                if not email:
                    continue
                leads.append({
                    "name": (row.get("name") or "").strip(),
                    "org": (row.get("org") or "").strip(),
                    "email": email,
                    "industry": (row.get("industry") or "").strip(),
                    "profile": (row.get("profile") or "nonprofit").strip(),
                    "source_url": "manual_csv",
                    "city": (row.get("city") or "Orlando, FL").strip(),
                    "notes": (row.get("notes") or "").strip(),
                })
    except Exception as exc:
        logger.error("Failed to read manual CSV %s: %s", filepath, exc)

    logger.info("Manual CSV: loaded %d leads.", len(leads))
    return leads


# ---------------------------------------------------------------------------
# Source 5: Google Maps API (stub — only runs if key is set)
# ---------------------------------------------------------------------------

def find_leads_google_maps(
    api_key: str,
    query: str = "nonprofit organization",
    location: str = "Orlando, FL",
    radius_meters: int = 40000,
    max_leads: int = 20,
) -> list[dict]:
    """
    Find leads using the Google Places API (Nearby Search + Place Details).

    Only called when GOOGLE_MAPS_API_KEY is set in .env.

    Args:
        api_key: Google Maps / Places API key
        query: text query for place search
        location: human-readable location (geocoded first)
        radius_meters: search radius
        max_leads: maximum results to return

    Returns:
        List of lead dicts.
    """
    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

    leads = []

    # Step 1: Geocode the location string to lat/lng
    geo_resp = _get(GEOCODE_URL, params={"address": location, "key": api_key})
    if geo_resp is None:
        logger.error("Google Maps: geocoding failed for '%s'.", location)
        return leads

    geo_data = geo_resp.json()
    if not geo_data.get("results"):
        logger.error("Google Maps: no geocoding results for '%s'.", location)
        return leads

    loc = geo_data["results"][0]["geometry"]["location"]
    lat_lng = f"{loc['lat']},{loc['lng']}"

    # Step 2: Text search for places
    params = {
        "query": f"{query} in {location}",
        "location": lat_lng,
        "radius": radius_meters,
        "key": api_key,
    }

    next_page_token = None
    while len(leads) < max_leads:
        if next_page_token:
            params["pagetoken"] = next_page_token
            _polite_delay()  # Google requires a short wait before using page token

        search_resp = _get(TEXTSEARCH_URL, params=params)
        if search_resp is None:
            break

        search_data = search_resp.json()
        places = search_data.get("results", [])

        for place in places:
            if len(leads) >= max_leads:
                break

            place_id = place.get("place_id")
            org_name = place.get("name", "")
            if not place_id or not org_name:
                continue

            # Step 3: Get place details for website + phone
            _polite_delay()
            detail_resp = _get(
                DETAILS_URL,
                params={
                    "place_id": place_id,
                    "fields": "name,website,formatted_phone_number,types",
                    "key": api_key,
                },
            )
            if detail_resp is None:
                continue

            detail = detail_resp.json().get("result", {})
            website = detail.get("website", "")
            place_types = detail.get("types", [])

            # Determine industry from place types
            industry = "Small Business"
            if any(t in place_types for t in ("church", "place_of_worship")):
                industry = "Nonprofit"
            elif "health" in " ".join(place_types):
                industry = "Healthcare"
            elif "school" in " ".join(place_types) or "university" in " ".join(place_types):
                industry = "Education / Nonprofit"

            email = None
            if website:
                _polite_delay()
                email = _find_contact_email(website)

            if not email:
                continue

            leads.append({
                "name": "",
                "org": org_name,
                "email": email,
                "industry": industry,
                "source_url": website or f"https://maps.google.com/?cid={place_id}",
                "city": location,
                "notes": "",
            })

        next_page_token = search_data.get("next_page_token")
        if not next_page_token:
            break

    logger.info("Google Maps: found %d leads with emails.", len(leads))
    return leads


# ---------------------------------------------------------------------------
# Master aggregator
# ---------------------------------------------------------------------------

def gather_leads_for_profiles(profiles: list, target: int = 12) -> list[dict]:
    """Fetch and filter leads for a specific set of profiles only."""
    all_leads: list[dict] = []
    locations = _todays_locations()

    try:
        all_leads.extend(find_leads_manual_csv())
    except Exception as exc:
        logger.error("Manual CSV source error: %s", exc)

    try:
        all_leads.extend(find_leads_orlando_local())
    except Exception as exc:
        logger.error("Orlando local biz source error: %s", exc)

    for location in locations:
        for source_fn in [find_leads_idealist, find_leads_guidestar, find_leads_chamber, find_leads_ngo_conferences]:
            try:
                all_leads.extend(source_fn(location=location))
            except Exception as exc:
                logger.error("Source %s / %s error: %s", source_fn.__name__, location, exc)

    # Filter to only requested profiles before dedup
    profile_set = set(profiles)
    all_leads = [l for l in all_leads if (l.get("profile") or "nonprofit") in profile_set]

    filtered = _dedupe_and_filter(all_leads)
    logger.info("[%s] %d leads after dedup (target: %d).", profiles, len(filtered), target)
    return filtered[:target]


def gather_all_leads(target: int = 15) -> list[dict]:
    """
    Collect leads from all available sources, deduplicate, filter already-contacted,
    and return up to `target` leads.

    Orlando and Tampa are always included. Three additional locations rotate
    daily so every market in TARGET_LOCATIONS gets covered over time.
    """
    all_leads: list[dict] = []
    locations = _todays_locations()
    logger.info("Today's target locations: %s", ", ".join(locations))

    # Always run manual CSV first
    try:
        all_leads.extend(find_leads_manual_csv())
    except Exception as exc:
        logger.error("Manual CSV source error: %s", exc)

    # Orlando local businesses (brand deals)
    try:
        all_leads.extend(find_leads_orlando_local())
    except Exception as exc:
        logger.error("Orlando local biz source error: %s", exc)

    # Scrape each location from each source
    for location in locations:
        for source_fn in [find_leads_idealist, find_leads_guidestar, find_leads_chamber, find_leads_ngo_conferences]:
            try:
                results = source_fn(location=location)
                all_leads.extend(results)
            except Exception as exc:
                logger.error("Source %s / %s error: %s", source_fn.__name__, location, exc)

        if len(all_leads) >= target * 2:
            break

    # Optional: Google Maps
    if GOOGLE_MAPS_API_KEY:
        for location in locations:
            try:
                all_leads.extend(find_leads_google_maps(
                    api_key=GOOGLE_MAPS_API_KEY,
                    query="nonprofit organization",
                    location=location,
                ))
                all_leads.extend(find_leads_google_maps(
                    api_key=GOOGLE_MAPS_API_KEY,
                    query="small business",
                    location=location,
                ))
            except Exception as exc:
                logger.error("Google Maps error for %s: %s", location, exc)

    filtered = _dedupe_and_filter(all_leads)
    logger.info(
        "Total after dedup + filter: %d leads (target: %d).", len(filtered), target
    )

    # Distribute leads evenly across the three sending inboxes:
    #   hello@       -> nonprofit         (12 slots)
    #   speaking@    -> speaker, creator  (12 slots, split evenly)
    #   partnerships@-> brand, talent     (12 slots, split evenly)
    from collections import defaultdict
    by_profile: dict = defaultdict(list)
    for lead in filtered:
        by_profile[lead.get("profile", "nonprofit")].append(lead)

    per_inbox = target // 3  # 12 each

    def _pull(profiles: list, slots: int) -> list:
        bucket = []
        active = [p for p in profiles if by_profile[p]]
        while len(bucket) < slots and any(by_profile[p] for p in profiles):
            for p in profiles:
                if by_profile[p] and len(bucket) < slots:
                    bucket.append(by_profile[p].pop(0))
        return bucket

    nonprofit_leads = _pull(["nonprofit"], per_inbox)
    speaking_leads = _pull(["speaker", "creator"], per_inbox)
    partner_leads = _pull(["brand", "talent"], per_inbox)

    # Interleave so all three inboxes send throughout the day
    result = []
    for i in range(max(len(nonprofit_leads), len(speaking_leads), len(partner_leads))):
        if i < len(nonprofit_leads):
            result.append(nonprofit_leads[i])
        if i < len(speaking_leads):
            result.append(speaking_leads[i])
        if i < len(partner_leads):
            result.append(partner_leads[i])

    logger.info(
        "Profile mix: %s",
        {p: sum(1 for r in result if r.get("profile") == p) for p in ["nonprofit", "speaker", "creator", "brand", "talent"]},
    )
    return result
