from __future__ import annotations

import logging
from typing import Any

from ..store.user_settings import category_names, default_label_settings
from .llm import chat_json
from .state import AgentState

logger = logging.getLogger(__name__)


def _build_system(cfg: dict[str, Any]) -> str:
    cats = cfg.get("categories", [])
    bullet = "\n".join(
        f"- {c['name']}" + (f": {c['description']}" if c.get("description") else "")
        for c in cats
    )
    names = ", ".join(c["name"] for c in cats)
    return (
        "You are an email triage classifier. Categorize each email into exactly one of "
        f"these categories:\n{bullet}\n"
        "Respond ONLY with a JSON array of objects: "
        '[{"id": "<email_id>", "category": "<one of the categories>", "reason": "<short reason>"}]. '
        f"Use only the provided id values. Allowed categories: {names}."
    )


def _email_brief(e: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": e["id"],
        "from": e.get("from", ""),
        "subject": e.get("subject", ""),
        "snippet": (e.get("snippet", "") or "")[:300],
    }


def classifier_node(state: AgentState) -> AgentState:
    emails = state.get("emails", [])
    if not emails:
        return {"classifications": {}}

    cfg = state.get("label_config") or default_label_settings()
    cats = category_names(cfg)
    if not cats:
        return {"classifications": {}}
    fallback = cats[-1]

    user = {
        "instruction": "Classify each email.",
        "categories": cats,
        "emails": [_email_brief(e) for e in emails],
    }

    try:
        result = chat_json(
            [
                {"role": "system", "content": _build_system(cfg)},
                {"role": "user", "content": str(user)},
            ]
        )
    except Exception as exc:
        logger.warning("classifier failed: %s", exc)
        return {
            "classifications": {e["id"]: {"category": fallback, "reason": "fallback"} for e in emails},
            "errors": list(state.get("errors", [])) + [f"classifier:{exc}"],
        }

    valid = set(cats)
    by_id: dict[str, dict[str, Any]] = {}
    if isinstance(result, list):
        for item in result:
            if not isinstance(item, dict):
                continue
            eid = str(item.get("id") or "")
            cat = str(item.get("category") or fallback)
            if cat not in valid:
                cat = fallback
            if eid:
                by_id[eid] = {"category": cat, "reason": item.get("reason", "")}

    for e in emails:
        by_id.setdefault(e["id"], {"category": fallback, "reason": "missing in LLM output"})

    return {"classifications": by_id}
