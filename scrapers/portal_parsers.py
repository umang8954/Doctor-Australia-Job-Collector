"""Portal-specific HTML parsers for sites where generic parse_job_cards() fails."""

from __future__ import annotations

import re
from typing import Callable
from urllib.parse import quote_plus

import config
from job_utils import JobRecord, detect_experience_level, detect_specialty
from scrapers.base import absolute_url, build_job, soup_from_html, text


def parse_peninsula_health(html: str, base_url: str) -> list[JobRecord]:
    """Peninsula Health PageUp-style careers site."""
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()
    cfg = config.PORTAL_CONFIG["peninsula_health"]

    selectors = [
        "a[href*='/job/']",
        ".jobTitle a",
        "li.job-result a",
        "article a[href*='/job/']",
    ]
    for sel in selectors:
        for a in soup.select(sel):
            href = a.get("href", "")
            title = text(a)
            if len(title) < 5 or "/job/" not in href:
                continue
            link = absolute_url(base_url, href)
            if link in seen:
                continue
            seen.add(link)
            parent = a.find_parent(["li", "article", "div", "tr"])
            card_text = text(parent) if parent else title
            if not _matches_keywords(title, card_text):
                continue
            job = build_job(
                title=title,
                link=link,
                base_url=base_url,
                portal_key="peninsula_health",
                card_text=card_text,
                hospital=cfg.get("hospital", ""),
                state=cfg.get("state", ""),
            )
            if job:
                jobs.append(job)
    return jobs[:50]


def parse_jobs_nt(html: str, base_url: str) -> list[JobRecord]:
    """NT Government jobs — accordion panels on Home/Search."""
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()
    cfg = config.PORTAL_CONFIG["jobs_nt"]

    for heading in soup.select(".jobTitle, .panel-heading .jobTitle, div.jobTitle"):
        spans = heading.find_all("span", recursive=True)
        title = ""
        for s in spans:
            t = text(s)
            if not t or t.lower() in ("applied", "new", "closing soon"):
                continue
            if len(t) >= 5 and not t.lower().startswith("registrar reg"):
                title = t
                break
        if not title:
            raw = text(heading)
            raw = re.sub(r"^Applied\s*", "", raw, flags=re.I).strip()
            title = raw.split("Registrar REG")[0].strip() if raw else ""
        title = re.sub(r"\s+", " ", title).strip()
        if len(title) < 5:
            continue
        if not _matches_keywords(title, text(heading)):
            continue

        panel = heading.find_parent("div", class_=re.compile(r"panel"))
        card_text = text(panel) if panel else text(heading)
        rtf_id = ""
        if panel:
            panel_body = panel.find("div", id=re.compile(r"panel$"))
            if panel_body and panel_body.get("id"):
                rtf_id = panel_body["id"].replace("panel", "")
            rtf_match = re.search(r"RTF:\s*(\d+)", card_text)
            if rtf_match:
                rtf_id = rtf_match.group(1)
        if not rtf_id:
            hid = heading.get("id") or (panel.get("id") if panel else "")
            if hid:
                m = re.search(r"(\d{5,})", hid)
                if m:
                    rtf_id = m.group(1)

        if rtf_id:
            link = f"{base_url.rstrip('/')}/Home/JobDetails/{rtf_id}"
        else:
            link = f"{base_url.rstrip('/')}/Home/Search"

        if link in seen:
            continue
        seen.add(link)

        job = build_job(
            title=title,
            link=link,
            base_url=base_url,
            portal_key="jobs_nt",
            card_text=card_text,
            hospital=cfg.get("hospital", ""),
            state=cfg.get("state", ""),
        )
        if job:
            jobs.append(job)
    return jobs[:50]


def parse_ranzcog(html: str, base_url: str) -> list[JobRecord]:
    """RANZCOG job board — table rows and listing articles."""
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()
    cfg = config.PORTAL_CONFIG["ranzcog"]

    for row in soup.select("table tr, .job-listing, article, .views-row, li.views-row"):
        link_el = row.find("a", href=True)
        if not link_el:
            continue
        title = text(link_el)
        if len(title) < 5:
            continue
        card_text = text(row)
        if not _matches_keywords(title, card_text):
            continue
        href = link_el["href"]
        link = absolute_url(base_url, href)
        if link in seen:
            continue
        seen.add(link)
        job = build_job(
            title=title,
            link=link,
            base_url=base_url,
            portal_key="ranzcog",
            card_text=card_text,
            specialty=detect_specialty(card_text) or "Obstetrics & Gynaecology",
            hospital=cfg.get("hospital", ""),
            state=cfg.get("state", "Australia"),
        )
        if job:
            jobs.append(job)
    return jobs[:50]


def parse_pageup_sa(html: str, base_url: str, hospital: str = "SA Health") -> list[JobRecord]:
    """SA Health PageUp — /caw/en/job/{id}/slug URLs."""
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()
    cfg = config.PORTAL_CONFIG["pageup"]

    skip_path = re.compile(r"/(login|alert|subscribe|applicationform|aw/application)", re.I)
    job_path = re.compile(r"/caw/en/job/\d+|/job/\d+|/en/job/\d+", re.I)

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if skip_path.search(href):
            continue
        if not job_path.search(href) and "/apply/" not in href:
            continue
        title = text(a)
        if len(title) < 5:
            parent = a.find_parent(["li", "div", "tr", "article", "h2", "h3"])
            title = text(parent)[:200] if parent else ""
        if len(title) < 5:
            continue
        if not _matches_keywords(title, text(a.find_parent(["li", "div", "article"]) or a)):
            continue
        link = absolute_url(base_url, href)
        if link in seen:
            continue
        seen.add(link)
        job = JobRecord(
            title=title[:200],
            specialty=detect_specialty(title),
            experience_level=detect_experience_level(title),
            hospital=hospital,
            location="SA",
            state="SA",
            apply_link=link,
            description=title,
            platform=cfg.get("sheet", "PageUp"),
            layer="pageup",
        )
        jobs.append(job)
    return jobs[:50]


def parse_qld_health(html: str, base_url: str) -> list[JobRecord]:
    """QLD Health careers search results."""
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = text(a)
        if len(title) < 8:
            continue
        if not re.search(r"job|requisition|vacancy|/en/job", href, re.I):
            continue
        if re.search(r"/apply-for-a-job|recruitment-contacts|application-process", href, re.I):
            continue
        if not _matches_keywords(title, title):
            continue
        link = absolute_url(base_url, href)
        if link in seen:
            continue
        seen.add(link)
        job = build_job(
            title=title,
            link=link,
            base_url=base_url,
            portal_key="pageup",
            card_text=title,
            hospital="Queensland Health",
            state="QLD",
        )
        if job:
            jobs.append(job)
    return jobs[:50]


def parse_nsw_health(html: str, base_url: str) -> list[JobRecord]:
    """NSW Health jobs.health.nsw.gov.au search results."""
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = text(a)
        if len(title) < 8:
            continue
        if "/jobs/" not in href or href.rstrip("/").endswith("/jobs"):
            continue
        if re.search(r"/moh$|/cclhd$|/hnelhd$|/islhd$|/mnclhd$|/search", href, re.I):
            continue
        if not _matches_keywords(title, title):
            continue
        link = absolute_url(base_url, href)
        if link in seen:
            continue
        seen.add(link)
        job = build_job(
            title=title,
            link=link,
            base_url=base_url,
            portal_key="pageup",
            card_text=title,
            hospital="NSW Health",
            state="NSW",
        )
        if job:
            jobs.append(job)
    return jobs[:50]


def parse_smartjobs_results(html: str, base_url: str) -> list[JobRecord]:
    """SmartJobs QLD jncustomsearch results page."""
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()
    cfg = config.PORTAL_CONFIG["smartjobs_qld"]

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = text(a)
        if len(title) < 8:
            continue
        if not re.search(
            r"viewFullSingle|/jobs/QLD-\d",
            href,
            re.I,
        ):
            continue
        if re.search(r"qld\.gov\.au/jobs/?$", href, re.I):
            continue
        if not _matches_keywords(title, title):
            continue
        link = absolute_url(base_url, href)
        if link in seen:
            continue
        seen.add(link)
        job = build_job(
            title=title,
            link=link,
            base_url=base_url,
            portal_key="smartjobs_qld",
            card_text=title,
            hospital=cfg.get("hospital", ""),
            state=cfg.get("state", ""),
        )
        if job:
            jobs.append(job)
    return jobs[:50]


def parse_mercy_workday_html(html: str, base_url: str) -> list[JobRecord]:
    """Mercy Health Workday careers page (Playwright-rendered)."""
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()
    cfg = config.PORTAL_CONFIG["mercy_workday"]

    for el in soup.select("[data-automation-id='jobTitle'], li[data-automation-id='jobPosting'] a, a[data-automation-id='jobTitle']"):
        if el.name == "a":
            a = el
        else:
            a = el.find("a", href=True) or el
        title = text(a if hasattr(a, "get") else el)
        href = a.get("href", "") if hasattr(a, "get") else ""
        if len(title) < 5 or not href:
            continue
        if not _matches_keywords(title, title):
            continue
        link = absolute_url(base_url, href)
        if link in seen:
            continue
        seen.add(link)
        job = build_job(
            title=title,
            link=link,
            base_url=base_url,
            portal_key="mercy_workday",
            card_text=title,
            hospital=cfg.get("hospital", ""),
            state=cfg.get("state", ""),
        )
        if job:
            jobs.append(job)
    return jobs[:50]


def _matches_keywords(title: str, card_text: str) -> bool:
    blob = f"{title} {card_text}".lower()
    return any(kw.lower() in blob for kw in config.KEYWORDS)


def merge_jobs(job_lists: list[list[JobRecord]]) -> list[JobRecord]:
    seen: set[str] = set()
    merged: list[JobRecord] = []
    for jobs in job_lists:
        for job in jobs:
            key = job.apply_link or job.title
            if key in seen:
                continue
            seen.add(key)
            merged.append(job)
    return merged[:50]
