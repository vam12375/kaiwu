"""File-related tool handlers."""

from __future__ import annotations

from server.tools.registry import ToolSpec, tool_registry
from server.utils.common import generate_html_file, save_project_file


def generate_html(payload: dict):
    return generate_html_file(payload["content"], payload.get("title", "AI对话"))


def save_project_html(payload: dict):
    html = payload.get("html") or generate_html(payload)
    return save_project_file(html, payload.get("title", "AI对话"), payload.get("folder", "AI 对话产出"), "html")


tool_registry.register(
    ToolSpec(
        name="file.generate_html",
        handler=generate_html,
        input_schema={"required": ["content"]},
        output_schema={"type": "html"},
        permission="project_files.write",
        timeout=30,
    )
)
tool_registry.register(
    ToolSpec(
        name="file.save_project_html",
        handler=save_project_html,
        input_schema={"required": ["content", "title"]},
        output_schema={"type": "path"},
        permission="project_files.write",
        timeout=30,
    )
)

