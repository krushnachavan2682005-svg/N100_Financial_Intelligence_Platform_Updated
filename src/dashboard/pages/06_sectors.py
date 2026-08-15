import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.utils import db

st.set_page_config(page_title="Sector Analysis - Nifty 100 Analytics", layout="wide")
st.title("Sector Analysis")

sectors_df = db.get_sectors()
if sectors_df.empty:
    st.warning("No sectors available.")
    st.stop()

# Sector Dropdown
sectors = sorted(sectors_df["sector"].dropna().unique().tolist())
# Option to select 'All Sectors'
sectors.insert(0, "All Sectors")
selected_sector = st.selectbox("Select Sector", sectors)

# Fetch data
companies_df = db.get_companies()
ratios_df = db.get_ratios()


# PL Data for Revenue
@st.cache_data(ttl=600)
def get_all_pl():
    return db._run_query(
        "SELECT p.company_id, p.year, p.sales, c.nse as ticker FROM profitandloss p JOIN companies c ON p.company_id = c.company_id"
    )


pl_df = get_all_pl()

if companies_df.empty or ratios_df.empty or pl_df.empty:
    st.warning("Insufficient data for sector analysis.")
    st.stop()

latest_year = ratios_df["year"].max()
year_ratios = ratios_df[ratios_df["year"] == latest_year]
year_pl = pl_df[pl_df["year"] == latest_year]

merged_df = pd.merge(
    companies_df,
    year_ratios[
        [
            "company_id",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "debt_to_equity",
        ]
    ],
    on="company_id",
    how="inner",
)
merged_df = pd.merge(
    merged_df, year_pl[["company_id", "sales"]], on="company_id", how="left"
)

# Filter by sector if not 'All Sectors'
if selected_sector != "All Sectors":
    filtered_df = merged_df[merged_df["sector"] == selected_sector].copy()
else:
    filtered_df = merged_df.copy()

if filtered_df.empty:
    st.info("No data available for the selected sector.")
    st.stop()

# Plotly Scatter Bubble Chart (X = Revenue, Y = ROE, Bubble Size = Market Cap, Color = Sector/Company)
# If single sector is selected, color by company to differentiate, else color by sector
color_col = "company_name" if selected_sector != "All Sectors" else "sector"

# Handle missing sizes
filtered_df["market_cap_cr"] = filtered_df["market_cap_cr"].fillna(
    1000
)  # Give a default size if missing
filtered_df["sales"] = filtered_df["sales"].fillna(0)
filtered_df["return_on_equity_pct"] = filtered_df["return_on_equity_pct"].fillna(0)

fig_bubble = px.scatter(
    filtered_df,
    x="sales",
    y="return_on_equity_pct",
    size="market_cap_cr",
    color=color_col,
    hover_name="company_name",
    log_x=True,  # Often better for revenue
    title=f"Revenue vs ROE (Size: Market Cap) - {selected_sector}",
    labels={"sales": "Revenue (Cr)", "return_on_equity_pct": "ROE (%)"},
)
fig_bubble.update_layout(margin=dict(t=50, b=0, l=0, r=0))
st.plotly_chart(fig_bubble, use_container_width=True)

st.divider()

# Sector median KPI bar chart
st.subheader("Sector Median KPIs")

if selected_sector != "All Sectors":
    st.write(f"Showing medians for **{selected_sector}** compared to overall market.")

    sector_medians = filtered_df[
        [
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "debt_to_equity",
            "sales",
        ]
    ].median()
    market_medians = merged_df[
        [
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "debt_to_equity",
            "sales",
        ]
    ].median()

    kpis = ["ROE (%)", "ROCE (%)", "D/E Ratio"]
    sector_vals = [
        sector_medians["return_on_equity_pct"],
        sector_medians["return_on_capital_employed_pct"],
        sector_medians["debt_to_equity"],
    ]
    market_vals = [
        market_medians["return_on_equity_pct"],
        market_medians["return_on_capital_employed_pct"],
        market_medians["debt_to_equity"],
    ]

    fig_bar = go.Figure(
        data=[
            go.Bar(name=selected_sector, x=kpis, y=sector_vals),
            go.Bar(name="Overall Market", x=kpis, y=market_vals),
        ]
    )
    fig_bar.update_layout(barmode="group", margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig_bar, use_container_width=True)

else:
    # If all sectors, show bar chart of medians per sector
    sector_grouped = (
        filtered_df.groupby("sector")[
            ["return_on_equity_pct", "return_on_capital_employed_pct", "debt_to_equity"]
        ]
        .median()
        .reset_index()
    )

    fig_bar = px.bar(
        sector_grouped,
        x="sector",
        y=["return_on_equity_pct", "return_on_capital_employed_pct"],
        title="Median ROE & ROCE by Sector",
        barmode="group",
        labels={"value": "Percentage (%)", "variable": "Metric", "sector": "Sector"},
    )
    fig_bar.update_layout(margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig_bar, use_container_width=True)
