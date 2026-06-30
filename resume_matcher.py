"""
Score jobs against doctor profiles — delegates to job_validator (Phases 2 & 3).

Match % weights (see job_validator.py):
  Title/role relevance 40% | Specialty 25% | Location 20% | Experience 15%
Match % >= 70 -> High Match
"""

from __future__ import annotations

from typing import Any

import config


def _score_category(text: str, tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for t in tokens if t.lower() in text_lower)
    return min(1.0, hits / max(len(tokens), 1))


def _profile_tokens(profile: dict[str, Any]) -> dict[str, list[str]]:
    resume = (profile.get("resume_text") or "").lower()
    specialties = [profile.get("specialty", "")]
    if profile.get("specialty"):
        specialties.append(profile["specialty"])
    for s in config.SPECIALTY_KEYWORDS:
        if s.lower() in resume:
            specialties.append(s)
    locations = list(profile.get("preferred_states") or [])
    for loc in config.AU_LOCATIONS:
        if loc.lower() in resume:
            locations.append(loc)
    levels = [profile.get("experience_level", "")]
    for lvl in config.EXPERIENCE_LEVEL_KEYWORDS:
        if lvl.lower() in resume:
            levels.append(lvl)
    keywords = list(profile.get("keywords") or [])
    for kw in config.KEYWORDS:
        if kw.lower() in resume:
            keywords.append(kw)
    return {
        "specialties": [x for x in dict.fromkeys(specialties) if x],
        "locations": [x for x in dict.fromkeys(locations) if x] or config.AU_LOCATIONS[:3],
        "levels": [x for x in dict.fromkeys(levels) if x] or ["medical officer"],
        "keywords": [x for x in dict.fromkeys(keywords) if x] or config.KEYWORDS[:5],
    }


def score_job_for_profile(
    profile: dict[str, Any],
    title: str,
    description: str = "",
    specialty: str = "",
    location: str = "",
    state: str = "",
    experience_level: str = "",
) -> int:
    """Delegate to job_validator for consistent Match % (Phases 2 & 3)."""
    from job_validator import score_job_validation

    return score_job_validation(
        profile, title, description, specialty, location, state, experience_level
    ).match_pct


def score_all_profiles(
    profiles: list[dict[str, Any]],
    title: str,
    description: str = "",
    specialty: str = "",
    location: str = "",
    state: str = "",
) -> list[dict[str, Any]]:
    scored = []
    for profile in profiles:
        pct = score_job_for_profile(
            profile, title, description, specialty, location, state, experience_level=""
        )
        scored.append({
            "profile_id": profile.get("id", ""),
            "profile_name": profile.get("name", ""),
            "match_pct": pct,
            "label": match_label(pct),
        })
    scored.sort(key=lambda x: x["match_pct"], reverse=True)
    return scored


def best_profile_match(
    profiles: list[dict[str, Any]],
    title: str,
    description: str = "",
    specialty: str = "",
    location: str = "",
    state: str = "",
) -> tuple[str, str, int]:
    """Return (profile_id, profile_name, best_match_pct)."""
    if not profiles:
        return ("", "", score_resume_match_legacy(title, description, specialty, location, state))
    scored = score_all_profiles(profiles, title, description, specialty, location, state)
    best = scored[0]
    return (best["profile_id"], best["profile_name"], best["match_pct"])


def score_resume_match(
    title: str,
    description: str = "",
    specialty: str = "",
    location: str = "",
    state: str = "",
    profiles: list[dict[str, Any]] | None = None,
) -> int:
    if profiles:
        _, _, pct = best_profile_match(profiles, title, description, specialty, location, state)
        return pct
    return score_resume_match_legacy(title, description, specialty, location, state)


def score_resume_match_legacy(
    title: str,
    description: str = "",
    specialty: str = "",
    location: str = "",
    state: str = "",
) -> int:
    fake_profile = {
        "resume_text": f"{specialty} {location} {state}",
        "specialty": specialty,
        "experience_level": "",
        "preferred_states": [state] if state else config.AU_LOCATIONS[:2],
        "keywords": config.KEYWORDS[:6],
    }
    return score_job_for_profile(fake_profile, title, description, specialty, location, state)


def match_label(score: int) -> str:
    if score >= config.HIGH_MATCH_THRESHOLD:
        return "High Match"
    if score >= 50:
        return "Good Match"
    if score >= 30:
        return "Partial Match"
    return "Low Match"
