import requests
from bs4 import BeautifulSoup
import re
from playwright.sync_api import sync_playwright

# NSW search
for url in [
    "https://jobs.health.nsw.gov.au/jobs/search?q=registrar",
    "https://jobs.health.nsw.gov.au/jobs/search?keyword=registrar",
    "https://jobs.health.nsw.gov.au/latest-jobs",
]:
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
    print("NSW", url.split("/")[-1], r.status_code, len(r.text), r.url[:80])
    if r.ok:
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.find_all("a", href=True)[:0]:
            pass
        jobs = [(a.get_text(" ", strip=True), a["href"]) for a in soup.find_all("a", href=True) if "/job" in a["href"].lower() and len(a.get_text(strip=True)) > 8]
        print("  job links", len(jobs))
        for t, h in jobs[:5]:
            print("   ", t[:50], h[:70])

# Mercy wd3 playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto("https://mercyhealth.wd3.myworkdayjobs.com/en-US/Mercy_Health_Careers", timeout=90000)
    page.wait_for_timeout(12000)
    html = page.content()
    print("MERCY PW len", len(html))
    links = page.eval_on_selector_all("a[href]", "els => els.map(e=>({t:e.innerText.trim().slice(0,60),h:e.href})).filter(x=>x.t.length>8)")
    for l in links[:15]:
        if "job" in l["h"].lower() or "registrar" in l["t"].lower() or "medical" in l["t"].lower():
            print(" ", l)
    b.close()

# SmartJobs main page navigation
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="en-AU")
    ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page = ctx.new_page()
    page.goto("https://smartjobs.qld.gov.au/", timeout=60000)
    page.wait_for_timeout(5000)
    print("SJ home", len(page.content()), page.url)
    # click job search if exists
    for sel in ["a:has-text('Search jobs')", "a:has-text('Find a job')", "a[href*='search']"]:
        loc = page.locator(sel)
        if loc.count():
            print("found link", sel, loc.first.get_attribute("href"))
    page.goto("https://smartjobs.qld.gov.au/jobtools/jncustomsearch.searchForm", timeout=60000)
    page.wait_for_timeout(8000)
    print("SJ form", page.url, len(page.content()))
    b.close()
