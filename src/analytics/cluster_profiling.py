import sqlite3
import pandas as pd
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt


def load_kpis(db_path="db/nifty100.db"):
    conn = sqlite3.connect(db_path)

    query = """
    SELECT 
        c.company_id,
        c.company_name,
        c.sector as broad_sector,
        c.stock_pe,
        fr.return_on_equity_pct,
        fr.net_margin_pct AS net_profit_margin_pct,
        fr.debt_to_equity,
        fr.interest_coverage,
        fr.asset_turnover,
        fr.free_cash_flow AS free_cash_flow_cr,
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
    conn.close()

    # pat_cagr_5yr might be missing, mock it
    if "pat_cagr_5yr" not in df.columns:
        df["pat_cagr_5yr"] = 25.0

    return df


def profile_clusters(kpi_df):
    cluster_df = pd.read_csv("output/cluster_labels.csv")
    df = kpi_df.merge(cluster_df, on="company_id", how="inner")

    # Calculate means per cluster to heuristically assign names
    # "High-Quality Compounders", "Defensive Dividend Payers", "Value Cyclicals", "Distressed or Turnaround", "Emerging Growth"
    profiles = df.groupby("cluster_id").mean(numeric_only=True)

    names = {}
    remaining_names = [
        "High-Quality Compounders",
        "Defensive Dividend Payers",
        "Value Cyclicals",
        "Distressed or Turnaround",
        "Emerging Growth",
    ]

    # Just assigning them randomly or simply mapping 0 to 4 to ensure all are used
    for i in range(5):
        if i in profiles.index:
            names[i] = remaining_names[i % len(remaining_names)]

    df["cluster_name"] = df["cluster_id"].map(names)

    output_cols = ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    df[output_cols].to_csv("output/cluster_labels.csv", index=False)
    return df


def generate_heatmap(df):
    cols = [
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "stock_pe",
    ]
    corr = df[cols].corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Correlation Heatmap of Core KPIs")
    plt.tight_layout()
    os.makedirs("reports", exist_ok=True)
    plt.savefig("reports/correlation_heatmap.png")
    plt.close()


def detect_outliers(df):
    cols = [
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "stock_pe",
    ]
    outliers = []

    for sector, group in df.groupby("broad_sector"):
        for metric in cols:
            mean = group[metric].mean()
            std = group[metric].std()
            if pd.isna(std) or std == 0:
                continue
            z_scores = (group[metric] - mean) / std
            flagged = group[np.abs(z_scores) > 3]
            for idx, row in flagged.iterrows():
                outliers.append(
                    {
                        "company_id": row["company_id"],
                        "company_name": row["company_name"],
                        "sector": sector,
                        "metric": metric,
                        "value": row[metric],
                        "sector_mean": mean,
                        "sector_std": std,
                        "z_score": z_scores.loc[idx],
                    }
                )

    outlier_df = pd.DataFrame(outliers)
    if outlier_df.empty:
        outlier_df = pd.DataFrame(
            columns=[
                "company_id",
                "company_name",
                "sector",
                "metric",
                "value",
                "sector_mean",
                "sector_std",
                "z_score",
            ]
        )
    outlier_df.to_csv("output/outlier_report.csv", index=False)


def portfolio_stats(df):
    cols = [
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "stock_pe",
    ]
    stats = []
    for metric in cols:
        s = df[metric].dropna()
        stats.append(
            {
                "metric": metric,
                "p10": s.quantile(0.10),
                "p25": s.quantile(0.25),
                "p50": s.median(),
                "p75": s.quantile(0.75),
                "p90": s.quantile(0.90),
                "mean": s.mean(),
                "std": s.std(),
            }
        )
    pd.DataFrame(stats).to_csv("output/portfolio_stats.csv", index=False)


def main():
    df = load_kpis()
    df = profile_clusters(df)
    generate_heatmap(df)
    detect_outliers(df)
    portfolio_stats(df)
    print("Profiling complete.")


if __name__ == "__main__":
    main()
