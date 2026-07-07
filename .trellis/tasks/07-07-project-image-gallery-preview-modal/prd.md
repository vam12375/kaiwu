# 图片库图片预览弹层

## Goal

把项目库「图片库」中点击图片直接打开新链接的体验，改成应用内的即梦风格图片详情预览：用户可以在弹层中查看大图、左右切换图片，并看到对应的提示词与生成参数信息，同时去掉参考图中右下角的二次创作工具区。

## What I Already Know

* 用户提供的当前截图显示：项目库图片卡片现在点击后浏览器直接打开 `/project-images/...jpg` 新标签页。
* 目标参考图是即梦式详情页：左侧大图，左右切换控件，右侧有关闭、下载、收藏/更多、缩略图组、图片提示词和基础参数信息。
* 用户明确要求不要参考图右下角那组工具功能区。
* 当前前端图片库位于 `kaiwu/src/features/layout/MainStage.tsx`，图片卡片目前是 `<a target="_blank">`。
* 当前后端 `/api/project-images` 由 `kaiwuback/server/api/routes_files.py` 返回 `name`、`url`、`size`、`modified`，暂未返回提示词或生成参数。
* 直接 AI 生图链路在 `kaiwuback/server/agent/runtime.py` 中已拥有 `message`、`image_model`、`image_ratio`、`image_resolution`、`image_count`、`reference_images` 等信息，保存图片时可以伴随写入元数据。

## Assumptions

* 弹层在项目库「图片库」文件夹内打开，不新增独立路由。
* 右侧信息区保留下载按钮；收藏和更多可以先作为视觉按钮/占位，不新增持久化收藏逻辑。
* 旧图片没有历史提示词元数据时，预览仍可用，并显示文件名、时间、大小等基础信息。
* 新生成图片应尽量记录提示词、模型、比例、分辨率、来源等元数据，供图片库详情展示。

## Requirements

* 点击图片库卡片时打开应用内预览弹层，不再直接跳转到新浏览器标签。
* 弹层左侧展示当前图片的大图，使用适配视窗的 `object-fit: contain`，避免裁切关键内容。
* 支持上一张/下一张切换，包括按钮点击和键盘左右方向键。
* 右侧展示当前图片同组缩略图；点击缩略图切换当前图片。
* 右侧展示图片提示词、模型/比例/分辨率/文件大小/更新时间等信息。
* 保留下载入口，下载逻辑沿用现有 `/api/download-image` 能力。
* 支持关闭弹层：关闭按钮、点击背景、`Esc`。
* 不实现参考图右下角的「生成视频、去画布编辑、用作参考图、超清、扩图、再次生成」等二次创作操作。
* 响应式布局：桌面为大图 + 右侧信息栏；窄屏下信息栏应可滚动或下置，不能遮挡图片。

## Acceptance Criteria

* [ ] 在项目库进入「图片库」后，点击任意图片不会打开新标签，而是在当前页面显示预览弹层。
* [ ] 弹层可通过左右按钮和键盘左右键切换图片，缩略图选中态同步更新。
* [ ] 弹层右侧能展示提示词；没有元数据的旧图片显示可理解的空状态。
* [ ] 弹层下载按钮能下载当前图片。
* [ ] 关闭按钮、背景点击和 `Esc` 都能关闭预览。
* [ ] 右下角二次创作工具区不出现。
* [ ] 前端 `npm run build` 通过；如修改后端，`python -m compileall kaiwuback/server` 通过。

## Definition Of Done

* 代码遵守前端组件拆分和类型安全规范，避免继续扩大 `MainStage.tsx` 的复杂 JSX。
* 后端仍只在 `server/api/`、`server/agent/`、`server/utils/` 等对应层处理业务，不把新逻辑放入 `main.py`。
* 图片元数据不包含密钥、Token 或隐私敏感内容。
* 对旧图片、缺失文件、图片加载失败等情况有合理降级。

## Out Of Scope

* 不做收藏持久化。
* 不做更多菜单功能。
* 不做参考图右下角二次创作工具区。
* 不做图片编辑、再次生成、扩图、超清、多角度等能力。
* 不迁移历史图片的完整提示词；历史图片只做基础信息展示。

## Technical Approach

* 前端新增一个 typed 图片预览组件，供 `MainStage.tsx` 的项目库图片区域调用。
* 扩展 `ProjectImage` 类型，允许可选 `prompt`、`style`、`model`、`ratio`、`resolution`、`source`、`reference_count` 等字段。
* 后端扩展 `/api/project-images`，读取图片旁的元数据文件并合并到列表响应。
* 在 AI 生图保存图片成功后写入对应元数据，确保后续图片库可展示提示词与参数。
* 下载继续复用现有 `/api/download-image?url=...`，避免重复实现文件流逻辑。

## Technical Notes

* Relevant frontend specs: `.trellis/spec/frontend/index.md`, `component-guidelines.md`, `state-management.md`, `type-safety.md`, `quality-guidelines.md`.
* Relevant backend spec index: `.trellis/spec/backend/index.md`.
* Likely frontend files: `kaiwu/src/features/layout/MainStage.tsx`, `kaiwu/src/types.ts`, `kaiwu/src/styles.css`; preferably add a focused component under `kaiwu/src/features/layout/`.
* Likely backend files: `kaiwuback/server/api/routes_files.py`, `kaiwuback/server/agent/runtime.py`, possibly a small utility in `kaiwuback/server/utils/`.
* Product design brief source: user screenshots comparing current project library behavior, browser raw-image behavior, and JiMeng-style image detail preview.
