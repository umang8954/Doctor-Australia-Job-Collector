# Phase 2: Data Validation Report

**Records reviewed:** 123
**Flagged (validation warnings):** 119
**Fuzzy title matches:** 2
**Would be filtered** (below threshold 30%): 53
**Filter active:** False

## Validation Logic Implemented

Module: `job_validator.py` — runs after fetch, before Excel write.

| Component | Weight | Notes |
|-----------|--------|-------|
| Title/role relevance | 40% | Fuzzy match of job title to profile specialty + level (proxy for identity; job boards have no doctor names) |
| Specialty alignment | 25% | Detected job specialty vs profile specialty |
| Location alignment | 20% | Job state vs profile preferred_states |
| Experience level | 15% | Job level vs profile experience_level |
| License/registration | N/A | Not exposed on AU hospital job portals — weight redistributed |

**Confidence threshold:** 30% (configurable in `config.py`)

## Per-Platform Summary

| Platform | Reviewed | Flagged | Fuzzy | Below threshold |
|----------|----------|---------|-------|-----------------|
| SmartJobs_QLD | 0 | — | — | — |
| Jobs_NT | 0 | — | — | — |
| Careers_VIC | 3 | 3 | 0 | 1 |
| Monash_Health | 23 | 22 | 0 | 8 |
| Western_Health | 16 | 16 | 0 | 12 |
| WA_Health | 24 | 24 | 1 | 9 |
| Mercy_Workday | 0 | — | — | — |
| Peninsula_Health | 0 | — | — | — |
| The_Womens | 1 | 0 | 0 | 0 |
| Grampians_Health | 14 | 13 | 1 | 6 |
| Eastern_Health | 11 | 10 | 0 | 1 |
| RCH | 7 | 7 | 0 | 0 |
| RANZCOG | 0 | — | — | — |
| RACP | 24 | 24 | 0 | 16 |
| JobRadars | 0 | — | — | — |
| PageUp | 0 | — | — | — |

## False-Positive Patterns

- **Common specialty overlap:** General Medicine jobs matched to multiple profiles
- **Fuzzy title matches:** Short titles (e.g. 'Registrar') match multiple specialties
- **Location gaps:** Jobs with empty state field score low on location despite being AU hospital jobs

## Sample Flagged Records

- **Careers_VIC** | Registrar - Medical Administration 2027 | Profile: Dr. Ananya Patel | Match: 38% | Flags: Weak title relevance, Specialty mismatch
- **Careers_VIC** | Registrar (Medical, Family Property and Defamation Lists) | Profile: Dr. Ananya Patel | Match: 37% | Flags: Weak title relevance, Specialty mismatch
- **Careers_VIC** | 2027 Endocrine/General Surgery Fellow | Profile: Dr. James Chen | Match: 16% | Flags: Weak title relevance, Specialty mismatch, Experience level mismatch
- **Monash_Health** | 2027 General Medicine Advanced Trainee | Profile: Dr. Michael O'Brien | Match: 41% | Flags: Weak title relevance, Experience level mismatch
- **Monash_Health** | 2026 Intensive Care Medicine Registrars - Dandenong and Case | Profile: Dr. Ananya Patel | Match: 39% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | 2027 Diabetes & Endocrinology Registrar - unaccredited | Profile: Dr. Priya Sharma | Match: 38% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | Consultant Paediatrician - Internal Locum | Profile: Dr. Michael O'Brien | Match: 36% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | 2027 Medical Administration Registrar | Profile: Dr. Ananya Patel | Match: 35% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | 2026 Anaesthetic Registrar | Profile: Dr. Ananya Patel | Match: 35% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | Consultant Paediatrician - Infectious Diseases Intenal Locum | Profile: Dr. Michael O'Brien | Match: 35% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | 2027 Psychiatry Unaccredited or Senior (RANZCP Stage 3) Regi | Profile: Dr. Ananya Patel | Match: 34% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | 2027 Dental Registrar | Profile: Dr. Ananya Patel | Match: 34% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | 2027 Anatomical Pathology Registrar | Profile: Dr. Ananya Patel | Match: 34% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | 2027 Obesity, Clinical Nutrition & Diabetes Clinical Registr | Profile: Dr. Ananya Patel | Match: 34% | Flags: Weak title relevance, Specialty mismatch
- **Monash_Health** | Consultant Paediatrician | Profile: Dr. Michael O'Brien | Match: 34% | Flags: Weak title relevance, Specialty mismatch
