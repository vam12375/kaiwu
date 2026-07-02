"""文件 I/O 工具 —— HTML生成、文件归档、图片保存、PDF转换"""
import os, uuid, requests as req
from pathlib import Path
from datetime import datetime

from server.config import PROJECT_LIB, IMG_STORE
from server.utils.markdown import markdown_to_html


def generate_html_file(content: str, title: str) -> str:
    """Generate a beautified, standards-compliant HTML5 file"""
    body_html = markdown_to_html(content)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f8fafc;color:#0f172a;line-height:1.7;padding:40px 20px}}
.container{{max-width:900px;margin:0 auto;background:#fff;border-radius:16px;padding:40px 48px;box-shadow:0 1px 3px rgba(15,23,42,.04);border:1px solid rgba(15,23,42,.06)}}
h1{{font-size:24px;font-weight:700;color:#1e1b4b;margin-bottom:8px}}
h2{{font-size:18px;font-weight:600;color:#0f172a;margin:28px 0 12px;padding-bottom:6px;border-bottom:2px solid rgba(99,102,241,.12)}}
h3{{font-size:15px;font-weight:600;color:#334155;margin:16px 0 8px}}
h4{{font-size:14px;font-weight:600;color:#475569;margin:12px 0 6px}}
p{{margin:8px 0;font-size:14px;color:#475569}}
strong{{color:#1e1b4b;font-weight:700}}
table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px}}
thead th{{background:#f8fafc;padding:8px 12px;text-align:left;font-weight:600;color:#0f172a;border-bottom:2px solid #e2e8f0}}
tbody td{{padding:8px 12px;border-bottom:1px solid #f1f5f9;color:#475569}}
ul,ol{{margin:8px 0 8px 20px}}
li{{margin:4px 0;font-size:14px;color:#475569}}
blockquote{{margin:12px 0;padding:10px 16px;border-left:3px solid #6366f1;background:linear-gradient(90deg,rgba(99,102,241,.04),rgba(139,92,246,.02));border-radius:0 8px 8px 0;color:#64748b;font-size:13px}}
hr{{border:0;height:1px;background:linear-gradient(90deg,rgba(99,102,241,.15),transparent);margin:20px 0}}
code{{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:.9em;color:#6366f1}}
.footer{{margin-top:32px;padding-top:16px;border-top:1px solid #e2e8f0;color:#94a3b8;font-size:12px;text-align:center}}
</style>
</head>
<body>
<div class="container">
{body_html}
<div class="footer">曜势科技 · AI自动生成 · {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</div>
</body>
</html>'''


def save_project_file(content: str, filename: str, folder: str, file_type: str = "html") -> str:
    """Save a file to the project library. Returns the file path."""
    import uuid
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)[:40]
    fname = f"{safe_name}_{uuid.uuid4().hex[:6]}.{file_type}"
    fpath = PROJECT_LIB / folder / fname
    fpath.write_text(content, encoding='utf-8')
    print(f"[FILE] Saved: {folder}/{fname}", flush=True)
    return str(fpath)


def save_project_file_bytes(data_bytes: bytes, filename: str, folder: str, file_type: str) -> str:
    """保存二进制数据到项目库"""
    import uuid
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)[:40]
    fname = f"{safe_name}_{uuid.uuid4().hex[:6]}.{file_type}"
    fpath = PROJECT_LIB / folder / fname
    fpath.write_bytes(data_bytes)
    print(f"[FILE] Saved: {folder}/{fname}", flush=True)
    return str(fpath)


def image_ratio_to_size(ratio: str) -> str:
    """Convert ratio like '16:9' to Seedream size"""
    return "2K"


def save_image_to_library(image_url: str, style: str) -> str:
    """Download image from URL and save to project image library. Dual archive."""
    import uuid
    resp = req.get(image_url, timeout=30)
    resp.raise_for_status()
    ext = "png" if "png" in resp.headers.get("content-type", "") else "jpg"
    filename = f"{style}_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    filepath = IMG_STORE / filename
    filepath.write_bytes(resp.content)
    (PROJECT_LIB / "图片库").mkdir(parents=True, exist_ok=True)
    (PROJECT_LIB / "AI 对话产出").mkdir(parents=True, exist_ok=True)
    (PROJECT_LIB / "图片库" / filename).write_bytes(resp.content)
    (PROJECT_LIB / "AI 对话产出" / filename).write_bytes(resp.content)
    print(f"[IMG] Saved: {filename} (图片库 + AI 对话产出)", flush=True)
    return filename


def html_to_pdf(html_content: str) -> bytes:
    """将HTML内容转换为PDF字节流（WeasyPrint → Chrome headless 降级）"""
    try:
        import weasyprint
        doc = weasyprint.HTML(string=html_content)
        return doc.write_pdf()
    except ImportError:
        import tempfile, subprocess
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
            f.write(html_content)
            html_path = f.name
        pdf_path = html_path.replace('.html', '.pdf')
        try:
            subprocess.run([
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '--headless', '--disable-gpu', '--no-sandbox',
                f'--print-to-pdf={pdf_path}', f'file://{html_path}'
            ], check=True, timeout=30, capture_output=True)
            with open(pdf_path, 'rb') as pf:
                return pf.read()
        finally:
            os.unlink(html_path)
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
