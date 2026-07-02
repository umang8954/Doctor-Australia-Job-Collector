"""Detect WAF blocks, error pages, and empty-result pages in scraped HTML."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PageAnalysis:
    is_blocked: bool
    is_error_page: bool
    is_no_results: bool
    reason: str
    html_len: int


_BLOCK_TITLE_PATTERNS = (
    r"403\s*forbidden",
    r"access\s*denied",
    r"bot\s*detected",
    r"request\s*blocked",
    r"security\s*check",
    r"captcha",
    r"cloudflare",
    r"please\s*verify",
)

_BLOCK_BODY_PATTERNS = (
    r"message-wrapper",
    r"cf-browser-verification",
    r"g-recaptcha",
    r"unusual\s*traffic",
    r"automated\s*access",
)

_ERROR_TITLE_PATTERNS = (
    r"404",
    r"page\s*not\s*found",
    r"error",
)

_NO_RESULTS_PATTERNS = (
    r"no\s*results?\s*found",
    r"no\s*jobs?\s*found",
    r"no\s*vacancies?\s*found",
    r"0\s*results?",
    r"we\s*couldn't\s*find",
    r"did\s*not\s*match\s*any",
)


def _title_snippet(html: str) -> str:
    m = re.search(r"<title[^>]*>([^<]{0,200})", html, re.I | re.S)
    return (m.group(1) if m else "").strip().lower()


def analyze_html(html: str, *, status_code: int | None = None) -> PageAnalysis:
    """Classify a fetched HTML response."""
    html_len = len(html or "")
    title = _title_snippet(html)
    lower = (html or "").lower()

    if status_code in (403, 429, 503):
        return PageAnalysis(True, True, False, f"HTTP {status_code}", html_len)

    if html_len < 5000 and status_code in (None, 200):
        if any(re.search(p, title, re.I) for p in _BLOCK_TITLE_PATTERNS):
            return PageAnalysis(True, True, False, f"block page (title: {title[:60]})", html_len)
        if any(p in lower for p in _BLOCK_BODY_PATTERNS):
            return PageAnalysis(True, True, False, "WAF/signature detected in HTML", html_len)
        if html_len < 2000 and "forbidden" in lower:
            return PageAnalysis(True, True, False, "403 forbidden body", html_len)

    if status_code == 404 or any(re.search(p, title, re.I) for p in _ERROR_TITLE_PATTERNS):
        if "404" in title or "not found" in title:
            return PageAnalysis(False, True, False, f"error page (title: {title[:60]})", html_len)

    no_results = any(re.search(p, lower, re.I) for p in _NO_RESULTS_PATTERNS)
    if no_results and html_len < 120000:
        return PageAnalysis(False, False, True, "no results message on page", html_len)

    return PageAnalysis(False, False, False, "", html_len)


def failure_reason_from_analysis(analysis: PageAnalysis, parser_found: int = 0) -> str:
    if analysis.is_blocked:
        return f"blocked: {analysis.reason}"
    if analysis.is_error_page:
        return f"error_page: {analysis.reason}"
    if analysis.is_no_results and parser_found == 0:
        return "no_jobs_matched: portal returned no results for query"
    if parser_found == 0:
        return "parser_found_nothing: page loaded but no job cards parsed"
    return ""
