"""Gmail label operations.

SAFETY: This module deliberately exposes ONLY additive operations:
  - ensure_label: idempotently creates a user label
  - add_labels:   adds labels to a message via users.messages.modify

There is intentionally NO function for removing labels, archiving, trashing,
or deleting messages. The `add_labels` function asserts that no removal or
trash payload ever reaches the Gmail API.
"""

from __future__ import annotations

from typing import Any

# In-process cache of label_name -> label_id, keyed per service object id.
_LABEL_CACHE: dict[int, dict[str, str]] = {}


def _labels_map(service: Any) -> dict[str, str]:
    key = id(service)
    if key not in _LABEL_CACHE:
        resp = service.users().labels().list(userId="me").execute()
        _LABEL_CACHE[key] = {
            label["name"]: label["id"] for label in resp.get("labels", [])
        }
    return _LABEL_CACHE[key]


def ensure_label(service: Any, name: str) -> str:
    """Return id for the named label, creating it if it doesn't exist."""
    cache = _labels_map(service)
    if name in cache:
        return cache[name]
    body = {
        "name": name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    created = service.users().labels().create(userId="me", body=body).execute()
    cache[name] = created["id"]
    return created["id"]


def list_user_labels(service: Any) -> list[dict[str, str]]:
    """Return all Gmail labels (user-created + system).

    Read-only. Each entry: ``{"id": ..., "name": ..., "type": "user"|"system"}``.
    """
    resp = service.users().labels().list(userId="me").execute()
    return [
        {
            "id": label["id"],
            "name": label["name"],
            "type": label.get("type", "user"),
        }
        for label in resp.get("labels", [])
    ]


def add_labels(service: Any, message_id: str, label_ids: list[str]) -> dict[str, Any]:
    """Add labels to a message. Adds only — never removes, archives, or trashes."""
    if not label_ids:
        return {"id": message_id, "labelIds": []}
    body: dict[str, Any] = {"addLabelIds": list(label_ids)}

    # Hard guards: never let removal/trash sneak through.
    assert "removeLabelIds" not in body, "removeLabelIds is forbidden"
    assert "trash" not in body, "trash is forbidden"
    assert "delete" not in body, "delete is forbidden"

    return (
        service.users()
        .messages()
        .modify(userId="me", id=message_id, body=body)
        .execute()
    )
