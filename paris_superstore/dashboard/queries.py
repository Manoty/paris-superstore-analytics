import duckdb
from config import DB_PATH
import pandas as pd

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

con = get_connection()

def q(sql):
    try:
        return con.execute(sql).df()
    except Exception as e:
        raise RuntimeError(f"Query failed: {e}\nSQL: {sql}")

def sales_summary():
    df = q("select * from main_marts.mart_sales_summary")
    df["order_month"] = pd.to_datetime(df["order_month"])
    return df

def returns_analysis():
    return q("select * from main_marts.mart_returns_analysis")

def discount_analysis():
    return q("select * from main_marts.mart_discount_analysis")

def state_summary():
    return q("""
        select
            state,
            region,
            sum(sales)               as revenue,
            sum(profit)              as profit,
            count(distinct order_id) as orders
        from main_marts.fct_orders
        group by 1, 2
    """)

def rfm_data():
    return q("select * from main_marts.mart_rfm")