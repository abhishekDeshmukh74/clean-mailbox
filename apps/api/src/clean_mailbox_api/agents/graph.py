from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterator

from langgraph.graph import END, StateGraph

from ..store.user_settings import load_label_settings
from .classifier import classifier_node
from .labeler import labeler_node
from .state import AgentState
from .summarizer import summarizer_node
from .supervisor import route, supervisor_node


@lru_cache
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("classify", classifier_node)
    g.add_node("summarize", summarizer_node)
    g.add_node("label", labeler_node)

    g.set_entry_point("supervisor")
    g.add_conditional_edges(
        "supervisor",
        route,
        {
            "classify": "classify",
            "summarize": "summarize",
            "label": "label",
            "end": END,
        },
    )
    for node in ("classify", "summarize", "label"):
        g.add_edge(node, "supervisor")

    return g.compile()


def _initial_state(sub: str, emails: list[dict]) -> AgentState:
    return {
        "sub": sub,
        "emails": emails,
        "label_config": load_label_settings(sub),
        "errors": [],
    }


def run_agents(sub: str, emails: list[dict]) -> AgentState:
    graph = build_graph()
    return graph.invoke(_initial_state(sub, emails))


def stream_agents(sub: str, emails: list[dict]) -> Iterator[dict[str, Any]]:
    """Yield per-node update chunks from LangGraph."""
    graph = build_graph()
    for chunk in graph.stream(_initial_state(sub, emails)):
        yield chunk
