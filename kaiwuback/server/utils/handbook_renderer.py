"""产品手册 HTML 渲染器 —— 纯函数，从 Markdown 直接渲染，不经过 LLM"""
from server.utils.markdown import markdown_to_html
from server.utils.report_html import render_report_html


def render_handbook_to_html(markdown_content: str, title: str, subtitle: str = "") -> str:
    """将产品手册/营销方案的 Markdown 内容渲染为专业 HTML 页面。

    不调用任何 LLM —— 内容已在 Markdown 中完整提供。
    """
    body_html = markdown_to_html(markdown_content)
    return render_report_html(body_html, title, subtitle)
