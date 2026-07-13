"""Request-to-task payload builder."""

from __future__ import annotations

from typing import Any

ALLOWED_IMAGE_RATIOS = {"21:9", "16:9", "3:2", "4:3", "1:1", "3:4", "2:3", "9:16"}
ALLOWED_IMAGE_RESOLUTIONS = {"2K", "4K"}
ALLOWED_IMAGE_MODELS = {
    "doubao-seedream-5-0-260128",
    "doubao-seedream-5-0-lite-260128",
    "doubao-seedream-4-5-251128",
    "doubao-seedream-4-0-250828",
}
MAX_IMAGE_COUNT = 4
MAX_REFERENCE_IMAGES = 4
MAX_REFERENCE_IMAGE_DATA_URL_LENGTH = 12 * 1024 * 1024
MAX_SKILL_CONTEXT_TEXT_LENGTH = 8000


def _normalize_image_count(value: Any) -> int:
    try:
        count = int(value or 1)
    except (TypeError, ValueError):
        count = 1
    return max(1, min(MAX_IMAGE_COUNT, count))


def _normalize_reference_images(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    images: list[dict[str, Any]] = []
    for item in value[:MAX_REFERENCE_IMAGES]:
        if not isinstance(item, dict):
            continue
        data_url = item.get("data_url")
        if not isinstance(data_url, str):
            continue
        if not data_url.startswith("data:image/"):
            continue
        if len(data_url) > MAX_REFERENCE_IMAGE_DATA_URL_LENGTH:
            continue
        try:
            image_size = int(item.get("size") or 0)
        except (TypeError, ValueError):
            image_size = 0
        images.append(
            {
                "name": str(item.get("name") or "reference.png")[:120],
                "mime_type": str(item.get("mime_type") or "image/png")[:80],
                "size": image_size,
                "data_url": data_url,
            }
        )
    return images


def _clean_skill_context_text(value: Any, limit: int = MAX_SKILL_CONTEXT_TEXT_LENGTH) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


def _normalize_skill_context(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None

    name = _clean_skill_context_text(value.get("name"), 120)
    if not name:
        return None

    return {
        "id": _clean_skill_context_text(value.get("id"), 120),
        "name": name,
        "description": _clean_skill_context_text(value.get("description"), 500),
        "category": _clean_skill_context_text(value.get("category"), 80),
        "doc": _clean_skill_context_text(value.get("doc")),
        "full_content": _clean_skill_context_text(value.get("full_content")),
    }


def build_task_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize API input into the runtime task payload."""
    message = (data.get("message") or "").strip()
    image_model = data.get("image_model") if data.get("image_model") in ALLOWED_IMAGE_MODELS else None
    has_reference_images = isinstance(data.get("reference_images"), list) and len(data.get("reference_images") or []) > 0
    is_image_task = data.get("task_type") == "image_generation" or image_model is not None or has_reference_images
    task_type = "image_generation" if is_image_task else "chat"
    image_ratio = data.get("image_ratio") if data.get("image_ratio") in ALLOWED_IMAGE_RATIOS else "1:1"
    image_resolution = data.get("image_resolution") if data.get("image_resolution") in ALLOWED_IMAGE_RESOLUTIONS else "2K"
    payload = {
        "message": message,
        "history": data.get("history") or [],
        "task_type": task_type,
        "image_model": image_model,
        "image_ratio": image_ratio,
        "image_resolution": image_resolution,
        "image_count": _normalize_image_count(data.get("image_count")),
        "reference_images": _normalize_reference_images(data.get("reference_images")),
        "followup_node": data.get("followup_node"),
        "model": data.get("model"),
        "conversation_id": data.get("conversation_id"),
        "skill_context": _normalize_skill_context(data.get("skill_context")),
        "stream": bool(data.get("stream", True)),
    }
    return payload
