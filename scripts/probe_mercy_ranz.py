import requests
from playwright.sync_api import sync_playwright

# RANZCOG main site
for url in [
    "https://ranzcog.edu.au/members/careers-and-employment",
    "https://ranzcog.edu.au/training/current-vacancies",
    "https://www.ranzcog.edu.au/womens-health/work-and-careers",
]:
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        print("RANZ", r.status_code, len(r.text), r.url[:70])
    except Exception as e:
        print("RANZ ERR", e)

# Mercy WD search
from scrapers.base import fetch_mercy_workday_search
from scrapers.portal_parsers import parse_mercy_workday_html

html = fetch_mercy_workday_search("medical", wait_ms=25000)
print("MERCY len", len(html))
jobs = parse_mercy_workday_html(html, "https://mercyhealth.wd3.myworkdayjobs.com")
print("MERCY jobs", len(jobs))
for j in jobs[:5]:
    print(" ", j.title, j.apply_link[:70])
