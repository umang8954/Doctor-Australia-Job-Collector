from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto("https://jobs.nt.gov.au/Home/Search", timeout=60000)
    page.wait_for_timeout(4000)
    page.locator("input[name*='keyword' i]").first.fill("registrar")
    page.locator("button:has-text('Search')").first.click()
    page.wait_for_timeout(8000)
    html = page.content()
    paths = set(re.findall(r"/Home/[A-Za-z0-9_/=-]+", html))
    print("paths sample:", sorted(paths)[:30])
    for m in re.findall(r"351010[^\"']{0,80}", html):
        print("351010 ctx", m[:80])
    # click open in new tab on first job
    btn = page.locator("button:has-text('Open this job in new tab')").first
    if btn.count():
        with page.expect_popup() as pop:
            btn.click()
        new = pop.value
        print("popup url", new.url)
        new.close()
    print("first job", page.locator(".jobTitle").first.inner_text()[:100])
    b.close()
