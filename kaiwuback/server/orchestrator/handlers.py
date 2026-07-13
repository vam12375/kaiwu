"""报告生成与文件导出的 SSE 流处理器 —— 从 main.py 抽取"""
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

from server.config import PROJECT_LIB, public_url
from server.utils.common import generate_html_file, save_project_file


REPORT_SOURCE_LABELS = {
    "summary": "报告",
    "node1": "市场调研报告",
    "node2": "商业方案报告",
    "node1.5": "品牌策略报告",
    "node3": "产品设计报告",
    "node4": "营销方案报告",
    "node5": "自媒体文案报告",
}


def _project_file_url(file_path: str) -> str:
    """Convert a saved project file path into the public project-files URL."""
    path = Path(file_path).resolve()
    root = PROJECT_LIB.resolve()
    relative = path.relative_to(root)
    folder = quote(relative.parent.as_posix(), safe="")
    filename = quote(relative.name, safe="")
    return public_url(f"/project-files/{folder}/{filename}")


def _unique_folders(folders: list[str]) -> list[str]:
    result = []
    for folder in folders:
        if folder and folder not in result:
            result.append(folder)
    return result


def _report_saved_event(
    *,
    title: str,
    file_path: str,
    file_url: str,
    folders: list[str],
    source_node: str,
    folder: str,
) -> dict:
    file_name = Path(file_path).name if file_path else f"{title}.html"
    source_label = REPORT_SOURCE_LABELS.get(source_node, "报告")
    return {
        "type": "file_saved",
        "message": f"{source_label}已生成",
        "artifact_type": "report",
        "report_title": title,
        "file_name": file_name,
        "file_type": "HTML",
        "source_node": source_node,
        "source_label": source_label,
        "folders": _unique_folders(folders),
        "folder": folder,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "auto_preview": True,
        "desktop_path": file_path,
        "url": file_url,
        "file_url": file_url,
    }


def handle_summary(message: str, history: list, model: str = None):
    """处理报告生成请求，SSE 流式推送进度"""
    from server.reports import generate_summary_report

    yield f"data: {json.dumps({'type': 'node_selected', 'node': 'summary', 'name': '报告生成', 'icon': '📊', 'topic': '', 'summary': ''})}\n\n"
    yield f"data: {json.dumps({'type': 'progress', 'node': 'summary', 'message': '正在分析对话节点...', 'percent': 10})}\n\n"

    result_holder = [None]
    def run_report():
        try:
            result_holder[0] = generate_summary_report(message, history, model)
        except Exception as e:
            result_holder[0] = {"error": str(e)[:200]}

    report_thread = threading.Thread(target=run_report, daemon=True)
    report_thread.start()

    progress_msgs = [
        (20, "正在提取关键数据..."), (30, "正在构建叙事框架..."),
        (50, "正在生成分析图表..."), (70, "正在排版美化..."),
        (85, "正在生成HTML文件..."), (95, "正在等待AI生成内容...")
    ]
    start_t = time.time()
    msg_idx = 0
    while report_thread.is_alive():
        elapsed = time.time() - start_t
        if elapsed < 120:
            pct = 10 + int(80 * (elapsed / 120))
        else:
            pct = 90 + min(8, int((elapsed - 120) / 15))
        if msg_idx < len(progress_msgs) and pct >= progress_msgs[msg_idx][0]:
            yield f"data: {json.dumps({'type': 'progress', 'node': 'summary', 'message': progress_msgs[msg_idx][1], 'percent': pct})}\n\n"
            msg_idx += 1
        elif elapsed > 120:
            yield f"data: {json.dumps({'type': 'progress', 'node': 'summary', 'message': 'AI 仍在生成中，请耐心等待...', 'percent': pct})}\n\n"
        time.sleep(0.8)
    report_thread.join(timeout=5)

    result = result_holder[0]
    if not result or result.get("error"):
        err_msg = result.get("error", "未知错误") if result else "未知错误"
        yield f"data: {json.dumps({'type': 'content', 'content': '报告生成失败：' + err_msg})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    report_title = result["report_title"]
    file_path = result.get("file_path", "")

    yield f"data: {json.dumps({'type': 'progress', 'node': 'summary', 'message': '正在保存文件...', 'percent': 99})}\n\n"

    if file_path and Path(file_path).exists():
        import subprocess
        subprocess.run(["open", "-a", "Google Chrome", file_path], check=False)
        file_url = _project_file_url(file_path)
        folders = result.get("archive_folders") or ["编程文件库", "AI 对话产出"]
        yield f"data: {json.dumps(_report_saved_event(title=report_title, file_path=file_path, file_url=file_url, folders=folders, source_node='summary', folder='编程文件库'))}\n\n"

    yield f"data: {json.dumps({'type': 'progress', 'node': 'summary', 'message': '完成', 'percent': 100})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


def handle_export(message: str, history: list, intent: dict):
    """处理文件导出请求，SSE 流式推送进度"""
    source_node = ""
    explicit_source_rules = [
        ("node5", ["导出自媒体文案报告", "导出营销文案报告", "自媒体文案报告", "营销文案报告", "内容营销体系报告"]),
        ("node4", ["导出营销方案报告", "导出营销方案", "营销方案报告", "内容营销方案报告", "系统化内容营销解决方案"]),
        ("node3", ["导出产品手册报告", "导出产品手册", "产品手册报告", "产品落地手册报告", "产品落地执行手册"]),
        ("node2", ["导出商业方案报告", "导出商业方案", "商业方案报告", "商业计划书", "品牌商业计划书"]),
        ("node1", ["导出调研报告", "导出市场调研报告", "调研报告", "市场调研报告"]),
    ]
    for node, keywords in explicit_source_rules:
        if any(keyword in message for keyword in keywords):
            source_node = node
            break

    node_keywords = {
        "node1": ["调研", "市场", "行业", "竞品", "用户画像", "洞察", "TAM", "SAM", "需求"],
        "node2": ["商业方案", "定位", "产品矩阵", "盈利", "风控", "供应链", "赛道"],
        "node3": ["产品手册", "产品落地", "产品设计", "SKU", "产品定位", "成本核算", "启动方案"],
        "node1.5": ["品牌理念", "品牌故事", "Slogan", "品牌屋", "品牌精神", "品牌策略"],
        "node4": ["营销方案", "营销策略", "内容营销", "传播矩阵", "发布节奏", "5A", "营销推广"],
        "node5": ["自媒体文案", "营销文案", "种草", "文案", "详情页", "话术", "短视频", "小红书", "抖音"],
    }
    if not source_node:
        source_node = "node1"
        max_score = 0
        for node, keywords in node_keywords.items():
            score = sum(1 for kw in keywords if kw in message)
            if score > max_score:
                max_score = score
                source_node = node

    # 优先从节点输出缓存取内容，避免历史消息错位
    from server.agent.runtime import get_node_output
    cached = get_node_output(source_node)
    if cached:
        full_content = cached
    else:
        full_content = ""
        node_stop_markers = {
            "node1": "node1 市场调研完整输出",
            "node2": "node2 商业方案完整输出",
            "node3": "node3 产品落地手册完整输出",
            "node4": "node4 内容营销方案完整输出",
            "node5": "node5 内容营销体系完整输出",
        }
        target_marker = node_stop_markers.get(source_node, "")
        ai_messages = []
        if history:
            for m in history:
                if m.get("role") == "ai" and m.get("content"):
                    ai_messages.append(m["content"])
        for content in reversed(ai_messages):
            if target_marker and target_marker in content:
                full_content = content
                break
        if not full_content:
            full_content = ai_messages[-1] if ai_messages else message
    if not full_content.strip():
        full_content = message
    title_map = {
        "node1": "深度商业调研报告",
        "node2": "品牌商业方案报告",
        "node3": "产品落地执行手册",
        "node4": "系统化内容营销方案",
        "node5": "自媒体文案报告",
    }
    title = title_map.get(source_node, intent.get('topic', 'AI导出'))[:30]

    source_label = REPORT_SOURCE_LABELS.get(source_node, "报告")
    yield f"data: {json.dumps({'type': 'progress', 'node': 'export', 'message': f'已识别上下文：{source_label}，正在生成HTML文件...', 'percent': 50})}\n\n"

    folder_map = {"node1": "创业资料", "node2": "创业资料", "node1.5": "产品设计", "node3": "产品设计", "node5": "营销素材", "node4": "营销素材"}
    target_folder = folder_map.get(source_node, "AI 对话产出")

    try:
        html_content = generate_html_file(full_content, title)
        path1 = save_project_file(html_content, title, "编程文件库", "html")
        save_project_file(html_content, title, target_folder, "html")
        save_project_file(html_content, title, "AI 对话产出", "html")
        file_url = _project_file_url(path1)
        folders = _unique_folders(["编程文件库", target_folder, "AI 对话产出"])
        yield f"data: {json.dumps(_report_saved_event(title=title, file_path=path1, file_url=file_url, folders=folders, source_node=source_node, folder=target_folder))}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'content', 'content': f'文件生成失败：{str(e)[:200]}'})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
