"""Shared HTTP fetch + HTML parsing helpers for medical job scrapers."""

from __future__ import annotations

import json
import random
import re
import time
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import config
from job_utils import (
    JobRecord,
    detect_experience_level,
    detect_specialty,
    detect_state,
    parse_relative_posted,
    safe_str,
)

_ua = UserAgent()


def get_random_headers(extra: Optional[dict[str, str]] = None) -> dict[str, str]:
    try:
        ua = _ua.random
    except Exception:  # noqa: BLE001
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Connection": "keep-alive",
    }
    if extra:
        headers.update(extra)
    return headers


def polite_delay() -> None:
    time.sleep(random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX))


def new_session(referer: Optional[str] = None) -> requests.Session:
    session = requests.Session()
    session.headers.update(get_random_headers())
    if referer:
        session.headers["Referer"] = referer
    return session


def fetch_html(
    url: str,
    timeout: int = 30,
    session: Optional[requests.Session] = None,
    extra_headers: Optional[dict[str, str]] = None,
    label: str = "fetch",
) -> str:
    polite_delay()
    headers = dict(session.headers if session else get_random_headers())
    if extra_headers:
        headers.update(extra_headers)
    client = session or requests
    response = client.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_json_post(
    url: str,
    payload: dict,
    timeout: int = 30,
    session: Optional[requests.Session] = None,
    label: str = "fetch_json_post",
) -> Any:
    polite_delay()
    headers = dict(session.headers if session else get_random_headers())
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"
    client = session or requests
    response = client.post(url, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_with_playwright(url: str, label: str = "playwright", wait_ms: int | None = None) -> str:
    from playwright.sync_api import sync_playwright

    polite_delay()
    wait = wait_ms or config.PLAYWRIGHT_WAIT_MS
    try:
        ua = _ua.random
    except Exception:  # noqa: BLE001
        ua = get_random_headers()["User-Agent"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=ua, locale="en-AU")
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(wait)
        html = page.content()
        browser.close()
    return html


def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def text(el) -> str:
    return safe_str(el.get_text(" ", strip=True) if el else "")


def absolute_url(base_url: str, href: str) -> str:
    if not href:
        return base_url
    if href.startswith("http"):
        return href
    return urljoin(base_url, href)


def build_job(
    title: str,
    link: str,
    base_url: str,
    portal_key: str,
    card_text: str = "",
    hospital: str = "",
    location: str = "",
    state: str = "",
    salary: str = "",
) -> Optional[JobRecord]:
    if not title or len(title) < 3:
        return None
    cfg = config.PORTAL_CONFIG.get(portal_key, {})
    combined = f"{title} {card_text}"
    specialty = detect_specialty(combined)
    experience = detect_experience_level(combined)
    return JobRecord(
        title=title[:200],
        specialty=specialty,
        experience_level=experience,
        hospital=hospital or cfg.get("hospital", ""),
        location=location or cfg.get("state", ""),
        state=state or cfg.get("state", ""),
        salary=salary,
        posted_date=parse_relative_posted(card_text),
        apply_link=absolute_url(base_url, link),
        description=card_text[:2000],
        platform=cfg.get("sheet", portal_key),
        layer=cfg.get("method", ""),
    )


def parse_job_cards(
    html: str,
    base_url: str,
    portal_key: str,
    selectors: list[str] | None = None,
) -> list[JobRecord]:
    """Generic parser for career page job listings."""
    soup = soup_from_html(html)
    jobs: list[JobRecord] = []
    seen: set[str] = set()
    cfg = config.PORTAL_CONFIG.get(portal_key, {})

    job_link_pattern = re.compile(
        r"(job|jobs|career|opening|vacancy|position|/j/|requisition|apply)",
        re.I,
    )

    cards = []
    if selectors:
        for sel in selectors:
            cards.extend(soup.select(sel))

    link_elements = cards if cards else soup.find_all("a", href=True)

    for el in link_elements:
        if el.name == "a":
            a = el
        else:
            a = el.find("a", href=True)
            if not a:
                continue

        href = a.get("href", "")
        if not job_link_pattern.search(href):
            continue

        title = text(a)
        if len(title) < 5 or len(title) > 200:
            continue

        link = absolute_url(base_url, href)
        if link in seen:
            continue
        seen.add(link)

        parent = a.find_parent(["article", "li", "div", "tr", "section"])
        card_text = text(parent) if parent else title

        if not any(kw.lower() in card_text.lower() for kw in config.KEYWORDS):
            if not any(kw.lower() in title.lower() for kw in config.KEYWORDS):
                continue

        job = build_job(
            title=title,
            link=link,
            base_url=base_url,
            portal_key=portal_key,
            card_text=card_text,
            hospital=cfg.get("hospital", ""),
            state=cfg.get("state", ""),
        )
        if job:
            jobs.append(job)

    return jobs[:50]
