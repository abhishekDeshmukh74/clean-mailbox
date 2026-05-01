from __future__ import annotations

import logging
from collections import Counter

from .llm import chat, chat_json
from .state import AgentState

logger = logging.getLogger(__name__)

PER_EMAIL_SYSTEM = (
    "Summarize each email in one short sentence (max 20 words). "
    'Respond ONLY with a JSON array: [{"id":"<email_id>","summary":"..."}]. '
    "Use only the provided id values."
)

DIGEST_SYSTEM = (
    "You write a brief inbox digest (4-6 sentences) for a user, "
    "highlighting noteworthy categories and notable senders. "
    "Be concise, neutral, no greetings."
)


def summarizer_node(state: AgentState) -> AgentState:
    emails = state.get("emails", [])
    if not emails:
        return {"summaries": {}, "digest": ""}

    payload = {
        "emails": [
            {
                "id": e["id"],
                "from": e.get("from", ""),
                "subject": e.get("subject", ""),
                "snippet": (e.get("snippet", "") or "")[:400],
            }
            for e in emails
        ],
    }

    summaries: dict[str, str] = {}
    try:
        result = chat_json(
            [
                {"role": "system", "content": PER_EMAIL_SYSTEM},
                {"role": "user", "content": str(payload)},
            ]
        )
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict) and item.get("id"):
                    summaries[str(item["id"])] = str(item.get("summary", ""))
    except Exception as exc:
        logger.warning("summarizer per-email failed: %s", exc)
        state.setdefault("errors", []).append(f"summarizer:{exc}")

    for e in emails:
        summaries.setdefault(e["id"], (e.get("snippet", "") or "")[:140])

    # Digest
    cls = state.get("classifications", {})
    cat_counts = Counter(v.get("category", "Other") for v in cls.values())

    top_items = emails[:8]

    digest_input = {
        "totals": {"emails": len(emails)},
        "by_category": dict(cat_counts),
        "top_items": [
            {
                "subject": e.get("subject", ""),
                "from": e.get("from", ""),
                "category": cls.get(e["id"], {}).get("category", "Other"),
                "summary": summaries.get(e["id"], ""),
            }
            for e in top_items
        ],
    }

    try:
        digest = chat(
            [
                {"role": "system", "content": DIGEST_SYSTEM},
                {"role": "user", "content": str(digest_input)},
            ]
        ).strip()
    except Exception as exc:
        logger.warning("digest failed: %s", exc)
        digest = (
            f"You have {len(emails)} recent emails. "
            f"Categories: {dict(cat_counts)}."
        )

    return {"summaries": summaries, "digest": digest}
