"""Tests for cases/expense/agent.py (Story 2.1: scaffold only).

Two kinds of test here:
  - fast/deterministic: build_model()'s provider switch, no network call --
    constructing a chat model client doesn't call its API.
  - one live integration test that actually spawns mcp/expense_server.py
    over stdio and fetches its tool list -- no LLM involved, so it's free
    and deterministic, but it does need cases/expense/expense.db to exist,
    which this test builds via load_seed first.

No live-LLM test here by default (see test_review_claim_live, skipped
unless EXPENSE_LIVE_TESTS=1) -- calling a real model on every `pytest` run
would be slow, flaky, and cost money without an explicit opt-in.
"""

import asyncio
import importlib.util
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = REPO_ROOT / "cases" / "expense"
SEED_DIR = CASE_DIR / "seed"


def _load_module(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


load_seed = _load_module("expense_load_seed_for_agent_test", "cases/expense/load_seed.py")
agent = _load_module("expense_agent_under_test", "cases/expense/agent.py")


def test_build_model_defaults_to_gemini(monkeypatch):
    monkeypatch.delenv("PROVIDER", raising=False)
    monkeypatch.delenv("MODEL", raising=False)

    model = agent.build_model()

    assert type(model).__name__ == "ChatGoogleGenerativeAI"
    assert model.model == "gemini-3.8-flash"


def test_build_model_respects_model_env_override(monkeypatch):
    monkeypatch.delenv("PROVIDER", raising=False)
    monkeypatch.setenv("MODEL", "gemini-2.5-flash")

    model = agent.build_model()

    assert model.model == "gemini-2.5-flash"


def test_build_model_groq_provider(monkeypatch):
    monkeypatch.setenv("PROVIDER", "groq")
    monkeypatch.delenv("MODEL", raising=False)

    model = agent.build_model()

    assert type(model).__name__ == "ChatGroq"
    assert model.model_name == "openai/gpt-oss-120b"


def test_build_model_groq_respects_model_env_override(monkeypatch):
    monkeypatch.setenv("PROVIDER", "groq")
    monkeypatch.setenv("MODEL", "llama-3.3-70b-versatile")

    model = agent.build_model()

    assert model.model_name == "llama-3.3-70b-versatile"


def test_get_expense_tools_exposes_all_five_epic1_tools():
    # The subprocess spawned over stdio reads the real, fixed expense.db
    # path (mcp/expense_server.py doesn't take a DB override), so make
    # sure it exists first -- load_seed is idempotent and gitignored.
    load_seed.load()

    tools = asyncio.run(agent.get_expense_tools())

    tool_names = {tool.name for tool in tools}
    assert tool_names == {
        "get_claim",
        "get_employee",
        "get_policy_limits",
        "record_decision",
        "get_employee_line_items",
    }


@pytest.mark.skipif(
    os.environ.get("EXPENSE_LIVE_TESTS") != "1",
    reason="live LLM call -- opt in with EXPENSE_LIVE_TESTS=1 (needs GEMINI_API_KEY or GROQ_API_KEY)",
)
def test_review_claim_live_smoke():
    load_seed.load()

    result = asyncio.run(agent.review_claim("CL-2001"))

    assert isinstance(result, str)
    assert result.strip() != ""
