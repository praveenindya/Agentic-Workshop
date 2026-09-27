"""Load cases/expense/seed/*.csv into a local SQLite database (CAP-1).

Usage:
    uv run python cases/expense/load_seed.py

Each CSV becomes one table, named after the file, with columns matching
the CSV header. The database is rebuilt from scratch every run -- any
existing file at DB_PATH is deleted first -- so running this twice in a
row produces a byte-for-byte identical database. No decisions, policy
logic, or business rules run here; this only makes the seed data queryable.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
SEED_DIR = CASE_DIR / "seed"
DB_PATH = CASE_DIR / "expense.db"

# One table per seed CSV. Order doesn't affect correctness, just readability.
TABLES = ["claims", "employees", "limits", "line_items"]


def _read_rows(csv_path: Path) -> tuple[list[str], list[list[str]]]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        return header, list(reader)


def _column_type(values: list[str]) -> str:
    """Infer a SQLite column type from every value in that column.

    Falls back to TEXT unless *every* value parses as the same numeric
    type, so mixed or empty columns stay safely TEXT.
    """
    if not values or any(v == "" for v in values):
        return "TEXT"
    if all(_parses_as(v, int) for v in values):
        return "INTEGER"
    if all(_parses_as(v, float) for v in values):
        return "REAL"
    return "TEXT"


def _parses_as(value: str, kind: type) -> bool:
    try:
        kind(value)
        return True
    except ValueError:
        return False


def _convert(value: str, col_type: str) -> int | float | str:
    if col_type == "INTEGER":
        return int(value)
    if col_type == "REAL":
        return float(value)
    return value


def _load_table(conn: sqlite3.Connection, table: str, seed_dir: Path) -> None:
    header, rows = _read_rows(seed_dir / f"{table}.csv")
    col_types = [_column_type(column) for column in zip(*rows)] if rows else ["TEXT"] * len(header)

    columns_sql = ", ".join(f'"{name}" {ctype}' for name, ctype in zip(header, col_types))
    conn.execute(f'CREATE TABLE "{table}" ({columns_sql})')

    quoted_cols = ", ".join(f'"{name}"' for name in header)
    placeholders = ", ".join("?" for _ in header)
    typed_rows = [
        [_convert(value, ctype) for value, ctype in zip(row, col_types)] for row in rows
    ]
    conn.executemany(f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({placeholders})', typed_rows)


def load(db_path: Path = DB_PATH, seed_dir: Path = SEED_DIR) -> Path:
    """(Re)build db_path from the CSVs in seed_dir, deterministically."""
    db_path.unlink(missing_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        for table in TABLES:
            _load_table(conn, table, seed_dir)
        conn.commit()
    finally:
        conn.close()
    return db_path


if __name__ == "__main__":
    result_path = load()
    print(f"Loaded {SEED_DIR} -> {result_path}")
