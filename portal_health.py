"""Track portal yield - auto-disable sources with 0 jobs for 3 consecutive runs."""

from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import config

HEALTH_PATH = config.LOGS_DIR / "portal_health.json"


def _load() -> dict:
    if not HEALTH_PATH.exists():
        return {"portals": {}, "disabled": [], "run_log": []}
    try:
        return json.loads(HEALTH_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"portals": {}, "disabled": [], "run_log": []}


def _save(data: dict) -> None:
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    HEALTH_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_portal_run(portal_key: str, jobs_found: int, error: str = "") -> None:
    data = _load()
    today = datetime.now(tz=ZoneInfo(config.AEST_TIMEZONE)).strftime("%Y-%m-%d")
    portals = data.setdefault("portals", {})
    entry = portals.setdefault(
        portal_key,
        {"zero_streak": 0, "last_jobs": 0, "last_run": today, "last_error": ""},
    )
    entry["last_run"] = today
    entry["last_jobs"] = jobs_found
    entry["last_error"] = error
    if jobs_found == 0:
        entry["zero_streak"] = entry.get("zero_streak", 0) + 1
    else:
        entry["zero_streak"] = 0

    run_log = data.setdefault("run_log", [])
    status = "ok" if not error else "error"
    run_log.append({
        "date": today,
        "portal": portal_key,
        "status": status,
        "jobs_found": jobs_found,
        "error": error,
    })
    data["run_log"] = run_log[-200:]

    disabled = set(data.get("disabled", []))
    if entry["zero_streak"] >= config.PORTAL_ZERO_STREAK_DISABLE:
        disabled.add(portal_key)
    elif jobs_found > 0:
        disabled.discard(portal_key)
    data["disabled"] = sorted(disabled)
    _save(data)


def is_portal_disabled(portal_key: str) -> bool:
    if not config.AUTO_DISABLE_DEAD_PORTALS:
        return False
    data = _load()
    return portal_key in data.get("disabled", [])


def get_health_summary() -> list[str]:
    data = _load()
    lines = []
    for key, entry in sorted(data.get("portals", {}).items()):
        err = entry.get("last_error", "")
        err_note = f", error={err[:60]}" if err else ""
        lines.append(
            f"{key}: status={'disabled' if key in data.get('disabled', []) else 'active'} | "
            f"jobs={entry.get('last_jobs', 0)} | zero_streak={entry.get('zero_streak', 0)}{err_note}"
        )
    if data.get("disabled"):
        lines.append(f"Auto-disabled portals: {', '.join(data['disabled'])}")
    return lines
