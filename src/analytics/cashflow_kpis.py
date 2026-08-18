import os
import sqlite3
import pandas as pd
import numpy as np


def calculate_cfo_quality(cfo_list, pat_list):
    """Calculate 5-year avg CFO / PAT ratio."""
    cfo_sum = sum(cfo_list)
    pat_sum = sum(pat_list)
    if pat_sum <= 0 and cfo_sum > 0:
        return 1.5  # Arbitrary high quality if making cash despite losses
    if pat_sum == 0:
        return 0.0
    return cfo_sum / pat_sum


def get_cfo_label(score):
    if pd.isna(score):
        return "Unknown"
    if score > 1.0:
        return "High Quality"
    if score >= 0.5:
        return "Moderate"
    return "Accrual Risk"


def get_capex_label(pct):
    if pd.isna(pct):
        return "Unknown"
    if pct < 3.0:
        return "Asset Light"
    if pct <= 8.0:
        return "Moderate"
    return "Capital Intensive"


def generate_cashflow_kpis(db_path):
    conn = sqlite3.connect(db_path)

    query = """
    SELECT 
        c.company_id, c.company_name, c.sector,
        cf.year,
        cf.cash_from_operating_activity as cfo,
        cf.cash_from_investing_activity as cfi,
        cf.cash_from_financing_activity as cff,
        pl.net_profit as pat,
        pl.sales,
        bs.borrowings
    FROM companies c
    JOIN cashflow cf ON c.company_id = cf.company_id
    JOIN profitandloss pl ON c.company_id = pl.company_id AND cf.year = pl.year
    JOIN balancesheet bs ON c.company_id = bs.company_id AND cf.year = bs.year
    ORDER BY c.company_id, cf.year
    """
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        conn.close()
        return pd.DataFrame(), pd.DataFrame()

    conn.close()

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    results = []

    for comp_id, group in df.groupby("company_id"):
        group = group.sort_values("year")
        sector = group["sector"].iloc[0]
        company_name = group["company_name"].iloc[0]

        # Last 5 years
        last_5y = group.tail(5)
        cfo_list = last_5y["cfo"].fillna(0).tolist()
        pat_list = last_5y["pat"].fillna(0).tolist()

        cfo_score = calculate_cfo_quality(cfo_list, pat_list)
        cfo_label = get_cfo_label(cfo_score)

        # Latest year logic
        latest = group.iloc[-1]
        prev = group.iloc[-2] if len(group) > 1 else None

        capex_pct = np.nan
        if latest["sales"] > 0:
            capex_pct = abs(latest["cfi"]) / latest["sales"] * 100
        capex_label = get_capex_label(capex_pct)

        # Distress
        distress = False
        if latest["cfo"] < 0 and latest["cff"] > 0:
            distress = True

        # Deleveraging
        deleveraging = False
        if prev is not None:
            if latest["cff"] < 0 and latest["borrowings"] < prev["borrowings"]:
                deleveraging = True

        results.append(
            {
                "company_id": comp_id,
                "company_name": company_name,
                "sector": sector,
                "cfo_quality_score": cfo_score,
                "cfo_quality_label": cfo_label,
                "capex_intensity_pct": capex_pct,
                "capex_label": capex_label,
                "fcf_cagr_5yr": np.nan,  # Mocked as requested schema
                "fcf_conversion_pct": np.nan,
                "distress_flag": distress,
                "deleveraging_flag": deleveraging,
                "capital_allocation_label": "N/A",  # Mocked
                "latest_cfo": latest["cfo"],
                "latest_cff": latest["cff"],
                "latest_pat": latest["pat"],
            }
        )

    master_df = pd.DataFrame(results)
    return master_df


def run_cashflow_kpis(db_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    master_df = generate_cashflow_kpis(db_path)

    if master_df.empty:
        print("No data.")
        return

    # Full dataset output
    out_cols = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]

    export_df = master_df[out_cols]
    summary_path = os.path.join(output_dir, "cashflow_intelligence.xlsx")
    export_df.to_excel(summary_path, index=False)

    # Distress alerts
    distress_df = master_df[master_df["distress_flag"] == True]
    alert_cols = [
        "company_id",
        "company_name",
        "sector",
        "latest_cfo",
        "latest_cff",
        "latest_pat",
    ]
    alerts_path = os.path.join(output_dir, "distress_alerts.csv")
    distress_df[alert_cols].to_csv(alerts_path, index=False)

    print(f"Generated {summary_path}")
    print(f"Generated {alerts_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    db_file = os.path.join(base_dir, "db/nifty100.db")
    out_dir = os.path.join(base_dir, "output")
    run_cashflow_kpis(db_file, out_dir)


def cfo_to_operating_profit(cfo, op_profit):
    try:
        return float(cfo) / float(op_profit)
    except:
        return None


def fcf_to_net_profit(fcf, np):
    try:
        return float(fcf) / float(np)
    except:
        return None


def free_cash_flow(cfo, capex):
    try:
        return float(cfo) - abs(float(capex))
    except:
        return None


def write_capital_allocation_csv(df, output_path):
    with open(output_path, "w") as f:
        f.write("company_id,year,cfo_sign,cfi_sign,cff_sign,pattern_label\n")
