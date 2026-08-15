import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.dashboard.utils import db

st.set_page_config(page_title="Peer Comparison - Nifty 100 Analytics", layout="wide")
st.title("Peer Comparison")

sectors_df = db.get_sectors()
if sectors_df.empty:
    st.warning("No sectors available.")
    st.stop()

# Dropdown for Peer Group
sectors = sorted(sectors_df["sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Select Peer Group (Sector)", sectors)

# Fetch peers for the selected sector
peers_df = db.get_peers(selected_sector)
if peers_df.empty:
    st.warning("No companies found in this sector.")
    st.stop()

# Dropdown for Benchmark Company
peer_names = peers_df["nse"] + " - " + peers_df["company_name"]
selected_peer_option = st.selectbox("Select Benchmark Company", peer_names.tolist())
benchmark_ticker = selected_peer_option.split(" - ")[0]

ratios_df = db.get_ratios()

# Get latest year for all peers
latest_year = ratios_df["year"].max()
year_ratios = ratios_df[ratios_df["year"] == latest_year]

# Merge peers with ratios
merged_peers = pd.merge(peers_df, year_ratios, on="company_id", how="inner")

if merged_peers.empty:
    st.warning("No financial data available for this peer group.")
    st.stop()

# 8 Metrics for Radar Chart
metrics = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_margin_pct",
    "gross_margin_pct",
    "sales_cagr_5y",
    "dividend_yield_pct_x",
    "price_to_earnings",
    "debt_to_equity",
]

# Calculate Percentiles for the Radar Chart
# Radar chart works best with 0-100 scale
radar_df = merged_peers.copy()
for m in metrics:
    if m in radar_df.columns:
        # For P/E and D/E, lower is better (so we invert the rank)
        if m in ["price_to_earnings", "debt_to_equity"]:
            radar_df[f"{m}_score"] = radar_df[m].rank(pct=True, ascending=False) * 100
        else:
            radar_df[f"{m}_score"] = radar_df[m].rank(pct=True) * 100
    else:
        radar_df[f"{m}_score"] = 50  # Default middle if missing

# Get Benchmark Data
benchmark_data = radar_df[radar_df["nse_x"] == benchmark_ticker]
if benchmark_data.empty:
    st.error("Benchmark company data not found for the selected year.")
    st.stop()
benchmark_data = benchmark_data.iloc[0]

# Get Peer Average Data
peer_avg_data = radar_df[[f"{m}_score" for m in metrics]].mean()

# Radar Chart
categories = [
    "ROE",
    "ROCE",
    "Net Margin",
    "Gross Margin",
    "Rev CAGR 5y",
    "Div Yield",
    "P/E (Inverted)",
    "D/E (Inverted)",
]

fig = go.Figure()

fig.add_trace(
    go.Scatterpolar(
        r=[benchmark_data[f"{m}_score"] for m in metrics],
        theta=categories,
        fill="toself",
        name=benchmark_ticker,
    )
)

fig.add_trace(
    go.Scatterpolar(
        r=[peer_avg_data[f"{m}_score"] for m in metrics],
        theta=categories,
        fill="toself",
        name="Peer Average",
    )
)

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True,
    margin=dict(t=50, b=50, l=50, r=50),
)

st.subheader("Relative Performance vs Peers (Percentile Scores)")
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader(f"KPI Table - {selected_sector} Sector")
# Side-by-side KPI table
display_cols = ["company_name", "nse_x"] + metrics
actual_cols = [c for c in display_cols if c in merged_peers.columns]


# Apply styling to highlight benchmark row
def highlight_row(row):
    if row["nse_x"] == benchmark_ticker:
        return ["background-color: rgba(0, 255, 0, 0.2)"] * len(row)
    return [""] * len(row)


styled_df = merged_peers[actual_cols].style.apply(highlight_row, axis=1)

st.dataframe(styled_df, use_container_width=True)
