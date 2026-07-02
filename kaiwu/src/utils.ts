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

  // ── Line processing ──
  const lines = html.split('\n');
  const out: string[] = [];
  let buf: string[] = [];
  let blanks = 0;

  let tableRows: string[] = [];
  let tableIsFirst = true;

  function flushTable() {
    if (tableRows.length === 0) return;
    out.push('<table class="md-table"><tbody>' + tableRows.join('') + '</tbody></table>');
    tableRows = [];
    tableIsFirst = true;
  }

  function flushBuf() {
    if (buf.length === 0) return;
    flushTable();
    out.push(`<p class="md-p">${buf.join('<br/>')}</p>`);
    buf = [];
  }

  for (const line of lines) {
    const t = line.trim();
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
      const cells = t.split('|').filter(c => c.trim() !== '').map(c => c.trim());
      if (/^[-:\s]+$/.test(cells.join(''))) continue; // skip |---| separator
      const tag = tableIsFirst ? 'th' : 'td';
      tableRows.push(`<tr>${cells.map(c => `<${tag} class="md-td">${c}</${tag}>`).join('')}</tr>`);
      tableIsFirst = false;
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
