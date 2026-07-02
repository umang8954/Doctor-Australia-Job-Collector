import requests
from bs4 import BeautifulSoup
import re

# NSW Health jobs
r = requests.get("https://jobs.health.nsw.gov.au/", timeout=30, headers={"User-Agent": "Mozilla/5.0"})
print("NSW", r.status_code, len(r.text))
soup = BeautifulSoup(r.text, "lxml")
for a in soup.find_all("a", href=True):
    t = a.get_text(" ", strip=True)
    h = a["href"]
    if len(t) > 8 and re.search(r"registrar|medical|doctor|job", t, re.I):
        print(" ", t[:60], h[:80])

# Mercy workday with session warmup
base = "https://mercyhealth.wd3.myworkdayjobs.com"
site_url = f"{base}/en-US/Mercy_Health_Careers"
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
try:
    s.get(site_url, timeout=30)
    for tenant_site in [
        ("mercyhealth", "Mercy_Health_Careers"),
        ("mercyhealth", "MercyHealthCareers"),
        ("mercyhealth", "External"),
    ]:
        api = f"{base}/wday/cxs/{tenant_site[0]}/{tenant_site[1]}/jobs"
        payload = {"limit": 20, "offset": 0, "searchText": "registrar", "appliedFacets": {}}
        r = s.post(api, json=payload, timeout=30)
        print("WD", tenant_site, r.status_code, r.text[:120])
        if r.ok:
            print(" jobs", len(r.json().get("jobPostings", [])))
except Exception as e:
    print("WD ERR", e)
