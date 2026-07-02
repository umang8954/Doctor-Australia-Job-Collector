"""RANZCOG RSS fallback — parse job-related items from main site feed when jobs board is blocked."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import config
from job_utils import JobRecord, detect_experience_level, detect_specialty, passes_filters
from resume_matcher import match_label, score_resume_match
from scrapers.base import fetch_html


def scrape_ranzcog_rss_fallback() -> list[JobRecord]:
    """Parse ranzcog.edu.au RSS for vacancy/job announcements."""
    rss_urls = [
        "https://www.ranzcog.edu.au/rss",
        "https://ranzcog.edu.au/feed/",
    ]
    jobs: list[JobRecord] = []
    seen: set[str] = set()
    cfg = config.PORTAL_CONFIG["ranzcog"]

    for rss_url in rss_urls:
        try:
            xml_text = fetch_html(rss_url, label="ranzcog_rss", timeout=20)
            root = ET.fromstring(xml_text)
        except Exception:  # noqa: BLE001
            continue

        for item in root.iter("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            if title_el is None or link_el is None:
                continue
            title = (title_el.text or "").strip()
            link = (link_el.text or "").strip()
            desc = (desc_el.text or "").strip() if desc_el is not None else ""
            combined = f"{title} {desc}"
            if not link or link in seen:
                continue
            if not re.search(
                r"vacanc|position|job|registrar|fellow|consultant|employment",
                combined,
                re.I,
            ):
                continue
            if not any(kw.lower() in combined.lower() for kw in config.KEYWORDS):
                continue
            seen.add(link)
            job = JobRecord(
                title=title[:200],
                specialty=detect_specialty(combined) or "Obstetrics & Gynaecology",
                experience_level=detect_experience_level(combined),
                hospital=cfg.get("hospital", "RANZCOG"),
                location="Australia",
                state="Australia",
                apply_link=link,
                description=desc[:2000],
                platform=cfg.get("sheet", "RANZCOG"),
                layer="rss",
                extraction_method="ranzcog_rss",
                method_reliability_note="Fallback — RANZCOG main site RSS (jobs board blocked)",
            )
            if passes_filters(job):
                job.match_pct = score_resume_match(
                    job.title, job.description, job.specialty, job.location, job.state
                )
                job.match_label = match_label(job.match_pct)
                jobs.append(job)
    return jobs[:20]


def scrape_ranzcog_peninsula_fallback() -> list[JobRecord]:
    """O&G registrar listings from Peninsula Health when RANZCOG board is blocked."""
    from scrapers.base import fetch_with_playwright
    from scrapers.portal_parsers import parse_peninsula_health

    cfg = config.PORTAL_CONFIG["ranzcog"]
    ph_cfg = config.PORTAL_CONFIG["peninsula_health"]
    html = fetch_with_playwright(ph_cfg["search_url"], label="peninsula_health")
    jobs = parse_peninsula_health(html, ph_cfg["base_url"])
    og_terms = ("obstet", "gynaec", "gynec", "o&g", "ranzcog", "maternity", "women")

    og_jobs: list[JobRecord] = []
    for job in jobs:
        blob = f"{job.title} {job.specialty} {job.description}".lower()
        if not any(term in blob for term in og_terms):
            continue
        job.platform = cfg.get("sheet", "RANZCOG")
        job.hospital = job.hospital or "Peninsula Health (O&G)"
        job.extraction_method = "peninsula_og_fallback"
        job.method_reliability_note = (
            "Fallback — O&G listings from Peninsula Health (RANZCOG board blocked)"
        )
        og_jobs.append(job)
    return og_jobs[:15]
