"""Phase 2 post-processing: apply queue, follow-ups, daily digest, profile sheets."""

from __future__ import annotations

import config
from excel_manager import ExcelManager
from job_utils import RunLogger, now_aest
from resume_matcher import match_label


def run_phase2_post_process(
    excel: ExcelManager,
    total_new: int,
    logger: RunLogger,
) -> None:
    all_count = excel.rebuild_all_jobs_sheet()
    logger.log(f"All_Jobs_Australia: {all_count} jobs consolidated")

    match_count = excel.rebuild_profile_matches_sheet()
    logger.log(f"Profile_Matches: {match_count} rows ({len(excel.profiles)} doctor profiles)")

    queue_size = excel.rebuild_apply_queue()
    logger.log(f"Apply Queue rebuilt: {queue_size} jobs (sorted by Match % desc)")
    for p in excel.profiles:
        logger.log(f"  Per-profile queue: Queue_{p.get('id', '')[:28]}")

    follow_ups = excel.get_follow_up_jobs()
    if follow_ups:
        logger.log(
            f"Follow-up needed ({len(follow_ups)} applied jobs, "
            f"no response after {config.FOLLOW_UP_AFTER_DAYS} days):"
        )
        for fu in follow_ups[:10]:
            logger.log(f"  - [{fu['days']}d] {fu['title']} @ {fu['hospital']} ({fu.get('profile', '')})")

    high_match = _count_high_match(excel)
    top_picks = _top_picks(excel, limit=5)

    profile_names = ", ".join(p.get("name", "") for p in excel.profiles[:5])
    digest_lines = [
        f"# Daily Digest - {now_aest().strftime('%d-%m-%Y')}",
        "",
        f"Profiles: {profile_names}",
        f"Today: **{total_new} new** | **{high_match} high match** | Apply Queue: {queue_size}",
        "",
        "## Top picks (best profile match)",
    ]
    if top_picks:
        for i, pick in enumerate(top_picks, 1):
            digest_lines.append(
                f"{i}. {pick['title']} @ {pick['hospital']} ({pick['state']}) - "
                f"{pick['match_pct']}% [{pick['label']}] -> {pick.get('profile', '')}"
            )
    else:
        digest_lines.append("_No high-match jobs today._")

    if follow_ups:
        digest_lines.extend(["", "## Follow-up reminders"])
        for fu in follow_ups[:5]:
            digest_lines.append(f"- {fu['title']} @ {fu['hospital']} ({fu['days']} days)")

    config.DIGEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.DIGEST_FILE.write_text("\n".join(digest_lines), encoding="utf-8")

    console_msg = (
        f"Today: {total_new} new | {high_match} high match | "
        f"{len(excel.profiles)} profiles | "
        f"Top picks: {[p['title'][:35] for p in top_picks]}"
    )
    logger.log(console_msg)
    print(f"\n{console_msg}\n")


def _match_col_index() -> int:
    return config.SHEET_COLUMNS.index("Match %") + 1


def _profile_col_index() -> int:
    return config.SHEET_COLUMNS.index("Best Profile") + 1


def _count_high_match(excel: ExcelManager) -> int:
    count = 0
    match_col = _match_col_index()
    for sheet in config.ALL_JOB_SOURCE_SHEETS:
        if sheet not in excel.wb.sheetnames:
            continue
        ws = excel.wb[sheet]
        for row in range(2, ws.max_row + 1):
            try:
                pct = int(float(ws.cell(row, match_col).value or 0))
            except (ValueError, TypeError):
                pct = 0
            if pct >= config.HIGH_MATCH_THRESHOLD:
                count += 1
    return count


def _top_picks(excel: ExcelManager, limit: int = 5) -> list[dict]:
    picks: list[dict] = []
    match_col = _match_col_index()
    profile_col = _profile_col_index()
    for sheet in config.ALL_JOB_SOURCE_SHEETS:
        if sheet not in excel.wb.sheetnames:
            continue
        ws = excel.wb[sheet]
        for row in range(2, ws.max_row + 1):
            title = ws.cell(row, 1).value
            if not title:
                continue
            try:
                pct = int(float(ws.cell(row, match_col).value or 0))
            except (ValueError, TypeError):
                pct = 0
            if pct >= config.HIGH_MATCH_THRESHOLD:
                picks.append({
                    "title": str(title),
                    "hospital": str(ws.cell(row, 3).value or ""),
                    "state": str(ws.cell(row, 5).value or ""),
                    "match_pct": pct,
                    "label": match_label(pct),
                    "profile": str(ws.cell(row, profile_col).value or ""),
                })
    picks.sort(key=lambda p: p["match_pct"], reverse=True)
    return picks[:limit]
