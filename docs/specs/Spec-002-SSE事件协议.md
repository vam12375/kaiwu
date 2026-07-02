# Spec-002: SSE 事件协议与前端约定

| 字段 | 内容 |
|------|------|
| Spec 类型 | 确定落地 |
| 冻结状态 | 已冻结 |
| 创建日期 | 2026-06-30 |
| 关联模块 | `main.py`（后端 emit）, `App.tsx`（前端 consume） |
| 关联 Spec | Spec-001（Node拆分）, Spec-004（会话管理） |

## 一、背景与现存问题

后端 AI 响应耗时 30-120 秒，如果采用传统 HTTP 请求-响应模式，用户在等待期间看不到任何反馈，体验极差。需要一套流式协议让前端实时展示进度、阶段切换、内容逐字输出。

## 二、最终实现方案

采用 **SSE（Server-Sent Events）**，后端通过 `StreamingResponse` 推送 JSON 事件，前端通过 `fetch + ReadableStream` 消费。

**13 种事件类型**：

| 事件类型 | 触发时机 | 前端行为 | payload 字段 |
|---------|---------|---------|-------------|
| `analyzing` | Intent识别开始 | 显示"正在分析…"加载态 | `message` |
| `node_selected` | Node匹配完成 | 显示Node名称+图标badge，切换progress阶段 | `node`, `name`, `icon` |
| `progress` | LLM生成中 | 更新进度条百分比+步骤文案 | `percent`, `message` |
| `response_start` | LLM开始输出 | 移除进度条，进入内容流式渲染 | — |
| `content` | LLM逐词输出 | 追加到AI消息气泡 | `content` |
| `svg` | SVG Logo生成 | 渲染SVG预览卡片+保存按钮 | `style`, `code` |
| `image` | 图片生成完成 | 渲染图片卡片+保存按钮 | `style`, `url`, `prompt` |
| `image_gen_start` | 图片生成流程开始 | 显示图片生成进度 | `count` |
| `svg_gen_start` | SVG生成流程开始 | 开始收集SVG序列 | `count` |
| `image_error` | 图片生成失败 | 显示单张失败提示，不中断流程 | `style`, `error` |
| `file_saved` | 文件归档完成 | 显示归档成功提示+自动预览 | `message`, `folder`, `auto_preview` |
| `suggestions` | 追问建议生成 | 渲染追问快捷按钮 | `items` |
| `done` | 全部流程结束 | 结束加载态 | — |

**事件流时序**：

```
analyzing → node_selected → progress(多次) → [可选: svg_gen_start → svg(多次)]
                                         → [可选: image_gen_start → image(多次)]
                                         → content(多次) → suggestions → done
```

## 三、做出该选择的底层原因

**业务原因**：创业者在等待AI输出时，需要看到"正在做什么"的反馈——进度条降低焦虑，阶段切换提供掌控感。

**技术原因**：
1. SSE 是 HTTP 原生协议，相比 WebSocket 更简单，无需握手升级
2. 单向推送（server→client）足够，前端不需要向流中发消息
3. 前端用 `fetch + ReadableStream` 消费，React 中逐词追加到 state

**对比过的备选方案**：
- 备选A：WebSocket → 弃用：双向通信在本场景是过度设计，增加连接管理复杂度
- 备选B：HTTP 轮询 → 弃用：延迟大，无法逐词输出
- 备选C：Chunked Transfer Encoding 裸推 → 弃用：无结构化事件，前端解析不可靠

## 四、落地硬性约束

- 每个 SSE 消息必须以 `data: ` 前缀 + JSON + `\n\n` 结尾
- `content` 事件使用 chunk_size=12 字符分片发送，确保流式感
- `node_selected` 必须在首次 `content` 之前发送
- `done` 事件必须是最后一条消息
- 前端 `isLoading` 状态在收到 `done` 事件后置 false

## 五、功能边界

### 覆盖场景
- Node 执行全流程（analyzing→node_selected→progress→content→done）
- 追问场景（跳过 analyzing，直接复用当前 node）
- 图片/SVG 生成并行流（在 content 之前插入）
- 停止生成（前端 abort，后端捕获 AbortError）

### 明确不覆盖
- 不处理 SSE 重连（断开即视为失败）
- 不处理多 Node 并行（单次请求仅一个 Node）
- 不处理二进制数据推送（图片通过 URL 引用，不通过 SSE 传输）

## 六、不这么做的风险

1. 无流式协议：用户等待 60 秒空白页后放弃使用
2. 事件类型不结构化：前端需要解析非结构化文本推断阶段，边界情况不可靠
3. Node 名称/图标硬编码在前端：后端新增 Node 时前端不同步更新，显示不一致
