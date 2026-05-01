from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import get_settings
from ..store.cache import load_user_data
from .me import require_session

router = APIRouter(tags=["emails"])


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _is_today(value: str | None) -> bool:
    dt = _parse_date(value)
    if dt is None:
        return False
    today = datetime.now(timezone.utc).date()
    return dt.astimezone(timezone.utc).date() == today


@router.get("/emails")
def list_emails(
    limit: int = Query(default=50, ge=1),
    sess: dict = Depends(require_session),
) -> list[dict]:
    settings = get_settings()
    if limit > settings.max_fetch_limit:
        raise HTTPException(
            status_code=400,
            detail=f"limit must be <= {settings.max_fetch_limit}",
        )
    data = load_user_data(sess["sub"])
    emails = data.get("emails", [])
    return emails[:limit]


@router.get("/summary")
def summary(sess: dict = Depends(require_session)) -> dict:
    data = load_user_data(sess["sub"])
    emails = data.get("emails", [])
    cat_counts = Counter(e.get("category") or "Other" for e in emails)
    saved = data.get("summary") or {}

    today_emails = [e for e in emails if _is_today(e.get("date"))]
    today_items = [
        {
            "id": e.get("id"),
            "from": e.get("from", ""),
            "subject": e.get("subject", ""),
            "category": e.get("category"),
            "summary": e.get("summary") or (e.get("snippet") or "")[:160],
        }
        for e in today_emails
    ]

    return {
        "totals": {"emails": len(emails)},
        "byCategory": dict(cat_counts),
        "digest": saved.get("digest", ""),
        "lastRunAt": data.get("last_run_at"),
        "today": {"count": len(today_items), "items": today_items},
    }
