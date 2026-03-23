import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ── theme ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Superstore Analytics",
    page_icon="🛍️",
    layout="wide"
)

ORANGE  = "#E8590C"
AMBER   = "#F59E0B"
PEACH   = "#FDBA74"
DARK    = "#1C1917"
SURFACE = "#292524"
MUTED   = "#78716C"

PALETTE = [ORANGE, AMBER, PEACH, "#C2410C", "#FED7AA", "#9A3412"]

st.markdown(f"""
<style>
  [data-testid="stAppViewContainer"] {{ background: {DARK}; color: #F5F5F4; }}
  [data-testid="stSidebar"] {{ background: {SURFACE}; }}
  [data-testid="metric-container"] {{
      background: {SURFACE};
      border: 1px solid #44403C;
      border-radius: 12px;
      padding: 1rem;
  }}
  h1, h2, h3 {{ color: {ORANGE} !important; }}
  .stTabs [data-baseweb="tab-list"] {{ background: {SURFACE}; border-radius: 8px; }}
  .stTabs [data-baseweb="tab"] {{ color: #A8A29E; }}
  .stTabs [data-baseweb="tab"][aria-selected="true"] {{ color: {ORANGE}; border-bottom: 2px solid {ORANGE}; }}
</style>
""", unsafe_allow_html=True)

# ── connection ─────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "dev.duckdb")

@st.cache_resource
def get_con():
    return duckdb.connect(DB_PATH, read_only=True)

con = get_con()

def q(sql):
    return con.execute(sql).df()

# ── kpi helpers ────────────────────────────────────────────────────────────
def kpi(label, value, delta=None, prefix="$", suffix=""):
    formatted = f"{prefix}{value:,.0f}{suffix}" if isinstance(value, float) else f"{prefix}{value:,}{suffix}"
    st.metric(label=label, value=formatted, delta=f"{delta:+.1f}%" if delta is not None else None)

# ── data ───────────────────────────────────────────────────────────────────
sales_df = q("select * from main_marts.mart_sales_summary")
returns_df = q("select * from main_marts.mart_returns_analysis")
sales_df["order_month"] = pd.to_datetime(sales_df["order_month"])

# current vs prior year totals for deltas
cur = sales_df[sales_df["order_month"].dt.year == sales_df["order_month"].dt.year.max()]
pri = sales_df[sales_df["order_month"].dt.year == sales_df["order_month"].dt.year.max() - 1]

def pct_delta(cur_val, pri_val):
    if pri_val == 0:
        return None
    return ((cur_val - pri_val) / pri_val) * 100

cur_rev    = cur["total_revenue"].sum()
pri_rev    = pri["total_revenue"].sum()
cur_profit = cur["total_profit"].sum()
pri_profit = pri["total_profit"].sum()
cur_orders = cur["total_orders"].sum()
pri_orders = pri["total_orders"].sum()
cur_margin = cur_profit / cur_rev * 100 if cur_rev else 0
pri_margin = pri_profit / pri_rev * 100 if pri_rev else 0
return_rate = returns_df["returned_lines"].sum() / returns_df["total_lines"].sum() * 100

# ── layout ─────────────────────────────────────────────────────────────────
st.title("🛍️ Superstore Analytics")

# KPI cards
k1, k2, k3, k4, k5 = st.columns(5)
with k1: kpi("Total revenue",    cur_rev,    pct_delta(cur_rev, pri_rev))
with k2: kpi("Total profit",     cur_profit, pct_delta(cur_profit, pri_profit))
with k3: kpi("Total orders",     cur_orders, pct_delta(cur_orders, pri_orders), prefix="")
with k4: kpi("Profit margin",    cur_margin, pct_delta(cur_margin, pri_margin), prefix="", suffix="%")
with k5: kpi("Return rate",      return_rate, None, prefix="", suffix="%")

st.divider()

tab1, tab2, tab3 = st.tabs(["📈  Sales & Revenue", "↩️  Returns & Profitability", "🗺️  Regional Performance"])

with tab1:
    st.subheader("Monthly revenue & profit")
    monthly = sales_df.groupby("order_month")[["total_revenue","total_profit"]].sum().reset_index()
    fig = px.line(monthly, x="order_month", y=["total_revenue","total_profit"],
                  markers=True, color_discrete_sequence=[ORANGE, AMBER])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#F5F5F4", legend_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Revenue by segment")
    seg = sales_df.groupby("segment")["total_revenue"].sum().reset_index().sort_values("total_revenue", ascending=False)
    fig2 = px.bar(seg, x="segment", y="total_revenue", color="segment", color_discrete_sequence=PALETTE)
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#F5F5F4", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Return rate by category")
    cat = returns_df.groupby("category").agg(
        returned_lines=("returned_lines","sum"),
        total_lines=("total_lines","sum")
    ).reset_index()
    cat["return_rate_pct"] = (cat["returned_lines"] / cat["total_lines"] * 100).round(2)
    fig3 = px.bar(cat, x="category", y="return_rate_pct", color="category", color_discrete_sequence=PALETTE)
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#F5F5F4", showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Profit lost to returns — bottom 10 sub-categories")
    lost = returns_df.groupby("sub_category")["profit_lost_to_returns"].sum().reset_index()
    lost = lost.sort_values("profit_lost_to_returns").head(10)
    fig4 = px.bar(lost, x="profit_lost_to_returns", y="sub_category", orientation="h",
                  color_discrete_sequence=[ORANGE])
    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#F5F5F4")
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    st.subheader("Revenue & profit by region")
    reg = sales_df.groupby(["region","manager_name"])[["total_revenue","total_profit"]].sum().reset_index()
    fig5 = px.bar(reg, x="region", y=["total_revenue","total_profit"], barmode="group",
                  color_discrete_sequence=[ORANGE, AMBER],
                  hover_data={"manager_name": True})
    fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#F5F5F4", legend_title="")
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("Profit margin by region & category")
    rm = sales_df.groupby(["region","category"]).apply(
        lambda x: pd.Series({
            "margin_pct": (x["total_profit"].sum() / x["total_revenue"].sum() * 100).round(2)
        })
    ).reset_index()
    fig6 = px.bar(rm, x="category", y="margin_pct", color="region", barmode="group",
                  color_discrete_sequence=PALETTE)
    fig6.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#F5F5F4", legend_title="Region")
    st.plotly_chart(fig6, use_container_width=True)