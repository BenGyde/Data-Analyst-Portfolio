# Pulse HR — People Analytics Dashboard using Python and Plotly Dash
 
<img width="1495" height="971" alt="Animation" src="https://github.com/user-attachments/assets/dd2ed395-d022-411c-96d2-f166619e5576" />
 
## Problem statement
 
HR and finance teams often track attendance, leave requests, and performance across separate spreadsheets and systems.
Getting a single live view — filterable by location — usually means manual exports and repeated copy-pasting.
 
## Solution & Features
 
- **Live Filtering**: Location dropdown instantly updates every KPI, chart, and table — no page reload.
- **Attendance Tracking**: 30-day attendance rate trend with daily present/absent breakdown.
- **Headcount Overview**: Department distribution at a glance.
- **Leave Management**: Leave requests by type, plus a pending approvals queue.
- **Compensation Insights**: Average monthly compensation by job level (base, allowance, bonus).
- **Performance Monitoring**: 12-month average performance score trend.

## File reference
 
| Name | File     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `app.py`      | `PY` | The Dash application (layout, charts, callbacks) |
| `generate_hr_data.py`      | `PY` | Seeded synthetic data generator |
| `assets/style.css`      | `CSS` | Custom design system for the dashboard |
| `data/employees.csv`      | `CSV` | 180 synthetic employee records |
| `data/attendance.csv`      | `CSV` | ~20,000 daily attendance records |
| `data/leave_requests.csv`      | `CSV` | 320 synthetic leave requests |
| `data/performance.csv`      | `CSV` | ~2,000 monthly performance scores |
 
## Dataset dictionary
 
| Table | Key fields |
| :-------- | :------- |
| `employees.csv` | `employee_id`, `department`, `role`, `job_level`, `location`, `hire_date`, `monthly_salary_pln`, `monthly_language_allowance_pln`, `monthly_bonus_base_pln`, `status` |
| `attendance.csv` | `date`, `employee_id`, `status` (Office / Remote / Absent / On Leave), `check_in` |
| `leave_requests.csv` | `leave_type`, `start_date`, `end_date`, `days`, `status` |
| `performance.csv` | `month`, `employee_id`, `performance_score` |
 
All data is 100% synthetic and reproducible — no real individuals or companies.
 
## Quick start
 
```bash
pip install -r requirements.txt
python app.py        # → http://127.0.0.1:8050
```
 
Regenerate the dataset with different parameters:
 
```bash
python generate_hr_data.py
```
 
## Built with
 
- Python
- Plotly Dash
- pandas / numpy
