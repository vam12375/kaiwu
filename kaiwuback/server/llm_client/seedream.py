"""火山方舟豆包Seedream文生图客户端"""
import requests, time
from server.config import SEEDREAM_API_KEY, SEEDREAM_URL, SEEDREAM_MODEL


def call_seedream(prompt: str, size: str = "2K") -> list[str]:
    """调用火山方舟豆包Seedream生成图片，返回URL列表"""
    headers = {
        "Authorization": f"Bearer {SEEDREAM_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": SEEDREAM_MODEL,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": True,
    }
    print(f"  🎨 Seedream生成中 (model={SEEDREAM_MODEL})...", flush=True)
    resp = requests.post(SEEDREAM_URL, headers=headers, json=body, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Seedream API {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    urls = [img["url"] for img in data.get("data", []) if img.get("url")]
    if urls:
        print(f"  ✅ Seedream完成: {len(urls)}张", flush=True)
    return urls
