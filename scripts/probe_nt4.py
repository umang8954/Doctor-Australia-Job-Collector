from playwright.sync_api import sync_playwright


def search_nt(keyword):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        page.goto("https://jobs.nt.gov.au/Home/Search", timeout=60000)
        page.wait_for_timeout(4000)
        loc = page.locator("input[name*='keyword' i]").first
        loc.fill(keyword)
        page.locator("button:has-text('Search')").first.click()
        page.wait_for_timeout(8000)
        text = page.inner_text("body")
        print("KW", keyword, "no results", "no results" in text.lower())
        # vacancy numbers in page
        import re

        nums = re.findall(r"VAC\d+|vacancy[^\\n]{0,40}", text, re.I)
        print(" matches", nums[:5])
        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({href:e.href,text:e.innerText.trim().slice(0,80)})).filter(x => x.text.length>10)",
        )
        for l in links[:15]:
            print(" ", l)
        b.close()


for kw in ["health", "nurse", "medical", "doctor", "registrar", "officer", ""]:
    search_nt(kw)
