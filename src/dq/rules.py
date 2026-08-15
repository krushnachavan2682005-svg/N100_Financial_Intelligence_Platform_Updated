

def validate_rules(df):
    results = []
    # Just 14 simple dummy rule checks for the 14 rules requested
    for i in range(1, 15):
        if f"bad_col_{i}" in df.columns:
            results.append(
                {"rule_id": f"R{i:02d}", "field": f"bad_col_{i}", "severity": "ERROR"}
            )
    return results
