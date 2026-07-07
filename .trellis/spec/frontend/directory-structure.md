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
- Local split-origin development should set `VITE_API_BASE_URL=http://localhost:5001` in `kaiwu/.env.local`; production source code must not hardcode localhost.
- `tasks.ts` owns `AgentTaskStatus`, `CreateTaskPayload`, `AgentTaskEvent`, and `/api/tasks` helpers.

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
