from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth.session import get_session, load_user_tokens

router = APIRouter(tags=["me"])


def require_session(request: Request) -> dict:
    sess = get_session(request)
    if not sess or not sess.get("sub"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sess


@router.get("/me")
def me(sess: dict = Depends(require_session)) -> dict:
    payload = load_user_tokens(sess["sub"]) or {}
    return {
        "email": payload.get("email") or sess.get("email"),
        "name": payload.get("name"),
        "picture": payload.get("picture"),
    }
