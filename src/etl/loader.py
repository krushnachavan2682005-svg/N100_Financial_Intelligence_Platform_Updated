"""Load the standardized surrogate CSV dataset into the N100 SQLite database.

Run from the repository root with ``python src/etl/loader.py``. The loader is
safe to re-run: source rows are upserted using their primary keys rather than
duplicated.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "nifty100.db"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"
SOURCE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "n100_kaggle_top92_clean"
    / "standardized_tables"
)
AUDIT_PATH = PROJECT_ROOT / "output" / "load_audit.csv"

LOAD_PLAN = (
    ("companies", "companies.csv"),
    ("profitandloss", "profitandloss.csv"),
    ("balancesheet", "balancesheet.csv"),
    ("cashflow", "cashflow.csv"),
    ("source_ratios", "source_ratios.csv"),
)


def _quote_identifier(identifier: str) -> str:
    """Quote a SQLite identifier after it has been sourced from schema/CSV."""
    return '"' + identifier.replace('"', '""') + '"'


def _table_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    return [row[1] for row in connection.execute(f"PRAGMA table_info({_quote_identifier(table_name)})")]


def _primary_key_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    columns = connection.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    return [row[1] for row in sorted(columns, key=lambda row: row[5]) if row[5] > 0]


def _read_source(csv_path: Path, table_name: str, connection: sqlite3.Connection) -> pd.DataFrame:
    """Read one CSV and reject source columns that do not belong to its table."""
    frame = pd.read_csv(csv_path)
    table_columns = _table_columns(connection, table_name)
    unexpected = sorted(set(frame.columns) - set(table_columns))
    if unexpected:
        raise ValueError(
            f"{csv_path.name} contains columns not defined on {table_name}: {', '.join(unexpected)}"
        )
    return frame


def _upsert_dataframe(connection: sqlite3.Connection, table_name: str, frame: pd.DataFrame) -> int:
    """Insert or update one source DataFrame using the table's declared primary key."""
    if frame.empty:
        return 0

    columns = list(frame.columns)
    primary_key = _primary_key_columns(connection, table_name)
    if not primary_key:
        raise ValueError(f"{table_name} has no primary key; cannot safely upsert")
    if missing_keys := set(primary_key) - set(columns):
        raise ValueError(f"{table_name} source is missing primary-key columns: {', '.join(sorted(missing_keys))}")

    quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    conflict_columns = ", ".join(_quote_identifier(column) for column in primary_key)
    update_columns = [column for column in columns if column not in primary_key]
    if update_columns:
        updates = ", ".join(
            f"{_quote_identifier(column)} = excluded.{_quote_identifier(column)}" for column in update_columns
        )
        conflict_action = f"DO UPDATE SET {updates}"
    else:
        conflict_action = "DO NOTHING"

    statement = (
        f"INSERT INTO {_quote_identifier(table_name)} ({quoted_columns}) VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_columns}) {conflict_action}"
    )
    values: list[tuple[Any, ...]] = [
        tuple(None if pd.isna(value) else value for value in row)
        for row in frame.itertuples(index=False, name=None)
    ]
    connection.executemany(statement, values)
    return len(values)


def _write_audit(rows: list[dict[str, Any]]) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["table_name", "rows_loaded", "status", "message"]).to_csv(
        AUDIT_PATH, index=False, quoting=csv.QUOTE_MINIMAL
    )


def load_standardized_data() -> Path:
    """Initialise the database, transactionally load the five CSVs, and audit it."""
    audit_rows: list[dict[str, Any]] = []
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    missing_files = [filename for _, filename in LOAD_PLAN if not (SOURCE_DIRECTORY / filename).is_file()]
    if missing_files:
        raise FileNotFoundError(f"Missing standardized CSV file(s): {', '.join(missing_files)}")

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON;")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

        with connection:
            for table_name, filename in LOAD_PLAN:
                try:
                    frame = _read_source(SOURCE_DIRECTORY / filename, table_name, connection)
                    row_count = _upsert_dataframe(connection, table_name, frame)
                    audit_rows.append(
                        {
                            "table_name": table_name,
                            "rows_loaded": row_count,
                            "status": "SUCCESS",
                            "message": f"Loaded {filename} via primary-key upsert.",
                        }
                    )
                except Exception as exc:
                    audit_rows.append(
                        {
                            "table_name": table_name,
                            "rows_loaded": 0,
                            "status": "FAILED",
                            "message": str(exc),
                        }
                    )
                    raise

            foreign_key_violations = connection.execute("PRAGMA foreign_key_check;").fetchall()
            if foreign_key_violations:
                audit_rows.append(
                    {
                        "table_name": "foreign_key_check",
                        "rows_loaded": len(foreign_key_violations),
                        "status": "CRITICAL",
                        "message": f"Foreign-key violations: {foreign_key_violations}",
                    }
                )
                raise RuntimeError("Foreign-key integrity check failed")

            audit_rows.append(
                {
                    "table_name": "foreign_key_check",
                    "rows_loaded": 0,
                    "status": "SUCCESS",
                    "message": "No foreign-key violations found.",
                }
            )
    except Exception:
        _write_audit(audit_rows)
        raise
    else:
        _write_audit(audit_rows)
        return AUDIT_PATH
    finally:
        connection.close()


def main() -> None:
    audit_path = load_standardized_data()
    print(f"Database loaded successfully: {DATABASE_PATH}")
    print(f"Audit report written to: {audit_path}")


if __name__ == "__main__":
    main()
