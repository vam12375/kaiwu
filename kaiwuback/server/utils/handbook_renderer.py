"""产品手册 HTML 渲染器 —— 纯函数，从 Markdown 直接渲染，不经过 LLM"""
from datetime import datetime
from server.utils.markdown import markdown_to_html


def render_handbook_to_html(markdown_content: str, title: str, subtitle: str = "") -> str:
    """将产品手册/营销方案的 Markdown 内容渲染为专业 HTML 页面。

    不调用任何 LLM —— 内容已在 Markdown 中完整提供。
    """
    body_html = markdown_to_html(markdown_content)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
:root {{
  --primary: #1a365d; --primary-light: #2c5282;
  --accent: #ed8936; --accent-light: rgba(237,137,54,.08);
  --bg: #f7fafc; --card-bg: #ffffff;
  --text: #2d3748; --text-light: #718096;
  --border: #e2e8f0; --radius: 12px;
  --sans: -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--sans);color:var(--text);background:var(--bg);line-height:1.8;-webkit-font-smoothing:antialiased}}

/* Cover */
.cover{{background:linear-gradient(135deg,var(--primary) 0%,var(--primary-light) 100%);padding:80px 60px;color:#fff}}
.cover h1{{font-size:36px;font-weight:700;margin-bottom:12px;letter-spacing:-0.5px}}
.cover .subtitle{{font-size:18px;opacity:.85;margin-bottom:32px}}
.cover .divider{{width:64px;height:3px;background:var(--accent);margin-bottom:32px}}
.cover .meta{{display:flex;gap:32px;font-size:13px;opacity:.7}}

/* Container */
.container{{max-width:1000px;margin:0 auto;padding:48px 40px}}

/* Section headers */
h1{{font-size:28px;font-weight:700;color:var(--primary);margin:48px 0 20px;padding-bottom:12px;border-bottom:2px solid var(--border)}}
h2{{font-size:22px;font-weight:600;color:var(--primary-light);margin:36px 0 16px}}
h3{{font-size:17px;font-weight:600;color:var(--text);margin:24px 0 12px}}
h4{{font-size:15px;font-weight:600;color:var(--text-light);margin:16px 0 8px}}

/* Content */
p{{margin:10px 0;font-size:15px;color:var(--text);line-height:1.9}}
strong{{color:var(--primary);font-weight:700}}
blockquote{{margin:16px 0;padding:14px 20px;border-left:3px solid var(--accent);background:var(--accent-light);border-radius:0 var(--radius) var(--radius) 0;color:var(--text-light);font-size:14px}}
ul,ol{{margin:10px 0 10px 24px}}
li{{margin:6px 0;font-size:15px;color:var(--text);line-height:1.7}}
hr{{border:0;height:1px;background:linear-gradient(90deg,rgba(99,102,241,.15),transparent);margin:32px 0}}

/* Tables */
table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;background:var(--card-bg);border-radius:var(--radius);overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
thead{{background:linear-gradient(135deg,var(--primary),var(--primary-light))}}
thead th{{color:#fff;padding:12px 16px;text-align:left;font-weight:600;font-size:13px;letter-spacing:.5px}}
tbody td{{padding:10px 16px;border-bottom:1px solid var(--border);color:var(--text)}}
tbody tr:last-child td{{border-bottom:none}}
tbody tr:hover{{background:rgba(237,137,54,.04)}}

/* Code */
code{{background:#f1f5f9;padding:2px 8px;border-radius:4px;font-size:.9em;color:#6366f1;font-family:"SF Mono",Monaco,monospace}}

/* Footer */
.footer{{margin-top:48px;padding:24px 0 0;border-top:1px solid var(--border);color:var(--text-light);font-size:12px;text-align:center}}
.footer a{{color:var(--accent);text-decoration:none}}

/* Print */
@media print{{
  body{{background:#fff}}
  .container{{max-width:100%;padding:20px 0}}
  .cover{{background:var(--primary) !important;-webkit-print-color-adjust:exact}}
}}
</style>
</head>
<body>
<div class="cover">
  <h1>{title}</h1>
  <div class="subtitle">{subtitle or '曜势科技 · AI 生成'}</div>
  <div class="divider"></div>
  <div class="meta">
    <span>曜势科技 Kaiwu</span>
    <span>{datetime.now().strftime('%Y-%m-%d')}</span>
  </div>
</div>
<div class="container">
{body_html}
<div class="footer">
  曜势科技 · 产品手册 · {datetime.now().strftime('%Y-%m-%d %H:%M')}
</div>
</div>
</body>
</html>'''
