"""Mercy Health careers — Mercury platform (primary) with Workday fallback."""

from __future__ import annotations

import logging
import re
import time

import requests

import config
from job_utils import JobRecord, detect_experience_level, detect_specialty, passes_filters, safe_str
from resume_matcher import match_label, score_resume_match
from scrapers.base import (
    absolute_url,
    fetch_html,
    fetch_json_post,
    fetch_mercy_workday_search,
    new_session,
    soup_from_html,
    text,
)
from scrapers.portal_parsers import parse_mercy_workday_html

logger = logging.getLogger(__name__)


def _scrape_mercy_mercury() -> tuple[list[JobRecord], str]:
    """Mercy Health Mercury ASP.NET portal with retries."""
    cfg = config.PORTAL_CONFIG["mercy_workday"]
    base_url = cfg["base_url"]
    timeout = cfg.get("mercury_timeout", 60)
    last_error = ""

    for keyword in ("registrar", "medical officer", "doctor"):
        search_url = f"{base_url.rstrip('/')}/SearchResults.aspx?Keywords={keyword.replace(' ', '+')}"
        for attempt in range(2):
            try:
                html = fetch_html(search_url, label="mercy_mercury", timeout=timeout)
                jobs = _parse_mercury_html(html, base_url, cfg)
                if jobs:
                    return jobs, ""
            except requests.RequestException as exc:
                last_error = f"mercury_http_{type(exc).__name__}: {str(exc)[:120]}"
                logger.warning("Mercy Mercury attempt %s failed: %s", attempt + 1, last_error)
                time.sleep(config.RETRY_DELAY_SECONDS)
    return [], last_error or "mercury_timeout: Mercury portal unreachable"


def _parse_mercury_html(html: str, base_url: str, cfg: dict) -> list[JobRecord]:
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = text(a)
        if len(title) < 8 or len(title) > 200:
            continue
        if not re.search(r"vacancy|position|job|searchresults", href, re.I):
            continue
        card = text(a.find_parent(["tr", "li", "div", "td"]) or a)
        if not any(kw.lower() in f"{title} {card}".lower() for kw in config.KEYWORDS):
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


def _scrape_mercy_workday_playwright() -> tuple[list[JobRecord], str]:
    """Mercy Health Workday careers via Playwright search."""
    cfg = config.PORTAL_CONFIG["mercy_workday"]
    base = cfg.get("workday_fallback_url", "")
    if not base:
        return [], "workday_disabled: no Workday URL configured"

    try:
        html = fetch_mercy_workday_search("registrar")
        jobs = parse_mercy_workday_html(html, base)
        if jobs:
            for job in jobs:
                job.extraction_method = "workday_playwright"
                job.method_reliability_note = "Fallback — Mercy Workday Playwright"
            return jobs, ""
        return [], "workday_playwright_empty: page loaded but no job titles found"
    except Exception as exc:  # noqa: BLE001
        return [], f"workday_playwright_{type(exc).__name__}: {str(exc)[:120]}"


def _scrape_mercy_workday_api() -> tuple[list[JobRecord], str]:
    """Workday CXS API — mercyagedcare External tenant (linked from mercyhealth.com.au)."""
    cfg = config.PORTAL_CONFIG["mercy_workday"]
    base_url = cfg.get("workday_fallback_url", "")
    if not base_url:
        return [], "workday_api_disabled"

    tenant = cfg.get("tenant", "mercyagedcare")
    site = cfg.get("site", "External")
    api_url = f"{base_url}/wday/cxs/{tenant}/{site}/jobs"

    session = new_session(referer=f"{base_url}/en-US/{site}")
    try:
        session.get(f"{base_url}/en-US/{site}", timeout=30)
    except requests.RequestException as exc:
        return [], f"workday_warmup_{type(exc).__name__}: {str(exc)[:80]}"

    jobs: list[JobRecord] = []
    last_error = ""

    for keyword in ("registrar", "medical officer", "doctor", "physician"):
        payload = {"limit": 20, "offset": 0, "searchText": keyword, "appliedFacets": {}}
        try:
            data = fetch_json_post(api_url, payload, session=session, label="mercy_workday")
        except requests.HTTPError as exc:
            last_error = f"workday_api_HTTP{exc.response.status_code if exc.response else '?'}: {str(exc)[:80]}"
            continue
        except Exception as exc:  # noqa: BLE001
            last_error = f"workday_api_{type(exc).__name__}: {str(exc)[:80]}"
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
                method_reliability_note="Fallback — Mercy Workday API",
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
    if unique:
        return unique, ""
    return [], last_error or "workday_api_empty: API returned no job postings"


def scrape_mercy_workday() -> list[JobRecord]:
    """Try Workday API first (reliable), then Mercury, then Workday Playwright."""
    jobs, wd_api_err = _scrape_mercy_workday_api()
    if jobs:
        return jobs

    jobs, mercury_err = _scrape_mercy_mercury()
    if jobs:
        return jobs

    jobs, wd_pw_err = _scrape_mercy_workday_playwright()
    if jobs:
        return jobs

    raise RuntimeError(
        f"mercy_all_failed: workday_api=[{wd_api_err}] mercury=[{mercury_err}] workday_pw=[{wd_pw_err}]"
    )
