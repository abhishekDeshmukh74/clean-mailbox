from __future__ import annotations

# Per-user in-memory state, e.g. "is a run currently in flight?".
_running: dict[str, bool] = {}


def is_running(sub: str) -> bool:
    return _running.get(sub, False)


def set_running(sub: str, value: bool) -> None:
    _running[sub] = value
