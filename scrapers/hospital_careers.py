"""Hospital career page scrapers - static HTML and Playwright."""

from __future__ import annotations

import config
from job_utils import JobRecord, passes_filters
from resume_matcher import match_label, score_resume_match
from scrapers.base import fetch_html, fetch_with_playwright
from scrapers.block_detection import analyze_html, failure_reason_from_analysis
from scrapers.portal_parsers import parse_peninsula_health


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
    from scrapers.base import parse_job_cards

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
    from scrapers.base import parse_job_cards

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


def scrape_peninsula_health() -> list[JobRecord]:
    """Peninsula Health — Playwright + portal-specific parser with zero-job retry."""
    cfg = config.PORTAL_CONFIG["peninsula_health"]
    last_reason = ""

    for attempt in range(2):
        html = fetch_with_playwright(cfg["search_url"], label="peninsula_health")
        analysis = analyze_html(html)
        jobs = parse_peninsula_health(html, cfg["base_url"])
        last_reason = failure_reason_from_analysis(analysis, len(jobs))
        if jobs:
            if attempt == 1:
                for job in jobs:
                    job.notes = "Recovered on retry after initial 0-job run"
            return _score_jobs(jobs)

    if last_reason:
        raise RuntimeError(last_reason)
    return []


def scrape_monash_health() -> list[JobRecord]:
    return _scrape_playwright("monash_health")


def scrape_western_health() -> list[JobRecord]:
    return _scrape_static("western_health")


def scrape_wa_health() -> list[JobRecord]:
    return _scrape_playwright("wa_health")


def scrape_the_womens() -> list[JobRecord]:
    return _scrape_static("the_womens")


def scrape_grampians_health() -> list[JobRecord]:
    return _scrape_static("grampians_health")


def scrape_eastern_health() -> list[JobRecord]:
    return _scrape_static("eastern_health")


def scrape_rch() -> list[JobRecord]:
    return _scrape_static("rch")


def scrape_gv_health() -> list[JobRecord]:
    return _scrape_static("gv_health")


def scrape_awh() -> list[JobRecord]:
    return _scrape_static("awh")


def scrape_act_health() -> list[JobRecord]:
    """ACT Health — Taleo ATS. The search page renders results client-side and
    ignores URL query params, so we fill the KEYWORD field and click search
    via Playwright (see fetch_taleo_search) rather than loading a static URL.
    """
    cfg = config.PORTAL_CONFIG["act_health"]
    from scrapers.base import fetch_taleo_search, soup_from_html, text, absolute_url, build_job
    from scrapers.portal_parsers import _matches_keywords
    import re

    keywords = ["obstetrics", "gynaecology", "registrar"]
    jobs: list[JobRecord] = []
    seen: set[str] = set()

    for kw in keywords:
        html = fetch_taleo_search(cfg["search_url"], kw)
        soup = soup_from_html(html)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = text(a)
            if len(title) < 8:
                continue
            if not re.search(r"jobdetail|requisition|/job/", href, re.I):
                continue
            link = absolute_url(cfg["base_url"], href)
            if link in seen:
                continue
            if not _matches_keywords(title, title):
                continue
            seen.add(link)
            job = build_job(
                title=title,
                link=link,
                base_url=cfg["base_url"],
                portal_key="act_health",
                card_text=title,
                hospital=cfg.get("hospital", ""),
                state=cfg.get("state", ""),
            )
            if job:
                jobs.append(job)

    return _score_jobs(jobs)


def scrape_wave() -> list[JobRecord]:
    """WAVE — rural/regional locum & staff job listing (Australia-wide)."""
    cfg = config.PORTAL_CONFIG["wave"]
    html = fetch_html(cfg["search_url"], label="wave")
    from scrapers.portal_parsers import parse_wave

    jobs = parse_wave(html, cfg["base_url"])
    return _score_jobs(jobs)


HOSPITAL_SCRAPERS = {
    "monash_health": scrape_monash_health,
    "western_health": scrape_western_health,
    "wa_health": scrape_wa_health,
    "peninsula_health": scrape_peninsula_health,
    "the_womens": scrape_the_womens,
    "grampians_health": scrape_grampians_health,
    "eastern_health": scrape_eastern_health,
    "rch": scrape_rch,
    "gv_health": scrape_gv_health,
    "awh": scrape_awh,
    "act_health": scrape_act_health,
    "wave": scrape_wave,
}
