from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto("https://jobs.nt.gov.au/Home/Search", timeout=60000)
    page.wait_for_timeout(4000)
    page.locator("input[name*='keyword' i]").first.fill("health")
    page.locator("button:has-text('Search')").first.click()
    page.wait_for_timeout(8000)
    html = page.content()
    soup = BeautifulSoup(html, "lxml")
    # all links
    for a in soup.find_all("a", href=True):
        t = a.get_text(" ", strip=True)
        h = a["href"]
        if len(t) > 12 and "http" not in t.lower()[:5]:
            print("LINK", t[:80], h[:80])
    # tables
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) > 1:
            print("TABLE rows", len(rows))
            for tr in rows[:5]:
                print(" ", tr.get_text(" | ", strip=True)[:150])
    # knockout/data bindings
    for el in soup.select("[data-bind], .result, .search-result, .vacancy, #searchResults"):
        print("EL", el.name, el.get("class"), el.get("id"), el.get_text(" ", strip=True)[:100])
    print("--- body snippet ---")
    body = soup.get_text("\n", strip=True)
    for line in body.split("\n"):
        if any(k in line.lower() for k in ["registrar", "medical", "doctor", "physician", "officer", "vacancy"]):
            if len(line) > 15:
                print("LINE", line[:120])
    b.close()
