"""Quick test of the 7 previously failing portals."""
from job_utils import RunLogger
from extraction_runner import extract_jobs_multi_method
from scrapers import ALL_SCRAPERS

FAILING = [
    "peninsula_health",
    "jobs_nt",
    "mercy_workday",
    "ranzcog",
    "smartjobs_qld",
    "jobradars",
    "pageup",
]

logger = RunLogger()
for key in FAILING:
    fn = ALL_SCRAPERS[key]
    print(f"\n=== {key} ===")
    try:
        outcome = extract_jobs_multi_method(key, fn, logger)
        print(f"jobs={len(outcome.jobs)} method={outcome.method_used} error={outcome.error[:120] if outcome.error else 'None'}")
        if outcome.jobs:
            j = outcome.jobs[0]
            print(f" sample: {j.title[:60]}")
            print(f" link:  {j.apply_link[:80]}")
    except Exception as e:
        print(f"EXCEPTION: {e}")
