import requests

urls = [
    "https://healthjobs.nsw.gov.au/",
    "https://jobs.health.nsw.gov.au/",
    "https://www.health.nsw.gov.au/careers/pages/medical-careers.aspx",
    "https://careers.sahealth.sa.gov.au/caw/en/listing/?search-keyword=registrar+medical",
    "https://careers.health.qld.gov.au/search/?q=registrar",
]
for u in urls:
    try:
        r = requests.get(u, timeout=20, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        print(r.status_code, len(r.text), r.url[:90])
    except Exception as e:
        print("ERR", u[:50], str(e)[:60])
