# forecast_sarimax.py
import argparse
import warnings
import pandas as pd
import numpy as np
from pathlib import Path
import itertools
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tools.sm_exceptions import ConvergenceWarning

warnings.simplefilter("ignore", ConvergenceWarning)
warnings.simplefilter("ignore", FutureWarning)

def mape(y_true, y_pred, eps=1e-8):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    denom = np.where(np.abs(y_true) < eps, eps, np.abs(y_true))
    return np.mean(np.abs((y_true - y_pred) / denom)) * 100.0

def smape(y_true, y_pred, eps=1e-8):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    denom = np.maximum((np.abs(y_true) + np.abs(y_pred)) / 2.0, eps)
    return np.mean(np.abs(y_pred - y_true) / denom) * 100.0

def month_ends_after(last_me, h):
    # Generate next h month-ends after last_me
    # last_me is already month-end; we step forward by month
    return pd.date_range(last_me + pd.offsets.MonthEnd(1), periods=h, freq="M")

def try_fit(endog, order, sorder, enforce_stationarity=False, enforce_invertibility=False):
    model = SARIMAX(
        endog,
        order=order,
        seasonal_order=sorder,
        trend="n",
        enforce_stationarity=enforce_stationarity,
        enforce_invertibility=enforce_invertibility
    )
    res = model.fit(disp=False)
    return res

def main(infile, horizon, val_months, out_forecast, out_summary):
    df = pd.read_csv(infile, parse_dates=["MonthEnd"])
    # We’ll forecast OverdueAmount_EUR
    target_col = "OverdueAmount_EUR"
    assert target_col in df.columns, f"{target_col} missing in {infile}"

    countries = sorted(df["Country"].unique())
    print(f"Found {len(countries)} countries: {countries}")

    # Small grid (kept intentionally tiny for speed + stability)
    p = d = q = [0, 1]
    P = D = Q = [0, 1]
    m = 12  # monthly seasonality
    order_grid = list(itertools.product(p, d, q))
    sorder_grid = [(P_i, D_i, Q_i, m) for P_i in P for D_i in D for Q_i in Q]

    all_fc_rows = []
    all_summ_rows = []

    for country in countries:
        ts = (
            df[df["Country"] == country]
            .sort_values("MonthEnd")
            .set_index("MonthEnd")[target_col]
            .astype(float)
        )

        # Sanity: need enough points
        if len(ts) < (val_months + 12):
            print(f"[{country}] Too few points ({len(ts)}). Skipping.")
            continue

        # Train/validation split
        train = ts.iloc[:-val_months]
        valid = ts.iloc[-val_months:]

        best = {
            "mape": np.inf, "smape": np.inf,
            "order": None, "sorder": None, "res": None
        }

        # Model selection loop (tiny grid)
        for order in order_grid:
            for sorder in sorder_grid:
                try:
                    res = try_fit(train, order, sorder)
                    pred = res.get_forecast(steps=len(valid)).predicted_mean
                    cur_mape = mape(valid.values, pred.values)
                    cur_smape = smape(valid.values, pred.values)
                    if cur_mape < best["mape"]:
                        best.update({"mape": cur_mape, "smape": cur_smape,
                                     "order": order, "sorder": sorder, "res": res})
                except Exception:
                    # Try relaxing stationarity/invertibility if failure
                    try:
                        res = try_fit(train, order, sorder,
                                      enforce_stationarity=False,
                                      enforce_invertibility=False)
                        pred = res.get_forecast(steps=len(valid)).predicted_mean
                        cur_mape = mape(valid.values, pred.values)
                        cur_smape = smape(valid.values, pred.values)
                        if cur_mape < best["mape"]:
                            best.update({"mape": cur_mape, "smape": cur_smape,
                                         "order": order, "sorder": sorder, "res": res})
                    except Exception:
                        continue

        if best["res"] is None:
            print(f"[{country}] No model converged. Skipping.")
            continue

        # Refit on full history with best params
        try:
            full_res = try_fit(ts, best["order"], best["sorder"])
        except Exception:
            full_res = try_fit(ts, best["order"], best["sorder"],
                               enforce_stationarity=False,
                               enforce_invertibility=False)

        # Forecast horizon
        fc = full_res.get_forecast(steps=horizon)
        mean = fc.predicted_mean
        conf = fc.conf_int(alpha=0.20)  # 80% interval (tweak as you prefer)
        last_me = ts.index.max()
        future_idx = month_ends_after(last_me, horizon)

        fc_df = pd.DataFrame({
            "MonthEnd": future_idx,
            "Country": country,
            "Forecast_EUR": mean.values,
            "Lower80_EUR": conf.iloc[:, 0].values,
            "Upper80_EUR": conf.iloc[:, 1].values
        })
        all_fc_rows.append(fc_df)

        # Save a row to the summary with validation metrics + model spec
        summ = {
            "Country": country,
            "BestOrder": str(best["order"]),
            "BestSeasonalOrder": str(best["sorder"]),
            "ValMonths": val_months,
            "MAPE_Valid_%": round(best["mape"], 3),
            "SMAPE_Valid_%": round(best["smape"], 3),
            "LastHistoryMonthEnd": str(last_me.date()),
            "HistoryPoints": len(ts)
        }
        all_summ_rows.append(summ)
        print(f"[{country}] Best {best['order']} x {best['sorder']} | "
              f"MAPE={summ['MAPE_Valid_%']}% | forecasting {horizon} m.")

    if all_fc_rows:
        out_fc = pd.concat(all_fc_rows, ignore_index=True)
        out_fc.to_csv(out_forecast, index=False)
        print(f"✅ Wrote forecasts to {out_forecast} ({len(out_fc)} rows)")

    if all_summ_rows:
        out_sm = pd.DataFrame(all_summ_rows)
        out_sm.to_csv(out_summary, index=False)
        print(f"✅ Wrote model summary to {out_summary} ({len(out_sm)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default="ar_country_monthly.csv")
    ap.add_argument("--h",  dest="horizon", type=int, default=1)
    ap.add_argument("--val", dest="val_months", type=int, default=3)
    ap.add_argument("--outf", dest="out_forecast", default="country_forecast.csv")
    ap.add_argument("--outs", dest="out_summary",  default="country_models_summary.csv")
    args = ap.parse_args()
    main(args.infile, args.horizon, args.val_months, args.out_forecast, args.out_summary)