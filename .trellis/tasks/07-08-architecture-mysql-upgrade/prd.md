# 全面优化架构和 MySQL 持久化

## Goal

把 Kaiwu 当前的 FastAPI + React + MySQL 架构升级为更可靠、可迁移、可扩展的模块化单体。第一目标是稳住数据库和任务事件底座，让 `/api/tasks`、SSE、会话保存、项目产物沉淀在更高并发和后续云部署下仍然可靠。

## What I Already Know

* 后端入口 `kaiwuback/main.py` 只做 FastAPI app、CORS 和路由注册，现有边界是正确的。
* 当前主链路是 `POST /api/tasks` -> `TaskService` -> `AgentRuntime` -> `EventStore` -> `agent_events` -> SSE -> 前端 reducer。
* MySQL 配置已经从环境变量读取，入口在 `kaiwuback/server/config.py`。
* 数据库访问仍是直接 PyMySQL：`server/persistence/database.py:get_db()` 每次创建新连接。
* `agent_tasks` / `agent_events` schema 同时存在于 `EventStore.ensure_schema()` 和 `docs/sql/2026-07-01-agent-tasks-events.sql`。
* `conversations` / `messages` 最小 schema 主要写在 README，缺少统一迁移机制。
* `agent_events.seq` 当前通过 `SELECT MAX(seq)+1` 生成，存在并发写冲突风险。
* 项目文件、图片元数据大量仍在 `.json` sidecar 文件里，后续适合迁入 MySQL。
* 前端事件链是 `useSseEvents -> useAgentTask -> agentEventReducer / agentTaskController -> UI`，不应在组件里重复解析 SSE。

## Research References

* [`research/database-runtime-options.md`](research/database-runtime-options.md) - 建议第一阶段采用兼容 PyMySQL 的保守基础设施升级，预留未来 SQLAlchemy/Alembic 路径。

## Assumptions

* 这次优化优先保证可上线稳定性，而不是一次性改成微服务。
* 现阶段不引入用户/租户/权限模型，除非用户明确要求。
* 不破坏现有前端接口、SSE event 类型、对话重命名、AI 生成文件双归档等业务约束。
* 若涉及数据迁移，会优先提供可重复执行的 SQL，而不是直接修改线上数据。

## Requirements (Evolving)

* 引入 SQLAlchemy Core 作为长期数据库基础设施，优先使用 Core/Engine/Connection，不引入 ORM 模型作为第一阶段目标。
* 引入 Alembic 作为正式 schema migration 工具，建立 migration 环境、版本表和首批 revision。
* 建立统一数据库连接入口，配置 MySQL 连接池、连接回收、连接预检和超时参数。
* 提供事务 helper，减少手写 `commit/finally/close` 重复代码。
* 保留现有 `get_db()` 调用兼容性，避免一次性重写所有 PyMySQL cursor 代码。
* 首批 Alembic migration 只覆盖核心主链路表：`conversations`、`messages`、`agent_tasks`、`agent_events`。
* 优化 `agent_events` 写入序号分配，避免同一 task 并发写事件时 `seq` 冲突。
* 增加必要索引，支持任务按状态/更新时间、会话按更新时间、事件按 task/seq 高效查询。
* 保持现有 `/api/tasks`、`/api/tasks/{id}/events`、`/api/conversations`、项目库 API 兼容。
* 保持任务事件先持久化、再由 SSE 输出的架构。

## Acceptance Criteria (Evolving)

* [x] 后端 `python -m compileall kaiwuback/server` 通过。
* [x] 前端 `npm run build` 在跨层改动后通过。
* [x] 新增 SQLAlchemy/Alembic 依赖并可在后端环境中导入。
* [x] Alembic migration 环境可发现 `upgrade head` 所需 revisions，首批 migration 覆盖 `conversations`、`messages`、`agent_tasks`、`agent_events`。
* [x] SQLAlchemy engine 配置 MySQL 连接池、连接回收和连接预检。
* [x] `get_db()` 兼容现有调用，不要求一次性重写所有 PyMySQL cursor SQL。
* [x] `agent_events` 对同一 `task_id` 保持单调递增 `seq`，并继续通过 `(task_id, seq)` 查询 SSE。
* [x] `/api/tasks` 创建任务、SSE 流、取消任务、会话保存路径保持可用。
* [x] README 或 docs 更新本地/生产数据库初始化方式。
* [x] 不提交任何真实 API key、MySQL 密码或本地密钥。
* [x] 第二阶段项目库/图片库元数据迁入 MySQL 表，同时保留 sidecar 回退。

## Definition of Done

* Tests/checks added or updated where risk warrants.
* Backend compile passes.
* Frontend build passes if API/event contracts change.
* Migration and rollback guidance documented.
* Existing task/SSE/conversation behavior preserved.
* Trellis spec update reviewed if new conventions are introduced.

## Feasible Approaches

### Approach A: 分阶段保守升级

第一阶段只升级数据库底座、migration、事件写入可靠性和文档。后续再迁项目库 JSON 元数据、产物表、worker 队列。

Pros:

* 风险最低。
* 最符合当前 PyMySQL 代码形态。
* 能快速解决最关键的稳定性问题。

Cons:

* 不是一次性完成所有长期架构目标。

### Approach B: SQLAlchemy Core + Alembic 一次引入 (Chosen)

把数据库连接池、事务和 migration 都放到 SQLAlchemy/Alembic 体系里，但暂不使用 ORM。

Pros:

* 长期标准化更强。
* migration 能力成熟。

Cons:

* 改动范围更大，需要适配现有 PyMySQL cursor 调用。

### Approach C: 全量架构重构

同时引入仓储层、artifact 表、项目库 MySQL 化、worker 队列、事件恢复 API。

Pros:

* 最接近长期目标。

Cons:

* 单次风险过高，不适合作为第一步。

## Decision (ADR-lite)

**Context**: Kaiwu 当前使用直接 PyMySQL 访问 MySQL，schema 分散在 runtime `CREATE TABLE IF NOT EXISTS`、SQL 文档和 README 中。用户希望选择长期正规化方案，而不是只做短期补丁。

**Decision**: 第一阶段采用 SQLAlchemy Core + Alembic。SQLAlchemy 提供长期统一的 engine、pool 和事务基础设施；Alembic 负责正式 schema migration。第一阶段暂不引入 ORM，不重写所有业务 SQL，优先保持现有 API/SSE/会话行为兼容。

**Consequences**: 短期改动量高于保守 PyMySQL 升级，需要新增依赖、migration 环境和桥接层；长期收益是数据库演进、连接管理、迁移记录和部署流程更正规。

## Scope Decision

第一阶段采用核心表优先：只正规化 `conversations`、`messages`、`agent_tasks`、`agent_events`。项目库、图片库、artifact 表和 JSON sidecar 迁移放入后续阶段。

第二阶段继续迁移项目库/图片库元数据：文件二进制仍保留在文件系统中，`.folder-meta.json`、`.file-meta.json`、`.folder-state.json` 和 `.image-meta.json` 对应的元数据进入 MySQL。运行时读取会合并旧 sidecar 和 MySQL 数据，MySQL 数据优先；写入优先 MySQL，数据库不可用时回退 sidecar。

## Open Questions

* None.

## Implementation Notes

* Added SQLAlchemy Core engine infrastructure in `kaiwuback/server/persistence/db.py`.
* Kept `server.persistence.database.get_db()` compatible with existing PyMySQL-style cursor callers.
* Added Alembic config and baseline migration under `kaiwuback/alembic/`.
* Baseline migration covers `conversations`, `messages`, `agent_tasks`, and `agent_events`.
* Added `agent_tasks.event_seq` and changed `EventStore.write_event()` to allocate event sequence numbers under a row lock.
* Updated README, `.env.example`, manual SQL references, and backend database Trellis spec.

## Stage 2 Implementation Notes

* Added Alembic migration for `project_folder_metadata`, `project_file_metadata`, and `project_image_metadata`.
* Added a project metadata persistence module that keeps old sidecar reads as fallback and compatibility input.
* Added one-time runtime backfill from legacy sidecars into empty MySQL metadata tables.
* MySQL writes mirror the current metadata map back to sidecars after successful DB transactions so fallback mode does not resurrect stale deletes or renames.
* Wired project folder/file/image metadata helpers to the MySQL-backed persistence module.
* Preserve existing API response fields and filesystem storage behavior.
* Keep project files/images themselves out of MySQL for this stage.

## Verification Results

* `python -m compileall kaiwuback/server kaiwuback/alembic` passed.
* `python -c "import sqlalchemy, alembic; print(sqlalchemy.__version__)"` passed after installing requirements.
* `python -m alembic history` from `kaiwuback/` found `20260708_0002` as head.
* `npm run build` from `kaiwu/` passed.
* `python -c "import main; print(main.app.title)"` from `kaiwuback/` passed.
* `python -c "from server.persistence import project_metadata; print(project_metadata.read_folder_state())"` passed; local DB without the new metadata table fell back to sidecar metadata as expected.
* FastAPI TestClient smoke for `GET /api/project-folders` and `GET /api/project-images` returned `200` list responses with sidecar fallback.
* `git diff --check` passed with line-ending warnings only.
* Secret scan found only documented placeholder keys in `.env.example`/README and the expected password config field reference.
* Did not run `python -m alembic upgrade head` against the configured MySQL database to avoid applying real schema changes without an explicit DB migration run.

## Out of Scope (Temporary)

* 用户体系、多租户、权限模型。
* 把整个 AgentRuntime 拆成独立微服务。
* 一次性把所有项目文件/图片二进制内容迁入 MySQL。
* 不把项目文件/图片二进制内容迁入 MySQL；二阶段只迁元数据。
* 改动 UI 视觉设计，除非数据库/API 升级必须同步。

## Technical Notes

* Relevant backend specs:
  * `.trellis/spec/backend/index.md`
  * `.trellis/spec/backend/database-guidelines.md`
  * `.trellis/spec/backend/directory-structure.md`
* Relevant frontend specs:
  * `.trellis/spec/frontend/index.md`
* Key files:
  * `kaiwuback/server/config.py`
  * `kaiwuback/server/persistence/database.py`
  * `kaiwuback/server/agent/event_store.py`
  * `kaiwuback/server/agent/task_service.py`
  * `kaiwuback/server/agent/runtime.py`
  * `kaiwuback/server/api/routes_tasks.py`
  * `kaiwuback/server/api/routes_conv.py`
  * `kaiwuback/server/api/routes_files.py`
  * `kaiwu/src/hooks/useSseEvents.ts`
  * `kaiwu/src/hooks/useAgentTask.ts`
  * `kaiwu/src/hooks/agentEventReducer.ts`
  * `kaiwu/src/hooks/agentTaskController.ts`
