"""Request-to-task payload builder."""

from __future__ import annotations

from typing import Any


def build_task_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize API input into the runtime task payload."""
    message = (data.get("message") or "").strip()
    payload = {
        "message": message,
        "history": data.get("history") or [],
        "image_ratio": data.get("image_ratio") or "1:1",
        "image_count": int(data.get("image_count") or 1),
        "followup_node": data.get("followup_node"),
        "model": data.get("model"),
        "conversation_id": data.get("conversation_id"),
        "stream": bool(data.get("stream", True)),
    }
    return payload

