"""Tests for CAP-1: cases/expense/load_seed.py.

Covers the story's stated success bar -- tables matching CSV columns,
row counts matching the source CSVs, and byte-identical output across
two runs -- nothing about tool behavior (that's Story 2+).
"""

import hashlib
import importlib.util
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = REPO_ROOT / "cases" / "expense"
SEED_DIR = CASE_DIR / "seed"

spec = importlib.util.spec_from_file_location("expense_load_seed", CASE_DIR / "load_seed.py")
expense_load_seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(expense_load_seed)

load = expense_load_seed.load
TABLES = expense_load_seed.TABLES


def _csv_header_and_row_count(table: str) -> tuple[list[str], int]:
    lines = (SEED_DIR / f"{table}.csv").read_text(encoding="utf-8").splitlines()
    return lines[0].split(","), len(lines) - 1


def test_creates_one_table_per_csv_with_matching_columns(tmp_path):
    db_path = load(db_path=tmp_path / "expense.db", seed_dir=SEED_DIR)

    conn = sqlite3.connect(db_path)
    try:
        for table in TABLES:
            expected_header, _ = _csv_header_and_row_count(table)
            actual_columns = [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')]
            assert actual_columns == expected_header
    finally:
        conn.close()


def test_row_counts_match_source_csvs(tmp_path):
    db_path = load(db_path=tmp_path / "expense.db", seed_dir=SEED_DIR)

    conn = sqlite3.connect(db_path)
    try:
        for table in TABLES:
            _, expected_count = _csv_header_and_row_count(table)
            actual_count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            assert actual_count == expected_count
    finally:
        conn.close()


def test_known_row_round_trips(tmp_path):
    db_path = load(db_path=tmp_path / "expense.db", seed_dir=SEED_DIR)

    conn = sqlite3.connect(db_path)
    try:
        employee_id = conn.execute(
            'SELECT employee_id FROM "claims" WHERE claim_id = ?', ("CL-2001",)
        ).fetchone()[0]
        assert employee_id == "E-101"

        level, city = conn.execute(
            'SELECT level, city FROM "employees" WHERE employee_id = ?', ("E-101",)
        ).fetchone()
        assert (level, city) == ("L2", "Toronto")

        limit_cad = conn.execute(
            'SELECT limit_cad FROM "limits" WHERE level = ? AND city = ? AND category = ?',
            ("L1", "Toronto", "meals"),
        ).fetchone()[0]
        assert limit_cad == 60  # inferred as INTEGER, not the string "60"
    finally:
        conn.close()


def test_double_load_produces_byte_identical_database(tmp_path):
    first = load(db_path=tmp_path / "run1.db", seed_dir=SEED_DIR)
    second = load(db_path=tmp_path / "run2.db", seed_dir=SEED_DIR)

    assert hashlib.sha256(first.read_bytes()).hexdigest() == hashlib.sha256(second.read_bytes()).hexdigest()

    # Same guarantee reloading over the *same* path, which is the real CLI usage.
    same_path = tmp_path / "reload.db"
    load(db_path=same_path, seed_dir=SEED_DIR)
    first_hash = hashlib.sha256(same_path.read_bytes()).hexdigest()
    load(db_path=same_path, seed_dir=SEED_DIR)
    second_hash = hashlib.sha256(same_path.read_bytes()).hexdigest()
    assert first_hash == second_hash
