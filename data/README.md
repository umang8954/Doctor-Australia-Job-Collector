# Doctor Job Collector - Data & Excel Guide

## Add your resumes (PDF)

Copy your file here:

```
data/Demo_Medical_Resumes.pdf
```

- One PDF page = one doctor profile
- Re-run `python job_collector.py` to extract profiles into `profiles.json`
- Until the PDF is added, 5 demo profiles in `profiles.json` are used

## Job_Tracker.xlsx structure

### 16 portal tabs (Australia doctor jobs only)

SmartJobs_QLD | Jobs_NT | Careers_VIC | Monash_Health | Western_Health | WA_Health |
Mercy_Workday | Peninsula_Health | The_Womens | Grampians_Health | Eastern_Health |
RCH | RANZCOG | RACP | JobRadars | PageUp

Each row: Job Title, Specialty, Hospital, Location, State, Salary, Posted Date,
Job Added On, **Apply Link**, Portal, **Best Profile**, **Match %**, Status, Applied?, Notes

### Profile tabs

| Tab | What it shows |
|-----|----------------|
| Doctor_Profiles | All doctors from PDF / profiles.json |
| Profile_Matches | Each job with match % for every doctor |
| All_Jobs_Australia | All portal jobs in one sheet |
| Apply_Queue | Best unapplied jobs (all doctors) |
| Queue_dr_* | Apply queue per doctor (sorted by Match %) |
| Daily_Summary | Jobs found per portal per run |

## Match scoring (per doctor)

Specialty 40% + Location 20% + Experience level 20% + Keywords 20%

Match % >= 70 = High Match (noted in Notes column)
