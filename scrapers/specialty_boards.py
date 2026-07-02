"""Specialty board scrapers - RANZCOG and RACP (Australia jobs only)."""

from __future__ import annotations

import re

import config
from job_utils import (
    JobRecord,
    contains_au_location,
    contains_non_au_location,
    detect_experience_level,
    detect_specialty,
    detect_state,
    passes_filters,
    safe_str,
)
from resume_matcher import match_label, score_resume_match
from scrapers.base import (
    absolute_url,
    fetch_html,
    fetch_html_with_status,
    fetch_with_playwright,
    get_runtime_environment,
    soup_from_html,
    text,
)
from scrapers.block_detection import analyze_html, failure_reason_from_analysis
from scrapers.portal_parsers import parse_ranzcog


def _score_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    filtered = []
    for job in jobs:
        if not passes_filters(job):
            continue
        job.match_pct = score_resume_match(
            job.title, job.description, job.specialty, job.location, job.state
        )
        job.match_label = match_label(job.match_pct)
        filtered.append(job)
    return filtered


def _is_au_job(card_text: str, title: str) -> bool:
    combined = f"{title} {card_text}"
    if contains_non_au_location(combined):
        return False
    return contains_au_location(combined) or bool(detect_state(combined))


def scrape_ranzcog() -> list[JobRecord]:
    """RANZCOG — stealth Playwright with static fallback and environment logging."""
    cfg = config.PORTAL_CONFIG["ranzcog"]
    env = get_runtime_environment()
    last_reason = ""

    try:
        html = fetch_with_playwright(
            cfg["search_url"],
            label="ranzcog",
            stealth=config.RANZCOG_USE_STEALTH,
            wait_until="networkidle",
        )
        analysis = analyze_html(html, status_code=200 if len(html) > 500 else 403)
        jobs = parse_ranzcog(html, cfg["base_url"])
        if jobs:
            return _score_jobs(jobs)
        last_reason = failure_reason_from_analysis(analysis, len(jobs))
    except Exception as exc:  # noqa: BLE001
        last_reason = f"playwright_{type(exc).__name__}: {str(exc)[:100]}"

    try:
        html, status = fetch_html_with_status(cfg["search_url"], label="ranzcog", raise_for_status=False)
        analysis = analyze_html(html, status_code=status)
        jobs = parse_ranzcog(html, cfg["base_url"])
        if jobs:
            return _score_jobs(jobs)
        if not last_reason:
            last_reason = failure_reason_from_analysis(analysis, len(jobs))
    except Exception as exc:  # noqa: BLE001
        last_reason = f"static_{type(exc).__name__}: {str(exc)[:100]}"

    from scrapers.ranzcog_rss import scrape_ranzcog_peninsula_fallback, scrape_ranzcog_rss_fallback

    rss_jobs = scrape_ranzcog_rss_fallback()
    if rss_jobs:
        return _score_jobs(rss_jobs)

    racp_jobs = scrape_ranzcog_peninsula_fallback()
    if racp_jobs:
        return _score_jobs(racp_jobs)

    raise RuntimeError(
        f"blocked: RANZCOG jobs board blocked from {env} — {last_reason or '403 Forbidden'}; all fallbacks empty"
    )


def scrape_racp() -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG["racp"]
    html = fetch_html(cfg["search_url"], label="racp")
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []

    for section in soup.select("table, .content, article, .vacancy, li"):
        links = section.find_all("a", href=True)
        for a in links:
            title = text(a)
            href = a.get("href", "")
            if len(title) < 8:
                continue
            if not any(
                kw.lower() in title.lower()
                for kw in config.KEYWORDS + ["physician", "medicine", "position"]
            ):
                continue
            card_text = text(section)
            if not _is_au_job(card_text, title):
                continue

            location_match = re.search(
                r"(Queensland|Victoria|Western Australia|Northern Territory|"
                r"New South Wales|South Australia|Tasmania|NSW|VIC|QLD|WA|NT|SA|TAS|ACT|Australia)",
                card_text,
                re.I,
            )
            state = detect_state(card_text, "")
            if not state and not location_match:
                continue

            combined = f"{title} {card_text}"
            job = JobRecord(
                title=title[:200],
                specialty=detect_specialty(combined),
                experience_level=detect_experience_level(combined),
                hospital=safe_str(section.find("strong")) or "RACP Member Hospital (AU)",
                location=location_match.group(0) if location_match else (state or "Australia"),
                state=state or "Australia",
                apply_link=absolute_url(cfg["base_url"], href),
                description=card_text[:2000],
                platform=cfg.get("sheet", "RACP"),
                layer="static",
            )
            jobs.append(job)

    seen = set()
    unique = []
    for job in jobs:
        key = job.apply_link
        if key not in seen:
            seen.add(key)
            unique.append(job)

    return _score_jobs(unique)


SPECIALTY_SCRAPERS = {
    "ranzcog": scrape_ranzcog,
    "racp": scrape_racp,
}
