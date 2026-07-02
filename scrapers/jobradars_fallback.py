"""JobRadars fallback when australia.jobradars.com is Cloudflare-blocked."""

from __future__ import annotations

import config
from job_utils import JobRecord, passes_filters
from resume_matcher import match_label, score_resume_match
from scrapers.base import fetch_html
from scrapers.portal_parsers import parse_nsw_health


def scrape_jobradars_nsw_fallback() -> list[JobRecord]:
    """
    When JobRadars returns 403/Cloudflare, pull registrar/medical listings
    from NSW Health jobs portal as an aggregator-style fallback.
    """
    cfg = config.PORTAL_CONFIG["jobradars"]
    url = "https://jobs.health.nsw.gov.au/jobs/search?q=registrar+medical"
    html = fetch_html(url, label="jobradars_fallback", timeout=30)
    jobs = parse_nsw_health(html, "https://jobs.health.nsw.gov.au")

    filtered: list[JobRecord] = []
    for job in jobs[:15]:
        job.platform = cfg.get("sheet", "JobRadars")
        job.extraction_method = "nsw_health_fallback"
        job.method_reliability_note = (
            "Fallback — NSW Health jobs search (JobRadars Cloudflare-blocked)"
        )
        if passes_filters(job):
            job.match_pct = score_resume_match(
                job.title, job.description, job.specialty, job.location, job.state
            )
            job.match_label = match_label(job.match_pct)
            filtered.append(job)
    return filtered
