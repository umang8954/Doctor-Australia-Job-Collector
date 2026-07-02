"""

Configuration for the daily Doctor/Medical Job Collector - Australia.

Single source of truth - scrapers must read values from here only.

"""

from pathlib import Path
from urllib.parse import urlparse

# --- Search profile ---
# Jobs are collected when title/description contains ANY of these (case-insensitive).

KEYWORDS = [
    # Experience / role level
    "medical officer",
    "resident doctor",
    "junior doctor",
    "registrar",
    "senior registrar",
    "consultant",
    "general practitioner",
    "gp",
    "resident medical officer",
    "rmo",
    "house officer",
    "pho",
    "principal house officer",
    "jmo",
    "junior medical officer",
    "intern",
    "fellow",
    "staff specialist",
    # Specialties
    "general physician",
    "internal medicine",
    "emergency medicine",
    "icu",
    "intensive care",
    "critical care",
    "general surgery",
    "orthopaedics",
    "orthopedics",
    "cardiology",
    "cardiologist",
    "neurology",
    "neurologist",
    "oncology",
    "oncologist",
    "anaesthesia",
    "anaesthetics",
    "anesthetics",
    "radiology",
    "psychiatry",
    "paediatrics",
    "pediatrics",
    "obstetrics & gynaecology",
    "obstetrics and gynaecology",
    "obstetrics",
    "gynaecology",
    "gynecology",
    "o&g",
    "dermatology",
    "ophthalmology",
    "ent",
    "otolaryngology",
    "urology",
    "gastroenterology",
    "nephrology",
    "pulmonology",
    "respiratory medicine",
    "endocrinology",
    "pathology",
    "general medicine",
    "general practice",
]

# Longest phrases first — used for Excel Specialty column (canonical display names).
SPECIALTY_RULES: list[tuple[str, str]] = [
    ("obstetrics & gynaecology", "Obstetrics & Gynaecology"),
    ("obstetrics and gynaecology", "Obstetrics & Gynaecology"),
    ("obstetrics and gynecology", "Obstetrics & Gynaecology"),
    ("emergency medicine", "Emergency Medicine"),
    ("internal medicine", "Internal Medicine"),
    ("general physician", "General Physician"),
    ("general practitioner", "General Practitioner (GP)"),
    ("general practice", "General Practitioner (GP)"),
    ("general surgery", "General Surgery"),
    ("general medicine", "Internal Medicine"),
    ("intensive care", "ICU"),
    ("critical care", "ICU"),
    ("respiratory medicine", "Pulmonology"),
    ("otolaryngology", "ENT"),
    ("orthopaedics", "Orthopaedics"),
    ("orthopedics", "Orthopaedics"),
    ("gastroenterology", "Gastroenterology"),
    ("endocrinology", "Endocrinology"),
    ("ophthalmology", "Ophthalmology"),
    ("anaesthetics", "Anaesthesia"),
    ("anesthetics", "Anaesthesia"),
    ("anaesthesia", "Anaesthesia"),
    ("paediatrics", "Paediatrics"),
    ("pediatrics", "Paediatrics"),
    ("gynaecology", "Obstetrics & Gynaecology"),
    ("gynecology", "Obstetrics & Gynaecology"),
    ("obstetrics", "Obstetrics & Gynaecology"),
    ("o&g", "Obstetrics & Gynaecology"),
    ("cardiology", "Cardiology"),
    ("cardiologist", "Cardiology"),
    ("neurology", "Neurology"),
    ("neurologist", "Neurology"),
    ("oncology", "Oncology"),
    ("oncologist", "Oncology"),
    ("radiology", "Radiology"),
    ("psychiatry", "Psychiatry"),
    ("psychiatrist", "Psychiatry"),
    ("dermatology", "Dermatology"),
    ("dermatologist", "Dermatology"),
    ("gastroenterology", "Gastroenterology"),
    ("nephrology", "Nephrology"),
    ("pulmonology", "Pulmonology"),
    ("pathology", "Pathology"),
    ("urology", "Urology"),
    ("ent", "ENT"),
    ("icu", "ICU"),
]

SPECIALTY_KEYWORDS = [phrase for phrase, _ in SPECIALTY_RULES]

# Longest phrases first — used for Excel Experience Level column.
EXPERIENCE_RULES: list[tuple[str, str]] = [
    ("senior registrar", "Senior Registrar"),
    ("principal house officer", "PHO"),
    ("resident medical officer", "Resident Doctor"),
    ("junior medical officer", "Junior Doctor"),
    ("resident doctor", "Resident Doctor"),
    ("junior doctor", "Junior Doctor"),
    ("medical officer", "Medical Officer"),
    ("house officer", "House Officer"),
    ("staff specialist", "Consultant"),
    ("general practitioner", "General Practitioner (GP)"),
    ("registrar", "Registrar"),
    ("consultant", "Consultant"),
    ("fellow", "Fellow"),
    ("intern", "Intern"),
    ("rmo", "Resident Doctor"),
    ("pho", "PHO"),
    ("jmo", "Junior Doctor"),
]

EXPERIENCE_LEVEL_KEYWORDS = [phrase for phrase, _ in EXPERIENCE_RULES]

STATE_ABBREVS = {

    "queensland": "QLD",

    "victoria": "VIC",

    "western australia": "WA",

    "northern territory": "NT",

    "new south wales": "NSW",

    "south australia": "SA",

    "tasmania": "TAS",

    "australian capital territory": "ACT",

}


# --- Australia-only filter (jobs must be in Australia) ---
AUSTRALIA_ONLY = True

AU_LOCATIONS = [
    "Queensland",
    "Victoria",
    "Western Australia",
    "Northern Territory",
    "New South Wales",
    "South Australia",
    "Tasmania",
    "Australia",
    "Australian Capital Territory",
]

LOCATIONS = AU_LOCATIONS  # Australia only

AU_LOCATION_KEYWORDS = [
    "australia",
    "australian",
    "queensland",
    "victoria",
    "western australia",
    "northern territory",
    "new south wales",
    "south australia",
    "tasmania",
    "nsw",
    "vic",
    "qld",
    "wa",
    "nt",
    "sa",
    "tas",
    "act",
    "sydney",
    "melbourne",
    "brisbane",
    "perth",
    "adelaide",
    "hobart",
    "darwin",
    "canberra",
    "gold coast",
    "geelong",
    "ballarat",
    "bendigo",
    "sunshine coast",
    "cairns",
    "townsville",
    "newcastle",
    "wollongong",
    "toowoomba",
    "rockhampton",
    "launceston",
    "mackay",
    "bundaberg",
]

NON_AU_LOCATION_KEYWORDS = [
    "new zealand",
    " nz",
    "nz ",
    "auckland",
    "wellington",
    "christchurch",
    "united kingdom",
    " uk",
    "uk ",
    "london",
    "england",
    "scotland",
    "wales",
    "united states",
    " u.s.",
    " usa",
    "usa ",
    "america",
    "california",
    "texas",
    "canada",
    "toronto",
    "vancouver",
    "montreal",
    "singapore",
    "malaysia",
    "india",
    "mumbai",
    "ireland",
    "dublin",
    "hong kong",
    "papua new guinea",
    "fiji",
    "samoa",
    "overseas",
    "international posting",
]

AU_DOMAIN_SUFFIXES = (".au", ".gov.au", ".edu.au", ".org.au", ".asn.au")

PAGEUP_AU_SEARCH_URLS = [
    {
        "url": "https://jobs.health.nsw.gov.au/jobs/search?q=registrar+medical",
        "method": "static",
        "hospital": "NSW Health",
        "state": "NSW",
        "parser": "nsw_health",
    },
    {
        "url": "https://careers.health.qld.gov.au/search/?q=registrar",
        "method": "playwright",
        "hospital": "Queensland Health",
        "state": "QLD",
        "parser": "qld_health",
    },
    {
        "url": "https://careers.sahealth.sa.gov.au/caw/en/listing/?search-keyword=registrar+medical",
        "method": "static",
        "hospital": "SA Health",
        "state": "SA",
        "parser": "pageup_sa",
    },
]

SMARTJOBS_SEARCH_URL = (
    "https://smartjobs.qld.gov.au/jobtools/jncustomsearch.jobsearch?in_organid=14904"
)
SMARTJOBS_SEARCH_KEYWORDS = ["registrar", "medical officer", "doctor"]

JOBS_NT_SEARCH_KEYWORDS = ["medical", "doctor", "registrar", "health"]

PORTAL_ZERO_STREAK_DISABLE = 3

AUTO_DISABLE_DEAD_PORTALS = True

# Skip JobRadars on CI/datacenter IPs where 403 is common
JOBRADARS_SKIP_IN_CI = True
RANZCOG_USE_STEALTH = True
PORTAL_ZERO_RETRY_ON_ZERO = True

DATE_FILTER_DAYS = 7

HIGH_MATCH_THRESHOLD = 70

# --- Validation (Phases 2 & 3) ---
# Job boards do not expose doctor license numbers; experience level used instead.
VALIDATION_WEIGHTS = {
    "title_relevance": 0.40,
    "specialty": 0.25,
    "location": 0.20,
    "experience": 0.15,
}

VALIDATION_CONFIDENCE_THRESHOLD = 30  # 0–100; jobs below this are flagged

VALIDATION_FILTER_BELOW_THRESHOLD = False  # True = drop jobs below threshold

FOLLOW_UP_AFTER_DAYS = 7

# --- Paths ---

REPO_ROOT = Path(__file__).resolve().parent

EXCEL_FILE_PATH = str(REPO_ROOT / "Job_Tracker.xlsx")
PROFILE_PDF = REPO_ROOT / "data" / "Demo_Medical_Resumes.pdf"
PROFILES_JSON = REPO_ROOT / "data" / "profiles.json"
RESUME_FILE = REPO_ROOT / "resume.txt"

LOGS_DIR = REPO_ROOT / "logs"

TARGET_HOSPITALS_FILE = REPO_ROOT / "data" / "target_hospitals.json"

DIGEST_FILE = LOGS_DIR / "daily_digest.md"

AEST_TIMEZONE = "Australia/Sydney"

# --- Scraping ---

REQUEST_DELAY_MIN = 2.0

REQUEST_DELAY_MAX = 5.0

MAX_RETRIES = 3

RETRY_DELAY_SECONDS = 5

PLAYWRIGHT_WAIT_MS = 4000

PORTAL_PLAYWRIGHT_WAIT_MS = {
    "peninsula_health": 12000,
    "wa_health": 8000,
    "careers_vic": 6000,
    "jobs_nt": 10000,
    "smartjobs_qld": 10000,
    "ranzcog": 10000,
    "jobradars": 10000,
    "mercy_workday": 15000,
}

# --- Excel ---

SHEET_COLUMNS = [
    "Job Title",
    "Specialty",
    "Experience Level",
    "Hospital",
    "Location",
    "State",
    "Salary",
    "Posted Date",
    "Job Added On",
    "Apply Link",
    "Portal",
    "Best Profile",
    "Match %",
    "Status",
    "Applied?",
]

DAILY_SUMMARY_SHEET = "Daily_Summary"
PROFILES_SHEET = "Doctor_Profiles"
ALL_JOBS_SHEET = "All_Jobs_Australia"
PROFILE_MATCHES_SHEET = "Profile_Matches"

SUMMARY_COLUMNS = [
    "Run Date",
    "Run Time (AEST)",
    "Platform",
    "Method",
    "Raw Jobs",
    "New Jobs Found",
    "Total Jobs in Sheet",
    "Duration (s)",
    "Errors?",
]

APPLY_QUEUE_SHEET = "Apply_Queue"

PROFILES_COLUMNS = [
    "Profile ID",
    "Doctor Name",
    "Specialty",
    "Experience Level",
    "Preferred States",
    "Resume Source",
    "Last Updated",
]

PROFILE_MATCHES_COLUMNS = [
    "Job Title",
    "Portal",
    "Hospital",
    "State",
    "Apply Link",
    "Best Profile",
    "Best Match %",
]

ALL_JOBS_COLUMNS = SHEET_COLUMNS

APPLY_QUEUE_COLUMNS = [
    "Rank",
    "Profile",
    "Source Sheet",
    "Job Title",
    "Specialty",
    "Experience Level",
    "Hospital",
    "Location",
    "State",
    "Apply Link",
    "Match %",
    "Match Label",
    "Status",
    "Applied?",
]

STATUS_NEW = "Yet to apply"

STATUS_APPLIED = "Applied"

STATUS_EXPIRED = "Expired"

# --- Platform toggles ---

PLATFORMS_TO_RUN = {

    "smartjobs_qld": True,

    "jobs_nt": True,

    "careers_vic": True,

    "monash_health": True,

    "western_health": True,

    "wa_health": True,

    "mercy_workday": True,

    "peninsula_health": True,

    "the_womens": True,

    "grampians_health": True,

    "eastern_health": True,

    "rch": True,

    "ranzcog": True,

    "racp": True,

    "jobradars": True,

    "pageup": True,

}

# --- Portal definitions (URLs, methods, sheet names) ---

PORTAL_CONFIG = {

    "smartjobs_qld": {

        "sheet": "SmartJobs_QLD",

        "base_url": "https://smartjobs.qld.gov.au",

        "search_url": "https://smartjobs.qld.gov.au/jobtools/jncustomsearch.jobsearch?in_organid=14904",

        "method": "playwright",

        "state": "QLD",

        "hospital": "Queensland Health",

    },

    "jobs_nt": {

        "sheet": "Jobs_NT",

        "base_url": "https://jobs.nt.gov.au",

        "search_url": "https://jobs.nt.gov.au/Home/Search",

        "method": "playwright",

        "state": "NT",

        "hospital": "NT Government",

    },

    "careers_vic": {

        "sheet": "Careers_VIC",

        "base_url": "https://careers.vic.gov.au",

        "search_url": "https://careers.vic.gov.au/jobs?keywords=registrar+medical",

        "method": "playwright",

        "state": "VIC",

        "hospital": "Victorian Government",

    },

    "monash_health": {

        "sheet": "Monash_Health",

        "base_url": "https://careers.monashhealth.org",

        "search_url": "https://careers.monashhealth.org/search/?q=registrar",

        "method": "playwright",

        "state": "VIC",

        "hospital": "Monash Health",

    },

    "western_health": {

        "sheet": "Western_Health",

        "base_url": "https://careers.wh.org.au",

        "search_url": "https://careers.wh.org.au/search/?q=medical+officer",

        "method": "static",

        "state": "VIC",

        "hospital": "Western Health",

    },

    "wa_health": {

        "sheet": "WA_Health",

        "base_url": "https://medcareerswa.health.wa.gov.au",

        "search_url": "https://medcareerswa.health.wa.gov.au/jobs/search?q=registrar",

        "method": "playwright",

        "state": "WA",

        "hospital": "WA Health",

    },

    "mercy_workday": {

        "sheet": "Mercy_Workday",

        "base_url": "https://mercyhealth.mercury.com.au",

        "search_url": "https://mercyhealth.mercury.com.au/SearchResults.aspx?Keywords=registrar",

        "method": "mercury",

        "state": "VIC",

        "hospital": "Mercy Health",

        "tenant": "mercyagedcare",

        "site": "External",

        "workday_fallback_url": "https://mercyagedcare.wd105.myworkdayjobs.com",

        "mercury_timeout": 60,

    },

    "peninsula_health": {

        "sheet": "Peninsula_Health",

        "base_url": "https://careers.peninsulahealth.org.au",

        "search_url": "https://careers.peninsulahealth.org.au/search/?q=registrar",

        "method": "playwright",

        "state": "VIC",

        "hospital": "Peninsula Health",

    },

    "the_womens": {

        "sheet": "The_Womens",

        "base_url": "https://careers.thewomens.org.au",

        "search_url": "https://careers.thewomens.org.au/search/?q=registrar",

        "method": "static",

        "state": "VIC",

        "hospital": "The Royal Women's Hospital",

    },

    "grampians_health": {

        "sheet": "Grampians_Health",

        "base_url": "https://careers.grampianshealth.com",

        "search_url": "https://careers.grampianshealth.com/search/?q=medical+officer",

        "method": "static",

        "state": "VIC",

        "hospital": "Grampians Health",

    },

    "eastern_health": {

        "sheet": "Eastern_Health",

        "base_url": "https://careers.easternhealth.org.au",

        "search_url": "https://careers.easternhealth.org.au/search/?q=registrar",

        "method": "static",

        "state": "VIC",

        "hospital": "Eastern Health",

    },

    "rch": {

        "sheet": "RCH",

        "base_url": "https://careers.rch.org.au",

        "search_url": "https://careers.rch.org.au/search/?q=registrar",

        "method": "static",

        "state": "VIC",

        "hospital": "Royal Children's Hospital",

    },

    "ranzcog": {

        "sheet": "RANZCOG",

        "base_url": "https://jobs.ranzcog.edu.au",

        "search_url": "https://jobs.ranzcog.edu.au/jobs",

        "method": "playwright",

        "state": "Australia",

        "hospital": "RANZCOG",

    },

    "racp": {

        "sheet": "RACP",

        "base_url": "https://www.racp.edu.au",

        "search_url": "https://www.racp.edu.au/about/all-medical-positions-vacant",

        "method": "static",

        "state": "Australia",

        "hospital": "RACP",

    },

    "jobradars": {

        "sheet": "JobRadars",

        "base_url": "https://australia.jobradars.com",

        "search_url": "https://australia.jobradars.com/jobs?q=registrar+medical",

        "method": "playwright",

        "state": "Australia",

        "hospital": "",

    },

    "pageup": {

        "sheet": "PageUp",

        "base_url": "https://jobs.health.nsw.gov.au",

        "search_url": "https://jobs.health.nsw.gov.au/jobs/search?q=registrar+medical",

        "method": "pageup",

        "state": "Australia",

        "hospital": "",

    },

}



def _portal_hosts():
    hosts = set()
    for cfg in PORTAL_CONFIG.values():
        url = cfg.get("base_url", "")
        host = urlparse(url).netloc
        if host:
            hosts.add(host)
    for entry in PAGEUP_AU_SEARCH_URLS:
        url = entry["url"] if isinstance(entry, dict) else entry
        host = urlparse(url).netloc
        if host:
            hosts.add(host)
    return sorted(hosts)


AU_TRUSTED_PORTAL_HOSTS = _portal_hosts()
AU_TRUSTED_PLATFORM_SHEETS = [cfg["sheet"] for cfg in PORTAL_CONFIG.values()]

PLATFORM_SHEETS = [cfg["sheet"] for cfg in PORTAL_CONFIG.values()]

ALL_JOB_SOURCE_SHEETS = PLATFORM_SHEETS

APPLY_QUEUE_SIZE = 20

