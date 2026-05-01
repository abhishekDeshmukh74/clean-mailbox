from __future__ import annotations

from typing import Any, TypedDict

# Static defaults — kept here for backwards compatibility. The real categories
# used at runtime come from per-user settings injected into AgentState as
# ``label_config`` (see ``store/user_settings.py``).
from ..config import CATEGORIES  # re-export


class EmailRecord(TypedDict, total=False):
    id: str
    threadId: str
    from_: str
    subject: str
    date: str
    snippet: str
    labelIds: list[str]
    # Enrichments produced by agents
    category: str
    category_reason: str
    summary: str
    applied_label_names: list[str]


class AgentState(TypedDict, total=False):
    sub: str
    emails: list[dict[str, Any]]
    label_config: dict[str, Any]  # per-user prefix/categories
    classifications: dict[str, dict[str, Any]]  # email_id -> {category, reason}
    summaries: dict[str, str]  # email_id -> summary line
    label_plan: dict[str, list[str]]  # email_id -> [label_names]
    applied_labels: dict[str, list[str]]  # email_id -> [label_names]
    digest: str
    next: str
    errors: list[str]
