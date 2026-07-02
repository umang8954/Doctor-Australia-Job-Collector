"""Temporary portal probe script — not part of collector."""
from playwright.sync_api import sync_playwright
import re


def pw_stealth(url, wait=12000):
    with sync_playwright() as p:
        b = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = b.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-AU",
            viewport={"width": 1366, "height": 768},
            extra_http_headers={
                "Accept-Language": "en-AU,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = ctx.new_page()
        api_responses = []

        def on_resp(r):
            ct = r.headers.get("content-type", "")
            if "json" in ct or "/api/" in r.url or "search" in r.url.lower():
                api_responses.append((r.url[:120], r.status))

        page.on("response", on_resp)
        page.goto(url, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(wait)
        html = page.content()
        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({href: e.href, text: e.innerText.trim().slice(0,80)}))",
        )
        b.close()
    return html, links, api_responses


if __name__ == "__main__":
    # Jobs NT
    html, links, apis = pw_stealth("https://jobs.nt.gov.au/jobs?search=doctor", 8000)
    print("JOBS_NT APIs:", apis[:15])
    job_links = [
        l
        for l in links
        if re.search(r"job|vacanc|position", l["href"], re.I)
        and len(l["text"]) > 8
        and l["text"] not in ("Job Search", "Candidate Home")
    ]
    print("JOBS_NT job-like:", len(job_links))
    for l in job_links[:8]:
        print(" ", l["text"][:70], l["href"][:80])
    print("no results:", "no results" in html.lower())

    # RANZCOG
    html, links, apis = pw_stealth("https://jobs.ranzcog.edu.au/jobs", 10000)
    print("RANZCOG html", len(html))
    job_links = [l for l in links if len(l["text"]) > 5]
    print("RANZCOG links", len(job_links))
    for l in job_links[:5]:
        print(" ", l["text"][:60])

    # QLD health
    html, links, apis = pw_stealth("https://careers.health.qld.gov.au/search/?q=registrar", 12000)
    print("QLD html", len(html))
    job_links = [l for l in links if "/job/" in l["href"] or "apply" in l["href"].lower()]
    print("QLD job links", len(job_links))
    for l in job_links[:5]:
        print(" ", l["text"][:60], l["href"][:80])

    # NSW iworkfor
    html, links, apis = pw_stealth("https://www.iworkfor.nsw.gov.au/jobs?keyword=registrar+medical", 12000)
    print("IWORKFORNSW html", len(html))
    job_links = [l for l in links if "job" in l["href"].lower() and len(l["text"]) > 8]
    print("IWORKFORNSW links", len(job_links))
    for l in job_links[:5]:
        print(" ", l["text"][:60])
