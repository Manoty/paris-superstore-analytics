import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ── page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Paris Superstore",
    page_icon="🛍️",
    layout="wide"
)

# ── theme ──────────────────────────────────────────────────────────────────
PRIMARY   = "#C2410C"
SECONDARY = "#EA580C"
ACCENT    = "#FDBA74"
TINT      = "#FFF7ED"
BG        = "#FAFAF9"
SURFACE   = "#FFFFFF"
BORDER    = "#E7E5E4"
TEXT      = "#1C1917"
MUTED     = "#A8A29E"

PALETTE   = [PRIMARY, SECONDARY, "#F97316", ACCENT, "#9A3412", "#7C2D12"]

st.markdown(f"""
<style>
  [data-testid="stAppViewContainer"] {{
      background: {BG};
  }}
  [data-testid="stSidebar"] {{
      background: {SURFACE};
      border-right: 0.5px solid {BORDER};
  }}
  [data-testid="stSidebar"] * {{
      color: {TEXT} !important;
  }}
  [data-testid="metric-container"] {{
      background: {SURFACE};
      border: 0.5px solid {BORDER};
      border-radius: 10px;
      padding: 1rem;
  }}
  div[data-testid="metric-container"] label {{
      color: {MUTED} !important;
      font-size: 12px !important;
      text-transform: uppercase;
      letter-spacing: 0.05em;
  }}
  div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
      color: {TEXT} !important;
      font-size: 22px !important;
      font-weight: 500 !important;
  }}
  h1 {{ color: {TEXT} !important; font-weight: 500 !important; letter-spacing: -0.02em; }}
  h2, h3 {{ color: {TEXT} !important; font-weight: 500 !important; }}
  .stTabs [data-baseweb="tab-list"] {{
      background: {SURFACE};
      border-radius: 8px;
      border: 0.5px solid {BORDER};
      padding: 2px;
      gap: 2px;
  }}
  .stTabs [data-baseweb="tab"] {{
      color: {MUTED};
      border-radius: 6px;
      font-size: 13px;
  }}
  .stTabs [data-baseweb="tab"][aria-selected="true"] {{
      background: {TINT} !important;
      color: {PRIMARY} !important;
      font-weight: 500;
  }}
  .stMarkdown hr {{ border-color: {BORDER}; }}
  [data-testid="stMetricDelta"] svg {{ display: none; }}
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

# ── load base data ─────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    sales    = q("select * from main_marts.mart_sales_summary")
    returns  = q("select * from main_marts.mart_returns_analysis")
    sales["order_month"] = pd.to_datetime(sales["order_month"])
    return sales, returns

sales_df, returns_df = load_data()

@st.cache_data
def load_discount():
    return q("select * from main_marts.mart_discount_analysis")

discount_df = load_discount()

# ── sidebar filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 🛍️ Paris Superstore")
    st.markdown("---")
    st.markdown("**Filters**")

    min_date = sales_df["order_month"].min().date()
    max_date = sales_df["order_month"].max().date()

    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    all_regions   = sorted(sales_df["region"].dropna().unique())
    all_segments  = sorted(sales_df["segment"].dropna().unique())
    all_categories = sorted(sales_df["category"].dropna().unique())

    regions    = st.multiselect("Region",   all_regions,    default=all_regions)
    segments   = st.multiselect("Segment",  all_segments,   default=all_segments)
    categories = st.multiselect("Category", all_categories, default=all_categories)

    st.markdown("---")
    st.caption(f"Data from {min_date.strftime('%b %Y')} to {max_date.strftime('%b %Y')}")

# ── apply filters ──────────────────────────────────────────────────────────
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start, end = sales_df["order_month"].min(), sales_df["order_month"].max()

sales = sales_df[
    (sales_df["order_month"] >= start) &
    (sales_df["order_month"] <= end) &
    (sales_df["region"].isin(regions)) &
    (sales_df["segment"].isin(segments)) &
    (sales_df["category"].isin(categories))
].copy()

returns = returns_df[
    (returns_df["region"].isin(regions)) &
    (returns_df["segment"].isin(segments)) &
    (returns_df["category"].isin(categories))
].copy()

# ── kpi helpers ────────────────────────────────────────────────────────────
def pct_delta(cur, pri):
    if pri == 0: return None
    return round(((cur - pri) / pri) * 100, 1)

def prior_period(df):
    mid = start + (end - start) / 2
    return df[df["order_month"] < mid]

def current_period(df):
    mid = start + (end - start) / 2
    return df[df["order_month"] >= mid]

cur = current_period(sales)
pri = prior_period(sales)

cur_rev    = cur["total_revenue"].sum()
pri_rev    = pri["total_revenue"].sum()
cur_profit = cur["total_profit"].sum()
pri_profit = pri["total_profit"].sum()
cur_orders = cur["total_orders"].sum()
pri_orders = pri["total_orders"].sum()
cur_margin = (cur_profit / cur_rev * 100) if cur_rev else 0
pri_margin = (pri_profit / pri_rev * 100) if pri_rev else 0
ret_lines  = returns["returned_lines"].sum()
tot_lines  = returns["total_lines"].sum()
return_rate = (ret_lines / tot_lines * 100) if tot_lines else 0

# ── plotly layout defaults ─────────────────────────────────────────────────
def chart_layout(fig, legend=False):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=SURFACE,
        font=dict(color=TEXT, family="Inter, sans-serif", size=12),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=8, b=0),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickcolor=BORDER),
        yaxis=dict(gridcolor=BORDER, linecolor="rgba(0,0,0,0)"),
    )
    return fig

# ── header ─────────────────────────────────────────────────────────────────
st.markdown("## 🛍️ Paris Superstore — Analytics")
st.markdown("---")

# ── kpi cards ──────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.metric("Revenue",     f"${cur_rev:,.0f}",    f"{pct_delta(cur_rev, pri_rev):+.1f}%" if pct_delta(cur_rev, pri_rev) else None)
with k2: st.metric("Profit",      f"${cur_profit:,.0f}", f"{pct_delta(cur_profit, pri_profit):+.1f}%" if pct_delta(cur_profit, pri_profit) else None)
with k3: st.metric("Orders",      f"{cur_orders:,.0f}",  f"{pct_delta(cur_orders, pri_orders):+.1f}%" if pct_delta(cur_orders, pri_orders) else None)
with k4: st.metric("Margin",      f"{cur_margin:.1f}%",  f"{pct_delta(cur_margin, pri_margin):+.1f}%" if pct_delta(cur_margin, pri_margin) else None)
with k5: st.metric("Return rate", f"{return_rate:.1f}%", None)

st.markdown("---")

# ── tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈  Sales & Revenue",
    "↩️  Returns & Profitability",
    "🗺️  Regional Performance",
    "💸  Discount Impact",
    "🗺️  US Map",
])
# ── tab 1 ──────────────────────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Monthly revenue & profit")
        monthly = sales.groupby("order_month")[["total_revenue","total_profit"]].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["order_month"], y=monthly["total_revenue"],
            name="Revenue", line=dict(color=PRIMARY, width=2), mode="lines+markers",
            marker=dict(size=4)
        ))
        fig.add_trace(go.Scatter(
            x=monthly["order_month"], y=monthly["total_profit"],
            name="Profit", line=dict(color=ACCENT, width=2, dash="dot"), mode="lines+markers",
            marker=dict(size=4)
        ))
        st.plotly_chart(chart_layout(fig, legend=True), use_container_width=True)

    with col2:
        st.markdown("#### By segment")
        seg = sales.groupby("segment")["total_revenue"].sum().reset_index().sort_values("total_revenue", ascending=False)
        fig2 = px.bar(seg, x="segment", y="total_revenue", color="segment",
                      color_discrete_sequence=PALETTE)
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(chart_layout(fig2), use_container_width=True)

    st.markdown("#### Revenue by category over time")
    cat_time = sales.groupby(["order_month","category"])["total_revenue"].sum().reset_index()
    fig3 = px.area(cat_time, x="order_month", y="total_revenue", color="category",
                   color_discrete_sequence=PALETTE)
    fig3.update_traces(line_width=1)
    st.plotly_chart(chart_layout(fig3, legend=True), use_container_width=True)

# ── tab 2 ──────────────────────────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Return rate by category")
        cat_ret = returns.groupby("category").agg(
            returned=("returned_lines","sum"),
            total=("total_lines","sum")
        ).reset_index()
        cat_ret["rate"] = (cat_ret["returned"] / cat_ret["total"] * 100).round(2)
        fig4 = px.bar(cat_ret, x="category", y="rate", color="category",
                      color_discrete_sequence=PALETTE)
        fig4.update_traces(marker_line_width=0)
        fig4.update_yaxes(title="return rate %")
        st.plotly_chart(chart_layout(fig4), use_container_width=True)

    with col2:
        st.markdown("#### Return rate by segment")
        seg_ret = returns.groupby("segment").agg(
            returned=("returned_lines","sum"),
            total=("total_lines","sum")
        ).reset_index()
        seg_ret["rate"] = (seg_ret["returned"] / seg_ret["total"] * 100).round(2)
        fig5 = px.bar(seg_ret, x="segment", y="rate", color="segment",
                      color_discrete_sequence=PALETTE)
        fig5.update_traces(marker_line_width=0)
        fig5.update_yaxes(title="return rate %")
        st.plotly_chart(chart_layout(fig5), use_container_width=True)

    st.markdown("#### Profit lost to returns — bottom 10 sub-categories")
    lost = returns.groupby("sub_category")["profit_lost_to_returns"].sum().reset_index()
    lost = lost.sort_values("profit_lost_to_returns").head(10)
    fig6 = px.bar(lost, x="profit_lost_to_returns", y="sub_category",
                  orientation="h", color_discrete_sequence=[PRIMARY])
    fig6.update_traces(marker_line_width=0)
    fig6.update_xaxes(title="profit lost ($)")
    st.plotly_chart(chart_layout(fig6), use_container_width=True)

# ── tab 3 ──────────────────────────────────────────────────────────────────
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Revenue by region")
        reg = sales.groupby(["region","manager_name"])[["total_revenue","total_profit"]].sum().reset_index()
        fig7 = px.bar(reg, x="region", y=["total_revenue","total_profit"],
                      barmode="group", color_discrete_sequence=[PRIMARY, ACCENT],
                      hover_data={"manager_name": True})
        fig7.update_traces(marker_line_width=0)
        st.plotly_chart(chart_layout(fig7, legend=True), use_container_width=True)

    with col2:
        st.markdown("#### Profit margin by region & category")
        rm = sales.groupby(["region","category"]).apply(
            lambda x: pd.Series({
                "margin_pct": round(x["total_profit"].sum() / x["total_revenue"].sum() * 100, 2)
                if x["total_revenue"].sum() > 0 else 0
            })
        ).reset_index()
        fig8 = px.bar(rm, x="category", y="margin_pct", color="region",
                      barmode="group", color_discrete_sequence=PALETTE)
        fig8.update_traces(marker_line_width=0)
        fig8.update_yaxes(title="margin %")
        st.plotly_chart(chart_layout(fig8, legend=True), use_container_width=True)

    st.markdown("#### Revenue trend by region")
    reg_time = sales.groupby(["order_month","region"])["total_revenue"].sum().reset_index()
    fig9 = px.line(reg_time, x="order_month", y="total_revenue", color="region",
                   color_discrete_sequence=PALETTE, markers=True)
    fig9.update_traces(marker_size=4, line_width=2)
    st.plotly_chart(chart_layout(fig9, legend=True), use_container_width=True)