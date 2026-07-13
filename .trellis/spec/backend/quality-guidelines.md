# Backend Quality Guidelines

> Code quality standards for backend development.

---

## Required Patterns

### Keep FastAPI Routes Thin

Routes validate requests, call services/utilities, and return responses. They should not own task orchestration, LLM prompt assembly, or persistence policy.

Good references:

- `server/api/routes_tasks.py`
- `server/api/routes_skills.py`

### Preserve Task-Driven AI Flow

New AI-visible work should flow through:

```text
route -> TaskService -> AgentRuntime -> EventStore -> /api/tasks/{id}/events -> frontend reducers
```

`/api/chat` in `main.py` is compatibility-only.

### Emit Events Before Streaming

Frontend-visible task output must be stored in `agent_events` before SSE streams it. This enables refresh/debug/retry behavior and aligns with `docs/specs/Spec-007-Task-Agent-Runtime.md`.

### Keep Node Changes Synchronized

When changing a Node:

- Update `server/nodes/prompts.py`.
- Update `server/intent/recognizer.py` trigger/dependency logic when routing or prerequisites change.
- Check `server/nodes/registry.py` still exposes the metadata the frontend/runtime needs.
- Re-read `docs/specs/Spec-001-Node拆分与依赖链.md` and `docs/specs/Spec-003-Intent识别策略.md`.

### Preserve Runtime Dates For Time-Sensitive Nodes

Node prompts must not rely on stale hardcoded dates for market, policy, price, financing, user-scale, or platform-rule data. Use `current_date_cn()` and `data_integrity_prompt()` from `server/config.py` when assembling LLM prompts, and add node-specific guards in the orchestration layer when a node has special date rules.

For `node1`, the runtime guard must:

- Derive the current year from `current_date_cn()`.
- Treat the current year as `YYYY年（截至最新公开数据）` when full-year public data may be incomplete.
- Require old data to say `公开数据截至YYYY年` or `来源发布于YYYY年`.
- Keep future 1-2 year values in a separate prediction table with `[预测]` or `[行业测算]`.

Wrong:

```python
dated_input = "[现在时间是2026年6月25日]\n\n" + user_input
```

Correct:

```python
current_date = current_date_cn()
dated_input = f"[现在时间是{current_date}]\n\n{user_input}"
```

### Preserve AI File Dual Archive

AI-generated files must continue to appear in the appropriate project folder and in `AI 对话产出`.

References:

- `曜势科技项目・极简记忆唤醒文档.md`
- `server/utils/file_io.py`
- `server/orchestrator/handlers.py`

---

## Forbidden Patterns

- Hardcoding API keys, tokens, or real passwords in source code.
- Adding new business logic to `main.py` or `/api/chat`.
- Bypassing `EventStore` for task-visible SSE output.
- Writing new implementation into `server/utils/common.py`.
- Treating `*.bak` files as current architecture.
- Removing `conversation_saved` as the backend-owned save notification for tasks.
- Adding a new external tool without considering `server/tools/registry.py` and `ToolSpec`.
- Returning provider raw errors or secrets to clients.

---

## Testing And Verification

There is no formal backend test suite yet. Use these checks according to change scope:

```powershell
python -m compileall kaiwuback/server
```

For task/SSE/frontend-integrated changes:

```powershell
Set-Location kaiwu
npm run build
```

Manual smoke targets:

- `GET http://localhost:5001/api/health`
- `POST /api/tasks` with a short message
- `GET /api/tasks/{task_id}`
- `GET /api/tasks/{task_id}/events`
- `GET /api/conversations`
- `GET /api/project-files` and `GET /api/project-images` after generated artifacts

---

## Review Checklist

Before finishing a backend change:

- Does it follow the frozen `docs/specs/` decision that owns the behavior?
- Does task output go through `EventStore`?
- Are task statuses valid according to `state_machine.py`?
- Are new API errors shaped as `{"error": "..."}`?
- Are secrets still only read from environment/config?
- Are project file outputs still dual archived when AI-generated?
- Did you avoid unrelated cleanup in generated artifacts and `.bak` files?
- Did you update `.trellis/spec/` or `docs/03-项目文档索引.md` if the convention changed?
