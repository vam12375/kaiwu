# 优化图片库懒加载性能

## Goal

图片库上线后打开速度慢，网络面板出现大量图片请求排队。目标是在不改变原图归档和用户下载原图能力的前提下，让图片库和 AI 生图消息优先展示轻量 WebP 预览，并只加载用户当前可见或即将可见的图片，避免 50 张原图同时进入浏览器请求队列。

## What I Already Know

* 用户截图显示图片库卡片长时间空白，网络面板里几十个图片请求处于待处理状态。
* 前端图片库在 `kaiwu/src/features/layout/MainStage.tsx` 中直接为每个卡片渲染 `<img src={img.url}>`。
* 图片预览弹层 `ProjectImagePreviewModal.tsx` 右侧缩略图列表也会直接加载所有原图。
* 后端 `/api/project-images` 当前返回最近 50 张图片，字段包含原图 `url`，没有缩略图 URL。
* 用户追加要求：AI 生成图片先展示 WebP，用户点击下载时才下载原图。
* 本次必须避免影响 AI 生成文件双归档和原图下载规则。

## Requirements

* 图片库网格卡片必须懒加载，只在图片进入可视区域附近时才设置真实 `src`。
* 图片加载需要限流，避免滚动或打开页面时同时发起几十个原图请求。
* 首屏可见图片应优先加载，滚动后再逐步加载后续图片。
* 预览弹层的主图保持立即加载，保证点击图片后的大图体验。
* 预览弹层缩略图不应一次性加载所有原图，避免打开预览时再次打爆请求队列。
* AI 生成的 PNG/JPG/JPEG 原图需要生成 WebP 预览文件；前端展示使用 WebP，下载使用原图。
* `/api/project-images` 需要同时返回展示 URL 和原图 URL，保持旧字段兼容。
* `/api/download-image` 对 WebP 预览 URL 也应返回对应原图，兼容历史会话和旧前端调用。
* 搜索、点击预览、左右切换、下载等现有交互保持不变。

## Acceptance Criteria

* [ ] 打开图片库时，不再为全部 50 张图片同时创建网络请求。
* [ ] 可视区域内图片能够逐步显示，离屏图片滚动接近时才开始加载。
* [ ] 打开图片预览时主图正常加载且优先使用 WebP 预览，右侧缩略图列表不会抢占所有网络请求。
* [ ] 图片库和新 AI 生图消息展示 WebP 地址，点击下载返回原图文件名和原图字节。
* [ ] `python -m compileall kaiwuback/server` 通过。
* [ ] `npm run build` 通过。

## Definition of Done

* 前端构建通过，后端语法检查通过。
* 代码遵循现有 `features/layout` 组件拆分风格。
* 不改动无关 WIP 文件。

## Technical Approach

新增一个轻量的项目图片懒加载组件，使用 `IntersectionObserver` 观察卡片/缩略图进入视口附近的时机，并用模块级小队列限制同一时间解锁真实图片 `src` 的数量。后端为 AI 生成原图生成独立 WebP 预览文件，`url` 继续作为展示 URL，新增 `original_url` 作为原图下载 URL。

## Decision (ADR-lite)

**Context**: 当前慢的根因是前端一次性给所有图片挂原图 `src`，导致浏览器对几十张图片排队。后端暂时没有缩略图能力。

**Decision**: 使用服务端 WebP 预览 + 前端 IntersectionObserver 懒加载 + 并发限流。`url` 指向 WebP 展示图，`original_url` 指向原图；下载按钮优先用 `original_url`。如果旧数据只有 WebP 预览 URL，下载接口反查原图。

**Consequences**: 首屏和预览加载体积更低，同时保留原图归档和下载质量；首次访问旧图片时可能需要生成 WebP 预览，若 Pillow 不可用或图片格式不支持，则回退原图 URL。

## Out of Scope

* 不改变 `/api/project-images` 返回数量或排序。
* 不改变图片下载、保存、双归档逻辑。
* 不对 SVG/GIF 强制转 WebP。

## Technical Notes

* 主要涉及 `kaiwu/src/features/layout/MainStage.tsx`。
* 预览缩略图涉及 `kaiwu/src/features/layout/ProjectImagePreviewModal.tsx`。
* 共享类型在 `kaiwu/src/types.ts`；本任务预计不需要改类型。
* 后端图片列表接口在 `kaiwuback/server/api/routes_files.py`，当前返回最近 50 张原图。
* WebP 生成需要 `Pillow` 依赖，加入 `kaiwuback/requirements.txt`。
