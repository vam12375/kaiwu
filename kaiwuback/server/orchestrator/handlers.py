"""报告生成与文件导出的 SSE 流处理器 —— 从 main.py 抽取"""
import json
import time
import threading
from pathlib import Path
from datetime import datetime

from server.utils.common import generate_html_file, save_project_file


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
        content_text = f"✅ **{report_title}** 已生成\n\n存放位置：\n- 编程文件库\n- AI 对话产出\n\n已在 Chrome 中打开。"
        yield f"data: {json.dumps({'type': 'content', 'content': content_text})}\n\n"
        file_msg = f"{report_title}已保存至「编程文件库」+「AI 对话产出」"
        yield f"data: {json.dumps({'type': 'file_saved', 'message': file_msg, 'folder': '编程文件库', 'auto_preview': True, 'desktop_path': file_path})}\n\n"

    yield f"data: {json.dumps({'type': 'progress', 'node': 'summary', 'message': '完成', 'percent': 100})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


def handle_export(message: str, history: list, intent: dict):
    """处理文件导出请求，SSE 流式推送进度"""
    source_node = "node1"
    node_keywords = {
        "node1": ["调研", "市场", "行业", "竞品", "用户画像", "洞察", "TAM", "SAM", "需求"],
        "node2": ["商业方案", "定位", "产品矩阵", "盈利", "风控", "供应链", "赛道"],
        "node3": ["Logo", "logo", "图片", "素材", "海报", "视觉", "设计图"],
        "node1.5": ["品牌理念", "品牌故事", "Slogan", "品牌屋", "品牌精神", "品牌策略"],
        "node5": ["种草", "文案", "详情页", "话术", "短视频", "营销投放", "小红书", "抖音"],
        "node4": ["PPT", "大纲", "页面要点", "汇报", "方案汇报"],
    }
    max_score = 0
    for node, keywords in node_keywords.items():
        score = sum(1 for kw in keywords if kw in message or (history and any(kw in m.get("content", "") for m in history)))
        if score > max_score:
            max_score = score
            source_node = node

    content_parts = []
    if history:
        for m in history:
            if m.get("role") == "ai" and m.get("content"):
                content_parts.append(m["content"])
    full_content = "\n\n".join(content_parts[-3:]) if content_parts else message
    if not full_content.strip():
        full_content = message
    title = intent.get('topic', 'AI导出')[:30]

    yield f"data: {json.dumps({'type': 'progress', 'node': 'export', 'message': f'已识别上下文：{source_node}，正在生成HTML文件...', 'percent': 50})}\n\n"

    folder_map = {"node1": "创业资料", "node2": "创业资料", "node1.5": "产品设计", "node3": "产品设计", "node5": "营销素材", "node4": "AI 对话产出"}
    target_folder = folder_map.get(source_node, "AI 对话产出")

    try:
        html_content = generate_html_file(full_content, title)
        path1 = save_project_file(html_content, title, "编程文件库", "html")
        save_project_file(html_content, title, target_folder, "html")
        save_project_file(html_content, title, "AI 对话产出", "html")
        yield f"data: {json.dumps({'type': 'file_saved', 'message': f'已调取{source_node}数据生成HTML，存入「编程文件库」+「{target_folder}」', 'folder': target_folder, 'auto_preview': True})}\n\n"
        yield f"data: {json.dumps({'type': 'content', 'content': f'✅ 文件已生成\\n\\n调取节点：{source_node}\\n文件类型：HTML\\n存放位置：编程文件库 + {target_folder}'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'content', 'content': f'文件生成失败：{str(e)[:200]}'})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
