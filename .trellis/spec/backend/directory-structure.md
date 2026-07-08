# Backend Directory Structure

> How `kaiwuback/` backend code is organized.

---

## Runtime Shape

`kaiwuback/main.py` is the FastAPI entrypoint. It should stay small: create `app`, install CORS, register route modules, expose `/api/health`, and keep the deprecated `/api/chat` compatibility endpoint.

Reference files:

- `kaiwuback/main.py`
- `kaiwuback/server/api/routes_tasks.py`
- `kaiwuback/server/agent/runtime.py`
- `docs/specs/Spec-007-Task-Agent-Runtime.md`

Do not move new business logic into `main.py` or `/api/chat`. New frontend-facing AI work goes through `/api/tasks` and task events.

---

## Directory Layout

```text
kaiwuback/
├── main.py                         # FastAPI app wiring only
├── requirements.txt
├── report_templates/               # HTML report templates and logo assets
├── skills-files/                   # External skill packs shown by /api/skills
└── server/
    ├── api/                        # Thin FastAPI route registration modules
    ├── agent/                      # TaskService, AgentRuntime, EventStore, state machine
    ├── intent/                     # Intent recognition, follow-up detection, dependency rules
    ├── llm_client/                 # LLM provider registry and provider wrappers
    ├── nodes/                      # Node metadata registry and system prompts
    ├── orchestrator/               # Legacy LLM/report/export orchestration bridges
    ├── persistence/                # Conversation database access and markdown export
    ├── tools/                      # Tool registry and concrete tool adapters
    └── utils/                      # File, markdown, SVG, session, and compatibility helpers
```

Generated user artifacts are stored outside source code:

- `kaiwuback/conversations/`
- `kaiwuback/project-files/`
- `kaiwuback/project-images/`

These folders are data outputs, not coding examples.

---

## API Modules

Route files use `register_*_routes(app)` and keep request validation near the HTTP boundary.

Current examples:

- `server/api/routes_tasks.py` registers task create/debug/events/cancel/retry endpoints.
- `server/api/routes_files.py` registers project file, image, upload, and download endpoints.
- `server/api/routes_conv.py` registers conversation CRUD and manual save endpoints.
- `server/api/routes_skills.py` reads skill metadata from `SKILLS_DIR`.

When adding an endpoint:

- Put it in the closest existing `routes_*.py` file, or create a new `routes_<domain>.py`.
- Register the new route module once in `main.py`.
- Keep orchestration in `server/agent/`, `server/orchestrator/`, `server/tools/`, or `server/utils/`, not inside the route function.

---

## Scenario: Project Image Library Metadata

### 1. Scope / Trigger

- Trigger: any change to generated project images, WebP previews, `GET /api/project-images`, or frontend project image preview fields.
- This is a cross-layer contract because `AgentRuntime` writes image metadata, `routes_files.py` serializes it, and the frontend `ProjectImage` type renders it.

### 2. Signatures

- `GET /api/project-images` -> `list[ProjectImageSummary]`
- `GET /project-image-previews/{filename:path}` -> WebP preview bytes or `404`.
- `save_image_to_library(image_url: str, style: str, metadata: dict[str, Any] | None = None) -> str`
- `ensure_project_image_webp_preview(image_path: Path) -> Path | None`
- Sidecar storage: `kaiwuback/project-images/.image-meta.json`, keyed by saved image filename.
- Preview storage: `kaiwuback/project-image-previews/<original-filename>.webp`.

### 3. Contracts

`ProjectImageSummary` required response fields:

- `name: string` - actual filename from `IMG_STORE`.
- `url: string` - display URL. Prefer local `/project-image-previews/<filename>.webp` when a WebP preview exists; otherwise fall back to `/project-images/<filename>`.
- `original_url: string` - original local `/project-images/<filename>` URL used by download actions.
- `preview_url: string` - same display URL as `url`; present for explicit consumers.
- `size: number` - file size from the filesystem.
- `modified: string` - filesystem modified time formatted as `YYYY-MM-DD HH:mm`.

Optional metadata fields:

- `prompt: string`
- `style: string`
- `model: string`
- `ratio: string`
- `resolution: string`
- `source: string`
- `reference_count: number`
- `created_at: string`

Core filesystem fields (`name`, `url`, `size`, `modified`) must win over metadata fields when merging. Metadata is display-only and must not contain API keys, provider tokens, or raw request headers.

For generated PNG/JPG/JPEG files, create WebP previews with Pillow. Do not list preview files as project images, and do not replace or delete originals. SVG/GIF/WebP originals may fall back to original URLs.

### 4. Validation & Error Matrix

- Missing `.image-meta.json` -> return image entries with required fields only.
- Malformed `.image-meta.json` -> log a short `[IMG] Metadata read failed` message and return required fields only.
- Missing metadata for a filename -> return required fields only.
- Unsupported file suffix in `IMG_STORE` -> skip it.
- Pillow missing or preview generation fails -> log `[IMG] WebP preview...` and return the original image URL as `url`.
- Preview route path traversal -> `404 {"error": "not found"}`.
- Preview URL passed to `/api/download-image` -> resolve back to the original image path when possible.
- Corrupt metadata that attempts to override `name`, `url`, `size`, or `modified` -> ignore the override by merging filesystem fields last.

### 5. Good/Base/Bad Cases

- Good: a newly generated PNG appears with a WebP `url`, an original `original_url`, and metadata fields such as `prompt`, `ratio`, `resolution`, and `source`.
- Base: an older image has no metadata and still previews with filename, time, and size.
- Base: Pillow is unavailable, so the API returns the original URL for display and download still works.
- Bad: route code reads metadata once per image or lets metadata override the local file URL.
- Bad: frontend displays and downloads from the same `url` after `url` has become a WebP preview URL.

### 6. Tests Required

- Backend syntax: `python -m compileall kaiwuback/server`.
- Frontend type/build: `Set-Location kaiwu; npm run build` when `ProjectImage` fields or preview UI changes.
- API smoke: `GET http://localhost:5001/api/project-images` returns `200` and JSON parse succeeds.
- WebP smoke: create a temporary PNG under `IMG_STORE`, call `ensure_project_image_webp_preview()`, assert the `.webp` file exists, then delete both files.
- Manual UI smoke: open project library -> 图片库, click an image, confirm the app opens the preview modal instead of a new browser tab.

### 7. Wrong vs Correct

#### Wrong

```python
images.append({
    "name": f.name,
    "url": original_url,
    **metadata,  # metadata can override name/url
})
```

#### Correct

```python
display_url = project_image_display_url(f.name)
original_url = project_image_original_url(f.name)
images.append({
    **metadata,
    "name": f.name,
    "url": display_url,
    "original_url": original_url,
    "preview_url": display_url,
    "size": f.stat().st_size,
    "modified": modified,
})
```

---

## Scenario: Public File And Image URLs

### 1. Scope / Trigger

- Trigger: any change to URLs returned for `project-files`, `project-images`, generated image SSE events, frontend API base configuration, or deployment env wiring.
- This is a cross-layer contract because the backend serializes URLs, task events persist them into conversations, and the browser fetches/renders/downloads those URLs.

### 2. Signatures

- Backend env: `PUBLIC_BASE_URL=<optional absolute origin>`.
- Frontend env: `VITE_API_BASE_URL=<optional absolute origin>`.
- Backend helper: `public_url(path: str) -> str`.
- Frontend helper: `API_BASE_URL` from `src/api/client.ts`.

### 3. Contracts

- `PUBLIC_BASE_URL` is optional. When empty, `public_url("/project-images/a.png")` returns `/project-images/a.png` for same-origin deployments.
- When `PUBLIC_BASE_URL=https://example.com`, `public_url("/project-images/a.png")` returns `https://example.com/project-images/a.png`.
- `VITE_API_BASE_URL` is optional. When empty, frontend API calls use same-origin `/api/...`; when set, all API/SSE/download calls use that origin.
- Runtime source must not hardcode `http://localhost:5001`; localhost belongs only in `.env.example` or local `.env.local` files.

### 4. Validation & Error Matrix

- Empty `PUBLIC_BASE_URL` + same-origin deployment -> return relative URLs.
- Empty `PUBLIC_BASE_URL` + split-origin local development -> images/files require local `.env.local` override.
- Public-domain `/project-images/...` download URL matching `PUBLIC_BASE_URL` -> resolve from `IMG_STORE` directly.
- Public-domain non-image API URL passed to `/api/download-image` -> reject with `400 {"error": "unsupported image url"}`.

### 5. Good/Base/Bad Cases

- Good: production sets `PUBLIC_BASE_URL=https://app.example.com` and users receive public file/image URLs.
- Base: same-origin deployment leaves both env vars empty and uses relative `/api` plus `/project-images` paths.
- Bad: frontend or backend source code embeds `http://localhost:5001`, causing a deployed browser to call the user's own machine.

### 6. Tests Required

- `rg "localhost:5001" kaiwu/src kaiwuback/server kaiwuback/main.py -g "!*.bak"` returns no production-code matches.
- `python -m compileall kaiwuback/server` passes after backend URL changes.
- `npm run build` passes after frontend API base changes.
- Smoke `public_url("/project-images/demo.png")` with empty and configured `PUBLIC_BASE_URL`.

### 7. Wrong vs Correct

#### Wrong

```python
"url": f"http://localhost:5001/project-images/{filename}"
```

#### Correct

```python
"url": public_url(f"/project-images/{quote(filename, safe='')}")
```

## Scenario: External Skill Library API

### 1. Scope / Trigger

- Trigger: any change to `kaiwuback/skills-files/`, `server.config.SKILLS_DIR`, or `server/api/routes_skills.py`.
- This is a cross-layer contract because the frontend skill library renders and filters fields returned by `/api/skills`.

### 2. Signatures

- `GET /api/skills` -> `list[SkillSummary]`
- `GET /api/skills/{skill_id}` -> `SkillSummary | {"error": "Skill not found"}`
- `SKILLS_DIR = Path(os.getenv("KAIWU_SKILLS_DIR", <repo>/kaiwuback/skills-files)).expanduser()`

### 3. Contracts

`SkillSummary` response fields:

- `id: string` - stable directory id under `SKILLS_DIR`
- `name: string` - display name from frontmatter `display_name`/`name`, fallback to directory name
- `description: string` - frontmatter `description_zh`/`description`, body summary, or name
- `category: string` - frontmatter `category`, fallback `方法论`
- `version: string` - optional frontmatter value, empty string when absent
- `source: "external"`
- `entry_file: string` - path relative to `SKILLS_DIR`
- `full_content: string` - raw skill markdown shown in the frontend detail modal

### 4. Validation & Error Matrix

- `SKILLS_DIR` missing -> `GET /api/skills` returns `[]`, not a 500.
- Skill directory has no `SKILL.md` or top-level `.md` fallback -> skip that directory.
- Unknown `skill_id` -> `{"error": "Skill not found"}` with status 404.
- Invalid or partial frontmatter -> parse what is present and fall back field-by-field.

### 5. Good/Base/Bad Cases

- Good: `skills/<name>/SKILL.md` has frontmatter; API returns structured metadata plus full content.
- Base: only `<skill_dir>/<name>.md` exists; API still returns a usable skill card.
- Bad: hardcoding a developer-specific absolute path; this breaks Windows and multi-developer checkouts.

### 6. Tests Required

- Backend smoke: import `list_external_skills()` and assert repository-local skills are discovered.
- Backend syntax: `python -m compileall kaiwuback/server`.
- Cross-layer smoke: frontend skill page renders at least one skill from `/api/skills` when backend is running.

### 7. Wrong vs Correct

#### Wrong

```python
SKILLS_DIR = Path("/Users/example/Desktop/kaiwuback/skills-files")
```

#### Correct

```python
SKILLS_DIR = Path(
    os.getenv("KAIWU_SKILLS_DIR", str(Path(__file__).parent.parent / "skills-files"))
).expanduser()
```

---

## Task Runtime Modules

The task pipeline is the current backend backbone:

- `server/agent/task_service.py` creates, starts, cancels, retries, and streams tasks.
- `server/agent/runtime.py` performs routing, Node execution, event emission, image generation, export bridges, and conversation saving.
- `server/agent/event_store.py` persists `agent_tasks` and `agent_events`, with an in-memory fallback for local development.
- `server/agent/state_machine.py` defines valid task status transitions.
- `server/agent/context_builder.py` normalizes HTTP request data into a task payload.

New task-visible behavior must emit events through `EventStore.write_event()` before the frontend sees it. The SSE endpoint reads stored events; it is not the business executor.

---

## Node And Intent Modules

Node changes are multi-file changes:

- Add/edit Node metadata and prompts in `server/nodes/prompts.py`.
- Keep structured metadata access in `server/nodes/registry.py`.
- Update trigger words, dependency rules, and prerequisite indicators in `server/intent/recognizer.py`.
- Keep behavior aligned with `docs/specs/Spec-001-Node拆分与依赖链.md` and `docs/specs/Spec-003-Intent识别策略.md`.

Node IDs are stable product contracts: `node0`, `node1`, `node1.5`, `node2`, `node3`, `node3.1`, `node4`, `node5`, `export`, `summary`, and `fallback`.

---

## Capability And Utility Boundaries

Use the local capability boundaries before adding new helpers:

- LLM providers: `server/llm_client/router.py` and provider wrappers.
- Future external tools: `server/tools/registry.py` with `ToolSpec`.
- File generation and dual archive: `server/utils/file_io.py`.
- Conversation CRUD: `server/persistence/database.py`.
- Markdown and report rendering: `server/utils/markdown.py`, `server/reports.py`, `server/utils/handbook_renderer.py`.

`server/utils/common.py` is a compatibility re-export layer. Do not add new implementation there; add implementation to the real utility module and only re-export if old imports require it.

---

## Naming Conventions

- Python modules and functions use `snake_case`.
- Route modules use `routes_<domain>.py`.
- Registration functions use `register_<domain>_routes(app)`.
- Task statuses use lowercase strings from `state_machine.py`.
- SSE event types use lowercase snake_case, matching `docs/specs/Spec-002-SSE事件协议.md`.
- Project library folder names must match the existing Chinese folder names exactly, especially `AI 对话产出`.

---

## Current Anti-Patterns

- Do not learn architecture from `kaiwu/src/App.tsx.bak` or any `*.bak` file.
- Do not add new business behavior to `/api/chat`; it is a compatibility bridge.
- Do not bypass task events by streaming direct ad hoc SSE frames from new code.
- Do not add new helpers to `server/utils/common.py` as a dumping ground.
- Do not remove the dual-archive behavior for AI-generated files.
