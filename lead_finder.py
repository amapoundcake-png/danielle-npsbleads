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
from notion_logger import is_already_contacted

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Blocklist — orgs to never contact
# ---------------------------------------------------------------------------
BLOCKED_ORGS = [
    "florida for all",
    "faith in florida",
    "dream defenders",
]

def _is_blocked(org: str) -> bool:
    org_lower = org.strip().lower()
    return any(blocked in org_lower for blocked in BLOCKED_ORGS)


def _todays_locations() -> list[str]:
    """
    Return the locations to target today.
    Always includes Orlando and Tampa, then rotates through the rest
    based on the day of the year so every market gets covered over time.
    """
    from datetime import date
    priority = ["Orlando, FL", "Tampa, FL"]
    rest = [loc for loc in TARGET_LOCATIONS if loc not in priority]
    # Pick 3 additional locations based on day of year rotation
    day_index = date.today().timetuple().tm_yday
    extras = []
    for i in range(3):
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
    ACTIVE_PROFILES = {"nonprofit", "brand", "speaker", "creator"}

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
        profile = (lead.get("profile") or "nonprofit").strip()
        if profile not in ACTIVE_PROFILES:
            logger.info("Skipping paused profile [%s]: %s", profile, lead.get("org"))
            continue
        seen_emails.add(email)
        try:
            already = is_already_contacted(email)
        except Exception as exc:
            logger.warning("Could not check Notion for %s: %s", email, exc)
            already = False
        if already:
            logger.info("Skipping already-contacted: %s", email)
            continue
        lead["email"] = email
        filtered.append(lead)
    return filtered


# ---------------------------------------------------------------------------
# Source 1: Idealist.org
# ---------------------------------------------------------------------------

def find_leads_idealist(max_leads: int = 10, location: str = "Orlando, FL") -> list[dict]:
    """Scrape nonprofit listings from Idealist.org for a given location."""
    city = location.split(",")[0].strip()
    url = f"https://www.idealist.org/en/organizations?q={requests.utils.quote(city)}&type=ORGANIZATION"
    logger.info("Scraping Idealist.org for %s...", location)
    leads = []

    resp = _get(url)
    if resp is None:
        return leads

    soup = BeautifulSoup(resp.text, "html.parser")

    # Idealist renders org cards — look for links and names
    # The site uses React, so we try to grab any structured data or static links
    org_cards = soup.find_all("a", href=re.compile(r"/en/organization/"))

    seen_hrefs: set[str] = set()
    for card in org_cards:
        href = card.get("href", "")
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        org_name = card.get_text(strip=True)
        if not org_name or len(org_name) < 3:
            continue

        org_url = urljoin("https://www.idealist.org", href)
        _polite_delay()

        # Visit the org page to get website / email
        org_resp = _get(org_url)
        if org_resp is None:
            continue

        org_soup = BeautifulSoup(org_resp.text, "html.parser")

        # Look for website link
        website_link = None
        for a in org_soup.find_all("a", href=True):
            href_val = a["href"]
            if href_val.startswith("http") and "idealist.org" not in href_val:
                website_link = href_val
                break

        email = None
        # First try inline emails on the org page
        inline_emails = _extract_emails_from_html(org_resp.text)
        if inline_emails:
            email = inline_emails[0]
        elif website_link:
            email = _find_contact_email(website_link)

        if not email:
            continue

        leads.append({
            "name": "",
            "org": org_name,
            "email": email,
            "industry": "Nonprofit",
            "source_url": org_url,
            "city": "Orlando, FL",
            "notes": "",
        })

        if len(leads) >= max_leads:
            break

    logger.info("Idealist: found %d leads with emails.", len(leads))
    return leads


# ---------------------------------------------------------------------------
# Source 2: Orlando Chamber of Commerce member directory
# ---------------------------------------------------------------------------

# Chamber URLs by city — falls back to a Google search for other cities
CHAMBER_URLS = {
    "Orlando": "https://www.orlando.org/members/",
    "Tampa": "https://www.tampachamber.com/member-directory/",
    "Birmingham": "https://www.birminghamchamber.com/directory/",
    "Atlanta": "https://www.metroatlantachamber.com/members/",
    "Charlotte": "https://www.charlottechamber.com/member-directory/",
    "Raleigh": "https://www.raleighchamber.org/directory/",
}


def find_leads_chamber(max_leads: int = 10, location: str = "Orlando, FL") -> list[dict]:
    """Scrape the local Chamber of Commerce member directory for a given location."""
    city = location.split(",")[0].strip()
    chamber_url = CHAMBER_URLS.get(city, f"https://www.google.com/search?q={requests.utils.quote(city)}+chamber+of+commerce+member+directory")
    logger.info("Scraping Chamber of Commerce for %s...", location)
    leads = []

    resp = _get(chamber_url)
    if resp is None:
        return leads

    soup = BeautifulSoup(resp.text, "html.parser")

    # Chamber pages vary — look for member listing links or business names
    # Common pattern: list items or divs with business name + website
    member_links = soup.find_all("a", href=re.compile(r"https?://(?!orlando\.org)"))

    seen: set[str] = set()
    for link in member_links:
        biz_url = link["href"]
        parsed = urlparse(biz_url)
        if not parsed.netloc or parsed.netloc in seen:
            continue
        seen.add(parsed.netloc)

        biz_name = link.get_text(strip=True)
        if not biz_name or len(biz_name) < 3:
            continue

        _polite_delay()
        email = _find_contact_email(biz_url)
        if not email:
            continue

        leads.append({
            "name": "",
            "org": biz_name,
            "email": email,
            "industry": "Small Business",
            "source_url": chamber_url,
            "city": "Orlando, FL",
            "notes": "",
        })

        if len(leads) >= max_leads:
            break

    logger.info("Chamber: found %d leads with emails.", len(leads))
    return leads


# ---------------------------------------------------------------------------
# Source 3: Candid / GuideStar (public search)
# ---------------------------------------------------------------------------

def find_leads_guidestar(max_leads: int = 10, location: str = "Orlando, FL") -> list[dict]:
    """
    Attempt to scrape nonprofits from GuideStar/Candid for a given location.

    Note: GuideStar is heavily JavaScript-rendered. This function scrapes
    the static HTML for any structured data or embedded org info.
    Results will be sparse unless the page loads static content.
    """
    city = location.split(",")[0].strip()
    candid_url = f"https://www.guidestar.org/search#advanced?searchTerm={requests.utils.quote(city)}&type=Organization"
    logger.info("Scraping GuideStar/Candid for %s...", location)
    leads = []

    resp = _get(candid_url)
    if resp is None:
        return leads

    soup = BeautifulSoup(resp.text, "html.parser")

    # Try JSON-LD structured data first
    import json
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = [data]
        else:
            continue

        for item in items:
            org_name = item.get("name", "")
            website = item.get("url", "")
            email = item.get("email", "")

            if not org_name:
                continue
            if not email and website:
                _polite_delay()
                email = _find_contact_email(website)
            if not email:
                continue

            leads.append({
                "name": "",
                "org": org_name,
                "email": email,
                "industry": "Nonprofit",
                "source_url": candid_url,
                "city": "Orlando, FL",
                "notes": "",
            })
            if len(leads) >= max_leads:
                break

    # Fallback: look for plain org name links in the HTML
    if not leads:
        org_links = soup.find_all("a", href=re.compile(r"/profile/"))
        for a in org_links:
            org_name = a.get_text(strip=True)
            if not org_name:
                continue
            profile_url = urljoin("https://www.guidestar.org", a["href"])
            _polite_delay()
            profile_resp = _get(profile_url)
            if profile_resp is None:
                continue
            emails = _extract_emails_from_html(profile_resp.text)
            if not emails:
                continue
            leads.append({
                "name": "",
                "org": org_name,
                "email": emails[0],
                "industry": "Nonprofit",
                "source_url": profile_url,
                "city": "Orlando, FL",
                "notes": "",
            })
            if len(leads) >= max_leads:
                break

    logger.info("GuideStar: found %d leads with emails.", len(leads))
    return leads


# ---------------------------------------------------------------------------
# Source 4: Orlando Local Businesses (brand deal targets)
# ---------------------------------------------------------------------------

ORLANDO_BIZ_CATEGORIES = [
    "coffee shop Orlando FL",
    "spa Orlando FL",
    "nail salon Orlando FL",
    "shoe store Orlando FL",
    "bakery Orlando FL",
    "jewelry store Orlando FL",
    "bookstore Orlando FL",
    "boutique clothing store Orlando FL",
    "hair salon Orlando FL",
    "wellness studio Orlando FL",
]


def find_leads_orlando_local(max_leads: int = 15) -> list[dict]:
    """
    Search for Orlando local businesses to target for brand deals.
    Uses DuckDuckGo HTML search to find business websites then scrapes
    contact emails directly from each site.
    """
    logger.info("Searching for Orlando local business brand deal targets...")
    leads = []
    seen_domains: set[str] = set()

    for category in ORLANDO_BIZ_CATEGORIES:
        if len(leads) >= max_leads:
            break

        search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(category)}"
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

            skip_domains = ("yelp.com", "google.com", "facebook.com", "instagram.com",
                            "yellowpages.com", "tripadvisor.com", "foursquare.com",
                            "mapquest.com", "bbb.org", "thumbtack.com")
            if any(s in domain for s in skip_domains):
                continue

            seen_domains.add(domain)
            _polite_delay()

            email = _find_contact_email(href)
            if not email:
                continue

            biz_name = domain.split(".")[0].replace("-", " ").replace("_", " ").title()

            if "coffee" in category:
                industry = "Coffee Shop"
            elif "spa" in category:
                industry = "Spa"
            elif "nail" in category:
                industry = "Nail Salon"
            elif "shoe" in category:
                industry = "Shoe Store"
            elif "baker" in category:
                industry = "Bakery"
            elif "jewelry" in category:
                industry = "Jewelry Store"
            elif "book" in category:
                industry = "Bookstore"
            elif "boutique" in category:
                industry = "Boutique"
            elif "hair" in category:
                industry = "Hair Salon"
            elif "wellness" in category:
                industry = "Wellness Studio"
            else:
                industry = "Local Business"

            leads.append({
                "name": "",
                "org": biz_name,
                "email": email,
                "industry": industry,
                "profile": "brand",
                "source_url": href,
                "city": "Orlando, FL",
                "notes": f"Orlando local business -- {category}",
            })
            logger.info("Orlando local biz found: %s <%s>", biz_name, email)

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
                    "city": "Orlando, FL",
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
                "city": "Orlando, FL",
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
        for source_fn in [find_leads_idealist, find_leads_chamber, find_leads_guidestar]:
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
    return filtered[:target]
