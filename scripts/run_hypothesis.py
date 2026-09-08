import asyncio
import json

from app.agents.hypothesis.agent import HypothesisAgent
from app.agents.hypothesis.models import HypothesisResult
from app.agents.hypothesis.prompts import build_hypothesis_prompt
from app.llm.provider import get_investigation_llm


INVESTIGATION_RESULT = {
    "incident_id": "INC-1042",
    "service": "order-service",
    "summary": (
        "Order service experienced elevated latency "
        "and error rate."
    ),
    "timeline": [
        "10:02 - deployment completed",
        "10:05 - latency started increasing",
        "10:06 - error rate exceeded threshold",
    ],
    "evidence": [
        "Redis connection utilization exceeded 80%",
        "Redis timeout exceptions increased",
        "Redis dependency latency increased",
        "Application CPU remained normal",
        "Incident started shortly after deployment",
    ],
    "correlated_signals": [
        "Redis latency",
        "Redis timeout rate",
        "Order-service latency",
        "Error rate",
    ],
    "recent_changes": [
        "order-service deployment at 10:02",
    ],
}


async def main():

    llm = get_investigation_llm()

    structured_llm = llm.with_structured_output(
        HypothesisResult,
    )

    reasoning_chain = (
        build_hypothesis_prompt()
        | structured_llm
    )

    agent = HypothesisAgent(
        reasoning_chain=reasoning_chain
    )

    result = await agent.generate(
        INVESTIGATION_RESULT
    )

    print("\n=== HYPOTHESIS RESULT ===\n")

    print(
        json.dumps(
            result.model_dump(),
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())