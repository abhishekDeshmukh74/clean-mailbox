# Copilot instructions

Read [AGENTS.md](../AGENTS.md), [apps/api/AGENTS.md](../apps/api/AGENTS.md) and [apps/web/AGENTS.md](../apps/web/AGENTS.md) before making non-trivial changes. Highlights:

- This is a Turborepo monorepo: `apps/web` (Vite + React + TS + Tailwind), `apps/api` (FastAPI + LangGraph + LiteLLM, managed by `uv`).
- **Never delete, archive, or trash Gmail messages.** The labeler is add-only. Don't pass `removeLabelIds`, `trash`, or `delete` to `messages.modify`. The safety contract is enforced in `apps/api/src/clean_mailbox_api/gmail/labels.py` and tested in `apps/api/tests/test_labeler_safety.py`.
- Storage is plain JSON under `apps/api/cache/`. Don't add a database.
- Don't reintroduce priorities (`PRIORITIES`, `P0`–`P3`, `priority_label`, "By priority" UI). They were removed deliberately.
- Don't log secrets or full email bodies — metadata + snippet only.

## Common commands

```bash
pnpm install
cd apps/api && uv sync

pnpm dev                            # web + api
cd apps/api && uv run pytest -q     # backend tests
cd apps/web && pnpm typecheck       # frontend typecheck
```

## Style

- Python: type-hinted, `from __future__ import annotations`, prefer `pathlib.Path`, settings via `get_settings()`.
- TypeScript: strict, functional React, Tailwind utilities only, all HTTP via `api.*` in `apps/web/src/api/client.ts`.
- Update the TS interfaces in `client.ts` whenever a backend response shape changes.

## When changing agents

If you add/remove a LangGraph node, also update: `agents/graph.py`, `agents/supervisor.py`, `routes/agents.py::NODE_LABELS` and `_step_detail`, and `routes/agents.py::_merge` if it produces per-email enrichment.
