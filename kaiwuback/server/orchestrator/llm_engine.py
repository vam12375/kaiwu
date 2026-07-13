"""LLM 响应生成引擎 —— 从 main.py 抽取，负责 prompt 组装与 LLM 调用"""
import re
from server.nodes.prompts import NODE_SYSTEM_PROMPTS
from server.llm_client import call_llm
from server.config import current_date_cn, data_integrity_prompt, DEEPSEEK_REASONING_MODEL


_STATIC_DATE_PREFIX_RE = re.compile(r"^\s*当前日期：\d{4}年\d{1,2}月\d{1,2}日。")


def _normalize_node_prompt(node_prompt: str) -> str:
    """去掉旧节点模板里的固定日期，避免与运行时日期互相冲突。"""
    return _STATIC_DATE_PREFIX_RE.sub("", node_prompt, count=1).lstrip()


def _node_currentness_guard(node_id: str, current_date: str) -> str:
    if node_id != "node1":
        return ""

    match = re.match(r"(\d{4})年(\d{1,2})月", current_date)
    if not match:
        return ""

    current_year = int(match.group(1))
    previous_year = current_year - 1
    start_year = current_year - 4
    next_year = current_year + 1
    following_year = current_year + 2
    return f"""
[Node1 市场调研时效性补充约束]
当前日期是{current_date}。节点模板中的示例年份只代表结构，不代表必须照抄。
“近5年市场规模变化趋势”应按当前日期动态重建年份列，优先覆盖{start_year}年至{current_year}年；当前年份写“{current_year}年（截至最新公开数据）”，不要写“{current_year}年(估)”。
如果只能找到{previous_year}年或更早的公开数据，必须在数据来源列写明“公开数据截至{previous_year}年/来源发布于{previous_year}年”，并在正文说明时效限制。
任何包含“市场规模/用户规模/门店规模/营收规模”的正文或表格都必须带年份与口径；细分市场表不得写“市场规模（{previous_year}年，估）”这类模糊表头，应改为“市场规模（公开数据截至{previous_year}年）”或“{current_year}年（行业测算，可人工复核）”。
如果基于{previous_year}年数据推算{current_year}年，必须在单元格或数据来源中标注[行业测算]，并写出增长假设；禁止把旧年估值当作{current_year}年现状。
未来年份需要保留为“未来1-2年预测补充”单独表格，至少包含{next_year}年和{following_year}年；必须标注[预测]或[行业测算]，不得与已发生市场规模混写。
结语语气必须专业、正式、克制，使用“您”或“创始人”称呼；禁止使用“老兄”“兄弟”“哥们”“找死”等过于口语或冒犯的表达。
"""


def _extract_pipeline_state(history: list) -> str:
    """从完整对话历史中提取管道状态卡片。
    采用多模式匹配：优先精确匹配，回退到宽松匹配。
    """
    if not history:
        return ""

    all_text = "\n".join([m.get("content", "") for m in history if m.get("role") in ("ai", "assistant")])

    state = {}
    sources = {}

    def first_match(patterns, text=None):
        """尝试多个正则，返回第一个非空匹配"""
        t = text if text is not None else all_text
        for pat in patterns:
            m = re.search(pat, t, re.DOTALL)
            if m:
                try:
                    return m.group(1).strip()
                except IndexError:
                    return m.group(0).strip()
        return None

    # ── §1 行业 ──
    v = first_match([
        r'###\s*1\.1\s*行业[\/品类]*\s*\n(.+?)(?:\n###|\n##|\n---)',
        r'行业[\/品类]*[：:]\s*(.+?)(?:\n|$)',
    ])
    if v:
        state["行业"] = v[:100]
        sources["行业"] = "对话信息摘要 §1"

    # ── 品牌名 (node2) ──
    v = first_match([
        r'(?:最终推荐|品牌名)[：:]\s*[*_]*[「【]?(.{2,6})[」】]?[*_]*\s*(?:\n|$)',
        r'品牌名\s*[「【]?(.{2,6})[」】]?',
    ])
    if v:
        state["品牌名"] = v.strip()
        sources["品牌名"] = "node2"

    # ── §3 用户画像 ──
    v = first_match([
        r'\|\s*(?:25|2[0-9]|3[0-5]).*?(?:岁|yo).*?\|\s*(.+?)\s*\|',
        r'目标用户[：:]\s*(.+?)(?:\n|$)',
    ])
    if v:
        state["目标用户"] = v[:80]
        sources["目标用户"] = "对话信息摘要 §3"

    # ── §5 预算 ──
    v = first_match([
        r'预算[：:范围]*\s*[□✅☑]*\s*(?:<|≤)?\s*(\d+[\d,.]*\s*万[^,\n]*)',
        r'[<≤]?\s*(\d+[\d,.]*\s*万).*?自有资金',
        r'预算.*?(\d+[\d,.]*\s*万)',
    ])
    if v:
        state["预算"] = v.strip()[:60]
        sources["预算"] = "对话信息摘要 §5"

    # ── §4 团队 ──
    v = first_match([
        r'创始人[\/背景]*[：:]\s*(.+?)(?:\n|$)',
        r'团队.*?\|\s*(?:创始人|单人)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|',
        r'(?:单人|1人|一个人|独立)',
    ])
    if v and v != "用户声称":
        state["团队"] = v[:60]
        sources["团队"] = "对话信息摘要 §4"
    elif "单人" in all_text or "1人" in all_text or "一个人" in all_text:
        state["团队"] = "单人启动"
        sources["团队"] = "对话信息摘要 §4"

    # ── 活跃平台 §3 ──
    v = first_match([
        r'(?:渠道偏好|活跃平台|在哪)[：\s]*[|]?\s*(.+?)(?:\||\n|$)',
        r'(\w+)[→>]\s*社群[→>]\s*付费',
    ])
    if v:
        state["活跃平台"] = v[:60]
        sources["活跃平台"] = "对话信息摘要 §3"

    # ── §5 顾虑 ──
    v = first_match([
        r'(?:最大顾虑|核心卡点|核心顾虑)[：:]\s*(.+?)(?:\n|$)',
        r'顾虑[：:]\s*(.+?)(?:\n|$)',
    ])
    if v and len(v) < 200 and "##" not in v and "###" not in v:
        state["核心顾虑"] = v[:100]
        sources["核心顾虑"] = "对话信息摘要 §5"

    # ── 产品线 (node3) ──
    products = []
    for m in re.finditer(r'(?:SKU|引流款|利润款|形象款|产品包|基础版|标准版|旗舰版).*?(\d+[\d,.]*\s*元)', all_text):
        name = m.group(0).strip()[:30]
        price = m.group(1)
        products.append(f"{name} {price}")
    if products:
        state["产品线"] = " / ".join(products[:4])[:120]
        sources["产品线"] = "node3"

    # ── 主渠道 (node4) ──
    v = first_match([
        r'P0[：:]\s*(.+?)(?:\n|$)',
        r'主渠道[：:]\s*(.+?)(?:\n|$)',
    ])
    if v:
        state["主渠道"] = v[:40]
        sources["主渠道"] = "node4"

    # ── node1 验证 ──
    verified = []
    for m in re.finditer(r'\|\s*\d+\s*\|\s*(.+?)\s*\|.*?\|\s*(✅[^|]+?)\s*\|', all_text):
        claim = m.group(1).strip()[:40]
        result = m.group(2).strip()[:30]
        verified.append(f"{result} | {claim}")
    if verified:
        state["验证结论"] = " ; ".join(verified[:3])[:150]
        sources["验证结论"] = "node1"

    if not state:
        return ""

    lines = ["## 管道状态（从上游节点自动提取，请以此为约束）", ""]
    lines.append("| 维度 | 数据 | 来源 |")
    lines.append("|------|------|------|")
    order = ["行业", "品牌名", "目标用户", "预算", "团队", "活跃平台", "主渠道", "核心顾虑", "产品线", "验证结论"]
    for key in order:
        if key in state:
            src = sources.get(key, "")
            lines.append(f"| {key} | {state[key]} | {src} |")

    lines.append("")
    lines.append("**重要**：以上数据来自上游节点输出，禁止凭空修改。如与上下文矛盾，以上游节点输出为准。")
    return "\n".join(lines)


def generate_ai_response(node_id: str, user_input: str, history: list = None, model: str = None, is_followup: bool = False) -> str:
    """使用 LLM 生成回复

    Args:
        node_id: 当前节点ID
        user_input: 用户输入文本
        history: 对话历史
        model: 指定模型（可选）
        is_followup: 是否为追问模式
    """
    from server.intent.recognizer import get_uploaded_files_text, rewrite_query, _session_state

    current_date = current_date_cn()
    integrity_prompt = data_integrity_prompt()
    node_prompt = _normalize_node_prompt(NODE_SYSTEM_PROMPTS.get(node_id, NODE_SYSTEM_PROMPTS["node1"]))
    base_system = integrity_prompt + "\n\n" + node_prompt
    currentness_guard = _node_currentness_guard(node_id, current_date)
    if currentness_guard:
        base_system = base_system + "\n\n" + currentness_guard

    if is_followup:
        if node_id == "node0":
            system = base_system + "\n\n⚠️ 追问模式：用户正在继续诊断对话。请基于对话上下文自然地推进下一轮诊断。如果用户已确认信息无误并要求生成报告，请直接输出完整的 # 品牌全案策略 · 对话信息摘要 报告，不要输出过渡语。"
        else:
            system = base_system + "\n\n⚠️ 追问模式：用户正在追问上一轮输出的某个具体部分。基于上述节点专业框架回答，但只聚焦用户追问的具体问题，深入展开该部分内容（含表格和具体数据），不要重新生成完整报告。"
    else:
        system = base_system

    # 下游节点（node2+）注入管道状态卡片，解决历史截断导致数据丢失
    if not is_followup and node_id in ("node2", "node3", "node4", "node5"):
        pipeline_card = _extract_pipeline_state(history)
        if pipeline_card:
            system = pipeline_card + "\n\n" + system

    # 注入已上传文件内容
    file_context = get_uploaded_files_text()

    processed_input = user_input
    if file_context:
        processed_input = file_context + "\n\n---\n用户提问：\n" + processed_input
    if is_followup:
        processed_input = rewrite_query(user_input, history or [])

    history_text = ""
    if history:
        if node_id in ("node4",):
            context_depth = 20
            recent = history[-context_depth:]
            history_text = "对话上下文：\n" + "\n".join(
                [f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in recent]
            ) + "\n\n"
        else:
            context_depth = 10 if is_followup else 6
            recent = history[-context_depth:]
            history_text = "对话上下文：\n" + "\n".join(
                [f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content'][:800]}" for m in recent]
            ) + "\n\n"

    if is_followup:
        is_summary = any(kw in user_input for kw in ["总结", "归纳", "概括", "汇总", "梳理", "整理一下"])
        session_note = ""
        if _session_state.get("has_report"):
            session_note = "注意：此前已生成完整的7层结构市场调研报告，请在此基础上补充/修改/细化，不要重新开始。"
        elif _session_state.get("entities"):
            session_note = "当前会话核心主题涉及：" + "、".join(_session_state.get("entities", [])[:8])
        if is_summary:
            followup_instruction = (
                "⚠️ 用户要求总结以上对话内容。你需要：\n"
                "1. 梳理上文中所有核心数据、关键结论、重要发现\n"
                "2. 整合为结构化摘要（标题+表格+要点）\n"
                "3. 引用上文具体数据（标注「上文提及」），不编造\n\n"
            )
        else:
            followup_instruction = (
                "⚠️ 这是对上一轮内容的延续追问。你必须基于上述对话上下文回答。\n"
                + session_note + "\n"
                "要求：基于上文输出完整回答，引用具体数据（标注「参考上文」），结构化呈现。\n\n"
            )
        dated_input = f"[现在时间是{current_date}]\n\n{history_text}{followup_instruction}追问：{processed_input}"
    else:
        dated_input = f"[现在时间是{current_date}]\n\n{history_text}用户当前提问：{user_input}"

    try:
        # 用户没指定模型时，按节点分配合适的模型
        if not model:
            if node_id in ("node1", "node2"):
                model = DEEPSEEK_REASONING_MODEL  # 深度分析用推理模型
            # 其他节点不设 model → call_llm 用 DEEPSEEK_MODEL (deepseek-chat)

        # token 预算：深度分析节点需要更大空间，node0 诊断需要容纳 §1-§7 输出
        max_tok_map = {"node1": 40000, "node2": 25000, "node3": 17000, "node4": 40000, "node5": 40000, "node0": 16000, "node6": 12000}
        max_tok = max_tok_map.get(node_id, 8192)

        # Node0 第6轮确认：用户信息确认完毕，需要输出完整 dialogue_brief，提高 token 上限
        if node_id == "node0" and is_followup:
            confirm_signals = ["确认", "准确", "没问题", "可以", "生成", "ok", "好的", "正确", "无误", "没毛病", "是的"]
            if any(kw in user_input.lower() for kw in confirm_signals):
                max_tok = 32000
        result = call_llm(system, dated_input, model=model, max_tokens=max_tok)
        return result
    except Exception as e:
        print(f"[LLM] Response generation failed: {e}", flush=True)
        return f"抱歉，AI 服务暂时不可用。请稍后重试。（错误信息：{str(e)[:200]}）"
