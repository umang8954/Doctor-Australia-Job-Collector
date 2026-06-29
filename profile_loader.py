"""
Load doctor profiles from Demo_Medical_Resumes.pdf or data/profiles.json.

Place Demo_Medical_Resumes.pdf in the data/ folder. Each PDF page is treated
as one doctor profile. Extracted text is cached to profiles.json.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import config
from job_utils import detect_specialty, now_aest


def _guess_name(text: str) -> str:
    for pattern in (
        r"(?:Dr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z'O-]+)+)",
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z'O-]+){1,3})\s*$",
    ):
        m = re.search(pattern, text, re.M)
        if m:
            return m.group(0).strip()[:80]
    return ""


def _guess_level(text: str) -> str:
    text_lower = text.lower()
    for level in config.EXPERIENCE_LEVEL_KEYWORDS:
        if level.lower() in text_lower:
            return level.title() if level.isupper() else level
    return ""


def _guess_states(text: str) -> list[str]:
    found = []
    text_lower = text.lower()
    for loc in config.AU_LOCATIONS:
        if loc.lower() in text_lower:
            found.append(loc)
    return found or ["Australia"]


def _extract_from_pdf(pdf_path: Path) -> list[dict[str, Any]]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return []

    reader = PdfReader(str(pdf_path))
    profiles: list[dict[str, Any]] = []

    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if len(text) < 40:
            continue
        name = _guess_name(text) or f"Doctor Profile {i}"
        specialty = detect_specialty(text) or "General Medicine"
        level = _guess_level(text) or "Medical Officer"
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower())[:20] or f"profile_{i}"
        profiles.append({
            "id": f"dr_{slug}_{i}",
            "name": name,
            "specialty": specialty,
            "experience_level": level,
            "preferred_states": _guess_states(text),
            "keywords": [k for k in config.KEYWORDS if k.lower() in text.lower()][:8],
            "source": f"Demo_Medical_Resumes.pdf (page {i})",
            "resume_text": text[:4000],
        })
    return profiles


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_json(path: Path, profiles: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")


def load_profiles(force_pdf: bool = False) -> list[dict[str, Any]]:
    """
    Load profiles: prefer PDF extraction when present, else profiles.json.
    PDF text is cached to profiles.json after extraction.
    """
    pdf_path = config.PROFILE_PDF
    json_path = config.PROFILES_JSON

    if pdf_path.exists() and (force_pdf or not json_path.exists()):
        extracted = _extract_from_pdf(pdf_path)
        if extracted:
            _save_json(json_path, extracted)
            return extracted

    profiles = _load_json(json_path)
    if profiles:
        return profiles

    if pdf_path.exists():
        extracted = _extract_from_pdf(pdf_path)
        if extracted:
            _save_json(json_path, extracted)
            return extracted

    return _load_json(json_path)


def profile_summary_rows(profiles: list[dict[str, Any]]) -> list[list]:
    today = now_aest().strftime("%d-%m-%Y")
    rows = []
    for p in profiles:
        rows.append([
            p.get("id", ""),
            p.get("name", ""),
            p.get("specialty", ""),
            p.get("experience_level", ""),
            ", ".join(p.get("preferred_states", [])),
            p.get("source", ""),
            today,
        ])
    return rows
