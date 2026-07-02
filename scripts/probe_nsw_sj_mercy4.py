from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto("https://jobs.health.nsw.gov.au/jobs/search?q=registrar", timeout=60000)
    page.wait_for_timeout(10000)
    html = page.content()
    print("NSW PW len", len(html), page.url)
    soup = BeautifulSoup(html, "lxml")
    for sel in [".job-title", ".job-result", "article", "h2 a", "h3 a", "[class*=job]", "li"]:
        els = soup.select(sel)
        if els and len(els) < 200:
            print("sel", sel, len(els), els[0].get_text(" ", strip=True)[:80] if els else "")
    for a in soup.find_all("a", href=True):
        t = a.get_text(" ", strip=True)
        h = a["href"]
        if len(t) > 12 and not t.startswith("http") and "lhd" not in h.lower():
            if re.search(r"registrar|medical|doctor|physician|resident|fellow", t, re.I):
                print("LINK", t[:70], h[:90])
    b.close()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="en-AU")
    page = ctx.new_page()
    page.goto("https://smartjobs.qld.gov.au/jobtools/jncustomsearch.jobsearch?in_organid=14904", timeout=60000)
    page.wait_for_timeout(8000)
    print("SJ organ len", len(page.content()))
    # try keyword input
    for sel in ["input[name*=keyword i]", "input[id*=keyword i]", "#keyword", "input[type=text]"]:
        loc = page.locator(sel)
        if loc.count():
            try:
                if loc.first.is_visible():
                    loc.first.fill("registrar")
                    print("filled", sel)
                    break
            except Exception:
                pass
    page.keyboard.press("Enter")
    page.wait_for_timeout(10000)
    html = page.content()
    print("SJ after search", len(html))
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        t = a.get_text(" ", strip=True)
        if len(t) > 8 and re.search(r"registrar|medical|doctor", t, re.I):
            print("SJ JOB", t[:60], a["href"][:80])
    b.close()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto("https://mercyhealth.wd3.myworkdayjobs.com/en-US/Mercy_Health_Careers", timeout=90000)
    page.wait_for_timeout(5000)
    search = page.locator("input[data-automation-id='searchBox']")
    if search.count():
        search.first.fill("registrar")
        page.keyboard.press("Enter")
        page.wait_for_timeout(12000)
    html = page.content()
    print("MERCY len", len(html))
    for li in page.locator("[data-automation-id='jobTitle']").all()[:10]:
        print(" MERCY JOB", li.inner_text()[:70])
    b.close()
