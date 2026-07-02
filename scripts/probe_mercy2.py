from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup

for url in [
    "https://www.mercyhealth.com.au/about-us/careers",
    "https://www.mercyhealth.com.au/careers",
    "https://www.mercyhealth.com.au/about/careers/search-jobs",
]:
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        print("HTTP", r.status_code, len(r.text), r.url[:80])
        if r.ok and len(r.text) > 5000:
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.find_all("a", href=True):
                t = a.get_text(" ", strip=True)
                if len(t) > 8 and any(k in t.lower() for k in ["registrar", "medical", "doctor", "nurse", "job"]):
                    print(" ", t[:60], a["href"][:70])
    except Exception as e:
        print("ERR", e)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    for url in [
        "https://www.mercyhealth.com.au/about-us/careers",
        "https://mercyhealth.wd3.myworkdayjobs.com/en-US/Mercy_Health_Careers/jobs",
    ]:
        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(15000)
            print("PW", url.split("/")[-1], len(page.content()))
            titles = page.locator("[data-automation-id='jobTitle']").all()
            print(" titles", len(titles))
            for t in titles[:5]:
                print("  ", t.inner_text()[:60])
        except Exception as e:
            print("PW ERR", e)
    b.close()
