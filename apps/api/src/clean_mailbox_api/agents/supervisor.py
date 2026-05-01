from __future__ import annotations

from .state import AgentState


def supervisor_node(state: AgentState) -> AgentState:
    """Decide the next step. Skips steps already completed.

    Uses key presence (not truthiness) so empty results from a step still
    count as completed and we don't loop forever on an empty inbox.
    """
    if len(state.get("errors", [])) > 5:
        return {"next": "end"}
    if "classifications" not in state:
        return {"next": "classify"}
    if "summaries" not in state or "digest" not in state:
        return {"next": "summarize"}
    if "applied_labels" not in state:
        return {"next": "label"}
    return {"next": "end"}


def route(state: AgentState) -> str:
    return state.get("next", "end")
