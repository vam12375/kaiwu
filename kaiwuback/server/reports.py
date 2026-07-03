"""报告生成模块"""
import json, re, threading, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from server.llm_client import call_deepseek, call_llm
from server.config import PROJECT_LIB, REPORT_TEMPLATES_DIR, DATA_INTEGRITY
from server.intent.recognizer import get_uploaded_files_text
from server.utils.handbook_renderer import render_handbook_to_html
from server.utils.markdown import markdown_to_html


def _is_number_sequence(text):
    """检测文本是否为逗号分隔的数字序列，如 '9,9,8,7,8,9,9,8'"""
    text = text.strip()
    if not text or len(text) < 3:
        return False
    parts = [p.strip() for p in text.split(',')]
    if len(parts) < 3:
        return False
    for p in parts:
        try:
            float(p)
        except ValueError:
            return False
    return True


def _parse_chart_value(s):
    """从图表数据字符串中提取数值，兼容 '85%' '1200万' '9.5亿' '7/10分' 等格式"""
    s = s.strip().replace(',','').replace('%','').replace('亿','').replace('万','').replace('元','').replace('分','').replace('/10','').replace('分制','')
    try:
        return float(s)
    except ValueError:
        pass
    m = re.search(r'[\d.]+', s)
    if m:
        try:
            return float(m.group())
        except ValueError:
            pass
    return 0


# REPORT_TEMPLATES_DIR imported from config above

NODE_REPORT_MAP = [
    # (node_ids, template_file, report_title)
    ({"node4"}, "品牌商业计划书.html", "系统化内容营销解决方案"),
    ({"node3", "node3.1"}, "产品落地执行手册.html", "产品落地执行手册"),
    ({"node2"}, "品牌商业计划书.html", "品牌商业计划书"),
    ({"node1"}, "杂志风报告模板.html", "深度商业调研报告"),
]


def detect_nodes_from_history(history: list) -> set:
    """从对话历史中推断涉及哪些node。通过分析意图识别结果。
    由于历史消息不包含node标记，使用关键词匹配推断。"""
    nodes = set()
    all_text = " ".join([m.get("content", "")[:800] for m in history])
    # Node1: 调研/市场/行业/竞品
    if any(kw in all_text for kw in ["调研", "市场", "行业", "竞品", "洞察", "TAM", "需求"]):
        nodes.add("node1")
    # Node1.5: 品牌精神/品牌屋/Slogan/品牌故事
    if any(kw in all_text for kw in ["品牌精神", "品牌屋", "品牌策略", "品牌全案", "Slogan", "品牌故事", "品牌文化"]):
        nodes.add("node1.5")
    # Node2: 商业方案/商业底层/定位/产品矩阵
    if any(kw in all_text for kw in ["商业方案", "商业底层", "商业计划", "赛道定位", "产品矩阵", "盈利模式"]):
        nodes.add("node2")
    # Node3: 产品设计（产品落地手册/SKU/成本核算/启动方案等）
    if any(kw in all_text for kw in ["产品定位", "SKU", "产品落地手册", "成本核算", "产品规划", "启动方案", "验证周期", "获客方案", "定价策略", "利润空间"]):
        nodes.add("node3")
    # Node3.1: 生成图片
    if any(kw in all_text for kw in ["生成图片", "生成一张", "画一张", "文生图"]):
        nodes.add("node3.1")
    # Node4: PPT
    if any(kw in all_text for kw in ["PPT", "大纲", "幻灯片"]):
        nodes.add("node4")
    return nodes


def select_report_template(history: list) -> tuple:
    """根据对话历史涉及的node，选择报告模板。返回(template_path, report_title)"""
    nodes = detect_nodes_from_history(history)
    print(f"[REPORT] Detected nodes: {nodes}", flush=True)
    for node_set, template_file, title in NODE_REPORT_MAP:
        if node_set & nodes:
            template_path = REPORT_TEMPLATES_DIR / template_file
            if template_path.exists():
                return str(template_path), title
    # 默认：深度商业调研报告
    return str(REPORT_TEMPLATES_DIR / "千瓜风格报告.html"), "深度商业调研报告"


def generate_summary_report(message, history, model=None):
    """简化版报告生成：发送全部上下文→LLM生成结构化markdown→解析为slides"""
    # 根据用户请求判定报告类型
    # 所有报告统一使用规范模板
    lower_msg = message.lower()
    if any(kw in lower_msg for kw in ["品牌手册"]):
        report_title = "品牌手册"
    elif any(kw in lower_msg for kw in ["产品手册", "产品落地"]):
        report_title = "产品落地执行手册"
    elif any(kw in lower_msg for kw in ["营销解决方案", "营销手册"]):
        report_title = "系统化内容营销解决方案"
    elif any(kw in lower_msg for kw in ["商业计划书"]):
        report_title = "品牌商业计划书"
    elif any(kw in lower_msg for kw in ["调研报告", "调研", "报告"]):
        report_title = "深度商业调研报告"
    else:
        _, report_title = select_report_template(history)

    # ── 四类报告统一方案：从节点输出缓存取内容 → 模板渲染，不调 LLM ──
    from server.agent.runtime import get_node_output

    # 按报告类型匹配源节点
    source_node_map = {
        "产品落地": "node3", "产品手册": "node3",
        "营销": "node4",
        "调研": "node1", "报告": "node1",
        "商业计划书": "node2",
    }
    source_node = "node1"
    for key, node in source_node_map.items():
        if key in report_title:
            source_node = node
            break

    handbook_md = get_node_output(source_node)
    # 缓存没有则回退到历史，按源节点标识匹配，避免取到其他节点的内容
    if not handbook_md or len(handbook_md) < 100:
        # 每个节点输出的唯一标识，用于在历史中定位对应内容
        node_stop_markers = {
            "node1": "node1 市场调研完整输出",
            "node2": "node2 商业方案完整输出",
            "node3": "node3 产品落地手册完整输出",
            "node4": "node4 内容营销方案完整输出",
        }
        target_marker = node_stop_markers.get(source_node, "")
        ai_msgs = [m["content"] for m in history if m.get("role") == "ai" and m.get("content")]
        # 从最新到最旧找第一条包含目标节点标识的消息
        for msg in reversed(ai_msgs):
            if target_marker and target_marker in msg:
                handbook_md = msg
                break
        # 找不到匹配节点 → 回退到取最后一条 AI 消息
        if not handbook_md:
            handbook_md = ai_msgs[-1] if ai_msgs else ""
    if len(handbook_md) < 100:
        return {"error": f"对话内容不足，无法生成报告。请先完成对应节点。"}

    # 在终止标识处截断
    m = re.search(r'以上为[^\n]{0,80}(?:完整输出|全部呈现|全部内容)', handbook_md)
    if m:
        end = m.end()
        remaining = handbook_md[end:]
        m2 = re.match(r'[^\n]*?(?:数据基于|行业公开|建议人工复核|人工复核后使用)[^\n]*?[。.]', remaining)
        if m2:
            end += m2.end()
        handbook_md = handbook_md[:end]

    html_content = render_handbook_to_html(handbook_md, report_title, "")
    file_id = uuid.uuid4().hex[:6]

    # 归档规则：按报告类型决定存放文件夹
    # 深度调研/商业计划书 → 编程文件库 + 创业资料 + AI对话产出
    # 产品落地手册 → 编程文件库 + AI对话产出
    # 营销解决方案 → 编程文件库 + 营销素材 + AI对话产出
    archive_folders = {"编程文件库", "AI 对话产出"}
    if "调研" in report_title or "商业计划书" in report_title:
        archive_folders.add("创业资料")
    if "营销" in report_title:
        archive_folders.add("营销素材")

    file_path = None
    for folder in archive_folders:
        fp = PROJECT_LIB / folder / f"{report_title}_{file_id}.html"
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(html_content, encoding='utf-8')
        if folder == "编程文件库":
            file_path = str(fp)

    print(f"[HANDBOOK] Template-rendered {len(html_content)} chars → {archive_folders}", flush=True)
    return {"report_title": report_title, "file_path": file_path or "", "method": "template"}


def _esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
