#!/usr/bin/env python3
"""
Daily Doctor/Medical Job Collector for Australia.

Collects Registrar, Senior Registrar, PHO, RMO, Consultant, and House Officer
roles from government portals, hospital career pages, specialty boards, and aggregators.

Run: python job_collector.py
"""

from __future__ import annotations

import sys

import config
from excel_manager import ExcelManager
from extraction_runner import extract_jobs_multi_method
from job_utils import RunLogger, now_aest, passes_filters
from job_validator import apply_validation_to_job
from phase2_processor import run_phase2_post_process
from portal_health import get_health_summary, is_portal_disabled, record_portal_run, reset_disabled_portals
from profile_loader import load_profiles
from scrapers import ALL_SCRAPERS


def run_all_scrapers(logger: RunLogger) -> dict[str, dict]:
    """Run each enabled portal; one failure must not stop others."""
    results: dict[str, dict] = {}
    profiles = load_profiles()

    for portal_key, scrape_fn in ALL_SCRAPERS.items():
        cfg = config.PORTAL_CONFIG.get(portal_key, {})
        sheet = cfg.get("sheet", portal_key)
        method = cfg.get("method", "unknown")

        if not config.PLATFORMS_TO_RUN.get(portal_key, False):
            logger.log(f"{portal_key}: skipped (disabled in config)")
            continue

        if is_portal_disabled(portal_key):
            logger.log(f"{portal_key}: skipped (auto-disabled - 0 jobs streak)")
            results[portal_key] = {"jobs": [], "error": "auto-disabled", "sheet": sheet, "method": method}
            continue

        try:
            logger.log(f"{portal_key}: scraping ({method})...")
            outcome = extract_jobs_multi_method(portal_key, scrape_fn, logger)
            raw_jobs = outcome.jobs
            filtered = []
            for job in raw_jobs:
                if not passes_filters(job):
                    continue
                if apply_validation_to_job(job, profiles):
                    filtered.append(job)
            logger.log(
                f"{portal_key}: {len(raw_jobs)} raw -> {len(filtered)} kept "
                f"(via {outcome.method_used}; Australia + validation)"
            )
            record_portal_run(portal_key, len(filtered), error=outcome.error)
            results[portal_key] = {
                "jobs": filtered,
                "error": outcome.error,
                "sheet": sheet,
                "method": outcome.method_used or method,
            }
        except Exception as exc:  # noqa: BLE001
            err = str(exc)
            logger.log(f"{portal_key} FAILED: {err}")
            record_portal_run(portal_key, 0, error=err)
            results[portal_key] = {"jobs": [], "error": err, "sheet": sheet, "method": method}

    return results


def print_summary(total_new: int, stats: dict[str, int]) -> None:
    run = now_aest()
    print("=" * 56)
    print("Doctor Job Collector - Run Complete")
    print(f"Date: {run.strftime('%d-%m-%Y')} | Time: {run.strftime('%H:%M')} AEST")
    print("-" * 56)
    for portal, count in sorted(stats.items()):
        print(f"  {portal}: {count} new")
    print("-" * 56)
    print(f"Total new jobs added: {total_new}")
    print(f"Excel: {config.EXCEL_FILE_PATH}")
    print(f"Digest: {config.DIGEST_FILE}")
    print("=" * 56)


def main() -> int:
    logger = RunLogger()
    logger.log("=== Doctor Job Collector run started ===")

    reenabled = reset_disabled_portals()
    if reenabled:
        logger.log(f"Re-enabled auto-disabled portals: {', '.join(reenabled)}")

    excel = ExcelManager()
    total_new = 0
    stats: dict[str, int] = {}

    scrape_results = run_all_scrapers(logger)

    for portal_key, result in scrape_results.items():
        sheet = result["sheet"]
        jobs = result["jobs"]
        method = result["method"]
        error = result["error"]

        added = excel.add_jobs(sheet, jobs)
        total = excel.sheet_job_count(sheet)
        excel.append_summary(sheet, method, added, total, error=error)
        stats[sheet] = added
        total_new += added
        logger.log(f"  {sheet}: {added} new (total: {total})")

    logger.log("Updating Status column...")
    excel.update_sheet_statuses()

    logger.log("Re-validating all jobs (Match %, profiles, flags)...")
    excel.revalidate_all_jobs()

    try:
        run_phase2_post_process(excel, total_new, logger)
    except Exception as exc:  # noqa: BLE001
        logger.log(f"Phase 2 post-process error: {exc}")

    logger.log(f"Doctor profiles loaded: {len(excel.profiles)}")

    for line in get_health_summary():
        logger.log(f"Portal health: {line}")

    excel.save()
    logger.log(f"Excel saved: {config.EXCEL_FILE_PATH}")
    logger.log(f"Total new jobs: {total_new}")
    logger.save()

    print_summary(total_new, stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
