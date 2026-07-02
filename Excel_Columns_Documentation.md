# Excel Columns Documentation — Job_Tracker.xlsx

**Workbook:** `Job_Tracker.xlsx`  
**Analysis date:** 30 June 2026  
**Total sheets:** 26 (16 portal tabs + 10 supporting tabs)

This document describes every column across all sheet types in the workbook.

---

## Sheet Types

| Sheet Type | Sheet Names | Purpose |
|------------|-------------|---------|
| **Portal job tabs** | SmartJobs_QLD … PageUp (16 sheets) | One tab per job portal; stores scraped vacancies |
| **Consolidated** | All_Jobs_Australia | All portal jobs in one view (123 rows) |
| **Matching** | Profile_Matches | Per-job scores against all 5 demo doctor profiles |
| **Queues** | Apply_Queue, Queue_dr_* (5 tabs) | Prioritised jobs to apply for, overall and per profile |
| **Reference** | Doctor_Profiles | Demo profile metadata used for Match % scoring |
| **Operations** | Daily_Summary | Per-portal run log (method, counts, errors) |

---

## Portal Job Tabs & All_Jobs_Australia (19 columns)

Used on all 16 portal sheets and mirrored in `All_Jobs_Australia`. Defined in `config.SHEET_COLUMNS`.

| # | Column Name | Purpose | Why Required | How It Is Used | Example Value | Mandatory/Optional |
|---|-------------|---------|--------------|----------------|---------------|-------------------|
| 1 | **Job Title** | Primary identifier for the vacancy | Deduplication, display, matching, apply queue ranking | Scraped from portal; used as dedup key with Hospital; fed to `job_validator` for title relevance (40% weight) | `2027 Obstetric & Gynaecology - Senior Registrar` | **Mandatory** |
| 2 | **Specialty** | Medical specialty detected from title/description | Profile matching (25% weight); filtering and queue grouping | Derived via `SPECIALTY_RULES` in `config.py` from job text | `Obstetrics & Gynaecology` | Optional (88/123 filled) |
| 3 | **Experience Level** | Seniority / role level | Profile matching (15% weight); queue filtering | Derived via `EXPERIENCE_RULES` from title text | `Senior Registrar` | Optional (102/123 filled) |
| 4 | **Hospital** | Employer or health service name | Deduplication key; location context; display | Set from portal config default or parsed from listing | `Monash Health` | **Mandatory** |
| 5 | **Location** | City, suburb, or region text | Location scoring vs profile preferred states | Parsed from job card or portal default | `Clayton` or `VIC` | **Mandatory** (often state-level only) |
| 6 | **State** | Australian state/territory abbreviation | Location filter (`AUSTRALIA_ONLY`); profile state preference matching | From portal config or parsed from location | `VIC` | **Mandatory** |
| 7 | **Salary** | Remuneration if published | User decision-making; future filtering | Scraped when available on listing | *(empty — 0/123 filled)* | Optional |
| 8 | **Posted Date** | When the job was advertised on portal | Freshness tracking; `DATE_FILTER_DAYS` (7-day window) | Parsed from listing or set to scrape date | `30-06-2026` | **Mandatory** |
| 9 | **Job Added On** | Timestamp when row was first written to Excel | Age-based Status (`Yet to apply` → `N days old`); follow-up logic | Set by `excel_manager.add_jobs()` at insert time (AEST) | `30-06-2026 21:27` | **Mandatory** |
| 10 | **Apply Link** | Direct URL to job detail or application page | Primary action link for user; dedup reference | Scraped href from portal; hyperlinked in Excel | `https://careers.monashhealth.org/job/Clayton-2027-...` | **Mandatory** |
| 11 | **Portal** | Source sheet / platform name | Traceability; filtering in consolidated views | Set to portal sheet name (e.g. `Monash_Health`) | `Monash_Health` | **Mandatory** |
| 12 | **Best Profile** | Highest-scoring demo doctor profile for this job | Personalised apply queue; Profile_Matches reference | From `job_validator.validate_job_against_profiles()` | `Dr. Priya Sharma` | **Mandatory** |
| 13 | **Match %** | 0–100 relevance score vs best profile | Apply queue ranking; High Match threshold (≥70) | Weighted: title 40%, specialty 25%, location 20%, experience 15% | `61` | **Mandatory** |
| 14 | **Extraction Method Used** | Scraper method that succeeded | Debugging portal failures; Phase 4 audit trail | Set by `extraction_runner.py` per job | `playwright` or `static_html` | **Mandatory** |
| 15 | **Method Reliability Note** | Human-readable note on extraction | Explains primary vs fallback method used | e.g. primary configured method vs fallback | `Primary — configured method` | **Mandatory** |
| 16 | **Validation Flags** | Quality warnings from validator | Surfaces weak matches without hiding jobs | Semicolon-separated flags from `job_validator` | `Weak title relevance; Specialty mismatch` | Optional (119/123 filled) |
| 17 | **Status** | Application lifecycle state | Track what needs action vs aged listings | Auto-updated: `Yet to apply`, `N days old`, `Applied`, `Expired` | `Yet to apply` | **Mandatory** |
| 18 | **Applied?** | User-entered application flag | Drives Status and excludes from Apply Queue when `Y` | Manual user input (`Y` / `Yes` / `Applied`) | *(empty — user fills)* | Optional |
| 19 | **Notes** | Free-text annotations | Validation flags copy; user comments; follow-up notes | Auto-populated from flags or manual | `Weak title relevance; Specialty mismatch` | Optional |

### Fill-rate summary (All_Jobs_Australia, n=123)

| Always filled | Often empty |
|---------------|-------------|
| Job Title, Hospital, Location, State, Posted Date, Job Added On, Apply Link, Portal, Best Profile, Match %, Extraction columns, Status | Salary (0%), Applied? (0%), Specialty (28% empty), Experience Level (17% empty) |

---

## Daily_Summary (7 columns)

Operational log — one row per portal per collector run. **96 rows** in current workbook.

| # | Column Name | Purpose | Why Required | How It Is Used | Example Value | Mandatory/Optional |
|---|-------------|---------|--------------|----------------|---------------|-------------------|
| 1 | **Run Date** | Date of collector run | Audit trail; correlate with Job Added On | `append_summary()` at run time | `30-06-2026` | **Mandatory** |
| 2 | **Run Time (AEST)** | Time of run (Australia/Sydney) | Distinguish multiple runs per day | HH:MM format | `21:27` | **Mandatory** |
| 3 | **Platform** | Portal sheet name | Identify which scraper ran | Matches portal tab name | `Monash_Health` | **Mandatory** |
| 4 | **Method** | Extraction method attempted | Compare static vs Playwright success | From portal config / extraction_runner | `playwright` | **Mandatory** |
| 5 | **New Jobs Found** | Jobs added this run | Measure scraper yield | Count from `add_jobs()` | `23` | **Mandatory** |
| 6 | **Total Jobs in Sheet** | Cumulative rows on portal tab | Track sheet growth over time | `sheet_job_count()` after run | `23` | **Mandatory** |
| 7 | **Errors?** | Error message or `No` | Diagnose failed portals | Exception text or `all_methods_failed` | `No` / `all_methods_failed` | **Mandatory** |

---

## Doctor_Profiles (7 columns)

Reference data for the 5 demo profiles in `data/profiles.json`. **5 rows.**

| # | Column Name | Purpose | Why Required | How It Is Used | Example Value | Mandatory/Optional |
|---|-------------|---------|--------------|----------------|---------------|-------------------|
| 1 | **Profile ID** | Internal profile key | Links to per-profile queue tabs (`Queue_dr_*`) | From `profiles.json` | `dr_og_registrar` | **Mandatory** |
| 2 | **Doctor Name** | Display name | Shown in Best Profile, queues, digest | From profiles.json | `Dr. Priya Sharma` | **Mandatory** |
| 3 | **Specialty** | Profile specialty | 25% of Match % scoring | `Obstetrics and Gynaecology` | **Mandatory** |
| 4 | **Experience Level** | Profile seniority | 15% of Match % scoring | `Registrar` | **Mandatory** |
| 5 | **Preferred States** | Where doctor wants to work | 20% location scoring | `Victoria, Queensland, New South Wales` | **Mandatory** |
| 6 | **Resume Source** | PDF/page reference | Documentation of demo data origin | `Demo_Medical_Resumes.pdf (page 1)` | **Mandatory** |
| 7 | **Last Updated** | Profile refresh date | Know when profiles were synced to Excel | Run date | `30-06-2026` | **Mandatory** |

---

## Profile_Matches (7 + N columns)

One row per job with scores against **every** profile. **123 rows.** Base columns + one `%` column per doctor.

| # | Column Name | Purpose | Why Required | How It Is Used | Example Value | Mandatory/Optional |
|---|-------------|---------|--------------|----------------|---------------|-------------------|
| 1 | **Job Title** | Job identifier | Row key for comparison | From portal tab | `Registrar - Medical Administration 2027` | **Mandatory** |
| 2 | **Portal** | Source portal | Filter by platform | Sheet name | `Careers_VIC` | **Mandatory** |
| 3 | **Hospital** | Employer | Context for user | From job row | `Victorian Government` | **Mandatory** |
| 4 | **State** | Job state | Location comparison | `VIC` | **Mandatory** |
| 5 | **Apply Link** | Application URL | Quick navigation | Full URL | `https://careers.vic.gov.au/job/...` | **Mandatory** |
| 6 | **Best Profile** | Top-matching profile name | Quick reference | Highest score profile | `Dr. Ananya Patel` | **Mandatory** |
| 7 | **Best Match %** | Top score | Rank jobs globally | Max of per-profile scores | `38` | **Mandatory** |
| 8+ | **Dr. [Name] %** | Per-profile score | Compare fit across all 5 demo doctors | `score_job_validation()` per profile | `33`, `17`, `38`, `16`, `15` | **Mandatory** (5 columns) |

---

## Apply_Queue (18 columns — config)

Top **20** jobs by Match % not yet applied. Defined in `config.APPLY_QUEUE_COLUMNS`.

| # | Column Name | Purpose | Why Required | How It Is Used | Example Value | Mandatory/Optional |
|---|-------------|---------|--------------|----------------|---------------|-------------------|
| 1 | **Rank** | Priority order (1 = best) | User applies top-down | Sorted by Match % descending | `1` | **Mandatory** |
| 2 | **Profile** | Best-matching doctor | Know who the job fits | From job row Best Profile | `Dr. Priya Sharma` | **Mandatory** |
| 3 | **Source Sheet** | Origin portal tab | Navigate back to source | Portal sheet name | `Grampians_Health` | **Mandatory** |
| 4 | **Job Title** | Vacancy title | Display | From job row | `Obstetrics & Gynaecology Registrar (Accredited)` | **Mandatory** |
| 5 | **Specialty** | Job specialty | Quick scan | From job row | `Obstetrics & Gynaecology` | Optional |
| 6 | **Experience Level** | Job level | Quick scan | From job row | `Registrar` | Optional |
| 7 | **Hospital** | Employer | Display | From job row | `Grampians Health` | **Mandatory** |
| 8 | **Location** | Location text | Display | From job row | `VIC` | **Mandatory** |
| 9 | **State** | State | Display / filter | `VIC` | **Mandatory** |
| 10 | **Apply Link** | Application URL | Primary action | Hyperlink | `https://careers.grampianshealth.com/job/...` | **Mandatory** |
| 11 | **Match %** | Relevance score | Ranking | Integer 0–100 | `67` | **Mandatory** |
| 12 | **Extraction Method Used** | How job was scraped | Debug data quality | `static_html` | **Mandatory** |
| 13 | **Method Reliability Note** | Extraction note | Audit trail | `Primary — configured method` | **Mandatory** |
| 14 | **Validation Flags** | Quality warnings | Avoid weak matches | From validator | `Fuzzy title match` | Optional |
| 15 | **Match Label** | Human-readable match tier | Quick visual tier | `High Match` / `Good Match` / `Low Match` | `Good Match` | **Mandatory** |
| 16 | **Status** | Application status | Exclude applied/expired | From job row | `Yet to apply` | **Mandatory** |
| 17 | **Applied?** | User application flag | User tracking | Manual | *(empty)* | Optional |
| 18 | **Notes** | Annotations | Extra context | From job row | `Fuzzy title match` | Optional |

> **Note:** The current workbook’s `Apply_Queue` header row may be **out of date** (missing Profile, Experience Level, and extraction columns). Data rows contain the full 18 fields — see `Excel_Improvements.md`.

---

## Per-Profile Queue Tabs (5 sheets)

`Queue_dr_og_registrar`, `Queue_dr_emergency_rmo`, `Queue_dr_paeds_registrar`, `Queue_dr_gen_med_consultant`, `Queue_dr_gen_med_pho`

Same **18 columns** as `Apply_Queue`, filtered to jobs where **Best Profile** matches that doctor. Up to **15 jobs** per profile.

| Sheet | Profile | Rows |
|-------|---------|------|
| Queue_dr_og_registrar | Dr. Priya Sharma | 13 |
| Queue_dr_emergency_rmo | Dr. James Chen | 15 |
| Queue_dr_paeds_registrar | Dr. Ananya Patel | 15 |
| Queue_dr_gen_med_consultant | Dr. Michael O'Brien | 15 |
| Queue_dr_gen_med_pho | Dr. Sarah Williams | 8 |

---

## Match Label Values

Derived from `Match %` via `resume_matcher.match_label()`:

| Match % Range | Label |
|---------------|-------|
| ≥ 70 | High Match |
| ≥ 50 | Good Match |
| ≥ 30 | Moderate Match |
| < 30 | Low Match |

Current workbook: **0 High Match** jobs (max Match % = 67; average = 30.4).

---

## Validation Flag Values

Common flags from `job_validator.py` (119/123 jobs have at least one):

| Flag | Meaning |
|------|---------|
| Weak title relevance | Job title poorly aligns with profile specialty/level |
| Specialty mismatch | Detected specialty does not match best profile |
| Experience level mismatch | Job level differs from profile level |
| Location mismatch | Job state not in profile preferred states |
| Below confidence threshold | Score under `VALIDATION_CONFIDENCE_THRESHOLD` (30) |

---

*Column definitions align with `config.py` and `excel_manager.py` as of 30 June 2026.*
