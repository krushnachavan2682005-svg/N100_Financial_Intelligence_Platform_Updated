import streamlit as st
import pandas as pd
from src.dashboard.utils import db

st.set_page_config(page_title="Screener - Nifty 100 Analytics", layout="wide")
st.title("Stock Screener")

# Fetch Data
companies_df = db.get_companies()
ratios_df = db.get_ratios()
# We need OPM and PAT CAGR, let's fetch PL data for all companies to get OPM
# To keep it simple, we'll fetch the whole PL table
@st.cache_data(ttl=600)
def get_all_pl():
    return db._run_query("SELECT p.*, c.nse as ticker FROM profitandloss p JOIN companies c ON p.company_id = c.company_id")

pl_df = get_all_pl()

if ratios_df.empty or companies_df.empty:
    st.warning("No data available.")
    st.stop()

# Get latest year
latest_year = ratios_df['year'].max()
df_latest = ratios_df[ratios_df['year'] == latest_year].copy()
pl_latest = pl_df[pl_df['year'] == latest_year].copy() if not pl_df.empty else pd.DataFrame()

# Merge all
merged = pd.merge(companies_df, df_latest, on='company_id', how='inner')
if not pl_latest.empty:
    merged = pd.merge(merged, pl_latest[['company_id', 'opm_pct']], on='company_id', how='left')
else:
    merged['opm_pct'] = 0

# Mock PAT CAGR if not present
if 'pat_cagr_5y' not in merged.columns:
    merged['pat_cagr_5y'] = merged['net_margin_pct'].fillna(0) # dummy proxy

# Setup Session State for Sliders
presets = {
    'Quality': {'roe': 15.0, 'de': 0.5, 'fcf': 0.0, 'rev_cagr': 10.0, 'pat_cagr': 10.0, 'opm': 15.0, 'pe': 50.0, 'pb': 10.0, 'div': 0.0, 'icr': 5.0},
    'Value': {'roe': 10.0, 'de': 1.0, 'fcf': 0.0, 'rev_cagr': 5.0, 'pat_cagr': 5.0, 'opm': 10.0, 'pe': 15.0, 'pb': 2.0, 'div': 1.0, 'icr': 3.0},
    'Growth': {'roe': 15.0, 'de': 1.5, 'fcf': 0.0, 'rev_cagr': 15.0, 'pat_cagr': 15.0, 'opm': 10.0, 'pe': 100.0, 'pb': 20.0, 'div': 0.0, 'icr': 3.0},
    'Dividend': {'roe': 10.0, 'de': 1.0, 'fcf': 100.0, 'rev_cagr': 5.0, 'pat_cagr': 5.0, 'opm': 10.0, 'pe': 30.0, 'pb': 5.0, 'div': 4.0, 'icr': 3.0},
    'Debt-Free': {'roe': 10.0, 'de': 0.0, 'fcf': 0.0, 'rev_cagr': 5.0, 'pat_cagr': 5.0, 'opm': 10.0, 'pe': 50.0, 'pb': 10.0, 'div': 0.0, 'icr': 5.0},
    'Turnaround': {'roe': 0.0, 'de': 2.0, 'fcf': -1000.0, 'rev_cagr': 0.0, 'pat_cagr': 0.0, 'opm': 0.0, 'pe': 100.0, 'pb': 5.0, 'div': 0.0, 'icr': 1.0},
    'Reset': {'roe': -50.0, 'de': 10.0, 'fcf': -10000.0, 'rev_cagr': -50.0, 'pat_cagr': -50.0, 'opm': -50.0, 'pe': 200.0, 'pb': 50.0, 'div': 0.0, 'icr': -10.0}
}

for key in presets['Reset'].keys():
    if key not in st.session_state:
        st.session_state[key] = presets['Reset'][key]

def apply_preset(preset_name):
    for key, val in presets[preset_name].items():
        st.session_state[key] = val

# Presets Buttons
st.markdown("### Screener Presets")
cols = st.columns(7)
preset_names = ['Quality', 'Value', 'Growth', 'Dividend', 'Debt-Free', 'Turnaround', 'Reset']
for idx, p_name in enumerate(preset_names):
    if cols[idx].button(p_name):
        apply_preset(p_name)

st.divider()

# Sidebar Sliders
st.sidebar.header("Filter Criteria")
st.session_state['roe'] = st.sidebar.slider("ROE Min (%)", min_value=-50.0, max_value=100.0, value=float(st.session_state['roe']), step=1.0)
st.session_state['de'] = st.sidebar.slider("D/E Max", min_value=0.0, max_value=10.0, value=float(st.session_state['de']), step=0.1)
st.session_state['fcf'] = st.sidebar.slider("FCF Min (Cr)", min_value=-10000.0, max_value=10000.0, value=float(st.session_state['fcf']), step=100.0)
st.session_state['rev_cagr'] = st.sidebar.slider("Rev CAGR 5y Min (%)", min_value=-50.0, max_value=100.0, value=float(st.session_state['rev_cagr']), step=1.0)
st.session_state['pat_cagr'] = st.sidebar.slider("PAT CAGR 5y Min (%)", min_value=-50.0, max_value=100.0, value=float(st.session_state['pat_cagr']), step=1.0)
st.session_state['opm'] = st.sidebar.slider("OPM Min (%)", min_value=-50.0, max_value=100.0, value=float(st.session_state['opm']), step=1.0)
st.session_state['pe'] = st.sidebar.slider("P/E Max", min_value=0.0, max_value=200.0, value=float(st.session_state['pe']), step=1.0)
st.session_state['pb'] = st.sidebar.slider("P/B Max", min_value=0.0, max_value=50.0, value=float(st.session_state['pb']), step=0.5)
st.session_state['div'] = st.sidebar.slider("Div Yield Min (%)", min_value=0.0, max_value=15.0, value=float(st.session_state['div']), step=0.1)
st.session_state['icr'] = st.sidebar.slider("ICR Min", min_value=-10.0, max_value=50.0, value=float(st.session_state['icr']), step=0.5)

# Filtering logic
filtered = merged.copy()
filtered = filtered[
    (filtered['return_on_equity_pct'].fillna(-100) >= st.session_state['roe']) &
    (filtered['debt_to_equity'].fillna(100) <= st.session_state['de']) &
    (filtered['free_cash_flow'].fillna(-10000) >= st.session_state['fcf']) &
    (filtered['sales_cagr_5y'].fillna(-100) >= st.session_state['rev_cagr']) &
    (filtered['pat_cagr_5y'].fillna(-100) >= st.session_state['pat_cagr']) &
    (filtered['opm_pct'].fillna(-100) >= st.session_state['opm']) &
    (filtered['price_to_earnings'].fillna(1000) <= st.session_state['pe']) &
    (filtered['price_to_book'].fillna(1000) <= st.session_state['pb']) &
    (filtered['dividend_yield_pct_x'].fillna(0) >= st.session_state['div']) &
    (filtered['interest_coverage'].fillna(-100) >= st.session_state['icr'])
]

# Composite Score
if 'return_on_equity_pct' in filtered.columns and 'return_on_capital_employed_pct' in filtered.columns:
    filtered['composite_score'] = filtered['return_on_equity_pct'].fillna(0) + filtered['return_on_capital_employed_pct'].fillna(0)
else:
    filtered['composite_score'] = 0

# Count Label
st.subheader(f"✅ {len(filtered)} companies match your filters")

display_cols = ['company_id', 'company_name', 'sector', 'composite_score', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow', 'sales_cagr_5y', 'opm_pct', 'price_to_earnings', 'price_to_book', 'dividend_yield_pct_x', 'interest_coverage']
actual_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(filtered[actual_cols].sort_values(by='composite_score', ascending=False).reset_index(drop=True), use_container_width=True)

# CSV Download
csv = filtered[actual_cols].to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Filtered Results as CSV",
    data=csv,
    file_name='screener_results.csv',
    mime='text/csv',
)
