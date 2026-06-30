"""
Multi-method job extraction per portal (Phase 4).

For each platform, tries an ordered chain of extraction methods (primary config
method first, then fallbacks). Records which method succeeded and a reliability note.

Method stats are persisted to logs/extraction_stats.json for the strategy report.
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


def _fallback_scrape(portal_key: str, method_id: str) -> list[JobRecord]:
    """Run alternate fetch method for hospital/govt portals."""
    from scrapers.base import fetch_html, fetch_with_playwright, parse_job_cards
    from scrapers.aggregators import scrape_pageup

    cfg = config.PORTAL_CONFIG.get(portal_key, {})
    if not cfg:
        return []

    if method_id == "pageup" and portal_key == "pageup":
        return scrape_pageup()

    if method_id == "workday" and portal_key == "mercy_workday":
        from scrapers.workday_scraper import _scrape_mercy_workday_api

        return _scrape_mercy_workday_api()

    url = cfg.get("search_url", "")
    base = cfg.get("base_url", "")
    if not url:
        return []

    if method_id == "playwright":
        html = fetch_with_playwright(url, label=portal_key, wait_ms=8000)
    elif method_id == "static":
        html = fetch_html(url, label=portal_key)
    else:
        return []

    return parse_job_cards(
        html,
        base,
        portal_key,
        selectors=[".job-result", ".job-listing", ".search-result", "article", "[data-job-id]", "li.data-row"],
    )


def extract_jobs_multi_method(
    portal_key: str,
    primary_scraper: Callable[[], list[JobRecord]],
    logger: RunLogger | None = None,
) -> ExtractionOutcome:
    """
    Try primary scraper, then configured fallbacks until jobs are returned.
    Tags each JobRecord with extraction_method and method_reliability_note.
    """
    cfg = config.PORTAL_CONFIG.get(portal_key, {})
    cfg_method = cfg.get("method", "static")
    chain: list[tuple[str, str, str]] = [(cfg_method, cfg_method, "Primary — configured method")]

    label_map = {
        "mercury": "mercury_html",
        "playwright": "playwright",
        "static": "static_html",
        "pageup": "pageup_html",
        "workday": "workday_api",
    }
    primary_label = label_map.get(cfg_method, cfg_method)
    chain[0] = (cfg_method, primary_label, "Primary — configured method")

    if cfg_method == "static":
        chain.append(("playwright", "playwright", "Fallback — Playwright JS render"))
    elif cfg_method == "playwright":
        chain.append(("static", "static_html", "Fallback — static HTML"))
    elif cfg_method == "mercury":
        chain = [("mercury", "mercury_html", "Primary — Mercy Mercury portal")]
        chain.append(("workday", "workday_api", "Fallback — Workday API"))
    elif cfg_method == "pageup":
        chain.append(("playwright", "playwright", "Fallback — Playwright on PageUp URLs"))

    methods_tried: list[dict] = []

    for idx, (method_id, method_label, reliability) in enumerate(chain):
        start = time.time()
        try:
            if idx == 0:
                jobs = primary_scraper()
            else:
                jobs = _fallback_scrape(portal_key, method_id)
            elapsed = round(time.time() - start, 2)
            methods_tried.append({"method": method_label, "jobs": len(jobs), "seconds": elapsed, "error": ""})
            if jobs:
                note = reliability if idx == 0 else f"Fallback — used after primary ({cfg_method}) returned 0 jobs"
                for job in jobs:
                    job.extraction_method = method_label
                    job.method_reliability_note = note
                _record_method_stats(portal_key, methods_tried)
                if logger:
                    logger.log(f"{portal_key}: extraction via {method_label} ({len(jobs)} jobs, {elapsed}s)")
                return ExtractionOutcome(
                    jobs=jobs,
                    method_used=method_label,
                    reliability_note=note,
                    methods_tried=methods_tried,
                )
        except Exception as exc:  # noqa: BLE001
            elapsed = round(time.time() - start, 2)
            methods_tried.append(
                {"method": method_label, "jobs": 0, "seconds": elapsed, "error": str(exc)[:200]}
            )
            if logger:
                logger.log(f"{portal_key}: method {method_label} failed: {exc}")

    _record_method_stats(portal_key, methods_tried)
    return ExtractionOutcome(
        jobs=[],
        method_used="none",
        reliability_note="All extraction methods returned 0 jobs or failed",
        methods_tried=methods_tried,
        error="all_methods_failed",
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
