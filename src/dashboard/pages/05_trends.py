import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.dashboard.utils import db

st.set_page_config(page_title="Trend Analysis - Nifty 100 Analytics", layout="wide")
st.title("Trend Analysis")

companies_df = db.get_companies()
if companies_df.empty:
    st.warning("No companies found in database.")
    st.stop()

# Company search box
company_options = companies_df["nse"] + " - " + companies_df["company_name"]
selected_company = st.selectbox("Select Company", company_options.tolist())
ticker = selected_company.split(" - ")[0]

# Multi-metric selector (up to 3)
available_metrics = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_margin_pct",
    "debt_to_equity",
    "free_cash_flow",
    "price_to_earnings",
]
selected_metrics = st.multiselect(
    "Select up to 3 metrics for trend analysis",
    available_metrics,
    default=["return_on_equity_pct"],
    max_selections=3,
)

if not selected_metrics:
    st.info("Please select at least one metric.")
    st.stop()

# Fetch ratios
ratios_df = db.get_ratios(ticker=ticker)
if ratios_df.empty:
    st.warning(f"No financial ratio data available for {ticker}.")
    st.stop()

# Sort by year for the trend
ratios_df = ratios_df.sort_values(by="year").tail(10)

if len(ratios_df) < 10:
    st.caption(f"*Note: Showing {len(ratios_df)} years of available data.*")

fig = go.Figure()

for metric in selected_metrics:
    if metric in ratios_df.columns:
        # Calculate YoY % change
        yoy_change = ratios_df[metric].pct_change() * 100

        # Create text for annotations (only show if not NaN and absolute value > 1%)
        text_annotations = []
        for val in yoy_change:
            if pd.isna(val):
                text_annotations.append("")
            else:
                prefix = "+" if val > 0 else ""
                text_annotations.append(f"{prefix}{val:.1f}%")

        fig.add_trace(
            go.Scatter(
                x=ratios_df["year"],
                y=ratios_df[metric],
                mode="lines+markers+text",
                name=metric,
                text=text_annotations,
                textposition="top center",
            )
        )

fig.update_layout(
    title=f"10-Year Trend Analysis for {ticker}",
    xaxis_title="Year",
    yaxis_title="Metric Value",
    hovermode="x unified",
    margin=dict(t=50, b=50, l=50, r=50),
)

st.plotly_chart(fig, use_container_width=True)
