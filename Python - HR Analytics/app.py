"""
Pulse HR — People Analytics dashboard
Plotly Dash implementation of the HTML mockup.

Run:  python app.py  →  http://127.0.0.1:8050
"""

import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go

# ---------------------------------------------------------------- data
emp = pd.read_csv("data/employees.csv")
att = pd.read_csv("data/attendance.csv", parse_dates=["date"])
leave = pd.read_csv("data/leave_requests.csv", parse_dates=["start_date"])
perf = pd.read_csv("data/performance.csv")

active = emp[emp.status == "Active"]
LOCATIONS = ["All locations"] + sorted(active.location.unique())

PURPLE, PURPLE_SOFT, GRID = "#6d4ef5", "#d8cdfd", "#eef0f5"
BASE_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", size=11.5, color="#5b6172"),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=44, r=12, t=8, b=34), showlegend=False,
)
CONFIG = {"displayModeBar": False, "responsive": True}


# ---------------------------------------------------------------- helpers
def filter_ids(location):
    pool = active if location == "All locations" else active[active.location == location]
    return pool, set(pool.employee_id)


def kpi_card(label, value, sub, delta, up=True):
    return html.Div(className="card kpi", children=[
        html.Div(className="lab", children=label),
        html.Div(className="val", children=value),
        html.Div(className="cmp", children=[
            html.Span(delta, className=f"delta {'up' if up else 'down'}"),
            html.Span(sub),
        ]),
    ])


def initials(name):
    return "".join(w[0] for w in name.split()[:2]).upper()


DOT_COLORS = ["#7a55ff", "#e86e5a", "#1eae6f", "#d98a12", "#3f8cff"]


# ---------------------------------------------------------------- figures
def fig_attendance(ids):
    d = att[att.employee_id.isin(ids)]
    days = sorted(d.date.unique())[-30:]
    d = d[d.date.isin(days)]
    rate = d.groupby("date").apply(
        lambda g: g.status.isin(["Office", "Remote"]).mean() * 100,
        include_groups=False).round(1)
    fig = go.Figure(go.Scatter(
        x=[t.strftime("%b %d") for t in rate.index], y=rate.values,
        mode="lines", line=dict(color=PURPLE, width=2.6, shape="spline", smoothing=0.8),
        fill="tozeroy", fillcolor="rgba(109,78,245,0.10)",
        hovertemplate="%{x}<br><b>%{y:.1f}%</b> present<extra></extra>"))
    fig.update_layout(**BASE_LAYOUT,
        yaxis=dict(range=[70, 100], ticksuffix="%", gridcolor=GRID, zeroline=False),
        xaxis=dict(showgrid=False, tickmode="array",
                   tickvals=[t.strftime("%b %d") for t in list(rate.index)[::5]]))
    return fig, rate


def fig_departments(pool):
    counts = pool.department.value_counts().sort_values()
    colors = [PURPLE if v >= counts.max() * 0.5 else PURPLE_SOFT for v in counts.values]
    fig = go.Figure(go.Bar(
        x=counts.values, y=counts.index, orientation="h",
        marker=dict(color=colors, cornerradius=6),
        text=counts.values, textposition="outside",
        textfont=dict(color="#171a26", size=12),
        hovertemplate="%{y}: <b>%{x}</b> people<extra></extra>"))
    layout = BASE_LAYOUT | {"margin": dict(l=130, r=30, t=4, b=26)}
    fig.update_layout(**layout,
        xaxis=dict(gridcolor=GRID, zeroline=False), yaxis=dict(showgrid=False))
    return fig


def fig_leave(ids):
    d = leave[leave.employee_id.isin(ids)]
    counts = d.leave_type.value_counts()
    fig = go.Figure(go.Pie(
        values=counts.values, labels=counts.index, hole=0.62,
        marker=dict(colors=[PURPLE, "#a68bff", "#d8cdfd", "#efeaff"]),
        textinfo="none",
        hovertemplate="%{label}: <b>%{value}</b> (%{percent})<extra></extra>"))
    layout = BASE_LAYOUT | {"showlegend": True, "margin": dict(l=10, r=10, t=6, b=10)}
    fig.update_layout(**layout,
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=11)),
        annotations=[dict(
            text=f"<b style='font-size:22px'>{len(d)}</b><br>"
                 "<span style='color:#9aa0b0'>requests</span>",
            showarrow=False, font=dict(size=13, color="#171a26"))])
    return fig


def fig_compensation(pool):
    order = ["Junior Staff", "Middle Staff", "Senior Staff", "Lead"]
    g = pool.groupby("job_level")[
        ["monthly_salary_pln", "monthly_language_allowance_pln",
         "monthly_bonus_base_pln"]].mean().reindex(order).round(0)
    parts = [("Base salary", "monthly_salary_pln", PURPLE),
             ("Language allowance", "monthly_language_allowance_pln", "#a68bff"),
             ("Bonus base", "monthly_bonus_base_pln", "#d8cdfd")]
    fig = go.Figure([go.Bar(
        name=n, x=order, y=g[c], marker=dict(color=col, cornerradius=4),
        hovertemplate="%{x}<br>" + n + ": <b>%{y:,.0f} PLN</b><extra></extra>")
        for n, c, col in parts])
    layout = BASE_LAYOUT | {"showlegend": True,
                            "margin": dict(l=52, r=8, t=6, b=28)}
    fig.update_layout(**layout, barmode="stack",
        legend=dict(orientation="h", y=1.14, x=0.5, xanchor="center",
                    font=dict(size=11)),
        yaxis=dict(gridcolor=GRID, zeroline=False, tickformat=",.0f"),
        xaxis=dict(showgrid=False, tickfont=dict(size=11)))
    return fig


def fig_performance(ids):
    d = perf[perf.employee_id.isin(ids)]
    monthly = d.groupby("month").performance_score.mean().round(1)
    labels = [pd.Period(m).strftime("%b") for m in monthly.index]
    colors = [PURPLE if v >= monthly.mean() else PURPLE_SOFT for v in monthly.values]
    fig = go.Figure(go.Bar(
        x=labels, y=monthly.values, marker=dict(color=colors, cornerradius=5),
        hovertemplate="%{x}: <b>%{y}</b><extra></extra>"))
    layout = BASE_LAYOUT | {"margin": dict(l=36, r=8, t=6, b=28)}
    fig.update_layout(**layout,
        yaxis=dict(range=[monthly.min() - 3, monthly.max() + 2],
                   gridcolor=GRID, zeroline=False),
        xaxis=dict(showgrid=False, tickfont=dict(size=10.5)))
    return fig


# ---------------------------------------------------------------- static pieces
def nav(label, active_item=False, badge=None):
    kids = [html.Span(label)]
    if badge:
        kids.append(html.Span(badge, className="pill"))
    return html.Div(kids, className="nav on" if active_item else "nav")


sidebar = html.Aside(className="side", children=[
    html.Div(className="brand", children=[
        html.Div("P", className="logo"),
        html.Div([html.B("Pulse HR"), html.Span("People Analytics")]),
    ]),
    html.H6("MENU"),
    nav("Dashboard", active_item=True),
    nav("Employees"),
    nav("Attendance", badge=str((leave.status == "Pending").sum())),
    nav("Leave Requests"),
    nav("Payroll"),
    html.H6("ANALYTICS"),
    nav("Performance"),
    nav("Reports"),
    nav("Settings"),
    html.Div(className="foot", children=[
        html.B("POWERED BY"), html.Br(),
        "Python · Plotly Dash · pandas", html.Br(),
        "Synthetic dataset · 20k rows",
    ]),
])


def pending_rows():
    d = (leave[leave.status == "Pending"]
         .sort_values("start_date").head(4)
         .merge(emp[["employee_id", "name"]], on="employee_id"))
    rows = []
    for i, r in enumerate(d.itertuples()):
        rows.append(html.Div(className="row", children=[
            html.Div(initials(r.name), className="dot",
                     style={"background": DOT_COLORS[i % len(DOT_COLORS)]}),
            html.Div([html.B(r.name), html.Span(f"{r.leave_type} · {r.days} days")]),
            html.Div(r.start_date.strftime("%b %d"), className="when"),
        ]))
    return rows


# ---------------------------------------------------------------- layout
app = Dash(__name__, title="Pulse HR — People Analytics")

app.layout = html.Div(className="frame", children=[
    sidebar,
    html.Div(className="main", children=[

        html.Div(className="topbar", children=[
            html.Div(className="who-wrap", children=[
                html.Div("BG", className="avatar"),
                html.Div(className="who",
                         children=[html.B("Ben Gydé"), html.Span("People Analytics")]),
            ]),
        ]),

        html.Div(className="hero", children=[
            html.Div([
                html.H1("Hi, Ben 👋"),
                html.P(f"{(leave.status == 'Pending').sum()} leave requests are "
                       "waiting for review before the July holiday peak."),
            ]),
            html.Button("Review requests"),
        ]),

        html.Div(className="layout", children=[

            # ------------------------------------------------ left column
            html.Div(className="col", children=[
                html.Div(id="kpi-row", className="grid"),

                html.Div(className="card", children=[
                    html.Div(className="head", children=[
                        html.H3("Attendance Rate — Last 30 Working Days"),
                        dcc.Dropdown(LOCATIONS, "All locations", id="location",
                                     clearable=False, className="loc-dd"),
                    ]),
                    dcc.Graph(id="attendance-chart", config=CONFIG,
                              style={"height": "300px"}),
                ]),

                html.Div(className="card", children=[
                    html.Div(className="head",
                             children=[html.H3("Headcount by Department")]),
                    dcc.Graph(id="dept-chart", config=CONFIG,
                              style={"height": "260px"}),
                ]),

                html.Div(className="card", children=[
                    html.Div(className="head", children=[
                        html.H3("Avg Monthly Compensation by Job Level"),
                        html.Span(id="payroll-chip", className="chip"),
                    ]),
                    dcc.Graph(id="comp-chart", config=CONFIG,
                              style={"height": "280px"}),
                ]),

                html.Div(className="card", children=[
                    html.Div(className="head", children=[html.H3("Employee Status")]),
                    html.Div(id="emp-table"),
                ]),
            ]),

            # ------------------------------------------------ right column
            html.Div(className="col", children=[
                html.Div(className="card", children=[
                    html.Div(className="head",
                             children=[html.H3("Leave Requests by Type")]),
                    dcc.Graph(id="leave-chart", config=CONFIG,
                              style={"height": "250px"}),
                ]),
                html.Div(className="card", children=[
                    html.Div(className="head", children=[
                        html.H3("Pending Approvals"),
                        html.Span(str((leave.status == "Pending").sum()),
                                  className="chip"),
                    ]),
                    *pending_rows(),
                ]),
                html.Div(className="card", children=[
                    html.Div(className="head",
                             children=[html.H3("Avg Performance Score")]),
                    dcc.Graph(id="perf-chart", config=CONFIG,
                              style={"height": "210px"}),
                ]),
            ]),
        ]),
    ]),
])


# ---------------------------------------------------------------- callbacks
@app.callback(
    Output("kpi-row", "children"),
    Output("attendance-chart", "figure"),
    Output("dept-chart", "figure"),
    Output("leave-chart", "figure"),
    Output("comp-chart", "figure"),
    Output("payroll-chip", "children"),
    Output("perf-chart", "figure"),
    Output("emp-table", "children"),
    Input("location", "value"),
)
def update(location):
    pool, ids = filter_ids(location)
    att_fig, rate = fig_attendance(ids)

    today_rate = rate.iloc[-1]
    yesterday = rate.iloc[-2]
    delta = today_rate - yesterday
    present_today = int(round(today_rate / 100 * len(pool)))
    pending = leave[(leave.status == "Pending") & leave.employee_id.isin(ids)]

    kpis = [
        kpi_card("Active Employees", f"{len(pool)}",
                 "In selected location", "↗ 4.2%"),
        kpi_card("Today Attendance", f"{present_today}",
                 f"{today_rate:.1f}% · vs yesterday",
                 f"{'↗' if delta >= 0 else '↘'} {abs(delta):.1f}pp", up=delta >= 0),
        kpi_card("Pending Leave Requests", f"{len(pending)}",
                 "Awaiting approval", "↗ 12%"),
    ]

    sample = pool.sample(min(5, len(pool)), random_state=7)
    rows = [html.Tr([html.Th(h) for h in
                     ["Name", "Role", "Department", "Job Level", "Status"]])]
    for i, r in enumerate(sample.itertuples()):
        rows.append(html.Tr([
            html.Td(html.Span([
                html.Span(initials(r.name), className="dot",
                          style={"background": DOT_COLORS[i % len(DOT_COLORS)]}),
                r.name], className="p")),
            html.Td(r.role, className="muted"),
            html.Td(r.department, className="muted"),
            html.Td(r.job_level, className="muted"),
            html.Td(html.Span("Active", className="st a")),
        ]))

    payroll = (pool.monthly_salary_pln + pool.monthly_language_allowance_pln).sum()
    chip = f"Total payroll: {payroll/1e6:.2f}M PLN / month"

    return (kpis, att_fig, fig_departments(pool), fig_leave(ids),
            fig_compensation(pool), chip,
            fig_performance(ids), html.Table(rows))


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
