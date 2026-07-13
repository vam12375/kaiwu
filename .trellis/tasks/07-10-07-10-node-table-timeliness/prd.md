# 修复 node 表格排版与市场数据时效性

## Goal

修复 AI node 输出中的 Markdown/报告表格排版不协调问题，并强化 node1 市场规模数据的时效性表达，避免在 2026 年继续把 2025 年估算误呈现为当前市场规模。

## What I Already Know

* 用户截图显示多列表格列宽分配不协调：短内容列占用过多空间，长内容列被压窄；局部表格首列/末列对齐也显得不稳定。
* 前端 AI 内容通过 `renderMarkdown()` 渲染，表格逻辑集中在 `kaiwu/src/utils.ts` 与 `kaiwu/src/styles/conversation/markdown-content.css`。
* 后端导出的 HTML 报告通过 `kaiwuback/server/utils/markdown.py` 和 `kaiwuback/server/utils/report_html.py` 渲染，表格权重应与前端保持相近。
* node1 prompt 和运行时已有当前日期注入与数据时效性约束，但截图说明细分市场表/正文仍可能输出 2025 年估值而未清楚标注时效限制。
* `docs/specs/Spec-*.md` 在当前工作树中未找到；本任务按 `.trellis/spec/` 与现有代码约定执行。

## Requirements

* 前端 Markdown 表格应根据表头语义与内容长度分配列宽：短字段少占空间，长描述/来源/方案/痛点列多占空间。
* 表格整体视觉保持协调：文字左对齐为主，短的首列可右对齐形成标签感，最后一列不再无条件右对齐导致阅读别扭。
* 后端 HTML 报告表格与前端对齐规则保持一致，导出结果不应再次变形。
* node1 市场规模输出必须以运行时当前年份为基准；当前年份数据若不完整，应写“YYYY年（截至最新公开数据）”并说明来源截至时间。
* 只有上一年或更早公开数据时，必须明确写“公开数据截至YYYY年/来源发布于YYYY年”，不能把旧年估值伪装成当前数据。
* 未来 1-2 年预测必须单列为预测补充，标注 `[预测]` 或 `[行业测算]`。

## Acceptance Criteria

* [x] 2/3/4/5+ 列 Markdown 表格能输出更合理的 `colgroup` 宽度。
* [x] 截图中的“目标用户”“用户痛点”“市场规模/细分市场”类表格不再出现短列挤占长列的明显失衡。
* [x] 前端表格单元格默认左对齐，首列短标签可以右对齐；最后一列不再被 CSS 强制右对齐。
* [x] 后端 HTML 报告表格使用相同列宽语义与对齐策略。
* [x] node1 prompt/运行时约束覆盖“近5年趋势表”“细分市场拆解”和正文中的年份/估算表述。
* [x] `npm run build` 与 `python -m compileall kaiwuback/server` 通过。

## Verification

* `python -m compileall kaiwuback/server` passed.
* `npm run build` passed in `kaiwu/`.
* Backend Markdown table smoke confirmed `colgroup`/`table-cols-4` output and semantic right alignment only for market-size columns.
* `current_date_cn()` returned `2026年7月10日`, and node1 currentness guard generated 2022-2026 actual-year guidance plus 2027-2028 prediction guidance.
* Follow-up screenshot pass: adjusted `年份`/`收入来源` columns to stay left-aligned and changed 2/3/4-column table CSS to fill the content width, matching the wider “发布节奏” table behavior.
* Follow-up header pass: centered table headers within their computed columns while preserving body-cell semantic alignment.
* Follow-up body pass: compact categorical body columns such as `类目` can center-align under centered headers, while long explanatory cells stay left-aligned.
* Follow-up compact comparison pass: 2-column short comparison tables such as `竞争者/市占率(估)` center-align both body columns to avoid left/right edge drift.
* Follow-up semantic header pass: table headers now follow their body column alignment, so `年份` stays above year values and `预测增速`/percentage headers align with their numeric data.

## Definition of Done

* 前端构建通过。
* 后端语法检查通过。
* 不回滚或覆盖工作树中已有的无关修改。
* 若发现需要更新 Trellis spec，记录原因；否则说明无需更新。

## Out of Scope

* 不重做整套聊天界面视觉系统。
* 不引入新的 Markdown 渲染库。
* 不更改 `/api/tasks`、SSE 事件协议或 conversation 保存机制。
* 不承诺 node1 一定能获取所有行业的 2026 年真实公开数据；本任务保证表达和标注不误导。

## Technical Approach

* 在现有表格权重函数上增强语义权重与内容长度权重，避免纯固定规则导致列宽不协调。
* 前端 CSS 调整对齐策略，移除最后一列强制右对齐，保留短标签首列右对齐的阅读结构。
* 同步后端 Markdown/HTML 报告表格权重与 CSS 对齐规则。
* 强化 node1 当前性 guard 和 prompt 中细分市场表说明，要求旧年数据必须写清时效限制。

## Technical Notes

* 相关前端规范：`.trellis/spec/frontend/index.md`、`directory-structure.md`、`component-guidelines.md`、`quality-guidelines.md`。
* 相关后端规范：`.trellis/spec/backend/index.md`、`directory-structure.md`、`quality-guidelines.md`。
* 思考指南：`.trellis/spec/guides/code-reuse-thinking-guide.md`、`cross-layer-thinking-guide.md`。
* 当前工作树已有多处未提交改动，本任务只在相关文件上做增量修补。
