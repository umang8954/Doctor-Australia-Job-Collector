"""Probe RANZCOG pagination / Load more."""
from __future__ import annotations

from scrapers.base import new_session
from scrapers.portal_parsers import parse_ranzcog

s = new_session(referer="https://jobs.ranzcog.edu.au/jobs")
r0 = s.get("https://jobs.ranzcog.edu.au/jobs", timeout=30)
print("page1", r0.status_code, len(parse_ranzcog(r0.text, "https://jobs.ranzcog.edu.au")))
print("cookies", s.cookies.get_dict())

for url in [
    "https://jobs.ranzcog.edu.au/jobs/?&page=2",
    "https://jobs.ranzcog.edu.au/jobs/?p=2",
    "https://jobs.ranzcog.edu.au/jobs/?page=2",
]:
    r = s.get(url, timeout=30)
    jobs = parse_ranzcog(r.text, "https://jobs.ranzcog.edu.au")
    print(url, r.status_code, "len", len(r.text), "jobs", len(jobs))

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        locale="en-AU",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
    )
    context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )
    page = context.new_page()
    page.goto("https://jobs.ranzcog.edu.au/jobs", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    html1 = page.content()
    print("pw page1", len(parse_ranzcog(html1, "https://jobs.ranzcog.edu.au")))
    btn = page.locator("text=Load more")
    if btn.count():
        btn.first.click()
        page.wait_for_timeout(5000)
        html2 = page.content()
        print("pw after load more", len(parse_ranzcog(html2, "https://jobs.ranzcog.edu.au")))
    else:
        print("no Load more button; buttons sample:")
        for el in page.locator("button, a.btn").all()[:15]:
            try:
                print(" ", el.inner_text()[:60])
            except Exception:
                pass
    browser.close()
