"""LangChain reviewer agent for expense claims, over mcp/expense_server.py's tools.

Story 2.1 (this file's first version): scaffold only -- provider switch,
MCP tool wiring, entry point. No POLICY.md precedence logic yet (that's
Story 2.2); whatever the model decides with the tools comes back as-is,
unvalidated.
"""

import os
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXPENSE_SERVER_PATH = REPO_ROOT / "mcp" / "expense_server.py"

SYSTEM_PROMPT = (
    "You are an expense claim reviewer. Given a claim_id, look up the claim "
    "and its line items, the employee's level and city, and the policy "
    "limits that apply, then decide every line item (approve, flag, or "
    "reject) and record each decision with the deciding clause."
)


def build_model():
    """Return a chat model per PROVIDER/MODEL env vars, same switch as the triage agent."""
    provider = os.environ.get("PROVIDER", "gemini")
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=os.environ.get("MODEL", "openai/gpt-oss-120b"))
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model=os.environ.get("MODEL", "gemini-3.8-flash"))


def _expense_mcp_connection() -> dict:
    """Stdio connection spec for mcp/expense_server.py, run with the current interpreter."""
    return {
        "expense": {
            "command": sys.executable,
            "args": [str(EXPENSE_SERVER_PATH)],
            "transport": "stdio",
        }
    }


async def get_expense_tools() -> list:
    """Fetch the live tool list from mcp/expense_server.py over stdio."""
    client = MultiServerMCPClient(_expense_mcp_connection())
    return await client.get_tools()


async def build_agent():
    """A create_agent instance wired to mcp/expense_server.py's tools."""
    tools = await get_expense_tools()
    return create_agent(model=build_model(), tools=tools, system_prompt=SYSTEM_PROMPT)


async def review_claim(claim_id: str) -> str:
    """Run the agent against one claim. Story 1: returns the model's final message, unvalidated."""
    agent = await build_agent()
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": f"Review claim {claim_id} and decide every line item."}]}
    )
    return result["messages"][-1].content
