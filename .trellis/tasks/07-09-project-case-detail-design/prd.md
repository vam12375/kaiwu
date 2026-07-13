# brainstorm: 项目案例详情页设计

## Goal

为首页右上角「项目案例」弹出的四个创业案例增加可进入的案例详情体验。用户点击「房地产中介」案例后，可以进入一个网页/详情视图，集中浏览「房地产中介备料」中的多份 HTML 报告，形成从案例卡到完整项目资料库的顺畅路径。

## What I Already Know

* 首页第二屏右上角已有「项目案例」按钮，点击后弹出四个案例卡片。
* 现有案例卡位于 `kaiwu/src/features/home/HomeExperience.tsx` 的 `HOME_CASES`。
* 「房地产中介」案例已有图片 `/home-cases/case-real-estate.jpg`。
* 用户提供的 `/Users/wangzijian/Desktop/房地产中介备料/` 中有 5 个 HTML 文件：
  * 深度市场调研报告 — 商业地产"办公+商业"复合赛道
  * 合租侠 — 商业模式计划书（含品牌体系）
  * 合租侠 — 产品落地手册
  * 合租侠 — 内容营销方案
  * 合租侠 — 内容营销体系

## Assumptions (Temporary)

* MVP 先只把「房地产中介」案例做成可进入详情，其他三个案例可以保留为展示卡或显示“即将上线”状态。
* 案例资料应随前端部署一起可访问，不能依赖用户桌面绝对路径。
* 详情页应该更像“案例档案馆/项目资料页”，不是简单新开一个孤立 HTML 文件。

## Open Questions

* 点击案例后，用户更希望进入独立页面，还是在当前应用内打开详情面板？

## Requirements (Evolving)

* 用户点击首页「项目案例」按钮后仍看到四张案例卡。
* 点击「房地产中介」卡片后，可以进入一个集中展示 5 份 HTML 报告的案例详情体验。
* 采用方案 C：先展示 5 张报告摘要卡，用户点击“查看完整报告”后再打开对应 HTML。
* 详情体验需要让用户理解 5 份资料之间的顺序：市场调研 → 商业方案 → 产品落地 → 营销方案 → 内容营销体系。
* HTML 资料需要可打开阅读。

## Acceptance Criteria (Evolving)

* [ ] 首页项目案例弹窗中的「房地产中介」卡片具备明确可点击状态。
* [ ] 点击后能进入房地产中介案例详情体验。
* [ ] 详情页/详情面板能展示 5 份 HTML 报告入口。
* [ ] 每份报告入口能打开对应 HTML 内容。
* [ ] 不影响其他首页技能卡、输入框、帮助按钮和项目案例弹窗原有布局。

## Definition of Done

* Tests/build checks pass (`npm run build`)。
* 代码遵循前端组件和样式规范。
* 静态资源路径不依赖本机桌面绝对路径。
* 方案保留未来扩展到其他三个案例的结构。

## Out of Scope (Explicit)

* 暂不重新设计 5 份 HTML 报告自身的视觉样式。
* 暂不为其他三个案例补齐真实 HTML 资料，除非用户提供资料。
* 暂不接入后端动态案例管理系统。

## Technical Notes

* 首页入口组件：`kaiwu/src/features/home/HomeExperience.tsx`
* 首页案例样式：`kaiwu/src/styles/home/home-experience.css`
* 当前静态图片目录：`kaiwu/public/home-cases/`
* 新增静态资料目录：`kaiwu/public/home-case-reports/real-estate/`
* 用户备料目录：`/Users/wangzijian/Desktop/房地产中介备料/`

## Decision (ADR-lite)

**Context**: 用户希望首页「项目案例」里的单个案例可以进入一个页面，承载该案例对应的多份 HTML 报告，同时不希望体验像文件夹列表一样生硬。

**Decision**: 采用方案 C。点击「房地产中介」案例后，在项目案例面板内进入案例资料页，先显示报告摘要卡；每张摘要卡提供“查看完整报告”，新窗口打开对应 HTML。

**Consequences**: 首页交互保持轻量，不引入 iframe 预览的尺寸和性能问题；未来如果用户希望沉浸式阅读，可以在此基础上升级为内嵌预览或独立路由。
