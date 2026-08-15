import os
import sqlite3
import pandas as pd

def get_pattern_label(cfo, cfi, cff):
    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return "Unknown"
        
    # Map signs
    s_cfo = "+" if cfo > 0 else "-"
    s_cfi = "+" if cfi > 0 else "-"
    s_cff = "+" if cff > 0 else "-"
    
    mapping = {
        ("+", "-", "-"): "Consistent Compounder",
        ("+", "-", "+"): "Growth Phase",
        ("+", "+", "-"): "Divestment & Deleveraging",
        ("+", "+", "+"): "Divestment & Expansion",
        ("-", "-", "+"): "Start-up / Cash Burn",
        ("-", "-", "-"): "Liquidation",
        ("-", "+", "-"): "Distress & Debt Repayment",
        ("-", "+", "+"): "Severe Distress"
    }
    
    return mapping.get((s_cfo, s_cfi, s_cff), "Unknown")

def generate_capital_report(db_path, output_dir):
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        c.company_id, c.company_name, c.sector,
        cf.year,
        cf.cash_from_operating_activity as cfo,
        cf.cash_from_investing_activity as cfi,
        cf.cash_from_financing_activity as cff
    FROM companies c
    JOIN cashflow cf ON c.company_id = cf.company_id
    ORDER BY c.company_id, cf.year
    """
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        conn.close()
        return
    conn.close()
    
    if df.empty:
        print("No cashflow data.")
        return
        
    df['pattern'] = df.apply(lambda row: get_pattern_label(row['cfo'], row['cfi'], row['cff']), axis=1)
    
    latest_year = df['year'].max()
    
    transitions = []
    latest_patterns = {}
    
    for comp_id, group in df.groupby('company_id'):
        group = group.sort_values('year')
        
        if len(group) < 2:
            continue
            
        latest = group.iloc[-1]
        prev = group.iloc[-2]
        
        comp_name = latest['company_name']
        sector = latest['sector']
        
        prev_pattern = prev['pattern']
        curr_pattern = latest['pattern']
        change_type = "Maintained" if prev_pattern == curr_pattern else "Changed"
        
        transitions.append({
            'company_id': comp_id,
            'company_name': comp_name,
            'sector': sector,
            'previous_year': prev['year'],
            'previous_pattern': prev_pattern,
            'latest_year': latest['year'],
            'latest_pattern': curr_pattern,
            'change_type': change_type
        })
        
        latest_patterns[comp_id] = curr_pattern

    # Generate pattern_changes.csv
    transitions_df = pd.DataFrame(transitions)
    if not transitions_df.empty:
        changes_path = os.path.join(output_dir, 'pattern_changes.csv')
        transitions_df.to_csv(changes_path, index=False)
        print(f"Generated {changes_path}")
        
    # Update cashflow_intelligence.xlsx
    excel_path = os.path.join(output_dir, 'cashflow_intelligence.xlsx')
    if os.path.exists(excel_path):
        cf_intel = pd.read_excel(excel_path)
        cf_intel['capital_allocation_label'] = cf_intel['company_id'].map(latest_patterns).fillna("Unknown")
        cf_intel.to_excel(excel_path, index=False)
        print(f"Updated {excel_path} with capital allocation labels")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    db_file = os.path.join(base_dir, 'nifty100.db')
    out_dir = os.path.join(base_dir, 'output')
    generate_capital_report(db_file, out_dir)
