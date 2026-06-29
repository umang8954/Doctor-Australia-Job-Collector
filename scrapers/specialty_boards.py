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
    build_job,
    fetch_html,
    fetch_with_playwright,
    soup_from_html,
    text,
)


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
    cfg = config.PORTAL_CONFIG["ranzcog"]
    html = fetch_with_playwright(cfg["search_url"], label="ranzcog")
    jobs = []

    soup = soup_from_html(html)
    for row in soup.select("table tr, .job-listing, article, li"):
        link_el = row.find("a", href=True)
        if not link_el:
            continue
        title = text(link_el)
        if len(title) < 5:
            continue
        card_text = text(row)
        if not any(kw.lower() in card_text.lower() for kw in config.KEYWORDS):
            continue
        if not _is_au_job(card_text, title):
            continue
        job = build_job(
            title=title,
            link=link_el["href"],
            base_url=cfg["base_url"],
            portal_key="ranzcog",
            card_text=card_text,
            specialty="Obstetrics and Gynaecology",
        )
        if job:
            jobs.append(job)

    return _score_jobs(jobs)


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
