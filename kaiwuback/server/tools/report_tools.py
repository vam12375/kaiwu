"""Report generation tool handlers."""

from __future__ import annotations

from server.reports import generate_summary_report
from server.tools.registry import ToolSpec, tool_registry


def generate_report(payload: dict):
    return generate_summary_report(payload["message"], payload.get("history") or [], payload.get("model"))


tool_registry.register(
    ToolSpec(
        name="report.summary",
        handler=generate_report,
        input_schema={"required": ["message"]},
        output_schema={"type": "report_result"},
        permission="project_files.write",
        timeout=180,
        retry_policy={"retries": 0},
    )
)

