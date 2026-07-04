"""
Fake HR dataset generator — "Northwind People Analytics"
Reproducible synthetic data for practicing HR dashboards (Plotly Dash / Streamlit / Power BI).

Outputs:
  employees.csv        - 180 employees, master data
  attendance.csv       - daily records, last 120 working days
  leave_requests.csv   - paid-leave / sick / unpaid requests
  performance.csv      - monthly performance score per employee

Run:  python generate_hr_data.py
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(42)

# ---------------------------------------------------------------- employees
N = 180
TODAY = date(2026, 7, 3)

first = ["Adam","Anna","Piotr","Kasia","Marek","Ola","Jan","Magda","Tomek","Ewa",
         "Ben","Lotte","Daan","Sanne","Milan","Femke","Lars","Iris","Noor","Sem",
         "James","Emily","Oliver","Sophie","Lucas","Mia","Ethan","Clara","Leo","Nina"]
last  = ["Kowalski","Nowak","Wisniewski","Wojcik","Kaminski","Lewandowski","Zielinski",
         "De Vries","Jansen","Bakker","Visser","Smit","Meijer","Mulder",
         "Smith","Brown","Taylor","Wilson","Evans","Thomas","Roberts","Walker"]

departments = {
    "Finance Operations": 0.28, "Engineering": 0.22, "Customer Success": 0.16,
    "Sales": 0.12, "HR": 0.08, "Marketing": 0.08, "IT Support": 0.06,
}
roles = {
    "Finance Operations": ["Credit Analyst","Collections Analyst","AR Specialist","Finance Automation Developer","Team Lead"],
    "Engineering": ["Backend Developer","Frontend Developer","Fullstack Developer","Data Engineer","QA Engineer"],
    "Customer Success": ["Support Specialist","Account Manager","Onboarding Specialist"],
    "Sales": ["Sales Executive","Sales Ops Analyst","Business Developer"],
    "HR": ["HR Generalist","Recruiter","People Analyst"],
    "Marketing": ["Content Specialist","Performance Marketer","Designer"],
    "IT Support": ["IT Support Specialist","System Administrator"],
}
levels = ["Junior Staff","Middle Staff","Senior Staff","Lead"]
level_p = [0.30, 0.38, 0.24, 0.08]
locations = ["Krakow","Warsaw","Amsterdam","Remote"]
loc_p = [0.52, 0.20, 0.14, 0.14]

dept_col = rng.choice(list(departments), size=N, p=list(departments.values()))
rows = []
for i in range(N):
    d = dept_col[i]
    lvl = rng.choice(levels, p=level_p)
    base = {"Junior Staff": 7500, "Middle Staff": 11000, "Senior Staff": 16000, "Lead": 21000}[lvl]
    salary = int(rng.normal(base, base * 0.12) // 100 * 100)
    hire = TODAY - timedelta(days=int(rng.integers(60, 2900)))
    active = rng.random() > 0.06
    # fake comp structure: base + optional language allowance + performance bonus base
    has_lang = rng.random() < 0.35
    lang_allowance = int(rng.choice([1500, 2000, 2500, 3000])) if has_lang else 0
    bonus_base = int(base * rng.choice([0.05, 0.08, 0.10, 0.12]))
    rows.append({
        "employee_id": f"E{1000+i}",
        "name": f"{rng.choice(first)} {rng.choice(last)}",
        "department": d,
        "role": rng.choice(roles[d]),
        "job_level": lvl,
        "location": rng.choice(locations, p=loc_p),
        "hire_date": hire.isoformat(),
        "monthly_salary_pln": max(salary, 5500),
        "monthly_language_allowance_pln": lang_allowance,
        "monthly_bonus_base_pln": bonus_base,
        "status": "Active" if active else "Terminated",
    })
emp = pd.DataFrame(rows)
emp.to_csv("employees.csv", index=False)

active_ids = emp.loc[emp.status == "Active", "employee_id"].to_numpy()

# --------------------------------------------------------------- attendance
workdays = pd.bdate_range(end=TODAY, periods=120)
att = []
# per-employee reliability so people have personalities
reliability = {e: rng.beta(9, 1.2) for e in active_ids}
remote_pref = {e: rng.beta(2, 4) for e in active_ids}

for d in workdays:
    season = 0.03 if d.month in (7, 8, 12) else 0.0   # holiday season dip
    for e in active_ids:
        r = rng.random()
        p_absent = (1 - reliability[e]) * 0.35 + season
        p_leave = 0.035 + season
        if r < p_absent:
            status = "Absent"; check_in = None
        elif r < p_absent + p_leave:
            status = "On Leave"; check_in = None
        else:
            status = "Remote" if rng.random() < remote_pref[e] else "Office"
            check_in = f"{rng.integers(7, 10):02d}:{rng.integers(0, 60):02d}"
        att.append((d.date().isoformat(), e, status, check_in))

pd.DataFrame(att, columns=["date", "employee_id", "status", "check_in"]) \
  .to_csv("attendance.csv", index=False)

# ------------------------------------------------------------ leave requests
types = ["Paid Leave", "Sick Leave", "Unpaid Leave", "Parental Leave"]
type_p = [0.62, 0.24, 0.09, 0.05]
lr = []
for i in range(320):
    e = rng.choice(active_ids)
    start = TODAY - timedelta(days=int(rng.integers(-30, 150)))  # some future requests
    dur = int(rng.choice([1, 2, 3, 5, 10, 15], p=[0.3, 0.2, 0.18, 0.18, 0.1, 0.04]))
    submitted = start - timedelta(days=int(rng.integers(3, 40)))
    if start > TODAY:
        st = rng.choice(["Pending", "Approved", "Rejected"], p=[0.55, 0.38, 0.07])
    else:
        st = rng.choice(["Approved", "Rejected"], p=[0.93, 0.07])
    lr.append({
        "request_id": f"LR{2000+i}",
        "employee_id": e,
        "leave_type": rng.choice(types, p=type_p),
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=dur - 1)).isoformat(),
        "days": dur,
        "submitted_on": submitted.isoformat(),
        "status": st,
    })
pd.DataFrame(lr).to_csv("leave_requests.csv", index=False)

# -------------------------------------------------------------- performance
months = pd.period_range(end=TODAY, periods=12, freq="M")
perf = []
base_score = {e: rng.normal(74, 9) for e in active_ids}
for m in months:
    for e in active_ids:
        s = np.clip(base_score[e] + rng.normal(0, 5), 35, 100)
        perf.append({"month": str(m), "employee_id": e, "performance_score": round(s, 1)})
pd.DataFrame(perf).to_csv("performance.csv", index=False)

print("Done:",
      f"{len(emp)} employees,",
      f"{len(att)} attendance rows,",
      f"{len(lr)} leave requests,",
      f"{len(perf)} performance rows")
