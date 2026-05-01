from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from ..gmail.client import get_service
from ..gmail.labels import list_user_labels
from ..store.user_settings import load_label_settings, save_label_settings
from .me import require_session

router = APIRouter(tags=["settings"])


@router.get("/settings/labels")
def get_labels(sess: dict = Depends(require_session)) -> dict:
    return load_label_settings(sess["sub"])


@router.put("/settings/labels")
def put_labels(
    body: dict = Body(...),
    sess: dict = Depends(require_session),
) -> dict:
    try:
        return save_label_settings(sess["sub"], body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/settings/gmail-labels")
def get_gmail_labels(sess: dict = Depends(require_session)) -> dict:
    """Return the user's existing Gmail user-created labels (read-only)."""
    try:
        service = get_service(sess["sub"])
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"labels": list_user_labels(service)}
