# Clean Mailbox

Turborepo monorepo: a React + Tailwind frontend and a FastAPI backend running a multi-agent system (LangGraph + LangChain + LiteLLM, Ollama by default) that classifies and labels Gmail. Never deletes.

> **Safety:** the labeler agent **only adds** labels. There is no code path that removes labels, archives, trashes, or deletes messages. Enforced in [apps/api/src/clean_mailbox_api/gmail/labels.py](apps/api/src/clean_mailbox_api/gmail/labels.py) and asserted in [apps/api/tests/test_labeler_safety.py](apps/api/tests/test_labeler_safety.py).

## Layout

```
apps/
  web/  Vite + React + TS + Tailwind
  api/  FastAPI (uv-managed)
packages/
  shared-types/  TS types mirroring API responses
```

## Prerequisites

- Node.js 20+ and **pnpm 9** (`npm i -g pnpm`)
- Python 3.11+ and **uv** (`brew install uv`)
- **Ollama** running locally with at least one model pulled, e.g. `ollama pull gemma3`
- Google Cloud OAuth 2.0 **Web** Client with redirect `http://localhost:8000/auth/callback` and Gmail API enabled

## Setup

```bash
pnpm install
cd apps/api && uv sync && cd ../..
cp .env.example apps/api/.env
cp .env.example apps/web/.env   # only VITE_API_URL is read here
```

Required env (see [.env.example](.env.example)):

- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `SESSION_SECRET` — `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `OLLAMA_BASE_URL` (default `http://localhost:11434`)
- `LLM_MODEL` (default `ollama/gemma3`)

## Run

```bash
pnpm dev
```

Vite on http://localhost:5173, FastAPI on http://localhost:8000. Sign in with Google, choose how many emails to fetch, click **Run agents** — progress streams in real time.

## Tests / typecheck

```bash
cd apps/api && uv run pytest -q
cd apps/web && pnpm typecheck
```

## Architecture

- `auth/` — Google OAuth Authorization Code flow. Tokens are encrypted at rest using a Fernet key derived from `SESSION_SECRET` and stored under `cache/users/<sub>.json`.
- `gmail/` — read-only listing + add-only labels.
- `agents/`:
  - `llm.py` — LiteLLM wrapper (Ollama by default).
  - `state.py` — `AgentState` TypedDict.
  - `classifier.py` — assigns a category from the user's configured list.
  - `summarizer.py` — per-email summary + dashboard digest.
  - `labeler.py` — applies category labels (add-only).
  - `supervisor.py` / `graph.py` — LangGraph routing.
- `routes/`:
  - `GET /me`, `GET /emails?limit=N`, `GET /summary`
  - `POST /agents/run { limit? }`, `POST /agents/run/stream` (SSE), `GET /agents/status`
  - `GET/PUT /settings/labels`, `GET /settings/gmail-labels`

## Notes

- No database. Per-user JSON files under `CACHE_DIR/data/`.
- Categories and label prefixes are user-configurable at `/settings/labels`.
- `Sign out` clears the browser session cookie only; the encrypted refresh token stays on disk so re-login doesn’t force re-consent.

## For AI agents working in this repo

See [AGENTS.md](AGENTS.md), [apps/api/AGENTS.md](apps/api/AGENTS.md), [apps/web/AGENTS.md](apps/web/AGENTS.md).
