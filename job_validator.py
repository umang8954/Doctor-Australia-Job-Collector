"""
Job-to-profile validation and Match % scoring (Phases 2 & 3).

These portals list **vacancies**, not individual doctors — there is no AHPRA/license
number on job listings. Scoring uses fields actually available:

  Title/role relevance  40%  — fuzzy alignment of job title with profile specialty & level
  Specialty alignment   25%  — detected job specialty vs profile specialty
  Location alignment    20%  — job state/location vs profile preferred_states
  Experience level      15%  — job level vs profile experience_level

When a field is missing, its weight is redistributed proportionally across the
remaining fields (documented in score_job_validation docstring).

Configurable: VALIDATION_CONFIDENCE_THRESHOLD, VALIDATION_FILTER_BELOW_THRESHOLD
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

import config


@dataclass
class ValidationResult:
    """Outcome of validating one job against the best-matching doctor profile."""

    match_pct: int
    profile_id: str
    profile_name: str
    title_score: float
    specialty_score: float
    location_score: float
    experience_score: float
    license_score: float | None  # always None for job boards (field not exposed)
    flags: list[str] = field(default_factory=list)
    passed: bool = True
    title_match_type: str = "none"  # exact | fuzzy | none


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def _token_overlap(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-z0-9]+", _normalize(a)))
    tb = set(re.findall(r"[a-z0-9]+", _normalize(b)))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _fuzzy_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _score_specialty(job_specialty: str, profile: dict[str, Any], text: str) -> float:
    profile_spec = _normalize(profile.get("specialty", ""))
    if not profile_spec:
        return 0.0
    if job_specialty:
        js = _normalize(job_specialty)
        if js == profile_spec or js in profile_spec or profile_spec in js:
            return 1.0
        if _fuzzy_ratio(js, profile_spec) >= 0.65:
            return 0.85
    # fallback: specialty terms in combined job text
    spec_tokens = [profile_spec] + [s for s in config.SPECIALTY_KEYWORDS if s in profile_spec]
    hits = sum(1 for t in spec_tokens if t and t.lower() in text)
    return min(1.0, hits / max(len(spec_tokens), 1))


def _score_location(state: str, location: str, profile: dict[str, Any]) -> float:
    preferred = profile.get("preferred_states") or []
    if not preferred:
        return 0.5
    blob = _normalize(f"{state} {location}")
    hits = 0
    for loc in preferred:
        ln = _normalize(loc)
        if ln in blob or _normalize(config.STATE_ABBREVS.get(ln, "")) in blob:
            hits += 1
    if hits:
        return min(1.0, hits / len(preferred))
    if _normalize("australia") in blob:
        return 0.4
    return 0.0


def _score_experience(job_level: str, profile: dict[str, Any], text: str) -> float:
    profile_level = _normalize(profile.get("experience_level", ""))
    if not profile_level:
        return 0.5
    if job_level:
        jl = _normalize(job_level)
        if jl == profile_level or jl in profile_level or profile_level in jl:
            return 1.0
        if _fuzzy_ratio(jl, profile_level) >= 0.7:
            return 0.85
    if profile_level in text:
        return 0.75
    return _token_overlap(profile_level, text)


def _score_title_relevance(title: str, profile: dict[str, Any]) -> tuple[float, str]:
    """
    Proxy for 'name match': job title vs profile specialty + level + keywords.
    Exact token overlap -> 'exact'; fuzzy >= 0.55 -> 'fuzzy'; else 'none'.
    """
    profile_blob = " ".join(
        [
            profile.get("specialty", ""),
            profile.get("experience_level", ""),
            " ".join(profile.get("keywords") or []),
        ]
    )
    exact_overlap = _token_overlap(title, profile_blob)
    fuzzy = _fuzzy_ratio(title, profile_blob)
    score = max(exact_overlap, fuzzy * 0.9)
    if exact_overlap >= 0.35:
        return min(1.0, score), "exact"
    if fuzzy >= 0.55:
        return min(1.0, fuzzy), "fuzzy"
    return score, "none"


def _redistribute_weights(scores: dict[str, float | None], weights: dict[str, float]) -> float:
    """Sum weighted scores; redistribute weight when license (or other) field is N/A."""
    active = {k: w for k, w in weights.items() if scores.get(k) is not None}
    total_w = sum(active.values())
    if total_w <= 0:
        return 0.0
    return sum((scores[k] or 0.0) * (w / total_w) for k, w in active.items())


def score_job_validation(
    profile: dict[str, Any],
    title: str,
    description: str = "",
    specialty: str = "",
    location: str = "",
    state: str = "",
    experience_level: str = "",
) -> ValidationResult:
    """
    Score one job against one doctor profile (0–100).

    Weight defaults (config.VALIDATION_WEIGHTS):
      title_relevance 40%, specialty 25%, location 20%, experience 15%.
    License/registration is NOT available on AU hospital job boards — weight omitted.
    """
    text = _normalize(f"{title} {description} {specialty} {location} {state} {experience_level}")
    weights = config.VALIDATION_WEIGHTS

    title_score, title_match_type = _score_title_relevance(title, profile)
    specialty_score = _score_specialty(specialty, profile, text)
    location_score = _score_location(state, location, profile)
    experience_score = _score_experience(experience_level, profile, text)

    scores = {
        "title_relevance": title_score,
        "specialty": specialty_score,
        "location": location_score,
        "experience": experience_score,
        "license": None,
    }
    total = _redistribute_weights(scores, weights)
    match_pct = min(100, max(0, int(round(total * 100))))

    flags: list[str] = []
    if title_match_type == "fuzzy":
        flags.append("Fuzzy title match")
    elif title_match_type == "none" and match_pct < 50:
        flags.append("Weak title relevance")
    if specialty_score < 0.3 and profile.get("specialty"):
        flags.append("Specialty mismatch")
    if location_score < 0.2 and profile.get("preferred_states"):
        flags.append("Location mismatch")
    if experience_score < 0.3 and profile.get("experience_level"):
        flags.append("Experience level mismatch")

    passed = match_pct >= config.VALIDATION_CONFIDENCE_THRESHOLD

    return ValidationResult(
        match_pct=match_pct,
        profile_id=profile.get("id", ""),
        profile_name=profile.get("name", ""),
        title_score=title_score,
        specialty_score=specialty_score,
        location_score=location_score,
        experience_score=experience_score,
        license_score=None,
        flags=flags,
        passed=passed,
        title_match_type=title_match_type,
    )


def validate_job_against_profiles(
    profiles: list[dict[str, Any]],
    title: str,
    description: str = "",
    specialty: str = "",
    location: str = "",
    state: str = "",
    experience_level: str = "",
) -> ValidationResult:
    """Pick best profile and return its validation result."""
    if not profiles:
        return ValidationResult(
            match_pct=0,
            profile_id="",
            profile_name="",
            title_score=0,
            specialty_score=0,
            location_score=0,
            experience_score=0,
            license_score=None,
            flags=["No profiles loaded"],
            passed=False,
        )
    best: ValidationResult | None = None
    for profile in profiles:
        result = score_job_validation(
            profile, title, description, specialty, location, state, experience_level
        )
        if best is None or result.match_pct > best.match_pct:
            best = result
    return best  # type: ignore[return-value]


def apply_validation_to_job(job, profiles: list[dict[str, Any]]) -> bool:
    """
    Run validation on a JobRecord; set match_pct, notes flags.
    Returns False if job should be filtered out (when VALIDATION_FILTER_BELOW_THRESHOLD).
    """
    result = validate_job_against_profiles(
        profiles,
        job.title,
        job.description,
        job.specialty,
        job.location,
        job.state,
        job.experience_level,
    )
    job.match_pct = result.match_pct
    job.validation_flags = "; ".join(result.flags)
    if result.flags:
        flag_str = job.validation_flags
        if flag_str not in (job.notes or ""):
            job.notes = f"{flag_str} | {job.notes}".strip(" |")
    if not result.passed and config.VALIDATION_FILTER_BELOW_THRESHOLD:
        return False
    return True
