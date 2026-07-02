# Excel Structure Improvements — Job_Tracker.xlsx

**Workbook:** `Job_Tracker.xlsx`  
**Analysis date:** 30 June 2026  
**Current state:** 26 sheets, 123 jobs, 19 columns on portal tabs

This document reviews the current Excel structure and recommends improvements for usability, data quality, and maintainability.

---

## Current Structure Assessment

### Strengths

- **Per-portal tabs** make it easy to see which sources are working vs empty
- **All_Jobs_Australia** provides a single searchable view without manual consolidation
- **Profile_Matches** enables side-by-side comparison across 5 demo doctors
- **Apply_Queue** and per-profile queues support prioritised application workflow
- **Phase 2–4 columns** (Match %, Validation Flags, Extraction Method) add transparency
- **Daily_Summary** gives an operational audit trail per run

### Weaknesses

- **7 of 16 portal tabs are empty** — workbook looks broken without explanation on-sheet
- **Salary never populated** (0/123) — column exists but adds no value today
- **Notes duplicates Validation Flags** on 119 rows — redundant storage
- **Apply_Queue header misaligned** with data (legacy header missing newer columns)
- **No High Match jobs** (max 67%) — queue may not feel actionable
- **Match % average 30.4** — many rows flagged as weak matches
- **Location often equals State** (e.g. both `VIC`) — low geographic precision

---

## Missing Useful Columns

| Proposed Column | Sheet(s) | Purpose | Priority |
|-----------------|----------|---------|----------|
| **Job ID / External Ref** | Portal tabs, All_Jobs | Stable dedup key from portal (e.g. PageUp requisition ID) | High |
| **Closing Date** | Portal tabs | Urgency — apply before deadline | High |
| **Employment Type** | Portal tabs | Full-time / part-time / locum / fellowship | Medium |
| **AHPRA / Registration Required** | Portal tabs | Eligibility filter for international doctors | Medium |
| **Visa Sponsorship** | Portal tabs | Common filter for overseas applicants | Medium |
| **Last Scraped On** | Portal tabs | Distinguish stale rows from fresh (separate from Job Added On) | High |
| **Portal Status** | Portal tabs (row 1 banner) or Daily_Summary | `OK` / `Empty` / `Error` / `Disabled` per portal | High |
| **Scrape Error** | Portal tabs (meta row) or Daily_Summary | Last error message when tab is empty | High |
| **Job Description Snippet** | Portal tabs | 200-char summary for manual review without opening link | Medium |
| **Duplicate Of** | All_Jobs | Link when same job appears on multiple portals | Medium |
| **Confidence Tier** | Portal tabs | `High` / `Moderate` / `Low` from validator (not just %) | Low |
| **Follow-Up Date** | Portal tabs | Auto-set 7 days after Applied? = Y | Medium |

---

## Redundant Columns

| Column(s) | Issue | Recommendation |
|-----------|-------|----------------|
| **Notes** vs **Validation Flags** | Same text copied to both on 119/123 rows | Keep **Validation Flags** as system field; use **Notes** for user-only input. Stop auto-copying flags into Notes. |
| **Location** vs **State** | Often identical (`VIC` / `VIC`) | Merge when redundant, or enforce Location = suburb/city and State = abbreviation only |
| **Portal** on portal tabs | Always equals sheet name on per-portal tabs | Keep on `All_Jobs_Australia` only; optional on portal tabs |
| **Profile_Matches** vs portal **Match %** | Best Match % duplicates portal Best Profile score | Keep Profile_Matches for multi-profile view; document that Best Match % = portal Match % |
| **Method Reliability Note** | Repetitive (`Primary — configured method` on most rows) | Collapse to single char code (`P`/`F`) + lookup table, or show only when fallback used |

---

## Better Naming Conventions

| Current Name | Suggested Name | Reason |
|--------------|----------------|--------|
| `Applied?` | `Applied` | Cleaner; use data validation `Y`/`N` instead of `?` in header |
| `Match %` | `Match Score` or `Match Pct` | Avoid `%` in header (formula confusion in Excel) |
| `Job Added On` | `First Seen` or `Collected At` | Clearer that this is scrape time, not employer post time |
| `Best Profile` | `Best Match Profile` | Clarifies this is profile matching, not employer |
| `The_Womens` | `The_Womens_Hospital` | Consistent with other hospital sheet names |
| `Mercy_Workday` | `Mercy_Health` | Reflects actual platform (Mercury, not Workday) |
| `Queue_dr_og_registrar` | `Queue_Priya_Sharma` | Human-readable; match Doctor Name |
| `Errors?` (Daily_Summary) | `Error Message` | More descriptive; `No` is ambiguous |

---

## Data Validation Improvements

| Field | Current State | Recommended Validation |
|-------|---------------|------------------------|
| **Applied?** | Free text, 0% filled | Dropdown: `Y`, `N`, blank. Trigger Status → `Applied` when `Y` |
| **Status** | Auto + manual mix | Dropdown: `Yet to apply`, `1 day old` … `Applied`, `Expired`, `Source unreachable` |
| **State** | Free text | Dropdown: `QLD`, `VIC`, `WA`, `NSW`, `SA`, `TAS`, `NT`, `ACT`, `Australia` |
| **Match %** | Integer | Range 0–100; conditional formatting (red &lt;30, amber 30–69, green ≥70) |
| **Apply Link** | URL string | Excel hyperlink format; flag invalid/missing URLs |
| **Posted Date** | DD-MM-YYYY text | Excel date type + format `dd-mm-yyyy` for sorting |
| **Job Added On** | Datetime text | Excel datetime type for sort/filter |
| **Specialty** | Free text | Dropdown from `SPECIALTY_RULES` canonical names |
| **Experience Level** | Free text | Dropdown from `EXPERIENCE_RULES` canonical names |

### Conditional formatting suggestions

| Rule | Format |
|------|--------|
| Match % ≥ 70 | Green fill — High Match |
| Match % 50–69 | Light green — Good Match |
| Match % &lt; 30 | Light red — review before applying |
| Validation Flags contains `Specialty mismatch` | Amber text |
| Status = `Expired` or portal tab empty | Grey row |
| Apply Link empty | Red border (should never happen on data rows) |

---

## Better Organization & Best Practices

### 1. Fix Apply_Queue column migration

**Problem:** Header row shows 13 columns (`Rank`, `Source Sheet`, `Job Title` …) but data rows contain 18 fields including `Profile`, `Experience Level`, and extraction columns.

**Fix:** Extend `_ensure_custom_sheet()` / `_migrate_columns()` for `Apply_Queue` and `Queue_*` tabs — same pattern used for portal tabs.

### 2. Add a README / Index sheet

First tab explaining:

- Sheet purposes and update schedule
- Column glossary (link to `Excel_Columns_Documentation.md`)
- Portal status dashboard (9 working / 7 empty)
- How to mark jobs Applied and refresh queues

### 3. Portal status banner on empty tabs

When a portal tab has 0 jobs, insert row 2:

| Portal | Status | Last Error | Last Run |
|--------|--------|------------|----------|
| SmartJobs_QLD | Failed | all_methods_failed | 30-06-2026 21:27 |

Avoids user confusion when opening an empty sheet.

### 4. Consolidate queue sheets

**Option A (current):** 1 global Apply_Queue + 5 per-profile queues (6 queue sheets)  
**Option B:** Single `Apply_Queue` with **Profile** filter column + Excel table filters  
**Option C:** Keep per-profile queues but hide when empty

Recommendation: **Option B** for simpler maintenance, unless users strongly prefer separate tabs.

### 5. Separate system vs user columns

| System (auto-written, avoid manual edit) | User (manual) |
|------------------------------------------|---------------|
| Job Title through Method Reliability Note | Applied?, Notes (user section only) |
| Match %, Validation Flags, Status (auto) | Optional: Interview Date, Outcome |
| Job Added On, Portal, Extraction fields | |

Use Excel **sheet protection** on system columns to prevent accidental overwrites.

### 6. Stale job handling

When a portal fetch fails but old rows remain (e.g. RCH historically):

- Set **Status** = `Source unreachable` on existing rows
- Add **Last Verified On** column updated only on successful re-scrape
- Optionally move jobs older than 30 days to `Archive` sheet

### 7. Reduce sheet count for performance

26 sheets is manageable but heavy for mobile Excel. Consider:

- **Archive** sheet for expired/old jobs removed from portal tabs
- **Pivot** on Daily_Summary for portal health dashboard
- Drop duplicate data: portal tabs are source of truth; `All_Jobs_Australia` rebuilt each run (keep)

### 8. Improve Daily_Summary

| Addition | Benefit |
|----------|---------|
| **Duration (seconds)** | Spot slow portals |
| **Method used (actual)** | Primary vs fallback |
| **Raw jobs before filter** | Distinguish scrape success vs keyword filter loss |
| **Portal enabled/disabled** | Show auto-disable state |

### 9. Hyperlinks and UX

- Ensure **Apply Link** column uses `=HYPERLINK()` or openpyxl hyperlink objects
- Freeze header row (row 1) on all data sheets
- Auto-filter on `All_Jobs_Australia` and `Apply_Queue`
- Sort portal tabs: working portals first, empty portals last

### 10. Data quality targets

Based on current fill rates:

| Column | Current | Target |
|--------|---------|--------|
| Specialty | 72% | ≥90% — improve parser from job title |
| Experience Level | 83% | ≥95% — add rules for “Advanced Trainee”, “Fellow” |
| Salary | 0% | ≥20% if shown on source sites |
| Validation Flags empty | 3% | OK — only when clean match |
| High Match (≥70%) | 0% | Tune thresholds or profiles for actionable queue |

---

## Priority Implementation Roadmap

| Phase | Action | Effort |
|-------|--------|--------|
| **1** | Fix Apply_Queue / Queue_* header migration | Low |
| **2** | Add Index/README sheet + portal status on empty tabs | Low |
| **3** | Stop duplicating Validation Flags → Notes | Low |
| **4** | Add data validation dropdowns (Applied, State, Status) | Medium |
| **5** | Add Closing Date, Last Scraped On, Job ID columns | Medium |
| **6** | Conditional formatting for Match % | Low |
| **7** | Rename columns per conventions (breaking — migrate carefully) | Medium |
| **8** | Consolidate queue sheets or add filters | Medium |

---

## Summary

The workbook is **functionally rich** for a v1 job tracker but shows strain from rapid Phase 2–4 expansion: header drift on queue sheets, empty portal tabs without explanation, and unused/redundant columns. The highest-impact improvements are **fixing queue header alignment**, **documenting empty portals on-sheet**, **separating system flags from user Notes**, and **adding Closing Date + Last Scraped On** for practical job-hunting workflow.

---

*Review based on `Job_Tracker.xlsx` (123 jobs, 30-06-2026 run) and `excel_manager.py`.*
