"""
Shared helpers: filtering, deduplication, logging, date formatting.
Australia-only: jobs must be located in Australia.
"""

from __future__ import annotations

import functools
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Optional
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import config

AEST = ZoneInfo(config.AEST_TIMEZONE)


@dataclass
class JobRecord:
    """Normalized medical job before writing to Excel."""

    title: str
    specialty: str = ""
    experience_level: str = ""
    hospital: str = ""
    location: str = ""
    state: str = ""
    salary: str = ""
    posted_date: Optional[datetime] = None
    apply_link: str = ""
    description: str = ""
    platform: str = ""
    layer: str = ""
    notes: str = ""
    match_pct: int = 0
    match_label: str = ""

    def combined_text(self) -> str:
        return (
            f"{self.title} {self.specialty} {self.hospital} {self.location} "
            f"{self.state} {self.description} {self.salary} {self.notes}"
        )


def now_aest() -> datetime:
    return datetime.now(tz=AEST)


def format_date(dt: Optional[datetime]) -> str:
    """All dates -> DD-MM-YYYY."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=AEST)
    else:
        dt = dt.astimezone(AEST)
    return dt.strftime("%d-%m-%Y")


def format_dt(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=AEST)
    else:
        dt = dt.astimezone(AEST)
    return dt.strftime("%d-%m-%Y %H:%M")


def parse_added_on(value: str) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%d-%m-%Y %H:%M", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip()[:16], fmt).replace(tzinfo=AEST)
        except ValueError:
            continue
    return None


def dedup_key(hospital: str, title: str) -> str:
    return re.sub(r"\s+", "", f"{hospital}{title}".lower().strip())


def contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)


def detect_specialty(text: str) -> str:
    text_lower = text.lower()
    for phrase, display in config.SPECIALTY_RULES:
        if phrase.lower() in text_lower:
            return display
    return ""


def detect_experience_level(text: str) -> str:
    text_lower = text.lower()
    for phrase, display in config.EXPERIENCE_RULES:
        if phrase.lower() in text_lower:
            return display
    return ""


def detect_state(text: str, default: str = "") -> str:
    text_lower = text.lower()
    for state_name, abbrev in config.STATE_ABBREVS.items():
        if state_name in text_lower or abbrev.lower() in text_lower:
            return abbrev
    for loc in config.AU_LOCATIONS:
        if loc.lower() in text_lower:
            return config.STATE_ABBREVS.get(loc.lower(), loc)
    return default


def _normalize_for_location_match(text: str) -> str:
    return f" {text.lower()} "


def contains_non_au_location(text: str) -> bool:
    """True if text explicitly references a non-Australian location."""
    padded = _normalize_for_location_match(text)
    for kw in config.NON_AU_LOCATION_KEYWORDS:
        token = kw.lower()
        if token in padded or f" {token}," in padded or f" {token}." in padded:
            return True
    return False


def contains_au_location(text: str) -> bool:
    """True if text references Australia or an Australian state/city."""
    text_lower = text.lower()
    if contains_any(text_lower, config.AU_LOCATION_KEYWORDS):
        return True
    if detect_state(text_lower):
        return True
    return False


def is_au_apply_link(url: str) -> bool:
    if not url:
        return False
    url_lower = url.lower()
    if any(suffix in url_lower for suffix in config.AU_DOMAIN_SUFFIXES):
        return True
    try:
        host = urlparse(url_lower).netloc
    except Exception:  # noqa: BLE001
        return False
    for trusted in config.AU_TRUSTED_PORTAL_HOSTS:
        if trusted in host or host.endswith(trusted):
            return True
    return host.endswith(".au")


def passes_australia_filter(job: JobRecord) -> bool:
    """Keep only jobs located in Australia."""
    if not config.AUSTRALIA_ONLY:
        return True

    text = job.combined_text()
    link = job.apply_link or ""

    if contains_non_au_location(text):
        return False

    if is_au_apply_link(link):
        return True

    if contains_au_location(text):
        return True

    # Jobs from AU hospital/govt portals default to Australia when state is set
    if job.state and job.state in set(config.STATE_ABBREVS.values()):
        if job.platform in config.AU_TRUSTED_PLATFORM_SHEETS:
            return True

    return False


def parse_relative_posted(text: str) -> Optional[datetime]:
    if not text:
        return None
    t = text.strip().lower()
    now = now_aest()

    if "just now" in t or "today" in t or "few hours" in t:
        return now
    if "minute" in t:
        m = re.search(r"(\d+)", t)
        return now - timedelta(minutes=int(m.group(1))) if m else now
    if "hour" in t:
        m = re.search(r"(\d+)", t)
        return now - timedelta(hours=int(m.group(1))) if m else now
    if "day" in t:
        m = re.search(r"(\d+)", t)
        return now - timedelta(days=int(m.group(1))) if m else now
    if "week" in t:
        m = re.search(r"(\d+)", t)
        days = int(m.group(1)) * 7 if m else 7
        return now - timedelta(days=days)
    if "month" in t:
        return now - timedelta(days=30)

    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(t[:20].strip(), fmt).replace(tzinfo=AEST)
        except ValueError:
            continue
    return None


def is_within_date_filter(job: JobRecord) -> bool:
    cutoff = now_aest() - timedelta(days=config.DATE_FILTER_DAYS)
    if job.posted_date is None:
        return True
    posted = job.posted_date
    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=AEST)
    else:
        posted = posted.astimezone(AEST)
    return posted >= cutoff


def passes_keyword_filter(job: JobRecord) -> bool:
    return contains_any(job.combined_text(), config.KEYWORDS)


def passes_filters(job: JobRecord) -> bool:
    if not job.title or len(job.title) < 3:
        return False
    if not passes_keyword_filter(job):
        return False
    if not passes_australia_filter(job):
        return False
    if not is_within_date_filter(job):
        return False
    if job.apply_link and not job.apply_link.startswith("http"):
        return False
    return True


def safe_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and str(value) == "nan":
        return ""
    return str(value).strip()


def retry(max_attempts: int = config.MAX_RETRIES, delay: int = config.RETRY_DELAY_SECONDS):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_error

        return wrapper

    return decorator


class RunLogger:
    def __init__(self):
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        day = now_aest().strftime("%Y-%m-%d")
        self.path = config.LOGS_DIR / f"run_{day}.log"
        self.lines: list[str] = []

    def log(self, message: str) -> None:
        stamp = now_aest().strftime("%d-%m-%Y %H:%M:%S AEST")
        line = f"[{stamp}] {message}"
        print(line)
        self.lines.append(line)

    def save(self) -> None:
        existing = ""
        if self.path.exists():
            existing = self.path.read_text(encoding="utf-8")
        self.path.write_text(existing + "\n".join(self.lines) + "\n", encoding="utf-8")
