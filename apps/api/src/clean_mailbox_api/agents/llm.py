"""Thin LiteLLM wrapper. Routes all completions through LiteLLM so we can
swap providers (Ollama by default) without touching agent code.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import litellm

from ..config import get_settings

logger = logging.getLogger(__name__)


def chat(messages: list[dict[str, str]], **kwargs: Any) -> str:
    """Run a chat completion via LiteLLM and return the assistant text."""
    settings = get_settings()
    try:
        resp = litellm.completion(
            model=settings.llm_model,
            messages=messages,
            api_base=settings.ollama_base_url,
            **kwargs,
        )
        return resp["choices"][0]["message"]["content"] or ""
    except Exception as exc:  # pragma: no cover - logged for visibility
        logger.exception("LLM call failed: %s", exc)
        raise


def chat_json(messages: list[dict[str, str]], **kwargs: Any) -> Any:
    """Chat completion that expects a JSON object/array response.

    Tolerant of code fences and stray prose around the JSON.
    """
    text = chat(messages, **kwargs).strip()
    # Strip markdown fences if present.
    if text.startswith("```"):
        text = text.strip("`")
        # Remove leading json marker line if any.
        if "\n" in text:
            first, rest = text.split("\n", 1)
            if first.strip().lower() in {"json", ""}:
                text = rest
    # Find first { or [ to be lenient.
    for start_char, end_char in (("{" , "}"), ("[", "]")):
        if start_char in text:
            i = text.find(start_char)
            j = text.rfind(end_char)
            if 0 <= i < j:
                candidate = text[i : j + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    raise ValueError(f"LLM did not return valid JSON: {text[:200]!r}")
