"""Hospital career page scrapers - static HTML and Playwright."""

from __future__ import annotations

import config
from job_utils import JobRecord, passes_filters
from resume_matcher import match_label, score_resume_match
from scrapers.base import (
    fetch_html,
    fetch_with_playwright,
    parse_job_cards,
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


def _scrape_static(portal_key: str) -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG[portal_key]
    html = fetch_html(cfg["search_url"], label=portal_key)
    jobs = parse_job_cards(
        html,
        cfg["base_url"],
        portal_key,
        selectors=[
            ".job-result",
            ".job-listing",
            ".search-result",
            "article.job",
            "li.job",
            "tr.job",
        ],
    )
    return _score_jobs(jobs)


def _scrape_playwright(portal_key: str) -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG[portal_key]
    html = fetch_with_playwright(cfg["search_url"], label=portal_key)
    jobs = parse_job_cards(
        html,
        cfg["base_url"],
        portal_key,
        selectors=[
            ".job-result",
            ".job-listing",
            ".search-result",
            "article",
            "[data-job-id]",
        ],
    )
    return _score_jobs(jobs)


def scrape_monash_health() -> list[JobRecord]:
    return _scrape_playwright("monash_health")


def scrape_western_health() -> list[JobRecord]:
    return _scrape_static("western_health")


def scrape_wa_health() -> list[JobRecord]:
    return _scrape_playwright("wa_health")


def scrape_peninsula_health() -> list[JobRecord]:
    return _scrape_static("peninsula_health")


def scrape_the_womens() -> list[JobRecord]:
    return _scrape_static("the_womens")


def scrape_grampians_health() -> list[JobRecord]:
    return _scrape_static("grampians_health")


def scrape_eastern_health() -> list[JobRecord]:
    return _scrape_static("eastern_health")


def scrape_rch() -> list[JobRecord]:
    return _scrape_static("rch")


HOSPITAL_SCRAPERS = {
    "monash_health": scrape_monash_health,
    "western_health": scrape_western_health,
    "wa_health": scrape_wa_health,
    "peninsula_health": scrape_peninsula_health,
    "the_womens": scrape_the_womens,
    "grampians_health": scrape_grampians_health,
    "eastern_health": scrape_eastern_health,
    "rch": scrape_rch,
}
