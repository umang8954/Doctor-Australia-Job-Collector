"""Specialty board scrapers - RANZCOG and RACP (Australia jobs only)."""

from __future__ import annotations

import re

import config
from job_utils import (
    JobRecord,
    contains_au_location,
    contains_non_au_location,
    detect_experience_level,
    detect_specialty,
    detect_state,
    passes_australia_filter,
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
    new_session,
    polite_delay,
    soup_from_html,
    text,
)
from scrapers.block_detection import analyze_html, failure_reason_from_analysis
from scrapers.portal_parsers import parse_ranzcog


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


def _score_ranzcog_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    """RANZCOG board is O&G-focused; keep AU clinical roles without the 7-day cut-off."""
    filtered: list[JobRecord] = []
    for job in jobs:
        if not job.title or len(job.title) < 3:
            continue
        if not job.apply_link.startswith("http"):
            continue
        blob = job.combined_text().lower()
        # Drop clearly overseas postings (Pacific / NZ academic roles)
        overseas = (
            "fiji",
            "papua new guinea",
            "solomon island",
            "new zealand",
            "wellington",
            "christchurch",
            "auckland",
        )
        title_hosp = f"{job.title} {job.hospital} {job.location}".lower()
        if any(x in title_hosp for x in overseas):
            continue
        if any(x in blob for x in ("fiji national", "papua new guinea", "solomon island")):
            continue
        if not passes_australia_filter(job):
            # Still keep if apply link is on jobs.ranzcog.edu.au and title isn't overseas
            if "jobs.ranzcog.edu.au" not in job.apply_link.lower():
                continue
            if any(x in title_hosp for x in overseas):
                continue
        job.specialty = job.specialty or "Obstetrics & Gynaecology"
        job.match_pct = score_resume_match(
            job.title, job.description, job.specialty, job.location, job.state
        )
        job.match_label = match_label(job.match_pct)
        filtered.append(job)
    return filtered


def _is_au_job(card_text: str, title: str) -> bool:
    combined = f"{title} {card_text}"
    if contains_non_au_location(combined):
        return False
    return contains_au_location(combined) or bool(detect_state(combined))


def _fetch_ranzcog_pages() -> tuple[list[JobRecord], str]:
    """
    Fetch RANZCOG listings via static HTML + AJAX pagination.
    Category filter URLs often return 403; the main board + ajax/?action=request_for_listings works.
    """
    cfg = config.PORTAL_CONFIG["ranzcog"]
    base = cfg["base_url"]
    all_jobs: list[JobRecord] = []
    seen: set[str] = set()
    last_reason = ""

    session = new_session(referer="https://www.ranzcog.edu.au/")
    try:
        polite_delay()
        resp = session.get(cfg["search_url"], timeout=45)
        status = resp.status_code
        html = resp.text
    except Exception as exc:  # noqa: BLE001
        return [], f"static_{type(exc).__name__}: {str(exc)[:100]}"

    analysis = analyze_html(html, status_code=status)
    if analysis.is_blocked:
        return [], failure_reason_from_analysis(analysis, 0)

    page1 = parse_ranzcog(html, base)
    for job in page1:
        if job.apply_link not in seen:
            seen.add(job.apply_link)
            all_jobs.append(job)

    # AJAX "Load more" pages (HTML fragments of listing-item articles)
    empty_streak = 0
    for page in range(2, 15):
        ajax_url = f"{base.rstrip('/')}/ajax/?action=request_for_listings&page={page}"
        try:
            polite_delay()
            r = session.get(
                ajax_url,
                timeout=30,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": cfg["search_url"],
                    "Accept": "text/html, */*; q=0.01",
                },
            )
            if r.status_code in (429, 503):
                last_reason = f"ajax_page{page}_HTTP{r.status_code}"
                break
            if r.status_code == 403:
                empty_streak += 1
                if empty_streak >= 2:
                    break
                continue
            frag = r.text or ""
            if len(frag.strip()) < 50:
                empty_streak += 1
                if empty_streak >= 2:
                    break
                continue
            page_jobs = parse_ranzcog(frag, base)
            if not page_jobs:
                empty_streak += 1
                if empty_streak >= 2:
                    break
                continue
            empty_streak = 0
            for job in page_jobs:
                if job.apply_link in seen:
                    continue
                seen.add(job.apply_link)
                all_jobs.append(job)
        except Exception as exc:  # noqa: BLE001
            last_reason = f"ajax_page{page}_{type(exc).__name__}: {str(exc)[:80]}"
            empty_streak += 1
            if empty_streak >= 2:
                break

    if all_jobs:
        return all_jobs, ""
    return [], last_reason or failure_reason_from_analysis(analysis, 0)


def scrape_ranzcog() -> list[JobRecord]:
    """RANZCOG — static + AJAX first (avoids category 403), then stealth Playwright, then fallbacks."""
    cfg = config.PORTAL_CONFIG["ranzcog"]
    env = get_runtime_environment()
    last_reason = ""

    jobs, err = _fetch_ranzcog_pages()
    if jobs:
        return _score_ranzcog_jobs(jobs)
    last_reason = err or "static_ajax_empty"

    try:
        html = fetch_with_playwright(
            cfg["search_url"],
            label="ranzcog",
            stealth=True,
            wait_until="domcontentloaded",
            referer="https://www.google.com.au/",
        )
        analysis = analyze_html(html, status_code=200 if len(html) > 2000 else 403)
        jobs = parse_ranzcog(html, cfg["base_url"])
        if jobs:
            return _score_ranzcog_jobs(jobs)
        last_reason = failure_reason_from_analysis(analysis, len(jobs)) or last_reason
    except Exception as exc:  # noqa: BLE001
        last_reason = f"playwright_{type(exc).__name__}: {str(exc)[:100]}"

    try:
        html, status = fetch_html_with_status(
            cfg["search_url"], label="ranzcog", raise_for_status=False
        )
        analysis = analyze_html(html, status_code=status)
        jobs = parse_ranzcog(html, cfg["base_url"])
        if jobs:
            return _score_ranzcog_jobs(jobs)
        if analysis.is_blocked:
            last_reason = failure_reason_from_analysis(analysis, 0)
    except Exception as exc:  # noqa: BLE001
        last_reason = f"static_{type(exc).__name__}: {str(exc)[:100]}"

    from scrapers.ranzcog_rss import scrape_ranzcog_peninsula_fallback, scrape_ranzcog_rss_fallback

    rss_jobs = scrape_ranzcog_rss_fallback()
    if rss_jobs:
        return _score_ranzcog_jobs(rss_jobs)

    peninsula_jobs = scrape_ranzcog_peninsula_fallback()
    if peninsula_jobs:
        return _score_ranzcog_jobs(peninsula_jobs)

    raise RuntimeError(
        f"ranzcog_failed from {env} — {last_reason or 'no listings parsed'}; all fallbacks empty"
    )


def scrape_racp() -> list[JobRecord]:
    cfg = config.PORTAL_CONFIG["racp"]
    html = fetch_html(cfg["search_url"], label="racp")
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []

    for section in soup.select("table, .content, article, .vacancy, li"):
        links = section.find_all("a", href=True)
        for a in links:
            title = text(a)
            href = a.get("href", "")
            if len(title) < 8:
                continue
            if not any(
                kw.lower() in title.lower()
                for kw in config.KEYWORDS + ["physician", "medicine", "position"]
            ):
                continue
            card_text = text(section)
            if not _is_au_job(card_text, title):
                continue

            location_match = re.search(
                r"(Queensland|Victoria|Western Australia|Northern Territory|"
                r"New South Wales|South Australia|Tasmania|NSW|VIC|QLD|WA|NT|SA|TAS|ACT|Australia)",
                card_text,
                re.I,
            )
            state = detect_state(card_text, "")
            if not state and not location_match:
                continue

            combined = f"{title} {card_text}"
            job = JobRecord(
                title=title[:200],
                specialty=detect_specialty(combined),
                experience_level=detect_experience_level(combined),
                hospital=safe_str(section.find("strong")) or "RACP Member Hospital (AU)",
                location=location_match.group(0) if location_match else (state or "Australia"),
                state=state or "Australia",
                apply_link=absolute_url(cfg["base_url"], href),
                description=card_text[:2000],
                platform=cfg.get("sheet", "RACP"),
                layer="static",
            )
            jobs.append(job)

    seen = set()
    unique = []
    for job in jobs:
        key = job.apply_link
        if key not in seen:
            seen.add(key)
            unique.append(job)

    return _score_jobs(unique)


SPECIALTY_SCRAPERS = {
    "ranzcog": scrape_ranzcog,
    "racp": scrape_racp,
}
