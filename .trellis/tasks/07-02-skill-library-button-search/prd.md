# 调整技能库按钮和搜索匹配

## Goal

让技能库卡片操作更贴近用户意图：已安装或已启用技能的主操作不再显示“管理”，而是显示“去使用”；搜索框只按技能标题匹配，避免因为描述、分类、连接器或完整文本命中导致结果过宽。

## Requirements

* 技能库卡片中，已安装技能的第二个操作按钮文案从“管理”改为“去使用”。
* 按钮原有交互保持不变：点击已安装技能仍进入当前管理弹窗，不新增跳转或启用逻辑。
* 技能库搜索仅匹配 `SkillLibraryItem.name`，支持用户输入“心理登月”“表格分析器”等标题关键词。
* 搜索框提示文案改为标题范围，避免暗示会搜索连接器或工作流。
* 分类筛选、技能市场/已安装视图切换、安装按钮和详情按钮保持现有行为。

## Acceptance Criteria

* [ ] “心理登月”等已安装技能卡片按钮显示“去使用”。
* [ ] 未安装技能卡片仍显示“安装”。
* [ ] 搜索“心理登月”只因标题命中显示对应技能。
* [ ] 搜索“表格分析器”只因标题命中显示对应技能。
* [ ] 搜索描述、分类或完整技能文本中的非标题词不再额外命中技能。
* [ ] 搜索框提示为“搜索技能标题”。
* [ ] 前端构建通过。

## Definition of Done

* 前端实现符合 `kaiwu/src/features/layout/SkillLibraryPage.tsx` 现有组件边界。
* 不扩大 `App.tsx` 或 SSE/任务流相关逻辑。
* `npm run build` 通过。

## Technical Approach

在 `SkillLibraryPage.tsx` 内收窄 `searchSkill` 的匹配字段，只对标题做大小写归一后的 `includes`；卡片按钮仍根据 `installed` 状态选择打开 `manage` 或 `install` 弹窗，仅将已安装状态文案改为“去使用”。

## Out of Scope

* 不改变“去使用”的点击目标。
* 不调整管理弹窗标题、启停开关、卸载逻辑。
* 不改变技能库数据来源或安装状态存储。

## Technical Notes

* Relevant specs read: `.trellis/spec/frontend/index.md`, `.trellis/spec/frontend/directory-structure.md`, `.trellis/spec/frontend/component-guidelines.md`, `.trellis/spec/frontend/quality-guidelines.md`.
* Relevant files discovered: `kaiwu/src/features/layout/SkillLibraryPage.tsx`, `kaiwu/src/hooks/useSkillLibrary.ts`, `kaiwu/src/data.ts`.
