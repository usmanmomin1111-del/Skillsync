"""Public AICTE National Internship Portal catalogue integration.

Only data that is exposed by the public AICTE catalogue is used here.  We do
not submit applications, access authenticated pages, or invent detail links.
Every returned card is confirmed through the public single-listing endpoint
before it is shown.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlparse

import requests


PORTAL_ORIGIN = "https://internship.aicte-india.org"
PUBLIC_CATALOGUE_URL = f"{PORTAL_ORIGIN}/api/v1/catalogue/internships"
PUBLIC_BROWSE_URL = f"{PORTAL_ORIGIN}/internships"
_CACHE_TTL = timedelta(minutes=10)
_cache: dict[str, tuple[datetime, list[dict[str, Any]]]] = {}

# These are search terms, not replacements for listing data.  The title,
# organization, stipend, dates, skills, and description always come from AICTE.
DOMAIN_QUERIES = {
    "Web Development": "Web Development",
    "AI / Machine Learning": "Artificial Intelligence",
    "Data Science": "Data Science",
    "Software Engineering": "Software Engineering",
    "Digital Marketing": "Digital Marketing",
    "Cybersecurity": "Cyber Security",
    "Cloud Computing": "Cloud Computing",
    "Internet of Things (IoT)": "Internet of Things",
    "UI/UX Design": "UI UX Design",
    "Android App Development": "Android App Development",
    "Blockchain Technology": "Blockchain",
    "Computer Networking": "Networking",
    "Embedded Systems": "Embedded Systems",
    "VLSI and Semiconductor Design": "VLSI Design",
    "Robotics and Automation": "Robotics",
}


def _public_details_url(internship_id: str) -> str | None:
    """Build a safe official detail URL from an AICTE catalogue identifier."""
    if not internship_id or not isinstance(internship_id, str):
        return None
    url = f"{PORTAL_ORIGIN}/internships/{quote(internship_id, safe='')}"
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "internship.aicte-india.org":
        return None
    return url


def _format_deadline(value: Any) -> str:
    if not value:
        return "Not specified"
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return str(value)


def _format_location(item: dict[str, Any]) -> str:
    location = str(item.get("location") or "Not specified")
    mode = str(item.get("mode") or "").strip()
    return f"{location} ({mode})" if mode else location


def _to_card(item: dict[str, Any]) -> dict[str, Any] | None:
    """Map a verified public record to the UI's existing card structure."""
    internship_id = item.get("id")
    details_url = _public_details_url(internship_id)
    if not details_url or not item.get("isOpen", False):
        return None

    skills = [str(skill).strip() for skill in item.get("skills", []) if str(skill).strip()]
    description = " ".join(str(item.get("description") or "").split())
    if len(description) > 330:
        description = f"{description[:327].rstrip()}..."

    openings = item.get("openings")
    openings_display = f"{openings} openings" if openings not in (None, "") else "Openings not specified"

    return {
        "id": str(internship_id),
        "title": str(item.get("title") or "Untitled internship"),
        "company": str(item.get("organization") or "Not specified"),
        "portal_type": "AICTE National Internship Portal",
        # `portal_url` is kept for existing form compatibility, but is never
        # the portal home page: it is this specific listing's official page.
        "portal_url": details_url,
        "details_url": details_url,
        "application_url": None,
        "application_login_required": True,
        "location": _format_location(item),
        "stipend": str(item.get("stipendDisplay") or "Not specified"),
        "duration": str(item.get("duration") or "Not specified"),
        "deadline": _format_deadline(item.get("deadline")),
        "openings": openings_display,
        "skills_required": skills,
        "description": description or "See the official AICTE details page for the full description.",
        "verified": bool(item.get("verified")),
        "source_name": "AICTE National Internship Portal",
    }


def _get_verified_detail(internship_id: str) -> dict[str, Any] | None:
    """Confirm that an exact public listing exists before its URL is displayed."""
    try:
        response = requests.get(
            f"{PUBLIC_CATALOGUE_URL}/{quote(internship_id, safe='')}",
            headers={"Accept": "application/json", "User-Agent": "SkillSync/1.0"},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        item = payload.get("item", {}) if isinstance(payload, dict) else {}
        if item.get("id") != internship_id:
            return None
        return item
    except (requests.RequestException, ValueError):
        return None


def get_recommendations(domain: str, limit: int = 6) -> list[dict[str, Any]]:
    """Return live, public, open AICTE listings for one SkillSync domain.

    The catalogue request discovers candidates.  Each candidate is then read
    through AICTE's public individual-listing endpoint, which prevents stale or
    fabricated detail links from reaching the UI.  A short cache keeps resume
    analysis responsive and respectful of the public service.
    """
    query = DOMAIN_QUERIES.get(domain, domain)
    now = datetime.now(timezone.utc)
    cached = _cache.get(query)
    if cached and now - cached[0] < _CACHE_TTL:
        return [dict(card) for card in cached[1][:limit]]

    try:
        response = requests.get(
            PUBLIC_CATALOGUE_URL,
            params={"q": query, "page": 1, "pageSize": max(limit * 2, 10), "sort": "best"},
            headers={"Accept": "application/json", "User-Agent": "SkillSync/1.0"},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        candidates = payload.get("items", []) if isinstance(payload, dict) else []
    except (requests.RequestException, ValueError):
        return []

    # Detail records are independent HTTP requests.  Verify a small batch in
    # parallel (rather than waiting for each request one by one) while keeping
    # the catalogue result order.  We still show only individually verified,
    # open AICTE listings.
    candidate_ids: list[str] = []
    seen_ids: set[str] = set()
    for candidate in candidates:
        internship_id = candidate.get("id") if isinstance(candidate, dict) else None
        internship_id = str(internship_id) if internship_id else ""
        if not internship_id or internship_id in seen_ids:
            continue
        seen_ids.add(internship_id)
        candidate_ids.append(internship_id)
        # Use extra candidates in case a listing has just closed or been
        # removed between the catalogue and detail requests.
        if len(candidate_ids) >= max(limit * 2, 10):
            break

    def verified_cards(ids: list[str]) -> list[dict[str, Any]]:
        """Verify one small ordered batch without delaying successful cards."""
        if not ids:
            return []
        worker_count = min(4, len(ids))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            # executor.map preserves the public catalogue order.
            return [
                card
                for item in executor.map(_get_verified_detail, ids)
                if (card := _to_card(item or {})) is not None
            ]

    # Most of the first `limit` catalogue entries are valid.  Check just those
    # first, then use the remaining candidates only when a listing closed in
    # the meantime.  This avoids making the page wait for unnecessary requests.
    cards = verified_cards(candidate_ids[:limit])
    if len(cards) < limit:
        cards.extend(verified_cards(candidate_ids[limit:]))
    cards = cards[:limit]

    _cache[query] = (now, cards)
    return [dict(card) for card in cards]
