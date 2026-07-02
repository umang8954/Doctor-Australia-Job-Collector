import re
import requests

r = requests.get(
    "https://jobs.nt.gov.au/bundles/HomeSearchTS?v=4ygnzkVQjQXcFjOxcAXKBK_Pm7uQTTDe1vpXQ79j0Sk1",
    timeout=30,
)
text = r.text
print("bundle len", len(text))
for pat in [r"/api/[^\"']+", r"SearchJobs[^\"']*", r"GetJob[^\"']*", r"Vacancy[^\"']*"]:
    for m in re.findall(pat, text):
        print(m[:100])

# try common NT API patterns
for url in [
    "https://jobs.nt.gov.au/api/jobs/search?keyword=medical",
    "https://jobs.nt.gov.au/Home/SearchJobs?keyword=medical",
    "https://jobs.nt.gov.au/Home/GetJobs?searchText=medical",
]:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        print(url, resp.status_code, resp.text[:150])
    except Exception as e:
        print(url, e)
