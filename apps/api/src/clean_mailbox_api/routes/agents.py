from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..agents.graph import stream_agents
from ..config import get_settings
from ..gmail.client import get_service
from ..gmail.messages import list_recent
from ..store.cache import load_user_data, save_user_data
from ..store.memory import is_running, set_running
from .me import require_session

router = APIRouter(tags=["agents"])


# Human-friendly labels for each LangGraph node.
NODE_LABELS = {
    "supervisor": "Routing",
    "classify": "Classifying emails",
    "summarize": "Summarizing & writing digest",
    "label": "Applying Gmail labels",
}


class RunRequest(BaseModel):
    limit: Optional[int] = Field(default=None, ge=1)


def _resolve_limit(limit: Optional[int]) -> int:
    settings = get_settings()
    n = limit or settings.default_fetch_limit
    if n > settings.max_fetch_limit:
        raise HTTPException(
            status_code=400,
            detail=f"limit must be <= {settings.max_fetch_limit}",
        )
    return n


def _merge(raw: list[dict], final: dict[str, Any]) -> list[dict]:
    cls = final.get("classifications", {}) or {}
    sumr = final.get("summaries", {}) or {}
    applied = final.get("applied_labels", {}) or {}

    out: list[dict] = []
    for e in raw:
        eid = e["id"]
        existing = e.get("labelIds", [])
        out.append(
            {
                "id": eid,
                "threadId": e.get("threadId", ""),
                "from": e.get("from", ""),
                "subject": e.get("subject", ""),
                "date": e.get("date", ""),
                "snippet": e.get("snippet", ""),
                "labels": list({*existing, *applied.get(eid, [])}),
                "summary": sumr.get(eid, ""),
                "category": cls.get(eid, {}).get("category"),
            }
        )
    return out


def _save_empty(sub: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    save_user_data(
        sub,
        {"emails": [], "summary": {"digest": "Inbox is empty."}, "last_run_at": now},
    )
    return {"processed": 0, "digest": "Inbox is empty.", "lastRunAt": now}


@router.post("/agents/run")
def run(body: RunRequest, sess: dict = Depends(require_session)) -> dict:
    sub = sess["sub"]
    limit = _resolve_limit(body.limit)

    if is_running(sub):
        raise HTTPException(status_code=409, detail="An agent run is already in progress")

    set_running(sub, True)
    try:
        try:
            service = get_service(sub)
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        raw = list_recent(service, limit)
        if not raw:
            return _save_empty(sub)

        # Aggregate streaming results into a single final state.
        final: dict[str, Any] = {}
        for chunk in stream_agents(sub, raw):
            for _node, update in chunk.items():
                if isinstance(update, dict):
                    final.update(update)

        enriched = _merge(raw, final)
        now = datetime.now(timezone.utc).isoformat()
        digest = final.get("digest", "")
        save_user_data(
            sub,
            {
                "emails": enriched,
                "summary": {"digest": digest},
                "last_run_at": now,
                "errors": final.get("errors", []),
            },
        )
        return {"processed": len(enriched), "digest": digest, "lastRunAt": now}
    finally:
        set_running(sub, False)


def _sse(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def _stream_run(sub: str, limit: int) -> Iterator[bytes]:
    if is_running(sub):
        yield _sse("error", {"message": "An agent run is already in progress"})
        return

    set_running(sub, True)
    try:
        yield _sse("step", {"node": "fetch", "label": "Fetching recent emails", "status": "started"})
        try:
            service = get_service(sub)
        except PermissionError as exc:
            yield _sse("error", {"message": str(exc)})
            return

        try:
            raw = list_recent(service, limit)
        except Exception as exc:  # pragma: no cover
            yield _sse("error", {"message": f"Gmail fetch failed: {exc}"})
            return

        yield _sse(
            "step",
            {"node": "fetch", "label": "Fetching recent emails", "status": "done", "count": len(raw)},
        )

        if not raw:
            result = _save_empty(sub)
            yield _sse("done", result)
            return

        final: dict[str, Any] = {}
        try:
            for chunk in stream_agents(sub, raw):
                for node, update in chunk.items():
                    label = NODE_LABELS.get(node, node)
                    if not isinstance(update, dict):
                        yield _sse("step", {"node": node, "label": label, "status": "done"})
                        continue
                    yield _sse("step", {"node": node, "label": label, "status": "started"})
                    final.update(update)
                    detail = _step_detail(node, update)
                    yield _sse(
                        "step",
                        {"node": node, "label": label, "status": "done", **detail},
                    )
        except Exception as exc:  # pragma: no cover
            yield _sse("error", {"message": f"Agent run failed: {exc}"})
            return

        enriched = _merge(raw, final)
        now = datetime.now(timezone.utc).isoformat()
        digest = final.get("digest", "")
        save_user_data(
            sub,
            {
                "emails": enriched,
                "summary": {"digest": digest},
                "last_run_at": now,
                "errors": final.get("errors", []),
            },
        )
        yield _sse(
            "done",
            {"processed": len(enriched), "digest": digest, "lastRunAt": now},
        )
    finally:
        set_running(sub, False)


def _step_detail(node: str, update: dict[str, Any]) -> dict[str, Any]:
    if node == "classify":
        return {"count": len(update.get("classifications", {}) or {})}
    if node == "summarize":
        digest = update.get("digest") or ""
        return {
            "count": len(update.get("summaries", {}) or {}),
            "digestPreview": digest[:120] + ("\u2026" if len(digest) > 120 else ""),
        }
    if node == "label":
        applied = update.get("applied_labels", {}) or {}
        total = sum(len(v) for v in applied.values())
        return {"messagesLabeled": len(applied), "labelsApplied": total}
    return {}


@router.post("/agents/run/stream")
def run_stream(body: RunRequest, sess: dict = Depends(require_session)) -> StreamingResponse:
    sub = sess["sub"]
    limit = _resolve_limit(body.limit)
    return StreamingResponse(
        _stream_run(sub, limit),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/agents/status")
def status(sess: dict = Depends(require_session)) -> dict:
    data = load_user_data(sess["sub"])
    return {
        "running": is_running(sess["sub"]),
        "lastRunAt": data.get("last_run_at"),
    }
