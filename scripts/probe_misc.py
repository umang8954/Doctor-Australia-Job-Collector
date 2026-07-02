import requests
from bs4 import BeautifulSoup

urls = [
    "https://www.ranzcog.edu.au/work-with-us/careers",
    "https://www.ranzcog.edu.au/about-us/work-with-us",
    "https://www.ranzcog.edu.au/training/current-vacancies",
]
for url in urls:
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        print(url, r.status_code, len(r.text), r.url[:80])
        if r.ok:
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.find_all("a", href=True):
                t = a.get_text(" ", strip=True)
                if len(t) > 8 and any(k in t.lower() for k in ["job", "vacanc", "registrar", "position"]):
                    print(" ", t[:60], a["href"][:70])
    except Exception as e:
        print(url, e)

# SmartJobs organ search
for url in [
    "https://smartjobs.qld.gov.au/jobtools/jncustomsearch.searchResults?in_organid=14904&in_keyword=registrar&in_max=50",
    "https://smartjobs.qld.gov.au/jobtools/jncustomsearch.searchResults?in_organid=14904&in_keyword=doctor",
]:
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        print("SJ", r.status_code, len(r.text), r.url[:90])
    except Exception as e:
        print("SJ ERR", e)
