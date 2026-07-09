# Backend Database Guidelines

> Database patterns and conventions for `kaiwuback/`.

---

## Overview

The backend uses SQLAlchemy Core for the long-term database engine, pooling, and migrations. It does not use an ORM. Existing PyMySQL-style cursor callers are kept compatible through `server.persistence.database.get_db()`, which returns a pooled DB-API connection from the SQLAlchemy engine.

Reference files:

- `kaiwuback/server/persistence/db.py`
- `kaiwuback/server/persistence/database.py`
- `kaiwuback/server/persistence/project_metadata.py`
- `kaiwuback/server/agent/event_store.py`
- `kaiwuback/server/config.py`
- `kaiwuback/alembic.ini`
- `kaiwuback/alembic/versions/20260708_0001_core_persistence.py`
- `kaiwuback/alembic/versions/20260708_0002_project_metadata.py`
- `docs/sql/2026-07-08-core-persistence.sql`
- `docs/sql/2026-07-08-project-metadata.sql`
- `docs/sql/2026-07-01-agent-tasks-events.sql`
- `docs/specs/Spec-007-Task-Agent-Runtime.md`

---

## Scenario: SQLAlchemy Core And Alembic Persistence

### 1. Scope / Trigger

- Trigger: any change to database connection creation, pool settings, schema migration files, core persistence tables, or task event sequence allocation.
- Goal: keep MySQL persistence production-grade while preserving existing task/SSE/conversation behavior.

### 2. Signatures

- `server.persistence.db.database_url() -> sqlalchemy.engine.URL`
- `server.persistence.db.get_engine() -> sqlalchemy.engine.Engine`
- `server.persistence.db.get_db() -> DB-API connection`
- `server.persistence.db.transaction() -> Iterator[sqlalchemy.engine.Connection]`
- Alembic command from `kaiwuback/`: `python -m alembic upgrade head`
- Core tables: `conversations`, `messages`, `agent_tasks`, `agent_events`

### 3. Contracts

- SQLAlchemy engine uses `mysql+pymysql`.
- `get_db()` must remain compatible with existing code that calls `db.cursor()`, `db.commit()`, `db.rollback()`, and `db.close()`.
- Pool configuration is read from:
  - `KAIWU_DB_POOL_SIZE`, default `5`
  - `KAIWU_DB_MAX_OVERFLOW`, default `10`
  - `KAIWU_DB_POOL_TIMEOUT`, default `30`
  - `KAIWU_DB_POOL_RECYCLE`, default `3600`
- Connection timeouts are read from:
  - `KAIWU_DB_CONNECT_TIMEOUT`, default `5`
  - `KAIWU_DB_READ_TIMEOUT`, default `30`
  - `KAIWU_DB_WRITE_TIMEOUT`, default `30`
- Schema changes must be represented as Alembic revisions. SQL files under `docs/sql/` are manual references, not the primary migration mechanism.
- `agent_tasks.event_seq` is the per-task event sequence cursor. `EventStore.write_event()` must allocate `seq` inside one transaction after locking the task row.

### 4. Validation & Error Matrix

- SQLAlchemy/Alembic dependency missing -> backend import or migration command fails; update `requirements.txt` and install dependencies.
- MySQL unavailable -> task event store may use in-memory fallback; conversation persistence still requires MySQL.
- Core task/event schema missing or `event_seq` absent -> `EventStore` treats MySQL task events as unavailable and falls back to memory until migrations are applied.
- Alembic migration with existing old tables -> migration must create missing tables and add missing columns/indexes without dropping existing data.
- Real secrets in env docs/logs/source -> forbidden; use ignored `.env` / `.env.local` or process environment.

### 5. Good/Base/Bad Cases

- Good: `python -m alembic upgrade head` creates or updates the four core tables, including `agent_tasks.event_seq`.
- Good: existing code using `with db.cursor() as cur:` continues to work through the pooled raw connection returned by `get_db()`.
- Base: local development without MySQL can still create task events in memory for task API testing.
- Bad: adding `CREATE TABLE` SQL inside runtime code instead of an Alembic revision.
- Bad: calculating event sequence with `SELECT MAX(seq) + 1`, which can conflict under concurrent event writes.

### 6. Tests Required

- Backend syntax: `python -m compileall kaiwuback/server kaiwuback/alembic`.
- Dependency smoke: `python -c "import sqlalchemy, alembic; print(sqlalchemy.__version__)"`.
- Alembic discovery: from `kaiwuback/`, run `python -m alembic history` and confirm the expected head exists.
- Migration smoke when safe against a disposable/local database: `python -m alembic upgrade head`, then assert the four core tables exist and `agent_tasks.event_seq` exists.
- Cross-layer build: `Set-Location kaiwu; npm run build` when task/SSE API contracts are touched.

### 7. Wrong vs Correct

#### Wrong

```python
cur.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM agent_events WHERE task_id = %s", (task_id,))
seq = cur.fetchone()[0]
```

#### Correct

```python
cur.execute("SELECT event_seq FROM agent_tasks WHERE id = %s FOR UPDATE", (task_id,))
seq = int(cur.fetchone()[0] or 0) + 1
cur.execute("UPDATE agent_tasks SET event_seq = %s WHERE id = %s", (seq, task_id))
```

## Scenario: Project Metadata Persistence

### 1. Scope / Trigger

- Trigger: any change to project folder descriptions, project file metadata, virtual folder state, project image metadata, or the legacy sidecar files under `project-files/` and `project-images/`.
- Goal: move project metadata into MySQL while keeping file/image binary content on the filesystem and preserving API response compatibility.

### 2. Signatures

- `server.persistence.project_metadata.read_folder_meta() -> dict[str, str]`
- `server.persistence.project_metadata.write_folder_meta(meta: dict[str, str]) -> None`
- `server.persistence.project_metadata.read_folder_state() -> dict[str, object]`
- `server.persistence.project_metadata.write_folder_state(state: dict[str, object]) -> None`
- `server.persistence.project_metadata.read_file_meta() -> dict[str, dict[str, Any]]`
- `server.persistence.project_metadata.write_file_meta(meta: dict[str, dict[str, Any]]) -> None`
- `server.persistence.project_metadata.read_image_meta() -> dict[str, dict[str, Any]]`
- `server.persistence.project_metadata.write_image_meta(meta: dict[str, dict[str, Any]]) -> None`
- Tables: `project_folder_metadata`, `project_file_metadata`, `project_image_metadata`.
- Legacy sidecars: `.folder-meta.json`, `.folder-state.json`, `.file-meta.json`, `.image-meta.json`.

### 3. Contracts

- Route modules must not read or write project metadata sidecars directly. Keep metadata policy in `server.persistence.project_metadata`.
- `project_folder_metadata` owns folder descriptions, virtual-folder hidden state, and display names.
- `project_file_metadata` stores JSON metadata keyed by `(folder_name, filename)`.
- `project_image_metadata` stores JSON metadata keyed by image filename.
- File and image binary content stays in `project-files/`, `project-images/`, and `project-image-previews/`; do not store binaries in MySQL in this stage.
- Runtime reads seed empty metadata tables from legacy sidecars once per process. Existing MySQL rows take priority over sidecar values.
- Runtime writes prefer MySQL. After a successful MySQL write, also mirror the current metadata map back to the sidecar file so fallback mode does not resurrect stale deletes or renames.
- If MySQL/schema is unavailable, metadata reads and writes fall back to sidecars and print one compact `[PROJECT_META]` warning.

### 4. Validation & Error Matrix

- MySQL unavailable -> read/write sidecars and keep project file/image APIs usable.
- Metadata tables missing -> fall back to sidecars until `python -m alembic upgrade head` is applied.
- Malformed sidecar JSON -> log `[PROJECT_META] Sidecar read failed...` and use an empty fallback shape.
- Empty MySQL metadata table with existing sidecar -> first successful metadata access backfills sidecar rows into MySQL.
- MySQL write succeeds but sidecar is stale -> mirror sidecar immediately after the DB transaction to keep fallback behavior aligned.
- Metadata values must not contain API keys, provider tokens, request headers, or raw binary content.

### 5. Good/Base/Bad Cases

- Good: `GET /api/project-folders` reads folder descriptions and virtual folder display names through `project_metadata`, not from route-local JSON parsing.
- Good: deleting an image removes the image metadata row and mirrors the sidecar map so the deleted entry does not reappear on the next read.
- Base: a developer without MySQL can still list and mutate project library metadata through sidecar fallback.
- Bad: adding another `.json` read helper in `routes_files.py`.
- Bad: putting project image bytes or uploaded file bytes into the metadata tables.

### 6. Tests Required

- Backend syntax: `python -m compileall kaiwuback/server kaiwuback/alembic`.
- Alembic discovery: from `kaiwuback/`, run `python -m alembic history` and confirm `20260708_0002` is the head.
- Import smoke: import `server.persistence.project_metadata` and call a read function with missing metadata tables to verify sidecar fallback does not crash.
- Cross-layer build: `Set-Location kaiwu; npm run build` when project file/image API fields are touched.
- Migration smoke when safe against a disposable/local database: `python -m alembic upgrade head`, then assert the three project metadata tables exist.

### 7. Wrong vs Correct

#### Wrong

```python
data = json.loads((PROJECT_LIB / ".file-meta.json").read_text(encoding="utf-8"))
```

#### Correct

```python
from server.persistence import project_metadata

data = project_metadata.read_file_meta()
```

## Scenario: MySQL Environment Configuration

### 1. Scope / Trigger

- Trigger: any change to MySQL connection settings, `DB_CONFIG`, `.env.example`, or setup documentation.
- Goal: keep database credentials out of source code while preserving the existing `DB_CONFIG` contract for callers.

### 2. Signatures

- `server.config.DB_CONFIG: dict[str, object]`
- `server.persistence.database.get_db() -> DB-API connection compatible with PyMySQL cursor callers`
- `server.persistence.db.get_engine() -> sqlalchemy.engine.Engine`

### 3. Contracts

Environment keys:

- `KAIWU_DB_HOST`: optional, default `localhost`.
- `KAIWU_DB_PORT`: optional integer, default `3306`.
- `KAIWU_DB_USER`: optional, default empty string.
- `KAIWU_DB_PASSWORD`: optional, default empty string. Never hardcode a real password or a fake default password in source.
- `KAIWU_DB_NAME`: optional, default `kaiwu`.
- `KAIWU_DB_CHARSET`: optional, default `utf8mb4`.
- `KAIWU_DB_POOL_SIZE`: optional integer, default `5`.
- `KAIWU_DB_MAX_OVERFLOW`: optional integer, default `10`.
- `KAIWU_DB_POOL_TIMEOUT`: optional integer seconds, default `30`.
- `KAIWU_DB_POOL_RECYCLE`: optional integer seconds, default `3600`.
- `KAIWU_DB_CONNECT_TIMEOUT`: optional integer seconds, default `5`.
- `KAIWU_DB_READ_TIMEOUT`: optional integer seconds, default `30`.
- `KAIWU_DB_WRITE_TIMEOUT`: optional integer seconds, default `30`.

`kaiwuback/server/config.py` may load `kaiwuback/.env.local` and `kaiwuback/.env`, but system environment variables must keep priority.

### 4. Validation & Error Matrix

- Missing MySQL env values -> `DB_CONFIG` uses non-secret defaults; MySQL-dependent calls may fail if credentials are required.
- Invalid `KAIWU_DB_PORT` -> config import raises `ValueError` with the variable name.
- MySQL unavailable -> `EventStore` may fall back to memory for task events; conversation persistence still requires MySQL.
- Real password/API key in source, docs, logs, or commits -> forbidden; move it to ignored `.env` / `.env.local` or the process environment.

### 5. Good/Base/Bad Cases

- Good: deployment sets all `KAIWU_DB_*` values through environment variables or an ignored env file.
- Base: local task API development omits credentials; event store can use its memory fallback when MySQL is unavailable.
- Bad: `DB_CONFIG = {"user": "root", "password": "password"}` or any real team credential in code.

### 6. Tests Required

- Backend syntax: `python -m compileall kaiwuback/server`.
- Config smoke: set temporary `KAIWU_DB_*` variables and assert `DB_CONFIG` reflects them without printing secrets.
- Secret scan: search source for hardcoded MySQL passwords before finishing.

### 7. Wrong vs Correct

#### Wrong

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "password",
    "database": "kaiwu",
}
```

#### Correct

```python
DB_CONFIG = {
    "host": os.getenv("KAIWU_DB_HOST", "localhost"),
    "port": _env_int("KAIWU_DB_PORT", 3306),
    "user": os.getenv("KAIWU_DB_USER", ""),
    "password": os.getenv("KAIWU_DB_PASSWORD", ""),
    "database": os.getenv("KAIWU_DB_NAME", "kaiwu"),
    "charset": os.getenv("KAIWU_DB_CHARSET", "utf8mb4"),
}
```

---

## Stores

### Conversations

Conversation data is stored in MySQL tables named `conversations` and `messages`, and each saved conversation also writes a markdown copy under `MD_STORE`.

Local pattern:

- `save_conversation()` inserts one conversation row, inserts all message rows, writes a markdown file, then updates `md_file_path`.
- `append_conversation_messages()` appends messages without deleting existing history.
- `update_conversation_messages()` fully replaces an existing conversation's messages.
- `delete_conversation()` deletes the markdown file if present before deleting the database row.

### Agent Tasks And Events

Task data is stored in `agent_tasks` and `agent_events`.

Local pattern:

- `EventStore.ensure_schema()` creates the task/event tables if needed.
- `EventStore.create_task()` stores the normalized task input as JSON.
- `EventStore.write_event()` assigns monotonically increasing per-task `seq` values.
- `TaskService.stream_events()` streams events ordered by `seq`.

The `EventStore` in-memory fallback exists only so local development can boot when MySQL is unavailable. Do not use it as a product persistence strategy.

### Project Library Metadata

Project folder/file/image metadata is stored in MySQL tables named `project_folder_metadata`, `project_file_metadata`, and `project_image_metadata`. Legacy JSON sidecars remain as migration input and local fallback, but new code should call `server.persistence.project_metadata` rather than reading those JSON files directly.

---

## Query And Transaction Patterns

Prefer SQLAlchemy Core for new database infrastructure or multi-statement logic:

```python
from server.persistence.db import transaction

with transaction() as conn:
    conn.execute(...)
```

Existing PyMySQL-style callers may keep the explicit transaction shape:

```python
db = get_db()
try:
    with db.cursor() as cur:
        cur.execute(...)
    db.commit()
finally:
    db.close()
```

Use `pymysql.cursors.DictCursor` when returning named fields to API code, as in `get_task()` and `list_conversations()`.

Use `json.dumps(..., ensure_ascii=False)` for task payloads and event payloads so Chinese business content is preserved.

---

## Schema And Migration Conventions

Core schema is owned by Alembic migrations under `kaiwuback/alembic/versions/`.

When changing schema:

- Add a new Alembic revision; do not add new runtime `CREATE TABLE` code.
- Update manual SQL references under `docs/sql/` when useful for operators.
- Keep `agent_events` uniquely indexed by `(task_id, seq)`.
- Keep `agent_tasks` indexed by conversation, status, and update time.
- Keep project metadata keyed by stable folder names and filenames; display names are metadata, not identity.
- Preserve `utf8mb4` character set and collation for Chinese content.
- Keep baseline migrations non-destructive when they may run against existing developer or production data.

---

## Naming Conventions

- Tables use lowercase plural nouns: `conversations`, `messages`, `agent_tasks`, `agent_events`.
- Project metadata tables use explicit domain names: `project_folder_metadata`, `project_file_metadata`, `project_image_metadata`.
- Columns use lowercase snake_case: `conversation_id`, `message_count`, `created_at`, `updated_at`.
- Index names should describe table and fields, such as `idx_agent_events_task`.
- Foreign keys should be explicit when persistence depends on cascade behavior, as in `fk_agent_events_task`.

---

## Sensitive Data

Do not store API keys or external provider tokens in database rows, markdown exports, event payloads, or log messages.

`docs/specs/Spec-006-API密钥管理(绝对不做).md` is the source of truth for secret handling. API keys currently use environment variables loaded from `kaiwuback/.env`; never add real keys to source code or committed docs.

---

## Common Mistakes

- Writing task-visible SSE output without first persisting an `agent_events` row.
- Updating conversation state both from the frontend and backend for the same task. For task-driven conversations, backend `AgentRuntime` is the save owner and the frontend listens for `conversation_saved`.
- Forgetting to close DB connections in `finally`.
- Changing task statuses without `require_transition()`.
- Treating the memory fallback as equivalent to MySQL persistence.
- Changing schema without an Alembic revision.
- Reintroducing `SELECT MAX(seq) + 1` for event sequence allocation.
- Updating MySQL project metadata without mirroring the sidecar fallback map.
