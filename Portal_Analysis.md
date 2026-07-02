# Portal Analysis — Job_Tracker.xlsx

**Workbook:** `Job_Tracker.xlsx`  
**Analysis date:** 30 June 2026  
**Data source:** Portal tabs, `All_Jobs_Australia`, `Daily_Summary`, `logs/portal_health.json`, `logs/extraction_stats.json`

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total portals configured | 16 |
| Portals with jobs in Excel | **9** (56%) |
| Portals with 0 jobs | **7** (44%) |
| Total jobs (`All_Jobs_Australia`) | **123** |
| Last collector run | 30-06-2026 21:27 AEST |

**Working portals** are returning apply links and populating their tabs. **Non-working portals** have empty tabs (headers only, 0 data rows) and `Daily_Summary` errors of `all_methods_failed` or HTTP-level failures.

---

## Portal Status Overview

| Portal Name | Sheet Tab | Jobs in Excel | Working Status | Config Method | Last Run Error |
|-------------|-----------|---------------|----------------|---------------|----------------|
| SmartJobs QLD | SmartJobs_QLD | 0 | **Not working** | Playwright | `all_methods_failed` |
| Jobs NT | Jobs_NT | 0 | **Not working** | Playwright | `all_methods_failed` |
| Careers VIC | Careers_VIC | 3 | Working (low yield) | Playwright | No |
| Monash Health | Monash_Health | 23 | Working | Playwright | No |
| Western Health | Western_Health | 16 | Working | Static | No |
| WA Health | WA_Health | 24 | Working | Playwright | No |
| Mercy Workday | Mercy_Workday | 0 | **Not working** | Mercury | `all_methods_failed` |
| Peninsula Health | Peninsula_Health | 0 | **Not working** | Playwright | `all_methods_failed` |
| The Women's | The_Womens | 1 | Working (low yield) | Static → Playwright fallback | No |
| Grampians Health | Grampians_Health | 14 | Working | Static | No |
| Eastern Health | Eastern_Health | 11 | Working | Static | No |
| RCH | RCH | 7 | Working | Static | No |
| RANZCOG | RANZCOG | 0 | **Not working** | Playwright | `all_methods_failed` |
| RACP | RACP | 24 | Working | Static | No |
| JobRadars | JobRadars | 0 | **Not working** | Static | `all_methods_failed` |
| PageUp (multi-site) | PageUp | 0 | **Not working** | PageUp | `all_methods_failed` |

---

## Non-Working Portals — Detailed Diagnosis

### 1. SmartJobs QLD

| Field | Detail |
|-------|--------|
| **Portal Name** | SmartJobs QLD (Queensland Government) |
| **Working Status** | Not working — 0 jobs |
| **Exact Reason** | **WAF / bot block + wrong fallback URL.** Playwright loads a small (~4.6 KB) error shell instead of search results; generic selectors find zero job cards. Static fallback hits **404** on `smartjobs.qld.gov.au/jobtools/search?keyword=medical+officer`. |
| **Evidence** | `extraction_stats.json`: Playwright 0 jobs; static 404. `portal_health.json`: `last_error: all_methods_failed`, `zero_streak: 2`. |
| **Recommended Fix** | Use longer Playwright wait (`networkidle`, scroll-to-load). Discover SmartJobs JSON/XHR API (Oracle/Taleo backend). Detect WAF block pages and log explicitly. Try AU residential IP or proxy if geo-blocked. Broaden keywords (`registrar`, `doctor`). |

---

### 2. Jobs NT

| Field | Detail |
|-------|--------|
| **Portal Name** | Jobs NT (Northern Territory Government) |
| **Working Status** | Not working — 0 jobs |
| **Exact Reason** | **No search results for current query + SPA DOM mismatch.** Portal returns “No Results Found” for `medical+officer`. Generic `parse_job_cards()` selectors (`.job-item`, `article`) do not match NT portal’s JavaScript-rendered layout. |
| **Evidence** | Both Playwright and static return 0 jobs. Page loads (~87 KB HTML) but no job cards parsed. `zero_streak: 2`. |
| **Recommended Fix** | Broaden search terms (`medical`, `doctor`, `registrar`) and use NT category filters. Inspect network tab for XHR/API endpoints. Build NT-specific parser. Manually verify whether medical jobs exist on portal before investing in pagination. |

---

### 3. Mercy Workday

| Field | Detail |
|-------|--------|
| **Portal Name** | Mercy Health (Mercy_Workday tab) |
| **Working Status** | Not working — 0 jobs |
| **Exact Reason** | **Mercury site timeout + invalid Workday fallback.** Primary Mercury URL (`mercyhealth.mercury.com.au/SearchResults.aspx`) times out after 24s. Workday API fallback targets wrong tenant (`mercyagedcare.wd105.myworkdayjobs.com`) and returns no jobs. |
| **Evidence** | `extraction_stats.json`: `ConnectTimeoutError` on Mercury; Workday API 0 jobs. Config still references aged-care Workday tenant. |
| **Recommended Fix** | Increase Mercury timeout and retries. Build dedicated Mercury ASP.NET parser with keyword search params. Remove or replace Workday fallback with correct Mercy Health tenant if one exists. Log API/HTTP status codes instead of swallowing errors. |

---

### 4. Peninsula Health

| Field | Detail |
|-------|--------|
| **Portal Name** | Peninsula Health |
| **Working Status** | Not working — 0 jobs (intermittent) |
| **Exact Reason** | **Intermittent Playwright failure + JS-rendered listings.** Earlier tests found 8–10 jobs with Playwright (8s wait); latest runs return 0 with both Playwright and static. Static HTTP returns JS shell without parseable cards. |
| **Evidence** | `extraction_stats.json` shows mixed history: Playwright 8 jobs in earlier runs, 0 in latest. Config method is `playwright` with 8s wait — may need longer wait or site is intermittently empty. |
| **Recommended Fix** | Increase `PORTAL_PLAYWRIGHT_WAIT_MS` to 10–12s. Add Peninsula-specific selectors. Retry on zero-result runs. Verify search URL `careers.peninsulahealth.org.au/search/?q=registrar` still returns listings manually. |

---

### 5. RANZCOG

| Field | Detail |
|-------|--------|
| **Portal Name** | RANZCOG (Royal Australian and New Zealand College of Obstetricians and Gynaecologists) |
| **Working Status** | Not working — 0 jobs |
| **Exact Reason** | **IP / bot blocking (403 Forbidden).** Static HTTP receives `403 Client Error: Forbidden`. Playwright also returns 0 jobs — likely blocked or parser cannot extract from blocked/minimal response. |
| **Evidence** | `extraction_stats.json`: static 403; Playwright 0 jobs. Intermittent — some runs load 82 KB with links, others get 144-byte 403 page. |
| **Recommended Fix** | Playwright with stealth settings and slower request rate. Dedicated RANZCOG DOM parser. Check for RSS/email job feed. Run from AU IP; avoid GitHub Actions datacenter IPs if consistently blocked. |

---

### 6. JobRadars

| Field | Detail |
|-------|--------|
| **Portal Name** | JobRadars Australia |
| **Working Status** | Not working — 0 jobs |
| **Exact Reason** | **Active bot blocking (403 Forbidden).** HTTP requests to `australia.jobradars.com/jobs?q=registrar+medical` are rejected. Playwright fallback also returns 0 jobs. |
| **Evidence** | Logged: `403 Client Error: Forbidden`. `zero_streak: 2`. |
| **Recommended Fix** | Playwright with full browser context and realistic headers. Consider deprecating aggregator in favour of direct hospital sources. If blocked from CI IPs, run JobRadars only from local/AU environment. |

---

### 7. PageUp (Multi-Site Aggregator)

| Field | Detail |
|-------|--------|
| **Portal Name** | PageUp — NSW / QLD / SA Health careers |
| **Working Status** | Not working — 0 jobs |
| **Exact Reason** | **Multi-site failures: dead DNS, 403, false-positive links.** Three configured URLs fail differently: `careers.slhd.nsw.gov.au` → **DNS resolution failure** (`ERR_NAME_NOT_RESOLVED`); `careers.health.qld.gov.au` → **403 Forbidden**; `careers.sahealth.sa.gov.au` → only login/job-alert links match apply regex, not real vacancies. |
| **Evidence** | `extraction_stats.json`: PageUp HTML 0 jobs; Playwright fails on SLHD DNS. `PAGEUP_AU_SEARCH_URLS` in `config.py`. Exceptions per-URL are silently skipped in scraper. |
| **Recommended Fix** | Replace dead SLHD URL with current NSW Health careers domain. Use Playwright for QLD/SA PageUp (JS-rendered). Tighten apply-link regex to exclude login forms. Add more PageUp AU hospitals from `data/target_hospitals.json`. Surface per-URL errors in `Daily_Summary`. |

---

## Working Portals — Notes

These portals populate Excel with valid apply links. Issues below are **yield/quality**, not total failure.

| Portal | Jobs | Notes |
|--------|------|-------|
| **Careers VIC** | 3 | URL fix worked; low count may reflect narrow keyword filter or few matching vacancies |
| **Monash Health** | 23 | Reliable Playwright extraction |
| **Western Health** | 16 | Static HTML sufficient |
| **WA Health** | 24 | Playwright after URL fix to `/jobs/search?q=registrar` |
| **The Women's** | 1 | Site migrated to SuccessFactors/jobs2web; Playwright fallback finds 1 job; static returns 0 |
| **Grampians Health** | 14 | Static HTML works |
| **Eastern Health** | 11 | Static HTML works |
| **RCH** | 7 | Static works; had connect timeouts in earlier runs (now recovered) |
| **RACP** | 24 | Static HTML on `racp.edu.au/about/all-medical-positions-vacant` |

---

## Cross-Cutting Issues Affecting Empty Portals

| Issue | Impact |
|-------|--------|
| Zero-job runs sometimes logged as success | Empty tabs with misleading `Errors?=No` in older runs |
| Generic `parse_job_cards()` parser | Fails on gov SPAs, SuccessFactors, Mercury, PageUp |
| No post-fetch validation | 404/WAF/block pages treated as valid empty HTML |
| `all_methods_failed` after primary + fallback | Both extraction methods exhausted with 0 jobs |
| Auto-disable after 3 zero streaks | Portals can be skipped until `reset_disabled_portals()` runs |
| GitHub Actions / datacenter IPs | Higher 403 rate on RANZCOG, JobRadars, SmartJobs |

---

## Priority Fix Matrix

| Priority | Portal | Effort | Expected Impact |
|----------|--------|--------|-----------------|
| 1 | Peninsula Health | Low | 8–10 jobs when Playwright wait stabilised |
| 2 | Jobs NT | Medium | NT government medical roles |
| 3 | Mercy Workday | Medium | Mercy Health VIC vacancies |
| 4 | SmartJobs QLD | High | Largest state employer portal |
| 5 | PageUp | High | NSW/QLD/SA public health jobs |
| 6 | RANZCOG | Medium–High | O&G specialty board listings |
| 7 | JobRadars | Medium | Aggregator; consider deprecating |

---

*Generated from analysis of `Job_Tracker.xlsx` and collector diagnostics.*
