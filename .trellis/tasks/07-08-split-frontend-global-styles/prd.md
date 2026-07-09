# 拆分前端全局样式

## Goal

将 `kaiwu/src/styles.css` 从单个近 7k 行的全局样式文件拆分为按基础、共享控件、布局、业务页面和生成内容归属的多个 CSS 文件，降低维护成本，并为后续组件级样式解耦做准备。

## Requirements

* 保持 `kaiwu/src/main.tsx` 的单入口样式导入不变，`styles.css` 作为聚合入口。
* 按当前选择器归属拆分到 `kaiwu/src/styles/` 下的多个域级 CSS 文件。
* 继续将较大的域级 CSS 文件拆到页面/组件级样式文件，优先让 owning component 通过 side-effect import 引入。
* 根入口只保留基础变量、应用壳、共享控件/动画等跨组件样式。
* 保持现有 className、视觉表现和样式覆盖顺序，避免一次性改动 React 组件结构。
* 不删除疑似旧样式；本次只做低风险拆分，未使用样式清理留到后续任务。
* 文件组织要支持后续逐步迁移到组件旁置样式或更细粒度 feature 样式。

## Acceptance Criteria

* [ ] `kaiwu/src/styles.css` 明显缩小，仅作为样式聚合入口。
* [ ] 新增的 CSS 文件按职责命名，便于定位 sidebar、home、conversation、project library、modal、settings、coding 等样式。
* [ ] 功能组件优先导入自己的页面/组件 CSS，减少根入口承担的业务样式。
* [ ] 前端构建 `npm run build` 通过。
* [ ] 不改动业务逻辑、API、状态管理或 SSE 链路。

## Definition of Done

* 前端规范已读取。
* 代码拆分完成并通过构建验证。
* 总结后续完全解耦建议。

## Technical Approach

采用渐进式 CSS 解耦：第一阶段保留全局类名和 `styles.css` 入口，通过 `@import` 串联新文件，严格按原文件顺序迁移块，最大程度保留 CSS cascade 行为。第二阶段将页面/组件 CSS 拆得更细，并由 owning component 直接 import；`styles.css` 只保留 base / shell / shared / legacy 兜底入口。

## Decision (ADR-lite)

**Context**: 当前 `styles.css` 包含基础变量、全局反馈、侧边栏、首页、对话页、项目库、弹窗、创作工作台、编程页、设置页、Markdown/生成图片样式等多个关注点，单文件维护成本高。

**Decision**: 本次先做低风险域级拆分，再推进页面/组件级样式导入，暂不引入 CSS Modules、CSS-in-JS 或大规模组件重构。

**Consequences**: 拆分后维护入口更清晰，但样式仍是全局 class。完全解耦需要后续配合组件拆分和局部导入继续推进。

## Out of Scope

* 不做视觉 redesign。
* 不清理疑似未使用样式。
* 不把 `MainStage.tsx` 中的大页面拆成独立组件。
* 不迁移到 CSS Modules、Tailwind 或其他样式方案。

## Technical Notes

* `kaiwu/src/main.tsx` 当前只导入 `./styles.css`。
* `kaiwu/src/styles.css` 当前约 6,895 行。
* 前端样式规范仍以全局 class-based styling 和 `:root` CSS 变量为主。
