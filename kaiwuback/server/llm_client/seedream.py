"""火山方舟豆包Seedream 图片生成客户端"""
from __future__ import annotations

import requests

from server.config import SEEDREAM_API_KEY, SEEDREAM_URL, SEEDREAM_MODEL


def call_seedream(
    prompt: str,
    size: str = "2K",
    *,
    model: str | None = None,
    reference_images: list[str] | None = None,
) -> list[str]:
    """调用火山方舟豆包 Seedream 生成图片，返回 URL 列表。"""
    selected_model = model or SEEDREAM_MODEL
    headers = {
        "Authorization": f"Bearer {SEEDREAM_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": selected_model,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": True,
    }

    if reference_images:
        body["image"] = reference_images[0] if len(reference_images) == 1 else reference_images

    print(f"  🎨 Seedream生成中 (model={selected_model})...", flush=True)
    resp = requests.post(SEEDREAM_URL, headers=headers, json=body, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Seedream API {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    urls = [img["url"] for img in data.get("data", []) if img.get("url")]
    if urls:
        print(f"  ✅ Seedream完成: {len(urls)}张", flush=True)
    return urls
