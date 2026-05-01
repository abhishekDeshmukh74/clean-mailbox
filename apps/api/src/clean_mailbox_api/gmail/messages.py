from __future__ import annotations

from typing import Any


def list_recent(service: Any, limit: int) -> list[dict[str, Any]]:
    """List up to `limit` most-recent messages with headers + snippet only.

    Never fetches full bodies; never deletes anything.
    """
    if limit <= 0:
        return []
    resp = (
        service.users()
        .messages()
        .list(userId="me", maxResults=limit, q="in:inbox")
        .execute()
    )
    ids = [m["id"] for m in resp.get("messages", [])]
    out: list[dict[str, Any]] = []
    for mid in ids:
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=mid,
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            )
            .execute()
        )
        headers = {
            h["name"].lower(): h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }
        out.append(
            {
                "id": msg["id"],
                "threadId": msg.get("threadId", ""),
                "snippet": msg.get("snippet", ""),
                "labelIds": msg.get("labelIds", []),
                "from": headers.get("from", ""),
                "subject": headers.get("subject", ""),
                "date": headers.get("date", ""),
            }
        )
    return out
