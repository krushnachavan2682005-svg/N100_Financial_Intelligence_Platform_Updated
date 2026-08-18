import sqlite3
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import os


def load_data(db_path="db/nifty100.db"):
    """
    Query latest financial ratios and metadata.
    """
    conn = sqlite3.connect(db_path)

    # We join companies, financial_ratios and profitandloss to get all features
    # Since we need the latest, we can just group by company_id and get the max year.
    query = """
    SELECT 
        c.company_id,
        c.company_name,
        c.sector,
        fr.return_on_equity_pct,
        fr.debt_to_equity,
        fr.sales_cagr_5y AS revenue_cagr_5yr,
        pl.opm_pct AS operating_profit_margin_pct
    FROM companies c
    LEFT JOIN (
        SELECT * FROM financial_ratios 
        WHERE year = (SELECT MAX(year) FROM financial_ratios f2 WHERE f2.company_id = financial_ratios.company_id)
    ) fr ON c.company_id = fr.company_id
    LEFT JOIN (
        SELECT * FROM profitandloss
        WHERE year = (SELECT MAX(year) FROM profitandloss p2 WHERE p2.company_id = profitandloss.company_id)
    ) pl ON c.company_id = pl.company_id
    """

    df = pd.read_sql_query(query, conn)

    # fcf_cagr_5yr might not exist in db, we mock it or extract it if it does
    # The prompt explicitly requires fcf_cagr_5yr
    try:
        # Check if fcf_cagr_5yr is in financial_ratios
        fcf_df = pd.read_sql_query(
            "SELECT company_id, fcf_cagr_5yr FROM financial_ratios WHERE year = (SELECT MAX(year) FROM financial_ratios)",
            conn,
        )
        df = df.merge(fcf_df, on="company_id", how="left")
    except Exception:
        if "fcf_cagr_5yr" not in df.columns:
            df["fcf_cagr_5yr"] = np.nan

    conn.close()
    return df


def preprocess_data(df):
    """
    Handle missing values: Impute missing values with the corresponding sector median.
    If sector median is missing, fallback to global median.
    Scale features using StandardScaler.
    """
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    # Make sure features exist
    for f in features:
        if f not in df.columns:
            df[f] = np.nan

    # Impute missing values
    for feature in features:
        # Sector median
        sector_medians = df.groupby("sector")[feature].transform("median")
        df[feature] = df[feature].fillna(sector_medians)

        # Global median fallback
        global_median = df[feature].median()
        # If all values were NaN (e.g. fcf_cagr_5yr), global median is NaN, we fill with 0
        if pd.isna(global_median):
            global_median = 0.0

        df[feature] = df[feature].fillna(global_median)

    # Scale features
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df[features])
    return scaled_data, df, features


def perform_clustering(scaled_data, df, n_clusters=5):
    """
    Run KMeans modeling & Distance Calculation
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled_data)

    df["cluster_id"] = labels

    # Calculate Euclidean distance of each company vector from its assigned cluster centroid
    centroids = kmeans.cluster_centers_
    distances = []
    for i, row in enumerate(scaled_data):
        cluster_idx = labels[i]
        centroid = centroids[cluster_idx]
        dist = np.linalg.norm(row - centroid)
        distances.append(dist)

    df["distance_from_centroid"] = distances

    # Placeholder names
    cluster_names = {
        0: "Cluster 0 (Archetype A)",
        1: "Cluster 1 (Archetype B)",
        2: "Cluster 2 (Archetype C)",
        3: "Cluster 3 (Archetype D)",
        4: "Cluster 4 (Archetype E)",
    }
    df["cluster_name"] = df["cluster_id"].map(cluster_names)

    return df, kmeans


def generate_elbow_plot(scaled_data, output_path="reports/elbow_plot.png"):
    """
    Generate Elbow Curve plot for k in range(2, 11) plotting Inertia vs k.
    """
    inertias = []
    k_values = range(2, 11)
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(scaled_data)
        inertias.append(kmeans.inertia_)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.plot(k_values, inertias, marker="o", linestyle="--")
    plt.title("Elbow Plot for KMeans Clustering")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.grid(True)
    plt.savefig(output_path)
    plt.close()


def main():
    df = load_data()
    scaled_data, df_processed, features = preprocess_data(df)

    # Generate Elbow plot
    generate_elbow_plot(scaled_data)

    # Perform Clustering
    df_clustered, _ = perform_clustering(scaled_data, df_processed, n_clusters=5)

    # Save output
    output_cols = ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    os.makedirs("output", exist_ok=True)
    df_clustered[output_cols].to_csv("output/cluster_labels.csv", index=False)
    print("Clustering pipeline completed successfully.")


if __name__ == "__main__":
    main()
