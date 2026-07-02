"""
Multi-method job extraction per portal (Phase 4).

For each platform, tries an ordered chain of extraction methods (primary config
method first, then fallbacks). Records which method succeeded and a reliability note.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Callable

import config
from job_utils import JobRecord, RunLogger


@dataclass
class ExtractionOutcome:
    jobs: list[JobRecord]
    method_used: str
    reliability_note: str
    methods_tried: list[dict] = field(default_factory=list)
    error: str = ""
    raw_count: int = 0
    duration_seconds: float = 0.0
    retried: bool = False


def _fallback_scrape(portal_key: str, method_id: str) -> list[JobRecord]:
    """Run alternate fetch method for hospital/govt portals."""
    from scrapers.base import fetch_html, fetch_with_playwright, parse_job_cards
    from scrapers.aggregators import scrape_pageup
    from scrapers.portal_parsers import parse_peninsula_health

    cfg = config.PORTAL_CONFIG.get(portal_key, {})
    if not cfg:
        return []

    if method_id == "pageup" and portal_key == "pageup":
        return scrape_pageup()

    if method_id == "workday" and portal_key == "mercy_workday":
        from scrapers.workday_scraper import _scrape_mercy_workday_api

        jobs, _ = _scrape_mercy_workday_api()
        return jobs

    url = cfg.get("search_url", "")
    base = cfg.get("base_url", "")
    if not url:
        return []

    if method_id == "playwright":
        html = fetch_with_playwright(
            url,
            label=portal_key,
            wait_ms=config.PORTAL_PLAYWRIGHT_WAIT_MS.get(portal_key, 8000),
            stealth=portal_key in ("ranzcog", "jobradars"),
        )
    elif method_id == "static":
        html = fetch_html(url, label=portal_key)
    else:
        return []

    if portal_key == "peninsula_health":
        return parse_peninsula_health(html, base)

    return parse_job_cards(
        html,
        base,
        portal_key,
        selectors=[".job-result", ".job-listing", ".search-result", "article", "[data-job-id]", "li.data-row"],
    )


def _build_error_message(methods_tried: list[dict], portal_key: str) -> str:
    parts = []
    for m in methods_tried:
        if m.get("error"):
            parts.append(f"{m['method']}={m['error'][:100]}")
        elif m.get("jobs", 0) == 0:
            parts.append(f"{m['method']}=0 jobs")
    if parts:
        return f"{portal_key}_failed: " + "; ".join(parts)
    return "all_methods_failed"


def extract_jobs_multi_method(
    portal_key: str,
    primary_scraper: Callable[[], list[JobRecord]],
    logger: RunLogger | None = None,
) -> ExtractionOutcome:
    """
    Try primary scraper, then configured fallbacks until jobs are returned.
    Optionally retry primary once on zero jobs (PORTAL_ZERO_RETRY_ON_ZERO).
    """
    start_all = time.time()
    cfg = config.PORTAL_CONFIG.get(portal_key, {})
    cfg_method = cfg.get("method", "static")

    label_map = {
        "mercury": "mercury_html",
        "playwright": "playwright",
        "static": "static_html",
        "pageup": "pageup_html",
        "workday": "workday_api",
    }
    primary_label = label_map.get(cfg_method, cfg_method)

    chain: list[tuple[str, str, str]] = [(cfg_method, primary_label, "Primary — configured method")]
    if cfg_method == "static":
        chain.append(("playwright", "playwright", "Fallback — Playwright JS render"))
    elif cfg_method == "playwright":
        chain.append(("static", "static_html", "Fallback — static HTML"))
    elif cfg_method == "mercury":
        chain = [("mercury", "mercury_html", "Primary — Mercy Mercury portal")]
        chain.append(("workday", "workday_api", "Fallback — Mercy Workday API"))
    elif cfg_method == "pageup":
        chain.append(("playwright", "playwright", "Fallback — Playwright on PageUp URLs"))

    methods_tried: list[dict] = []
    raw_count = 0
    retried = False

    for idx, (method_id, method_label, reliability) in enumerate(chain):
        attempts = 2 if idx == 0 and config.PORTAL_ZERO_RETRY_ON_ZERO else 1
        for attempt in range(attempts):
            start = time.time()
            try:
                if idx == 0:
                    jobs = primary_scraper()
                else:
                    jobs = _fallback_scrape(portal_key, method_id)
                elapsed = round(time.time() - start, 2)
                err = ""
                if idx == 0 and not jobs and attempt == 0 and attempts > 1:
                    methods_tried.append(
                        {"method": method_label, "jobs": 0, "seconds": elapsed, "error": "zero_jobs_retry"}
                    )
                    retried = True
                    if logger:
                        logger.log(f"{portal_key}: 0 jobs on first attempt — retrying primary")
                    continue
            except Exception as exc:  # noqa: BLE001
                elapsed = round(time.time() - start, 2)
                err = str(exc)[:200]
                jobs = []
                methods_tried.append(
                    {"method": method_label, "jobs": 0, "seconds": elapsed, "error": err}
                )
                if logger:
                    logger.log(f"{portal_key}: method {method_label} failed: {err}")
                break

            methods_tried.append({"method": method_label, "jobs": len(jobs), "seconds": elapsed, "error": err})
            raw_count = max(raw_count, len(jobs))

            if jobs:
                note = reliability if idx == 0 else f"Fallback — used after primary ({cfg_method}) returned 0 jobs"
                if retried and idx == 0:
                    note = f"{note} (recovered on retry)"
                for job in jobs:
                    job.extraction_method = method_label
                    job.method_reliability_note = note
                _record_method_stats(portal_key, methods_tried)
                if logger:
                    logger.log(
                        f"{portal_key}: extraction via {method_label} ({len(jobs)} jobs, {elapsed}s"
                        f"{', retry recovered' if retried else ''})"
                    )
                return ExtractionOutcome(
                    jobs=jobs,
                    method_used=method_label,
                    reliability_note=note,
                    methods_tried=methods_tried,
                    raw_count=raw_count,
                    duration_seconds=round(time.time() - start_all, 2),
                    retried=retried,
                )
            break

    _record_method_stats(portal_key, methods_tried)
    error = _build_error_message(methods_tried, portal_key)
    return ExtractionOutcome(
        jobs=[],
        method_used="none",
        reliability_note="All extraction methods returned 0 jobs or failed",
        methods_tried=methods_tried,
        error=error,
        raw_count=raw_count,
        duration_seconds=round(time.time() - start_all, 2),
        retried=retried,
    )


def _record_method_stats(portal_key: str, methods_tried: list[dict]) -> None:
    path = config.LOGS_DIR / "extraction_stats.json"
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    portals = data.setdefault("portals", {})
    history = portals.setdefault(portal_key, {"runs": []})
    history["runs"].append({"methods": methods_tried})
    history["runs"] = history["runs"][-50:]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_method_rankings() -> dict[str, list[dict]]:
    """Aggregate success rates per portal/method for Phase 4 report."""
    path = config.LOGS_DIR / "extraction_stats.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    rankings: dict[str, list[dict]] = {}
    for portal_key, entry in data.get("portals", {}).items():
        method_stats: dict[str, dict] = {}
        for run in entry.get("runs", []):
            for m in run.get("methods", []):
                name = m.get("method", "unknown")
                stat = method_stats.setdefault(
                    name, {"attempts": 0, "successes": 0, "total_jobs": 0, "errors": 0}
                )
                stat["attempts"] += 1
                if m.get("jobs", 0) > 0:
                    stat["successes"] += 1
                    stat["total_jobs"] += m["jobs"]
                if m.get("error"):
                    stat["errors"] += 1
        ranked = []
        for name, stat in method_stats.items():
            rate = (stat["successes"] / stat["attempts"] * 100) if stat["attempts"] else 0
            ranked.append({**stat, "method": name, "success_rate_pct": round(rate, 1)})
        ranked.sort(key=lambda x: x["success_rate_pct"], reverse=True)
        rankings[portal_key] = ranked
    return rankings
