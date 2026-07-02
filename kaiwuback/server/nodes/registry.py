"""Node metadata registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from server.intent.recognizer import DEPENDENCIES
from server.nodes.prompts import NODES, NODE_SYSTEM_PROMPTS


@dataclass(frozen=True)
class NodeMetadata:
    id: str
    name: str
    icon: str
    steps: list[dict[str, Any]]
    prompt: str
    dependencies: dict[str, list[str]]
    need_search: bool = False
    expected_duration: int = 30


def get_node_metadata(node_id: str) -> NodeMetadata | None:
    node = NODES.get(node_id)
    if not node:
        return None
    return NodeMetadata(
        id=node_id,
        name=node["name"],
        icon=node["icon"],
        steps=node.get("steps", []),
        prompt=NODE_SYSTEM_PROMPTS.get(node_id, ""),
        dependencies=DEPENDENCIES.get(node_id, {"hard": [], "soft": []}),
        need_search=bool(node.get("need_search", False)),
        expected_duration=int(node.get("expected_duration", 90 if node.get("need_search") else 30)),
    )


def list_node_metadata() -> list[NodeMetadata]:
    return [meta for node_id in NODES.keys() if (meta := get_node_metadata(node_id))]

