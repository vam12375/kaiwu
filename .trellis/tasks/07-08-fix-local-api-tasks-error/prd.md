# 修复本地 api tasks 请求错误

## Goal

修复本地开发环境中前端调用 `POST /api/tasks` 落到 Vite 端口 `localhost:5173` 后无法正确到达后端的问题，让任务驱动对话流程在本地可用。

## Requirements

* 本地开发时，当前端使用相对路径 `/api/tasks` 时，请求应能被转发到 FastAPI 后端 `localhost:5001`。
* 保持生产环境通过 `VITE_API_BASE_URL` 配置公开 API 基础地址的能力。
* 不改变 `/api/tasks`、`/api/tasks/{id}/events` 的前后端业务协议。
* 更新前端环境变量示例，避免把 `VITE_API_BASE_URL` 指向 Vite 自身端口造成误导。

## Acceptance Criteria

* [x] Vite dev server 对 `/api` 请求有明确代理配置。
* [x] `kaiwu/.env.example` 不再建议 `http://localhost:5173/` 作为 API base URL。
* [x] `npm run build` 通过。

## Definition of Done

* 前端构建通过。
* 只修改与本地 API 请求路由相关的配置/文档示例。
* 不提交或写入任何密钥、Token、密码。

## Technical Approach

在 `kaiwu/vite.config.ts` 添加开发代理，将 `/api` 转发到 `http://localhost:5001`。保留 `src/api/client.ts` 现有行为：`VITE_API_BASE_URL` 为空时使用同源相对 URL；生产或特殊部署可显式配置 `VITE_API_BASE_URL`。

## Out of Scope

* 不修改任务运行时、SSE 解析、对话保存逻辑。
* 不新增后端业务接口。
* 不处理数据库、模型密钥或远程部署配置。

## Technical Notes

* 报错入口：`kaiwu/src/api/tasks.ts` 通过 `apiJson('/api/tasks')` 发起任务创建。
* API base URL：`kaiwu/src/api/client.ts` 从 `VITE_API_BASE_URL` 读取；为空时使用相对路径。
* 后端入口：`kaiwuback/main.py` 使用 Uvicorn 监听 `5001`。
* 前端规范：`.trellis/spec/frontend/directory-structure.md` 说明本地 split-origin 可用 `VITE_API_BASE_URL=http://localhost:5001`，源码不硬编码后端源。
