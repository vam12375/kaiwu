# Frontend Hook Guidelines

> How hooks, event reducers, and data fetching are used.

---

## Hook Responsibilities

The frontend task/conversation flow is split intentionally:

| File | Responsibility |
|------|----------------|
| `src/hooks/useSseEvents.ts` | Low-level SSE `fetch` + stream frame parsing |
| `src/hooks/useAgentTask.ts` | Create/cancel/retry tasks, maintain task status, subscribe to events |
| `src/hooks/useConversationTask.ts` | Prepare user input, optimistic messages, follow-up node, controller wiring, cache final state |
| `src/hooks/agentTaskController.ts` | Convert task events into UI side effects |
| `src/hooks/agentEventReducer.ts` | Pure message-state reducer for content/svg/image/file/conversation events |
| `src/hooks/useConversation.ts` | Conversation history load/delete/rename/reset/cache restore |

Keep new logic in the layer that matches its responsibility. For example, new event types usually need a pure reducer change plus controller side effects, not a large `handleSend()` rewrite.

---

## Data Fetching

Use `apiJson<T>()` from `src/api/client.ts` for JSON endpoints whenever practical.

Current exceptions:

- `useSseEvents()` uses raw `fetch` because it reads a stream.
- File/image downloads use raw `fetch` or `window.open`.
- Do not hardcode backend origins such as `http://localhost:5001` in frontend source. Use `API_BASE_URL` and API helpers; local split-origin development belongs in `VITE_API_BASE_URL`.

Do not call `/api/chat` from new frontend code. Current task flow uses `/api/tasks` via `src/api/tasks.ts`.

---

## SSE Event Handling

SSE frames are parsed as one or more `data: ` lines separated by a blank line. `useSseEvents()` owns that protocol detail.

Task status mapping lives in `useAgentTask()`:

- `task_created` -> `queued`
- `analyzing` -> `routing`
- `node_selected` and `progress` -> `running`
- `response_start`, `content`, `svg_gen_start`, `image_gen_start` -> `streaming`
- `file_saved` -> `saving`
- `done` -> `completed`
- `error` -> `failed`
- `cancelled` -> `cancelled`

If the backend adds a new event type that affects loading state, update this map and then update reducer/controller handling.

---

## Reducer Versus Controller

Use `agentEventReducer.ts` for pure message state updates:

- `content`
- `svg`
- `image`
- `file_saved`
- `conversation_saved`

Use `agentTaskController.ts` for UI side effects:

- workflow phase changes
- node progress display
- active node updates
- suggested questions
- history refresh
- project image refresh
- coding preview opening
- error/cancel UI transitions

Do not mix side effects into `reduceAgentEvent()`.

---

## Refs And Abort Controllers

The app uses refs for mutable values that must survive async callbacks:

- `convIdRef`
- `sseConvIdRef`
- `followupNodeRef`
- `suggestedQuestionsRef`
- `convCacheRef`
- `isComposingRef`

`useAgentTask()` owns the active `AbortController`. Stopping generation should call `cancelTask()` and then reset local UI state.

---

## Common Mistakes

- Adding a new SSE event on the backend without updating `AgentTaskEvent` consumers.
- Saving the same task conversation from the frontend and backend.
- Forgetting to clear `followupNodeRef` after a task finishes.
- Parsing suggestions or image markdown in multiple places instead of `useConversation()`.
- Swallowing an error that should update the AI placeholder message.
