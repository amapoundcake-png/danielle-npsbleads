"""
lead_qualifier.py — Qualification scoring for the Lead Pipeline.

Scores discovered organizations against lane-specific rubrics.
Does NOT collect email addresses — that happens only after human approval.

Lanes:
  nonprofit_consulting  — Danielle Adams as fractional comms/outreach strategist
  nonprofit_speaking    — Danni Adams speaking to a nonprofit's community
  youth_speaking        — Danni Adams speaking to youth programs
  universities          — Danni Adams at universities, conferences, professional associations
  venue_hosting         — Danni Adams as host/emcee/MC at independent venues
  brand_partnerships    — @amapoundcake creator/UGC/activation work
  talent_representation — Danni Adams seeking theatrical/commercial representation

Tiers:
  A = strong prospect — flagged for human review
  B = possible prospect — staged at lower priority
  C = low priority — stored for auditing only
  Disqualified = removed from active pipeline, reason logged
"""

import logging
import re
import time
import random
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants: chain and large-venue disqualifiers
# ---------------------------------------------------------------------------

CHAIN_KEYWORDS = (
    "marriott", "hilton", "hyatt", "ritz", "westin", "sheraton", "doubletree",
    "hard rock", "house of blues", "live nation", "ticketmaster", "anschutz",
    "disney", "universal", "seaworld", "busch gardens", "dave and busters",
    "topgolf", "wyndham", "ihg", "best western", "omni hotels",
    "kimpton", "loews", "radisson", "sofitel", "novotel",
    "chicken n pickle", "tin roof", "dueling pianos",
)

LARGE_VENUE_PATTERNS = (
    r"\b\d{1,3}[,\s]\d{3}\+?\s*(?:seats?|capacity|guests?)\b",  # "1,000 seats"
    r"\b(?:5|6|7|8|9|10|15|20)\s*,?\s*000\s*(?:seats?|capacity|sq\.?\s*ft\.?)\b",
    r"largest\s+venue\s+in\s+\w+",
    r"in-house\s+production\s+team",
    r"full\s+av\s+production\s+staff",
    r"resident\s+entertainment\s+director",
    r"resident\s+host",
    r"locations?\s+nationwide",
    r"visit\s+us\s+at\s+any\s+of\s+our\s+\d+\s+locations?",
    r"franchis(?:e|ed)\s+locations?",
)

LARGE_VENUE_TYPE_WORDS = (
    "convention center", "arena", "stadium", "amphitheater", "amphitheatre",
    "coliseum", "colosseum",
)

DISQUALIFICATION_REASONS = {
    "chain": "National chain / franchise",
    "large_venue": "Large venue (1,000+ capacity)",
    "convention": "Convention center / arena / stadium",
    "no_programming": "No active programming",
    "no_outside_talent": "No evidence of outside talent booking",
    "inhouse_only": "In-house production only",
    "no_mission_fit": "Irrelevant mission (no intersection with Danni's documented experience)",
    "generic_listing": "Generic directory listing (not a real org page)",
    "inactive": "Inactive organization",
    "outside_geography": "Outside geographic target",
    "duplicate": "Duplicate record",
    "other": "Other",
}

# ---------------------------------------------------------------------------
# Page fetch helpers
# ---------------------------------------------------------------------------

def _polite_delay() -> None:
    time.sleep(2 + random.uniform(0, 1))


def _get_page(url: str) -> Optional[str]:
    """Fetch a URL and return its HTML text, or None on error."""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.debug("Could not fetch %s: %s", url, exc)
        return None


def _fetch_org_pages(base_url: str) -> dict:
    """
    Fetch multiple pages from an org's website: home, about, events, staff, contact.
    Returns a dict of {url: html_text} for all pages that responded.
    """
    slugs = [
        "", "about", "about-us", "events", "calendar", "shows",
        "programming", "staff", "team", "contact", "contact-us",
        "our-team", "about/team", "about/staff",
    ]
    pages = {}
    base = base_url.rstrip("/")
    for slug in slugs:
        url = f"{base}/{slug}" if slug else base
        _polite_delay()
        html = _get_page(url)
        if html:
            pages[url] = html
        if len(pages) >= 6:  # enough signal, stop fetching
            break
    return pages


def _combined_text(pages: dict) -> str:
    """Combine visible text from all fetched pages into one lowercase string."""
    combined = []
    for html in pages.values():
        try:
            soup = BeautifulSoup(html, "html.parser")
            combined.append(soup.get_text(separator=" ", strip=True))
        except Exception:
            pass
    return " ".join(combined).lower()


def _page_title(html: str) -> str:
    """Extract <title> text from HTML."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("title")
        if title:
            return title.get_text(strip=True)
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
    except Exception:
        pass
    return ""


def _extract_excerpt(text: str, keywords: list, max_chars: int = 200) -> str:
    """
    Find the first keyword match in text and return a surrounding excerpt.
    Returns empty string if no keyword found.
    """
    text_lower = text.lower()
    for kw in keywords:
        idx = text_lower.find(kw.lower())
        if idx != -1:
            start = max(0, idx - 60)
            end = min(len(text), idx + max_chars)
            return text[start:end].strip()
    return ""


def _find_staff_name_title(pages: dict) -> tuple:
    """
    Look for a named staff member and their title in the fetched pages.
    Returns (name, title) or ("", "").
    """
    name_pattern = re.compile(
        r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})\b'
    )
    title_words = (
        "director", "executive", "president", "founder", "manager",
        "coordinator", "producer", "artistic director", "booking",
        "programmer", "curator", "editor", "owner", "operator",
    )
    skip_words = {
        "Contact", "Email", "Phone", "Address", "Director", "Manager",
        "Program", "Executive", "Community", "Development",
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday", "January", "February", "March",
        "April", "June", "July", "August", "September", "October",
        "November", "December",
    }
    for url, html in pages.items():
        if "staff" not in url and "team" not in url:
            continue
        try:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = text.split("\n")
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(tw in line_lower for tw in title_words):
                    # Look at surrounding lines for a name
                    context = "\n".join(lines[max(0, i-2):i+3])
                    match = name_pattern.search(context)
                    if match:
                        name = match.group(1)
                        parts = name.split()
                        if not any(p in skip_words for p in parts):
                            return name, line.strip()[:80]
        except Exception:
            pass
    return "", ""

# ---------------------------------------------------------------------------
# Disqualification check (runs before fetching pages)
# ---------------------------------------------------------------------------

def check_disqualify_early(org_name: str, domain: str) -> Optional[str]:
    """
    Fast pre-fetch disqualification check based on org name and domain only.
    Returns disqualification reason string if disqualified, else None.
    """
    combined = (org_name + " " + domain).lower()

    for keyword in CHAIN_KEYWORDS:
        if keyword in combined:
            return DISQUALIFICATION_REASONS["chain"]

    for term in LARGE_VENUE_TYPE_WORDS:
        if term in combined:
            return DISQUALIFICATION_REASONS["convention"]

    return None


def check_disqualify_page(text: str, org_name: str) -> Optional[str]:
    """
    Page-level disqualification based on scraped text.
    Returns disqualification reason string if disqualified, else None.
    """
    text_lower = text.lower()

    for keyword in CHAIN_KEYWORDS:
        if keyword in text_lower:
            return DISQUALIFICATION_REASONS["chain"]

    for pattern in LARGE_VENUE_PATTERNS:
        if re.search(pattern, text_lower):
            return DISQUALIFICATION_REASONS["large_venue"]

    for term in LARGE_VENUE_TYPE_WORDS:
        if term in text_lower:
            return DISQUALIFICATION_REASONS["convention"]

    return None

# ---------------------------------------------------------------------------
# Size estimation
# ---------------------------------------------------------------------------

def _estimate_size(text: str, pages: dict) -> str:
    """
    Estimate org size only from explicit evidence.
    Never infers from capacity, followers, events, or revenue.
    Returns: Small (under 10) / Mid (10-75) / Large (75+) / Unknown
    """
    # Look for explicit staff page evidence
    staff_pages = {url: html for url, html in pages.items()
                   if "staff" in url or "team" in url}

    if staff_pages:
        for html in staff_pages.values():
            try:
                soup = BeautifulSoup(html, "html.parser")
                # Count named person entries (heuristic: headings or cards with names)
                names = re.findall(
                    r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', soup.get_text()
                )
                # Filter obvious false positives
                skip = {"Contact Us", "About Us", "Learn More", "Read More"}
                real_names = [n for n in names if n not in skip]
                count = len(set(real_names))
                if 1 <= count <= 10:
                    return "Small (under 10)"
                elif count <= 30:
                    return "Mid (10-75)"
                elif count > 30:
                    return "Mid (10-75)"  # still might be mid
            except Exception:
                pass

    # Look for explicit language
    size_signals = {
        "Small (under 10)": (
            "family-owned", "family owned", "small team", "just the two of us",
            "husband and wife", "solo", "one-person", "one person",
        ),
        "Mid (10-75)": (
            "our team of", "staff of", "employees",
        ),
        "Large (75+)": (
            "hundreds of employees", "large organization", "national staff",
        ),
    }

    for label, signals in size_signals.items():
        if any(s in text for s in signals):
            return label

    return "Unknown"


def _is_independent(text: str) -> str:
    """
    Determine if an org appears to be independent/local.
    Returns: Yes / No / Unknown
    """
    independent_signals = (
        "family-owned", "family owned", "locally owned", "locally operated",
        "independently owned", "independently operated", "founded by",
        "owner-operated", "small business",
    )
    chain_signals = (
        "part of", "member of", "franchise", "our locations", "locations nationwide",
        "corporate", "national chain",
    )

    if any(s in text for s in chain_signals):
        return "No"
    if any(s in text for s in independent_signals):
        return "Yes"
    return "Unknown"

# ---------------------------------------------------------------------------
# Programming and hiring potential signals
# ---------------------------------------------------------------------------

PROGRAMMING_KEYWORDS = (
    "upcoming", "schedule", "calendar", "shows", "performances",
    "events", "tickets", "reserve", "book now", "buy tickets",
    "doors open", "showtime", "this weekend", "next week",
    "season", "lineup", "series",
)

HIRING_KEYWORDS = (
    "host", "emcee", "mc ", "moderator", "facilitator",
    "comedy night", "open mic", "jazz night", "trivia night",
    "book talent", "outside talent", "guest", "performer",
    "rotating", "weekly show", "monthly show",
)

INHOUSE_SIGNALS = (
    "in-house host", "resident host", "our host", "house emcee",
    "staff-led", "staff led", "in-house production",
    "resident entertainment", "in-house entertainment",
)

def _score_programming(text: str) -> tuple:
    """
    Returns (score 0-2, excerpt of evidence found).
    """
    text_lower = text.lower()

    # Check for dated upcoming events (strongest signal)
    has_dated = bool(re.search(
        r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\.?\s+\d{1,2}',
        text_lower
    ) or re.search(r'\b\d{1,2}/\d{1,2}/20\d{2}\b', text_lower))

    has_calendar = any(kw in text_lower for kw in PROGRAMMING_KEYWORDS)
    excerpt = _extract_excerpt(text, list(PROGRAMMING_KEYWORDS), 160)

    if has_dated and has_calendar:
        return 2, excerpt
    elif has_calendar:
        return 1, excerpt
    return 0, ""


def _score_hiring_potential(text: str) -> int:
    text_lower = text.lower()

    if any(s in text_lower for s in INHOUSE_SIGNALS):
        return 0

    host_mentions = sum(1 for kw in HIRING_KEYWORDS if kw in text_lower)
    if host_mentions >= 3:
        return 2
    elif host_mentions >= 1:
        return 1
    return 0

# ---------------------------------------------------------------------------
# Lane: Venue & Event Hosting
# ---------------------------------------------------------------------------

VENUE_TYPE_SCORES = {
    "comedy club": 3,
    "improv theater": 3,
    "improv theatre": 3,
    "jazz club": 3,
    "cabaret": 3,
    "black box theater": 3,
    "black box theatre": 3,
    "black-box theater": 3,
    "black-box theatre": 3,
    "community theater": 2,
    "community theatre": 2,
    "performing arts": 2,
    "supper club": 2,
    "dinner theater": 2,
    "dinner theatre": 2,
    "arts center": 2,
    "cultural center": 2,
    "gallery": 2,
    "creative space": 2,
    "music venue": 1,
    "live music": 1,
    "lounge": 1,
    "jazz lounge": 3,
    "speakeasy": 1,
    "boutique venue": 1,
    "event space": 1,
}


def _score_venue_type(text: str, org_name: str, query_industry: str) -> tuple:
    """Returns (score 0-3, venue_type label)."""
    combined = (text + " " + org_name + " " + query_industry).lower()

    best_score = 0
    best_label = "Other"

    for venue_type, score in VENUE_TYPE_SCORES.items():
        if venue_type in combined and score > best_score:
            best_score = score
            best_label = venue_type.title()

    return best_score, best_label


def score_venue_hosting(
    org_name: str, domain: str, pages: dict, query_industry: str = ""
) -> dict:
    """
    Score an org for the Venue & Event Hosting lane.
    Returns full scoring breakdown dict.
    """
    text = _combined_text(pages)
    home_html = next(iter(pages.values()), "") if pages else ""

    # Pre-fetch disqualification (belt and suspenders, also runs on text)
    page_disq = check_disqualify_page(text, org_name)
    if page_disq:
        return {
            "lane": "venue_hosting",
            "tier": "Disqualified",
            "total_score": 0,
            "disqualification_reason": page_disq,
            "breakdown": {},
            "venue_type": "Unknown",
            "programming_evidence": "",
            "contact_name": "",
            "contact_title": "",
            "estimated_size": "Unknown",
            "independent": "Unknown",
            "why_danni_fits": "",
            "evidence_source": "",
        }

    # Score each category
    venue_score, venue_type = _score_venue_type(text, org_name, query_industry)
    prog_score, prog_excerpt = _score_programming(text)
    hire_score = _score_hiring_potential(text)
    estimated_size = _estimate_size(text, pages)
    independent = _is_independent(text)

    # Independence (max 3): 2 for independent, +1 for local language
    if independent == "No":
        indep_score = 0
    elif independent == "Yes":
        indep_score = 2
        local_bonus_words = (
            "family-owned", "family owned", "locally owned",
            "locally operated", "founded in", "our neighborhood",
        )
        if any(w in text.lower() for w in local_bonus_words):
            indep_score = 3
    else:
        indep_score = 1  # Unknown — neutral

    # Contact reachability (max 1)
    contact_name, contact_title = _find_staff_name_title(pages)
    contact_score = 1 if contact_name else 0

    total = venue_score + indep_score + prog_score + hire_score + contact_score

    # Tier
    if total >= 8:
        tier = "A"
    elif total >= 5:
        tier = "B"
    elif total >= 2:
        tier = "C"
    else:
        tier = "Disqualified"
        return {
            "lane": "venue_hosting",
            "tier": "Disqualified",
            "total_score": total,
            "disqualification_reason": DISQUALIFICATION_REASONS["no_programming"],
            "breakdown": {
                "venue_type": venue_score,
                "independence": indep_score,
                "programming": prog_score,
                "hiring_potential": hire_score,
                "contact": contact_score,
            },
            "venue_type": venue_type,
            "programming_evidence": prog_excerpt,
            "contact_name": contact_name,
            "contact_title": contact_title,
            "estimated_size": estimated_size,
            "independent": independent,
            "why_danni_fits": "",
            "evidence_source": "",
        }

    # Generate why_danni_fits
    why, evidence_source = _generate_why_venue(
        org_name, venue_type, prog_excerpt, hire_score, contact_name, pages
    )

    return {
        "lane": "venue_hosting",
        "tier": tier,
        "total_score": total,
        "disqualification_reason": "",
        "breakdown": {
            "venue_type": venue_score,
            "independence": indep_score,
            "programming": prog_score,
            "hiring_potential": hire_score,
            "contact": contact_score,
        },
        "venue_type": venue_type,
        "programming_evidence": prog_excerpt[:300],
        "contact_name": contact_name,
        "contact_title": contact_title,
        "estimated_size": estimated_size,
        "independent": independent,
        "why_danni_fits": why,
        "evidence_source": evidence_source,
    }


def _generate_why_venue(
    org_name, venue_type, prog_excerpt, hire_score, contact_name, pages
) -> tuple:
    """
    Generate why_danni_fits for venue leads.
    Requires at least 2 signals (venue type + programming OR hiring evidence).
    Returns (why_text, evidence_source_url).
    """
    signals_found = []
    signals_missing = []

    if venue_type and venue_type != "Other":
        signals_found.append(f"venue type: {venue_type}")
    else:
        signals_missing.append("specific venue type")

    if prog_excerpt:
        signals_found.append(f"active programming: '{prog_excerpt[:80]}...'")
    else:
        signals_missing.append("active programming calendar")

    if hire_score >= 1:
        signals_found.append("references to hosts/emcees/outside talent")
    else:
        signals_missing.append("mention of outside hosts or emcees")

    if len(signals_found) < 2:
        return (
            f"NEEDS MANUAL REVIEW — found: {', '.join(signals_found) or 'none'} / "
            f"missing: {', '.join(signals_missing)}",
            "",
        )

    # Build the reason from what was actually found
    venue_phrase = f"a {venue_type.lower()}" if venue_type != "Other" else "a venue"
    prog_phrase = ""
    if prog_excerpt:
        prog_phrase = f" with active programming ({prog_excerpt[:60].strip()}...)"

    hire_phrase = ""
    if hire_score >= 2:
        hire_phrase = " and regularly books outside hosts or emcees"
    elif hire_score == 1:
        hire_phrase = " with programming formats that typically involve a host"

    danni_credit = (
        "Danni has hosted the Social Icon Influencer Conference and BET Beauty Brunch, "
        "appeared on TLC, The Jennifer Hudson Show, and Tamron Hall, and has experience "
        "as an emcee, moderator, and on-camera host."
    )

    why = (
        f"{org_name} is {venue_phrase}{prog_phrase}{hire_phrase}. "
        f"{danni_credit} "
        f"The venue's programming format is a realistic match for her hosting work."
    )

    # Evidence source: the first events/calendar page found
    evidence_url = ""
    for url in pages:
        if any(s in url for s in ("event", "calendar", "shows", "tickets")):
            evidence_url = url
            break
    if not evidence_url and pages:
        evidence_url = next(iter(pages))

    return why, evidence_url

# ---------------------------------------------------------------------------
# Lane: Nonprofit Consulting
# ---------------------------------------------------------------------------

NONPROFIT_CONSULTING_PROGRAMMING_KEYWORDS = (
    "communications", "outreach", "campaign", "marketing", "visibility",
    "stakeholder", "community engagement", "partnerships", "donor",
    "fundraising", "newsletter", "social media", "digital", "annual report",
    "strategic", "messaging", "brand",
)

NONPROFIT_MISSION_KEYWORDS = (
    "women", "youth", "survivors", "lgbtq", "queer", "trans",
    "body image", "mental health", "arts", "community", "housing",
    "food", "health", "education", "civic", "advocacy",
)


def score_nonprofit_consulting(org_name: str, domain: str, pages: dict) -> dict:
    """Score an org for the Nonprofit Consulting lane."""
    text = _combined_text(pages)
    estimated_size = _estimate_size(text, pages)
    independent = _is_independent(text)
    contact_name, contact_title = _find_staff_name_title(pages)

    # Category 1: Programming Need (max 3)
    # Does the org have documented programming where Danni's consulting skills apply?
    prog_keywords_found = [kw for kw in NONPROFIT_CONSULTING_PROGRAMMING_KEYWORDS
                           if kw in text.lower()]
    if len(prog_keywords_found) >= 4:
        prog_score = 3
    elif len(prog_keywords_found) >= 2:
        prog_score = 2
    elif len(prog_keywords_found) >= 1:
        prog_score = 1
    else:
        prog_score = 0

    prog_excerpt = _extract_excerpt(text, prog_keywords_found[:3], 200)

    # Category 2: Mission Alignment (max 2) — population served supports match, not decides it
    mission_found = [kw for kw in NONPROFIT_MISSION_KEYWORDS if kw in text.lower()]
    if len(mission_found) >= 3:
        mission_score = 2
    elif len(mission_found) >= 1:
        mission_score = 1
    else:
        mission_score = 0

    # Category 3: Budget Signals (max 2)
    budget_signals = (
        "annual report", "grant", "donor", "funders", "sponsors",
        "fundraising", "campaign", "endowment", "planned giving",
    )
    budget_found = [s for s in budget_signals if s in text.lower()]
    budget_score = 2 if len(budget_found) >= 2 else (1 if budget_found else 0)

    # Category 4: Staff and Structure (max 2)
    has_staff_page = any("staff" in url or "team" in url for url in pages)
    has_board = "board" in text.lower() or "advisory" in text.lower()
    if has_staff_page and contact_name:
        staff_score = 2
    elif has_board or has_staff_page:
        staff_score = 1
    else:
        staff_score = 0

    # Category 5: Contact Reachability (max 1)
    contact_score = 1 if contact_name else 0

    total = prog_score + mission_score + budget_score + staff_score + contact_score

    if total >= 7:
        tier = "A"
    elif total >= 4:
        tier = "B"
    elif total >= 1:
        tier = "C"
    else:
        tier = "Disqualified"

    why, evidence_source = _generate_why_nonprofit_consulting(
        org_name, prog_keywords_found, mission_found, budget_found, pages
    )

    return {
        "lane": "nonprofit_consulting",
        "tier": tier,
        "total_score": total,
        "disqualification_reason": "" if tier != "Disqualified" else DISQUALIFICATION_REASONS["no_mission_fit"],
        "breakdown": {
            "programming_need": prog_score,
            "mission_alignment": mission_score,
            "budget_signals": budget_score,
            "staff_structure": staff_score,
            "contact": contact_score,
        },
        "venue_type": "Nonprofit",
        "programming_evidence": prog_excerpt[:300],
        "contact_name": contact_name,
        "contact_title": contact_title,
        "estimated_size": estimated_size,
        "independent": independent,
        "why_danni_fits": why,
        "evidence_source": evidence_source,
    }


def _generate_why_nonprofit_consulting(
    org_name, prog_keywords_found, mission_found, budget_found, pages
) -> tuple:
    signals_found = []
    signals_missing = []

    if len(prog_keywords_found) >= 2:
        signals_found.append(f"communications/outreach need ({', '.join(prog_keywords_found[:3])})")
    else:
        signals_missing.append("documented communications or outreach programming")

    if mission_found:
        signals_found.append(f"mission alignment ({', '.join(mission_found[:3])})")
    else:
        signals_missing.append("mission overlap with Danni's documented expertise")

    if budget_found:
        signals_found.append(f"budget signals ({', '.join(budget_found[:2])})")
    else:
        signals_missing.append("budget or funding evidence")

    if len(signals_found) < 2:
        return (
            f"NEEDS MANUAL REVIEW — found: {', '.join(signals_found) or 'none'} / "
            f"missing: {', '.join(signals_missing)}",
            "",
        )

    evidence_url = next(iter(pages), "")
    why = (
        f"{org_name} shows evidence of {signals_found[0]}"
        + (f" and {signals_found[1]}" if len(signals_found) > 1 else "")
        + ". Danielle Adams has an MPA from UNF, led statewide communications campaigns "
        "as Senior Strategic Director at Florida For All, managed the City of Sanford "
        "Influencer Program, and co-created the Institute for Body Image. "
        "She works with nonprofits on outreach systems, donor visibility, and community engagement."
    )
    return why, evidence_url

# ---------------------------------------------------------------------------
# Lane: Nonprofit Speaking / Youth Speaking
# ---------------------------------------------------------------------------

NONPROFIT_SPEAKER_MISSION_KEYWORDS = {
    "youth_speaking": (
        "youth", "teen", "girl", "young women", "student",
        "after school", "mentoring", "kids", "children", "adolescent",
    ),
    "nonprofit_speaking": (
        "women", "survivors", "domestic", "shelter", "lgbtq", "queer",
        "community", "arts", "culture", "health", "wellness", "body image",
    ),
}


def score_nonprofit_speaking(
    org_name: str, domain: str, pages: dict, lane: str = "nonprofit_speaking"
) -> dict:
    """Score an org for Nonprofit Speaking or Youth Speaking lane."""
    text = _combined_text(pages)
    estimated_size = _estimate_size(text, pages)
    contact_name, contact_title = _find_staff_name_title(pages)

    # Category 1: Programming Need (max 3)
    speaker_signals = (
        "speaker", "keynote", "workshop", "facilitator", "presenter",
        "panel", "event", "program", "community education", "seminar",
        "webinar", "talk", "discussion", "curriculum",
    )
    speaker_found = [s for s in speaker_signals if s in text.lower()]
    if len(speaker_found) >= 4:
        prog_score = 3
    elif len(speaker_found) >= 2:
        prog_score = 2
    elif len(speaker_found) >= 1:
        prog_score = 1
    else:
        prog_score = 0

    prog_excerpt = _extract_excerpt(text, speaker_found[:3], 200)

    # Category 2: Mission Alignment (max 2)
    mission_keywords = NONPROFIT_SPEAKER_MISSION_KEYWORDS.get(lane, ())
    mission_found = [kw for kw in mission_keywords if kw in text.lower()]
    mission_score = 2 if len(mission_found) >= 2 else (1 if mission_found else 0)

    # Category 3: Budget (max 2)
    budget_signals = ("grant", "donor", "fundraising", "sponsors", "annual report")
    budget_found = [s for s in budget_signals if s in text.lower()]
    budget_score = 2 if len(budget_found) >= 2 else (1 if budget_found else 0)

    # Category 4: Staff (max 2)
    has_staff_page = any("staff" in url or "team" in url for url in pages)
    has_board = "board" in text.lower()
    if has_staff_page and contact_name:
        staff_score = 2
    elif has_board or has_staff_page:
        staff_score = 1
    else:
        staff_score = 0

    # Category 5: Contact (max 1)
    contact_score = 1 if contact_name else 0

    total = prog_score + mission_score + budget_score + staff_score + contact_score

    if total >= 7:
        tier = "A"
    elif total >= 4:
        tier = "B"
    elif total >= 1:
        tier = "C"
    else:
        tier = "Disqualified"

    why, evidence_source = _generate_why_speaking(
        org_name, lane, speaker_found, mission_found, pages
    )

    return {
        "lane": lane,
        "tier": tier,
        "total_score": total,
        "disqualification_reason": "" if tier != "Disqualified" else DISQUALIFICATION_REASONS["no_mission_fit"],
        "breakdown": {
            "programming_need": prog_score,
            "mission_alignment": mission_score,
            "budget_signals": budget_score,
            "staff_structure": staff_score,
            "contact": contact_score,
        },
        "venue_type": "Nonprofit",
        "programming_evidence": prog_excerpt[:300],
        "contact_name": contact_name,
        "contact_title": contact_title,
        "estimated_size": estimated_size,
        "independent": _is_independent(text),
        "why_danni_fits": why,
        "evidence_source": evidence_source,
    }


def _generate_why_speaking(
    org_name, lane, speaker_found, mission_found, pages
) -> tuple:
    signals_found = []
    signals_missing = []

    if len(speaker_found) >= 2:
        signals_found.append(f"documented speaker/workshop programming ({', '.join(speaker_found[:3])})")
    else:
        signals_missing.append("speaker or workshop programming evidence")

    if mission_found:
        signals_found.append(f"mission relevance ({', '.join(mission_found[:2])})")
    else:
        signals_missing.append("mission overlap with Danni's speaking topics")

    if len(signals_found) < 2:
        return (
            f"NEEDS MANUAL REVIEW — found: {', '.join(signals_found) or 'none'} / "
            f"missing: {', '.join(signals_missing)}",
            "",
        )

    if lane == "youth_speaking":
        danni_context = (
            "Danni Adams has delivered talks to youth programs on social media literacy, "
            "digital safety, self-esteem, and not giving up. She has done this work at "
            "girls' mentoring programs and women's shelters on an ongoing basis."
        )
    else:
        danni_context = (
            "Danni Adams has spoken at Harvard, the University of Ottawa, "
            "Bethune-Cookman University, and the Seminole Leadership Conference. "
            "Her topics include resilience, confidence, storytelling, social media, "
            "and building a career when no one hands you the blueprint."
        )

    why = (
        f"{org_name} has {signals_found[0]} and {signals_found[1]}. "
        f"{danni_context}"
    )
    evidence_url = next(iter(pages), "")
    return why, evidence_url

# ---------------------------------------------------------------------------
# Lane: Universities & Conferences
# ---------------------------------------------------------------------------

def score_universities(org_name: str, domain: str, pages: dict) -> dict:
    """Score an org for the Universities & Conferences lane."""
    text = _combined_text(pages)
    contact_name, contact_title = _find_staff_name_title(pages)

    # Category 1: Speaker Programming (max 3)
    speaker_signals = (
        "request a speaker", "speaker series", "speaker bureau",
        "keynote", "speaker", "panel", "conference", "symposium",
        "lecture series", "visiting speaker",
    )
    speaker_found = [s for s in speaker_signals if s in text.lower()]
    if "request a speaker" in text.lower() or "speaker series" in text.lower():
        prog_score = 3
    elif len(speaker_found) >= 3:
        prog_score = 2
    elif len(speaker_found) >= 1:
        prog_score = 1
    else:
        prog_score = 0

    prog_excerpt = _extract_excerpt(text, list(speaker_signals), 200)

    # Category 2: Org Type (max 2)
    is_university = any(w in (org_name + " " + domain).lower() for w in (
        "university", "college", "edu", "institute", "school"
    ))
    is_conference = any(w in text.lower() for w in (
        "conference", "summit", "symposium", "association", "professional development"
    ))
    if is_university:
        org_type_score = 2
    elif is_conference:
        org_type_score = 1
    else:
        org_type_score = 0

    # Category 3: Budget Signals (max 2)
    budget_signals = (
        "ticket", "registration fee", "sponsor", "honorarium",
        "speaker fee", "paid", "professional development",
    )
    budget_found = [s for s in budget_signals if s in text.lower()]
    budget_score = 2 if len(budget_found) >= 2 else (1 if budget_found else 0)

    # Category 4: Contact (max 1)
    contact_score = 1 if contact_name else 0

    # Category 5: Audience Alignment (max 2)
    audience_signals = (
        "women", "youth", "creatives", "first-gen", "first generation",
        "minority", "underrepresented", "diverse", "community",
        "professional women", "emerging leaders",
    )
    topic_signals = (
        "personal brand", "social media", "creator", "resilience",
        "career", "entrepreneurship", "storytelling", "networking",
        "leadership", "body image", "digital",
    )
    audience_found = [s for s in audience_signals if s in text.lower()]
    topic_found = [s for s in topic_signals if s in text.lower()]
    if audience_found and topic_found:
        audience_score = 2
    elif audience_found or topic_found:
        audience_score = 1
    else:
        audience_score = 0

    total = prog_score + org_type_score + budget_score + contact_score + audience_score

    if total >= 7:
        tier = "A"
    elif total >= 4:
        tier = "B"
    elif total >= 1:
        tier = "C"
    else:
        tier = "Disqualified"

    signals_found = []
    if prog_score >= 2:
        signals_found.append(f"documented speaker programming ({', '.join(speaker_found[:2])})")
    if audience_found:
        signals_found.append(f"audience alignment ({', '.join(audience_found[:2])})")
    if topic_found:
        signals_found.append(f"topic alignment ({', '.join(topic_found[:2])})")

    if len(signals_found) >= 2:
        why = (
            f"{org_name} has {signals_found[0]} and {signals_found[1]}. "
            "Danni Adams has spoken at Harvard University, the University of Ottawa, "
            "Full Sail University, Bethune-Cookman University, and the Seminole Leadership Conference. "
            "She has been featured on The Jennifer Hudson Show and Tamron Hall."
        )
        evidence_url = next(iter(pages), "")
    else:
        signals_missing = []
        if prog_score < 2:
            signals_missing.append("clear speaker booking process")
        if not audience_found:
            signals_missing.append("audience alignment evidence")
        why = (
            f"NEEDS MANUAL REVIEW — found: {', '.join(signals_found) or 'none'} / "
            f"missing: {', '.join(signals_missing)}"
        )
        evidence_url = ""

    return {
        "lane": "universities",
        "tier": tier,
        "total_score": total,
        "disqualification_reason": "" if tier != "Disqualified" else DISQUALIFICATION_REASONS["no_mission_fit"],
        "breakdown": {
            "speaker_programming": prog_score,
            "org_type": org_type_score,
            "budget_signals": budget_score,
            "contact": contact_score,
            "audience_alignment": audience_score,
        },
        "venue_type": "University" if is_university else "Conference",
        "programming_evidence": prog_excerpt[:300],
        "contact_name": contact_name,
        "contact_title": contact_title,
        "estimated_size": _estimate_size(text, pages),
        "independent": "Unknown",
        "why_danni_fits": why,
        "evidence_source": evidence_url,
    }

# ---------------------------------------------------------------------------
# Lane: Brand Partnerships
# ---------------------------------------------------------------------------

CREATOR_SIGNALS = (
    "influencer", "creator", "ugc", "user-generated", "ambassador",
    "brand ambassador", "content creator", "collaboration", "collab",
    "partnership", "brand partner", "social media campaign",
    "experiential", "activation", "brand activation", "pr event",
    "micro-influencer", "nano influencer", "content partnership",
    "sponsored content", "paid partnership",
)

BRAND_AUDIENCE_SIGNALS = (
    "women", "plus size", "curvy", "body positive", "inclusive",
    "lifestyle", "fashion", "beauty", "wellness", "food", "travel",
    "home", "health", "fitness", "style",
)


def score_brand_partnerships(org_name: str, domain: str, pages: dict) -> dict:
    """Score an org for the Brand Partnerships lane."""
    text = _combined_text(pages)
    contact_name, contact_title = _find_staff_name_title(pages)

    # Category 1: Creator/Influencer Marketing Evidence (max 4 — this is the gate)
    creator_found = [s for s in CREATOR_SIGNALS if s in text.lower()]
    if len(creator_found) >= 4:
        creator_score = 4
    elif len(creator_found) >= 2:
        creator_score = 3
    elif len(creator_found) >= 1:
        creator_score = 2
    else:
        creator_score = 0  # No creator marketing evidence = disqualify

    creator_excerpt = _extract_excerpt(text, list(CREATOR_SIGNALS), 200)

    # Category 2: Consumer Audience Relevance (max 2)
    audience_found = [s for s in BRAND_AUDIENCE_SIGNALS if s in text.lower()]
    audience_score = 2 if len(audience_found) >= 2 else (1 if audience_found else 0)

    # Category 3: Contact (max 1)
    contact_score = 1 if contact_name else 0

    if creator_score == 0:
        return {
            "lane": "brand_partnerships",
            "tier": "Disqualified",
            "total_score": 0,
            "disqualification_reason": "No evidence of influencer/creator marketing activity",
            "breakdown": {"creator_marketing": 0, "audience_relevance": 0, "contact": 0},
            "venue_type": "Brand",
            "programming_evidence": "",
            "contact_name": contact_name,
            "contact_title": contact_title,
            "estimated_size": _estimate_size(text, pages),
            "independent": _is_independent(text),
            "why_danni_fits": "",
            "evidence_source": "",
        }

    total = creator_score + audience_score + contact_score

    if total >= 6:
        tier = "A"
    elif total >= 4:
        tier = "B"
    elif total >= 2:
        tier = "C"
    else:
        tier = "Disqualified"

    signals_found = []
    if creator_found:
        signals_found.append(f"creator/influencer marketing ({', '.join(creator_found[:3])})")
    if audience_found:
        signals_found.append(f"audience relevance ({', '.join(audience_found[:2])})")

    if len(signals_found) >= 2:
        why = (
            f"{org_name} shows evidence of {signals_found[0]} and {signals_found[1]}. "
            "@amapoundcake (Danni Adams) is a lifestyle creator with 52.5K Instagram followers, "
            "74% women ages 25-54, based in Orlando with top markets in Atlanta, Miami, and NYC. "
            "She has worked with T-Mobile, YITTY by Lizzo, and Hilton Hotels."
        )
        evidence_url = next(iter(pages), "")
    else:
        why = (
            f"NEEDS MANUAL REVIEW — found: {', '.join(signals_found) or 'none'} / "
            "missing: clear audience-creator alignment"
        )
        evidence_url = ""

    return {
        "lane": "brand_partnerships",
        "tier": tier,
        "total_score": total,
        "disqualification_reason": "",
        "breakdown": {
            "creator_marketing": creator_score,
            "audience_relevance": audience_score,
            "contact": contact_score,
        },
        "venue_type": "Brand",
        "programming_evidence": creator_excerpt[:300],
        "contact_name": contact_name,
        "contact_title": contact_title,
        "estimated_size": _estimate_size(text, pages),
        "independent": _is_independent(text),
        "why_danni_fits": why,
        "evidence_source": evidence_url,
    }

# ---------------------------------------------------------------------------
# Lane: Talent & Representation
# ---------------------------------------------------------------------------

TALENT_AGENCY_SIGNALS = (
    "talent agency", "talent management", "literary agency",
    "represents", "our roster", "roster of talent", "client roster",
    "theatrical representation", "commercial representation",
    "actors", "actresses", "models", "hosts", "on-camera talent",
    "television talent", "submit", "submissions", "submission guidelines",
    "seeking representation", "now accepting",
)

AGENCY_DISQUALIFY = (
    "staffing agency", "temp agency", "employment agency",
    "job placement", "recruiting", "headhunter", "hr solutions",
)


def score_talent_representation(org_name: str, domain: str, pages: dict) -> dict:
    """Score an org for the Talent & Representation lane."""
    text = _combined_text(pages)
    contact_name, contact_title = _find_staff_name_title(pages)

    # Hard disqualify: staffing/employment agencies are not the target
    if any(s in text.lower() for s in AGENCY_DISQUALIFY):
        return {
            "lane": "talent_representation",
            "tier": "Disqualified",
            "total_score": 0,
            "disqualification_reason": "Staffing or employment agency — not theatrical representation",
            "breakdown": {},
            "venue_type": "Talent Agency",
            "programming_evidence": "",
            "contact_name": contact_name,
            "contact_title": contact_title,
            "estimated_size": "Unknown",
            "independent": "Unknown",
            "why_danni_fits": "",
            "evidence_source": "",
        }

    # Score representation signals (max 5)
    agency_found = [s for s in TALENT_AGENCY_SIGNALS if s in text.lower()]

    roster_signals = ("actors", "actresses", "models", "hosts", "on-camera", "television")
    roster_found = [s for s in roster_signals if s in text.lower()]

    submission_signals = ("submit", "submission", "accepting", "query", "inquire")
    sub_found = [s for s in submission_signals if s in text.lower()]

    if len(agency_found) >= 4 and roster_found and sub_found:
        agency_score = 5
    elif len(agency_found) >= 3 and (roster_found or sub_found):
        agency_score = 4
    elif len(agency_found) >= 2:
        agency_score = 3
    elif len(agency_found) >= 1:
        agency_score = 2
    else:
        agency_score = 0

    contact_score = 1 if contact_name else 0
    total = agency_score + contact_score

    if agency_score == 0:
        return {
            "lane": "talent_representation",
            "tier": "Disqualified",
            "total_score": 0,
            "disqualification_reason": "No evidence of talent representation activity",
            "breakdown": {"agency_signals": 0, "contact": 0},
            "venue_type": "Talent Agency",
            "programming_evidence": "",
            "contact_name": contact_name,
            "contact_title": contact_title,
            "estimated_size": _estimate_size(text, pages),
            "independent": _is_independent(text),
            "why_danni_fits": "",
            "evidence_source": "",
        }

    if total >= 5:
        tier = "A"
    elif total >= 3:
        tier = "B"
    else:
        tier = "C"

    signals_found = []
    if roster_found:
        signals_found.append(f"represents talent ({', '.join(roster_found[:2])})")
    if sub_found:
        signals_found.append("accepts submissions or inquiries")
    if len(agency_found) >= 2:
        signals_found.append(f"agency signals ({', '.join(agency_found[:2])})")

    if len(signals_found) >= 2:
        why = (
            f"{org_name} {signals_found[0]} and {signals_found[1]}. "
            "Danni Adams is seeking theatrical and commercial representation. "
            "Her credits include TLC, The Jennifer Hudson Show, Tamron Hall, Sixt (principal, national), "
            "Leach Law Firm (principal, regional), T-Mobile, Stage Struck at Lake Nona Arts (upcoming), "
            "Vogue and The Cut editorial, and Miami Swim Week. "
            "She is available nationally and internationally."
        )
        evidence_url = next(iter(pages), "")
    else:
        why = (
            f"NEEDS MANUAL REVIEW — found: {', '.join(signals_found) or 'none'} / "
            "missing: clear representation or roster evidence"
        )
        evidence_url = ""

    return {
        "lane": "talent_representation",
        "tier": tier,
        "total_score": total,
        "disqualification_reason": "",
        "breakdown": {"agency_signals": agency_score, "contact": contact_score},
        "venue_type": "Talent Agency",
        "programming_evidence": _extract_excerpt(text, list(TALENT_AGENCY_SIGNALS), 200)[:300],
        "contact_name": contact_name,
        "contact_title": contact_title,
        "estimated_size": _estimate_size(text, pages),
        "independent": _is_independent(text),
        "why_danni_fits": why,
        "evidence_source": evidence_url,
    }

# ---------------------------------------------------------------------------
# Primary qualifier: routes an org to the right lane(s) and picks primary
# ---------------------------------------------------------------------------

LANE_TO_PROFILE = {
    "venue_hosting": "venue_host",
    "nonprofit_consulting": "nonprofit",
    "nonprofit_speaking": "nonprofit_speaker",
    "youth_speaking": "nonprofit_speaker",
    "universities": "speaker",
    "brand_partnerships": "brand",
    "talent_representation": "talent",
}


def qualify_lead(
    org_name: str,
    domain: str,
    source_url: str,
    city: str,
    state: str,
    query_industry: str = "",
    candidate_lanes: list = None,
) -> dict:
    """
    Full qualification pass for a discovered org.

    Steps:
    1. Early disqualification check (no page fetch)
    2. Fetch org pages
    3. Page-level disqualification check
    4. Score against candidate lanes
    5. Pick primary and secondary lane
    6. Return full lead record

    Args:
        org_name: org name (from page title or <h1>)
        domain: bare domain (e.g. "thegreenroom.com")
        source_url: URL where the org was discovered
        city: city string
        state: state string
        query_industry: industry tag from the search query that found this org
        candidate_lanes: list of lane names to score against.
                         If None, scores against all lanes.
    Returns:
        Full lead dict ready for Notion staging.
    """
    if candidate_lanes is None:
        candidate_lanes = list(LANE_TO_PROFILE.keys())

    # Step 1: Pre-fetch disqualification
    early_disq = check_disqualify_early(org_name, domain)
    if early_disq:
        logger.info("Pre-fetch disqualified: %s — %s", org_name, early_disq)
        return _disqualified_record(
            org_name, domain, source_url, city, state, early_disq
        )

    # Step 2: Fetch pages
    base_url = f"https://{domain}"
    logger.info("Qualifying: %s (%s)...", org_name, domain)
    pages = _fetch_org_pages(base_url)

    if not pages:
        logger.info("No pages fetched for %s — disqualifying", org_name)
        return _disqualified_record(
            org_name, domain, source_url, city, state,
            "Could not fetch org website — may be inactive"
        )

    # Step 3: Page-level disqualification
    combined_text = _combined_text(pages)
    page_disq = check_disqualify_page(combined_text, org_name)
    if page_disq:
        logger.info("Page-level disqualified: %s — %s", org_name, page_disq)
        return _disqualified_record(
            org_name, domain, source_url, city, state, page_disq
        )

    # Step 4: Score each candidate lane
    scores = {}
    for lane in candidate_lanes:
        try:
            if lane == "venue_hosting":
                scores[lane] = score_venue_hosting(org_name, domain, pages, query_industry)
            elif lane == "nonprofit_consulting":
                scores[lane] = score_nonprofit_consulting(org_name, domain, pages)
            elif lane == "nonprofit_speaking":
                scores[lane] = score_nonprofit_speaking(org_name, domain, pages, "nonprofit_speaking")
            elif lane == "youth_speaking":
                scores[lane] = score_nonprofit_speaking(org_name, domain, pages, "youth_speaking")
            elif lane == "universities":
                scores[lane] = score_universities(org_name, domain, pages)
            elif lane == "brand_partnerships":
                scores[lane] = score_brand_partnerships(org_name, domain, pages)
            elif lane == "talent_representation":
                scores[lane] = score_talent_representation(org_name, domain, pages)
        except Exception as exc:
            logger.error("Scoring error for %s / lane %s: %s", org_name, lane, exc)

    # Step 5: Pick primary and secondary lane
    # Only count non-disqualified lanes
    active = {
        lane: result for lane, result in scores.items()
        if result.get("tier") in ("A", "B", "C")
    }

    if not active:
        return _disqualified_record(
            org_name, domain, source_url, city, state,
            "Scored below threshold on all candidate lanes"
        )

    # Sort by score descending
    sorted_lanes = sorted(active.items(), key=lambda x: x[1]["total_score"], reverse=True)
    primary_lane, primary_result = sorted_lanes[0]

    secondary_lane = ""
    secondary_lane_reasoning = ""
    if len(sorted_lanes) > 1:
        second_lane, second_result = sorted_lanes[1]
        # Only record secondary if it scores within 2 pts of primary and is B or above
        if (primary_result["total_score"] - second_result["total_score"] <= 2
                and second_result["tier"] in ("A", "B")):
            secondary_lane = second_lane
            secondary_lane_reasoning = (
                f"Secondary: {second_lane} (score {second_result['total_score']}) — "
                f"{second_result.get('why_danni_fits', '')[:100]}"
            )

    lane_reasoning = (
        f"Primary: {primary_lane} (score {primary_result['total_score']}, tier {primary_result['tier']}) — "
        f"{primary_result.get('why_danni_fits', '')[:120]}"
    )
    if secondary_lane_reasoning:
        lane_reasoning += " | " + secondary_lane_reasoning

    # Step 6: Build full lead record
    home_html = next(iter(pages.values()), "")
    page_title = _page_title(home_html)

    return {
        # Identity
        "org_name": page_title or org_name,
        "domain": domain,
        "source_url": source_url,
        "city": city,
        "state": state,

        # Scoring
        "lead_score": primary_result["tier"],
        "primary_lane": primary_lane,
        "secondary_lane": secondary_lane,
        "lane_reasoning": lane_reasoning,
        "profile": LANE_TO_PROFILE.get(primary_lane, "nonprofit"),

        # Org details
        "venue_type": primary_result.get("venue_type", "Other"),
        "estimated_size": primary_result.get("estimated_size", "Unknown"),
        "independent": primary_result.get("independent", "Unknown"),
        "programming_evidence": primary_result.get("programming_evidence", ""),

        # Contact (blank — email lookup happens after approval)
        "contact_name": primary_result.get("contact_name", ""),
        "contact_title": primary_result.get("contact_title", ""),
        "email": "",
        "email_source": "",
        "verification_status": "Not Started",
        "last_verified_date": "",

        # Why Danni fits
        "why_danni_fits": primary_result.get("why_danni_fits", "NEEDS MANUAL REVIEW"),
        "evidence_source": primary_result.get("evidence_source", ""),

        # Pipeline fields
        "status": "Qualified",
        "disqualification_reason": "",
        "approval_notes": "",
        "approved_by": "",
        "discovered_date": "",  # set by notion_pipeline at write time
        "sent_date": "",
        "last_contact_date": "",
        "touch_count": 0,
        "response": "",
        "last_delivery_event": "",
        "bounce_type": "",
        "website_check_status": "Not Checked",
        "website_check_date": "",
    }


def _disqualified_record(
    org_name: str, domain: str, source_url: str,
    city: str, state: str, reason: str
) -> dict:
    return {
        "org_name": org_name,
        "domain": domain,
        "source_url": source_url,
        "city": city,
        "state": state,
        "lead_score": "Disqualified",
        "primary_lane": "",
        "secondary_lane": "",
        "lane_reasoning": "",
        "profile": "",
        "venue_type": "",
        "estimated_size": "Unknown",
        "independent": "Unknown",
        "programming_evidence": "",
        "contact_name": "",
        "contact_title": "",
        "email": "",
        "email_source": "",
        "verification_status": "Not Started",
        "last_verified_date": "",
        "why_danni_fits": "",
        "evidence_source": "",
        "status": "Disqualified",
        "disqualification_reason": reason,
        "approval_notes": "",
        "approved_by": "",
        "discovered_date": "",
        "sent_date": "",
        "last_contact_date": "",
        "touch_count": 0,
        "response": "",
        "last_delivery_event": "",
        "bounce_type": "",
        "website_check_status": "Not Checked",
        "website_check_date": "",
    }
