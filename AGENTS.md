# AGENTS.md

Guidance for AI coding agents working in this repository. Keep it short, keep it true.

## Repo at a glance

- **Monorepo** managed by Turborepo + pnpm 9 workspaces.
- **Frontend:** [apps/web](apps/web) — Vite + React 18 + TS 5.5 + Tailwind 3 + react-router 7.
- **Backend:** [apps/api](apps/api) — FastAPI on Python 3.11, managed by `uv`. Multi-agent system using LangGraph + LangChain + LiteLLM. Defaults to Ollama (`ollama/gemma3`).
- **Shared types:** [packages/shared-types](packages/shared-types).
- **Storage:** plain JSON under `apps/api/cache/`. No database. Tokens are Fernet-encrypted; user data is plain JSON.

## Hard invariants — do not break

1. **Never delete, archive, or trash Gmail messages.** Never call `users().messages().trash/untrash/delete`. Never pass `removeLabelIds`, `trash`, or `delete` to `messages.modify`. The labeler is **add-only**. See [apps/api/src/clean_mailbox_api/gmail/labels.py](apps/api/src/clean_mailbox_api/gmail/labels.py) and the safety test in [apps/api/tests/test_labeler_safety.py](apps/api/tests/test_labeler_safety.py).
2. **Do not log secrets or full email bodies.** Subject + sender + snippet only.
3. **Do not bypass `_coerce` in [store/user_settings.py](apps/api/src/clean_mailbox_api/store/user_settings.py).** All user-supplied label config must round-trip through it.
4. **Do not reintroduce `PRIORITIES` / priority labels.** They were removed deliberately.
5. **Do not commit `apps/api/.env`, `cache/`, or any token files.**

## Common commands

```bash
pnpm install                       # install JS deps
cd apps/api && uv sync             # install Python deps

pnpm dev                           # run web + api together (turbo)
pnpm dev:web                       # web only
pnpm dev:api                       # api only

cd apps/api && uv run pytest -q    # backend tests
cd apps/web && pnpm typecheck      # frontend typecheck
cd apps/web && pnpm lint           # eslint
```

## Code conventions

- **Python:** type-hinted, `from __future__ import annotations`, no implicit `Any` in new code, prefer `pathlib.Path`, prefer pydantic models at boundaries. Settings come from [config.py](apps/api/src/clean_mailbox_api/config.py).
- **TypeScript:** strict; no `any` unless unavoidable; functional React components with hooks; Tailwind utility classes (no CSS modules).
- **API ↔ UI types:** mirror manually in [apps/web/src/api/client.ts](apps/web/src/api/client.ts). Update both sides together.
- **Imports:** absolute within Python package (`from ..config import ...`); relative within app for TS.
- **No new top-level dependencies** without a clear justification.

## Architecture quick map

```
apps/api/src/clean_mailbox_api/
  main.py            FastAPI app + router registration
  config.py          Settings (env) + CATEGORIES + scopes
  auth/              Google OAuth code flow + Fernet token store
  gmail/             messages.list (read-only), labels (add-only)
  agents/
    llm.py           LiteLLM wrapper
    state.py         AgentState TypedDict
    classifier.py    LLM → category per email
    summarizer.py    per-email summaries + dashboard digest
    labeler.py       applies category labels (add-only)
    supervisor.py    LangGraph routing
    graph.py         StateGraph build + run/stream entry points
  routes/
    me.py, emails.py, agents.py, settings.py
  store/
    cache.py         per-user JSON I/O
    memory.py        in-process “is running” lock
    user_settings.py per-user label config
```

```
apps/web/src/
  api/client.ts      typed fetch + SSE consumer for /agents/run/stream
  auth/              AuthContext (session probe)
  pages/             Dashboard, LabelSettings, Login
  components/        SummaryCards, AgentRunButton, AgentProgress, FetchCountControl
```

## Streaming agent run

`POST /agents/run/stream` returns Server-Sent Events. Event names: `step`, `done`, `error`. The frontend reads it via `fetch` + `ReadableStream` in [client.ts](apps/web/src/api/client.ts) → `runAgentsStream`. If you add a new agent node, also add it to `NODE_LABELS` in [routes/agents.py](apps/api/src/clean_mailbox_api/routes/agents.py) and consider exposing per-step detail in `_step_detail`.

## Workflow expectations

- Read before editing — files change frequently.
- After backend changes: run `uv run pytest -q`.
- After frontend changes: run `pnpm typecheck` from `apps/web`.
- Don’t add markdown documentation unless asked; update existing docs when behavior changes.
- Don’t introduce new background processes or daemons; this app is local-first.
