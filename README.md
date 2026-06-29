# Doctor / Medical Job Collector ù Australia

Fully automated daily job collector for doctors seeking Australia-only medical roles: Registrar, Senior Registrar, PHO, RMO, Consultant, and House Officer.

Non-Australian jobs (NZ, UK, USA, etc.) are automatically rejected.

Built on the same architecture as the [Java Backend Job Collector](../Umang-Gupta-Java-Backend-Job-Hunt-NCR) project.

## Platforms

| Category | Portals |
|----------|---------|
| **Government** | smartjobs.qld.gov.au, jobs.nt.gov.au, careers.vic.gov.au |
| **Hospitals** | Monash Health, Western Health, WA Health, Peninsula Health, The Women's, Grampians Health, Eastern Health, RCH, Mercy (Workday) |
| **Specialty Boards** | RANZCOG, RACP |
| **Aggregators** | australia.jobradars.com, PageUp-powered sites |

## Quick start

```bash
cd Doctor-Australia-Job-Collector
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
playwright install chromium
python job_collector.py
```

Edit `resume.txt` at the repo root to tune Match % scoring.

## Output ù `Job_Tracker.xlsx`

One tab per platform plus `Daily_Summary` and `Apply_Queue`.

| Column | Description |
|--------|-------------|
| Job Title | Role title |
| Specialty | Detected specialty (O&G, Paediatrics, etc.) |
| Hospital | Employer / health service |
| Location | City or region |
| State | QLD, VIC, WA, NT, NSW |
| Salary | If shown on listing |
| Posted Date | DD-MM-YYYY |
| Job Added On | When collector found it |
| Apply Link | Absolute URL |
| Match % | Resume match score (0ù100) |
| Status | Yet to apply / N days old / Applied / Expired |
| Applied? | Y when you've applied |
| Notes | High Match flag, etc. |

### Status logic

- **Yet to apply** ù new in today's run
- **1 day old / 2 days old** ù not yet applied
- **Applied** ù when Applied? = Y
- **Expired** ù job no longer on portal

## Resume matching

`resume_matcher.py` scores each job:

| Component | Weight |
|-----------|--------|
| Specialty | 40% |
| Location | 20% |
| Experience level | 20% |
| Keywords | 20% |

Match % ? 70 ? flagged as **High Match** in Excel and surfaced in the daily digest.

## Phase 2 ù daily digest

After each run, `phase2_processor.py` produces:

- **Apply Queue** ù unapplied jobs sorted by Match % (desc)
- **Follow-up list** ù applied jobs with no response after 7 days
- **Console digest** ù `Today: {N} new | {M} high match | Top picks: [...]`
- **logs/daily_digest.md** ù markdown summary

## Portal health

`portal_health.py` logs each portal: status, jobs found, errors.

After **3 consecutive runs with 0 jobs**, the portal is auto-disabled (logged in `logs/portal_health.json`).

## GitHub Actions

Runs daily at **8:00 AM AEST** (22:00 UTC):

1. Checkout ? Python 3.11 ? pip install ? Playwright Chromium
2. `python job_collector.py`
3. Commit `Job_Tracker.xlsx` + `logs/` ? push

Enable in your repo: **Settings ? Actions ? General ? Workflow permissions ? Read and write**.

## Scraping strategy

| Method | Portals |
|--------|---------|
| **Static HTML** (requests + BeautifulSoup) | Western Health, Peninsula Health, The Women's, Grampians, Eastern Health, RCH, RACP, JobRadars |
| **Playwright** (JS-rendered) | SmartJobs QLD, Jobs NT, Careers VIC, Monash Health, WA Health, RANZCOG |
| **Workday API** (POST JSON) | Mercy Health |
| **PageUp** | Sites with `/apply/{id}/aw/` links |

## Configuration

All settings live in `config.py` ù scrapers read from there only:

- `KEYWORDS`, `LOCATIONS`, `DATE_FILTER_DAYS`
- `PLATFORMS_TO_RUN` ù toggle any portal on/off
- `PORTAL_CONFIG` ù URLs, methods, sheet names

## File structure

```
job_collector.py
config.py
excel_manager.py
job_utils.py
resume_matcher.py
phase2_processor.py
portal_health.py
resume.txt
scrapers/
  govt_portals.py
  hospital_careers.py
  workday_scraper.py
  specialty_boards.py
  aggregators.py
data/target_hospitals.json
.github/workflows/job_collector.yml
requirements.txt
logs/
Job_Tracker.xlsx   (created on first run)
```

## Australia-only filtering

`config.py` sets `AUSTRALIA_ONLY = True`. Every job must pass:

1. **Reject** if text mentions non-AU countries (New Zealand, UK, USA, Canada, etc.)
2. **Accept** if apply link is an `.au` or trusted AU hospital/govt domain
3. **Accept** if location mentions an Australian state, city, or "Australia"

RACP and RANZCOG listings that only reference overseas hospitals are dropped. PageUp scraper uses **AU hospital sites only** (NSW, QLD, SA Health) ù not the global pageuppeople.com site.

## Rules

1. 2ù5 sec random delay between requests
2. Rotating User-Agent via `fake-useragent`
3. All dates ? DD-MM-YYYY
4. Apply links must be absolute URLs
5. Excel auto column width via openpyxl
6. One portal failing does not stop others
7. Every run logged to `logs/run_{date}.log`
8. Runs fully without user input

## License

Personal job-hunt automation ù use responsibly and respect portal terms of service.
