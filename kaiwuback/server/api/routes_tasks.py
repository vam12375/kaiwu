"""Task API routes."""

from __future__ import annotations

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from server.agent.context_builder import build_task_payload
from server.agent.task_service import task_service


def register_task_routes(app: FastAPI):
    """Register task lifecycle endpoints."""

    @app.post("/api/tasks")
    async def create_task(request: Request):
        data = await request.json()
        if not data or not (data.get("message") or "").strip():
            return JSONResponse({"error": "message is required"}, status_code=400)
        payload = build_task_payload(data)
        task = task_service.create_task(payload)
        return {"task_id": task["id"], "task": task}

    @app.get("/api/tasks/{task_id}")
    def get_task(task_id: str):
        task = task_service.get_task_debug(task_id)
        if not task:
            return JSONResponse({"error": "task not found"}, status_code=404)
        return task

    @app.get("/api/tasks/{task_id}/events")
    def stream_task_events(task_id: str, after: int = Query(0, ge=0)):
        task = task_service.get_task(task_id)
        if not task:
            return JSONResponse({"error": "task not found"}, status_code=404)
        return StreamingResponse(
            task_service.stream_events(task_id, after_seq=after),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/api/tasks/{task_id}/cancel")
    def cancel_task(task_id: str):
        task = task_service.cancel_task(task_id)
        if not task:
            return JSONResponse({"error": "task not found"}, status_code=404)
        return {"status": "ok", "task": task}

    @app.post("/api/tasks/{task_id}/retry")
    def retry_task(task_id: str):
        task = task_service.retry_task(task_id)
        if not task:
            return JSONResponse({"error": "task not found"}, status_code=404)
        return {"task_id": task["id"], "task": task}
