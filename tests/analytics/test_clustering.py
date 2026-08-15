import pandas as pd
import numpy as np
from src.analytics.clustering import (
    preprocess_data,
    perform_clustering,
    generate_elbow_plot,
)


def test_imputation_and_scaling():
    # Create mock dataframe with 92 rows
    data = []
    for i in range(92):
        # We make some missing data to test imputation
        data.append(
            {
                "company_id": i,
                "company_name": f"Comp_{i}",
                "sector": "Tech" if i < 46 else "Finance",
                "return_on_equity_pct": 15.0 if i % 10 != 0 else np.nan,
                "debt_to_equity": 1.0,
                "revenue_cagr_5yr": 10.0,
                "fcf_cagr_5yr": np.nan,  # All missing
                "operating_profit_margin_pct": 20.0 if i % 5 != 0 else np.nan,
            }
        )
    df = pd.DataFrame(data)

    scaled_data, df_processed, features = preprocess_data(df)

    # Assert shape
    assert scaled_data.shape == (92, 5)

    # Assert no missing values
    for f in features:
        assert not df_processed[f].isna().any()

    # Assert scaling (mean ~ 0, std ~ 1) - some columns might have std 0 if all values are same
    means = np.nanmean(scaled_data, axis=0)
    for m in means:
        assert np.isclose(m, 0.0, atol=1e-5)


def test_kmeans_clustering():
    np.random.seed(42)
    # 92 companies, 5 features, random data
    scaled_data = np.random.randn(92, 5)
    df = pd.DataFrame({"company_id": range(92)})

    df_clustered, kmeans_model = perform_clustering(scaled_data, df, n_clusters=5)

    assert "cluster_id" in df_clustered.columns
    assert "cluster_name" in df_clustered.columns
    assert "distance_from_centroid" in df_clustered.columns

    assert len(df_clustered) == 92
    assert set(df_clustered["cluster_id"].unique()).issubset({0, 1, 2, 3, 4})

    # Ensure distances are positive
    assert (df_clustered["distance_from_centroid"] >= 0).all()


def test_output_generation(tmp_path):
    np.random.seed(42)
    scaled_data = np.random.randn(92, 5)

    # Elbow plot
    plot_path = tmp_path / "elbow_plot.png"
    generate_elbow_plot(scaled_data, output_path=str(plot_path))
    assert plot_path.exists()
    assert plot_path.stat().st_size > 0
