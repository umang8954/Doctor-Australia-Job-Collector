# Platform Extraction Strategy Report

Generated from `extraction_runner.py`, `logs/extraction_stats.json`, and Phase 1 diagnosis.

## Method Ranking Table

| Platform | Method 1 | Method 2 | Working? | Best Method | Worst Method | Reason Best | Reason Worst |
|----------|----------|----------|----------|-------------|--------------|-------------|--------------|
| SmartJobs_QLD | playwright | static/API | N | playwright | static | Only configured method; needs API/WAF bypass | Static blocked by WAF |
| Jobs_NT | playwright | static | N | playwright | static | SPA needs browser | Returns no results for current query |
| Careers_VIC | playwright | static | N | playwright | static | JS portal | 404 URL — both fail |
| Monash_Health | playwright | static | Y | playwright | static | 23 jobs via Playwright | Static returns empty shell |
| Western_Health | static | playwright | Y | static | playwright | Static HTML sufficient — 12 jobs | Playwright unnecessary |
| WA_Health | playwright | static | N | playwright | static | JS required | Wrong URL — page not found |
| Mercy_Workday | workday_api | mercury_html | N | mercury_html | workday_api | Mercy uses Mercury not Workday | 404 on configured Workday tenant |
| Peninsula_Health | static | playwright | N* | playwright | static | Playwright finds 8+ jobs (not yet default) | Static returns JS shell |
| The_Womens | static | successfactors | N | playwright | static | Real jobs on SuccessFactors | Timeout + wrong static URL |
| Grampians_Health | static | playwright | Y | static | playwright | Static works — 14 jobs | — |
| Eastern_Health | static | playwright | Y | static | playwright | Static works — 12 jobs | — |
| RCH | static | playwright | Partial | static | playwright | Static worked historically (7 stale rows) | Latest run: connect timeout |
| RANZCOG | playwright | static | N | playwright | static | When not 403, page has articles | 403 Forbidden intermittent |
| RACP | static | playwright | Y | static | playwright | Static HTML — 41 jobs | — |
| JobRadars | static | playwright | N | static_html | static | May work with browser | 403 bot block on HTTP |
| PageUp | pageup_html | playwright | N | pageup_html | pageup_html | JS PageUp sites need browser | Dead DNS + false-positive links |

## Per-Platform Narrative

See `phase1_missing_data_diagnosis.md` for detailed root-cause analysis.

**Auto-disabled portals (0):** 

Multi-method extraction is implemented in `extraction_runner.py`. Each run tries the configured
primary method, then a fallback (static ↔ Playwright). Results are logged to
`logs/extraction_stats.json`. Excel columns **Extraction Method Used** and
**Method Reliability Note** record which method succeeded per job.

## Recommendations

### Keep using
- **Static HTML** for Western Health, Grampians, Eastern Health, RACP
- **Playwright** for Monash Health
- **Multi-method fallback** chain (now automatic)

### Deprecate / replace
- **Mercy Workday API** → build Mercury scraper
- **JobRadars HTTP** → blocked; use direct hospital sources
- **PageUp link regex** on SA Health → false positives only

### Engineering investment
1. Peninsula Health — switch primary to Playwright (**low effort, high yield**)
2. Careers VIC — fix 404 URL
3. SmartJobs QLD — WAF bypass / API discovery
4. The Women's — SuccessFactors parser
5. Reset `portal_health.json` disabled list after fixes

