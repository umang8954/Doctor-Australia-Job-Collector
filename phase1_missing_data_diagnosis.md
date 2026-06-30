# Phase 1: Missing Platform Data Diagnosis

**Workbook analysed:** `Job_Tracker.xlsx`  
**Analysis date:** 29-06-2026  
**Codebase version:** `master` @ post keyword-expansion push  
**Live diagnostics:** `logs/phase1_live_diag.txt` (generated 29-06-2026)

---

## Executive Summary

| Category | Count | Platform tabs |
|----------|-------|---------------|
| **Empty (0 rows)** | 10 | SmartJobs_QLD, Jobs_NT, Careers_VIC, WA_Health, Mercy_Workday, Peninsula_Health, The_Womens, RANZCOG, JobRadars, PageUp |
| **Partial / stale** | 1 | RCH (7 rows from earlier runs; latest fetch failed) |
| **Working** | 5 | Monash_Health (23), Western_Health (12), Grampians_Health (14), Eastern_Health (12), RACP (41) |
| **Consolidated** | 109 | All_Jobs_Australia |

**Critical cross-cutting finding:** 10 portals are **auto-disabled** in `logs/portal_health.json` after three consecutive zero-job runs. Even if scrapers are fixed, `job_collector.py` will **skip** them until they are re-enabled in portal health state.

```36:39:job_collector.py
        if is_portal_disabled(portal_key):
            logger.log(f"{portal_key}: skipped (auto-disabled - 0 jobs streak)")
            results[portal_key] = {"jobs": [], "error": "auto-disabled", "sheet": sheet, "method": method}
            continue
```

---

## Workbook Tab Inventory

| Tab | Data rows | Status | Config method | Scraper module |
|-----|-----------|--------|---------------|----------------|
| SmartJobs_QLD | 0 | Empty | playwright | `scrapers/govt_portals.py` |
| Jobs_NT | 0 | Empty | playwright | `scrapers/govt_portals.py` |
| Careers_VIC | 0 | Empty | playwright | `scrapers/govt_portals.py` |
| Monash_Health | 23 | OK | playwright | `scrapers/hospital_careers.py` |
| Western_Health | 12 | OK | static | `scrapers/hospital_careers.py` |
| WA_Health | 0 | Empty | playwright | `scrapers/hospital_careers.py` |
| Mercy_Workday | 0 | Empty | workday | `scrapers/workday_scraper.py` |
| Peninsula_Health | 0 | Empty | static | `scrapers/hospital_careers.py` |
| The_Womens | 0 | Empty | static | `scrapers/hospital_careers.py` |
| Grampians_Health | 14 | OK | static | `scrapers/hospital_careers.py` |
| Eastern_Health | 12 | OK | static | `scrapers/hospital_careers.py` |
| RCH | 7 | **Partial/stale** | static | `scrapers/hospital_careers.py` |
| RANZCOG | 0 | Empty | playwright | `scrapers/specialty_boards.py` |
| RACP | 41 | OK | static | `scrapers/specialty_boards.py` |
| JobRadars | 0 | Empty | static | `scrapers/aggregators.py` |
| PageUp | 0 | Empty | pageup | `scrapers/aggregators.py` |

Supporting tabs: `Daily_Summary` (48 run records), `Apply_Queue` (20), `Doctor_Profiles` (5), `All_Jobs_Australia` (109), `Profile_Matches` (109), five per-profile queue tabs.

---

## Problematic Platform Diagnoses

---

### 1. SmartJobs_QLD

**Root Cause:** Bot/WAF block page returned instead of job listings. Playwright receives a ~4.6 KB styled error shell, not search results. Generic CSS selectors find zero cards.

**Evidence:**
- Live diag: `html_len=4637`, `job_links=0`, empty title
- Scraper returns 0 raw jobs; `Daily_Summary` shows `Errors?=No` (failure is silent — no exception raised)
- Search URL: `https://smartjobs.qld.gov.au/jobs/search?keyword=medical+officer`
- Parser selectors in `govt_portals.py`: `.job-result`, `.search-result`, `article`, `.job-listing-item`

**Checked & ruled out:**
- Authentication/token expiry — public portal, no auth in code
- Pagination — never reached; zero HTML content to paginate
- Search parameter mismatch — secondary; page blocked before results load

**Recommended Fix:** **High** effort  
- Use longer Playwright wait + `networkidle` / scroll-to-load  
- Try SmartJobs JSON/API endpoints (many Oracle/Taleo backends expose XHR)  
- Rotate residential proxy or run from AU IP if geo-blocked  
- Surface WAF/block detection in logs (detect `message-wrapper` HTML pattern)  
- Reset `smartjobs_qld` in `portal_health.json` after fix

---

### 2. Jobs_NT

**Root Cause:** Portal search genuinely returns **“No Results Found”** for query `medical+officer`, AND generic parser does not target NT portal’s DOM (0 card selectors matched). Likely combination of empty result set + wrong selectors if jobs exist under different keywords.

**Evidence:**
- Live diag: `no_results=True`, `html_len=87484`, only 2 nav links (not job listings)
- `fetch` of `https://jobs.nt.gov.au/jobs?search=medical+officer` shows “No Results Found” in page text
- Scraper: `scrape_jobs_nt()` → `parse_job_cards()` with `.job-item`, `.search-results li`, `article`
- `portal_health.json`: `zero_streak=3`, auto-disabled

**Checked & ruled out:**
- Network errors — page loads successfully
- Rate limiting — no 403/429 observed

**Recommended Fix:** **Medium** effort  
- Broaden search terms (`medical`, `doctor`, `registrar`) and NT category filter (`Medical Officer` category exists in UI)  
- Inspect NT portal XHR/API for job search (likely SPA)  
- Add portal-specific parser for NT job rows  
- Verify whether jobs exist on portal manually before engineering pagination

---

### 3. Careers_VIC

**Root Cause:** **Deprecated/wrong search URL** — Playwright loads a **404 Page not found** page (`title_snippet: 404 - Page not found | Careers Vic`).

**Evidence:**
- Config URL: `https://careers.vic.gov.au/job-search?keyword=registrar` (404)
- Live diag: 6 links, all nav/how-to-apply — no job cards
- `parse_job_cards()` returns 0; logged as success with 0 jobs

**Recommended Fix:** **Low–Medium** effort  
- Find current Careers VIC job search URL (likely `/jobs` with different query params)  
- Update `PORTAL_CONFIG["careers_vic"]["search_url"]`  
- Add HTTP status / title validation after fetch to fail loudly on 404

---

### 4. WA_Health

**Root Cause:** **Wrong URL path + JS-rendered listings.** Playwright loads `medcareerswa.health.wa.gov.au/search/?q=registrar` which returns **“Page not found”** (title). Parser only finds nav links (`/jobs/search`, `/how-to-apply`).

**Evidence:**
- Live diag: `title_snippet: Page not found`, `card_selectors=0`
- Static fetch returns **403 Forbidden** (bot block on simple HTTP)
- Working hospitals (Monash) use same `parse_job_cards()` pattern — WA URL/platform differs

**Recommended Fix:** **Medium** effort  
- Correct base search URL (likely `/jobs/search` with proper query params)  
- Increase Playwright wait; add WA-specific selectors  
- Consider API endpoint if WA Health uses iCIMS/SuccessFactors backend

---

### 5. Mercy_Workday

**Root Cause:** **Wrong Workday tenant entirely** — configured API returns **404 Not Found**. Mercy Health Australia uses **Mercury** (`mercyhealth.mercury.com.au`), not `mercyagedcare.wd105.myworkdayjobs.com`.

**Evidence:**
- Live diag error: `404 Client Error: Not Found for url: .../mercyagedcare/MercyCare/jobs`
- Config in `config.py` lines 504–522 points to aged-care Workday tenant
- `workday_scraper.py` silently `continue`s on POST failure:

```28:31:scrapers/workday_scraper.py
        try:
            data = fetch_json_post(api_url, payload, session=session, label="mercy_workday")
        except Exception:  # noqa: BLE001
            continue
```

**Checked & ruled out:**
- Auth/token — endpoint does not exist (404), not an auth issue

**Recommended Fix:** **Medium** effort  
- Replace Workday scraper with Mercury ASP.NET scraper (`SearchResults.aspx`)  
- Or find correct Mercy Health hospital Workday tenant if separate from aged care  
- Stop swallowing exceptions — log API status codes

---

### 6. Peninsula_Health

**Root Cause:** **Wrong fetch method (static vs Playwright).** Jobs exist and parse correctly with Playwright; static HTTP returns JS shell without listings.

**Evidence:**
- Static: `html_len=52912`, `job_links=0`
- Playwright (8s wait): `html_len=91022`, **10 job links** e.g. `/job/2026-O&G-Un-accredited-Registrar-Sandringham/5136-en_GB`
- Manual test: `parse_job_cards()` on Playwright HTML → **8 jobs** parsed
- Config: `"method": "static"` but site requires JS (`hospital_careers.py` → `_scrape_static`)

**Recommended Fix:** **Low** effort  
- Change `peninsula_health` method to `playwright` in config  
- Increase `PLAYWRIGHT_WAIT_MS` to 8000+ for this portal  
- Reset auto-disable flag after fix

---

### 7. The_Womens

**Root Cause:** **Site migrated to SuccessFactors/jobs2web** + **intermittent network timeout**. Static scraper hits redirect shell; real jobs live on `theroyalwo.jobs2web.com` / SuccessFactors. Last run: **30s connect timeout**.

**Evidence:**
- `portal_health.json` last_error: `ConnectTimeoutError ... careers.thewomens.org.au timed out`
- Live diag (when reachable): redirects to `theroyalwo.jobs2web.com` and `career10.successfactors.com`
- Static HTML has 111 KB but no parseable job cards via current selectors
- `Daily_Summary` records timeout on 29-06-2026 20:16 run

**Recommended Fix:** **High** effort  
- Update URL to SuccessFactors/jobs2web search endpoint  
- Switch to Playwright with longer timeout (60s+)  
- Build SuccessFactors-specific parser (different DOM from PageUp static sites)  
- Add retry logic for transient timeouts

---

### 8. RANZCOG

**Root Cause:** **IP blocking (403 Forbidden)** on `jobs.ranzcog.edu.au` during automated access. When blocked, HTML is 144 bytes with title “403 Forbidden”. Custom parser never receives job content.

**Evidence:**
- Live diag: `html_len=144`, `title_snippet: 403 Forbidden`
- Earlier run (same day) got 82 KB with 45 links — **intermittent block**
- Parser in `specialty_boards.py` filters heavily (keywords + AU location on empty titles)
- Even when page loads, many `article` elements have empty link titles

**Recommended Fix:** **Medium–High** effort  
- Playwright with stealth / slower request rate  
- Fix parser for RANZCOG job board DOM (dedicated selectors)  
- Relax `_is_au_job()` if AU location in separate field  
- Consider RSS/email feed if RANZCOG offers one

---

### 9. JobRadars

**Root Cause:** **403 Forbidden — active bot blocking** on `australia.jobradars.com`.

**Evidence:**
- Exception raised and logged: `403 Client Error: Forbidden`
- `Daily_Summary` correctly shows error text
- `portal_health.json`: `zero_streak=3`, disabled

**Recommended Fix:** **Medium** effort  
- Switch to Playwright with browser context  
- Use alternate aggregator or direct hospital sources  
- Deprecate if consistently blocked from CI/GitHub Actions IPs

---

### 10. PageUp

**Root Cause:** **Multi-site failures + false-positive link matching.** Three configured AU URLs: one DNS dead, one 403, one returns only login/alert links matching `/apply/\d+/aw/` regex — not actual job listings.

**Evidence:**
- `PAGEUP_AU_SEARCH_URLS` in `config.py`:
  - `careers.slhd.nsw.gov.au` → **DNS resolution failure**
  - `careers.health.qld.gov.au` → **403 Forbidden**
  - `careers.sahealth.sa.gov.au` → 3 apply links, all `apply/532/aw/applicationForm` (job alert/login, not vacancies)
- `scrape_pageup()` silently `continue`s on per-URL exceptions:

```66:69:scrapers/aggregators.py
        try:
            html = fetch_html(url, label="pageup")
        except Exception:  # noqa: BLE001
            continue
```

**Recommended Fix:** **High** effort  
- Replace dead SLHD URL; find current NSW Health careers domain  
- Use Playwright for QLD/SA PageUp sites (JS-rendered listings)  
- Tighten apply-link regex to exclude login forms (e.g. require job title in parent card)  
- Add NSW Health, ACT Health, other PageUp AU hospitals from `target_hospitals.json`

---

### 11. RCH (Partial / Stale Data)

**Root Cause:** **Connect timeout on latest run** — tab retains **7 jobs from earlier successful runs** but is not refreshing.

**Evidence:**
- Workbook: 7 data rows on RCH tab
- Last `Daily_Summary` entry: 0 new jobs, error = `ConnectTimeoutError ... careers.rch.org.au timed out`
- `portal_health.json`: `zero_streak=1` (not yet disabled)
- Same static method as working Western Health / Grampians — likely transient network or site downtime, not selector breakage

**Recommended Fix:** **Low–Medium** effort  
- Add retry with backoff in `fetch_html()`  
- Increase timeout from 30s to 60s  
- Mark stale rows in Excel when fetch fails (status = “Source unreachable”)  
- Monitor — if timeouts persist, investigate RCH CDN/firewall

---

## Cross-Cutting Code Issues

| Issue | Location | Impact |
|-------|----------|--------|
| Zero-job runs logged as success | `job_collector.py` + `portal_health.py` | Empty tabs with no error in Daily_Summary |
| Exceptions swallowed | `aggregators.py`, `workday_scraper.py` | Failures invisible except in debug |
| Generic `parse_job_cards()` | `scrapers/base.py` | Fails on non-standard DOM (govt SPAs, SuccessFactors) |
| No pagination | All scrapers (`return jobs[:50]`) | Caps at 50; not root cause of zero-data tabs |
| Auto-disable after 3 zeros | `portal_health.py` | 10 portals currently skipped on every run |
| No post-fetch validation | `fetch_with_playwright()` | 404/block pages treated as valid HTML |
| Double filtering | Scrapers `_score_jobs()` + `passes_filters()` in collector | Jobs dropped twice; can reduce yield on edge cases |

---

## Priority Fix Matrix

| Priority | Platform | Fix | Effort |
|----------|----------|-----|--------|
| 1 | Peninsula_Health | Switch static → Playwright | **Low** |
| 2 | Careers_VIC | Update 404 search URL | **Low** |
| 3 | Mercy_Workday | Replace with Mercury scraper | **Medium** |
| 4 | Jobs_NT | New search params + NT parser | **Medium** |
| 5 | WA_Health | Fix URL + Playwright selectors | **Medium** |
| 6 | SmartJobs_QLD | Bypass WAF / find API | **High** |
| 7 | PageUp | Fix URLs, Playwright, link filter | **High** |
| 8 | The_Womens | SuccessFactors URL + parser | **High** |
| 9 | RANZCOG | Anti-bot + dedicated parser | **Medium–High** |
| 10 | JobRadars | Playwright or deprecate | **Medium** |
| 11 | RCH | Retry/timeout (stale data) | **Low** |

**Before any fix:** Clear or reset `disabled` list in `logs/portal_health.json` for portals being repaired, or set `AUTO_DISABLE_DEAD_PORTALS = False` during testing.

---

## Phase 1 Completion Notes

- **Working platforms** (Monash, Western, Grampians, Eastern, RACP) use URLs and fetch methods that still match live site behaviour; generic parser + keyword filter produce data.
- **Empty platforms** fail for distinct reasons — there is no single bug; fixes are per-portal.
- **Phase 2 prerequisite:** Clarify that current “Best Profile” matching is **job-to-demo-profile** scoring (specialty/location/keywords), **not** doctor registry identity matching — no license numbers are available from these job boards.

---

*End of Phase 1 report. Proceed to Phase 2 only after review.*
