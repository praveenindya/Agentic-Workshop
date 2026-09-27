"""Tests for cases/expense's MCP tools (mcp/expense_server.py).

Each test builds a fresh, isolated database via load_seed.load() and points
the server module at it via monkeypatch, so these tests never depend on
(or pollute) a real cases/expense/expense.db. Grows one story at a time:
this file starts with CAP-2/CAP-3 (Story 1.2); later stories append their
own tool's tests here rather than spinning up a second test module for the
same server.
"""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = REPO_ROOT / "cases" / "expense" / "seed"


def _load_module(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


load_seed = _load_module("expense_load_seed", "cases/expense/load_seed.py")
expense_server = _load_module("expense_server_under_test", "mcp/expense_server.py")


@pytest.fixture
def db(tmp_path, monkeypatch):
    db_path = load_seed.load(db_path=tmp_path / "expense.db", seed_dir=SEED_DIR)
    monkeypatch.setattr(expense_server, "DB_PATH", db_path)
    return db_path


def test_get_claim_returns_employee_and_full_line_items(db):
    claim = expense_server.get_claim("CL-2001")

    assert claim["employee_id"] == "E-101"
    assert len(claim["line_items"]) == 4
    categories = {item["category"] for item in claim["line_items"]}
    assert categories == {"flight", "hotel", "meals", "ground"}
    # every line item field should be present, not a trimmed-down projection
    assert set(claim["line_items"][0].keys()) == {
        "line_id", "claim_id", "date", "city", "category", "merchant",
        "amount", "has_receipt", "description",
    }


def test_get_claim_unknown_id_raises(db):
    with pytest.raises(ValueError):
        expense_server.get_claim("CL-9999")


def test_get_employee_returns_level_and_city(db):
    employee = expense_server.get_employee("E-101")

    assert employee["level"] == "L2"
    assert employee["city"] == "Toronto"


def test_get_employee_unknown_id_raises(db):
    with pytest.raises(ValueError):
        expense_server.get_employee("E-999")
