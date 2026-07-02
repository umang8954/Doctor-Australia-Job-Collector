from playwright.sync_api import sync_playwright
import re


def probe_nt_search():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        page.goto("https://jobs.nt.gov.au/Home/Search", timeout=60000)
        page.wait_for_timeout(5000)
        # Screenshot-like debug: list visible inputs/buttons
        buttons = page.locator("button, input[type=submit], a.btn, .search-button").all()
        print("buttons", len(buttons))
        for i, btn in enumerate(buttons[:10]):
            try:
                print(i, btn.inner_text()[:40], btn.get_attribute("id"), btn.get_attribute("class"))
            except Exception:
                pass
        # Try keyword search field by placeholder/label
        for sel in [
            "#Keywords",
            "#SearchKeywords",
            "input[name*='keyword' i]",
            "input[name*='search' i]",
            "#search-input",
            ".search-input",
        ]:
            loc = page.locator(sel)
            if loc.count() and loc.first.is_visible():
                print("found", sel)
                loc.first.fill("doctor")
                page.wait_for_timeout(1000)
                break
        # click search
        for sel in ["button:has-text('Search')", "#btnSearch", "input[value='Search']"]:
            loc = page.locator(sel)
            if loc.count():
                print("click", sel)
                loc.first.click()
                page.wait_for_timeout(10000)
                break
        html = page.content()
        print("html len", len(html))
        print("no results", "no results" in html.lower(), "no vacancies" in html.lower())
        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({href:e.href,text:e.innerText.trim().slice(0,80)}))",
        )
        for l in links:
            if re.search(r"vacanc|/job|requisition|/details", l["href"], re.I) and len(l["text"]) > 8:
                print("JOB", l)
        # table rows
        rows = page.locator("table tr, .search-result, .job-item, [class*=vacancy]").all()
        print("row elements", len(rows))
        for row in rows[:5]:
            try:
                print(" ROW", row.inner_text()[:120].replace("\n", " | "))
            except Exception:
                pass
        b.close()


def probe_mercy_wd():
    import requests
    from bs4 import BeautifulSoup

    url = "https://mercyhealth.wd3.myworkdayjobs.com/en-US/Mercy_Health_Careers"
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    print("mercy page", r.status_code, len(r.text))
    # find cxs path in html
    for m in re.findall(r"/wday/cxs/[^\"']+", r.text):
        print("cxs", m[:80])
    soup = BeautifulSoup(r.text, "lxml")
    for script in soup.find_all("script"):
        t = script.string or ""
        if "cxs" in t:
            for m in re.findall(r"mercyhealth/[^\"']+", t):
                print("script", m[:80])


if __name__ == "__main__":
    probe_nt_search()
    probe_mercy_wd()
