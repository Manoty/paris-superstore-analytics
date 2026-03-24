import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from config import PRIMARY, SECONDARY, ACCENT, TINT, BG, SURFACE, BORDER, TEXT, MUTED, PALETTE
import queries as qry

# ── page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Paris Superstore",
    page_icon="🛍️",
    layout="wide"
)

st.markdown(f"""
<style>
  [data-testid="stAppViewContainer"] {{ background: {BG}; }}
  [data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 0.5px solid {BORDER}; }}
  [data-testid="stSidebar"] * {{ color: {TEXT} !important; }}
  [data-testid="metric-container"] {{
      background: {SURFACE}; border: 0.5px solid {BORDER};
      border-radius: 10px; padding: 1rem;
  }}
  div[data-testid="metric-container"] label {{
      color: {MUTED} !important; font-size: 12px !important;
      text-transform: uppercase; letter-spacing: 0.05em;
  }}
  div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
      color: {TEXT} !important; font-size: 22px !important; font-weight: 500 !important;
  }}
  h1, h2, h3 {{ color: {TEXT} !important; font-weight: 500 !important; }}
  .stTabs [data-baseweb="tab-list"] {{
      background: {SURFACE}; border-radius: 8px;
      border: 0.5px solid {BORDER}; padding: 2px; gap: 2px;
  }}
  .stTabs [data-baseweb="tab"] {{ color: {MUTED}; border-radius: 6px; font-size: 13px; }}
  .stTabs [data-baseweb="tab"][aria-selected="true"] {{
      background: {TINT} !important; color: {PRIMARY} !important; font-weight: 500;
  }}
  .stMarkdown hr {{ border-color: {BORDER}; }}
</style>
""", unsafe_allow_html=True)

# ── load data with error handling ──────────────────────────────────────────
@st.cache_data
def load_all():
    try:
        return (
            qry.sales_summary(),
            qry.returns_analysis(),
            qry.discount_analysis(),
            qry.state_summary(),
            qry.rfm_data(),
        )
    except RuntimeError as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

with st.spinner("Loading data..."):
    sales_df, returns_df, discount_df, state_raw, rfm_df = load_all()

# ── sidebar filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛍️ Paris Superstore")
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

    regions    = st.multiselect("Region",   sorted(sales_df["region"].dropna().unique()),   default=sorted(sales_df["region"].dropna().unique()))
    segments   = st.multiselect("Segment",  sorted(sales_df["segment"].dropna().unique()),  default=sorted(sales_df["segment"].dropna().unique()))
    categories = st.multiselect("Category", sorted(sales_df["category"].dropna().unique()), default=sorted(sales_df["category"].dropna().unique()))

    st.markdown("---")
    st.caption(f"Data: {min_date.strftime('%b %Y')} → {max_date.strftime('%b %Y')}")
    st.caption(f"{len(sales_df):,} rows loaded")

# ── apply filters ──────────────────────────────────────────────────────────
start, end = (
    (pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
    if len(date_range) == 2
    else (sales_df["order_month"].min(), sales_df["order_month"].max())
)

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

discount = discount_df[
    (discount_df["region"].isin(regions)) &
    (discount_df["category"].isin(categories))
].copy()

# ── kpis ───────────────────────────────────────────────────────────────────
def pct_delta(cur, pri):
    if pri == 0: return None
    return round(((cur - pri) / pri) * 100, 1)

mid      = start + (end - start) / 2
cur      = sales[sales["order_month"] >= mid]
pri      = sales[sales["order_month"] < mid]

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

# ── chart helper ───────────────────────────────────────────────────────────
def chart_layout(fig, legend=False):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=SURFACE,
        font=dict(color=TEXT, size=12),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=8, b=0),
        xaxis=dict(showgrid=False, linecolor=BORDER, tickcolor=BORDER),
        yaxis=dict(gridcolor=BORDER, linecolor="rgba(0,0,0,0)"),
    )
    return fig

# ── header + kpi row ───────────────────────────────────────────────────────
st.markdown("## 🛍️ Paris Superstore — Analytics")
st.markdown("---")

k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.metric("Revenue",     f"${cur_rev:,.0f}",    f"{pct_delta(cur_rev, pri_rev):+.1f}%" if pct_delta(cur_rev, pri_rev) else None)
with k2: st.metric("Profit",      f"${cur_profit:,.0f}", f"{pct_delta(cur_profit, pri_profit):+.1f}%" if pct_delta(cur_profit, pri_profit) else None)
with k3: st.metric("Orders",      f"{int(cur_orders):,}", f"{pct_delta(cur_orders, pri_orders):+.1f}%" if pct_delta(cur_orders, pri_orders) else None)
with k4: st.metric("Margin",      f"{cur_margin:.1f}%",  f"{pct_delta(cur_margin, pri_margin):+.1f}%" if pct_delta(cur_margin, pri_margin) else None)
with k5: st.metric("Return rate", f"{return_rate:.1f}%", None)

st.markdown("---")

# ── tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈  Sales & Revenue",
    "↩️  Returns & Profitability",
    "🗺️  Regional Performance",
    "💸  Discount Impact",
    "👥  RFM Segments",
])

# ── tab 1 ──────────────────────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Monthly revenue & profit")
        monthly = sales.groupby("order_month")[["total_revenue","total_profit"]].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly["order_month"], y=monthly["total_revenue"],
            name="Revenue", line=dict(color=PRIMARY, width=2), mode="lines+markers", marker=dict(size=4)))
        fig.add_trace(go.Scatter(x=monthly["order_month"], y=monthly["total_profit"],
            name="Profit", line=dict(color=ACCENT, width=2, dash="dot"), mode="lines+markers", marker=dict(size=4)))
        st.plotly_chart(chart_layout(fig, legend=True), width="stretch")

    with col2:
        st.markdown("#### By segment")
        seg = sales.groupby("segment")["total_revenue"].sum().reset_index().sort_values("total_revenue", ascending=False)
        fig2 = px.bar(seg, x="segment", y="total_revenue", color="segment", color_discrete_sequence=PALETTE)
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(chart_layout(fig2), width="stretch")

    st.markdown("#### Revenue by category over time")
    cat_time = sales.groupby(["order_month","category"])["total_revenue"].sum().reset_index()
    fig3 = px.area(cat_time, x="order_month", y="total_revenue", color="category", color_discrete_sequence=PALETTE)
    fig3.update_traces(line_width=1)
    st.plotly_chart(chart_layout(fig3, legend=True), width="stretch")

# ── tab 2 ──────────────────────────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Return rate by category")
        cat_ret = returns.groupby("category").agg(returned=("returned_lines","sum"), total=("total_lines","sum")).reset_index()
        cat_ret["rate"] = (cat_ret["returned"] / cat_ret["total"] * 100).round(2)
        fig4 = px.bar(cat_ret, x="category", y="rate", color="category", color_discrete_sequence=PALETTE)
        fig4.update_traces(marker_line_width=0)
        st.plotly_chart(chart_layout(fig4), width="stretch")

    with col2:
        st.markdown("#### Return rate by segment")
        seg_ret = returns.groupby("segment").agg(returned=("returned_lines","sum"), total=("total_lines","sum")).reset_index()
        seg_ret["rate"] = (seg_ret["returned"] / seg_ret["total"] * 100).round(2)
        fig5 = px.bar(seg_ret, x="segment", y="rate", color="segment", color_discrete_sequence=PALETTE)
        fig5.update_traces(marker_line_width=0)
        st.plotly_chart(chart_layout(fig5), width="stretch")

    st.markdown("#### Profit lost to returns — bottom 10 sub-categories")
    lost = returns.groupby("sub_category")["profit_lost_to_returns"].sum().reset_index()
    lost = lost.sort_values("profit_lost_to_returns").head(10)
    fig6 = px.bar(lost, x="profit_lost_to_returns", y="sub_category", orientation="h", color_discrete_sequence=[PRIMARY])
    fig6.update_traces(marker_line_width=0)
    st.plotly_chart(chart_layout(fig6), width="stretch")

# ── tab 3 ──────────────────────────────────────────────────────────────────
with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Revenue & profit by region")
        reg = sales.groupby(["region","manager_name"])[["total_revenue","total_profit"]].sum().reset_index()
        fig7 = px.bar(reg, x="region", y=["total_revenue","total_profit"], barmode="group",
                      color_discrete_sequence=[PRIMARY, ACCENT], hover_data={"manager_name": True})
        fig7.update_traces(marker_line_width=0)
        st.plotly_chart(chart_layout(fig7, legend=True), width="stretch")

    with col2:
        st.markdown("#### Profit margin by region & category")
        rm = sales.groupby(["region","category"]).apply(
            lambda x: pd.Series({"margin_pct": round(x["total_profit"].sum() / x["total_revenue"].sum() * 100, 2) if x["total_revenue"].sum() > 0 else 0})
        ).reset_index()
        fig8 = px.bar(rm, x="category", y="margin_pct", color="region", barmode="group", color_discrete_sequence=PALETTE)
        fig8.update_traces(marker_line_width=0)
        st.plotly_chart(chart_layout(fig8, legend=True), width="stretch")

    st.markdown("#### Revenue trend by region")
    reg_time = sales.groupby(["order_month","region"])["total_revenue"].sum().reset_index()
    fig9 = px.line(reg_time, x="order_month", y="total_revenue", color="region",
                   color_discrete_sequence=PALETTE, markers=True)
    fig9.update_traces(marker_size=4, line_width=2)
    st.plotly_chart(chart_layout(fig9, legend=True), width="stretch")

    st.markdown("#### US revenue map")
    map_metric = st.radio("Metric", ["Revenue", "Profit", "Orders", "Margin %"], horizontal=True)
    state_df = state_raw.copy()
    state_df["margin"] = (state_df["profit"] / state_df["revenue"] * 100).round(2)
    metric_map = {
        "Revenue":  ("revenue", "Revenue ($)"),
        "Profit":   ("profit",  "Profit ($)"),
        "Orders":   ("orders",  "Orders"),
        "Margin %": ("margin",  "Margin (%)"),
    }
    col, label = metric_map[map_metric]
    fig12 = px.choropleth(
        state_df, locations="state", locationmode="USA-states", color=col, scope="usa",
        color_continuous_scale=[[0, "#FFF7ED"], [0.5, ACCENT], [1, PRIMARY]],
        labels={col: label}, hover_name="state",
    )
    fig12.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor=BG, landcolor="#F5F5F4", showlakes=True),
        font=dict(color=TEXT),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig12, width="stretch")

    st.markdown("#### Top 10 states by " + map_metric.lower())
    top10 = state_df.nlargest(10, col)[["state", col]].reset_index(drop=True)
    top10.index += 1
    top10.columns = ["State", label]
    st.dataframe(top10, width="stretch")

# ── tab 4 ──────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("#### Discount rate vs profit margin")
    st.caption("Each point is one order line. Reveals exactly where discounting destroys margin.")

    col1, col2 = st.columns([3, 1])
    with col2:
        cat_filter = st.multiselect("Category", options=sorted(discount_df["category"].unique()),
                                    default=sorted(discount_df["category"].unique()), key="disc_cat")
        show_trendline = st.checkbox("Show trendline", value=True)

    disc = discount[discount["category"].isin(cat_filter)].copy()

    with col1:
        fig10 = px.scatter(
            disc, x="discount_pct", y="profit_margin_pct",
            color="category", size="sales", size_max=18,
            hover_data=["product_name", "region", "sub_category", "sales"],
            color_discrete_sequence=PALETTE,
            trendline="ols" if show_trendline else None,
            labels={"discount_pct": "Discount %", "profit_margin_pct": "Profit margin %"},
        )
        fig10.add_hline(y=0, line_dash="dash", line_color=PRIMARY, line_width=1,
                        annotation_text="breakeven", annotation_font_color=PRIMARY)
        fig10.update_traces(marker_line_width=0, selector=dict(mode="markers"))
        st.plotly_chart(chart_layout(fig10, legend=True), width="stretch")

    st.markdown("#### Average profit margin by discount tier")
    tier_order = ["No discount", "1–10%", "11–20%", "21–30%", "30%+"]
    tier = disc.groupby("discount_tier").agg(
        avg_margin=("profit_margin_pct", "mean"),
        order_count=("order_id", "count")
    ).reset_index()
    tier["avg_margin"] = tier["avg_margin"].round(2)
    tier["discount_tier"] = pd.Categorical(tier["discount_tier"], categories=tier_order, ordered=True)
    tier = tier.sort_values("discount_tier")
    fig11 = px.bar(tier, x="discount_tier", y="avg_margin",
                   color="avg_margin",
                   color_continuous_scale=[[0, PRIMARY], [0.5, ACCENT], [1, "#FFF7ED"]],
                   text="avg_margin",
                   labels={"avg_margin": "avg margin %", "discount_tier": "discount tier"})
    fig11.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
    fig11.update_coloraxes(showscale=False)
    st.plotly_chart(chart_layout(fig11), width="stretch")

# ── tab 5 — rfm ────────────────────────────────────────────────────────────
with tab5:
    st.markdown("#### Customer RFM segmentation")
    st.caption("Customers scored on Recency, Frequency, and Monetary value — then grouped into actionable segments.")

    col1, col2 = st.columns([1, 2])

    with col1:
        seg_counts = rfm_df.groupby("rfm_segment").agg(
            customers=("customer_id", "count"),
            avg_spend=("monetary", "mean"),
            avg_orders=("frequency", "mean"),
        ).reset_index()
        seg_counts["avg_spend"]  = seg_counts["avg_spend"].round(0)
        seg_counts["avg_orders"] = seg_counts["avg_orders"].round(1)
        seg_counts = seg_counts.sort_values("customers", ascending=False)

        fig13 = px.bar(seg_counts, x="customers", y="rfm_segment", orientation="h",
                       color="customers",
                       color_continuous_scale=[[0, TINT], [0.5, ACCENT], [1, PRIMARY]],
                       text="customers",
                       labels={"customers": "customers", "rfm_segment": ""})
        fig13.update_traces(textposition="outside", marker_line_width=0)
        fig13.update_coloraxes(showscale=False)
        st.plotly_chart(chart_layout(fig13), width="stretch")

    with col2:
        st.markdown("#### Segment breakdown")
        st.dataframe(
            seg_counts.rename(columns={
                "rfm_segment": "Segment",
                "customers":   "Customers",
                "avg_spend":   "Avg spend ($)",
                "avg_orders":  "Avg orders",
            }),
            width="stretch",
            hide_index=True
        )

    st.markdown("#### RFM scatter — frequency vs monetary, sized by recency")
    fig14 = px.scatter(
        rfm_df, x="frequency", y="monetary",
        color="rfm_segment", size="r_score", size_max=20,
        hover_data=["customer_name", "region", "recency_days"],
        color_discrete_sequence=PALETTE,
        labels={"frequency": "Order frequency", "monetary": "Total spend ($)", "rfm_segment": "Segment"},
    )
    fig14.update_traces(marker_line_width=0)
    st.plotly_chart(chart_layout(fig14, legend=True), width="stretch")

    st.markdown("#### Average spend by segment & region")
    rfm_reg = rfm_df.groupby(["rfm_segment","region"])["monetary"].mean().round(2).reset_index()
    fig15 = px.bar(rfm_reg, x="rfm_segment", y="monetary", color="region",
                   barmode="group", color_discrete_sequence=PALETTE,
                   labels={"monetary": "avg spend ($)", "rfm_segment": "segment"})
    fig15.update_traces(marker_line_width=0)
    st.plotly_chart(chart_layout(fig15, legend=True), width="stretch")