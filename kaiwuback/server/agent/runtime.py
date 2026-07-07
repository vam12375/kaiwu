"""Agent runtime: routing, node execution orchestration, and event emission."""

from __future__ import annotations

import json
import re
import threading
import time
import uuid
from typing import Any, Iterable

from server.agent.event_store import EventStore
from server.agent.state_machine import ROUTING, RUNNING, STREAMING, SAVING, COMPLETED, FAILED, CANCELLED
from server.intent.recognizer import (
    DEPENDENCIES,
    _session_state,
    detect_followup_type,
    identify_node_intent,
    recognize_intent,
    save_session_state,
    validate_node_prerequisites,
)
from server.nodes.prompts import NODES
from server.orchestrator.handlers import handle_export, handle_summary
from server.orchestrator.llm_engine import generate_ai_response
from server.utils.common import (
    _extract_logo_prompts,
    _generate_logo_svg,
    append_conversation_messages,
    image_ratio_to_size,
    save_conversation,
    save_image_to_library,
)
from server.utils.session import save_session_state as sess_save
from server.llm_client import call_seedream

# 节点输出缓存：导出 HTML 时按 node 取对应内容，避免取错历史消息
_node_output_cache: dict[str, str] = {}


def get_node_output(node_id: str) -> str:
    """获取指定 node 的最新输出（用于导出 HTML）"""
    return _node_output_cache.get(node_id, "")


def clear_node_output_cache():
    """清空节点输出缓存"""
    _node_output_cache.clear()


class AgentRuntime:
    """Executes one task and writes all observable output to the event store."""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    def execute(self, task_id: str, payload: dict[str, Any]):
        """Run a task to a terminal status."""
        try:
            self._execute(task_id, payload)
        except Exception as exc:
            error = str(exc)[:500]
            print(f"[TASK] {task_id} failed: {error}", flush=True)
            try:
                if not self.event_store.is_cancelled(task_id):
                    self.event_store.update_task(task_id, status=FAILED, error=error)
                    self.emit(task_id, "error", {"message": error})
                    self.emit(task_id, "done", {})
            except Exception as inner:
                print(f"[TASK] failed to persist error: {inner}", flush=True)

    def _execute(self, task_id: str, payload: dict[str, Any]):
        message = payload["message"]
        history = payload.get("history") or []
        task_type = payload.get("task_type") or "chat"
        image_model = payload.get("image_model")
        image_ratio = payload.get("image_ratio") or "1:1"
        image_resolution = payload.get("image_resolution") or "2K"
        image_count = int(payload.get("image_count") or 1)
        reference_images = payload.get("reference_images") or []
        followup_node = payload.get("followup_node")
        selected_model = payload.get("model")
        conversation_id = payload.get("conversation_id")

        self.event_store.update_task(task_id, status=ROUTING)

        if task_type == "image_generation":
            self._execute_image_generation_task(
                task_id=task_id,
                message=message,
                history=history,
                image_model=image_model,
                image_ratio=image_ratio,
                image_resolution=image_resolution,
                image_count=image_count,
                reference_images=reference_images,
                conversation_id=conversation_id,
            )
            return

        if followup_node and followup_node in NODES:
            node_id = followup_node
            intent = {"node": followup_node.replace("node", ""), "topic": message[:30], "summary": message, "constraints": ""}
            self.emit(task_id, "analyzing", {"message": "正在延续上下文..."})
        else:
            self.emit(task_id, "analyzing", {"message": "正在分析您的需求意图..."})
            intent = recognize_intent(message, selected_model)
            node_id = self._node_id_from_intent(intent)
            node_id = self._apply_node0_context(node_id, message)

            if node_id == "fallback" and history and not self._is_node0_transition(message):
                followup_type = detect_followup_type(message, history)
                if followup_type.get("is_followup"):
                    node_id = _session_state.get("last_node") or "node1"
                    if node_id not in NODES:
                        node_id = "node1"
                    intent = {"node": node_id.replace("node", ""), "topic": message[:30], "summary": message, "constraints": ""}

        if self._cancelled(task_id):
            return

        if node_id == "node3.1" and self._should_run_direct_image_generation(message):
            self._execute_image_generation_task(
                task_id=task_id,
                message=message,
                history=history,
                image_model=image_model,
                image_ratio=image_ratio,
                image_resolution=image_resolution,
                image_count=image_count,
                reference_images=reference_images,
                conversation_id=conversation_id,
                emit_analyzing=False,
            )
            return

        if node_id in DEPENDENCIES and node_id not in ("fallback", "export", "summary"):
            node_intent = identify_node_intent(message)
            if node_intent["is_generation"]:
                validation = validate_node_prerequisites(node_id, history)
                if not validation["ok"]:
                    self.event_store.update_task(task_id, status=STREAMING, node_id=node_id)
                    self._stream_text(task_id, validation["message"])
                    self.event_store.update_task(task_id, status=SAVING)
                    saved_text, saved_conversation_id = self._save_conversation(
                        message=message,
                        history=history,
                        ai_text=validation["message"],
                        node_id=node_id,
                        intent=intent,
                        suggested_questions=[],
                        image_urls=[],
                        conversation_id=conversation_id,
                    )
                    self._emit_conversation_saved(task_id, saved_conversation_id, message, node_id)
                    self.event_store.update_task(task_id, status=COMPLETED, result=saved_text)
                    self.emit(task_id, "done", {})
                    return

        if node_id == "export":
            self.event_store.update_task(task_id, status=RUNNING, node_id=node_id)
            ai_text = self._relay_legacy_sse(task_id, handle_export(message, history, intent))
            if not self.event_store.is_cancelled(task_id):
                self.event_store.update_task(task_id, status=SAVING)
                saved_text, saved_conversation_id = self._save_conversation(
                    message=message,
                    history=history,
                    ai_text=ai_text or "文件导出任务已完成。",
                    node_id=node_id,
                    intent=intent,
                    suggested_questions=[],
                    image_urls=[],
                    conversation_id=conversation_id,
                )
                self._emit_conversation_saved(task_id, saved_conversation_id, message, node_id)
                self.event_store.update_task(task_id, status=COMPLETED, result=saved_text)
                self.emit(task_id, "done", {})
            return

        if node_id == "summary":
            self.event_store.update_task(task_id, status=RUNNING, node_id=node_id)
            ai_text = self._relay_legacy_sse(task_id, handle_summary(message, history, selected_model))
            if not self.event_store.is_cancelled(task_id):
                self.event_store.update_task(task_id, status=SAVING)
                saved_text, saved_conversation_id = self._save_conversation(
                    message=message,
                    history=history,
                    ai_text=ai_text or "报告生成任务已完成。",
                    node_id=node_id,
                    intent=intent,
                    suggested_questions=[],
                    image_urls=[],
                    conversation_id=conversation_id,
                )
                self._emit_conversation_saved(task_id, saved_conversation_id, message, node_id)
                self.event_store.update_task(task_id, status=COMPLETED, result=saved_text)
                self.emit(task_id, "done", {})
            return

        node = NODES[node_id]
        self.event_store.update_task(task_id, status=RUNNING, node_id=node_id)
        self.emit(
            task_id,
            "node_selected",
            {
                "node": node_id,
                "name": node["name"],
                "icon": node["icon"],
                "topic": intent.get("topic", ""),
                "summary": intent.get("summary", ""),
            },
        )

        ai_response = [None]
        llm_error = [None]

        def run_llm():
            try:
                ai_response[0] = generate_ai_response(node_id, message, history, selected_model, bool(followup_node))
            except Exception as exc:
                llm_error[0] = str(exc)[:300]

        llm_thread = threading.Thread(target=run_llm, daemon=True)
        llm_thread.start()
        llm_start_time = time.time()
        total_steps = len(node["steps"])
        base_pct = 10
        expected_duration = node.get("expected_duration", 90 if node.get("need_search") else 30)
        last_progress = base_pct

        while llm_thread.is_alive():
            if self._cancelled(task_id):
                return
            elapsed = time.time() - llm_start_time
            progress = base_pct + min(85, int(85 * (elapsed / expected_duration)))
            progress = min(95, progress)
            progress = max(last_progress, progress)
            last_progress = progress
            step_idx = min(total_steps - 1, int((progress - base_pct) / 80 * total_steps))
            step_msg = node["steps"][step_idx]["msg"]
            self.emit(task_id, "progress", {"node": node_id, "message": step_msg, "percent": progress})
            time.sleep(0.4)

        llm_thread.join(timeout=5)
        if self._cancelled(task_id):
            return

        self.emit(task_id, "progress", {"node": node_id, "message": "正在生成最终报告...", "percent": 97})

        if llm_error[0]:
            ai_text = f"抱歉，AI 服务暂时不可用。错误信息：{llm_error[0]}"
        elif ai_response[0] and len(ai_response[0]) > 20:
            ai_text = ai_response[0]
        else:
            ai_text = "抱歉，AI 服务暂时不可用。请稍后重试。"

        print(f"[RESPONSE] Node={node_id}, len={len(ai_text)}, err={bool(llm_error[0])}", flush=True)
        sess_save(history, node_id)
        save_session_state(history, node_id)

        # 缓存节点输出，供导出 HTML 时按 node 取对应内容
        _node_output_cache[node_id] = ai_text

        # node0 完成后将 dialogue_brief.md 存入 AI 对话产出
        if node_id == "node0":
            import re as _re_md
            m = _re_md.search(
                r'(# 品牌全案策略 · 对话信息摘要.*?)(?:```\s*$|以上为 node0)',
                ai_text, _re_md.DOTALL
            )
            brief_md = m.group(1).strip() if m else ""
            if brief_md:
                from server.config import PROJECT_LIB
                (PROJECT_LIB / "AI 对话产出").mkdir(parents=True, exist_ok=True)
                fname = f"dialogue_brief_{uuid.uuid4().hex[:6]}.md"
                (PROJECT_LIB / "AI 对话产出" / fname).write_text(brief_md, encoding='utf-8')
                print(f"[NODE0] dialogue_brief.md → AI 对话产出", flush=True)

        suggested_questions = self._suggested_questions(node_id)

        self.event_store.update_task(task_id, status=STREAMING)
        self.emit(task_id, "response_start", {})
        self._stream_text(task_id, ai_text)

        if suggested_questions:
            self.emit(task_id, "suggestions", {"items": suggested_questions[:3]})

        image_urls = []
        if node_id == "node3.1":
            self._generate_svg_logos(task_id)

        if node_id in ("node1.5", "node3.1"):
            image_urls = self._generate_images(task_id, node_id, ai_text, image_ratio, image_count)

        if self._cancelled(task_id):
            return

        self.event_store.update_task(task_id, status=SAVING)
        saved_text, saved_conversation_id = self._save_conversation(
            message=message,
            history=history,
            ai_text=ai_text,
            node_id=node_id,
            intent=intent,
            suggested_questions=suggested_questions,
            image_urls=image_urls,
            conversation_id=conversation_id,
        )
        if saved_conversation_id:
            self._emit_conversation_saved(task_id, saved_conversation_id, message, node_id)
        self.event_store.update_task(task_id, status=COMPLETED, result=saved_text)
        self.emit(task_id, "progress", {"node": node_id, "message": "生成完成", "percent": 100})
        self.emit(task_id, "done", {})

    def emit(self, task_id: str, event_type: str, payload: dict[str, Any] | None = None):
        self.event_store.write_event(task_id, event_type, payload or {})

    def _stream_text(self, task_id: str, text: str):
        chunk_size = 12
        for i in range(0, len(text), chunk_size):
            if self._cancelled(task_id):
                return
            self.emit(task_id, "content", {"content": text[i : i + chunk_size]})
            time.sleep(0.006)

    def _execute_image_generation_task(
        self,
        *,
        task_id: str,
        message: str,
        history: list,
        image_model: str | None,
        image_ratio: str,
        image_resolution: str,
        image_count: int,
        reference_images: list[dict[str, Any]],
        conversation_id: int | None,
        emit_analyzing: bool = True,
    ):
        node_id = "image_generation"
        intent = {"node": "image_generation", "topic": message[:30], "summary": message, "constraints": ""}
        if emit_analyzing:
            self.emit(task_id, "analyzing", {"message": "正在准备图片生成任务..."})
        if self._cancelled(task_id):
            return

        self.event_store.update_task(task_id, status=RUNNING, node_id=node_id)
        self.emit(
            task_id,
            "image_gen_start",
            {
                "count": image_count,
                "label": "图片生成",
                "message": f"正在生成 {image_count} 张图片...",
            },
        )

        reference_data_urls = [
            item["data_url"]
            for item in reference_images
            if isinstance(item, dict) and isinstance(item.get("data_url"), str)
        ]
        image_prompt = self._build_direct_image_prompt(message, image_ratio)
        image_urls: list[dict[str, str]] = []

        self.event_store.update_task(task_id, status=STREAMING, node_id=node_id)
        for img_i in range(image_count):
            if self._cancelled(task_id):
                return
            percent = 15 + int(80 * (img_i + 1) / image_count)
            self.emit(
                task_id,
                "progress",
                {
                    "node": node_id,
                    "message": f"正在生成第 {img_i + 1} 张图片...",
                    "percent": percent,
                },
            )

            try:
                if img_i > 0:
                    time.sleep(1)
                result: list[str] = []

                def run_seedream():
                    try:
                        result.extend(
                            call_seedream(
                                image_prompt,
                                size=image_resolution,
                                model=image_model,
                                reference_images=reference_data_urls,
                            )
                        )
                    except Exception as exc:
                        result.append(f"ERR:{exc}")

                thread = threading.Thread(target=run_seedream, daemon=True)
                thread.start()
                while thread.is_alive():
                    if self._cancelled(task_id):
                        return
                    thread.join(timeout=2)

                urls = [url for url in result if not str(url).startswith("ERR:")]
                if any(str(url).startswith("ERR:") for url in result):
                    err_msg = next(str(url)[4:] for url in result if str(url).startswith("ERR:"))
                    raise RuntimeError(err_msg)
                if not urls:
                    raise RuntimeError("Seedream API did not return an image URL")

                provider_url = urls[0]
                display_url = provider_url
                try:
                    filename = save_image_to_library(provider_url, "AI生图")
                    display_url = f"http://localhost:5001/project-images/{filename}"
                except Exception as exc:
                    print(f"[IMG] Save failed: {exc}", flush=True)

                image = {"style": f"图片生成#{img_i + 1}", "url": display_url, "prompt": message}
                image_urls.append(image)
                self.emit(task_id, "image", image)
            except Exception as exc:
                print(f"[IMAGE] Failed for direct image generation: {exc}", flush=True)
                self.emit(task_id, "image_error", {"style": f"图片生成#{img_i + 1}", "error": str(exc)[:200]})

        if self._cancelled(task_id):
            return

        if not image_urls:
            raise RuntimeError("图片生成失败，请稍后重试。")

        self.event_store.update_task(task_id, status=SAVING)
        saved_text, saved_conversation_id = self._save_conversation(
            message=message,
            history=history,
            ai_text="图片生成完成",
            node_id=node_id,
            intent=intent,
            suggested_questions=[],
            image_urls=image_urls,
            conversation_id=conversation_id,
        )
        if saved_conversation_id:
            self._emit_conversation_saved(task_id, saved_conversation_id, message, node_id)
        self.event_store.update_task(task_id, status=COMPLETED, result=saved_text)
        self.emit(task_id, "progress", {"node": node_id, "message": "图片生成完成", "percent": 100})
        self.emit(task_id, "done", {})

    @staticmethod
    def _build_direct_image_prompt(message: str, image_ratio: str) -> str:
        text = message.strip()
        if re.search(r"--ar\s+\d+:\d+", text):
            return text
        return f"{text} --ar {image_ratio}"

    @staticmethod
    def _is_logo_request(message: str) -> bool:
        lower = message.lower()
        logo_keywords = ("logo", "brand mark", "brandmark", "标志", "品牌标识", "品牌标志", "商标")
        return any(keyword in lower for keyword in logo_keywords)

    @classmethod
    def _should_run_direct_image_generation(cls, message: str) -> bool:
        if cls._is_logo_request(message):
            return False
        lower = message.lower()
        image_keywords = (
            "生成图片",
            "生成图",
            "生成一张",
            "图片生成",
            "文生图",
            "出图",
            "画一张",
            "帮我画",
            "照片",
            "写真",
            "实拍",
            "画面",
            "镜头",
            "构图",
            "光影",
            "场景",
            "人物",
            "image",
            "photo",
            "portrait",
        )
        return any(keyword in lower for keyword in image_keywords)

    def _generate_svg_logos(self, task_id: str) -> list[dict[str, str]]:
        self.emit(task_id, "svg_gen_start", {"count": 3})
        svg_styles = [
            ("极简符号", {"shape": "circle", "mainColor": "#1a1a2e", "accentColor": "#c9a96e", "element": "star"}),
            ("古典徽章", {"shape": "shield", "mainColor": "#2d2d2d", "accentColor": "#d4a853", "element": "crown"}),
            ("现代字体", {"shape": "roundrect", "mainColor": "#0f172a", "accentColor": "#6366f1", "element": "gem"}),
        ]
        results = []
        for style, params in svg_styles:
            if self._cancelled(task_id):
                return results
            try:
                svg_code = _generate_logo_svg(params)
                results.append({"style": style, "code": svg_code})
                self.emit(task_id, "svg", {"style": style, "code": svg_code})
            except Exception as exc:
                print(f"[SVG] Failed for {style}: {exc}", flush=True)
        return results

    def _generate_images(
        self,
        task_id: str,
        node_id: str,
        ai_text: str,
        image_ratio: str,
        image_count: int,
    ) -> list[dict[str, str]]:
        image_prompts = _extract_logo_prompts(ai_text, node_id)
        image_urls = []
        if not image_prompts:
            return image_urls

        self.emit(task_id, "image_gen_start", {"count": len(image_prompts)})
        for idx, (style, prompt) in enumerate(image_prompts):
            custom_prompt = re.sub(r"--ar\s+\d+:\d+", f"--ar {image_ratio}", prompt)
            for img_i in range(image_count):
                if self._cancelled(task_id):
                    return image_urls
                percent = 90 + int(8 * (idx + 1) / len(image_prompts))
                self.emit(
                    task_id,
                    "progress",
                    {
                        "node": node_id,
                        "message": f"正在生成风格{idx + 1}第{img_i + 1}张：{style}...",
                        "percent": percent,
                    },
                )
                try:
                    if idx > 0 or img_i > 0:
                        time.sleep(1)
                    result = []

                    def run_seedream():
                        try:
                            result.extend(call_seedream(custom_prompt, size=image_ratio_to_size(image_ratio)))
                        except Exception as exc:
                            result.append(f"ERR:{exc}")

                    thread = threading.Thread(target=run_seedream, daemon=True)
                    thread.start()
                    while thread.is_alive():
                        if self._cancelled(task_id):
                            return image_urls
                        thread.join(timeout=2)
                    urls = [url for url in result if not str(url).startswith("ERR:")]
                    if any(str(url).startswith("ERR:") for url in result):
                        err_msg = next(str(url)[4:] for url in result if str(url).startswith("ERR:"))
                        raise RuntimeError(err_msg)
                    if urls:
                        try:
                            from server.utils.common import save_image_to_library

                            save_image_to_library(urls[0], style[:4])
                        except Exception as exc:
                            print(f"[IMG] Save failed: {exc}", flush=True)
                        image = {"style": f"{style}#{img_i + 1}", "url": urls[0], "prompt": prompt}
                        image_urls.append(image)
                        self.emit(task_id, "image", image)
                except Exception as exc:
                    print(f"[IMAGE] Failed for {style}: {exc}", flush=True)
                    self.emit(task_id, "image_error", {"style": style, "error": str(exc)[:200]})
        return image_urls

    def _save_conversation(
        self,
        *,
        message: str,
        history: list,
        ai_text: str,
        node_id: str,
        intent: dict[str, Any],
        suggested_questions: list[str],
        image_urls: list[dict[str, str]],
        conversation_id: int | None,
    ) -> tuple[str, int | None]:
        saved_text = ai_text
        if image_urls:
            saved_text += "\n\n" + "\n".join([f"![{img['style']}]({img['url']})" for img in image_urls])
        if suggested_questions:
            saved_text += "\n\n<!--suggestions:" + json.dumps(suggested_questions, ensure_ascii=False) + "-->"

        try:
            if conversation_id:
                append_conversation_messages(
                    conversation_id,
                    [
                        {"role": "user", "content": message},
                        {"role": "ai", "content": saved_text},
                    ],
                )
                return saved_text, int(conversation_id)

            all_msgs = list(history) if history else []
            all_msgs.append({"role": "user", "content": message})
            all_msgs.append({"role": "ai", "content": saved_text})
            title = message[:40] + ("..." if len(message) > 40 else "")
            new_conversation_id = save_conversation(title, node_id, intent.get("topic", ""), all_msgs)
            return saved_text, int(new_conversation_id)
        except Exception as exc:
            print(f"[DB] Save failed: {exc}", flush=True)
        return saved_text, None

    def _relay_legacy_sse(self, task_id: str, packets: Iterable[str]) -> str:
        content_parts = []
        for packet in packets:
            if self._cancelled(task_id):
                return "\n".join(content_parts)
            for event in self._parse_sse_packet(packet):
                event_type = event.pop("type", None)
                if not event_type:
                    continue
                if event_type == "content":
                    content_parts.append(event.get("content", ""))
                elif event_type == "file_saved" and event.get("message"):
                    content_parts.append(f"\n\n📁 {event['message']}")
                if event_type == "done":
                    continue
                self.emit(task_id, event_type, event)
        return "".join(content_parts).strip()

    def _emit_conversation_saved(self, task_id: str, conversation_id: int | None, message: str, node_id: str):
        if not conversation_id:
            return
        self.event_store.update_task(task_id, conversation_id=conversation_id)
        self.emit(
            task_id,
            "conversation_saved",
            {
                "conversation_id": conversation_id,
                "title": message[:40] + ("..." if len(message) > 40 else ""),
                "node_id": node_id,
            },
        )

    @staticmethod
    def _parse_sse_packet(packet: str) -> list[dict[str, Any]]:
        events = []
        for segment in packet.split("\n\n"):
            for line in segment.splitlines():
                if not line.startswith("data: "):
                    continue
                try:
                    events.append(json.loads(line[6:]))
                except Exception:
                    pass
        return events

    @staticmethod
    def _node_id_from_intent(intent: dict[str, Any]) -> str:
        nid = intent.get("node")
        if nid == "fallback":
            return "fallback"
        if nid == "export":
            return "export"
        if nid == "summary":
            return "summary"
        node_id = f"node{nid}" if nid else "fallback"
        if node_id not in NODES and node_id not in ("export", "summary"):
            return "fallback"
        return node_id

    @staticmethod
    def _is_node0_transition(message: str) -> bool:
        # 短消息（≤30字）才视为切换指令；长消息是诊断回答，不触发切换
        if len(message.strip()) > 30:
            return False
        transition_signals = ["开始调研", "做商业方案", "产品设计", "营销方案", "营销文案", "品牌设计"]
        return any(keyword in message for keyword in transition_signals)

    def _apply_node0_context(self, node_id: str, message: str) -> str:
        last_node = _session_state.get("last_node")
        if last_node != "node0":
            return node_id
        if self._is_node0_transition(message):
            if any(keyword in message for keyword in ["开始调研", "生成报告"]):
                return "node1"
            if any(keyword in message for keyword in ["做商业方案", "商业方案"]):
                return "node2"
            if "产品设计" in message:
                return "node3"
            if "营销方案" in message:
                return "node4"
            if "营销文案" in message:
                return "node5"
            if "品牌设计" in message:
                return "node1.5"
        if node_id != "node0":
            return "node0"
        return node_id

    @staticmethod
    def _suggested_questions(node_id: str) -> list[str]:
        if node_id == "node2":
            return ["能详细展开品牌定位部分吗？", "产品体系方面有什么建议？", "盈利模式如何落地执行？"]
        if node_id == "node1":
            return ["这个市场的规模增速是多少？", "核心目标人群是谁？", "有哪些竞品值得关注？"]
        return []

    def _cancelled(self, task_id: str) -> bool:
        if not self.event_store.is_cancelled(task_id):
            return False
        self.event_store.update_task(task_id, status=CANCELLED)
        self.emit(task_id, "done", {})
        return True
