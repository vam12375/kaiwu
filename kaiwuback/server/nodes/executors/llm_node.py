"""Generic LLM-backed node executor."""

from __future__ import annotations

from server.nodes.executors.base import NodeExecutionContext, NodeExecutionResult
from server.orchestrator.llm_engine import generate_ai_response


class LlmNodeExecutor:
    def __init__(self, node_id: str):
        self.node_id = node_id

    def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        content = generate_ai_response(
            self.node_id,
            context.message,
            context.history,
            context.model,
            context.is_followup,
        )
        return NodeExecutionResult(content=content)

