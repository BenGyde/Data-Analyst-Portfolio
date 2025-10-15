# Overdue forecast (Month end)

## Problem statement

Finance teams need visibility into future overdue amounts to manage cash flow and credit risk. Raw invoice-level data is difficult to analyze directly, and manual forecasting is time-consuming and inconsistent.

## Solution & Features

- **Data Transformation**: Converts invoice-level data into a clean monthly panel with overdue and open balance metrics per country.
- **Automated Forecasting**: Applies SARIMAX time-series models to predict overdue amounts for each country.
- **Model Selection**: Chooses the best model configuration using validation metrics (MAPE and SMAPE).
- **Actionable Outputs**: Generates forecast CSV files with confidence intervals and a summary of model performance.
- **Retro vibes**: Based on the iconic windows 95 look to boost productivity

## Example Screenshot

<img width="1274" height="715" alt="Dashboard" src="https://github.com/user-attachments/assets/29cfc579-c878-4309-aaa8-446e38e0c23e" />

## File reference

| Name                          | File   | Description                                |
| :---------------------------- | :----- | :------------------------------------------ |
| `Dashboard.pbix`    | PBIX   | The finished Power BI dashboard             |
| `build_monthly.py`| PY    | Aggregates invoice-level data into monthly metrics    |
| `forecast_sarimax.py` | PY | Forecasts overdue amounts using SARIMAX models |
| `ar_invoices_sample.csv` | CSV | Sample anonymized invoice data for demonstration |
