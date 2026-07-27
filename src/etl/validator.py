"""Data-quality validation for the standardized N100 surrogate dataset.

The validator deliberately reads standardized files only.  It never mutates
source data; its sole artifact is an auditable validation-failures CSV.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd


FAILURE_COLUMNS = [
    "rule_id",
    "severity",
    "table_name",
    "company_id",
    "year",
    "column_name",
    "message",
]

ANNUAL_TABLES = ("profitandloss", "balancesheet", "cashflow", "source_ratios")
SOURCE_FILENAMES = {
    "companies": "companies.csv",
    "profitandloss": "profitandloss.csv",
    "balancesheet": "balancesheet.csv",
    "cashflow": "cashflow.csv",
    "source_ratios": "source_ratios.csv",
}


class DataValidator:
    """Run Sprint 1 data-quality checks over standardized financial tables.

    Args:
        data_dir: Directory containing the five standardized CSV files.  If
            omitted, the project surrogate-data location is used.
        tables: Optional mapping of table name to DataFrame.  Supplying this
            makes the class straightforward to use in unit tests or another
            ETL process without touching disk.
        output_path: Destination for the validation failures CSV.
    """

    skipped_rules = {
        "DQ-09": "Skipped: dividend_payout_pct is entirely null in the surrogate dataset.",
        "DQ-10": "Skipped: the surrogate dataset has no URL column to validate.",
    }

    def __init__(
        self,
        data_dir: str | Path | None = None,
        tables: Mapping[str, pd.DataFrame] | None = None,
        output_path: str | Path | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.data_dir = Path(data_dir) if data_dir else project_root / "data/raw/n100_kaggle_top92_clean/standardized_tables"
        self.output_path = Path(output_path) if output_path else project_root / "output/validation_failures.csv"
        self.tables = {name: frame.copy() for name, frame in tables.items()} if tables else {}
        self._failures: list[dict[str, object]] = []

    def load_data(self) -> dict[str, pd.DataFrame]:
        """Load the standardized source files when DataFrames were not supplied."""
        if self.tables:
            self._assert_required_tables()
            return self.tables

        for table_name, filename in SOURCE_FILENAMES.items():
            file_path = self.data_dir / filename
            if not file_path.is_file():
                raise FileNotFoundError(f"Required standardized file not found: {file_path}")
            self.tables[table_name] = pd.read_csv(file_path)
        return self.tables

    def validate(self) -> pd.DataFrame:
        """Execute implemented DQ checks and return failures in the fixed contract."""
        self.load_data()
        self._failures = []

        self.check_dq01_pk_uniqueness()
        self.check_dq02_composite_key_uniqueness()
        self.check_dq03_foreign_key_integrity()
        self.check_dq04_bs_balance()
        self.check_dq05_opm_cross_check()
        self.check_dq06_positive_sales()
        self.check_dq07_net_cash_reconciliation()
        self.check_dq11_eps_sign_consistency()

        result = pd.DataFrame(self._failures, columns=FAILURE_COLUMNS)
        if not result.empty:
            result["year"] = pd.array(result["year"], dtype="Int64")
        return result

    def write_failures(self, failures: pd.DataFrame | None = None) -> pd.DataFrame:
        """Write validation results, creating only the configured output directory."""
        result = self.validate() if failures is None else failures
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(self.output_path, index=False)
        return result

    def check_dq01_pk_uniqueness(self) -> None:
        """DQ-01 CRITICAL: company identifiers must be unique."""
        companies = self.tables["companies"]
        self._require_columns("companies", {"company_id"})
        duplicates = companies[companies.duplicated("company_id", keep=False)]
        for _, row in duplicates.iterrows():
            self._add_failure("DQ-01", "CRITICAL", "companies", row["company_id"], None, "company_id", "Duplicate company_id in companies table.")

    def check_dq02_composite_key_uniqueness(self) -> None:
        """DQ-02 CRITICAL: annual records must be unique by company and year."""
        for table_name in ANNUAL_TABLES:
            table = self.tables[table_name]
            self._require_columns(table_name, {"company_id", "year"})
            duplicates = table[table.duplicated(["company_id", "year"], keep=False)]
            for _, row in duplicates.iterrows():
                self._add_failure("DQ-02", "CRITICAL", table_name, row["company_id"], row["year"], "company_id,year", "Duplicate (company_id, year) composite key.")

    def check_dq03_foreign_key_integrity(self) -> None:
        """DQ-03 CRITICAL: annual company IDs must be present in companies."""
        companies = self.tables["companies"]
        self._require_columns("companies", {"company_id"})
        valid_ids = set(companies["company_id"].dropna())
        for table_name in ANNUAL_TABLES:
            table = self.tables[table_name]
            self._require_columns(table_name, {"company_id", "year"})
            orphans = table[~table["company_id"].isin(valid_ids)]
            for _, row in orphans.iterrows():
                self._add_failure("DQ-03", "CRITICAL", table_name, row["company_id"], row["year"], "company_id", "company_id is absent from companies table.")

    def check_dq04_bs_balance(self) -> None:
        """DQ-04 WARNING: balance-sheet totals must agree exactly."""
        table = self.tables["balancesheet"]
        self._require_columns("balancesheet", {"company_id", "year", "total_assets", "total_liabilities"})
        invalid = table[table["total_assets"] != table["total_liabilities"]]
        for _, row in invalid.iterrows():
            difference = row["total_assets"] - row["total_liabilities"]
            self._add_failure("DQ-04", "WARNING", "balancesheet", row["company_id"], row["year"], "total_assets,total_liabilities", f"Balance sheet does not balance; assets minus liabilities = {difference}.")

    def check_dq05_opm_cross_check(self, tolerance: float = 0.6) -> None:
        """DQ-05 WARNING: OPM must agree within the source-rounding tolerance."""
        table = self.tables["profitandloss"]
        self._require_columns("profitandloss", {"company_id", "year", "sales", "operating_profit", "opm_pct"})
        eligible = table[table["sales"].notna() & (table["sales"] != 0)].copy()
        eligible["calculated_opm"] = eligible["operating_profit"] / eligible["sales"] * 100
        invalid = eligible[(eligible["opm_pct"] - eligible["calculated_opm"]).abs() > tolerance]
        for _, row in invalid.iterrows():
            self._add_failure("DQ-05", "WARNING", "profitandloss", row["company_id"], row["year"], "opm_pct", f"Reported OPM {row['opm_pct']:.4f}% differs from calculated OPM {row['calculated_opm']:.4f}% by more than {tolerance:.1f} percentage points.")

    def check_dq06_positive_sales(self) -> None:
        """DQ-06 WARNING: sales must be strictly positive."""
        table = self.tables["profitandloss"]
        self._require_columns("profitandloss", {"company_id", "year", "sales"})
        invalid = table[table["sales"].notna() & (table["sales"] <= 0)]
        for _, row in invalid.iterrows():
            self._add_failure("DQ-06", "WARNING", "profitandloss", row["company_id"], row["year"], "sales", f"Sales must be positive; found {row['sales']}.")

    def check_dq07_net_cash_reconciliation(self, tolerance: float = 1.0) -> None:
        """DQ-07 WARNING: cash-flow components must reconcile within ±1 crore."""
        table = self.tables["cashflow"]
        required = {"company_id", "year", "cash_from_operating_activity", "cash_from_investing_activity", "cash_from_financing_activity", "net_cash_flow"}
        self._require_columns("cashflow", required)
        calculated = table["cash_from_operating_activity"] + table["cash_from_investing_activity"] + table["cash_from_financing_activity"]
        invalid = table[(calculated - table["net_cash_flow"]).abs() > tolerance].copy()
        invalid["difference"] = calculated.loc[invalid.index] - invalid["net_cash_flow"]
        for _, row in invalid.iterrows():
            self._add_failure("DQ-07", "WARNING", "cashflow", row["company_id"], row["year"], "net_cash_flow", f"Cash-flow components differ from net_cash_flow by {row['difference']}; tolerance is ±{tolerance:g} crore.")

    def check_dq11_eps_sign_consistency(self) -> None:
        """DQ-11 WARNING: net profit and EPS must have the same mathematical sign."""
        table = self.tables["profitandloss"]
        self._require_columns("profitandloss", {"company_id", "year", "net_profit", "eps"})
        eligible = table[table["net_profit"].notna() & table["eps"].notna()]
        invalid = eligible[np.sign(eligible["net_profit"]) != np.sign(eligible["eps"])]
        for _, row in invalid.iterrows():
            self._add_failure("DQ-11", "WARNING", "profitandloss", row["company_id"], row["year"], "net_profit,eps", f"net_profit ({row['net_profit']}) and eps ({row['eps']}) have different signs.")

    def _assert_required_tables(self) -> None:
        missing = set(SOURCE_FILENAMES) - set(self.tables)
        if missing:
            raise KeyError(f"Missing required tables: {', '.join(sorted(missing))}")

    def _require_columns(self, table_name: str, required: set[str]) -> None:
        missing = required - set(self.tables[table_name].columns)
        if missing:
            raise KeyError(f"{table_name} is missing required columns: {', '.join(sorted(missing))}")

    def _add_failure(self, rule_id: str, severity: str, table_name: str, company_id: object, year: object, column_name: str, message: str) -> None:
        self._failures.append({"rule_id": rule_id, "severity": severity, "table_name": table_name, "company_id": company_id, "year": year, "column_name": column_name, "message": message})


def main() -> None:
    """Run validation for the default standardized data directory."""
    validator = DataValidator()
    failures = validator.write_failures()
    print(f"Validation complete: {len(failures)} failure(s) written to {validator.output_path}")
    for rule_id, reason in validator.skipped_rules.items():
        print(f"{rule_id}: {reason}")


if __name__ == "__main__":
    main()
