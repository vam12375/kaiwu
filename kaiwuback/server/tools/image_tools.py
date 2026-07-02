"""Image generation tool handlers."""

from __future__ import annotations

from server.llm_client import call_seedream
from server.tools.registry import ToolSpec, tool_registry
from server.utils.common import image_ratio_to_size


def generate_image(payload: dict):
    ratio = payload.get("ratio", "1:1")
    return call_seedream(payload["prompt"], size=image_ratio_to_size(ratio))


tool_registry.register(
    ToolSpec(
        name="image.generate",
        handler=generate_image,
        input_schema={"required": ["prompt"]},
        output_schema={"type": "image_urls"},
        permission="llm.image.generate",
        timeout=120,
        retry_policy={"retries": 1, "backoff_seconds": 1},
    )
)

