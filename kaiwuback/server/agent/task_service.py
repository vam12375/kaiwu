"""Task service API for creating, streaming, cancelling, and retrying tasks."""

from __future__ import annotations

import json
import threading
from typing import Any, Generator

from server.agent.event_store import EventStore, event_store
from server.agent.runtime import AgentRuntime
from server.agent.state_machine import QUEUED, CANCELLED, TERMINAL_STATUSES


class TaskService:
    def __init__(self, store: EventStore):
        self.store = store
        self.runtime = AgentRuntime(store)

    def create_task(self, payload: dict[str, Any], *, autostart: bool = True) -> dict[str, Any]:
        task = self.store.create_task(payload)
        self.store.update_task(task["id"], status=QUEUED)
        self.store.write_event(task["id"], "task_created", {"status": QUEUED})
        if autostart:
            self.start_task(task["id"], payload)
        return self.store.get_task(task["id"]) or task

    def start_task(self, task_id: str, payload: dict[str, Any]):
        thread = threading.Thread(target=self.runtime.execute, args=(task_id, payload), daemon=True)
        thread.start()

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return self.store.get_task(task_id)

    def get_task_debug(self, task_id: str) -> dict[str, Any] | None:
        return self.store.get_task_debug(task_id)

    def cancel_task(self, task_id: str) -> dict[str, Any] | None:
        return self.store.mark_cancelled(task_id)

    def retry_task(self, task_id: str) -> dict[str, Any] | None:
        task = self.store.get_task(task_id)
        if not task:
            return None
        payload = task.get("input") or {}
        return self.create_task(payload, autostart=True)

    def stream_events(self, task_id: str, after_seq: int = 0) -> Generator[str, None, None]:
        last_seq = after_seq
        while True:
            events = self.store.wait_for_events(task_id, last_seq, timeout=1.0)
            for event in events:
                last_seq = max(last_seq, event["seq"])
                data = self.store.stream_event_dict(event)
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                if event["type"] == "done":
                    return

            task = self.store.get_task(task_id)
            if task and task["status"] in TERMINAL_STATUSES:
                if task["status"] == CANCELLED:
                    yield f"data: {json.dumps({'type': 'cancelled', 'task_id': task_id, 'seq': last_seq + 1}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'task_id': task_id, 'seq': last_seq + 1}, ensure_ascii=False)}\n\n"
                return


task_service = TaskService(event_store)
