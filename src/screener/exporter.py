import pandas as pd
import os


def export_screener_results(
    presets_results: dict, output_path: str, presets_criteria: dict
):
    """
    Export screener results to Excel with conditional formatting.
    presets_results: dict of {preset_name: DataFrame}
    presets_criteria: dict of {preset_name: criteria_dict}
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        for preset_name, df in presets_results.items():
            if df.empty:
                # Still create an empty sheet
                export_df = pd.DataFrame(columns=["ticker", "composite_quality_score"])
            else:
                cols = df.columns.tolist()
                # Ensure composite_quality_score and ticker are at the front
                front_cols = [
                    "ticker",
                    "company_name",
                    "sector",
                    "composite_quality_score",
                ]
                front_cols = [c for c in front_cols if c in cols]
                other_cols = [c for c in cols if c not in front_cols]

                # Take up to 20 columns
                final_cols = (front_cols + other_cols)[:20]
                export_df = df[final_cols]
                if "composite_quality_score" in export_df.columns:
                    export_df = export_df.sort_values(
                        "composite_quality_score", ascending=False
                    )

            # Excel sheet names can be max 31 chars and no special chars like []/*?:\
            sheet_name = str(preset_name).replace("/", "_").replace(":", "_")[:31]
            export_df.to_excel(writer, sheet_name=sheet_name, index=False)

            if df.empty:
                continue

            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            green_format = workbook.add_format(
                {"bg_color": "#C6EFCE", "font_color": "#006100"}
            )
            red_format = workbook.add_format(
                {"bg_color": "#FFC7CE", "font_color": "#9C0006"}
            )

            criteria = presets_criteria.get(preset_name, {})

            col_map = {
                "roe_min": ("roe", ">="),
                "d_e_max": ("debt_to_equity", "<="),
                "fcf_min": ("fcf", ">="),
                "revenue_cagr_5yr_min": ("revenue_cagr_5yr", ">="),
                "pe_max": ("pe_ratio", "<="),
                "pb_max": ("pb_ratio", "<="),
                "dividend_yield_min": ("dividend_yield", ">="),
                "pat_cagr_5yr_min": ("pat_cagr_5yr", ">="),
                "dividend_payout_max": ("dividend_payout", "<="),
                "sales_min": ("sales", ">="),
                "revenue_cagr_3yr_min": ("revenue_cagr_3yr", ">="),
            }

            for crit_key, val in criteria.items():
                if crit_key in col_map:
                    col_name, op = col_map[crit_key]
                    if col_name in export_df.columns:
                        col_idx = export_df.columns.get_loc(col_name)
                        if col_idx < 26:
                            col_letter = chr(ord("A") + col_idx)
                        else:
                            # Not handling > 26 cols since we capped at 20
                            continue

                        # Apply green format
                        worksheet.conditional_format(
                            f"{col_letter}2:{col_letter}{len(export_df)+1}",
                            {
                                "type": "cell",
                                "criteria": op,
                                "value": val,
                                "format": green_format,
                            },
                        )

                        # Apply red format
                        inverse_op = "<" if op == ">=" else ">"
                        worksheet.conditional_format(
                            f"{col_letter}2:{col_letter}{len(export_df)+1}",
                            {
                                "type": "cell",
                                "criteria": inverse_op,
                                "value": val,
                                "format": red_format,
                            },
                        )
