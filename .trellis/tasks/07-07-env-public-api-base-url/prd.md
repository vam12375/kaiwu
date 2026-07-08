# 统一前后端公开地址配置

## Goal

将项目中指向后端服务的硬编码 `http://localhost:5001` 收敛到环境变量和统一配置入口，避免部署后用户浏览器请求自己电脑的 localhost，同时保持本地开发默认可用。

## Requirements

* 前端所有 API 请求统一通过 `API_BASE_URL` 或基于它的 API helper 发起。
* 后端所有返回给前端的项目文件、项目图片公开 URL 统一使用 `PUBLIC_BASE_URL`。
* 代码未配置环境变量时使用相对/同源 URL，避免生产漏配时回退到用户电脑的 localhost。
* `.env.example` 保留本地开发示例值，便于前后端分端口开发时复制到本地 `.env.local`。
* `.env.example` 补充 `PUBLIC_BASE_URL`，说明生产环境应配置为部署域名。
* 不处理第三方模型 API 地址、数据库 localhost、文档/测试示例中的 localhost。

## Acceptance Criteria

* [x] `kaiwu/src` 生产代码中没有 `http://localhost:5001` API 请求或默认回退。
* [x] `routes_files.py` 返回的 `project-files`、`project-images` URL 使用后端公开基础地址配置。
* [x] `runtime.py` 生成的图片事件 URL 使用后端公开基础地址配置。
* [x] `python -m compileall kaiwuback/server` 通过。
* [x] `npm run build` 通过。

## Definition of Done

* 前后端配置入口清晰，后续新增请求不需要复制 host 字符串。
* 变更范围仅限地址配置和直接相关调用点。
* 已确认不会把 API key、token、密码写入源码。

## Technical Approach

前端复用现有 `src/api/client.ts` 的 `API_BASE_URL`，补齐 `App.tsx` 和 `ConversationPanel.tsx` 中的散落 fetch。后端在 `server.config` 中新增 `PUBLIC_BASE_URL`，并提供生成公开 URL 的小工具，供文件路由和任务运行时复用。

## Decision (ADR-lite)

**Context**: 浏览器端不能收到指向 `localhost` 的生产 URL，否则用户环境会把请求打到自己的电脑。

**Decision**: 前端使用 `VITE_API_BASE_URL`，后端使用 `PUBLIC_BASE_URL`；未配置时使用相对/同源 URL，localhost 仅出现在环境变量示例中。

**Consequences**: 部署时建议在后端环境中设置 `PUBLIC_BASE_URL=https://<domain>`，前端构建时设置 `VITE_API_BASE_URL=https://<domain>` 或对应 API 网关地址。若前后端同源部署，可不设置前端变量，浏览器会请求同源 `/api`。

## Out of Scope

* 不改数据库主机等内部服务配置的默认 localhost。
* 不重构所有 API helper，只修复当前硬编码和直接相关的同类调用。
* 不修改历史任务 PRD 或 Trellis spec 中的示例 URL。

## Technical Notes

* 相关前端文件：`kaiwu/src/App.tsx`、`kaiwu/src/features/chat/ConversationPanel.tsx`、`kaiwu/src/api/client.ts`。
* 相关后端文件：`kaiwuback/server/config.py`、`kaiwuback/server/api/routes_files.py`、`kaiwuback/server/agent/runtime.py`。
* 代码搜索排除了 `*.bak`、`project-files/`、`project-images/`。
* 当前仓库没有 `docs/specs/` 目录，冻结文档无法读取；本次按 `.trellis/spec` 中的前后端契约执行。
