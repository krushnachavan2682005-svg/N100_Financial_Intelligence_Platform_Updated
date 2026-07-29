import os
import sqlite3
import pandas as pd
import numpy as np

def get_valuation_data(db_path):
    """Fetches and processes valuation data from the database."""
    conn = sqlite3.connect(db_path)
    
    # Fetch companies
    companies_df = pd.read_sql_query("SELECT company_id, company_name, sector, market_cap_cr FROM companies", conn)
    
    # Fetch ratios
    ratios_df = pd.read_sql_query("SELECT company_id, year, price_to_earnings, price_to_book, free_cash_flow FROM financial_ratios", conn)
    
    conn.close()
    
    if ratios_df.empty or companies_df.empty:
        return pd.DataFrame()
        
    latest_year = ratios_df['year'].max()
    latest_ratios = ratios_df[ratios_df['year'] == latest_year].copy()
    
    # 5yr median PE
    five_years_ago = latest_year - 4
    last_5y_ratios = ratios_df[ratios_df['year'] >= five_years_ago]
    median_pe_5y = last_5y_ratios.groupby('company_id')['price_to_earnings'].median().reset_index()
    median_pe_5y.rename(columns={'price_to_earnings': '5yr_median_PE'}, inplace=True)
    
    # Merge datasets
    merged = pd.merge(companies_df, latest_ratios, on='company_id', how='inner')
    merged = pd.merge(merged, median_pe_5y, on='company_id', how='left')
    
    # Calculate FCF Yield
    # FCF Yield: FCF / Market Cap (in Cr) * 100
    merged['market_cap_cr'] = pd.to_numeric(merged['market_cap_cr'], errors='coerce')
    merged['free_cash_flow'] = pd.to_numeric(merged['free_cash_flow'], errors='coerce')
    merged['FCF_yield_pct'] = np.where(merged['market_cap_cr'] > 0, 
                                       (merged['free_cash_flow'] / merged['market_cap_cr']) * 100, 
                                       np.nan)
    
    # Sector median P/E
    sector_medians = merged.groupby('sector')['price_to_earnings'].median().reset_index()
    sector_medians.rename(columns={'price_to_earnings': 'sector_median_PE'}, inplace=True)
    
    merged = pd.merge(merged, sector_medians, on='sector', how='left')
    
    # Calculate PE vs sector median pct
    merged['PE_vs_sector_median_pct'] = np.where(merged['sector_median_PE'] > 0,
                                                 ((merged['price_to_earnings'] - merged['sector_median_PE']) / merged['sector_median_PE']) * 100,
                                                 np.nan)
    
    # Apply valuation flags
    def assign_flag(row):
        if pd.isna(row['price_to_earnings']) or pd.isna(row['sector_median_PE']):
            return "Unknown"
        if row['price_to_earnings'] > row['sector_median_PE'] * 1.5:
            return "Caution"
        elif row['price_to_earnings'] < row['sector_median_PE'] * 0.7:
            return "Discount"
        else:
            return "Fair"
            
    merged['flag'] = merged.apply(assign_flag, axis=1)
    
    # Rename and select required columns
    # Expected: company_id, company_name, sector, P/E, P/B, EV/EBITDA, FCF_yield_pct, 5yr_median_PE, PE_vs_sector_median_pct, flag
    merged.rename(columns={'price_to_earnings': 'P/E', 'price_to_book': 'P/B'}, inplace=True)
    
    # Add dummy EV/EBITDA as it's not in the base schema but requested
    merged['EV/EBITDA'] = np.nan 
    
    final_cols = ['company_id', 'company_name', 'sector', 'P/E', 'P/B', 'EV/EBITDA', 
                  'FCF_yield_pct', '5yr_median_PE', 'PE_vs_sector_median_pct', 'flag']
    
    # Return available columns if some are missing, but based on above logic all are present
    return merged[final_cols]

def generate_reports(db_path, output_dir):
    """Generates valuation summary and flags reports."""
    df = get_valuation_data(db_path)
    if df.empty:
        print("No data available to generate reports.")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Valuation Summary
    summary_path = os.path.join(output_dir, 'valuation_summary.xlsx')
    df.to_excel(summary_path, index=False)
    print(f"Generated {summary_path}")
    
    # 2. Valuation Flags (Only Caution or Discount)
    flags_df = df[df['flag'].isin(['Caution', 'Discount'])]
    flags_path = os.path.join(output_dir, 'valuation_flags.csv')
    flags_df.to_csv(flags_path, index=False)
    print(f"Generated {flags_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    db_file = os.path.join(base_dir, 'nifty100.db')
    out_dir = os.path.join(base_dir, 'output')
    generate_reports(db_file, out_dir)
