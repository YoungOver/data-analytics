# data-analytics

Financial modelling and sales analytics in Python. The outputs are what a founder or a bank actually asks for: a working Excel model and a readable report.

## financial-model

24-month model of a coffee shop generated with openpyxl. All numbers are live Excel formulas, so the client can change assumptions and see the result immediately.

- assumptions sheet: average check, traffic, seasonality, COGS, rent, payroll, capex
- monthly P&L and cash flow, break-even month and payback period
- native Excel charts plus a PNG summary for the pitch deck

![](docs/finmodel.jpg)

## sales-analytics

Sales report built with pandas and matplotlib: revenue by channel and cohort, ABC analysis of products, retention and a list of recommended actions.

![](docs/analytics.jpg)

## Dashboard

Interactive sales dashboard used as a front end for these numbers.

![](docs/dashboard_1440_0.jpg)

```bash
pip install -r requirements.txt
python financial-model/build.py
python sales-analytics/report.py
```
