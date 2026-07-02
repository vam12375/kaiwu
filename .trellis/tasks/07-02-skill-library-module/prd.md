# brainstorm: 完善技能库功能模块

## Goal

完善 Kaiwu 项目的技能库功能模块，让多人协作团队可以围绕技能、能力模板或可复用工作流进行维护、浏览和使用，并与现有前后端架构保持一致。

## What I already know

* 用户希望开始完善“技能库”功能模块。
* 项目是多人合作项目，需要任务和决策沉淀到 Trellis。
* 前端位于 `kaiwu/`，后端位于 `kaiwuback/`。
* 新 AI 对话流程应走 `/api/tasks` 与 `/api/tasks/{id}/events`，不要在 `/api/chat` 增加新业务逻辑。
* 前端已有技能库页面：`kaiwu/src/features/layout/MainStage.tsx` 支持“技能市场 / 已安装”两个视图。
* 技能详情、安装、管理、自定义技能弹窗在 `kaiwu/src/features/layout/AppModals.tsx`，但多数按钮还只是 UI 占位。
* 静态市场数据在 `kaiwu/src/data.ts`，已安装列表目前也是静态常量。
* 后端已有 `kaiwuback/server/api/routes_skills.py`，提供 `GET /api/skills` 和 `GET /api/skills/{skill_id}`。
* 仓库内存在外部技能包 `kaiwuback/skills-files/心理登月`。
* `server.config.SKILLS_DIR` 当前写死为 `/Users/wangzijian/Desktop/kaiwu_All/kaiwuback/skills-files`，在多人协作和 Windows 工作区中不可移植。
* AGENTS 提到的 `docs/specs/` 与 `docs/00-文件索引-开发速查.md` 当前不在仓库里；现有可读规范主要来自 `.trellis/spec/`。

## Assumptions (temporary)

* “技能库”可能已经存在部分前端页面或后端接口，需要先盘点现状再决定 MVP。
* 技能库可能需要支持技能的展示、分类、搜索、使用入口，以及未来的团队维护能力。
* 本任务优先完善用户可见的核心流程，不一次性做完整权限、审核、版本管理等复杂协作能力。
* 第一版应优先解决“看得到、搜得到、装得上、状态保得住”，再考虑多人审核、版本发布、权限策略。

## Open Questions

* None for MVP.

## Requirements (evolving)

* 复用项目既有前后端架构和 Trellis 规范。
* 保持已有 AI 对话、会话保存、归档等硬约束不被破坏。
* MVP 方向为“先做可用技能库”：浏览、搜索、安装、管理、自定义技能可用。
* 后端技能目录应支持环境变量覆盖，并默认读取仓库内 `kaiwuback/skills-files`。
* 技能列表应返回足够前端展示和筛选的结构化字段。
* 前端技能库应支持真实搜索、分类筛选、已安装视图，以及安装/启用/卸载状态。
* 自定义技能至少应在第一版中能创建并进入已安装列表。

## Acceptance Criteria (evolving)

* [x] 明确技能库 MVP 范围和非目标。
* [x] 识别并复用现有技能库相关代码、文档和数据模型。
* [ ] `GET /api/skills` 在当前仓库环境可读到 `kaiwuback/skills-files` 下的技能。
* [ ] 技能库页面搜索和分类筛选可用。
* [ ] 安装、启用、卸载、自定义技能操作有状态反馈，刷新后不丢失本地用户选择。
* [ ] 若进入实现，前端构建和后端语法检查通过。

## Technical Approach

* Backend: keep `routes_skills.py` as the thin API boundary, improve metadata extraction, path portability, and response fields without adding database migrations.
* Frontend: add local skill state in `App.tsx`, pass typed handlers into `MainStage` and `AppModals`, and persist installed/enabled/custom skills in `localStorage`.
* UI: reuse the existing skill library cards and modals; convert placeholder buttons into working actions.

## Decision (ADR-lite)

**Context**: The existing skill library UI is mostly present, but actions are static and backend skill discovery depends on a developer-specific absolute path.

**Decision**: Build the first MVP as a user-level usable skill library with repository-backed external skills and browser-local install/manage/custom state.

**Consequences**: This gives the product a usable workflow quickly while deferring team-wide persistence, review, versioning, and permission models to a later task.

## Implementation Results

* `GET /api/skills` now reads the repository-local `kaiwuback/skills-files` directory by default and supports `KAIWU_SKILLS_DIR` override.
* Backend skill parsing returns structured fields for display, filtering, source, version, entry file, and full skill content.
* Frontend skill library supports browsing, category filtering, real search input, installed view, install, enable/disable, uninstall, and custom skill creation.
* Installed/enabled/custom skill choices persist in browser `localStorage`.
* Verification passed: `python -m compileall kaiwuback/server`.
* Verification passed: `npm run build` in `kaiwu/`.

## Definition of Done (team quality bar)

* Tests added/updated where appropriate.
* Lint / type-check / CI green for touched areas.
* Docs/notes updated if behavior changes.
* Rollout/rollback considered if risky.

## Out of Scope (explicit)

* 未经确认前，不引入复杂权限审批、商业化计费或第三方插件市场。
* 未经确认前，不引入数据库迁移或多人权限模型。
* 不从 `*.bak`、`project-files/`、`project-images/` 学习当前架构。

## Technical Notes

* Relevant frontend files: `kaiwu/src/App.tsx`, `kaiwu/src/features/layout/MainStage.tsx`, `kaiwu/src/features/layout/AppModals.tsx`, `kaiwu/src/data.ts`, `kaiwu/src/types.ts`.
* Relevant backend files: `kaiwuback/server/config.py`, `kaiwuback/server/api/routes_skills.py`.
* Cross-layer flow for MVP: `skills-files/SKILL.md` -> `routes_skills.py` metadata parser -> `GET /api/skills` -> `App.tsx` state -> `MainStage` cards -> `AppModals` actions.
* Frontend state can initially use `localStorage` for user-level installed/enabled/custom skill choices to avoid DB migration in MVP.
