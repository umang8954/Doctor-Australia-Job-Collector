"""Aggregator scrapers - Australia JobRadars and AU PageUp hospital sites only."""

from __future__ import annotations

import re

import config
from job_utils import (
    JobRecord,
    contains_au_location,
    contains_non_au_location,
    detect_specialty,
    detect_state,
    passes_filters,
    safe_str,
)
from resume_matcher import match_label, score_resume_match
from scrapers.base import absolute_url, fetch_html, parse_job_cards, soup_from_html, text


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


def scrape_jobradars() -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG["jobradars"]
    html = fetch_html(cfg["search_url"], label="jobradars")
    jobs = parse_job_cards(
        html,
        cfg["base_url"],
        "jobradars",
        selectors=[".job-card", ".job-listing", "article", ".result"],
    )
    au_jobs = []
    for job in jobs:
        if not job.hospital:
            job.hospital = safe_str(job.description.split("|")[0][:80]) or "Unknown"
        job.state = detect_state(job.location + " " + job.description, "Australia")
        job.location = job.location or job.state or "Australia"
        combined = job.combined_text()
        if contains_non_au_location(combined):
            continue
        if not contains_au_location(combined):
            continue
        au_jobs.append(job)
    return _score_jobs(au_jobs)


def scrape_pageup() -> list[JobRecord]:
    """PageUp: AU hospital career sites only (NSW, QLD, SA health)."""
    cfg = config.PORTAL_CONFIG["pageup"]
    jobs: list[JobRecord] = []
    seen: set[str] = set()
    apply_pattern = re.compile(r"/apply/\d+/aw/", re.I)

    for url in config.PAGEUP_AU_SEARCH_URLS:
        try:
            html = fetch_html(url, label="pageup")
        except Exception:  # noqa: BLE001
            continue

        soup = soup_from_html(html)
        base = "/".join(url.split("/")[:3])

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not apply_pattern.search(href):
                continue
            title = text(a)
            if len(title) < 5:
                parent = a.find_parent(["li", "div", "tr", "article"])
                title = text(parent)[:200] if parent else ""
            if len(title) < 5:
                continue

            link = absolute_url(base, href)
            if link in seen:
                continue
            seen.add(link)

            parent = a.find_parent(["li", "div", "tr", "article"])
            card_text = text(parent) if parent else title

            if not any(kw.lower() in card_text.lower() for kw in config.KEYWORDS):
                continue
            if contains_non_au_location(card_text):
                continue

            state = detect_state(card_text, "")
            if not state and not contains_au_location(card_text):
                continue

            hospital = ""
            for part in url.split("/"):
                if "careers" in part or "health" in part:
                    hospital = part.replace("careers.", "").replace(".", " ").title()
                    break

            job = JobRecord(
                title=title[:200],
                specialty=detect_specialty(card_text),
                hospital=hospital or "AU Health Service",
                location=state or "Australia",
                state=state or "Australia",
                apply_link=link,
                description=card_text[:2000],
                platform=cfg.get("sheet", "PageUp"),
                layer="pageup",
            )
            jobs.append(job)

    return _score_jobs(jobs)


AGGREGATOR_SCRAPERS = {
    "jobradars": scrape_jobradars,
    "pageup": scrape_pageup,
}
