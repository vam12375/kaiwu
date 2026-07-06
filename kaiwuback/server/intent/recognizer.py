"""意图识别模块"""
import json, re
from server.llm_client import call_deepseek
from server.config import REPORT_MODEL

# 会话级状态存储
_session_state: dict = {}
_uploaded_files: list = []  # 上传文件持久缓存 [(filename, content), ...]


def add_uploaded_file(filename: str, content: str):
    """存储上传文件内容到会话"""
    for i, (fn, _) in enumerate(_uploaded_files):
        if fn == filename:
            _uploaded_files[i] = (filename, content)
            return
    _uploaded_files.append((filename, content))


def get_uploaded_files_text() -> str:
    """获取所有已上传文件的合并文本"""
    if not _uploaded_files:
        return ""
    text = "\n\n## 已上传文件内容（优先参考数据源）\n"
    for fn, ct in _uploaded_files:
        text += f"\n### 📄 {fn}\n{ct[:5000]}\n"
    return text


def clear_uploaded_files():
    """清除所有上传文件"""
    _uploaded_files.clear()
from server.config import REPORT_MODEL

INTENT_PROMPT = """你是意图调度Agent。你的唯一职责：识别用户意图，分配唯一Node节点或转交兜底Agent。

## 可用Node节点

Node0（用户诊断）：当用户表达了模糊的创业意向但没有明确下一步指令时优先触发。触发特征："我想做XX""我想创业""有什么赛道""做什么赚钱""我想开XX"——用户还没想清楚要调研还是做方案，只是在表达创业意图或探索方向。Node0先了解创始人的背景、资源、动机和约束，输出 dialogue_brief.md 后再让用户选择下一步。注意：如果用户已经明确要求调研/方案/设计，不要截胡到Node0。

Node1（调研市场 / 行业需求洞察）：当意图识别为【调研市场】时触发。模糊需求→类型一：创业机会概述（大赛道挖掘细分机会+收入预估+ABC选项对比+陪跑支持）；明确赛道→类型二：可行性评估（三维度评分+时间线+风险应对+决策支持+优化建议）。覆盖：市场调研、赛道分析、用户画像、竞品格局、收入预估、风险预警、心理登月调研。

Node2（商业中枢）：四柱商业骨架（用户画像+品牌定位+盈利模式+行动路径）+三条故事线（品牌故事+产品故事+客户故事，传入Node4做营销）。覆盖：品牌屋搭建、RTB论据、产品矩阵、Slogan设计、财务测算、风险评估。用户说"商业方案""品牌定位""产品矩阵""盈利模式"都是Node2

Node3（产品设计）：基于商业模式确定首批SKU，输出产品定位/定价/成本/启动方案。触发词："做什么产品""产品规划""产品方案"。

Node3.1（Logo/图片设计）：接收品牌信息设计Logo方案，或接收图片描述生成效果图。触发词："设计logo""logo""品牌logo""生成图片""画一张"。

Node4（商业PPT方案输出）：调研报告/商业方案/品牌全案整理为PPT大纲、结构化每页文案、PPT内容排版

Node5（营销文案全链路创作）：小红书/抖音/B站种草文案、短视频脚本、产品详情页、海报文案、私域话术、节日营销内容

Node_export（文件导出）：导出HTML/生成HTML/生成PPT/生成PDF/把分析做成文件/导出为文件。根据上下文自动匹配源节点数据

## 调度铁律
1. 单条指令仅分配1个Node；多流程需求只识别当前第一步核心任务
2. 只有完全匹配上述业务场景才分配Node；其余一律判定为【非流水线业务】→ 转交兜底Agent(node=fallback)
3. 禁止主观扩充、脑补用户隐藏需求
4. 需求模糊、缺少关键信息时 → 转交兜底Agent(node=fallback)
5. 用户说"设计logo/品牌logo/logo" → Node3.1；用户说"做什么产品/产品规划" → Node3；用户说"生成图片/画一张" → Node3.1

## 输出格式（严格JSON，禁止多余话术）
{"node":"0|1|2|3|3.1|4|5|fallback","topic":"核心话题","summary":"意图说明+匹配原因","constraints":"本次任务关键执行要求"}"""

def recognize_intent(user_input: str, model: str = None) -> dict:
    """用LLM识别意图, 返回 {node, topic, summary, constraints}"""
    import re
    lower_input = user_input.lower()

    # ════════════════════════════════════
    # 第一层：Node1 市场调研最高优先级强匹配
    # ════════════════════════════════════
    # 创业意图通用检测：意图词 + 动作词 + 品类 → Node0
    intent_words = ["想", "要", "准备", "打算", "考虑", "希望", "计划"]
    action_words = ["做", "进入", "开", "搞", "干", "创业", "尝试", "往", "发展", "从事"]
    has_intent = any(kw in lower_input for kw in intent_words)
    has_action = any(kw in lower_input for kw in action_words)
    has_entrepreneurial_intent = has_intent and has_action

    research_signal = ["调研", "行业", "赛道", "市场分析", "大盘研判", "行业报告"]
    has_research = any(kw in lower_input for kw in research_signal)
    # 具体品类词（可扩展）
    category_words = ["服装", "网球", "餐饮", "美妆", "宠物", "咖啡", "茶饮", "运动", "家居", "电子", "汽车", "教育", "医疗", "金融", "母婴", "零食", "酒", "鞋", "箱包", "香氛", "香水"]
    has_category = any(kw in lower_input for kw in category_words)

    # 检测到品类 + 创业意图 → 优先 Node0
    if has_category and has_entrepreneurial_intent:
        print(f"[INTENT] Node0 priority: entrepreneurial intent detected, intent={has_intent}, action={has_action}", flush=True)
        return {"node": "0", "topic": user_input[:30], "summary": user_input, "constraints": ""}
    # 检测到调研关键词 + 品类，且无创业意图 → Node1
    if has_research and has_category:
        print(f"[INTENT] Node1 priority routing: research={has_research}, category={has_category}", flush=True)
        return {"node": "1", "topic": user_input[:30], "summary": user_input, "constraints": ""}

    # ════════════════════════════════════
    # 第二层：通用报告节点（仅纯文案总结/文档改写，不含调研关键词）
    # ════════════════════════════════════
    blacklist_for_report = ["调研", "赛道", "市场", "行业", "竞品", "供应链", "大盘"]
    has_blacklist = any(kw in lower_input for kw in blacklist_for_report)
    pure_report_triggers = ["生成报告", "生成调研报告", "调研报告", "品牌手册", "商业计划书", "品牌商业计划书", "生成产品手册", "产品落地手册", "生成产品落地手册", "生成系统化内容营销解决方案", "营销解决方案", "生成营销手册", "营销手册"]
    # 只有纯"生成一份"才路由报告节点（排除"生成一份商业方案"这类组合词）
    node_triggers = ["商业方案", "品牌定位", "产品矩阵", "盈利模式", "行动路径", "商业策划"]

    # ════════════════════════════════════
    # 第二层半：营销意图关键词优先拦截
    # Node5（文案）优先判断，避免"如何做营销文案"被Node4关键词误拦截
    # 然后Node4（营销方案）拦截"如何做营销/如何去做营销"等变体
    # ════════════════════════════════════
    copy_triggers = ["文案", "素材", "种草", "短视频脚本", "产品详情页", "私域话术", "宣传文案", "节日营销"]
    if any(kw in lower_input for kw in copy_triggers):
        return {"node": "5", "topic": user_input[:30], "summary": "已识别为营销文案创作需求，调度Node5", "constraints": ""}
    marketing_triggers = ["营销方案", "营销策划", "营销推广", "营销策略", "如何营销", "怎么营销", "怎么做营销", "做营销",
                         "如何推广", "怎么推广", "怎么做推广", "做推广", "营销计划", "推广方案"]
    if any(kw in lower_input for kw in marketing_triggers):
        return {"node": "4", "topic": user_input[:30], "summary": "已识别为营销方案设计需求，调度Node4", "constraints": ""}
    if "生成一份" in lower_input and not any(kw in lower_input for kw in node_triggers):
        return {"node": "summary", "topic": user_input[:30], "summary": user_input, "constraints": ""}
    if any(kw in lower_input for kw in pure_report_triggers):
        return {"node": "summary", "topic": user_input[:30], "summary": user_input, "constraints": ""}

    # ════════════════════════════════════
    # 第三层：LLM意图识别
    # ════════════════════════════════════
    try:
        raw = call_deepseek(
            INTENT_PROMPT,
            f'用户当前输入: "{user_input}"\n\n判断意图并返回JSON:',
            timeout=15,
            model=None
        )
        m = re.search(r'\{[^{}]*"node"[^{}]*\}', raw)
        if m:
            result = json.loads(m.group(0))
        else:
            result = json.loads(raw.strip())
        if isinstance(result, dict) and "node" in result:
            rnode = result.get("node")
            # 兜底校验：LLM返回通用报告但输入含调研关键词 → 强制修正为Node1
            if rnode in ("export", "summary") and (has_research or has_category):
                print(f"[INTENT] LLM returned {rnode} but research detected, forcing Node1", flush=True)
                return {"node": "1", "topic": user_input[:30], "summary": "已识别为行业市场调研需求，自动调度Node1", "constraints": ""}
            if rnode != "fallback":
                return result
    except Exception as e:
        print(f"[INTENT] DeepSeek intent recognition failed: {e}", flush=True)

    # ════════════════════════════════════
    # 第四层：关键词兜底匹配
    # ════════════════════════════════════
    kw_map = [
        (["我想做", "我要做", "我想开", "我想创业", "创业方向", "有什么机会", "做什么赚钱", "有什么赛道", "推荐赛道", "适合做什么", "有没有什么好做的"], "0"),
        (["商业方案", "商业底层", "商业计划", "生成商业", "设计商业", "商业定位", "产品矩阵", "盈利模式", "财务测算", "供应链", "风险评估"], "2"),
        (["PPT", "ppt", "演示文稿", "幻灯片", "PPT大纲", "营销方案", "营销策划", "营销推广"], "4"),
        (["生成图片", "生成图", "生成一张", "帮我生成一张", "文生图", "图片生成", "生成一个", "帮我画", "画出", "画一张", "出图", "设计品牌logo", "设计Logo", "设计LOGO", "品牌标志设计", "logo", "品牌logo", "设计logo"], "3.1"),
        (["产品设计", "做什么产品", "做哪些产品", "做产品", "产品规划", "设计产品", "产品手册", "产品落地", "做什么服务", "做哪些服务", "做服务", "设计服务", "服务规划", "服务设计"], "3"),
        (["确立品牌", "建立品牌", "打造品牌", "我的品牌", "品牌怎么", "品牌塑造", "品牌故事", "品牌屋", "品牌文化", "品牌理念", "品牌内核", "品牌符号", "品牌全案", "品牌策划"], "2"),
        (["文案", "素材", "种草", "短视频脚本", "产品详情页", "私域话术", "小红书", "抖音", "B站", "营销素材", "宣传文案", "节日营销"], "5"),
        (["调研", "调查", "分析", "评估", "市场", "行业", "赛道", "趋势", "竞品", "用户画像", "洞察", "市场规模", "TAM", "SAM"], "1"),
    ]
    for keywords, nid in kw_map:
        for kw in keywords:
            if kw.lower() in lower_input:
                # 兜底：命中通用报告类关键词但有调研语义 → Node1
                if nid in ("export", "summary") and (has_research or has_category):
                    return {"node": "1", "topic": user_input[:30], "summary": "已识别为行业市场调研需求", "constraints": ""}
                return {"node": nid, "topic": user_input[:30], "summary": user_input, "constraints": ""}
    return {"node": "fallback", "topic": user_input[:30], "summary": user_input, "constraints": ""}

FOLLOWUP_INDICATORS = [
    "这个", "那个", "它", "上文", "前面", "刚才", "上一", "之前",
    "补充", "修改", "细化", "拓展", "继续", "再", "还", "也",
    "这块", "这部分", "那边", "里面", "其中",
    "展开", "详细", "具体", "深入", "进一步",
    "调整", "优化", "完善", "改进", "增强",
]
TOPIC_SWITCH_SIGNALS = ["新的", "另一个", "换个", "不同", "其他行业", "另外"]

def detect_followup_type(user_input: str, history: list) -> dict:
    """判定输入类型：全新请求 / 追问迭代 / 话题切换"""
    lower = user_input.lower().strip()
    result = {"is_new": True, "is_followup": False, "is_topic_switch": False, "rewritten_query": user_input}

    # 0. 报告/总结类命令优先 —— 始终视为新请求
    REPORT_TRIGGERS = ["市场调研报告", "生成调研报告", "调研报告", "生成报告", "生成产品落地手册", "生成产品手册", "产品落地手册", "商业方案", "品牌落地", "商业策划", "商业计划书", "品牌商业计划书", "品牌手册", "营销方案", "营销策划", "提炼品牌", "生成品牌屋", "生成logo", "设计logo", "logo", "品牌logo", "设计品牌logo", "做什么产品", "做哪些产品", "做产品", "产品规划", "生成系统化内容营销解决方案", "营销解决方案", "生成营销手册", "营销手册"]
    if any(kw in lower for kw in REPORT_TRIGGERS):
        result["is_new"] = True
        return result

    # 1. 指代/追问词检测
    has_indicator = any(kw in lower for kw in FOLLOWUP_INDICATORS)
    has_switch = any(kw in lower for kw in TOPIC_SWITCH_SIGNALS)

    # 2. 历史上下文检查
    has_history = history and len([m for m in history if m.get("role") == "assistant" or m.get("role") == "ai"]) > 0

    # 3. 短句+有历史 = 大概率追问
    is_short = len(user_input.strip()) < 20

    if has_switch:
        result["is_topic_switch"] = True
        result["is_new"] = True
        return result

    if has_indicator and has_history:
        result["is_followup"] = True
        result["is_new"] = False  # 修复点4: 追问优先

    elif is_short and has_history:
        # 修复点6: 短句预处理，改写为完整追问
        result["is_followup"] = True
        result["is_new"] = False

    # 4. 恢复会话上下文（修复点2）
    if result["is_followup"] and _session_state:
        result["session_context"] = _session_state

    return result


def save_session_state(history: list, node_id: str):
    """保存对话核心状态：主题、实体、报告结构（修复点2+7）"""
    if not history: return
    all_text = " ".join([m.get("content", "")[:500] for m in history[-6:]])
    # 提取实体关键词
    entities = set()
    for kw in ["市场", "行业", "消费者", "品牌", "产品", "定价", "渠道", "竞品", "风险",
               "增速", "规模", "画像", "痛点", "差异", "供应链", "流量", "库存", "营收"]:
        if kw in all_text:
            entities.add(kw)
    _session_state.clear()
    _session_state["entities"] = list(entities)[:10]
    _session_state["last_node"] = node_id
    _session_state["has_report"] = "市场调研报告" in all_text or "七层" in all_text


# ═══════════════════════════════════════
# 节点依赖校验系统
# ═══════════════════════════════════════

NODE_TRIGGERS = {
    "node0": ["用户诊断", "了解我", "诊断", "帮我分析一下我的情况", "评估我的资源"],
    "node1": ["市场调研报告", "生成调研报告", "调研报告", "行业研判", "行业大盘", "行业报告"],
    "node1.5": ["提炼品牌精神", "提取人群共性", "生成品牌屋", "生成设计提示词", "品牌精神", "品牌价值观", "品牌屋生成"],
    "node2": ["商业方案", "品牌落地规划", "商业策划", "落地执行方案"],
    "node3": ["产品设计", "做什么产品", "做哪些产品", "做什么样的服务", "产品规划", "设计产品", "产品方案"],
    "node4": ["商业PPT", "融资PPT", "项目汇报PPT", "汇报演示"],
}

REGENERATE_TRIGGERS = ["重新生成", "重做", "刷新全套", "重新做", "重跑"]

DEPENDENCIES = {
    "node0": {"hard": [], "soft": []},
    "node1": {"hard": [], "soft": ["node0"]},
    "node2": {"hard": ["node1"], "soft": []},
    "node1.5": {"hard": ["node1", "node2"], "soft": []},
    "node3": {"hard": ["node2"], "soft": []},
    "node4": {"hard": ["node1", "node2"], "soft": ["node1.5"]},
}

MANUAL_TRIGGERS = {
    "brand_handbook": ["生成品牌手册"],
    "product_handbook": ["生成产品手册", "导出产品手册"],
    "full_handbook": ["导出全套手册"],
}


def identify_node_intent(user_input: str) -> dict:
    """识别用户输入中的节点意图。返回 {node_id, is_regenerate, is_generation}"""
    result = {"node_id": None, "is_regenerate": False, "is_generation": False}
    lower = user_input.lower()

    # 检查重生成
    if any(kw in lower for kw in REGENERATE_TRIGGERS):
        result["is_regenerate"] = True

    # 检查各节点触发词
    for node_id, keywords in NODE_TRIGGERS.items():
        if any(kw in lower for kw in keywords):
            result["node_id"] = node_id
            result["is_generation"] = True
            return result

    # 检查手册导出
    for manual_type, keywords in MANUAL_TRIGGERS.items():
        if any(kw in lower for kw in keywords):
            result["node_id"] = manual_type
            result["is_generation"] = True
            return result

    return result


def validate_node_prerequisites(node_id: str, history: list) -> dict:
    """校验节点前置依赖。返回 {ok, missing_hard, missing_soft, message}"""
    if node_id not in DEPENDENCIES:
        return {"ok": True, "missing_hard": [], "missing_soft": [], "message": ""}

    deps = DEPENDENCIES[node_id]
    all_text = " ".join([m.get("content","")[:500] for m in history]) if history else ""

    missing_hard = []
    for dep in deps["hard"]:
        # Check if the dependency node's output exists in conversation
        dep_indicators = {
            "node0": ["创始人画像摘要", "赛道/品类", "预算量级", "用户诊断"],
            "node1": ["市场规模", "消费者画像", "竞争格局", "行业增速", "人群特征"],
            "node1.5": ["品牌精神", "品牌屋", "品牌价值观", "品牌理念", "品牌命名", "品牌差异化", "三合一提示词", "Logo设计提示词"],
            "node2": ["商业方案", "产品线", "营销渠道", "财务目标", "品牌价值观", "品牌命名", "品牌理念"],
        }
        indicators = dep_indicators.get(dep, [])
        if not any(kw in all_text for kw in indicators):
            missing_hard.append(dep)

    missing_soft = []
    for dep in deps["soft"]:
        indicators = {
            "node0": ["创始人画像摘要", "用户诊断"],
            "node1.5": ["品牌精神", "品牌屋", "人群精神词条"],
        }
        indicators = indicators.get(dep, [])
        if not any(kw in all_text for kw in indicators):
            missing_soft.append(dep)

    if missing_hard:
        dep_names = {"node0":"用户诊断","node1":"行业调研报告","node1.5":"品牌精神数据","node2":"商业方案","node3":"Logo方案"}
        names = [dep_names.get(d,d) for d in missing_hard]
        msg = f"⚠️ 当前节点需要先完成：{', '.join(names)}。请先执行前置节点后再试。"
        return {"ok": False, "missing_hard": missing_hard, "missing_soft": missing_soft, "message": msg}

    if missing_soft:
        dep_names = {"node1.5":"品牌精神数据"}
        names = [dep_names.get(d,d) for d in missing_soft]
        msg = f"💡 建议先执行 {names[0]} 以获得更精准的品牌约束。是否跳过直接生成？（回复 1 继续执行或回复 2 先执行Node1.5）"
        return {"ok": True, "missing_hard": [], "missing_soft": missing_soft, "message": msg}

    return {"ok": True, "missing_hard": [], "missing_soft": [], "message": ""}


def rewrite_query(user_input: str, history: list) -> str:
    """将模糊追问改写为完整上下文问句（修复点6）"""
    lower = user_input.strip().lower()
    # 提取上一轮核心主题
    last_ai = ""
    for m in reversed(history):
        if m.get("role") in ("ai", "assistant") and m.get("content"):
            last_ai = m.get("content", "")[:500]
            break
    if not last_ai:
        return user_input

    # 简单的改写：拼接上下文
    if len(lower) < 15 and any(kw in lower for kw in ["补充", "修改", "细化", "拓展", "详细", "具体", "继续"]):
        # 提取上一轮的关键主题词
        topic_hint = ""
        for kw in ["行业", "报告", "分析", "方案", "数据", "风险", "用户", "竞品"]:
            if kw in last_ai:
                topic_hint = kw
                break
        if topic_hint:
            return f"基于上一轮{topic_hint}内容，{user_input}"
    return user_input
