import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils import db

st.set_page_config(page_title="Home - Nifty 100 Analytics", layout="wide")
st.title("Home - Dashboard Overview")

# Fetch all relevant data
companies_df = db.get_companies()
ratios_df = db.get_ratios()

# Check if we have data
if companies_df.empty or ratios_df.empty:
    st.warning("Database is empty or data not found.")
    st.stop()

# Get available years
years = sorted(ratios_df["year"].dropna().unique().tolist(), reverse=True)
if not years:
    st.warning("No year data available in ratios.")
    st.stop()

# Sidebar Year Selector
st.sidebar.header("Filters")
selected_year = st.sidebar.selectbox("Select Year", years, index=0)

# Filter data by year
year_ratios = ratios_df[ratios_df["year"] == selected_year]
# Merge with companies for sector info
merged_df = pd.merge(companies_df, year_ratios, on="company_id", how="inner")

# Calculate KPIs
avg_roe = (
    merged_df["return_on_equity_pct"].mean()
    if "return_on_equity_pct" in merged_df
    else 0
)
median_pe = (
    merged_df["price_to_earnings"].median() if "price_to_earnings" in merged_df else 0
)
median_de = merged_df["debt_to_equity"].median() if "debt_to_equity" in merged_df else 0
total_companies = len(merged_df)
median_rev_cagr = (
    merged_df["sales_cagr_5y"].median() if "sales_cagr_5y" in merged_df else 0
)
debt_free_count = (
    len(merged_df[merged_df["debt_to_equity"] == 0])
    if "debt_to_equity" in merged_df
    else 0
)

# Display KPIs
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric("Average ROE", f"{avg_roe:.2f}%" if pd.notnull(avg_roe) else "N/A")
with col2:
    st.metric("Median P/E", f"{median_pe:.2f}" if pd.notnull(median_pe) else "N/A")
with col3:
    st.metric("Median D/E", f"{median_de:.2f}" if pd.notnull(median_de) else "N/A")
with col4:
    st.metric("Total Companies", total_companies)
with col5:
    st.metric(
        "Median Rev CAGR 5yr",
        f"{median_rev_cagr:.2f}%" if pd.notnull(median_rev_cagr) else "N/A",
    )
with col6:
    st.metric("Debt-Free Companies", debt_free_count)

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Sector Breakdown")
    sector_counts = companies_df["sector"].value_counts().reset_index()
    sector_counts.columns = ["sector", "count"]
    fig_sector = px.pie(sector_counts, names="sector", values="count", hole=0.4)
    fig_sector.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_sector, use_container_width=True)

with col_right:
    st.subheader("Top 5 Companies by Quality Score")
    # Proxy quality score: ROE + ROCE (higher is better)
    if (
        "return_on_equity_pct" in merged_df.columns
        and "return_on_capital_employed_pct" in merged_df.columns
    ):
        merged_df["composite_score"] = merged_df["return_on_equity_pct"].fillna(
            0
        ) + merged_df["return_on_capital_employed_pct"].fillna(0)
    else:
        merged_df["composite_score"] = 0

    top_5 = merged_df.sort_values(by="composite_score", ascending=False).head(5)

    display_cols = [
        "company_name",
        "nse_x",
        "sector",
        "return_on_equity_pct",
        "composite_score",
    ]
    # Filter columns that actually exist
    display_cols = [c for c in display_cols if c in top_5.columns]

    st.dataframe(top_5[display_cols].reset_index(drop=True), use_container_width=True)
