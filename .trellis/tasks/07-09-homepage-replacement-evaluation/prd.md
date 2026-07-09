# brainstorm: 首页替换评估

## Goal

将 `/Users/wangzijian/Desktop/首页/` 中的静态首页方案迁移为 Kaiwu 当前 React 应用首页：保留开场页，下滑进入主首页；主首页迁移技能卡横滑和项目案例抽屉，同时保留现有对话输入的真实业务能力。

## What I already know

* 用户已确认按推荐方案实施。
* 外部文件夹包含 `home-alt.html` 和 4 张案例图：宠物银饰、房地产中介、餐饮品牌、服装品牌。
* `home-alt.html` 是完整静态页面，包含自有侧边栏、开场页、技能卡横滑、输入框、项目案例抽屉和原生 JS 交互。
* 当前项目首页位于 `kaiwu/src/features/home/`，由 `BrandHeader`、`ChatInput`、`WorkflowSteps`、`FeatureCards`、`FreeMode` 等组件组成。
* 当前首页由 `MainStage.tsx` 组装，`App.tsx` 负责状态和任务对话 wiring。

## Assumptions

* 目标是更新当前应用首页主舞台，而不是替换整个应用 shell 和侧边栏。
* 外部首页的案例图可以作为前端静态资源迁入 `kaiwu/public/` 或更合适的资产目录。

## Open Questions

* 无阻塞问题。

## Requirements (Evolving)

* 保留 `home-alt.html` 的第一屏开场页，用户下滑进入真正首页主舞台。
* 开场页每次进入首页都显示，保持完整品牌开场体验。
* 第二屏主首页完整迁移 `home-alt.html` 的技能卡横滑和项目案例抽屉。
* 保留当前应用侧边栏、对话发送、模型选择、停止生成、会话历史等业务能力。
* 不照搬外部 HTML 的原生 JS 状态逻辑；交互应转换成 React state。
* 静态案例图迁移后需要稳定引用，不能依赖桌面绝对路径。

## Acceptance Criteria

* [x] 首页视觉接近外部 `home-alt.html` 的主舞台设计。
* [x] 用户能从开场页顺畅下滑进入首页主舞台。
* [x] 每次从应用首页入口进入时，先看到开场页。
* [x] 第二屏包含可交互技能卡横滑和项目案例抽屉。
* [x] 当前 `ChatInput` 的发送、停止、IME 输入、模型选择能力不回退。
* [x] `npm run build` 通过。
* [x] 首页在桌面和较窄宽度下没有明显遮挡或溢出。

## Definition of Done

* 前端构建通过。
* 迁移范围清晰，未引入无关 shell/侧边栏重构。
* 如迁移图片资源，路径和引用方式稳定。

## Out of Scope

* 替换整个 App shell。
* 重写侧边栏、历史记录、项目库、技能库。
* 引入独立 HTML 页面绕过 React 应用。

## Technical Notes

* 外部文件：`/Users/wangzijian/Desktop/首页/home-alt.html`
* 当前首页组装：`kaiwu/src/features/layout/MainStage.tsx`
* 当前首页组件：`kaiwu/src/features/home/*`
* 当前首页样式：`kaiwu/src/styles/home/*`
