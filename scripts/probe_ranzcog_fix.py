"""Probe RANZCOG / Seek / Jora HTML structures."""
from __future__ import annotations

import re
from pathlib import Path

from scrapers.base import fetch_html, fetch_with_playwright, soup_from_html, text

OUT = Path("logs")
OUT.mkdir(exist_ok=True)


def probe_ranzcog() -> None:
    html = fetch_html("https://jobs.ranzcog.edu.au/jobs", label="ranzcog_probe")
    (OUT / "ranzcog_sample.html").write_text(html, encoding="utf-8")
    soup = soup_from_html(html)
    print("RANZCOG title:", soup.title.string if soup.title else None)
    print("len:", len(html))

    for sel in [
        ".job",
        "article",
        ".views-row",
        ".listing",
        ".card",
        "[class*=job]",
        "h2 a",
        "h3 a",
        ".job-listing",
        "table tr",
    ]:
        els = soup.select(sel)
        if els:
            print(f"  {sel}: {len(els)} eg={text(els[0])[:70]!r}")

    hrefs = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        t = text(a)
        if "/jobs/" in h and "categories" not in h and h.rstrip("/").endswith("/jobs") is False:
            if re.search(r"/jobs/\d+|/jobs/[a-z0-9-]+", h, re.I):
                hrefs.append((t[:70], h[:120]))
    print("detail-like hrefs:", len(hrefs))
    for x in hrefs[:15]:
        print(" ", x)

    # Look for data attributes / API hints
    for pat in [r"/api/[^\"']+", r"wp-json[^\"']+", r"ajax[^\"']+", r"listings[^\"']+\.json"]:
        hits = re.findall(pat, html, re.I)
        if hits:
            print("api hint", pat, hits[:5])

    # Try category pages that look like trainee/specialist
    cats = [
        "https://jobs.ranzcog.edu.au/jobs/?categories[]=Yr%205%20(Advanced)%20FRANZCOG%20Trainee%20Positions",
        "https://jobs.ranzcog.edu.au/jobs/?categories[]=Specialist%20Position",
        "https://jobs.ranzcog.edu.au/jobs/?categories[]=Yr%201-4%20FRANZCOG%20Trainee%20Positions",
    ]
    for url in cats:
        try:
            ch = fetch_html(url, label="ranzcog_cat")
            cs = soup_from_html(ch)
            details = []
            for a in cs.find_all("a", href=True):
                h = a["href"]
                t = text(a)
                if re.search(r"/jobs/\d+|/job/", h, re.I) and len(t) > 5:
                    details.append((t[:70], h[:100]))
            print(f"CAT {url.split('categories')[-1][:40]}: html={len(ch)} details={len(details)}")
            for d in details[:5]:
                print("   ", d)
            # also print first few job-looking titles
            for a in cs.find_all("a", href=True)[:30]:
                t = text(a)
                if len(t) > 20 and any(k in t.lower() for k in ("registrar", "obstet", "fellow", "consultant", "trainee")):
                    print("   titleish", t[:80], a["href"][:80])
        except Exception as exc:  # noqa: BLE001
            print("CAT fail", exc)


def probe_playwright_ranzcog() -> None:
    try:
        html = fetch_with_playwright(
            "https://jobs.ranzcog.edu.au/jobs",
            label="ranzcog",
            stealth=True,
            wait_until="networkidle",
        )
        print("PW len", len(html), "forbidden" in html.lower(), "403" in html[:500])
        soup = soup_from_html(html)
        print("PW title", soup.title.string if soup.title else None)
        details = []
        for a in soup.find_all("a", href=True):
            h = a["href"]
            t = text(a)
            if re.search(r"/jobs/\d+", h) or ("/jobs/" in h and "categories" not in h and len(t) > 15):
                details.append((t[:70], h[:100]))
        print("PW candidates", len(details))
        for d in details[:10]:
            print(" ", d)
        (OUT / "ranzcog_pw.html").write_text(html, encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print("PW fail", exc)


def probe_seek() -> None:
    html = fetch_html(
        "https://www.seek.com.au/obstetrics-gynaecology-registrar-jobs/in-All-Australia",
        label="seek",
    )
    soup = soup_from_html(html)
    jobs = []
    for a in soup.find_all("a", href=True):
        if "/job/" in a["href"] and len(text(a)) > 8:
            jobs.append((text(a)[:70], a["href"][:100]))
    print("Seek static jobs", len(jobs))
    for j in jobs[:8]:
        print(" ", j)


if __name__ == "__main__":
    probe_ranzcog()
    print("---")
    probe_playwright_ranzcog()
    print("---")
    probe_seek()
