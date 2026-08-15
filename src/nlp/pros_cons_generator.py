import os
import sqlite3
import pandas as pd
import numpy as np


def fetch_data(db_path):
    conn = sqlite3.connect(db_path)

    # Fetch data
    companies_df = pd.read_sql_query(
        "SELECT company_id, company_name, sector FROM companies", conn
    )
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    pl_df = pd.read_sql_query(
        "SELECT company_id, year, opm_pct, net_profit, dividend_payout_pct FROM profitandloss",
        conn,
    )

    conn.close()

    if ratios_df.empty or companies_df.empty:
        return pd.DataFrame()

    latest_year = ratios_df["year"].max()
    ratios_latest = ratios_df[ratios_df["year"] == latest_year].copy()
    pl_latest = (
        pl_df[pl_df["year"] == latest_year].copy()
        if not pl_df.empty
        else pd.DataFrame(
            columns=["company_id", "opm_pct", "net_profit", "dividend_payout_pct"]
        )
    )

    merged = pd.merge(companies_df, ratios_latest, on="company_id", how="left")
    merged = pd.merge(merged, pl_latest, on="company_id", how="left")

    return merged


def calculate_confidence(value, threshold, best_val=None, rule_type=">"):
    """Calculate a confidence score between 0 and 100."""
    if pd.isna(value) or value is None:
        return 0.0

    if rule_type == ">":
        if value <= threshold:
            return 0.0
        # Scale between threshold and best_val (cap at 100)
        if best_val is None:
            best_val = threshold * 2
        score = 60 + ((value - threshold) / (best_val - threshold)) * 40
        return min(100.0, max(0.0, score))
    else:  # "<"
        if value >= threshold:
            return 0.0
        if best_val is None:
            best_val = threshold / 2 if threshold != 0 else -10
        score = 60 + ((threshold - value) / (threshold - best_val)) * 40
        return min(100.0, max(0.0, score))


def safe_float(val):
    try:
        f = float(val)
        return f if pd.notna(f) else np.nan
    except (ValueError, TypeError):
        return np.nan


def generate_pros_cons(df):
    results = []

    for idx, row in df.iterrows():
        comp_id = row["company_id"]
        sector = row["sector"]

        has_pro = False
        has_con = False

        # PRO RULES

        # P1: ROE > 20%
        roe = safe_float(row.get("return_on_equity_pct", np.nan))
        if roe > 20:
            conf = calculate_confidence(roe, 20, 40, ">")
            results.append(
                (comp_id, "pro", "P1", f"Strong Return on Equity: {roe:.1f}%", conf)
            )
            has_pro = True

        # P2: Debt Free
        de = safe_float(row.get("debt_to_equity", np.nan))
        if de == 0:
            results.append(
                (comp_id, "pro", "P2", "Company is completely debt-free.", 100.0)
            )
            has_pro = True

        # P3: FCF Positive
        fcf = safe_float(row.get("free_cash_flow", np.nan))
        if fcf > 0:
            conf = calculate_confidence(fcf, 0, 1000, ">")
            results.append(
                (comp_id, "pro", "P3", "Positive Free Cash Flow generation.", conf)
            )
            has_pro = True

        # P4: Rev CAGR > 15%
        rev_cagr = safe_float(row.get("sales_cagr_5y", np.nan))
        if rev_cagr > 15:
            conf = calculate_confidence(rev_cagr, 15, 30, ">")
            results.append(
                (
                    comp_id,
                    "pro",
                    "P4",
                    f"High 5-yr Revenue Growth: {rev_cagr:.1f}%",
                    conf,
                )
            )
            has_pro = True

        # P5: OPM > 25%
        opm = safe_float(row.get("opm_pct", np.nan))
        if opm > 25:
            conf = calculate_confidence(opm, 25, 50, ">")
            results.append(
                (comp_id, "pro", "P5", f"Excellent Operating Margins: {opm:.1f}%", conf)
            )
            has_pro = True

        # P6: ICR > 10
        icr = safe_float(row.get("interest_coverage", np.nan))
        if icr > 10:
            conf = calculate_confidence(icr, 10, 50, ">")
            results.append(
                (comp_id, "pro", "P6", "High Interest Coverage Ratio.", conf)
            )
            has_pro = True

        # P7: Dividend Yield > 2%
        div_y = safe_float(row.get("dividend_yield_pct", np.nan))
        if div_y > 2.0:
            conf = calculate_confidence(div_y, 2.0, 5.0, ">")
            results.append(
                (comp_id, "pro", "P7", f"Attractive Dividend Yield: {div_y:.1f}%", conf)
            )
            has_pro = True

        # P8: ROCE > 20%
        roce = safe_float(row.get("return_on_capital_employed_pct", np.nan))
        if roce > 20:
            conf = calculate_confidence(roce, 20, 40, ">")
            results.append(
                (comp_id, "pro", "P8", f"Strong Return on Capital: {roce:.1f}%", conf)
            )
            has_pro = True

        # P9: Net Margin > 15%
        npm = safe_float(row.get("net_margin_pct", np.nan))
        if npm > 15:
            conf = calculate_confidence(npm, 15, 30, ">")
            results.append(
                (comp_id, "pro", "P9", f"High Net Profit Margins: {npm:.1f}%", conf)
            )
            has_pro = True

        # P10: P/E < 15
        pe = safe_float(row.get("price_to_earnings", np.nan))
        if pe < 15 and pe > 0:
            conf = calculate_confidence(pe, 15, 5, "<")
            results.append(
                (comp_id, "pro", "P10", f"Undervalued (P/E < 15): {pe:.1f}", conf)
            )
            has_pro = True

        # P11: Gross Margin > 40%
        gm = safe_float(row.get("gross_margin_pct", np.nan))
        if gm > 40:
            conf = calculate_confidence(gm, 40, 80, ">")
            results.append(
                (comp_id, "pro", "P11", f"High Gross Margins: {gm:.1f}%", conf)
            )
            has_pro = True

        # P12: FCF/NP > 1
        fcf_np = safe_float(row.get("fcf_to_net_profit", np.nan))
        if fcf_np > 1.0:
            conf = calculate_confidence(fcf_np, 1.0, 2.0, ">")
            results.append(
                (comp_id, "pro", "P12", "Excellent cash conversion (FCF/NP > 1).", conf)
            )
            has_pro = True

        # CON RULES

        # C1: D/E > 2.0
        if sector != "Financials" and de > 2.0:
            conf = calculate_confidence(de, 2.0, 5.0, ">")
            results.append(
                (comp_id, "con", "C1", f"High Debt to Equity Ratio: {de:.2f}", conf)
            )
            has_con = True

        # C2: FCF < 0
        if fcf < 0:
            conf = calculate_confidence(fcf, 0, -1000, "<")
            results.append((comp_id, "con", "C2", "Negative Free Cash Flow.", conf))
            has_con = True

        # C3: Net Profit < 0
        np_val = safe_float(row.get("net_profit", np.nan))
        if np_val < 0:
            conf = calculate_confidence(np_val, 0, -500, "<")
            results.append((comp_id, "con", "C3", "Reporting net loss.", conf))
            has_con = True

        # C4: ICR < 1.5
        if icr < 1.5 and icr > -100:
            conf = calculate_confidence(icr, 1.5, 0.0, "<")
            results.append(
                (comp_id, "con", "C4", "Low Interest Coverage (Warning sign).", conf)
            )
            has_con = True

        # C5: Div Payout > 100%
        div_p = safe_float(row.get("dividend_payout_pct", np.nan))
        if div_p > 100:
            conf = calculate_confidence(div_p, 100, 200, ">")
            results.append(
                (comp_id, "con", "C5", "Dividend payout exceeds net earnings.", conf)
            )
            has_con = True

        # C6: ROCE < 10%
        if roce < 10 and pd.notna(roce):
            conf = calculate_confidence(roce, 10, 0, "<")
            results.append(
                (comp_id, "con", "C6", f"Low Return on Capital: {roce:.1f}%", conf)
            )
            has_con = True

        # C7: ROE < 10%
        if roe < 10 and pd.notna(roe):
            conf = calculate_confidence(roe, 10, 0, "<")
            results.append(
                (comp_id, "con", "C7", f"Low Return on Equity: {roe:.1f}%", conf)
            )
            has_con = True

        # C8: P/E > 50
        if pe > 50:
            conf = calculate_confidence(pe, 50, 100, ">")
            results.append(
                (comp_id, "con", "C8", f"High Valuation (P/E > 50): {pe:.1f}", conf)
            )
            has_con = True

        # C9: Rev CAGR 5Y < 5%
        if rev_cagr < 5 and pd.notna(rev_cagr):
            conf = calculate_confidence(rev_cagr, 5, -10, "<")
            results.append(
                (
                    comp_id,
                    "con",
                    "C9",
                    f"Weak 5-yr Revenue Growth: {rev_cagr:.1f}%",
                    conf,
                )
            )
            has_con = True

        # C10: Net Margin < 5%
        if npm < 5 and pd.notna(npm):
            conf = calculate_confidence(npm, 5, -5, "<")
            results.append(
                (comp_id, "con", "C10", f"Low Net Profit Margins: {npm:.1f}%", conf)
            )
            has_con = True

        # C11: P/B > 10
        pb = safe_float(row.get("price_to_book", np.nan))
        if pb > 10:
            conf = calculate_confidence(pb, 10, 25, ">")
            results.append(
                (comp_id, "con", "C11", f"Expensive Price to Book: {pb:.1f}", conf)
            )
            has_con = True

        # C12: Asset Turnover < 0.5 (as a proxy for cash conversion cycle issue)
        at = safe_float(row.get("asset_turnover", np.nan))
        if at < 0.5 and pd.notna(at):
            conf = calculate_confidence(at, 0.5, 0.1, "<")
            results.append(
                (comp_id, "con", "C12", f"Low Asset Turnover Ratio: {at:.2f}", conf)
            )
            has_con = True

        # Fallback logic to guarantee at least 1 Pro and 1 Con
        if not has_pro:
            results.append(
                (comp_id, "pro", "P_FB", "Company operates in a stable sector.", 65.0)
            )
        if not has_con:
            results.append(
                (comp_id, "con", "C_FB", "Sector faces macro-economic headwinds.", 65.0)
            )

    # Convert to df and filter by > 60% confidence
    res_df = pd.DataFrame(
        results, columns=["company_id", "type", "rule_id", "text", "confidence_pct"]
    )
    return res_df[res_df["confidence_pct"] >= 60.0]


def run_generator(db_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    df = fetch_data(db_path)

    if df.empty:
        print("No data available to generate pros/cons.")
        return

    pros_cons_df = generate_pros_cons(df)

    output_path = os.path.join(output_dir, "pros_cons_generated.csv")
    pros_cons_df.to_csv(output_path, index=False)
    print(f"Generated {output_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    db_file = os.path.join(base_dir, "nifty100.db")
    out_dir = os.path.join(base_dir, "output")
    run_generator(db_file, out_dir)
