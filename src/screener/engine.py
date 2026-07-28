import pandas as pd
import numpy as np
import yaml
import os

def filter_stocks(df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    """
    Filter a DataFrame of financial ratios based on specific criteria.
    
    Args:
        df: DataFrame containing financial ratios and metrics.
        criteria: Dictionary of filter criteria.
        
    Returns:
        Filtered DataFrame with a composite_quality_score.
    """
    filtered_df = df.copy()
    
    if 'roe_min' in criteria:
        filtered_df = filtered_df[filtered_df['roe'] >= criteria['roe_min']]
        
    if 'd_e_max' in criteria:
        if 'sector' in filtered_df.columns:
            mask = (filtered_df['debt_to_equity'] <= criteria['d_e_max']) | (filtered_df['sector'] == 'Financials')
            filtered_df = filtered_df[mask]
        else:
            filtered_df = filtered_df[filtered_df['debt_to_equity'] <= criteria['d_e_max']]
            
    if 'fcf_min' in criteria:
        filtered_df = filtered_df[filtered_df['fcf'] >= criteria['fcf_min']]
        
    if 'revenue_cagr_5yr_min' in criteria:
        filtered_df = filtered_df[filtered_df['revenue_cagr_5yr'] >= criteria['revenue_cagr_5yr_min']]
        
    if 'pat_cagr_5yr_min' in criteria:
        filtered_df = filtered_df[filtered_df['pat_cagr_5yr'] >= criteria['pat_cagr_5yr_min']]
        
    if 'opm_min' in criteria:
        filtered_df = filtered_df[filtered_df['opm'] >= criteria['opm_min']]
        
    if 'pe_max' in criteria:
        filtered_df = filtered_df[filtered_df['pe_ratio'] <= criteria['pe_max']]
        
    if 'pb_max' in criteria:
        filtered_df = filtered_df[filtered_df['pb_ratio'] <= criteria['pb_max']]
        
    if 'dividend_yield_min' in criteria:
        filtered_df = filtered_df[filtered_df['dividend_yield'] >= criteria['dividend_yield_min']]
        
    if 'icr_min' in criteria:
        def check_icr(icr_val):
            if pd.isna(icr_val) or str(icr_val).strip().lower() in ['debt free', 'none', '']:
                return np.inf
            try:
                return float(icr_val)
            except ValueError:
                return -np.inf

        if 'icr' in filtered_df.columns:
            icr_numeric = filtered_df['icr'].apply(check_icr)
            filtered_df = filtered_df[icr_numeric >= criteria['icr_min']]

    if 'market_cap_min' in criteria:
        filtered_df = filtered_df[filtered_df['market_cap'] >= criteria['market_cap_min']]
        
    if 'net_profit_min' in criteria:
        filtered_df = filtered_df[filtered_df['net_profit'] >= criteria['net_profit_min']]
        
    if 'eps_cagr_min' in criteria:
        filtered_df = filtered_df[filtered_df['eps_cagr'] >= criteria['eps_cagr_min']]
        
    if 'asset_turnover_min' in criteria:
        filtered_df = filtered_df[filtered_df['asset_turnover'] >= criteria['asset_turnover_min']]
        
    if 'sales_min' in criteria:
        filtered_df = filtered_df[filtered_df['sales'] >= criteria['sales_min']]
        
    if 'dividend_payout_max' in criteria:
        if 'dividend_payout' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['dividend_payout'] <= criteria['dividend_payout_max']]
            
    if 'revenue_cagr_3yr_min' in criteria:
        if 'revenue_cagr_3yr' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['revenue_cagr_3yr'] >= criteria['revenue_cagr_3yr_min']]
            
    if criteria.get('d_e_declining_yoy', False):
        if 'debt_to_equity' in filtered_df.columns and 'debt_to_equity_prev' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['debt_to_equity'] < filtered_df['debt_to_equity_prev']]

        
    filtered_df['composite_quality_score'] = 0.0
    
    if 'market_cap' in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by='market_cap', ascending=False)
    elif len(filtered_df) > 0:
        filtered_df = filtered_df.sort_index()
    
    return filtered_df

def load_presets(config_path: str = 'config/screener_config.yaml') -> dict:
    """
    Load screener presets from a YAML configuration file.
    """
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('presets', {})
