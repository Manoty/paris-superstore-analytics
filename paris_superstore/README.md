# Paris Superstore Analytics

A end-to-end data engineering and analytics project built on the Tableau Sample Superstore dataset.
Raw CSV data is modelled with dbt, stored in DuckDB, and served through a Streamlit dashboard.

## Stack

| Layer | Tool |
|---|---|
| Transformation | dbt-core + dbt-duckdb |
| Storage | DuckDB |
| Dashboard | Streamlit + Plotly |
| Language | Python 3.11+ / SQL |

## Architecture
```
Raw CSVs (data/raw/)
    └── load_raw.py → DuckDB (dev.duckdb)
            └── dbt run
                    ├── staging/        (views)  — cast types, rename cols
                    ├── intermediate/   (tables) — joins, business logic
                    └── marts/          (tables) — dims, facts, aggregates
                            └── Streamlit dashboard
```

## Models

| Model | Layer | Description |
|---|---|---|
| `stg_orders` | Staging | Cast dates, snake_case columns, fix postal codes |
| `stg_returns` | Staging | Parse returned flag to boolean |
| `stg_people` | Staging | Region to manager lookup |
| `int_orders_enriched` | Intermediate | Join all three staging models, derive days_to_ship and profit_margin |
| `dim_customers` | Marts | Distinct customers with segment |
| `dim_products` | Marts | Distinct products with category, deduped by frequency |
| `dim_geography` | Marts | Distinct city/state/region combinations |
| `fct_orders` | Marts | Incremental fact table on order_date |
| `mart_sales_summary` | Marts | Revenue and profit aggregated by month, region, segment, category |
| `mart_returns_analysis` | Marts | Return rate and profit impact by category and sub-category |
| `mart_discount_analysis` | Marts | Order-level discount vs margin for scatter analysis |
| `mart_rfm` | Marts | Customer RFM scoring and segmentation using ntile(5) |

## Key Insights

1. **Discounts above 20% are almost always unprofitable.** The discount scatter plot shows a clear negative correlation between discount rate and profit margin — orders in the 30%+ tier average negative margins across all categories.

2. **Tables sub-category is the single biggest drag on profitability.** Despite reasonable sales volume, Tables consistently posts negative profit margins and accounts for a disproportionate share of profit lost to returns.

3. **The West region leads on revenue but the East leads on margin.** West generates the highest total sales but East converts a higher share of revenue into profit — suggesting pricing or cost structure differences worth investigating.

## Setup
```bash
# 1. install dependencies
pip install -r requirements.txt

# 2. split the source Excel into CSVs
python split_raw.py

# 3. load CSVs into DuckDB
python load_raw.py

# 4. run dbt models
dbt run
dbt test

# 5. launch dashboard
cd dashboard
streamlit run app.py
```

## Project Structure
```
paris_superstore/
├── data/raw/               # source CSVs (not committed)
├── models/
│   ├── staging/            # stg_ models + sources.yml
│   ├── intermediate/       # int_ models
│   └── marts/              # dim_, fct_, mart_ models + schema.yml
├── dashboard/
│   ├── app.py              # Streamlit app
│   ├── config.py           # theme + DB path
│   └── queries.py          # all SQL queries
├── load_raw.py             # CSV → DuckDB loader
├── dbt_project.yml
├── requirements.txt
└── README.md
```

## Tests
```bash
dbt test
```

Covers unique and not_null constraints on all primary keys across dims and facts.