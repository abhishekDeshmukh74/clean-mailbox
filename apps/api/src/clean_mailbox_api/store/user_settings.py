"""Per-user label configuration: prefix and categories.

Stored as plain JSON (no secrets) in ``cache/data/<sub>.settings.json``.
Falls back to defaults from :mod:`clean_mailbox_api.config` for new users.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config import CATEGORIES, get_settings


def _safe_sub(sub: str) -> str:
    return "".join(c for c in sub if c.isalnum() or c in "-_")


def _settings_path(sub: str) -> Path:
    return get_settings().cache_dir / "data" / f"{_safe_sub(sub)}.settings.json"


def default_label_settings() -> dict[str, Any]:
    return {
        "prefix": "",
        "categorySubPrefix": "",
        "categories": [{"name": name, "description": ""} for name in CATEGORIES],
    }


def _coerce(raw: Any) -> dict[str, Any]:
    """Normalize a user-supplied or stored config to the canonical shape."""
    if not isinstance(raw, dict):
        return default_label_settings()

    out = default_label_settings()

    prefix = raw.get("prefix")
    if isinstance(prefix, str):
        out["prefix"] = prefix.strip().strip("/")

    sub = raw.get("categorySubPrefix")
    if isinstance(sub, str):
        out["categorySubPrefix"] = sub.strip().strip("/")

    items: list[dict[str, str]] = []
    seen: set[str] = set()
    value = raw.get("categories")
    if isinstance(value, list):
        for entry in value:
            if isinstance(entry, str):
                name, desc = entry.strip(), ""
            elif isinstance(entry, dict):
                name = str(entry.get("name", "")).strip()
                desc = str(entry.get("description", "") or "").strip()
            else:
                continue
            if not name or name in seen:
                continue
            seen.add(name)
            items.append({"name": name, "description": desc})
    if items:
        out["categories"] = items
    return out


def load_label_settings(sub: str) -> dict[str, Any]:
    path = _settings_path(sub)
    if not path.exists():
        return default_label_settings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_label_settings()
    return _coerce(raw)


def save_label_settings(sub: str, raw: Any) -> dict[str, Any]:
    cfg = _coerce(raw)
    if not cfg["categories"]:
        raise ValueError("At least one category is required.")
    path = _settings_path(sub)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return cfg


# ---------------------------------------------------------------------------
# Helpers used by agents
# ---------------------------------------------------------------------------


def _join(*parts: str) -> str:
    return "/".join(p for p in parts if p)


def category_label(cfg: dict[str, Any], category: str) -> str:
    return _join(cfg.get("prefix", ""), cfg.get("categorySubPrefix", ""), category)


def category_names(cfg: dict[str, Any]) -> list[str]:
    return [c["name"] for c in cfg.get("categories", [])]
