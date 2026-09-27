"""Review one expense claim with the agent and print the result.

Usage: uv run python cases/expense/review_claim.py CL-2001
"""

import asyncio
import sys

import mlflow
from dotenv import load_dotenv


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: uv run python cases/expense/review_claim.py <claim_id>")
    claim_id = sys.argv[1]

    load_dotenv()
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("expense-reviewer")
    mlflow.langchain.autolog()

    from agent import review_claim

    with mlflow.start_span(name="review_claim", span_type="AGENT") as span:
        span.set_inputs({"claim_id": claim_id})
        result = asyncio.run(review_claim(claim_id))
        span.set_outputs(result)
    print(result)


if __name__ == "__main__":
    main()
