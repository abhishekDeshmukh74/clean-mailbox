from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config import get_settings


def _user_data_path(sub: str) -> Path:
    settings = get_settings()
    safe = "".join(c for c in sub if c.isalnum() or c in "-_")
    return settings.cache_dir / "data" / f"{safe}.json"


def load_user_data(sub: str) -> dict[str, Any]:
    path = _user_data_path(sub)
    if not path.exists():
        return {"emails": [], "summary": None, "last_run_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"emails": [], "summary": None, "last_run_at": None}


def save_user_data(sub: str, data: dict[str, Any]) -> None:
    path = _user_data_path(sub)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
