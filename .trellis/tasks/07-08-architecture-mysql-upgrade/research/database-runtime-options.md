# Database and Runtime Upgrade Options

## Research Question

How should Kaiwu upgrade its current direct PyMySQL persistence and task-event runtime without destabilizing the existing FastAPI + React task/SSE flow?

## Sources Consulted

* SQLAlchemy 2.0 documentation via Context7: pooling, MySQL `pool_recycle`, `QueuePool`, explicit transaction scopes.
* Alembic documentation via Context7: migration environment structure, revision scripts, version table, upgrade/downgrade functions.
* Local repo files:
  * `kaiwuback/server/persistence/database.py`
  * `kaiwuback/server/agent/event_store.py`
  * `kaiwuback/server/agent/task_service.py`
  * `kaiwuback/server/agent/runtime.py`
  * `kaiwuback/server/api/routes_files.py`
  * `docs/sql/2026-07-01-agent-tasks-events.sql`
  * `README.md`

## Current Local Constraints

* The backend currently uses direct PyMySQL access through `get_db()`.
* Most database calls expect a PyMySQL-compatible connection and cursor API.
* Task/event tables are auto-created at runtime by `EventStore.ensure_schema()`.
* Conversation tables are documented in README, not managed by runtime schema creation or migrations.
* Frontend task rendering depends on persisted `agent_events` being streamed in `seq` order.
* Project file/image metadata still lives in JSON sidecar files, while task events and conversations live in MySQL.

## Comparable Approaches

### Approach A: Conservative PyMySQL Infrastructure Upgrade

Keep PyMySQL as the caller-facing database API. Add a small internal DB module with:

* connection pooling compatible with PyMySQL callers,
* transaction/context helpers,
* explicit connect/read/write timeouts,
* SQL migrations kept as versioned files,
* improved task event sequence allocation.

Pros:

* Lowest blast radius.
* Fits existing code and Trellis database guidelines.
* Can be implemented in stages.
* Avoids converting query code to SQLAlchemy immediately.

Cons:

* Requires maintaining a small local infrastructure layer.
* Less feature-rich than SQLAlchemy/Alembic long term.

### Approach B: SQLAlchemy Core + Alembic Foundation

Introduce SQLAlchemy Core for pooling, transactions, and SQL execution, plus Alembic for migrations. Keep raw SQL where useful, but route through SQLAlchemy engines/connections.

Pros:

* Mature pooling and migration story.
* Clear long-term path for schema evolution.
* Alembic gives revision ordering and version tracking.

Cons:

* Higher first-change blast radius.
* Existing PyMySQL cursor code must be adapted or bridged.
* Adds dependencies and project conventions at once.

### Approach C: Full ORM and Runtime Refactor

Introduce SQLAlchemy ORM models for tasks, events, conversations, messages, artifacts, project files, then refactor runtime around repositories/services.

Pros:

* Cleanest long-term domain model.
* Easier to extend to users, tenants, permissions, artifacts, and search.

Cons:

* Too large for one safe pass.
* High regression risk around task/SSE and conversation saving.

## Recommended Direction

Use Approach A for the first implementation phase, while designing the migration directory and DB helper names so Approach B can be adopted later.

The first phase should focus on:

* reliable connection lifecycle,
* explicit transactions,
* versioned SQL migration files,
* production-safe `agent_events.seq` allocation,
* schema/index improvements,
* preserving existing API and frontend behavior.

## Follow-Up Candidate Phases

* Phase 2: move project file/image metadata sidecars into MySQL.
* Phase 3: introduce artifact tables and link generated files/images to tasks, messages, and conversations.
* Phase 4: split task execution into a worker queue while SSE remains a read-only event stream.
