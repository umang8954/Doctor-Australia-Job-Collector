"""Inspect RANZCOG article markup and AJAX listings endpoint."""
from __future__ import annotations

import re
from pathlib import Path

from scrapers.base import new_session, soup_from_html, text

html = Path("logs/ranzcog_sample.html").read_text(encoding="utf-8")
soup = soup_from_html(html)
arts = soup.select("article")
print("articles", len(arts))

out = []
for i, art in enumerate(arts[:5]):
    out.append(f"=== article {i} ===\n")
    out.append(str(art)[:2000])
    out.append("\nTEXT: " + text(art)[:400] + "\n")
    out.append("LINKS: " + repr([(text(x), x.get("href")) for x in art.find_all("a", href=True)]) + "\n\n")
Path("logs/ranzcog_articles.txt").write_text("".join(out), encoding="utf-8")
print("wrote logs/ranzcog_articles.txt")

# classes on article
for art in arts[:3]:
    print("classes", art.get("class"), "id", art.get("id"))
    for a in art.find_all("a", href=True):
        print("  a", text(a)[:60], "->", a.get("href")[:100])

# ajax
s = new_session(referer="https://jobs.ranzcog.edu.au/jobs")
r0 = s.get("https://jobs.ranzcog.edu.au/jobs", timeout=30)
print("warmup", r0.status_code)

candidates = [
    ("GET", "https://jobs.ranzcog.edu.au/ajax/?action=request_for_listings&page=1"),
    ("GET", "https://jobs.ranzcog.edu.au/?ajax=1&action=request_for_listings&page=1"),
    ("POST", "https://jobs.ranzcog.edu.au/"),
]
for method, url in candidates:
    try:
        if method == "GET":
            r = s.get(url, timeout=30)
        else:
            r = s.post(
                url,
                data={"action": "request_for_listings", "page": "1"},
                headers={"X-Requested-With": "XMLHttpRequest"},
                timeout=30,
            )
        snippet = r.text[:500].replace("\n", " ")
        print(method, url[:80], r.status_code, len(r.text), snippet[:200])
        Path(f"logs/ranzcog_ajax_{method.lower()}.txt").write_text(r.text[:5000], encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print("fail", method, url, exc)

# Find form of listings in original HTML via regex
m = re.search(r"request_for_listings.{0,400}", html)
print("context", m.group(0) if m else None)
# find listing URLs pattern like /jobs/something-slug/
slugs = re.findall(r'https?://jobs\.ranzcog\.edu\.au/jobs/[a-z0-9][^\"\'\s<>]{5,80}', html, re.I)
print("slug urls", len(set(slugs)))
for u in list(dict.fromkeys(slugs))[:15]:
    print(" ", u)
