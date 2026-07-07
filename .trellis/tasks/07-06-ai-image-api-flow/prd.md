# 完整实现 AI 生图 API 流程

## Goal

把创造模式里的 AI 生图从旧的“先走普通对话/节点回答，再从回答里抽取图片 prompt”的模式，改成正常的任务 API 流程：前端图片模式提交结构化参数，后端直接调用 Seedream 图片生成接口，结果通过现有 SSE 事件链展示、保存会话，并按项目规则双归档。

## Requirements

- AI 生图点击后继续打开当前对话式图片生成界面，保留截图中的图片模式输入体验。
- 图片模式发送时必须走 `/api/tasks`，请求体显式标识图片生成任务，不再依赖关键词路由到 Node3.1。
- 请求体携带用户输入、图片模型、比例、分辨率、生成张数、会话 ID 等结构化字段。
- 参考图上传必须真实参与生成：前端把本地参考图读取为 `data:image/...;base64,...`，随 `/api/tasks` payload 提交，后端传给 Seedream client。
- 参考图支持单图/多图，前端和后端都限制数量与大小，避免超大任务 payload。
- 后端在任务 payload 边界规范化图片生成字段，并在 `AgentRuntime` 中直接进入图片生成分支。
- 图片生成分支直接调用 Seedream API wrapper，不再让 LLM 生成内嵌 prompt，不再调用 `_extract_logo_prompts()` 作为 AI 生图入口。
- 每张成功图片通过 `image` SSE 事件返回，前端使用现有 `agentEventReducer` 渲染图片网格。
- 生成图片保存到 `project-images/`，并同步归档到项目库的 `图片库` 和 `AI 对话产出`。
- 任务完成后由后端保存对话，并通过 `conversation_saved` 更新前端当前会话和历史列表。
- 图片生成错误以任务事件呈现，错误信息截断且不暴露密钥、请求头或完整 provider payload。
- 所有读写保持 UTF-8 编码。

## Acceptance Criteria

- [ ] 在 AI 生图模式输入文字并发送时，前端请求 `/api/tasks` 的 payload 包含图片任务类型和结构化图片参数。
- [ ] 后端图片任务不触发普通 LLM 文本生成，也不依赖从 AI 文本中抽取 prompt。
- [ ] SSE 事件序列能正常驱动 UI：`task_created/analyzing/image_gen_start/progress/image/conversation_saved/done`。
- [ ] 生成结果在当前对话中显示图片，并且历史会话重新加载后图片仍可渲染。
- [ ] 项目图片列表能刷新并显示新生成图片。
- [ ] 普通对话、AI 视频、AI 编程仍使用普通对话按钮和普通任务路径。
- [ ] 对话重命名功能不受影响。
- [ ] `python -m compileall kaiwuback/server` 通过。
- [ ] `npm run build` 在 `kaiwu/` 下通过。

## Definition of Done

- 前后端实现完成，且没有引入 `/api/chat` 新调用。
- 任务/SSE 事件流继续由 `useSseEvents -> useAgentTask -> agentEventReducer / agentTaskController -> UI` 处理。
- 后端路由保持薄层，业务逻辑在 payload builder、runtime、Seedream client 等对应层内。
- 不提交密钥、token、密码或真实 provider 响应全文。
- 删除或绕开与新 AI 生图入口无关的旧内嵌 prompt 依赖。

## Technical Approach

前端在 `ConversationPanel` 中把图片模型、分辨率和参考图状态上提到 `useConversationTask` 可见的位置，发送时把图片模式转换为结构化任务字段。后端在 `context_builder.py` 规范化这些字段，并在 `AgentRuntime._execute()` 的早期分支处理 `task_type == "image_generation"`：直接调用图片生成 helper，逐张 emit `image` 事件，保存图片和对话，然后完成任务。

MVP 实现文生图和参考图生成的正式 API 调用流程。参考图以 Base64 data URL 随任务提交，不依赖公网图片托管，也不改变当前 AI 生图页面布局。

## Decision (ADR-lite)

**Context**: 现有后端只在 `node1.5/node3.1` 完成普通 LLM 回答后，从回答内容里抽取图片 prompt 再调 Seedream，这导致 AI 生图入口不是真正的 API 图片任务。

**Decision**: 为 `/api/tasks` 增加图片任务类型和结构化图片参数，图片模式直接走图片任务分支。旧节点内的 logo/配图生成能力可以保留给节点工作流，但不再作为 AI 生图入口的主路径。

**Consequences**: 前端和后端的职责更清晰，图片生成不再依赖 LLM 输出格式；后续支持参考图/图生图时，只需要扩展图片任务 payload 和 Seedream client，而不需要改普通对话节点。

## Out of Scope

- 不实现 AI 视频生成。
- 不实现 AI 编程工作台。
- 不新增积分扣费系统。
- 不接入新的第三方图片服务。
- 不实现蒙版局部重绘、画布涂抹或历史图片二次编辑。

## Technical Notes

- 相关前端文件：`kaiwu/src/api/tasks.ts`、`kaiwu/src/hooks/useConversationTask.ts`、`kaiwu/src/hooks/useAgentTask.ts`、`kaiwu/src/hooks/agentEventReducer.ts`、`kaiwu/src/hooks/agentTaskController.ts`、`kaiwu/src/features/chat/ConversationPanel.tsx`、`kaiwu/src/App.tsx`。
- 相关后端文件：`kaiwuback/server/agent/context_builder.py`、`kaiwuback/server/agent/runtime.py`、`kaiwuback/server/llm_client/seedream.py`、`kaiwuback/server/utils/file_io.py`。
- 项目规范：`.trellis/spec/frontend/state-management.md`、`.trellis/spec/frontend/hook-guidelines.md`、`.trellis/spec/frontend/quality-guidelines.md`、`.trellis/spec/backend/error-handling.md`、`.trellis/spec/backend/quality-guidelines.md`。
- `docs/specs/` 在当前工作树不存在，已记录为缺失；本任务以 `.trellis/spec/` 和现有代码为准。
