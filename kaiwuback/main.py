#!/usr/bin/env python3
"""Kaiwu Backend - FastAPI entrypoint."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from server.agent.context_builder import build_task_payload
from server.agent.task_service import task_service
from server.api.routes_conv import register_conv_routes
from server.api.routes_events import register_event_routes
from server.api.routes_files import register_file_routes
from server.api.routes_skills import register_skills_routes
from server.api.routes_tasks import register_task_routes
from server.config import PUBLIC_BASE_URL
from server.nodes.prompts import NODES


app = FastAPI(title="Kaiwu Backend", version="4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_skills_routes(app)
register_file_routes(app)
register_conv_routes(app)
register_task_routes(app)
register_event_routes(app)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "kaiwu-backend",
        "framework": "FastAPI",
        "architecture": "task-driven-agent-runtime",
        "nodes": list(NODES.keys()),
    }


@app.post("/api/chat")
async def chat_compat(request: Request):
    """Deprecated compatibility endpoint.

    New clients should use:
    - POST /api/tasks
    - GET /api/tasks/{task_id}/events
    """
    data = await request.json()
    if not data or not (data.get("message") or "").strip():
        return JSONResponse({"error": "message is required"}, status_code=400)

    payload = build_task_payload(data)
    task = task_service.create_task(payload)
    return StreamingResponse(
        task_service.stream_events(task["id"]),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Kaiwu-Task-Id": task["id"]},
    )


if __name__ == "__main__":
    import uvicorn

    public_label = PUBLIC_BASE_URL or "relative same-origin URLs"
    print(f"Kaiwu Backend (FastAPI) starting; public base: {public_label}")
    uvicorn.run(app, host="0.0.0.0", port=5001)
