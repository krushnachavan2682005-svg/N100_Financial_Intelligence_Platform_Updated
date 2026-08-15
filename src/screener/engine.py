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

    if "roe_min" in criteria:
        filtered_df = filtered_df[filtered_df["roe"] >= criteria["roe_min"]]

    if "d_e_max" in criteria:
        if "sector" in filtered_df.columns:
            mask = (filtered_df["debt_to_equity"] <= criteria["d_e_max"]) | (
                filtered_df["sector"] == "Financials"
            )
            filtered_df = filtered_df[mask]
        else:
            filtered_df = filtered_df[
                filtered_df["debt_to_equity"] <= criteria["d_e_max"]
            ]

    if "fcf_min" in criteria:
        filtered_df = filtered_df[filtered_df["fcf"] >= criteria["fcf_min"]]

    if "revenue_cagr_5yr_min" in criteria:
        filtered_df = filtered_df[
            filtered_df["revenue_cagr_5yr"] >= criteria["revenue_cagr_5yr_min"]
        ]

    if "pat_cagr_5yr_min" in criteria:
        filtered_df = filtered_df[
            filtered_df["pat_cagr_5yr"] >= criteria["pat_cagr_5yr_min"]
        ]

    if "opm_min" in criteria:
        filtered_df = filtered_df[filtered_df["opm"] >= criteria["opm_min"]]

    if "pe_max" in criteria:
        filtered_df = filtered_df[filtered_df["pe_ratio"] <= criteria["pe_max"]]

    if "pb_max" in criteria:
        filtered_df = filtered_df[filtered_df["pb_ratio"] <= criteria["pb_max"]]

    if "dividend_yield_min" in criteria:
        filtered_df = filtered_df[
            filtered_df["dividend_yield"] >= criteria["dividend_yield_min"]
        ]

    if "icr_min" in criteria:

        def check_icr(icr_val):
            if pd.isna(icr_val) or str(icr_val).strip().lower() in [
                "debt free",
                "none",
                "",
            ]:
                return np.inf
            try:
                return float(icr_val)
            except ValueError:
                return -np.inf

        if "icr" in filtered_df.columns:
            icr_numeric = filtered_df["icr"].apply(check_icr)
            filtered_df = filtered_df[icr_numeric >= criteria["icr_min"]]

    if "market_cap_min" in criteria:
        filtered_df = filtered_df[
            filtered_df["market_cap"] >= criteria["market_cap_min"]
        ]

    if "net_profit_min" in criteria:
        filtered_df = filtered_df[
            filtered_df["net_profit"] >= criteria["net_profit_min"]
        ]

    if "eps_cagr_min" in criteria:
        filtered_df = filtered_df[filtered_df["eps_cagr"] >= criteria["eps_cagr_min"]]

    if "asset_turnover_min" in criteria:
        filtered_df = filtered_df[
            filtered_df["asset_turnover"] >= criteria["asset_turnover_min"]
        ]

    if "sales_min" in criteria:
        filtered_df = filtered_df[filtered_df["sales"] >= criteria["sales_min"]]

    if "dividend_payout_max" in criteria:
        if "dividend_payout" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["dividend_payout"] <= criteria["dividend_payout_max"]
            ]

    if "revenue_cagr_3yr_min" in criteria:
        if "revenue_cagr_3yr" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["revenue_cagr_3yr"] >= criteria["revenue_cagr_3yr_min"]
            ]

    if criteria.get("d_e_declining_yoy", False):
        if (
            "debt_to_equity" in filtered_df.columns
            and "debt_to_equity_prev" in filtered_df.columns
        ):
            filtered_df = filtered_df[
                filtered_df["debt_to_equity"] < filtered_df["debt_to_equity_prev"]
            ]

    if not filtered_df.empty:
        filtered_df = calculate_composite_score(filtered_df)
    else:
        filtered_df["composite_quality_score"] = 0.0

    if "composite_quality_score" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(
            by="composite_quality_score", ascending=False
        )
    elif "market_cap" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by="market_cap", ascending=False)
    elif len(filtered_df) > 0:
        filtered_df = filtered_df.sort_index()

    return filtered_df


def calculate_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    score_df = df.copy()

    def scale_metric(series, invert=False):
        s = pd.to_numeric(series, errors="coerce").fillna(0)
        if s.empty:
            return s
        p10 = s.quantile(0.10)
        p90 = s.quantile(0.90)

        if p10 == p90:
            return pd.Series(50.0, index=s.index)

        s_clip = s.clip(lower=p10, upper=p90)
        scaled = (s_clip - p10) / (p90 - p10) * 100

        if invert:
            scaled = 100 - scaled

        return scaled

    roe = score_df.get("roe", pd.Series(0, index=score_df.index))
    roce = score_df.get(
        "roce",
        score_df.get(
            "return_on_capital_employed_pct", pd.Series(0, index=score_df.index)
        ),
    )
    npm = score_df.get("net_margin_pct", pd.Series(0, index=score_df.index))

    fcf_cagr = score_df.get("fcf_cagr_5yr", pd.Series(0, index=score_df.index))
    cfo_pat = score_df.get(
        "cfo_to_net_profit",
        score_df.get("fcf_to_net_profit", pd.Series(0, index=score_df.index)),
    )
    fcf_pos = score_df.get("fcf", pd.Series(0, index=score_df.index)) > 0

    rev_cagr = score_df.get("revenue_cagr_5yr", pd.Series(0, index=score_df.index))
    pat_cagr = score_df.get("pat_cagr_5yr", pd.Series(0, index=score_df.index))

    de = score_df.get("debt_to_equity", pd.Series(0, index=score_df.index))
    icr = score_df.get(
        "icr", score_df.get("interest_coverage", pd.Series(0, index=score_df.index))
    )

    roe_score = scale_metric(roe)
    roce_score = scale_metric(roce)
    npm_score = scale_metric(npm)

    fcf_cagr_score = scale_metric(fcf_cagr)
    cfo_pat_score = scale_metric(cfo_pat)
    fcf_pos_score = fcf_pos.astype(float) * 100

    rev_cagr_score = scale_metric(rev_cagr)
    pat_cagr_score = scale_metric(pat_cagr)

    de_score = scale_metric(de, invert=True)

    icr_num = pd.to_numeric(
        icr.replace(["Debt Free", "None", ""], np.inf), errors="coerce"
    ).fillna(0)
    icr_num = icr_num.replace(np.inf, 1e6)
    icr_score = scale_metric(icr_num)

    profitability = roe_score * 0.15 + roce_score * 0.10 + npm_score * 0.10
    cash_quality = fcf_cagr_score * 0.15 + cfo_pat_score * 0.10 + fcf_pos_score * 0.05
    growth = rev_cagr_score * 0.10 + pat_cagr_score * 0.10
    leverage = de_score * 0.10 + icr_score * 0.05

    raw_composite = profitability + cash_quality + growth + leverage

    def sector_norm(group):
        g_min = group.min()
        g_max = group.max()
        if g_min == g_max:
            return pd.Series(50.0, index=group.index)
        return (group - g_min) / (g_max - g_min) * 100

    if "sector" in score_df.columns and len(score_df["sector"].dropna()) > 0:
        score_df["composite_quality_score"] = raw_composite.groupby(
            score_df["sector"], group_keys=False
        ).apply(sector_norm)
    else:
        score_df["composite_quality_score"] = sector_norm(raw_composite)

    return score_df


def load_presets(config_path: str = "config/screener_config.yaml") -> dict:
    """
    Load screener presets from a YAML configuration file.
    """
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config.get("presets", {})
