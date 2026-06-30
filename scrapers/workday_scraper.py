"""Mercy Health careers — Mercury platform (primary) with Workday API fallback."""

from __future__ import annotations

import re

import config
from job_utils import JobRecord, detect_experience_level, detect_specialty, passes_filters, safe_str
from resume_matcher import match_label, score_resume_match
from scrapers.base import absolute_url, fetch_html, fetch_json_post, new_session, soup_from_html, text


def _scrape_mercy_mercury() -> list[JobRecord]:
    """Mercy Health Australia uses Mercury, not the aged-care Workday tenant."""
    cfg = config.PORTAL_CONFIG["mercy_workday"]
    base_url = cfg["base_url"]
    search_url = cfg["search_url"]
    html = fetch_html(search_url, label="mercy_mercury", timeout=45)
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = text(a)
        if len(title) < 8 or len(title) > 200:
            continue
        if not any(kw.lower() in title.lower() for kw in config.KEYWORDS):
            parent = a.find_parent(["tr", "li", "div", "td"])
            card = text(parent) if parent else title
            if not any(kw.lower() in card.lower() for kw in config.KEYWORDS):
                continue
        else:
            card = title

        if "vacancy" not in href.lower() and "job" not in href.lower() and "position" not in href.lower():
            if not re.search(r"vacancy|position|job", href, re.I):
                continue

        link = absolute_url(base_url, href)
        if link in seen:
            continue
        seen.add(link)

        combined = f"{title} {card}"
        job = JobRecord(
            title=title[:200],
            specialty=detect_specialty(combined),
            experience_level=detect_experience_level(combined),
            hospital=cfg.get("hospital", "Mercy Health"),
            location="Victoria",
            state=cfg.get("state", "VIC"),
            apply_link=link,
            description=card[:2000],
            platform=cfg.get("sheet", "Mercy_Workday"),
            layer="mercury",
            extraction_method="mercury_html",
            method_reliability_note="Primary — Mercy Mercury careers portal",
        )
        if passes_filters(job):
            job.match_pct = score_resume_match(
                job.title, job.description, job.specialty, job.location, job.state
            )
            job.match_label = match_label(job.match_pct)
            jobs.append(job)

    return jobs[:50]


def _scrape_mercy_workday_api() -> list[JobRecord]:
    """Legacy Workday aged-care tenant — kept as fallback only."""
    cfg = config.PORTAL_CONFIG["mercy_workday"]
    base_url = cfg.get("workday_fallback_url", "")
    if not base_url:
        return []
    tenant = cfg.get("tenant", "mercyagedcare")
    site = cfg.get("site", "MercyCare")
    api_url = f"{base_url}/wday/cxs/{tenant}/{site}/jobs"

    session = new_session(referer=base_url)
    jobs: list[JobRecord] = []

    for keyword in config.KEYWORDS[:4]:
        payload = {"limit": 20, "offset": 0, "searchText": keyword, "appliedFacets": {}}
        try:
            data = fetch_json_post(api_url, payload, session=session, label="mercy_workday")
        except Exception:  # noqa: BLE001
            continue

        for item in data.get("jobPostings", []):
            title = safe_str(item.get("title"))
            if not title:
                continue
            ext_path = safe_str(item.get("externalPath", ""))
            link = absolute_url(base_url, ext_path) if ext_path else base_url
            location = safe_str(item.get("locationsText", ""))
            combined = f"{title} {location}"

            job = JobRecord(
                title=title,
                specialty=detect_specialty(combined),
                experience_level=detect_experience_level(combined),
                hospital=cfg.get("hospital", "Mercy Health"),
                location=location,
                state=cfg.get("state", "VIC"),
                apply_link=link,
                description=combined,
                platform=cfg.get("sheet", "Mercy_Workday"),
                layer="workday",
                extraction_method="workday_api",
                method_reliability_note="Fallback — Workday API (aged-care tenant)",
            )
            if passes_filters(job):
                job.match_pct = score_resume_match(
                    job.title, job.description, job.specialty, job.location, job.state
                )
                job.match_label = match_label(job.match_pct)
                jobs.append(job)

    seen = set()
    unique: list[JobRecord] = []
    for job in jobs:
        if job.apply_link not in seen:
            seen.add(job.apply_link)
            unique.append(job)
    return unique


def scrape_mercy_workday() -> list[JobRecord]:
    """Try Mercury first, then Workday API fallback."""
    jobs = _scrape_mercy_mercury()
    if jobs:
        return jobs
    return _scrape_mercy_workday_api()
