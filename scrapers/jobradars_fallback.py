"""JobRadars fallback when australia.jobradars.com is Cloudflare-blocked."""

from __future__ import annotations

import config
from job_utils import JobRecord, passes_filters
from resume_matcher import match_label, score_resume_match
from scrapers.base import fetch_html
from scrapers.portal_parsers import parse_nsw_health


def scrape_jobradars_nsw_fallback() -> list[JobRecord]:
    """
    When JobRadars returns 403/404/Cloudflare, pull registrar/medical listings
    from NSW Health jobs portal as an aggregator-style fallback.
    """
    cfg = config.PORTAL_CONFIG["jobradars"]
    queries = (
        "registrar medical",
        "obstetrics gynaecology registrar",
        "O&G registrar",
    )
    filtered: list[JobRecord] = []
    seen: set[str] = set()

    for q in queries:
        url = f"https://jobs.health.nsw.gov.au/jobs/search?q={q.replace(' ', '+')}"
        try:
            html = fetch_html(url, label="jobradars_fallback", timeout=30)
        except Exception:  # noqa: BLE001
            continue
        jobs = parse_nsw_health(html, "https://jobs.health.nsw.gov.au")
        for job in jobs[:15]:
            if job.apply_link in seen:
                continue
            seen.add(job.apply_link)
            job.platform = cfg.get("sheet", "JobRadars")
            job.extraction_method = "nsw_health_fallback"
            job.method_reliability_note = (
                "Fallback — NSW Health jobs search (JobRadars unavailable)"
            )
            if passes_filters(job):
                job.match_pct = score_resume_match(
                    job.title, job.description, job.specialty, job.location, job.state
                )
                job.match_label = match_label(job.match_pct)
                filtered.append(job)
    return filtered
