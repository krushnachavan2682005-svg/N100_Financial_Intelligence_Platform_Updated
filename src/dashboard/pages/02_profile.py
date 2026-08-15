import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.dashboard.utils import db

st.set_page_config(page_title="Company Profile - Nifty 100 Analytics", layout="wide")
st.title("Company Profile")

# Load companies for the dropdown
companies_df = db.get_companies()
if companies_df.empty:
    st.warning("Database is empty or data not found.")
    st.stop()

# Create a combined ticker-name for search
company_options = companies_df["nse"] + " - " + companies_df["company_name"]

# Search Box
st.sidebar.header("Search")
selected_option = st.sidebar.selectbox(
    "Search Company", company_options.tolist(), index=0
)
ticker = selected_option.split(" - ")[0] if selected_option else None

if not ticker:
    st.info("Please select a company.")
    st.stop()

# Load company specific data
company_info = db.get_company(ticker)
if company_info.empty:
    st.error("Ticker not found")
    st.stop()

company_info = company_info.iloc[0]

# Company Header Card
st.subheader(f"{company_info['company_name']} ({company_info['nse']})")
st.markdown(
    f"**Sector:** {company_info['sector']} | **Market Cap:** ₹{company_info.get('market_cap_cr', 'N/A')} Cr"
)
st.write(company_info.get("description", "No description available for this company."))

st.divider()

# Load financial data
ratios_df = db.get_ratios(ticker=ticker)
pl_df = db.get_pl(ticker=ticker)

if ratios_df.empty and pl_df.empty:
    st.warning("No financial data available for this company.")
    st.stop()

# Get latest year data for KPIs
latest_year_ratios = (
    ratios_df.sort_values(by="year", ascending=False).iloc[0]
    if not ratios_df.empty
    else pd.Series()
)
latest_year_pl = (
    pl_df.sort_values(by="year", ascending=False).iloc[0]
    if not pl_df.empty
    else pd.Series()
)

# 6 KPIs: ROE, ROCE, NPM, D/E, Revenue CAGR 5yr, Latest FCF
col1, col2, col3, col4, col5, col6 = st.columns(6)

roe = latest_year_ratios.get("return_on_equity_pct", "N/A")
roce = latest_year_ratios.get("return_on_capital_employed_pct", "N/A")
npm = latest_year_ratios.get("net_margin_pct", "N/A")
de = latest_year_ratios.get("debt_to_equity", "N/A")
rev_cagr = latest_year_ratios.get("sales_cagr_5y", "N/A")
fcf = latest_year_ratios.get("free_cash_flow", "N/A")

with col1:
    st.metric("ROE", f"{roe:.2f}%" if pd.notnull(roe) and type(roe) != str else "N/A")
with col2:
    st.metric(
        "ROCE", f"{roce:.2f}%" if pd.notnull(roce) and type(roce) != str else "N/A"
    )
with col3:
    st.metric("NPM", f"{npm:.2f}%" if pd.notnull(npm) and type(npm) != str else "N/A")
with col4:
    st.metric("D/E", f"{de:.2f}" if pd.notnull(de) and type(de) != str else "N/A")
with col5:
    st.metric(
        "Revenue CAGR 5y",
        f"{rev_cagr:.2f}%" if pd.notnull(rev_cagr) and type(rev_cagr) != str else "N/A",
    )
with col6:
    st.metric(
        "Latest FCF", f"₹{fcf} Cr" if pd.notnull(fcf) and type(fcf) != str else "N/A"
    )

st.divider()

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Revenue vs Net Profit (10 Years)")
    if not pl_df.empty:
        pl_10yr = pl_df.sort_values("year").tail(10)
        if len(pl_10yr) < 10:
            st.caption(f"*Note: Showing {len(pl_10yr)} years of available P&L data.*")
        fig_bar = go.Figure()
        if "sales" in pl_10yr.columns:
            fig_bar.add_trace(
                go.Bar(x=pl_10yr["year"], y=pl_10yr["sales"], name="Revenue")
            )
        if "net_profit" in pl_10yr.columns:
            fig_bar.add_trace(
                go.Bar(x=pl_10yr["year"], y=pl_10yr["net_profit"], name="Net Profit")
            )

        fig_bar.update_layout(
            barmode="group",
            xaxis_title="Year",
            yaxis_title="Amount (Cr)",
            margin=dict(t=30, b=0, l=0, r=0),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.write("No P&L data available.")

with col_chart2:
    st.subheader("ROE & ROCE Trend (10 Years)")
    if not ratios_df.empty:
        rat_10yr = ratios_df.sort_values("year").tail(10)
        if len(rat_10yr) < 10:
            st.caption(
                f"*Note: Showing {len(rat_10yr)} years of available ratios data.*"
            )
        fig_line = go.Figure()

        if "return_on_equity_pct" in rat_10yr.columns:
            fig_line.add_trace(
                go.Scatter(
                    x=rat_10yr["year"],
                    y=rat_10yr["return_on_equity_pct"],
                    name="ROE",
                    mode="lines+markers",
                )
            )
        if "return_on_capital_employed_pct" in rat_10yr.columns:
            fig_line.add_trace(
                go.Scatter(
                    x=rat_10yr["year"],
                    y=rat_10yr["return_on_capital_employed_pct"],
                    name="ROCE",
                    mode="lines+markers",
                )
            )

        fig_line.update_layout(
            xaxis_title="Year",
            yaxis_title="Percentage (%)",
            margin=dict(t=30, b=0, l=0, r=0),
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.write("No Ratios data available.")

st.divider()

st.subheader("Pros & Cons")
col_pros, col_cons = st.columns(2)

pros = []
cons = []

if pd.notnull(roe) and type(roe) != str:
    if roe > 15:
        pros.append(f"High Return on Equity: {roe:.2f}%")
    elif roe < 10:
        cons.append(f"Low Return on Equity: {roe:.2f}%")

if pd.notnull(roce) and type(roce) != str:
    if roce > 15:
        pros.append(f"High Return on Capital Employed: {roce:.2f}%")
    elif roce < 10:
        cons.append(f"Low Return on Capital Employed: {roce:.2f}%")

if pd.notnull(de) and type(de) != str:
    if de < 0.5:
        pros.append(f"Low Debt to Equity Ratio: {de:.2f}")
    elif de > 1.5:
        cons.append(f"High Debt to Equity Ratio: {de:.2f}")

if pd.notnull(rev_cagr) and type(rev_cagr) != str:
    if rev_cagr > 10:
        pros.append(f"Strong 5-year Revenue CAGR: {rev_cagr:.2f}%")
    elif rev_cagr < 5:
        cons.append(f"Weak 5-year Revenue CAGR: {rev_cagr:.2f}%")

with col_pros:
    st.markdown("### 👍 Pros")
    if pros:
        for p in pros:
            st.markdown(f"- ✅ {p}")
    else:
        st.write("No distinct pros identified.")

with col_cons:
    st.markdown("### 👎 Cons")
    if cons:
        for c in cons:
            st.markdown(f"- ❌ {c}")
    else:
        st.write("No distinct cons identified.")
