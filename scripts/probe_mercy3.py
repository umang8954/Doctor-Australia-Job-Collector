from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto("https://www.mercyhealth.com.au/about-us/careers", timeout=60000)
    page.wait_for_timeout(10000)
    links = page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => ({t:e.innerText.trim().slice(0,70), h:e.href})).filter(x => x.t.length > 5)",
    )
    for l in links:
        if re.search(r"job|career|registrar|medical|workday|search", l["t"] + l["h"], re.I):
            print(l)
    # workday iframe?
    print("frames", len(page.frames))
    for f in page.frames:
        print(" frame", f.url[:80])
    b.close()
