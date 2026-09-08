from typing import TypedDict

from .agent import HypothesisAgent
from .models import HypothesisResult


class HypothesisState(TypedDict, total=False):
    investigation: dict
    hypotheses: HypothesisResult
    error: str


async def hypothesis_node(
    state: HypothesisState,
) -> HypothesisState:

    agent = HypothesisAgent()

    result = await agent.run(
        state["investigation"]
    )

    return {
        **state,
        "hypotheses": result,
    }


def build_hypothesis_graph():

    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(HypothesisState)

    graph.add_node(
        "generate_hypotheses",
        hypothesis_node,
    )

    graph.add_edge(
        START,
        "generate_hypotheses",
    )

    graph.add_edge(
        "generate_hypotheses",
        END,
    )

    return graph.compile()