"""DeepSeek 客户端（兼容旧接口）"""
from .router import call_llm


def call_deepseek(system_prompt: str, user_message: str, timeout: int = 300, max_tokens: int = 8192, model: str = None) -> str:
    return call_llm(system_prompt, user_message, timeout, max_tokens, model)
