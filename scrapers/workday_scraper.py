"""Workday API scraper for Mercy Health careers."""

from __future__ import annotations

import config
from job_utils import JobRecord, detect_experience_level, detect_specialty, passes_filters, safe_str
from resume_matcher import match_label, score_resume_match
from scrapers.base import absolute_url, fetch_json_post, new_session


def scrape_mercy_workday() -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG["mercy_workday"]
    tenant = cfg["tenant"]
    site = cfg["site"]
    base_url = cfg["base_url"]
    api_url = f"{base_url}/wday/cxs/{tenant}/{site}/jobs"

    session = new_session(referer=base_url)
    jobs: list[JobRecord] = []

    for keyword in config.KEYWORDS[:4]:
        payload = {
            "limit": 20,
            "offset": 0,
            "searchText": keyword,
            "appliedFacets": {},
        }
        try:
            data = fetch_json_post(api_url, payload, session=session, label="mercy_workday")
        except Exception:  # noqa: BLE001
            continue

        for item in data.get("jobPostings", []):
            title = safe_str(item.get("title"))
            if not title:
                continue
            ext_path = safe_str(item.get("externalPath", ""))
            link = absolute_url(base_url, ext_path) if ext_path else base_url
            location = safe_str(item.get("locationsText", ""))
            posted = safe_str(item.get("postedOn", ""))
            combined = f"{title} {location} {posted}"

            job = JobRecord(
                title=title,
                specialty=detect_specialty(combined),
                experience_level=detect_experience_level(combined),
                hospital=cfg.get("hospital", "Mercy Health"),
                location=location,
                state=cfg.get("state", "VIC"),
                posted_date=None,
                apply_link=link,
                description=combined,
                platform=cfg.get("sheet", "Mercy_Workday"),
                layer="workday",
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
        key = job.apply_link
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique
