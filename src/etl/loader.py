import pandas as pd
import sqlite3
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_actual_data():
    """
    Reads actual Screener.in Excel files from data/raw/, applies conditional 
    skiprows formatting, normalizes columns, and loads them into nifty100.db.
    """
    # 1. Define Paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_data_dir = base_dir / "data" / "raw"
    supporting_dir = raw_data_dir / "supporting_dataset"
    db_path = base_dir / "db" / "nifty100.db"
    
    # Create DB folder if not exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 2. Configuration Map: Table Name -> (File Path, Skiprows)
    file_mapping = {
        # Root Files (Require skiprows=1 because of Metadata row)
        "companies": (raw_data_dir / "companies.xlsx", 1),
        "analysis": (raw_data_dir / "analysis.xlsx", 1),
        "balance_sheet": (raw_data_dir / "balancesheet.xlsx", 1),
        "cash_flow": (raw_data_dir / "cashflow.xlsx", 1),
        "documents": (raw_data_dir / "documents.xlsx", 1),
        "profit_and_loss": (raw_data_dir / "profitandloss.xlsx", 1),
        "pros_and_cons": (raw_data_dir / "prosandcons.xlsx", 1),
        
        # Supporting Dataset (Clean format, no skiprows needed)
        "financial_ratios": (supporting_dir / "financial_ratios.xlsx", 0),
        "market_cap": (supporting_dir / "market_cap.xlsx", 0),
        "peer_groups": (supporting_dir / "peer_groups.xlsx", 0),
        "sectors": (supporting_dir / "sectors.xlsx", 0),
        "stock_prices": (supporting_dir / "stock_prices.xlsx", 0),
    }

    logging.info("Starting Data Swapping Phase ETL Pipeline...")
    
    # 3. Connect to SQLite DB
    conn = sqlite3.connect(db_path)

    # 4. Iterate, Extract, Transform, and Load (ETL)
    for table_name, (file_path, skip) in file_mapping.items():
        if not file_path.exists():
            logging.warning(f"File missing, skipping: {file_path}")
            continue
            
        logging.info(f"Processing {file_path.name} -> Table: '{table_name}'")
        
        try:
            # EXTRACT
            df = pd.read_excel(file_path, skiprows=skip)
            
            # TRANSFORM (Normalize Headers)
            # Example: Changes 'Year' to 'year', removes leading/trailing spaces
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            # LOAD
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            logging.info(f"✅ Loaded {len(df)} rows into '{table_name}'.")
            
        except Exception as e:
            logging.error(f"❌ Error processing {file_path.name}: {e}")

    conn.close()
    logging.info("🚀 ETL Process Complete! Real data is now mapped to nifty100.db.")

if __name__ == "__main__":
    load_actual_data()