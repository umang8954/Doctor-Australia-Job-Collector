import requests
from bs4 import BeautifulSoup
import re
from playwright.sync_api import sync_playwright

# SmartJobs jobsearch with keyword
url = "https://smartjobs.qld.gov.au/jobtools/jncustomsearch.jobsearch?in_organid=14904&in_keyword=registrar&in_max=50"
r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
print("SJ HTTP", r.status_code, len(r.text), r.url[:100])
if r.ok:
    soup = BeautifulSoup(r.text, "lxml")
    for a in soup.find_all("a", href=True):
        t = a.get_text(" ", strip=True)
        h = a["href"]
        if len(t) > 8 and re.search(r"registrar|medical|doctor|officer", t, re.I):
            print(" ", t[:60], h[:80])

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto(url, timeout=60000)
    page.wait_for_timeout(10000)
    html = page.content()
    print("SJ PW len", len(html))
    links = page.eval_on_selector_all("a[href]", "els => els.map(e=>({t:e.innerText.trim().slice(0,70),h:e.href})).filter(x=>x.t.length>8)")
    for l in links:
        if re.search(r"registrar|medical|doctor|officer", l["t"], re.I):
            print(" SJ", l)
    b.close()

# NSW actual job postings
r = requests.get("https://jobs.health.nsw.gov.au/jobs/search?q=registrar+medical", timeout=30, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
soup = BeautifulSoup(r.text, "lxml")
print("NSW search final", r.url)
for a in soup.find_all("a", href=True):
    t = a.get_text(" ", strip=True)
    h = a["href"]
    if re.search(r"/jobs/\d|/job/\d|vacancy|position", h, re.I) and len(t) > 10:
        print(" NSWJOB", t[:60], h[:80])

# Mercy WD3 links
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto("https://mercyhealth.wd3.myworkdayjobs.com/en-US/Mercy_Health_Careers?q=registrar", timeout=90000)
    page.wait_for_timeout(15000)
    links = page.eval_on_selector_all("a[href]", "els => els.map(e=>({t:e.innerText.trim().slice(0,70),h:e.href})).filter(x=>x.t.length>5)")
    for l in links:
        if "job" in l["h"].lower() or re.search(r"registrar|medical|nurs|doctor", l["t"], re.I):
            print(" MERCY", l)
    b.close()
