# Backend agent guide — apps/api

FastAPI + LangGraph multi-agent service. Python 3.11, managed by `uv`.

## Run

```bash
uv sync                  # install deps (run from apps/api)
uv run uvicorn clean_mailbox_api.main:app --reload --port 8000
uv run pytest -q
```

## Layout

- `main.py` — app factory + router registration. Add new routers here.
- `config.py` — env-driven `Settings` (pydantic-settings) and static constants (`CATEGORIES`, `GOOGLE_OAUTH_SCOPES`, `FORBIDDEN_MODIFY_KEYS`). Read via `get_settings()` (cached).
- `auth/` — Google OAuth code flow (custom httpx, not oauthlib `Flow`). Tokens encrypted with Fernet derived from `SESSION_SECRET`. Stored in `cache/users/<sub>.json`.
- `gmail/`
  - `client.py` — builds the Gmail API service for a user.
  - `messages.py` — `list_recent` (metadata + snippet only; no full body).
  - `labels.py` — `ensure_label`, `add_labels`, `list_user_labels`. **Add-only.** `add_labels` asserts no `removeLabelIds`/`trash`/`delete`.
- `agents/`
  - `llm.py` — `chat` and `chat_json` via LiteLLM (Ollama by default).
  - `state.py` — `AgentState` TypedDict (single source of truth for state shape).
  - `classifier.py` — assigns a category from the user's configured list.
  - `summarizer.py` — per-email summaries + dashboard digest text.
  - `labeler.py` — applies category labels (add-only).
  - `supervisor.py` — decides next node; routes by key presence in state.
  - `graph.py` — builds the `StateGraph`, exposes `run_agents` and `stream_agents`.
- `routes/`
  - `me.py` — `GET /me`, `require_session` dependency used by all auth-gated routes.
  - `emails.py` — `GET /emails`, `GET /summary` (includes today's emails).
  - `agents.py` — `POST /agents/run`, `POST /agents/run/stream` (SSE), `GET /agents/status`.
  - `settings.py` — `GET/PUT /settings/labels`, `GET /settings/gmail-labels`.
- `store/`
  - `cache.py` — per-user enriched email JSON.
  - `memory.py` — in-process "agent run in progress" lock.
  - `user_settings.py` — per-user label config (prefix, categorySubPrefix, categories).

## Adding a new agent node

1. Add a node module under `agents/` exposing a function `node_name(state: AgentState) -> AgentState`.
2. Add a key to `AgentState` for its output (presence-based completion).
3. Wire it in `agents/graph.py` (`add_node`, conditional edges, `add_edge` back to `supervisor`).
4. Add a key-presence branch in `agents/supervisor.py`.
5. Add a label in `routes/agents.py::NODE_LABELS` and (optionally) a branch in `_step_detail` for richer progress.
6. If the node enriches per-email data, merge it in `routes/agents.py::_merge`.

## Adding a new route

1. Create a router in `routes/<name>.py`. Use `Depends(require_session)` for auth.
2. Register it in `main.py` (`app.include_router(...)`).
3. Mirror the response type in [apps/web/src/api/client.ts](../web/src/api/client.ts).

## Env

All env vars live in `apps/api/.env`. See [.env.example](../../.env.example). Never commit `.env`.

## Don'ts

- Don't call any Gmail mutation other than `messages.modify` with `addLabelIds`.
- Don't log full email bodies. `snippet[:400]` is the cap used internally.
- Don't read tokens directly — use `gmail.client.get_service(sub)`.
- Don't add a database. Storage is intentionally JSON-on-disk.
