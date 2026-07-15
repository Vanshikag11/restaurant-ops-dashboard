# Restaurant Performance & Delivery Ops Dashboard

A SQL + pandas analytics project on food-delivery order data (Zomato/Swiggy-style),
built to answer the questions an ops/MIS analyst would actually be asked:
*where are we slow, who's churning, and which restaurants need attention.*

**[View the live dashboard →](https://vanshikag11.github.io/restaurant-ops-dashboard/dashboard.html)**

## Business questions answered

1. **Delivery SLA by city** — which cities are dragging down delivery times, and by how much?
2. **Peak-hour strain** — how much does lunch/dinner demand degrade delivery speed vs off-peak?
3. **Revenue by cuisine** — which cuisines drive the most order value, and does speed hurt ratings?
4. **Customer churn** — what % of the customer base in each city has gone quiet (60+ days inactive)?
5. **Restaurant leaderboard** — top 5 restaurants by revenue in each city (window functions)
6. **Order volume trend** — is demand growing or shrinking month-over-month, per city?
7. **SLA breach risk** — which specific restaurants chronically blow past delivery targets?

## Key findings

- **Mumbai has the slowest average delivery time** (39.4 min) vs Pune, the fastest (28.1 min) — an 11-minute city-level gap worth investigating for rider allocation.
- **Dinner peak (7–10pm) adds ~6 minutes** to delivery time vs off-peak hours — the clearest lever for SLA improvement.
- **Delhi NCR has the highest churn rate (28.0%)**, nearly 6 points above Mumbai (22.5%) — flags a retention gap worth a city-specific campaign.
- **North Indian cuisine drives the most total revenue** (₹27.2L) despite Continental having the highest average order value (₹560) — volume beats basket size here.
- **15 restaurants breach the 55-min SLA on >8% of orders**, with the worst offender at 21.3% — a short, actionable watchlist rather than a vague "delivery is slow" statement.

## Stack

- **Data**: synthetic dataset (30,000 orders, 2,500 customers, 180 restaurants, 6 cities) generated with realistic embedded patterns — city-level traffic effects, cuisine price tiers, peak-hour slowdowns, and customer churn curves
- **SQL**: SQLite — CTEs, window functions (`RANK()`, `LAG()`), multi-table joins ([`analysis.sql`](analysis.sql))
- **Analysis**: Python (pandas, numpy) for data generation and validation ([`generate_data.py`](generate_data.py))
- **Dashboard**: HTML + Chart.js (no framework dependency — opens directly in browser)

## Repo structure

```
├── generate_data.py      # synthetic dataset generator (customers, restaurants, orders)
├── customers.csv
├── restaurants.csv
├── orders.csv             # 30,000 rows, the core analysis table
├── analysis.sql            # 7 business-question queries (CTEs, window functions, joins)
├── query_results.json      # output of every query, for reference
├── dashboard.html           # the dashboard itself
└── README.md
```

## How to run

```bash
# regenerate the dataset (optional - orders.csv is already included)
python3 generate_data.py

# load into SQLite and explore
sqlite3 food_delivery.db < setup.sql   # or load the CSVs directly with pandas.to_sql()

# open the dashboard
open dashboard.html   # or just double-click it
```


