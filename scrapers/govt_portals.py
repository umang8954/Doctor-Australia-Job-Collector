"""Government portal scrapers - QLD SmartJobs, NT Jobs, VIC Careers."""

from __future__ import annotations

import config
from job_utils import JobRecord, passes_filters
from resume_matcher import match_label, score_resume_match
from scrapers.base import build_job, fetch_with_playwright, parse_job_cards


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


def scrape_smartjobs_qld() -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG["smartjobs_qld"]
    html = fetch_with_playwright(cfg["search_url"], label="smartjobs_qld")
    jobs = parse_job_cards(
        html,
        cfg["base_url"],
        "smartjobs_qld",
        selectors=[".job-result", ".search-result", "article", ".job-listing-item"],
    )
    return _score_jobs(jobs)


def scrape_jobs_nt() -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG["jobs_nt"]
    html = fetch_with_playwright(cfg["search_url"], label="jobs_nt")
    jobs = parse_job_cards(
        html,
        cfg["base_url"],
        "jobs_nt",
        selectors=[".job-item", ".search-results li", "article"],
    )
    return _score_jobs(jobs)


def scrape_careers_vic() -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG["careers_vic"]
    html = fetch_with_playwright(cfg["search_url"], label="careers_vic")
    jobs = parse_job_cards(
        html,
        cfg["base_url"],
        "careers_vic",
        selectors=[".job-result", ".search-result-item", "article"],
    )
    return _score_jobs(jobs)


GOVT_SCRAPERS = {
    "smartjobs_qld": scrape_smartjobs_qld,
    "jobs_nt": scrape_jobs_nt,
    "careers_vic": scrape_careers_vic,
}
