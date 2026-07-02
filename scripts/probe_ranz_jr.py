from playwright.sync_api import sync_playwright

# RANZCOG - session from main site first
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
        locale="en-AU",
        viewport={"width": 1366, "height": 768},
    )
    ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page = ctx.new_page()
    page.goto("https://www.ranzcog.edu.au/", timeout=60000)
    page.wait_for_timeout(3000)
    page.goto("https://jobs.ranzcog.edu.au/jobs", timeout=60000)
    page.wait_for_timeout(8000)
    print("RANZCOG len", len(page.content()), page.url)
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.innerText.trim()).filter(t => t.length > 5)")
    print("links", links[:10])
    b.close()

# JobRadars with referer
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
        locale="en-AU",
        extra_http_headers={"Referer": "https://www.google.com.au/"},
    )
    ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page = ctx.new_page()
    page.goto("https://australia.jobradars.com/jobs?q=registrar+medical+australia", timeout=60000)
    page.wait_for_timeout(8000)
    print("JR len", len(page.content()))
    links = page.eval_on_selector_all("a[href]", "els => els.map(e=>({t:e.innerText.trim().slice(0,60),h:e.href})).filter(x=>x.t.length>8)[:10]")
    print("JR links", links)
    b.close()
