# 全局统一 Toast 提示

## Goal

为 Kaiwu 前端增加一个全局统一的 toast 提示系统，让编辑成功、删除成功、生成成功、上传成功、保存成功、复制成功等轻量反馈使用同一套优雅样式和调用方式，替代散落的 `alert` 或临时成功提示。

## Requirements

* 新增全局 toast 能力，支持 `success`、`error`、`info` 三类提示。
* Toast 在应用根部统一渲染，自动消失，并支持短时间内多条提示队列。
* 替换前端现有适合轻量反馈的 `alert`：
  * 语音输入不支持、附件选择。
  * 参考图大小/数量/读取失败。
  * 保存到项目成功。
  * 删除项目文件夹失败。
* 为常见成功操作接入 toast：
  * 新建文件夹成功。
  * 上传文件成功。
  * 保存自定义技能成功。
  * 安装、启用/停用、卸载技能成功。
  * 删除对话成功、重命名对话成功。
  * 任务事件中的图片生成、文件保存、会话保存成功。
  * 复制 AI 回复成功/失败。
* 危险操作仍需二次确认，但确认框必须使用应用内统一弹层，不使用浏览器原生 `alert()` / `window.confirm()`。
* 不改变现有业务数据流、SSE 解析和对话保存逻辑。

## Acceptance Criteria

* [x] 应用根组件渲染一个统一 Toast 容器。
* [x] 所有新增/替换的提示都通过同一个 `showToast` 入口发起。
* [x] 项目库删除确认使用应用内确认弹层，不再触发浏览器原生 confirm。
* [x] Toast 样式符合当前产品的克制工作台风格，不遮挡核心输入区。
* [x] 前端构建通过 `npm run build`。

## Definition of Done

* Frontend build passes.
* Existing user WIP is preserved.
* No secrets or backend behavior changes.

## Technical Approach

新增 `src/features/toast/ToastProvider.tsx`，通过 React context 暴露 `useToast()`；在 `App.tsx` 内用 Provider 包裹工作台，并将 `showToast` 传入需要提示的 hook/component。Toast 使用 `framer-motion` 做轻量进入/退出动画，CSS 放入现有 `styles.css`。

## Decision (ADR-lite)

**Context**: 现有提示散落在多个组件和 hook 中，既有 `alert`，也有局部 modal status，成功反馈不一致。

**Decision**: 使用应用内自维护 ToastProvider，而不是引入第三方依赖。这样保持依赖简单，并符合现有 React + framer-motion 技术栈。

**Consequences**: 需要通过 props 将 `showToast` 传给若干现有组件/hook；后续如果引入全局 store，可以再把 toast 调用进一步解耦。

## Out of Scope

* 不新增后端接口或改变 API 返回格式。
* 不重构现有弹窗、项目库或技能库数据模型。

## Technical Notes

* Relevant frontend files inspected: `kaiwu/src/App.tsx`, `kaiwu/src/features/chat/ConversationPanel.tsx`, `kaiwu/src/features/home/ChatInput.tsx`, `kaiwu/src/features/layout/AppModals.tsx`, `kaiwu/src/hooks/useConversation.ts`, `kaiwu/src/hooks/agentTaskController.ts`.
* Existing workspace has unrelated uncommitted changes; edits should be narrow and preserve current file state.
