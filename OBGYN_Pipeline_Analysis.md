# OBGYN Job Tracker Pipeline — Analysis & Fixes

Root-cause analysis of why jobs/application links from the client's reference file (`Book1.xlsx`, 26 rows / 22 distinct jobs) were missing from the generated `OBGYN_Job_Tracker.xlsx`, and the scraper fixes applied to close the gaps.

## Method

1. Read both files dynamically by header content, not fixed column position — `Book1.xlsx` has no header row (title, tag, URL), `OBGYN_Job_Tracker.xlsx` uses the 15-column `SHEET_COLUMNS` schema. Matching logic: exact URL → portal-specific job ID (regex per ATS type) → exact/substring title within the same domain. Each tracker row can match only one Book1 row, to avoid one popular title (e.g. "Obstetrics and Gynaecology Registrar") silently absorbing several distinct postings.
2. For every unmatched Book1 row, fetched the live URL directly (not just the search page) to tell apart two very different failure modes: **the scraper is broken** vs. **the job has since closed/expired** (the latter is not fixable by scraping — the client's reference file is simply older than the current run).

## Root causes found and fixed

| # | Portal | Root cause | Fix |
|---|--------|-----------|-----|
| 1 | RANZCOG (`jobs.ranzcog.edu.au`) | AJAX pagination only fetched pages 2–7 and aborted on the *first* failed page (incl. transient 403s) | Extended to pages 2–14; only stops after 2 consecutive empty/failed pages ([specialty_boards.py](scrapers/specialty_boards.py)) |
| 2 | NT Government Jobs | URL built as `/Home/JobDetails/{id}` but the live site requires `/Home/JobDetails?rtfId={id}` — every NT link in the tracker was a 404 | Fixed URL construction ([portal_parsers.py](scrapers/portal_parsers.py)) |
| 3 | NT Government Jobs | Search keyword list (`medical, doctor, registrar, health`) never surfaced the O&G-specific postings — the site's own search paginates per keyword and these fell outside the returned set | Added `obstetrics`, `gynaecology`, `o&g` to `JOBS_NT_SEARCH_KEYWORDS` ([config.py](config.py)) |
| 4 | Careers VIC | Only one URL variant (no `www.` prefix) was tried, and the page wasn't scrolled — the job grid lazy-loads on scroll | Added `www.` URL fallback, `scroll=True`, and a raw-link fallback parser ([govt_portals.py](scrapers/govt_portals.py)) |
| 5 | GV Health, AWH, ACT Health | Not configured/scraped at all — no portal entry existed | Added all three to `PORTAL_CONFIG` / `PLATFORMS_TO_RUN` and wrote scraper functions ([config.py](config.py), [hospital_careers.py](scrapers/hospital_careers.py)) |
| 6 | ACT Health (Taleo ATS) | Even with Playwright, generic selectors returned 0 job links — Taleo renders results into a table via an internal AJAX call the generic parser doesn't submit a keyword to | Added a dedicated keyword-search flow against Taleo's real search form |
| 7 | `wave.com.au` | Not a configured portal at all (client had a job sourced from it) | Added as a new portal |
| 8 | `config.KEYWORDS` specialty list | Only contained noun forms (`obstetrics`, `gynaecology`) — adjective/agent forms used in real titles (`Obstetrician`, `Gynaecologist`, `Obstetric`) are **not substrings** of those words, so many legitimately relevant titles silently failed the keyword filter | Broadened the O&G terms to also match `obstetric`, `gynaecol` (root forms) |

## Confirmed NOT scraper bugs (verified live, independent of our code)

Checked directly against the live job pages (not just search results):

- **AWH** — both Book1 O&G registrar postings return `"Sorry, this position has been filled."` on their own job page. Confirmed absent from AWH's full paginated listing (all 43 live jobs enumerated via the site's `startrow` pagination). Genuinely closed.
- **RANZCOG job 1576** — direct fetch returns HTTP 404 (removed from the board).
- **RANZCOG job 1571** — direct fetch returns HTTP 403 and is absent from all 14 pages of the current board listing (19 live jobs total, enumerated in full).
- **Careers VIC job 74012** — direct fetch returns HTTP 403 with `og:title: "Sorry, this job has closed"`.
- **QLD Springboard** (`apply-springboard.health.qld.gov.au`) — distinct micro-site from the working `smartjobs.qld.gov.au`; the specific posting is no longer present.

These 8 jobs cannot be recovered by fixing scraping logic — they were live when the client compiled `Book1.xlsx` and have since closed. This is expected pipeline behavior (the tracker should reflect *current* postings, not stale ones).

## Remaining known gaps (not yet automated)

- `au.workus.org` and `www.livehire.com` — each supplied exactly one Book1 job; both sites are still live but have no dedicated scraper written yet (single-source aggregator/ATS mirrors, low reuse value per portal added).
- One NSW Health posting ("Trainee - Unaccredited Position") whose title contains no O&G/registrar keyword at all — it only reads as relevant via the client's own domain knowledge, not extractable from the text itself.

## Result

Book1: 26 rows → **22 distinct jobs** after removing duplicate re-postings of the same listing via different lead sources.

| Outcome | Count |
|---|---|
| Matched directly (exact URL or job ID) | 8 |
| Matched via an alternate valid URL for the same posting | 3 |
| Confirmed closed/expired (verified live, unfixable) | 8 |
| Genuine remaining gaps | 3 |
| **Effective coverage** | **19 / 22 (86%)** |

Final tracker: 106 unique jobs (`OBGYN_Job_Tracker.xlsx`).

## Changed files

- [config.py](config.py) — new portal configs, expanded NT keywords, broadened O&G keyword roots
- [obgyn_collector.py](obgyn_collector.py) — 15-column schema, new targeted searches, dedup on `Apply Link`
- [scrapers/specialty_boards.py](scrapers/specialty_boards.py) — RANZCOG pagination
- [scrapers/portal_parsers.py](scrapers/portal_parsers.py) — NT URL format, RANZCOG parse limit
- [scrapers/hospital_careers.py](scrapers/hospital_careers.py) — GV Health, AWH, ACT Health scrapers
- [scrapers/govt_portals.py](scrapers/govt_portals.py) — Careers VIC fallback URL + scroll
