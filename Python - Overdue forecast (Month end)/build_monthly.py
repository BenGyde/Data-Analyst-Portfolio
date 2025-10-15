# build_monthly.py
import argparse
import pandas as pd
import numpy as np
from collections import defaultdict
from pathlib import Path

def me(d):  # convert any date to month-end
    return pd.Timestamp(d).to_period("M").to_timestamp("M")

def add_diff(dct, key, start_me, end_me_inclusive, value):
    """Add +value from start_me..end_me inclusive using a difference-array."""
    if value == 0 or pd.isna(start_me) or pd.isna(end_me_inclusive):
        return
    dct[key][start_me] += value
    after_end = end_me_inclusive + pd.offsets.MonthEnd(1)
    dct[key][after_end] -= value

def main(inp, outp):
    # -------- 1) Load with resilient parsing --------
    req_cols = {
        "InvoiceDate","DueDate","PaymentDate","AsOfDate","Country","CountryCode","Currency",
        "InvoiceAmount_LCY","PaidAmount_LCY","FX_to_EUR"
    }
    print(f"Reading: {inp}")
    df = pd.read_csv(
        inp,
        parse_dates=["InvoiceDate","DueDate","PaymentDate","AsOfDate"],
        keep_default_na=True,
        na_values=["", "NaN", "NA", "None", "NaT"]
    )

    missing = req_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {inp}: {sorted(missing)}")

    # Safeguard numeric types
    df["InvoiceAmount_LCY"] = pd.to_numeric(df["InvoiceAmount_LCY"], errors="coerce").fillna(0.0)
    df["PaidAmount_LCY"]    = pd.to_numeric(df["PaidAmount_LCY"], errors="coerce").fillna(0.0)
    df["FX_to_EUR"]         = pd.to_numeric(df["FX_to_EUR"], errors="coerce").fillna(1.0)

    # -------- 2) Panel time range (month-ends) --------
    start_me = df["InvoiceDate"].min().to_period("M").to_timestamp("M")
    end_me   = df["AsOfDate"].max().to_period("M").to_timestamp("M")
    all_months = pd.date_range(start_me, end_me, freq="M")
    print(f"Building series from {start_me.date()} to {end_me.date()} ({len(all_months)} months)")

    # -------- 3) Difference arrays per country --------
    od_diff_lcy = defaultdict(lambda: defaultdict(float))
    od_diff_eur = defaultdict(lambda: defaultdict(float))
    od_cnt_diff = defaultdict(lambda: defaultdict(int))
    open_diff_lcy = defaultdict(lambda: defaultdict(float))
    open_diff_eur = defaultdict(lambda: defaultdict(float))

    asof_end = all_months.max()

    for r in df.itertuples(index=False):
        country = r.Country
        fx = float(r.FX_to_EUR)
        amt = float(r.InvoiceAmount_LCY)
        paid = float(r.PaidAmount_LCY)
        amt_eur = amt * fx

        inv_me = me(r.InvoiceDate)
        due_me = me(r.DueDate)
        pay_dt = pd.to_datetime(r.PaymentDate) if pd.notna(r.PaymentDate) else pd.NaT
        residual = max(0.0, amt - paid)

        # ---- Open balance: from invoice month-end until fully paid; residual persists if partial ----
        if pd.isna(pay_dt):  # unpaid
            add_diff(open_diff_lcy, country, inv_me, asof_end, amt)
            add_diff(open_diff_eur, country, inv_me, asof_end, amt_eur)
        else:
            pay_me = me(pay_dt)
            if paid >= amt:  # fully paid before/at pay_me
                prev_me = pay_me - pd.offsets.MonthEnd(1)
                if inv_me <= prev_me:
                    add_diff(open_diff_lcy, country, inv_me, prev_me, amt)
                    add_diff(open_diff_eur, country, inv_me, prev_me, amt_eur)
            else:  # partial: full until payment, then residual onwards
                prev_me = pay_me - pd.offsets.MonthEnd(1)
                if inv_me <= prev_me:
                    add_diff(open_diff_lcy, country, inv_me, prev_me, amt)
                    add_diff(open_diff_eur, country, inv_me, prev_me, amt_eur)
                add_diff(open_diff_lcy, country, pay_me, asof_end, residual)
                add_diff(open_diff_eur, country, pay_me, asof_end, residual * fx)

        # ---- Overdue balance: starts at due month-end if still unpaid/part-paid ----
        start_od = due_me
        if asof_end <= start_od:
            continue  # never overdue within the panel

        if pd.isna(pay_dt):  # unpaid
            add_diff(od_diff_lcy, country, start_od, asof_end, amt)
            add_diff(od_diff_eur, country, start_od, asof_end, amt_eur)
            add_diff(od_cnt_diff, country, start_od, asof_end, 1)
        else:
            pay_me = me(pay_dt)
            if pay_me <= start_od and paid >= amt:
                pass  # fully paid before overdue
            elif pay_me <= start_od and paid < amt:
                add_diff(od_diff_lcy, country, start_od, asof_end, residual)
                add_diff(od_diff_eur, country, start_od, asof_end, residual * fx)
                add_diff(od_cnt_diff, country, start_od, asof_end, 1)
            elif pay_me > start_od and paid >= amt:
                prev_me = pay_me - pd.offsets.MonthEnd(1)
                add_diff(od_diff_lcy, country, start_od, prev_me, amt)
                add_diff(od_diff_eur, country, start_od, prev_me, amt_eur)
                add_diff(od_cnt_diff, country, start_od, prev_me, 1)
            else:  # pay_me > start_od and partial
                prev_me = pay_me - pd.offsets.MonthEnd(1)
                add_diff(od_diff_lcy, country, start_od, prev_me, amt)
                add_diff(od_diff_eur, country, start_od, prev_me, amt_eur)
                add_diff(od_cnt_diff, country, start_od, prev_me, 1)
                add_diff(od_diff_lcy, country, pay_me, asof_end, residual)
                add_diff(od_diff_eur, country, pay_me, asof_end, residual * fx)
                add_diff(od_cnt_diff, country, pay_me, asof_end, 1)

    # -------- 4) Turn diffs → time series panel --------
    countries = df[["Country","CountryCode","Currency"]].drop_duplicates()
    rows = []
    for c in countries.itertuples(index=False):
        country, code, curr = c.Country, c.CountryCode, c.Currency
        od_lcy = od_eur = open_lcy = open_eur = 0.0
        cnt = 0
        for m in all_months:
            od_lcy   += od_diff_lcy[country].get(m, 0.0)
            od_eur   += od_diff_eur[country].get(m, 0.0)
            cnt      += od_cnt_diff[country].get(m, 0)
            open_lcy += open_diff_lcy[country].get(m, 0.0)
            open_eur += open_diff_eur[country].get(m, 0.0)
            rows.append({
                "MonthEnd": m,
                "Country": country,
                "CountryCode": code,
                "Currency": curr,
                "OverdueAmount_LCY": max(0.0, od_lcy),
                "OverdueAmount_EUR": max(0.0, od_eur),
                "OverdueInvoices": max(0, cnt),
                "OpenBalance_LCY": max(0.0, open_lcy),
                "OpenBalance_EUR": max(0.0, open_eur)
            })

    monthly = pd.DataFrame(rows)
    monthly["Year"] = monthly["MonthEnd"].dt.year
    monthly["Month"] = monthly["MonthEnd"].dt.month
    monthly["YearMonth"] = monthly["MonthEnd"].dt.to_period("M").astype(str)

    monthly.to_csv(outp, index=False, encoding="utf-8")
    print(f"✅ Wrote {outp} with {len(monthly)} rows")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="ar_invoices_sample.csv")
    ap.add_argument("--out", dest="outp", default="ar_country_monthly.csv")
    args = ap.parse_args()
    main(args.inp, args.outp)