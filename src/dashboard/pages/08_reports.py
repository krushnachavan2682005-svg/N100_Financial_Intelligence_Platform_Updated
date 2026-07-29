import streamlit as st
import pandas as pd
import requests
from src.dashboard.utils import db

st.set_page_config(page_title="Annual Reports - Nifty 100 Analytics", layout="wide")
st.title("Annual Reports & Filings")

companies_df = db.get_companies()
if companies_df.empty:
    st.warning("No companies found.")
    st.stop()

# Company Dropdown
company_options = companies_df['nse'] + " - " + companies_df['company_name']
selected_company = st.selectbox("Search Company for Reports", company_options.tolist())
ticker = selected_company.split(" - ")[0]
company_id = companies_df[companies_df['nse'] == ticker]['company_id'].iloc[0]

# Fetch Documents
docs_df = db._run_query("SELECT * FROM documents WHERE company_id = ? AND document_type LIKE '%Annual%'", (int(company_id),))

# Mock data if empty for demonstration
if docs_df.empty:
    st.info("No documents found in DB. Showing mocked data for demonstration.")
    docs_df = pd.DataFrame({
        'title': [f"{ticker} Annual Report 2023", f"{ticker} Annual Report 2022", f"{ticker} Annual Report 2021"],
        'document_date': ['2023-03-31', '2022-03-31', '2021-03-31'],
        'source_url': ['https://www.bseindia.com/mock/report2023.pdf', 'https://www.bseindia.com/mock/report2022.pdf', ''] # Last one is empty
    })

st.subheader(f"Available Reports for {ticker}")

@st.cache_data(ttl=3600)
def check_url(url):
    if not url:
        return False
    try:
        # Use a quick HEAD request
        response = requests.head(url, timeout=2)
        return response.status_code < 400
    except:
        return False

for idx, row in docs_df.iterrows():
    col_text, col_badge = st.columns([3, 1])
    with col_text:
        st.write(f"**{row['title']}** ({row['document_date']})")
        if row['source_url']:
            st.markdown(f"[Download PDF]({row['source_url']})")
    
    with col_badge:
        # Check URL validity
        url = row.get('source_url', '')
        if url:
            # For demonstration, we assume valid if it starts with http, since live checking can block the app
            # and fake bse urls will always fail.
            # We'll use our mock logic to show red badge if URL is empty or explicitly invalid.
            if "mock" in url and "2023" in url:
                st.markdown("✅ **Available**")
            elif "mock" in url:
                st.markdown("❌ **Report Unavailable (404)**")
            else:
                is_valid = check_url(url)
                if is_valid:
                    st.markdown("✅ **Available**")
                else:
                    st.markdown("❌ **Report Unavailable**")
        else:
            st.markdown("❌ **Link Missing**")
            
    st.divider()
