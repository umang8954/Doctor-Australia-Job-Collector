import requests
from bs4 import BeautifulSoup
import re

r = requests.get(
    "https://jobs.health.nsw.gov.au/jobs/search?q=registrar+medical",
    timeout=30,
    headers={"User-Agent": "Mozilla/5.0"},
    allow_redirects=True,
)
print("NSW static", r.status_code, len(r.text), r.url)
soup = BeautifulSoup(r.text, "lxml")
for a in soup.find_all("a", href=True):
    t = a.get_text(" ", strip=True)
    h = a["href"]
    if len(t) > 12 and re.search(r"registrar|medical|doctor|physician|resident|fellow|officer", t, re.I):
        if "lhd" not in h.lower() or "/jobs/" in h:
            print(t[:70], h[:90])

# class patterns
for sel in ["[class*=title]", "[class*=job]", "article", "h2", "h3"]:
    els = soup.select(sel)
    if 0 < len(els) < 100:
        print("SEL", sel, len(els))
