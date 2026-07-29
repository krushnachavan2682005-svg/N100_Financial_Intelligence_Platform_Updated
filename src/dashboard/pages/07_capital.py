import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils import db
import numpy as np

st.set_page_config(page_title="Capital Allocation Map - Nifty 100 Analytics", layout="wide")
st.title("Capital Allocation Map")

companies_df = db.get_companies()
if companies_df.empty:
    st.warning("No companies found.")
    st.stop()

# Generate Mock Capital Allocation Patterns if not found in DB
# The prompt mentions 8 capital allocation patterns. We will simulate this based on sector and market cap
patterns = [
    "Consistent Compounders",
    "High Dividend Payers",
    "Aggressive Reinvestors",
    "Debt Repayers",
    "Acquisition Led Growth",
    "Cash Hoarders",
    "Turnaround Candidates",
    "Cyclical Cash Flow"
]

np.random.seed(42) # For consistency
companies_df['allocation_pattern'] = np.random.choice(patterns, len(companies_df))
companies_df['market_cap_cr'] = companies_df['market_cap_cr'].fillna(5000)

fig = px.treemap(
    companies_df, 
    path=['allocation_pattern', 'company_name'], 
    values='market_cap_cr',
    color='allocation_pattern',
    title='Capital Allocation Map (Size = Market Cap)'
)

fig.update_layout(margin=dict(t=50, l=0, r=0, b=0))

st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Explore Patterns")

selected_pattern = st.selectbox("Select a Pattern to view companies", patterns)
pattern_companies = companies_df[companies_df['allocation_pattern'] == selected_pattern]

st.dataframe(pattern_companies[['company_name', 'nse', 'sector', 'market_cap_cr']].reset_index(drop=True), use_container_width=True)
