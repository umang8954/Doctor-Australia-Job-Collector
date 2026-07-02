"""Probe Jobs NT, QLD health, Mercy Workday, JobRadars."""
from playwright.sync_api import sync_playwright
import re
import requests
from bs4 import BeautifulSoup


def probe_jobs_nt():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(locale="en-AU")
        page = ctx.new_page()
        page.goto("https://jobs.nt.gov.au/Home/Search", timeout=60000)
        page.wait_for_timeout(4000)
        search = page.locator("input[type=text], input[type=search]").first
        if search.count():
            search.fill("medical")
            page.keyboard.press("Enter")
            page.wait_for_timeout(10000)
        html = page.content()
        print("NT len", len(html), "no results", "no results" in html.lower())
        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({href:e.href,text:e.innerText.trim().slice(0,80)}))",
        )
        jobs = [
            l
            for l in links
            if re.search(r"/job|/vacanc|requisition|position|/jobs/", l["href"], re.I)
            and len(l["text"]) > 8
        ]
        print("NT job links", len(jobs))
        for l in jobs[:10]:
            print(" ", l)
        b.close()


def probe_qld():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(locale="en-AU")
        page = ctx.new_page()
        page.goto("https://careers.health.qld.gov.au/search/?q=registrar", timeout=90000)
        page.wait_for_timeout(12000)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        print("QLD len", len(html))
        for a in soup.find_all("a", href=True):
            t = a.get_text(" ", strip=True)
            h = a["href"]
            if len(t) > 10 and re.search(r"registrar|medical|doctor|physician|officer", t, re.I):
                if re.search(r"job|requisition|/en/", h, re.I):
                    print(" QLD", t[:70], h[:90])
        b.close()


def probe_mercy_workday():
    base = "https://mercyhealth.wd3.myworkdayjobs.com"
    api = f"{base}/wday/cxs/mercyhealth/Mercy_Health_Careers/jobs"
    payload = {"limit": 20, "offset": 0, "searchText": "registrar", "appliedFacets": {}}
    r = requests.post(api, json=payload, timeout=30, headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Mozilla/5.0"})
    print("MERCY WD3", r.status_code, len(r.text))
    if r.ok:
        data = r.json()
        posts = data.get("jobPostings", [])
        print(" jobs", len(posts))
        for j in posts[:5]:
            print(" ", j.get("title"), j.get("externalPath", "")[:60])


def probe_jobradars_pw():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
            locale="en-AU",
        )
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = ctx.new_page()
        try:
            page.goto("https://australia.jobradars.com/jobs?q=registrar+medical", timeout=60000)
            page.wait_for_timeout(8000)
            print("JOBRADARS", len(page.content()), page.url)
            links = page.eval_on_selector_all(
                "a[href]",
                "els => els.filter(e => e.href.includes('job')).map(e => e.innerText.trim().slice(0,60))",
            )
            print(" links", links[:5])
        except Exception as e:
            print("JOBRADARS ERR", e)
        b.close()


if __name__ == "__main__":
    probe_jobs_nt()
    probe_qld()
    probe_mercy_workday()
    probe_jobradars_pw()
