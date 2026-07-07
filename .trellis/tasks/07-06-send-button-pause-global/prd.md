# 将暂停操作整合进发送按钮

## Goal

生成中不再在对话页右上角显示独立暂停/停止按钮，而是在发送按钮位置提供停止生成能力，让全局输入体验保持一致。

## What I Already Know

* 用户指出截图中右上角暂停按钮应放入发送按钮中，并要求“全局”生效。
* 当前普通对话页的停止按钮在 `kaiwu/src/features/chat/ConversationPanel.tsx` header 的 `.doubao-header-actions` 内。
* 当前普通对话页和首页输入框各自有发送按钮，均使用 `.icon-action.send-action`。
* 任务驱动对话取消能力已由 `stopGeneration` 提供，前端不需要新增后端接口。

## Assumptions

* “全局”指真实对话输入入口：对话页输入框和首页输入框，而不是 `MainStage.tsx` 中用于 AI 图片/视频/编程工作台展示的静态 mock 按钮。
* 加载中发送按钮应变为可点击的停止生成按钮，而不是 disabled。
* 图片模式仍遵守现有“AI 生图按钮与普通对话按钮区分”的业务约束，不在本次改变生图发送流程。

## Requirements

* 生成中时，不在对话 header 右上角渲染独立停止/暂停按钮。
* 生成中时，发送按钮位置显示停止图标并调用 `stopGeneration`。
* 非生成中时，发送按钮保持现有发送行为和禁用逻辑。
* 对话页与首页输入框使用一致的加载中发送按钮语义。

## Acceptance Criteria

* [ ] 普通对话生成中，右上角没有独立停止按钮。
* [ ] 普通对话生成中，输入框发送按钮变为停止按钮，点击后调用停止生成。
* [ ] 非生成中，发送按钮仍按原逻辑发送消息。
* [ ] 首页输入框在全局加载中时同样显示停止按钮并可停止。
* [ ] 前端构建通过。

## Definition of Done

* 前端代码遵守组件与状态管理规范。
* 运行 `npm run build` 验证前端构建。
* 不改动后端任务/SSE 协议。

## Out of Scope

* 不新增暂停后恢复能力；沿用现有停止生成/取消任务行为。
* 不调整 AI 生图、AI 视频、AI 编程的业务发送分流。
* 不修改历史备份、生成产物或静态 mock 工作台按钮。

## Technical Notes

* 相关文件：`kaiwu/src/features/chat/ConversationPanel.tsx`、`kaiwu/src/features/home/ChatInput.tsx`、`kaiwu/src/styles.css`。
* 前端规范入口：`.trellis/spec/frontend/index.md`。
