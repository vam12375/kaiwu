"""工具函数兼容层 —— 从拆分后的子模块重导出，保持已有 import 不中断"""
# Markdown
from server.utils.markdown import markdown_to_html, _escape_html, _render_inline

# File I/O
from server.utils.file_io import (
    generate_html_file, save_project_file, save_project_file_bytes,
    html_to_pdf, image_ratio_to_size, save_image_to_library,
)

# SVG / Logo
from server.utils.svg import generate_logo_svg as _generate_logo_svg
from server.utils.svg import extract_logo_prompts as _extract_logo_prompts

# Database (from persistence layer)
from server.persistence.database import (
    get_db, save_conversation, update_conversation_messages, append_conversation_messages,
    list_conversations, load_conversation, delete_conversation,
    _safe_filename,
)
