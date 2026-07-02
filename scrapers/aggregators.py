"""Aggregator scrapers - Australia JobRadars and AU PageUp hospital sites only."""

from __future__ import annotations

import os
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
    parse_job_cards,
    soup_from_html,
    text,
)
from scrapers.block_detection import analyze_html, failure_reason_from_analysis
from scrapers.portal_parsers import parse_nsw_health, parse_pageup_sa, parse_qld_health


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
    """JobRadars — Playwright stealth primary; optional skip in CI."""
    if config.JOBRADARS_SKIP_IN_CI and (
        os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI")
    ):
        raise RuntimeError(
            f"skipped_ci: JobRadars skipped in {get_runtime_environment()} (403-prone datacenter IP)"
        )

    cfg = config.PORTAL_CONFIG["jobradars"]
    env = get_runtime_environment()
    last_reason = ""

    try:
        html = fetch_with_playwright(
            cfg["search_url"],
            label="jobradars",
            stealth=True,
            wait_until="networkidle",
            referer="https://www.google.com.au/",
        )
        analysis = analyze_html(html)
        jobs = parse_job_cards(
            html,
            cfg["base_url"],
            "jobradars",
            selectors=[".job-card", ".job-listing", "article", ".result", "a[href*='/job']"],
        )
        au_jobs = _filter_au_jobs(jobs)
        if au_jobs:
            return _score_jobs(au_jobs)
        last_reason = failure_reason_from_analysis(analysis, len(au_jobs))
    except Exception as exc:  # noqa: BLE001
        last_reason = f"playwright_{type(exc).__name__}: {str(exc)[:100]}"

    try:
        html, status = fetch_html_with_status(cfg["search_url"], label="jobradars", raise_for_status=False)
        analysis = analyze_html(html, status_code=status)
        if analysis.is_blocked:
            raise RuntimeError(f"blocked: JobRadars 403 from {env}")
        jobs = parse_job_cards(
            html,
            cfg["base_url"],
            "jobradars",
            selectors=[".job-card", ".job-listing", "article", ".result"],
        )
        au_jobs = _filter_au_jobs(jobs)
        if au_jobs:
            return _score_jobs(au_jobs)
        last_reason = failure_reason_from_analysis(analysis, len(au_jobs))
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001
        last_reason = f"static_{type(exc).__name__}: {str(exc)[:100]}"

    raise RuntimeError(f"blocked: JobRadars forbidden from {env} — {last_reason}")


def _filter_au_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
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
    return au_jobs


def _fetch_pageup_site(entry: dict) -> tuple[list[JobRecord], str]:
    """Fetch one PageUp site; return jobs and status note."""
    url = entry["url"]
    method = entry.get("method", "static")
    parser = entry.get("parser", "pageup_sa")
    hospital = entry.get("hospital", "AU Health Service")
    state = entry.get("state", "Australia")
    base = "/".join(url.split("/")[:3])
    label = f"pageup_{state.lower()}"

    try:
        if method == "playwright":
            html = fetch_with_playwright(url, label=label, stealth=True, wait_until="networkidle")
            status = 200
        else:
            html, status = fetch_html_with_status(url, label=label, raise_for_status=False)
    except Exception as exc:  # noqa: BLE001
        return [], f"{state}_error:{type(exc).__name__}:{str(exc)[:80]}"

    analysis = analyze_html(html, status_code=status)
    if analysis.is_blocked:
        return [], f"{state}_blocked:HTTP {status}"
    if analysis.is_error_page:
        return [], f"{state}_error_page:{analysis.reason[:60]}"

    if parser == "nsw_health":
        jobs = parse_nsw_health(html, base)
    elif parser == "qld_health":
        jobs = parse_qld_health(html, base)
    else:
        jobs = parse_pageup_sa(html, base, hospital=hospital)

    for job in jobs:
        if not job.hospital:
            job.hospital = hospital
        if state and job.state in ("", "Australia"):
            job.state = state

    if jobs:
        return jobs, f"{state}_ok:{len(jobs)}"
    if analysis.is_no_results:
        return [], f"{state}_no_results:0 jobs for query"
    return [], f"{state}_parser_empty:0 parsed (HTTP {status})"


def scrape_pageup() -> list[JobRecord]:
    """PageUp multi-site — NSW Health, QLD Health, SA Health with per-URL logging."""
    all_jobs: list[JobRecord] = []
    site_notes: list[str] = []
    seen: set[str] = set()

    for entry in config.PAGEUP_AU_SEARCH_URLS:
        jobs, note = _fetch_pageup_site(entry)
        site_notes.append(note)
        for job in jobs:
            key = job.apply_link or job.title
            if key in seen:
                continue
            seen.add(key)
            all_jobs.append(job)

    if all_jobs:
        return _score_jobs(all_jobs)

    raise RuntimeError("pageup_all_failed: " + " | ".join(site_notes))


def scrape_jobradars_entry() -> list[JobRecord]:
    """JobRadars with NSW Health fallback when Cloudflare blocks the aggregator."""
    try:
        return scrape_jobradars()
    except RuntimeError:
        from scrapers.jobradars_fallback import scrape_jobradars_nsw_fallback

        jobs = scrape_jobradars_nsw_fallback()
        if jobs:
            return jobs
        raise


AGGREGATOR_SCRAPERS = {
    "jobradars": scrape_jobradars_entry,
    "pageup": scrape_pageup,
}
