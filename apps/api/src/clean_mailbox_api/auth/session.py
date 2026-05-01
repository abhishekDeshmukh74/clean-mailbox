from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Request

from ..config import get_settings

SESSION_COOKIE = "cm_session"


def _fernet() -> Fernet:
    settings = get_settings()
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.session_secret.encode("utf-8")).digest()
    )
    return Fernet(key)


def encrypt(data: dict[str, Any]) -> str:
    return _fernet().encrypt(json.dumps(data).encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> dict[str, Any] | None:
    try:
        raw = _fernet().decrypt(token.encode("utf-8"))
    except (InvalidToken, ValueError):
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def get_session(request: Request) -> dict[str, Any] | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    return decrypt(token)


def user_token_path(sub: str) -> Path:
    settings = get_settings()
    safe = "".join(c for c in sub if c.isalnum() or c in "-_")
    return settings.cache_dir / "users" / f"{safe}.json"


def save_user_tokens(sub: str, payload: dict[str, Any]) -> None:
    path = user_token_path(sub)
    path.parent.mkdir(parents=True, exist_ok=True)
    encrypted = encrypt(payload)
    path.write_text(encrypted, encoding="utf-8")


def load_user_tokens(sub: str) -> dict[str, Any] | None:
    path = user_token_path(sub)
    if not path.exists():
        return None
    return decrypt(path.read_text(encoding="utf-8"))
