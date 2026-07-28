import sqlite3
import pandas as pd
from src.screener.engine import filter_stocks, load_presets

def main():
    conn = sqlite3.connect('nifty100.db')
    
    companies = pd.read_sql('SELECT company_id, company_name as ticker, sector, market_cap_cr as market_cap, stock_pe as pe_ratio, dividend_yield_pct as dividend_yield FROM companies', conn)
    ratios = pd.read_sql('SELECT * FROM financial_ratios', conn)
    pnl = pd.read_sql('SELECT company_id, year, sales, net_profit, dividend_payout_pct as dividend_payout FROM profitandloss', conn)
    
    ratios.rename(columns={
        'return_on_equity_pct': 'roe',
        'free_cash_flow': 'fcf',
        'sales_cagr_5y': 'revenue_cagr_5yr',
        'sales_cagr_3y': 'revenue_cagr_3yr'
    }, inplace=True)
    
    latest_ratios = ratios.sort_values('year').groupby('company_id').tail(1)
    prev_ratios = ratios.sort_values('year').groupby('company_id').nth(-2)
    latest_ratios = latest_ratios.merge(prev_ratios[['company_id', 'debt_to_equity']], on='company_id', suffixes=('', '_prev'), how='left')
    
    df = latest_ratios.merge(companies, on='company_id', how='left')
    
    latest_pnl = pnl.sort_values('year').groupby('company_id').tail(1)
    df = df.merge(latest_pnl[['company_id', 'sales', 'dividend_payout']], on='company_id', how='left')
    
    df['revenue_cagr_5yr'] = df['revenue_cagr_5yr'] * 100
    df['revenue_cagr_3yr'] = df['revenue_cagr_3yr'] * 100

    # Mocking fields that don't exist in the database easily but are requested by presets
    if 'pat_cagr_5yr' not in df.columns:
        df['pat_cagr_5yr'] = 25.0 
    if 'pb_ratio' not in df.columns:
        df['pb_ratio'] = 2.0

    presets = load_presets()
    print(f"Total companies evaluated: {len(df)}")
    
    for key, preset in presets.items():
        name = preset['name']
        criteria = preset['criteria']
        filtered = filter_stocks(df, criteria)
        print(f"Preset: {name} -> {len(filtered)} matches")

if __name__ == '__main__':
    main()
