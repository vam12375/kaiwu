# Frontend Directory Structure

> How `kaiwu/src/` frontend code is organized.

---

## Current Layout

```text
kaiwu/
├── package.json
├── vite.config.ts
├── public/                      # Logo/image assets served by Vite
└── src/
    ├── App.tsx                  # Top-level state owner and component wiring
    ├── api/
    │   ├── client.ts            # API base URL and JSON helper
    │   └── tasks.ts             # Task API types and calls
    ├── features/
    │   ├── chat/                # Conversation UI and sidebar history
    │   └── layout/              # Sidebar, main stage, modals
    ├── hooks/                   # Task transport, event reducers/controllers, conversation cache
    ├── data.ts                  # Static product config and UI lists
    ├── types.ts                 # Shared UI/domain types
    ├── utils.ts                 # Markdown rendering and helpers
    └── styles.css               # Global class-based styling
```

The old docs mention `pages/` and `context/`, but the current codebase uses `features/*` plus hooks. Do not create `pages/` or `context/` just because older docs mention them.

---

## Ownership Boundaries

### API Layer

Use `src/api/client.ts` and `src/api/tasks.ts` for JSON API calls and task types.

Current pattern:

- `apiJson<T>()` centralizes JSON requests.
- `API_BASE_URL` reads `VITE_API_BASE_URL`; when it is empty, calls use same-origin relative `/api/...` URLs.
- Local Vite development may leave `VITE_API_BASE_URL` empty and use the dev proxy in `vite.config.ts`; direct split-origin development may set `VITE_API_BASE_URL=http://localhost:5001` in `kaiwu/.env.local`.
- Production source code must not hardcode localhost.
- `tasks.ts` owns `AgentTaskStatus`, `CreateTaskPayload`, `AgentTaskEvent`, and `/api/tasks` helpers.

### Scenario: Frontend API base URL and Vite dev proxy

#### 1. Scope / Trigger

Use this contract when changing `src/api/client.ts`, `kaiwu/vite.config.ts`, frontend environment examples, or any browser-facing API/download/SSE URL construction.

#### 2. Signatures

- Environment key: `VITE_API_BASE_URL=<absolute origin or empty>`.
- Frontend helper: `API_BASE_URL` from `src/api/client.ts`.
- Dev proxy: `server.proxy['/api'].target = 'http://localhost:5001'` in `kaiwu/vite.config.ts`.

#### 3. Contracts

- `VITE_API_BASE_URL=` (empty): API helpers call same-origin `/api/...`; local Vite dev forwards `/api` to the backend through its proxy.
- `VITE_API_BASE_URL=http://localhost:5001`: browser calls the local backend directly and bypasses the Vite proxy.
- `VITE_API_BASE_URL=https://<domain>`: browser calls a deployed backend/API gateway.
- `kaiwu/src/**` must not embed `http://localhost:5001`; local origins belong in env examples, local `.env.local`, or Vite dev-only proxy config.

#### 4. Validation & Error Matrix

- `VITE_API_BASE_URL=http://localhost:5173` -> browser posts back to the Vite frontend server and `/api/tasks` fails unless explicitly proxied; do not use this value.
- Backend on `5001` is not running -> Vite proxy returns a proxy/network error; start `kaiwuback/main.py`.
- `localhost:5001` hardcoded in `kaiwu/src/**` -> deployed browsers call the user's own machine; move the origin to env/config.

#### 5. Good/Base/Bad Cases

- Good local proxy: `VITE_API_BASE_URL=` and `GET http://127.0.0.1:<vite-port>/api/health` returns backend health JSON.
- Good local direct: `VITE_API_BASE_URL=http://localhost:5001` and API calls go directly to FastAPI.
- Base same-origin deploy: leave `VITE_API_BASE_URL` empty and serve frontend/backend behind the same origin.
- Bad: `VITE_API_BASE_URL=http://localhost:5173`.

#### 6. Tests Required

- Run `npm run build` from `kaiwu/`.
- For proxy changes, smoke test a Vite dev server request to `/api/health` and confirm it returns the backend health response.
- Run `rg "localhost:5001" kaiwu/src kaiwuback/server kaiwuback/main.py -g "!*.bak"` and expect no production runtime matches.

#### 7. Wrong vs Correct

Wrong:

```dotenv
VITE_API_BASE_URL=http://localhost:5173
```

Correct local proxy:

```dotenv
VITE_API_BASE_URL=
```

Correct local direct backend:

```dotenv
VITE_API_BASE_URL=http://localhost:5001
```

### Hook Layer

Use hooks for stateful logic and side effects:

- `useAgentTask()` creates/cancels/retries tasks and subscribes to events.
- `useSseEvents()` parses `data: ...\n\n` SSE frames.
- `useConversationTask()` owns send orchestration, optimistic messages, and task controller setup.
- `agentTaskController.ts` maps task events to UI side effects.
- `agentEventReducer.ts` is the pure reducer for content/image/svg/file/conversation events.
- `useConversation()` loads, deletes, renames, resets, and caches conversations.

### Feature Components

Feature components should focus on rendering and user interaction:

- `features/chat/ConversationPanel.tsx`
- `features/chat/SidebarHistory.tsx`
- `features/layout/AppSidebar.tsx`
- `features/layout/MainStage.tsx`
- `features/layout/AppModals.tsx`

Do not put new transport logic directly into feature components when a hook or API helper is the natural owner.

### Static Config And Types

- Add static menu/model/folder/skill options to `data.ts`.
- Derive shared union types in `types.ts` from `data.ts` when possible.
- Keep task API types in `api/tasks.ts` because they are API contracts, not generic UI types.

---

## Naming Conventions

- React components use PascalCase filenames and exports.
- Hooks use `use*` filenames and exports.
- Pure event helpers use descriptive names such as `reduceAgentEvent()`.
- Type aliases use PascalCase.
- CSS classes currently use kebab-case and are globally scoped in `styles.css`.

---

## Generated And Legacy Files

Do not learn current behavior from:

- `src/App.tsx.bak`
- `src/styles.css.bak`
- generated HTML under `kaiwuback/project-files/`

These files can help investigate history, but they are not the active architecture.

---

## Examples To Follow

- Use `src/api/tasks.ts` for typed task API calls.
- Use `src/hooks/useSseEvents.ts` for SSE parsing instead of duplicating stream parsing.
- Use `src/hooks/agentEventReducer.ts` for message-content event handling.
- Use `src/features/chat/ConversationPanel.tsx` for chat interaction patterns.
- Use `src/features/layout/AppSidebar.tsx` for typed component props.
