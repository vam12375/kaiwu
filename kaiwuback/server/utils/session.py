"""会话状态管理（追问识别系统）"""
from server.intent.recognizer import _session_state


def save_session_state(history: list, node_id: str):
    """保存对话核心状态：主题、实体、报告结构"""
    if not history:
        return
    all_text = " ".join([m.get("content", "")[:500] for m in history[-6:]])
    entities = set()
    for kw in ["市场", "行业", "消费者", "品牌", "产品", "定价", "渠道", "竞品", "风险",
               "增速", "规模", "画像", "痛点", "差异", "供应链", "流量", "库存", "营收"]:
        if kw in all_text:
            entities.add(kw)
    _session_state.clear()
    _session_state["entities"] = list(entities)[:10]
    _session_state["last_node"] = node_id
    _session_state["has_report"] = "市场调研报告" in all_text or "七层" in all_text


def reset_session_state():
    """重置会话状态"""
    _session_state.clear()
