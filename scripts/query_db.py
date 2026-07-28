import sqlite3

c = sqlite3.connect("nifty100.db")
print(
    "Screener count:",
    c.execute(
        "SELECT COUNT(*) FROM financial_ratios "
        "WHERE return_on_equity_pct > 15 AND debt_to_equity < 1"
    ).fetchone()[0],
)
print(
    "Financial sectors:",
    c.execute(
        "SELECT DISTINCT sector FROM companies "
        "WHERE sector LIKE '%Bank%' OR sector LIKE '%Finance%' OR sector LIKE '%NBFC%'"
    ).fetchall(),
)
print(
    "Source compare sample:",
    c.execute(
        """
        SELECT fr.company_id, fr.year, fr.return_on_equity_pct, sr.roe_pct,
               fr.return_on_capital_employed_pct, sr.roce_pct
        FROM financial_ratios fr
        JOIN source_ratios sr ON sr.company_id = fr.company_id AND sr.year = fr.year
        WHERE fr.return_on_equity_pct IS NOT NULL AND sr.roe_pct IS NOT NULL
        LIMIT 5
        """
    ).fetchall(),
)
