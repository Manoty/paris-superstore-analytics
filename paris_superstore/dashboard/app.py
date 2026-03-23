import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "dev.duckdb")

@st.cache_resource
def get_con():
    return duckdb.connect(DB_PATH, read_only=True)

con = get_con()

st.title("Superstore Analytics")

tab1, tab2, tab3 = st.tabs(["Sales & Revenue", "Returns & Profitability", "Regional Performance"])

with tab1:
    st.subheader("Monthly revenue & profit")
    df = con.execute("""
        select
            order_month,
            sum(total_revenue) as revenue,
            sum(total_profit)  as profit
        from main_marts.mart_sales_summary
        group by 1
        order by 1
    """).df()
    df["order_month"] = pd.to_datetime(df["order_month"])
    fig = px.line(df, x="order_month", y=["revenue", "profit"], markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Revenue by segment")
    df2 = con.execute("""
        select segment, sum(total_revenue) as revenue
        from main_marts.mart_sales_summary
        group by 1
        order by 2 desc
    """).df()
    st.plotly_chart(px.bar(df2, x="segment", y="revenue"), use_container_width=True)

with tab2:
    st.subheader("Return rate by category")
    df3 = con.execute("""
        select category, sum(returned_lines) as returns, sum(total_lines) as total,
               round(sum(returned_lines)/sum(total_lines)*100, 2) as return_rate_pct
        from main_marts.mart_returns_analysis
        group by 1
        order by 3 desc
    """).df()
    st.plotly_chart(px.bar(df3, x="category", y="return_rate_pct", color="category"), use_container_width=True)

    st.subheader("Profit lost to returns by sub-category")
    df4 = con.execute("""
        select sub_category, sum(profit_lost_to_returns) as profit_lost
        from main_marts.mart_returns_analysis
        group by 1
        order by 2
        limit 10
    """).df()
    st.plotly_chart(px.bar(df4, x="profit_lost", y="sub_category", orientation="h"), use_container_width=True)

with tab3:
    st.subheader("Revenue & profit by region")
    df5 = con.execute("""
        select region, manager_name,
               sum(total_revenue) as revenue,
               sum(total_profit)  as profit
        from main_marts.mart_sales_summary
        group by 1, 2
        order by 3 desc
    """).df()
    st.plotly_chart(px.bar(df5, x="region", y=["revenue", "profit"],
                           barmode="group", color_discrete_sequence=px.colors.qualitative.Safe),
                    use_container_width=True)

    st.subheader("Profit margin by region & category")
    df6 = con.execute("""
        select region, category,
               round(sum(total_profit)/nullif(sum(total_revenue),0)*100, 2) as margin_pct
        from main_marts.mart_sales_summary
        group by 1, 2
        order by 3 desc
    """).df()
    st.plotly_chart(px.bar(df6, x="category", y="margin_pct", color="region", barmode="group"),
                    use_container_width=True)