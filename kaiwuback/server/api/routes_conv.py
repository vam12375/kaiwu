"""对话与项目管理 API 路由 —— 从 main.py 抽取"""
import json
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from server.config import DB_CONFIG
from server.utils.common import (
    generate_html_file, save_project_file, save_project_file_bytes,
    html_to_pdf, get_db, save_conversation, update_conversation_messages,
    list_conversations, load_conversation, delete_conversation,
)


def register_conv_routes(app):
    """向 FastAPI app 注册对话/项目管理相关路由"""

    @app.get("/api/conversations")
    def api_list_conversations():
        return list_conversations()

    @app.get("/api/conversations/{conv_id}")
    def api_load_conversation(conv_id: int):
        conv = load_conversation(conv_id)
        if not conv:
            return JSONResponse({"error": "Conversation not found"}, status_code=404)
        return conv

    @app.post("/api/conversations/{conv_id}/rename")
    async def api_rename_conversation(conv_id: int, request: Request):
        data = await request.json()
        new_title = data.get('title', '')
        if not new_title:
            return JSONResponse({"error": "title required"}, status_code=400)
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("UPDATE conversations SET title = %s WHERE id = %s", (new_title, conv_id))
                db.commit()
            return {"status": "ok"}
        finally:
            db.close()

    @app.delete("/api/conversations/{conv_id}")
    def api_delete_conversation(conv_id: int):
        delete_conversation(conv_id)
        return {"status": "ok"}

    @app.post("/api/conversations/save")
    async def api_save_placeholder(request: Request):
        data = await request.json()
        if not data:
            return JSONResponse({"error": "data required"}, status_code=400)
        conv_id = data.get('conv_id')
        title = data.get('title', '新对话')
        messages = data.get('messages', [])
        node_id = data.get('node_id', '')
        try:
            if conv_id and conv_id < 1000000000:
                update_conversation_messages(conv_id, messages)
            else:
                conv_id = save_conversation(title, node_id, '', messages)
            updated_list = list_conversations()
            return {"id": conv_id, "status": "updated" if data.get('conv_id') else "saved", "conversations": updated_list}
        except Exception as e:
            print(f"[DB] Save error: {e}", flush=True)
            return JSONResponse({"error": str(e)[:200]}, status_code=500)

    @app.post("/api/save-to-project")
    async def api_save_to_project(request: Request):
        data = await request.json()
        content = data.get('content', '')
        title = data.get('title', 'AI对话')[:40]
        if not content.strip():
            return JSONResponse({"error": "content required"}, status_code=400)
        try:
            html_content = generate_html_file(content, title)
            html_path = save_project_file(html_content, title, "AI 对话产出", "html")
            pdf_path = ""
            try:
                pdf_bytes = html_to_pdf(html_content)
                if pdf_bytes:
                    pdf_path = save_project_file_bytes(pdf_bytes, title, "AI 对话产出", "pdf")
            except Exception as e:
                print(f"[PDF] failed: {e}", flush=True)
            msg = "已保存至 AI 对话产出"
            if pdf_path:
                msg += " (HTML + PDF)"
            return {"status": "ok", "path": html_path, "pdf_path": pdf_path, "message": msg}
        except Exception as e:
            return JSONResponse({"error": str(e)[:200]}, status_code=500)
