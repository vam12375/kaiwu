"""统一LLM调用路由 —— 注册表模式，新增提供商只需注册"""
import requests
from server.config import DEEPSEEK_URL, DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DOUBAO_URL, DOUBAO_API_KEY, DOUBAO_MODEL


def _call_deepseek(system_prompt: str, user_message: str, timeout: int = 300, max_tokens: int = 8192, **_kw) -> str:
    resp = requests.post(
        DEEPSEEK_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json={"model": DEEPSEEK_MODEL, "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ], "max_tokens": max_tokens, "temperature": 0.2, "stream": False},
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"DeepSeek API {resp.status_code}: {resp.text[:300]}")
    msg = resp.json()["choices"][0]["message"]
    content = msg.get("content", "")
    # deepseek-v4-pro 是推理模型，推理可能吞掉所有 token 导致 content 为空，回退到 reasoning_content
    if not content or len(content.strip()) < 10:
        reasoning = msg.get("reasoning_content", "")
        if reasoning:
            return reasoning
    return content


def _call_doubao(system_prompt: str, user_message: str, timeout: int = 300, max_tokens: int = 8192, model: str = None, **_kw) -> str:
    model_name = model or DOUBAO_MODEL
    resp = requests.post(
        DOUBAO_URL,
        headers={"Authorization": f"Bearer {DOUBAO_API_KEY}", "Content-Type": "application/json"},
        json={"model": model_name, "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ], "max_tokens": max_tokens, "temperature": 0.2, "stream": False},
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Doubao API {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"]


# 注册表：provider_key → callable
PROVIDER_REGISTRY = {
    "deepseek": _call_deepseek,
    "doubao": _call_doubao,
}


def call_llm(system_prompt: str, user_message: str, timeout: int = 300, max_tokens: int = 8192, model: str = None) -> str:
    """统一LLM调用 —— 根据 model 参数在注册表中查找对应提供商

    路由规则：model 参数中包含注册表 key 则使用该提供商，否则默认 deepseek
    例如 model="doubao-seed-2-0-lite" → 路由到豆包
    """
    provider = "deepseek"  # default
    if model:
        for key in PROVIDER_REGISTRY:
            if key in model.lower():
                provider = key
                break

    handler = PROVIDER_REGISTRY.get(provider, _call_deepseek)
    return handler(system_prompt, user_message, timeout=timeout, max_tokens=max_tokens, model=model)
