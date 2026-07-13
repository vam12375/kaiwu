/**
 * =============================================================================
 * # 角色
 * 工具函数层 —— 为曜势科技 App 提供纯函数处理能力。
 * 当前包含 Markdown 到 HTML 的渲染引擎，支持标准 Markdown 语法、
 * 表格、SVG 代码块嵌入、内联样式等扩展能力。
 *
 * # 输入
 * - content: string —— 原始 Markdown 格式文本
 *   支持语法：标题(#)、粗体(**)、链接([]())、图片(![]())、
 *   行内代码(`)、引用(>)、无序列表(-)、有序列表(1.)、
 *   表格(|...|)、分隔线(---)、SVG代码块(```svg)
 *
 * # 输出结构
 * ## 1. HTML 字符串
 * 返回经过 CSS class 标注的 HTML 字符串，可直接通过
 * dangerouslySetInnerHTML 渲染到 DOM 中。
 *
 * ## 2. CSS Class 映射
 * | Markdown 元素 | 渲染标签 | CSS Class |
 * |-------------|---------|-----------|
 * | # 标题       | h2      | md-h2     |
 * | ## 标题      | h3      | md-h3     |
 * | ### 标题     | h4      | md-h4     |
 * | #### 标题    | h5      | md-h5     |
 * | **粗体**     | strong  | md-bold   |
 * | `代码`       | code    | md-code   |
 * | > 引用       | blockquote | md-blockquote |
 * | - 列表项     | li      | md-li     |
 * | 1. 有序列表  | li      | md-li-ordered |
 * | \|表头\|     | th      | md-td     |
 * | \|单元格\|   | td      | md-td     |
 * | ---分隔线    | hr      | md-hr     |
 *
 * ## 3. SVG 代码块处理
 * ```svg 代码块会被提取并内联渲染，附带下载按钮。
 * ```xml 中若包含 <svg> 标签也会被识别为 SVG。
 * =============================================================================
 */

type MarkdownTableRow = string[];

const STORY_GROUP_BY_PREFIX: Record<string, string> = {
  A: '痛点故事',
  B: '品牌故事',
  D: '用户证言',
  E: '愿景故事',
  F: '创始人故事',
  P: '产品故事',
  C: '客户故事',
};

const DEV_GHOST_LINE_PREFIX = '%%DEV_GHOST_LINE_';
const DEV_NODE_TOKEN = 'node(?:0|1(?:\\.5)?|2|3(?:\\.1)?|4|5)';
const DEV_NODE_TOKEN_RE = new RegExp(`(^|[^A-Za-z0-9_])(${DEV_NODE_TOKEN})(?![A-Za-z0-9_])`, 'gi');
const DEV_NODE_ONLY_RE = new RegExp(DEV_NODE_TOKEN, 'gi');
const DEV_BRACKET_CONSTRAINT_RE = /[\[【]\s*(?:[≥>=]\s*)?\d+\s*(?:秒|字)(?:脚本|图文|私域)?\s*[\]】]/g;
const DEV_PAREN_CONSTRAINT_RE = /[（(][^）)]*(?:[≥>=]\s*\d+\s*字|至少\s*\d+\s*行|\d+\s*大模块|MVP原则)[^）)]*[）)]/g;
const DEV_PAREN_SUMMARY_RE = /[（(]\s*结语\s*[）)]/g;
const DEV_HINT_LINE_PATTERNS = [
  /^`{2,3}$/,
  new RegExp(`^（由\\s*${DEV_NODE_TOKEN}\\s*[^）]*自动生成）$`, 'i'),
  new RegExp(`^现在开始执行\\s*${DEV_NODE_TOKEN}\\s*.+$`, 'i'),
  new RegExp(`^调取节点\\s*[:：]\\s*${DEV_NODE_TOKEN}\\s*$`, 'i'),
  new RegExp(`^以上为\\s*${DEV_NODE_TOKEN}\\s*.+(?:完整输出|已全部呈现)[。.]?$`, 'i'),
];

function escapeHtml(value: string) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function normalizedDeveloperHintLine(line: string) {
  return line
    .replace(/^#+\s*/, '')
    .replace(/^>\s*/, '')
    .replace(/^\*+|\*+$/g, '')
    .trim();
}

function isDeveloperConstraintOnlyLine(line: string) {
  const cleaned = line
    .replace(DEV_NODE_ONLY_RE, '')
    .replace(/dialogue_brief\.md/gi, '')
    .replace(DEV_BRACKET_CONSTRAINT_RE, '')
    .replace(DEV_PAREN_CONSTRAINT_RE, '')
    .replace(DEV_PAREN_SUMMARY_RE, '')
    .replace(/[`*_#>\-\s+.,，。:：/|、()[\]（）【】]+/g, '');
  return cleaned.length === 0 && cleaned !== line;
}

function isDeveloperHintLine(line: string) {
  const text = normalizedDeveloperHintLine(line);
  if (!text) return false;
  if (/^\|.*\|$/.test(text)) return false;
  return DEV_HINT_LINE_PATTERNS.some((pattern) => pattern.test(text)) || isDeveloperConstraintOnlyLine(text);
}

function protectDeveloperHintLines(content: string) {
  const lines: string[] = [];
  const html = content.replace(/^.*$/gm, (line) => {
    if (!isDeveloperHintLine(line)) return line;
    const index = lines.push(line) - 1;
    return `${DEV_GHOST_LINE_PREFIX}${index}%%`;
  });
  return { html, lines };
}

function wrapDeveloperGhost(value: string) {
  return `<span class="md-dev-ghost" aria-hidden="true">${value}</span>`;
}

function concealDeveloperHints(html: string) {
  let next = html
    .replace(DEV_BRACKET_CONSTRAINT_RE, (match) => wrapDeveloperGhost(match))
    .replace(DEV_PAREN_CONSTRAINT_RE, (match) => wrapDeveloperGhost(match))
    .replace(DEV_PAREN_SUMMARY_RE, (match) => wrapDeveloperGhost(match))
    .replace(/dialogue_brief\.md/gi, (match) => wrapDeveloperGhost(match));
  next = next.replace(DEV_NODE_TOKEN_RE, (_match, prefix: string, token: string) => `${prefix}${wrapDeveloperGhost(token)}`);
  return next;
}

function plainCell(cell = '') {
  return cell
    .replace(/<br\s*\/?>/gi, ' ')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ')
    .trim();
}

function headerKey(header: string) {
  return plainCell(header)
    .replace(/[（(][^）)]*[）)]/g, '')
    .replace(/\s+/g, '');
}

function firstHeaderIndex(headers: MarkdownTableRow, candidates: string[]) {
  const candidateKeys = candidates.map((item) => headerKey(item));
  const index = headers.findIndex((header) => {
    const normalizedHeader = headerKey(header);
    if (!normalizedHeader) return false;
    return candidateKeys.some((candidate) => normalizedHeader === candidate || normalizedHeader.includes(candidate) || candidate.includes(normalizedHeader));
  });
  return index >= 0 ? index : null;
}

function cellAt(row: MarkdownTableRow, index: number | null) {
  if (index === null || index < 0 || index >= row.length) return '';
  return row[index] || '';
}

function splitMarkdownTableCells(line: string) {
  return line.replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
}

function isMarkdownSeparatorRow(cells: MarkdownTableRow) {
  return cells.length > 0 && cells.every((cell) => /^[-:\s]+$/.test(cell));
}

function fitTableRow(row: MarkdownTableRow, width: number) {
  if (width <= 0) return row;
  if (row.length === width) return row;
  if (row.length < width) return [...row, ...Array.from({ length: width - row.length }, () => '')];
  return [...row.slice(0, width - 1), row.slice(width - 1).join(' | ')];
}

function normalizeTableRows(rows: MarkdownTableRow[]) {
  const width = Math.max(rows[0]?.length || 0, 1);
  return rows.map((row) => fitTableRow(row, width));
}

function contentLengthWeight(longestValue: number, averageValue: number) {
  const score = Math.max(longestValue * 0.72, averageValue * 1.28);
  if (score <= 4) return 0.68;
  if (score <= 8) return 0.92;
  if (score <= 14) return 1.2;
  if (score <= 24) return 1.55;
  if (score <= 42) return 2.08;
  return 2.7;
}

function clampWeight(weight: number, min: number, max: number) {
  return Math.min(Math.max(weight, min), max);
}

function isKeyValueTable(headers: MarkdownTableRow) {
  const headerKeys = headers.map((item) => headerKey(item));
  return headers.length === 2
    && /^(维度|项目|类别|平台|渠道|方式|指标|要素)$/.test(headerKeys[0] || '')
    && /^(内容|说明|描述|结论|优先级)$/.test(headerKeys[1] || '');
}

function tableColumnWeight(header: string, rows: MarkdownTableRow[], index: number, headers: MarkdownTableRow) {
  const key = headerKey(header);
  const tableWidth = headers.length;
  const values = rows.map((row) => plainCell(cellAt(row, index)));
  const longestValue = Math.max(key.length, ...values.map((value) => value.length), 0);
  const averageValue = values.length > 0 ? values.reduce((sum, value) => sum + value.length, 0) / values.length : 0;
  const contentWeight = contentLengthWeight(longestValue, averageValue);
  if (isKeyValueTable(headers)) return index === 0 ? clampWeight(contentWeight, 0.54, 0.74) : clampWeight(contentWeight, 2.75, 3.55);
  if (/^(人数|人次|数量)$/.test(key) && longestValue <= 8) return clampWeight(contentWeight, 0.55, 0.82);
  if (/^(来源|依据|依据章节|轮次)$/.test(key) && longestValue <= 12) return clampWeight(contentWeight, 0.7, 1.0);
  if (/^(角色|资产类型|类型|类别|项目|维度|平台|渠道|方式|阶段|状态|固定变动)$/.test(key) && longestValue <= 16) {
    return clampWeight(contentWeight, 0.75, 1.15);
  }
  if (tableWidth >= 3 && longestValue <= 12 && averageValue <= 8) return clampWeight(contentWeight, 0.72, 1.08);
  if (tableWidth === 3) {
    if (index === 0 && /^(月|月份|阶段|方式|媒介|渠道|平台|类型|类目)$/.test(key)) return clampWeight(contentWeight, 0.78, 1.05);
    if (index === 1 && /^(目标|内容形式|故事类型|维度|说明)$/.test(key)) return clampWeight(contentWeight, 1.35, 2.35);
    if (index === 2 && /^(内容|内容产出|输出内容|频率|发布频率|节奏|发布节奏|说明|优先级)$/.test(key)) return clampWeight(contentWeight, 1.9, 2.85);
  }
  if (/^(序号|编号|排名|id|no)$/i.test(key) || /^(序号|编号|排名|痛点编号)$/.test(key)) return clampWeight(contentWeight, 0.55, 0.82);
  if (/^(年份|年度)$/.test(key)) return clampWeight(contentWeight, 0.82, 1.28);
  if (/^(月|月份|阶段|方式|媒介|渠道|平台|故事类型|内容形式|目标|类型|类目|竞品名|品牌名|竞争者)$/.test(key)) return clampWeight(contentWeight, 0.88, 1.35);
  if (/^(频率|发布频率|节奏|发布节奏)$/.test(key)) return clampWeight(contentWeight, 1.7, 2.65);
  if (/^(内容|内容产出|输出内容|核心内容)$/.test(key)) return clampWeight(contentWeight, 2.25, 3.1);
  if (/(数据来源|来源|测算依据|时效限制|依据|备注|说明)/.test(key)) {
    return longestValue <= 24 ? clampWeight(contentWeight, 1.05, 1.85) : clampWeight(contentWeight, 1.85, 3.05);
  }
  if (/(核心特征|明显短板|短板|缺陷|不足|机会点|机会|风险|解决方案|方案|解法|需求|痛点|描述|说明|具体说明|原因|建议|方向|策略|内容|分析|结论|理由|脚本|文案|金句)/.test(key)) return clampWeight(contentWeight, 2.15, 3.25);
  if (/(目标人群|核心人群|用户画像|人群画像|客群|受众)/.test(key)) return clampWeight(contentWeight, 1.45, 2.45);
  if (/(市场规模|预测市场规模|规模|用户规模|门店规模|营收规模|年营收|融资)/.test(key)) return clampWeight(contentWeight, 1.0, 1.65);
  if (/(同比增速|预测增速|增速|增长率|复合增长率|cagr)$/i.test(key)) return clampWeight(contentWeight, 0.82, 1.18);
  if (/(市占率|占比|比例|评分|程度|紧迫度|可行性|等级|状态)$/.test(key)) return clampWeight(contentWeight, 0.78, 1.2);
  if (/(时间|周期|数量|容量|预算|金额|价格|单价|成本|售价|毛利|预估|价格带)$/.test(key)) return clampWeight(contentWeight, 0.9, 1.35);
  return clampWeight(contentWeight, 0.8, 2.7);
}

function renderTableColgroup(rows: MarkdownTableRow[]) {
  const headers = rows[0] || [];
  if (headers.length === 0) return '';
  const bodyRows = rows.slice(1);
  const weights = headers.map((header, index) => tableColumnWeight(header, bodyRows, index, headers));
  const total = weights.reduce((sum, weight) => sum + weight, 0) || 1;
  return `<colgroup>${weights.map((weight) => `<col style="width:${((weight / total) * 100).toFixed(2)}%" />`).join('')}</colgroup>`;
}

function isRightAlignedTableColumn(header: string, rows: MarkdownTableRow[], index: number) {
  const key = headerKey(header);
  if (index === 0) return false;
  if (/^(年份|年度)$/.test(key)) return false;
  if (/(收入来源|数据来源|来源|测算依据|时效限制|依据|备注|说明)/.test(key)) return false;
  if (/(同比增速|预测增速|增速|增长率|复合增长率|cagr|市占率|占比|比例|评分|程度|紧迫度|可行性|等级|状态)$/i.test(key)) return true;
  if (/(市场规模|预测市场规模|用户规模|门店规模|营收规模|年营收|融资|预算|金额|价格|单价|成本|售价|毛利|价格带)$/.test(key)) return true;
  if (/(收入估算|月收入|年收入|稳定期月收入估算)$/.test(key)) return true;
  return false;
}

function tableColumnLongestValue(header: string, rows: MarkdownTableRow[], index: number) {
  const key = headerKey(header);
  const values = rows.map((row) => plainCell(cellAt(row, index)));
  return Math.max(key.length, ...values.map((value) => value.length), 0);
}

function isDescriptiveOrSourceTableColumn(header: string) {
  const key = headerKey(header);
  return /(年份|年度|收入来源|数据来源|来源|测算依据|时效限制|依据|备注|说明|内容|描述|结论|核心特征|机会点|风险|策略|建议|脚本|文案|金句)/.test(key);
}

function isCompactTwoColumnComparisonTable(headers: MarkdownTableRow, rows: MarkdownTableRow[]) {
  if (headers.length !== 2 || rows.length === 0) return false;
  if (isKeyValueTable(headers)) return false;
  if (headers.some((header) => isDescriptiveOrSourceTableColumn(header))) return false;
  return headers.every((header, index) => tableColumnLongestValue(header, rows, index) <= 18);
}

function isCenterAlignedTableColumn(header: string, rows: MarkdownTableRow[], index: number) {
  if (isRightAlignedTableColumn(header, rows, index)) return false;
  const key = headerKey(header);
  if (/^(年份|年度|收入来源|数据来源|测算依据|时效限制|备注|说明)$/.test(key)) return false;
  const longestValue = tableColumnLongestValue(header, rows, index);
  const values = rows.map((row) => plainCell(cellAt(row, index))).filter(Boolean);
  const averageValue = values.length > 0 ? values.reduce((sum, value) => sum + value.length, 0) / values.length : 0;
  if (/^(序号|编号|排名|id|no|痛点编号|类目|类别|项目|维度|方式|渠道|平台|媒介|阶段|类型|月份|月|人数|人次|数量|来源|依据|依据章节|轮次|角色|资产类型|固定变动)$/.test(key)) {
    return longestValue <= 18;
  }
  return rows.length > 0 && longestValue <= 18 && averageValue <= 12;
}

function tableCellClassName(headers: MarkdownTableRow, bodyRows: MarkdownTableRow[], index: number) {
  const header = headers[index] || '';
  const key = headerKey(header);
  const classes = ['md-td'];
  const keyValueTable = isKeyValueTable(headers);
  if (keyValueTable && index === 0) classes.push('md-td-label');
  if (isCompactTwoColumnComparisonTable(headers, bodyRows)) {
    classes.push('md-td-center');
  } else {
    if (isRightAlignedTableColumn(header, bodyRows, index)) classes.push('md-td-right');
    if (!keyValueTable && isCenterAlignedTableColumn(header, bodyRows, index)) classes.push('md-td-center');
  }
  if (/^(序号|编号|排名|id|no|痛点编号)$/i.test(key)) classes.push('md-td-compact');
  if (/(核心特征|短板|缺陷|不足|机会点|机会|风险|解决方案|方案|解法|需求|痛点|描述|说明|具体说明|原因|建议|方向|策略|内容|分析|结论|理由|脚本|文案|金句)/.test(key)) classes.push('md-td-rich');
  return classes.join(' ');
}

function isStoryOutputTable(headers: MarkdownTableRow, rows: MarkdownTableRow[]) {
  if (rows.length === 0) return false;
  const storyFieldIndexes = [
    firstHeaderIndex(headers, ['核心金句', '金句']),
    firstHeaderIndex(headers, ['短视频脚本', '短视频', '视频脚本']),
    firstHeaderIndex(headers, ['图文文案', '图文']),
    firstHeaderIndex(headers, ['私域文案', '私域']),
    firstHeaderIndex(headers, ['适用平台', '平台']),
  ].filter((index): index is number => index !== null);
  const uniqueStoryFieldCount = new Set(storyFieldIndexes).size;
  const hasCode = firstHeaderIndex(headers, ['序号', '内容编号', '故事编号']) !== null;
  const hasStoryContext = firstHeaderIndex(headers, ['故事ID', '故事类型', '故事角度']) !== null;
  return hasCode && hasStoryContext && uniqueStoryFieldCount >= 4;
}

function storyGroupTitle(row: MarkdownTableRow, code: string, typeIndex: number | null) {
  const explicitType = plainCell(cellAt(row, typeIndex));
  if (explicitType) return explicitType;
  const prefix = plainCell(code).match(/[A-Za-z]/)?.[0]?.toUpperCase();
  return prefix ? STORY_GROUP_BY_PREFIX[prefix] || '故事内容' : '故事内容';
}

function storySummaryTitle(row: MarkdownTableRow, storyIdIndex: number | null, angleIndex: number | null, codeIndex: number | null, fallback: string) {
  const storyId = plainCell(cellAt(row, storyIdIndex));
  const angle = plainCell(cellAt(row, angleIndex));
  const code = plainCell(cellAt(row, codeIndex));
  if (storyId && angle && storyId !== angle) return `${storyId} · ${angle}`;
  return storyId || angle || code || fallback;
}

function splitPlatforms(cell: string) {
  const normalized = plainCell(cell).replace(/以及/g, '、').replace(/及/g, '、');
  return normalized
    .split(/[、,，/|]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function renderStoryField(label: string, value: string, extraClass = '') {
  if (!plainCell(value)) return '';
  const textLength = plainCell(value).length;
  const shouldCollapse = !extraClass.includes('md-story-quote-block')
    && /(短视频脚本|视频脚本|图文文案|私域文案|正文|脚本|文案)/.test(plainCell(label));
  if (shouldCollapse) {
    return `<details class="md-story-field md-story-collapsible-field${extraClass}"><summary><span class="md-story-field-label">${plainCell(label)}</span><span class="md-story-field-count">${textLength}字</span></summary><div class="md-story-field-body">${value}</div></details>`;
  }
  return `<div class="md-story-field${extraClass}"><div class="md-story-field-label">${plainCell(label)}</div><div class="md-story-field-body">${value}</div></div>`;
}

function renderStoryMetaField(headers: MarkdownTableRow, row: MarkdownTableRow, indexes: Array<number | null>) {
  const items = indexes
    .filter((index): index is number => index !== null)
    .map((index) => {
      const value = cellAt(row, index);
      if (!plainCell(value)) return '';
      return `<span><strong>${plainCell(headers[index])}：</strong>${value}</span>`;
    })
    .filter(Boolean);
  if (items.length === 0) return '';
  return `<div class="md-story-field md-story-meta-field"><div class="md-story-field-label">基础信息</div><div class="md-story-field-body">${items.join('')}</div></div>`;
}

function renderStoryAccordion(headers: MarkdownTableRow, rows: MarkdownTableRow[]) {
  const codeIndex = firstHeaderIndex(headers, ['序号', '内容编号', '故事编号']) ?? firstHeaderIndex(headers, ['故事ID']);
  const storyIdIndex = firstHeaderIndex(headers, ['故事ID']);
  const typeIndex = firstHeaderIndex(headers, ['故事类型']);
  const angleIndex = firstHeaderIndex(headers, ['故事角度']);
  const platformIndex = firstHeaderIndex(headers, ['适用平台', '平台']);
  const quoteIndex = firstHeaderIndex(headers, ['核心金句', '金句']);
  const excluded = new Set(
    [codeIndex, storyIdIndex, typeIndex, angleIndex, platformIndex, quoteIndex].filter((index): index is number => index !== null),
  );
  const fieldIndexes = headers.map((_header, index) => index).filter((index) => !excluded.has(index));

  const groups: Array<{ title: string; rows: MarkdownTableRow[] }> = [];
  const groupLookup = new Map<string, MarkdownTableRow[]>();
  rows.forEach((row) => {
    const code = cellAt(row, codeIndex);
    const title = storyGroupTitle(row, code, typeIndex);
    if (!groupLookup.has(title)) {
      groupLookup.set(title, []);
      groups.push({ title, rows: groupLookup.get(title)! });
    }
    groupLookup.get(title)!.push(row);
  });

  let firstItem = true;
  const parts = ['<div class="md-story-accordion">'];
  groups.forEach((group) => {
    parts.push('<section class="md-story-group">');
    parts.push(`<div class="md-story-group-head"><strong>${group.title}</strong><span>${group.rows.length}条内容</span></div>`);
    group.rows.forEach((row) => {
      const code = cellAt(row, codeIndex);
      const title = storySummaryTitle(row, storyIdIndex, angleIndex, codeIndex, group.title);
      const quote = cellAt(row, quoteIndex);
      const platforms = splitPlatforms(cellAt(row, platformIndex));
      const openAttr = firstItem ? ' open' : '';
      firstItem = false;

      parts.push(`<details class="md-story-item"${openAttr}>`);
      parts.push('<summary>');
      parts.push(`<span class="md-story-code">${code}</span>`);
      parts.push('<span class="md-story-summary-main">');
      parts.push(`<span class="md-story-title">${title}</span>`);
      if (plainCell(quote)) parts.push(`<span class="md-story-quote">${quote}</span>`);
      parts.push('</span>');
      parts.push(`<span class="md-story-platforms">${platforms.map((platform) => `<span>${platform}</span>`).join('')}</span>`);
      parts.push('</summary>');
      parts.push('<div class="md-story-detail">');
      parts.push(renderStoryMetaField(headers, row, [codeIndex, storyIdIndex, angleIndex, platformIndex]));
      parts.push(renderStoryField('核心金句', quote, ' md-story-quote-block'));
      fieldIndexes.forEach((index) => {
        parts.push(renderStoryField(headers[index], cellAt(row, index)));
      });
      parts.push('</div>');
      parts.push('</details>');
    });
    parts.push('</section>');
  });
  parts.push('</div>');
  return parts.join('');
}

function renderMarkdownTable(rows: MarkdownTableRow[]) {
  const normalizedRows = normalizeTableRows(rows);
  const columnCount = normalizedRows[0]?.length || 1;
  const headers = normalizedRows[0] || [];
  const bodyRows = normalizedRows.slice(1);
  const tableClasses = ['md-table', `md-table-cols-${columnCount}`];
  if (isKeyValueTable(headers)) tableClasses.push('md-table-kv');
  return `<table class="${tableClasses.join(' ')}">` + renderTableColgroup(normalizedRows) + '<tbody>' + normalizedRows.map((row, rowIndex) => {
    const tag = rowIndex === 0 ? 'th' : 'td';
    return `<tr>${row.map((cell, cellIndex) => `<${tag} class="${tableCellClassName(headers, bodyRows, cellIndex)}">${cell}</${tag}>`).join('')}</tr>`;
  }).join('') + '</tbody></table>';
}

export function renderMarkdown(content: string): string {
  let html = content;
  // ── Pre-clean: collapse 3+ consecutive newlines into 2 ──
  html = html.replace(/\n{3,}/g, '\n\n');
  // ── Extract SVG blocks ──
  const svgBlocks: string[] = [];
  html = html.replace(/```svg\n([\s\S]*?)```/g, (_m, svg: string) => {
    svgBlocks.push(svg.trim());
    return `%%SVG_${svgBlocks.length - 1}%%`;
  });
  html = html.replace(/```xml\n([\s\S]*?)```/g, (_m, code: string) => {
    if (code.includes('<svg') && code.includes('</svg>')) {
      svgBlocks.push(code.trim());
      return `%%SVG_${svgBlocks.length - 1}%%`;
    }
    return `<pre class="md-code-block"><code>${code.replace(/</g,'&lt;')}</code></pre>`;
  });
  const protectedDevHints = protectDeveloperHintLines(html);
  html = protectedDevHints.html;

  // ── Block elements ──
  html = html.replace(/^[-]{3,}\s*$/gm, '<hr class="md-hr"/>');
  html = html.replace(/^#### (.*)/gm, '<h5 class="md-h5">$1</h5>');
  html = html.replace(/^### (.*)/gm, '<h4 class="md-h4">$1</h4>');
  html = html.replace(/^## (.*)/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^# (.*)/gm, '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^> (.*)/gm, '<blockquote class="md-blockquote">$1</blockquote>');
  html = html.replace(/^- (.*)/gm, '<li class="md-li">$1</li>');
  html = html.replace(/^(\d+)[、.)]\s*(.*)/gm, '<li class="md-li-ordered"><strong class="md-num">$1.</strong> $2</li>');

  // ── Chart directive: BAR / HBAR / PIE ──
  html = html.replace(/^(BAR|HBAR|PIE):\s*(.+)$/gm, (_m: string, type: string, data: string) => {
    const items = data.split(',').map(s => {
      const parts = s.split('|');
      if (parts.length < 2) return null;
      return { label: parts[0].trim(), value: parts.slice(1).join('|').trim() };
    }).filter(Boolean) as { label: string; value: string }[];
    if (items.length === 0) return '';
    const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16', '#ec4899'];
    if (type === 'PIE') {
      return '<div class="md-chart-legend">' + items.map((item, i) =>
        `<div class="md-chart-legend-item"><span class="md-chart-dot" style="background:${colors[i % colors.length]}"></span><span class="md-chart-legend-label">${item.label}</span><strong class="md-chart-legend-value">${item.value}</strong></div>`
      ).join('') + '</div>';
    }
    const nums = items.map(i => parseFloat(String(i.value).replace(/[^0-9.]/g, '')) || 0);
    const maxNum = Math.max(...nums, 1);
    return '<div class="md-chart-bar">' + items.map((item, i) => {
      const pct = Math.round((nums[i] / maxNum) * 100);
      return `<div class="md-chart-bar-row"><span class="md-chart-bar-label">${item.label}</span><span class="md-chart-bar-track"><span class="md-chart-bar-fill" style="width:${pct}%;background:${colors[i % colors.length]}"></span></span><span class="md-chart-bar-value">${item.value}</span></div>`;
    }).join('') + '</div>';
  });

  // ── Inline ──
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="md-bold">$1</strong>');
  html = html.replace(/!\[(.+?)\]\((.+?)\)/g, '<img src="$2" alt="$1" style="max-width:100%;border-radius:8px;margin:4px 0" />');
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" class="md-link">$1</a>');
  html = html.replace(/`([^`]+)`/g, '<code class="md-code">$1</code>');
  html = html.replace(/━+/g, ''); // remove full-width dividers
  html = concealDeveloperHints(html);

  // ── Line processing ──
  const lines = html.split('\n');
  const out: string[] = [];
  let buf: string[] = [];
  let blanks = 0;

  let tableRows: MarkdownTableRow[] = [];

  function flushTable() {
    if (tableRows.length === 0) return;
    const normalizedRows = normalizeTableRows(tableRows);
    const headers = normalizedRows[0] || [];
    const rows = normalizedRows.slice(1);
    out.push(isStoryOutputTable(headers, rows) ? renderStoryAccordion(headers, rows) : renderMarkdownTable(tableRows));
    tableRows = [];
  }

  function flushBuf() {
    if (buf.length === 0) return;
    flushTable();
    out.push(`<p class="md-p">${buf.join('<br/>')}</p>`);
    buf = [];
  }

  for (const line of lines) {
    const t = line.trim();
    const devGhostMatch = t.match(/^%%DEV_GHOST_LINE_(\d+)%%$/);
    if (devGhostMatch) {
      flushBuf();
      flushTable();
      blanks = 0;
      const hiddenLine = protectedDevHints.lines[Number(devGhostMatch[1])] || '';
      out.push(`<div class="md-dev-ghost-line" aria-hidden="true">${escapeHtml(hiddenLine)}</div>`);
      continue;
    }
    // SVG placeholder
    if (t.startsWith('%%SVG_')) {
      flushBuf(); blanks = 0;
      const idx = parseInt(t.match(/\d+/)![0], 10);
      if (svgBlocks[idx]) out.push(`<div class="md-svg-container">${svgBlocks[idx]}<button class="md-svg-save-btn" onclick="var s=this.parentElement.querySelector('svg').outerHTML;var b=new Blob([s],{type:'image/svg+xml'});var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='logo.svg';a.click();URL.revokeObjectURL(a.href)" title="保存图片">⬇</button></div></div>`);
      continue;
    }
    // Table row detection
    if (/^\|.*\|$/.test(t)) {
      flushBuf();
      const cells = splitMarkdownTableCells(t);
      if (isMarkdownSeparatorRow(cells)) continue; // skip |---| separator
      tableRows.push(cells);
      blanks = 0;
      continue;
    }
    // Not a table row → close any open table
    if (tableRows.length > 0) flushTable();
    // Block tags
    if (t.startsWith('<li') || t.startsWith('<h') || t.startsWith('<hr') || t.startsWith('<blockquote') || t.startsWith('<pre')) {
      flushBuf(); blanks = 0;
      out.push(line);
      continue;
    }
    // Blank line
    if (t === '') {
      blanks++;
      if (blanks === 1) flushBuf();
      continue;
    }
    blanks = 0;
    buf.push(line);
  }
  flushBuf();
  flushTable();
  return out.join('');
}
