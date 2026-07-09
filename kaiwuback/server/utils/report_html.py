"""Shared report HTML renderer for Kaiwu generated reports."""
from __future__ import annotations

from html import escape
from datetime import datetime


REPORT_CSS = """
:root {
  --primary: #0f172a; --primary-light: #1e293b;
  --accent: #e05a2b; --accent-rgb: 224,90,43; --accent-light: rgba(224,90,43,.07);
  --bg: #f1f5f9; --card-bg: #ffffff;
  --text: #1e293b; --text-light: #64748b; --text-muted: #94a3b8;
  --border: #e2e8f0; --border-light: #f1f5f9;
  --radius: 12px; --radius-lg: 18px;
  --sans: -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:var(--sans);
  color:var(--text);
  background:
    radial-gradient(circle at top left, rgba(var(--accent-rgb),.10), transparent 28%),
    linear-gradient(180deg,#f8fafc 0%,var(--bg) 100%);
  line-height:1.8;
  -webkit-font-smoothing:antialiased;
}
.report-shell{
  max-width:1040px;
  margin:32px auto 56px;
  background:var(--card-bg);
  border:1px solid rgba(226,232,240,.9);
  border-radius:24px;
  overflow:hidden;
  box-shadow:0 20px 70px rgba(15,23,42,.08);
}
.cover{
  background:
    radial-gradient(circle at 82% 18%, rgba(var(--accent-rgb),.28), transparent 24%),
    linear-gradient(135deg,var(--primary) 0%,var(--primary-light) 100%);
  padding:76px 60px 52px;
  color:#fff;
  position:relative;
  overflow:hidden;
}
.cover::before{
  content:"";
  position:absolute;
  inset:0;
  background:
    linear-gradient(rgba(255,255,255,.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px);
  background-size:40px 40px;
  mask-image:linear-gradient(180deg, rgba(0,0,0,.7), transparent 88%);
  pointer-events:none;
}
.cover h1,.cover .subtitle,.cover .divider,.cover .meta{position:relative;z-index:1}
.cover h1{
  font-size:40px;
  line-height:1.18;
  font-weight:800;
  margin-bottom:14px;
  color:#fff;
}
.cover .subtitle{font-size:17px;opacity:.82;margin-bottom:34px;max-width:760px}
.cover .divider{width:58px;height:3px;background:var(--accent);margin-bottom:34px;border-radius:999px}
.cover .meta{display:flex;flex-wrap:wrap;gap:12px;font-size:13px}
.cover .meta span{
  display:inline-flex;
  padding:8px 12px;
  border-radius:999px;
  background:rgba(255,255,255,.10);
  border:1px solid rgba(255,255,255,.16);
  color:rgba(255,255,255,.82);
}
.container{padding:46px 52px 54px}
.report-summary + .container{padding-top:28px}
.report-summary{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:14px;
  margin:24px 52px 0;
  position:relative;
  z-index:2;
}
.data-card{
  border-radius:14px;
  padding:20px 22px;
  min-height:118px;
  box-shadow:0 10px 30px rgba(15,23,42,.08);
}
.data-card.primary{background:linear-gradient(135deg,var(--primary),var(--primary-light));color:#fff}
.data-card.accent{background:linear-gradient(135deg,var(--accent),#f5a623);color:#fff}
.data-card.light{background:#fff;border:1px solid var(--border-light)}
.data-card .card-label{
  font-size:11px;
  font-weight:700;
  letter-spacing:1px;
  text-transform:uppercase;
  margin-bottom:8px;
  opacity:.72;
}
.data-card .card-value{
  font-size:26px;
  line-height:1.2;
  font-weight:900;
  margin-bottom:6px;
  word-break:break-word;
}
.data-card.light .card-value{color:var(--primary)}
.data-card .card-note{font-size:12px;opacity:.72;line-height:1.55}
.content-card{
  margin-top:28px;
  padding:30px;
  border:1px solid var(--border-light);
  border-radius:var(--radius-lg);
  background:linear-gradient(180deg,#fff 0%,#fcfdff 100%);
}
h1{
  font-size:28px;
  line-height:1.3;
  font-weight:800;
  color:var(--primary);
  margin:54px 0 24px;
  padding-bottom:14px;
  border-bottom:2px solid var(--border);
}
h1:first-child{margin-top:0}
h2{
  font-size:26px;
  line-height:1.28;
  font-weight:800;
  color:var(--primary);
  margin:44px 0 14px;
}
h2::before{
  content:"";
  display:block;
  width:28px;
  height:3px;
  background:var(--accent);
  border-radius:999px;
  margin-bottom:10px;
}
h3{
  font-size:18px;
  font-weight:700;
  color:var(--text);
  margin:28px 0 12px;
  padding-left:14px;
  border-left:3px solid var(--accent);
}
h4{
  font-size:14px;
  font-weight:700;
  color:var(--text-muted);
  margin:20px 0 8px;
  text-transform:uppercase;
  letter-spacing:.5px;
}
p{margin:10px 0;font-size:15px;color:var(--text);line-height:2}
p.lead-line{
  margin-top:22px;
  padding:12px 14px;
  border-radius:10px;
  background:#f8fafc;
  border:1px solid var(--border-light);
}
strong{color:var(--primary);font-weight:700}
blockquote{
  margin:18px 0;
  padding:16px 20px;
  border-left:3px solid var(--accent);
  background:var(--accent-light);
  border-radius:0 var(--radius) var(--radius) 0;
  color:var(--text-light);
  font-size:14px;
}
.content-card > ul,
.content-card > ol{
  display:grid;
  gap:10px;
  margin:14px 0 20px;
  padding:0;
  list-style:none;
}
.content-card > ul > li,
.content-card > ol > li{
  margin:0;
  padding:14px 16px;
  border:1px solid var(--border-light);
  border-radius:12px;
  background:#fff;
  font-size:15px;
  color:var(--text);
  line-height:1.85;
  box-shadow:0 1px 2px rgba(15,23,42,.03);
}
.content-card > ol{counter-reset:report-step}
.content-card > ol > li{counter-increment:report-step}
.content-card > ol > li::before{
  content:counter(report-step, decimal-leading-zero);
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-width:28px;
  height:22px;
  margin-right:8px;
  border-radius:999px;
  background:var(--accent-light);
  color:var(--accent);
  font-size:11px;
  font-weight:800;
  vertical-align:1px;
}
.content-card > ul > li:has(strong:first-child),
.content-card > ol > li:has(strong:first-child){
  background:linear-gradient(180deg,#fff 0%,#fbfdff 100%);
}
ul ul, ul ol, ol ul, ol ol{margin:8px 0 8px 22px}
ul ul li, ul ol li, ol ul li, ol ol li{margin:5px 0;font-size:14px;line-height:1.7}
hr{border:0;height:1px;background:linear-gradient(90deg,var(--border),transparent);margin:38px 0}
table{
  width:100%;
  border-collapse:separate;
  border-spacing:0;
  margin:22px 0;
  font-size:14px;
  border-radius:var(--radius);
  overflow:hidden;
  border:1px solid var(--border);
  box-shadow:0 1px 3px rgba(15,23,42,.04);
}
thead th{
  background:var(--primary);
  color:#fff;
  padding:14px 16px;
  text-align:left;
  font-weight:600;
  font-size:12px;
  letter-spacing:.5px;
  text-transform:uppercase;
  white-space:nowrap;
}
tbody td{
  padding:12px 16px;
  border-bottom:1px solid var(--border-light);
  background:var(--card-bg);
  color:var(--text);
  vertical-align:top;
  word-break:break-word;
}
tbody tr:nth-child(even) td{background:#f8fafc}
tbody tr:hover td{background:#fef3c7;transition:background .15s ease}
tbody tr:last-child td{border-bottom:none}
tbody td:first-child{font-weight:600;color:var(--primary)}
.story-accordion{
  display:grid;
  gap:18px;
  margin:24px 0 34px;
}
.story-group{
  border:1px solid var(--border-light);
  border-radius:16px;
  background:linear-gradient(180deg,#fff 0%,#fbfdff 100%);
  padding:18px;
}
.story-group-title{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  margin-bottom:12px;
}
.story-group-title strong{
  font-size:16px;
  color:var(--primary);
}
.story-group-title span{
  color:var(--text-muted);
  font-size:12px;
}
.story-item{
  border:1px solid var(--border);
  border-radius:14px;
  background:#fff;
  overflow:hidden;
  box-shadow:0 1px 3px rgba(15,23,42,.04);
}
.story-item + .story-item{margin-top:10px}
.story-item[open]{box-shadow:0 12px 32px rgba(15,23,42,.08)}
.story-item summary{
  cursor:pointer;
  list-style:none;
  padding:16px 18px;
  display:grid;
  grid-template-columns:auto minmax(0,1fr) auto 28px;
  gap:14px;
  align-items:center;
}
.story-item summary::-webkit-details-marker{display:none}
.story-item summary::after{
  content:"";
  width:8px;
  height:8px;
  border:solid var(--text-muted);
  border-width:0 2px 2px 0;
  transform:rotate(45deg);
  transition:transform .18s ease, border-color .18s ease;
  justify-self:center;
}
.story-item[open] summary::after{
  transform:rotate(-135deg);
  border-color:var(--primary);
}
.story-code{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-width:44px;
  height:30px;
  border-radius:999px;
  background:var(--primary);
  color:#fff;
  font-size:12px;
  font-weight:800;
  letter-spacing:.4px;
}
.story-summary-main{display:grid;gap:4px}
.story-summary-title{
  color:var(--primary);
  font-size:15px;
  font-weight:800;
}
.story-quote{
  color:var(--text-light);
  font-size:13px;
  line-height:1.55;
}
.story-platforms{
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  justify-content:flex-end;
}
.story-platforms span{
  border:1px solid rgba(var(--accent-rgb),.18);
  background:var(--accent-light);
  color:var(--accent);
  border-radius:999px;
  padding:4px 8px;
  font-size:11px;
  font-weight:700;
  white-space:nowrap;
}
.story-detail{
  border-top:1px solid var(--border-light);
  padding:18px;
  display:grid;
  gap:14px;
  background:#fcfdff;
}
.story-field{
  border:1px solid var(--border-light);
  border-radius:12px;
  background:#fff;
  padding:14px 16px;
}
.story-meta-field{
  background:#f8fafc;
}
.story-meta-field .story-field-body{
  display:flex;
  flex-wrap:wrap;
  gap:8px 18px;
}
.story-meta-field .story-field-body span{
  color:var(--text);
}
.story-meta-field .story-field-body strong{
  color:var(--text-muted);
}
.story-field-label{
  color:var(--text-muted);
  font-size:12px;
  font-weight:800;
  letter-spacing:.3px;
  margin-bottom:6px;
}
.story-field-body{
  color:var(--text);
  font-size:14px;
  line-height:1.85;
}
.story-field.quote-block{
  border-left:4px solid var(--accent);
  background:var(--accent-light);
}
.story-field.quote-block .story-field-body{
  color:var(--primary);
  font-size:16px;
  font-weight:800;
}
code{
  background:#f1f5f9;
  padding:2px 8px;
  border-radius:4px;
  font-size:.9em;
  color:var(--accent);
  font-family:"SF Mono",Monaco,monospace;
}
.footer{
  margin-top:48px;
  padding-top:22px;
  border-top:1px solid var(--border);
  color:var(--text-muted);
  font-size:12px;
  text-align:center;
}
@media (max-width:760px){
  body{background:#fff}
  .report-shell{margin:0;border-radius:0;border:none;box-shadow:none}
  .cover{padding:48px 22px 88px}
  .cover h1{font-size:30px}
  .report-summary{grid-template-columns:1fr;margin:18px 18px 0}
  .container{padding:24px 18px 36px}
  .content-card{padding:20px;border-radius:14px}
  h1{font-size:24px}
  h2{font-size:22px}
  table{font-size:12px;display:block;overflow-x:auto;-webkit-overflow-scrolling:touch}
  thead th,tbody td{padding:9px 10px}
  .story-group{padding:12px}
  .story-item summary{grid-template-columns:auto minmax(0,1fr) 28px;gap:10px;padding:14px}
  .story-item summary::after{grid-column:3;grid-row:1}
  .story-platforms{grid-column:1 / -1;justify-content:flex-start}
  .story-detail{padding:14px}
}
@media print{
  body{background:#fff}
  .report-shell{max-width:100%;margin:0;border:none;box-shadow:none;border-radius:0}
  .cover{background:var(--primary)!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .report-summary{margin:18px 0 0;padding:0 20px}
  .container{padding:20px}
}
"""


def render_report_html(body_html: str, title: str, subtitle: str = "") -> str:
    """Render already-converted HTML into Kaiwu's unified report layout."""
    now = datetime.now()
    safe_title = escape(str(title))
    subtitle_text = escape(str(subtitle or "曜势科技 · AI 生成"))
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title}</title>
<style>
{REPORT_CSS}
</style>
</head>
<body>
<div class="report-shell">
  <div class="cover">
    <h1>{safe_title}</h1>
    <div class="subtitle">{subtitle_text}</div>
    <div class="divider"></div>
    <div class="meta">
      <span>曜势科技 Kaiwu</span>
      <span>{now.strftime('%Y-%m-%d')}</span>
    </div>
  </div>
  <div class="report-summary">
    <div class="data-card primary">
      <div class="card-label">报告类型</div>
      <div class="card-value">{safe_title}</div>
      <div class="card-note">统一专业报告模板</div>
    </div>
    <div class="data-card accent">
      <div class="card-label">生成来源</div>
      <div class="card-value">AI 工作流</div>
      <div class="card-note">Node 输出自动排版归档</div>
    </div>
    <div class="data-card light">
      <div class="card-label">交付格式</div>
      <div class="card-value">HTML</div>
      <div class="card-note">支持浏览器阅读与打印导出</div>
    </div>
  </div>
  <div class="container">
    <div class="content-card">
{body_html}
      <div class="footer">曜势科技 · 产品手册 · {now.strftime('%Y-%m-%d %H:%M')}</div>
    </div>
  </div>
</div>
</body>
</html>'''
