import pytest
import pandas as pd
from src.nlp.pros_cons_generator import calculate_confidence, generate_pros_cons

def test_calculate_confidence():
    # > threshold test
    assert calculate_confidence(25, 20, 40, ">") == 70.0 # (25-20)/(40-20) * 40 + 60 = 5/20 * 40 + 60 = 10 + 60 = 70
    assert calculate_confidence(15, 20, 40, ">") == 0.0 # below threshold
    assert calculate_confidence(100, 20, 40, ">") == 100.0 # capped at 100
    
    # < threshold test
    assert calculate_confidence(10, 15, 5, "<") == 80.0 # (15-10)/(15-5) * 40 + 60 = 5/10 * 40 + 60 = 20 + 60 = 80
    assert calculate_confidence(20, 15, 5, "<") == 0.0 # above threshold
    assert calculate_confidence(0, 15, 5, "<") == 100.0 # capped at 100

def test_generate_pros_cons():
    mock_data = pd.DataFrame({
        'company_id': [1, 2],
        'sector': ['IT', 'Financials'],
        'return_on_equity_pct': [25, 5], # P1 pro for comp 1, C7 con for comp 2
        'debt_to_equity': [0, 2.5], # P2 pro for comp 1. C1 con for comp 2? No, comp 2 is Financials so C1 doesn't apply.
        'free_cash_flow': [1000, -500], # P3 pro for comp 1, C2 con for comp 2
        'sales_cagr_5y': [20, 2], # P4 pro for comp 1, C9 con for comp 2
        'opm_pct': [30, 2], 
        'interest_coverage': [15, 1],
        'dividend_yield_pct': [3.0, 0.5],
        'return_on_capital_employed_pct': [25, 5],
        'net_margin_pct': [20, 2],
        'price_to_earnings': [10, 100],
        'gross_margin_pct': [50, 20],
        'fcf_to_net_profit': [1.5, 0.5],
        'net_profit': [500, -100],
        'dividend_payout_pct': [50, 150],
        'price_to_book': [5, 15],
        'asset_turnover': [1.5, 0.2]
    })
    
    result = generate_pros_cons(mock_data)
    
    # Check if we have both pros and cons
    assert not result.empty
    
    comp1_pros = result[(result['company_id'] == 1) & (result['type'] == 'pro')]
    comp2_cons = result[(result['company_id'] == 2) & (result['type'] == 'con')]
    
    assert len(comp1_pros) >= 1
    assert len(comp2_cons) >= 1
    
    # Check specific rules
    # Comp 1 should have P1 (ROE > 20)
    assert 'P1' in comp1_pros['rule_id'].values
    
    # Comp 2 should have C2 (FCF < 0)
    assert 'C2' in comp2_cons['rule_id'].values

def test_fallback_rules():
    mock_data = pd.DataFrame({
        'company_id': [3],
        'sector': ['IT'],
        'return_on_equity_pct': [15], # between 10 and 20 (no rule triggered)
        'debt_to_equity': [1.0], 
        'free_cash_flow': [0], # exactly 0
        'sales_cagr_5y': [10],
        'opm_pct': [20],
        'interest_coverage': [5],
        'dividend_yield_pct': [1.0],
        'return_on_capital_employed_pct': [15],
        'net_margin_pct': [10],
        'price_to_earnings': [30],
        'gross_margin_pct': [30],
        'fcf_to_net_profit': [0.5],
        'net_profit': [100],
        'dividend_payout_pct': [50],
        'price_to_book': [5],
        'asset_turnover': [1.0]
    })
    
    result = generate_pros_cons(mock_data)
    
    comp3_pros = result[(result['company_id'] == 3) & (result['type'] == 'pro')]
    comp3_cons = result[(result['company_id'] == 3) & (result['type'] == 'con')]
    
    # Should trigger the fallback rules because no other rules match
    assert len(comp3_pros) == 1
    assert comp3_pros.iloc[0]['rule_id'] == 'P_FB'
    
    assert len(comp3_cons) == 1
    assert comp3_cons.iloc[0]['rule_id'] == 'C_FB'
