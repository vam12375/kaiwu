"""Base interfaces for node executors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class NodeExecutionContext:
    task_id: str
    node_id: str
    message: str
    history: list[dict[str, Any]] = field(default_factory=list)
    model: str | None = None
    is_followup: bool = False


@dataclass
class NodeExecutionResult:
    content: str
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class NodeExecutor(Protocol):
    node_id: str

    def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        """Execute a node and return its text/artifact result."""

