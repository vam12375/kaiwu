# Spec-007: Task-driven Agent Runtime 架构

| 字段 | 内容 |
|------|------|
| Spec 类型 | 确定落地 |
| 冻结状态 | 已冻结 |
| 创建日期 | 2026-07-01 |
| 关联模块 | `server/agent/*`, `server/api/routes_tasks.py`, `src/hooks/useAgentTask.ts`, `src/hooks/useConversationTask.ts`, `src/hooks/useConversation.ts`, `src/hooks/agentTaskController.ts`, `src/features/chat/*`, `src/features/layout/*` |
| 关联 Spec | Spec-001（Node拆分）, Spec-002（SSE事件协议）, Spec-003（Intent路由） |

## 一、背景与现存问题

原实现以 `/api/chat` 为中心：一次请求里同时完成意图识别、Node 执行、SSE 推流、图片生成、文件归档和对话保存。这个模式适合原型，但任务一旦耗时、用户刷新页面、网络断开或后端需要重试，执行状态就不可恢复。

## 二、最终实现方案

引入任务驱动架构：

```
前端 UI
  -> API 层：tasks / events / conversations / files / skills
  -> Task Service：创建、取消、重试、查询
  -> Agent Runtime：状态机、Node 路由、执行编排
  -> Node Executor：逐步迁移到独立执行器
  -> 能力层：LLM Gateway / Tool Registry / Artifact Service
  -> 数据层：MySQL agent_tasks / agent_events / project files
```

新增接口：

| 方法 | 路径 | 职责 |
|------|------|------|
| POST | `/api/tasks` | 创建并启动任务 |
| GET | `/api/tasks/{id}` | 查询任务调试闭环：`status`, `node_id`, `conversation_id`, `event_count`, `last_seq`, `error` |
| GET | `/api/tasks/{id}/events` | 按 seq 订阅任务事件 |
| POST | `/api/tasks/{id}/cancel` | 请求取消任务 |
| POST | `/api/tasks/{id}/retry` | 基于原输入创建重试任务 |

`/api/chat` 保留为兼容层，只负责创建任务并转发事件流，前端新代码不再直接调用它。

任务保存契约：

| 事件类型 | 触发时机 | payload |
|----------|----------|---------|
| `conversation_saved` | 后端完成对话创建或追加后 | `conversation_id`, `title`, `node_id` |

前端不得在任务发送前后调用 `/api/conversations/save` 参与同一次任务保存；它只根据 `conversation_saved` 更新当前会话 ID 和历史列表。

前端任务消费分层：

| 层 | 模块 | 职责 |
|----|------|------|
| Task API | `src/api/tasks.ts` | 创建、取消、重试任务，生成 SSE URL |
| Task Transport | `src/hooks/useAgentTask.ts` | 创建任务并订阅事件流，维护 taskId/status/events |
| Conversation Orchestration | `src/hooks/useConversationTask.ts` | 处理发送输入、追问 node、乐观消息、任务 controller、停止生成、缓存写回 |
| Conversation State | `src/hooks/useConversation.ts` | 初始化历史、加载会话、删除会话、恢复任务缓存、重置当前会话 |
| Event Controller | `src/hooks/agentTaskController.ts` | 处理 analyzing/node_selected/progress/response_start/suggestions/cancelled/error 等任务事件 |
| Event Reducer | `src/hooks/agentEventReducer.ts` | 处理 content/svg/image/file_saved/conversation_saved 等消息内容事件 |
| Chat Components | `src/features/chat/ConversationPanel.tsx`, `src/features/chat/SidebarHistory.tsx` | 展示历史列表、消息流、节点进度、建议追问、会话输入区 |
| Layout Components | `src/features/layout/AppSidebar.tsx`, `src/features/layout/MainStage.tsx`, `src/features/layout/AppModals.tsx` | 承载侧栏、主舞台页面切换、全局弹窗，避免 App 继续堆 JSX |
| UI Shell | `src/App.tsx` | 只持有顶层 UI 状态、hooks wiring 和组件挂载，通过 `useConversationTask()` 获取任务动作，通过 `useConversation()` 获取会话动作 |

## 三、做出该选择的底层原因

**业务原因**：Agent 输出可能持续 30-120 秒，用户需要看到任务状态；后续还会出现排队、重试、恢复、审计等企业级诉求，单次流式请求无法承载这些生命周期。

**技术原因**：
1. 任务状态和事件持久化后，SSE 端点只负责读取事件，不再耦合业务执行。
2. `AgentRuntime` 只负责生命周期和编排，Node 业务能力可以逐步迁入 executor。
3. `ToolRegistry` 统一声明工具名、schema、权限、超时、重试和审计字段，避免文件、图片、报告能力继续散落在主流程。

## 四、落地硬性约束

- 任务状态固定为：`created -> queued -> routing -> running -> streaming -> saving -> completed`，失败和取消进入 `failed/cancelled`。
- 所有前端可见事件必须先写入 `agent_events`，SSE 订阅接口只读取事件并推送。
- 新前端不得直接解析 `/api/chat` 响应，应通过 `useConversationTask()` 触发对话任务，并由 `useAgentTask()` 消费任务状态和事件。
- 同一次 Agent 任务的对话保存唯一 owner 是后端 `AgentRuntime`，前端只接收 `conversation_saved` 事件。
- 新工具接入必须注册到 `ToolRegistry`，声明 permission、timeout、retry_policy、audit_log。
- `/api/chat` 仅作为兼容层保留，不允许继续新增业务逻辑。

## 五、功能边界

### 覆盖场景

- 单任务创建、查询、取消、重试
- 任务事件持久化和 SSE 订阅
- 旧 `/api/chat` 客户端兼容
- Node/Tool 注册表的第一层边界

### 明确不覆盖

- 不实现多 Node 并行执行
- 不实现跨进程任务队列或分布式 worker
- 不立即把所有 Node 业务逻辑迁出通用 runtime
- 不改变现有 LLM prompt 和业务输出格式

## 六、不这么做的风险

1. 继续在 `/api/chat` 中堆职责，会让路由文件重新退化成主流程上帝文件。
2. 没有事件存储，前端刷新和网络断开后无法恢复任务，也无法做审计和问题追踪。
3. 没有 Tool Registry，接入搜索、RAG、浏览器自动化等能力时会污染 Agent Runtime，长期变成网状依赖。
