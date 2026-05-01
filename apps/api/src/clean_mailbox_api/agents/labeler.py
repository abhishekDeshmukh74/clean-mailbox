"""Labeler agent. ONLY adds labels — never removes, archives, or deletes."""

from __future__ import annotations

import logging

from ..gmail.client import get_service
from ..gmail.labels import add_labels, ensure_label
from ..store.user_settings import (
    category_label,
    default_label_settings,
)
from .state import AgentState

logger = logging.getLogger(__name__)


def _plan_for_email(eid: str, state: AgentState) -> list[str]:
    cfg = state.get("label_config") or default_label_settings()
    cat = state.get("classifications", {}).get(eid, {}).get("category")
    names: list[str] = []
    if cat:
        names.append(category_label(cfg, cat))
    return [n for n in names if n]


def labeler_node(state: AgentState) -> AgentState:
    emails = state.get("emails", [])
    sub = state.get("sub")
    if not emails or not sub:
        return {"label_plan": {}, "applied_labels": {}}

    plan: dict[str, list[str]] = {e["id"]: _plan_for_email(e["id"], state) for e in emails}
    applied: dict[str, list[str]] = {}

    try:
        service = get_service(sub)
    except Exception as exc:
        logger.warning("labeler: cannot get gmail service: %s", exc)
        return {
            "label_plan": plan,
            "applied_labels": {},
            "errors": list(state.get("errors", [])) + [f"labeler:{exc}"],
        }

    # Resolve label ids once
    name_to_id: dict[str, str] = {}
    for names in plan.values():
        for name in names:
            if name not in name_to_id:
                try:
                    name_to_id[name] = ensure_label(service, name)
                except Exception as exc:  # pragma: no cover
                    logger.warning("ensure_label(%s) failed: %s", name, exc)

    for eid, names in plan.items():
        ids = [name_to_id[n] for n in names if n in name_to_id]
        if not ids:
            applied[eid] = []
            continue
        try:
            add_labels(service, eid, ids)
            applied[eid] = names
        except Exception as exc:  # pragma: no cover
            logger.warning("add_labels(%s) failed: %s", eid, exc)
            applied[eid] = []

    return {"label_plan": plan, "applied_labels": applied}
