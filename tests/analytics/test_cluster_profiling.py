import os
import pytest
import pandas as pd
import numpy as np
from src.analytics.cluster_profiling import profile_clusters, generate_heatmap, detect_outliers, portfolio_stats

@pytest.fixture
def mock_df():
    data = []
    sectors = ['Tech', 'Finance', 'Health']
    for i in range(92):
        data.append({
            'company_id': i,
            'company_name': f'Comp_{i}',
            'broad_sector': sectors[i % 3],
            'return_on_equity_pct': np.random.randn() * 10 + 15,
            'operating_profit_margin_pct': np.random.randn() * 5 + 20,
            'net_profit_margin_pct': np.random.randn() * 5 + 10,
            'debt_to_equity': np.random.rand() * 2,
            'interest_coverage': np.random.randn() * 2 + 5,
            'asset_turnover': np.random.rand() * 2,
            'free_cash_flow_cr': np.random.randn() * 1000 + 500,
            'revenue_cagr_5yr': np.random.randn() * 5 + 10,
            'pat_cagr_5yr': np.random.randn() * 5 + 12,
            'stock_pe': np.random.randn() * 10 + 20
        })
    df = pd.DataFrame(data)
    
    # Insert an outlier
    df.loc[0, 'return_on_equity_pct'] = 1000.0
    return df

def test_profile_clusters(mock_df, tmp_path, monkeypatch):
    # Mock cluster_labels.csv
    cluster_df = pd.DataFrame({
        'company_id': range(92),
        'cluster_id': [i % 5 for i in range(92)],
        'distance_from_centroid': [1.0] * 92
    })
    os.makedirs('output', exist_ok=True)
    cluster_df.to_csv('output/cluster_labels.csv', index=False)
    
    df = profile_clusters(mock_df)
    assert 'cluster_name' in df.columns
    assert len(df['cluster_name'].unique()) == 5
    
    saved_df = pd.read_csv('output/cluster_labels.csv')
    assert 'cluster_name' in saved_df.columns

def test_heatmap_generation(mock_df, tmp_path):
    # Change working directory so it saves to tmp_path/reports/
    os.makedirs('reports', exist_ok=True)
    generate_heatmap(mock_df)
    assert os.path.exists('reports/correlation_heatmap.png')

def test_outlier_detection(mock_df):
    os.makedirs('output', exist_ok=True)
    detect_outliers(mock_df)
    assert os.path.exists('output/outlier_report.csv')
    outliers = pd.read_csv('output/outlier_report.csv')
    assert len(outliers) > 0
    assert 'company_id' in outliers.columns
    assert 'z_score' in outliers.columns

def test_portfolio_stats(mock_df):
    os.makedirs('output', exist_ok=True)
    portfolio_stats(mock_df)
    assert os.path.exists('output/portfolio_stats.csv')
    stats = pd.read_csv('output/portfolio_stats.csv')
    assert len(stats) == 10
    assert 'p50' in stats.columns
    assert 'mean' in stats.columns
