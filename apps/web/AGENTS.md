# Frontend agent guide — apps/web

Vite + React 18 + TypeScript 5.5 + Tailwind 3 + react-router 7.

## Run

```bash
pnpm dev          # vite dev server on :5173
pnpm build        # tsc -b && vite build
pnpm typecheck    # tsc -b --noEmit
pnpm lint         # eslint, max-warnings 0
```

## Layout

- `src/main.tsx` — entry; mounts `<App />` inside `<AuthProvider>` + `<BrowserRouter>`.
- `src/App.tsx` — auth-gated routes: `/login`, `/`, `/settings/labels`.
- `src/api/client.ts` — typed fetch wrapper. **Source of truth for response shapes** the UI uses. Includes `runAgentsStream` (SSE consumer over `fetch` + `ReadableStream`).
- `src/auth/AuthContext.tsx` — probes `/me`, exposes `useAuth()`.
- `src/pages/`
  - `Dashboard.tsx` — main view: fetch-count control, run button, streaming progress, summary cards (incl. Today section).
  - `LabelSettings.tsx` — `/settings/labels` page; edits per-user categories + label prefixes; can import labels from Gmail.
  - `Login.tsx` — Google login redirect.
- `src/components/`
  - `SummaryCards.tsx` — Emails / Last run / By category compact cards + Today list + Digest panel.
  - `AgentRunButton.tsx` — disabled-while-running button.
  - `AgentProgress.tsx` — live SSE checklist (in-progress / done) per node.
  - `FetchCountControl.tsx` — number-of-emails control with `localStorage` persistence.

## Conventions

- Tailwind utility classes only. No CSS modules / styled-components.
- Functional components, hooks. No class components.
- Strict TS: no `any`, prefer narrow types over casts.
- All API calls go through `api.*` in [client.ts](src/api/client.ts) — never `fetch` directly from a component.
- File links / paths in JSX should not be invented; check the route table in `App.tsx`.

## Adding a new API call

1. Add the response interface to `src/api/client.ts`.
2. Add a method to the `api` object using `request<T>()`.
3. Use it from a component via `useEffect` or an event handler. Show errors via an inline banner like Dashboard does — don't `alert()`.

## SSE notes

`api.runAgentsStream(limit, onEvent)` is the reference SSE consumer. Event types are `step | done | error` (see `AgentStreamEvent`). The parser is tolerant of multi-line `data:` blocks and ignores comments. If the backend introduces a new event name, extend `parseSSE` and the discriminated union.

## Don'ts

- Don't reintroduce a "Recent emails" list, "By priority" card, or any priority badge — these were removed deliberately.
- Don't render or send full email bodies; the API only exposes metadata + snippet + summary.
- Don't add a global state library. Local state + context is enough.
