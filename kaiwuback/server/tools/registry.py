"""Central registry for external capabilities/tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    handler: ToolHandler
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    permission: str = "internal"
    timeout: int = 60
    retry_policy: dict[str, Any] = field(default_factory=lambda: {"retries": 0})
    audit_log: bool = True


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec):
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def list(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def call(self, name: str, payload: dict[str, Any]) -> Any:
        spec = self.get(name)
        if not spec:
            raise KeyError(f"tool not registered: {name}")
        return spec.handler(payload)


tool_registry = ToolRegistry()

