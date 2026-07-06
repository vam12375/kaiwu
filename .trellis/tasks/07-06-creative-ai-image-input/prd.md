# 调整创造模式 AI 生图输入框

## Goal

让左侧“创造模式 -> AI生图”进入对话后，底部输入框明确切换为图片生成专用输入框，并参考即梦输入框展示用户期望的生图字段。

## Requirements

* 点击“AI生图”后打开新对话，并显示图片生成专用 composer，而不是普通咨询输入框样式。
* 图片生成 composer 需要包含参考即梦截图的核心字段：参考图上传入口、图片生成模式、图片模型、画面比例、分辨率、提示词/主体入口、生成张数、发送按钮。
* 图片模型下拉展示模型 ID，不展示“图片 4.5/图片 4.0/写实增强/插画模型”等旧标签；模型项使用 `doubao-seedream-5-0-260128`、`doubao-seedream-5-0-lite-260128`、`doubao-seedream-4-5-251128`、`doubao-seedream-4-0-250828`。
* 上传参考图后，参考图框直接显示上传图片缩略图；不要把“已上传 N 张参考图”插入提示词输入框。
* 左侧创造模式中所有子菜单都需要显示二级菜单选中态；后续新增子菜单也应复用同一套状态配置。
* 已上传的参考图需要提供删除 `x` 按钮，可以清空已选择图片。
* 复用现有 `isImageMode`、`imageRatio`、`imageCount` 与任务发送链路，避免引入新的后端协议。
* AI 视频、AI 编程继续使用现有流程；不要误用生图 composer。
* 保留 IME 输入、Enter 发送、停止生成、对话重命名和历史行为。

## Acceptance Criteria

* [ ] 左侧点击“AI生图”后，底部 composer 在空对话中显示图片生成字段。
* [ ] 图片模型下拉使用 seedream 模型 ID 列表。
* [ ] 上传参考图后缩略图出现在参考图框内。
* [ ] AI生图、AI视频、AI编程选中时左侧二级菜单分别高亮。
* [ ] 参考图缩略图右上角有删除按钮，点击后恢复为空参考图框。
* [ ] 生图模式下比例支持更多即梦式选项，至少包含 `3:2`、`1:1`、`16:9`、`9:16`。
* [ ] 生图模式下张数选择仍写入 `imageCount`，发送时仍通过 `/api/tasks` 带上 `image_ratio` 和 `image_count`。
* [ ] 普通对话、AI 视频、AI 编程不显示生图专用字段。
* [ ] `npm run build` 通过。

## Definition of Done

* Frontend build passes.
* Existing dirty worktree changes not related to this task are preserved.
* No backend changes unless frontend verification reveals a required contract issue.

## Technical Approach

Update `features/chat/ConversationPanel.tsx` so `isImageMode` switches both the textarea placeholder and toolbar composition to a richer image-generation composer. Add focused CSS classes in `styles.css`, reusing the current global toolbar/popover styles where possible. Keep state ownership in `App.tsx` unchanged unless a field must become functional.

## Out of Scope

* Calling a new image model API or changing backend image generation behavior.
* Building the standalone `activePage === 'image'` workspace into the sidebar click path.
* Persisting new image-only fields beyond existing ratio/count.

## Technical Notes

* Current sidebar calls `resetConversation({ imageMode: true, open: true, activePage: 'home' })` for AI生图, so the intended surface is the conversation composer.
* Current `ConversationPanel` only swaps normal file controls for ratio/count when `isImageMode` is true; it still looks like a normal chat input.
* `useConversationTask` already sends `image_ratio` and `image_count`.
* Product Design saved context preflight returned no saved context; visual source is the user's即梦 screenshot plus current Kaiwu UI.
* Relevant specs read: `.trellis/spec/frontend/index.md`, `component-guidelines.md`, `state-management.md`, `type-safety.md`, `quality-guidelines.md`, `directory-structure.md`.
