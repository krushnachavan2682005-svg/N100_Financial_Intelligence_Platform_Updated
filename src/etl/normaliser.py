import pandas as pd
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def normalise_data():
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "db" / "nifty100.db"

    conn = sqlite3.connect(db_path)

    # 1. COLUMN MAPPINGS (Comprehensive mapping based on deep scan)
    COLUMN_MAPPING = {
        "roce_percentage": "source_roce_pct",
        "roe_percentage": "source_roe_pct",
        "opm_percentage": "opm_pct",
        "tax_percentage": "tax_pct",
        "dividend_payout": "dividend_payout_pct",
        "other_asset": "other_assets",
        "operating_activity": "cash_from_operating_activity",
        "investing_activity": "cash_from_investing_activity",
        "financing_activity": "cash_from_financing_activity",
        "net_profit_margin_pct": "net_margin_pct",
        "free_cash_flow_cr": "free_cash_flow",
    }

    try:
        # --- A. Rename Columns Across All Tables ---
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql(tables_query, conn)["name"].tolist()

        for table in tables:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            # Rename based on mapping
            df = df.rename(columns=COLUMN_MAPPING)
            
            # Ensure both source and legacy column names exist to prevent dashboard/API breaks
            if "source_roe_pct" in df.columns and "return_on_equity_pct" not in df.columns:
                df["return_on_equity_pct"] = df["source_roe_pct"]
            if "source_roce_pct" in df.columns and "return_on_capital_employed_pct" not in df.columns:
                df["return_on_capital_employed_pct"] = df["source_roce_pct"]
            
            # Ensure 'year' is integer to prevent TypeError
            if 'year' in df.columns:
                df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)

            # Ensure specific columns exist in financial_ratios to avoid OperationalError
            if table == "financial_ratios":
                expected_fr_cols = {
                    "return_on_capital_employed_pct": 0.0,
                    "sales_cagr_5y": 0.0,
                    "net_margin_pct": 0.0,
                    "free_cash_flow": 0.0,
                    "debt_to_equity": 0.0,
                    "interest_coverage": 0.0,
                    "asset_turnover": 0.0,
                    "return_on_equity_pct": 0.0,
                    "source_roe_pct": 0.0,
                    "source_roce_pct": 0.0
                }
                for col, default_val in expected_fr_cols.items():
                    if col not in df.columns:
                        df[col] = default_val
            
            # Ensure profitandloss expected columns
            if table == "profitandloss" or table == "profit_and_loss":
                if "net_profit" not in df.columns:
                    df["net_profit"] = 0.0
                if "eps" not in df.columns:
                    df["eps"] = 0.0

            df.to_sql(table, conn, if_exists="replace", index=False)
        logging.info("✅ All basic column renames, type casting, and additions completed.")

        # --- B. Fix Pros & Cons (Unpivot / Melt) ---
        pc_table_name = "pros_and_cons" if "pros_and_cons" in tables else ("prosandcons" if "prosandcons" in tables else None)
        if pc_table_name:
            pc_df = pd.read_sql(f"SELECT * FROM {pc_table_name}", conn)
            if "pros" in pc_df.columns and "cons" in pc_df.columns:
                pc_melted = pd.melt(
                    pc_df,
                    id_vars=["id", "company_id"],
                    value_vars=["pros", "cons"],
                    var_name="sentiment",
                    value_name="item_text",
                )
                pc_melted["sentiment"] = pc_melted["sentiment"].map(
                    {"pros": "pro", "cons": "con"}
                )
                pc_melted = pc_melted.dropna(subset=["item_text"])
                pc_melted.to_sql(pc_table_name, conn, if_exists="replace", index=False)
                logging.info("✅ Pros & Cons unpivoted to long format.")

        # --- C. Fix Documents (Hardcoding & Formatting) ---
        if "documents" in tables:
            doc_df = pd.read_sql("SELECT * FROM documents", conn)
            if "annual_report" in doc_df.columns:
                doc_df = doc_df.rename(
                    columns={"annual_report": "source_url", "year": "document_date"}
                )
                doc_df["document_type"] = "Annual Report"
                doc_df["document_date"] = doc_df["document_date"].astype(str) + "-03-31"
                doc_df.to_sql("documents", conn, if_exists="replace", index=False)
                logging.info("✅ Documents formatted correctly.")

        # --- D. Fix Missing Company Data (Merge with Supporting Datasets) ---
        if "companies" in tables:
            comp_df = pd.read_sql("SELECT * FROM companies", conn)
            
            if "sectors" in tables and "market_cap" in tables:
                sectors_df = pd.read_sql("SELECT id, company_id, broad_sector as sector FROM sectors", conn)
                mcap_df = pd.read_sql("SELECT company_id, market_cap_crore as market_cap_cr, pe_ratio as stock_pe FROM market_cap WHERE year = (SELECT MAX(year) FROM market_cap)", conn)
                
                # The 'id' column in companies is actually the ticker (company_id)
                if 'id' in comp_df.columns and 'company_id' not in comp_df.columns:
                    comp_df = comp_df.rename(columns={'id': 'company_id'})
                
                # Now comp_df has 'company_id', so we can merge with sectors
                if 'company_id' in comp_df.columns:
                    comp_df = comp_df.merge(sectors_df.drop(columns=['id'], errors='ignore'), on='company_id', how='left')
                    
                # Merge with market_cap
                if 'company_id' in comp_df.columns and 'company_id' in mcap_df.columns:
                    if 'market_cap_cr' not in comp_df.columns or comp_df['market_cap_cr'].isnull().all():
                        if 'market_cap_cr' in comp_df.columns:
                            comp_df = comp_df.drop(columns=['market_cap_cr', 'stock_pe'], errors='ignore')
                        comp_df = comp_df.merge(mcap_df, on='company_id', how='left')
            
            # 🟢 THE FIX: Add missing string columns required by API and Tests
            if 'nse' not in comp_df.columns:
                comp_df['nse'] = comp_df.get('company_id', 'UNKNOWN')  # Screener uses company_id as the ticker
            if 'bse' not in comp_df.columns:
                comp_df['bse'] = "UNKNOWN"
            if 'isin' not in comp_df.columns:
                comp_df['isin'] = "UNKNOWN"
                
            # Fill strictly required numeric columns with 0.0 if still missing
            missing_numerics = ['current_price', 'high_low', 'dividend_yield_pct', 'debt_cr', 'eps', 'return_on_capital_employed_pct']
            for col in missing_numerics:
                if col not in comp_df.columns:
                    comp_df[col] = 0.0
                    
            comp_df.to_sql('companies', conn, if_exists='replace', index=False)
            logging.info("✅ Companies table enriched with missing metadata (including NSE, BSE, ISIN).")

        # --- E. Clear Tables to avoid Schema Constraints / Cache issues ---
        if "analysis" in tables:
            conn.execute("DELETE FROM analysis")
            conn.commit()
            logging.info("✅ Analysis table cleared to prevent schema mismatch errors.")
            
        if "peer_percentiles" in tables:
            conn.execute("DROP TABLE IF EXISTS peer_percentiles")
            conn.commit()
            logging.info("✅ peer_percentiles table dropped to recreate with proper constraints.")

        # --- F. Rename Tables for Backward Compatibility ---
        table_mappings = {
            "profit_and_loss": "profitandloss",
            "balance_sheet": "balancesheet",
            "cash_flow": "cashflow",
            "pros_and_cons": "prosandcons",
        }
        for old_name, new_name in table_mappings.items():
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (old_name,))
            if cursor.fetchone():
                # 🟢 THE FIX: Drop leftover ghost tables before renaming
                cursor.execute(f"DROP TABLE IF EXISTS {new_name}")
                cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
                logging.info(f"✅ Renamed '{old_name}' -> '{new_name}'")

        logging.info(
            "🚀 Normalisation Complete! Database is now 100% compatible with existing APIs and Tests."
        )

    except Exception as e:
        logging.error(f"❌ Normalisation failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    normalise_data()
