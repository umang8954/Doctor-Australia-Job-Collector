"""Government portal scrapers - QLD SmartJobs, NT Jobs, VIC Careers."""

from __future__ import annotations

import config
from job_utils import JobRecord, passes_filters
from resume_matcher import match_label, score_resume_match
from scrapers.base import fetch_nt_search, fetch_smartjobs_search, fetch_with_playwright
from scrapers.block_detection import analyze_html, failure_reason_from_analysis
from scrapers.portal_parsers import merge_jobs, parse_jobs_nt, parse_smartjobs_results


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
    """SmartJobs QLD — jncustomsearch form with keyword searches."""
    cfg = config.PORTAL_CONFIG["smartjobs_qld"]
    all_parsed: list[list[JobRecord]] = []
    last_reason = ""

    for keyword in config.SMARTJOBS_SEARCH_KEYWORDS:
        html = fetch_smartjobs_search(keyword)
        analysis = analyze_html(html)
        if analysis.is_blocked or analysis.is_error_page:
            last_reason = failure_reason_from_analysis(analysis)
            continue
        jobs = parse_smartjobs_results(html, cfg["base_url"])
        if not jobs:
            last_reason = failure_reason_from_analysis(analysis, 0)
        all_parsed.append(jobs)

    merged = merge_jobs(all_parsed)
    if merged:
        return _score_jobs(merged)
    if last_reason:
        raise RuntimeError(last_reason or "parser_found_nothing: SmartJobs returned no listings")
    raise RuntimeError("no_jobs_matched: SmartJobs search returned no medical listings")


def scrape_jobs_nt() -> list[JobRecord]:
    """Jobs NT — Home/Search accordion panels across multiple keywords."""
    cfg = config.PORTAL_CONFIG["jobs_nt"]
    all_parsed: list[list[JobRecord]] = []
    last_reason = ""

    for keyword in config.JOBS_NT_SEARCH_KEYWORDS:
        html = fetch_nt_search(keyword)
        analysis = analyze_html(html)
        jobs = parse_jobs_nt(html, cfg["base_url"])
        if not jobs and analysis.is_no_results:
            last_reason = "no_jobs_matched: NT portal returned no results for query"
        elif not jobs:
            last_reason = failure_reason_from_analysis(analysis, 0)
        all_parsed.append(jobs)

    merged = merge_jobs(all_parsed)
    if merged:
        return _score_jobs(merged)
    raise RuntimeError(last_reason or "parser_found_nothing: NT parser found no job panels")


def scrape_careers_vic() -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG["careers_vic"]
    html = fetch_with_playwright(cfg["search_url"], label="careers_vic")
    from scrapers.base import parse_job_cards

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
