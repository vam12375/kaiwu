"""Persistent task/event store for the Agent runtime."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from typing import Any

import pymysql

from server.persistence.database import get_db
from server.agent.state_machine import CREATED, CANCELLED, TERMINAL_STATUSES, require_transition


class EventStore:
    """Stores task lifecycle state and SSE events.

    MySQL is the primary store. If the database is unavailable during local
    development, this class falls back to an in-memory store so the API layer
    can still boot and tests can exercise the routing surface.
    """

    def __init__(self):
        self._schema_ready = False
        self._db_available = True
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._memory_tasks: dict[str, dict[str, Any]] = {}
        self._memory_events: dict[str, list[dict[str, Any]]] = {}

    def ensure_schema(self):
        if self._schema_ready or not self._db_available:
            return
        try:
            db = get_db()
            try:
                with db.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS agent_tasks (
                            id VARCHAR(36) PRIMARY KEY,
                            conversation_id BIGINT NULL,
                            status VARCHAR(32) NOT NULL,
                            node_id VARCHAR(32) NULL,
                            input LONGTEXT NOT NULL,
                            result LONGTEXT NULL,
                            error TEXT NULL,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL,
                            INDEX idx_agent_tasks_conversation (conversation_id),
                            INDEX idx_agent_tasks_status (status),
                            INDEX idx_agent_tasks_updated (updated_at)
                        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS agent_events (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            task_id VARCHAR(36) NOT NULL,
                            `type` VARCHAR(64) NOT NULL,
                            payload LONGTEXT NOT NULL,
                            seq INT NOT NULL,
                            created_at DATETIME NOT NULL,
                            UNIQUE KEY uniq_agent_events_task_seq (task_id, seq),
                            INDEX idx_agent_events_task (task_id, seq),
                            CONSTRAINT fk_agent_events_task
                                FOREIGN KEY (task_id) REFERENCES agent_tasks(id)
                                ON DELETE CASCADE
                        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                        """
                    )
                db.commit()
                self._schema_ready = True
            finally:
                db.close()
        except Exception as exc:
            self._db_available = False
            print(f"[EVENT_STORE] MySQL unavailable, using memory store: {exc}", flush=True)

    def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.ensure_schema()
        task_id = str(uuid.uuid4())
        now = datetime.now()
        task = {
            "id": task_id,
            "conversation_id": payload.get("conversation_id"),
            "status": CREATED,
            "node_id": None,
            "input": payload,
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        if not self._db_available:
            with self._condition:
                self._memory_tasks[task_id] = task
                self._memory_events[task_id] = []
                self._condition.notify_all()
            return self._public_task(task)

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_tasks
                        (id, conversation_id, status, node_id, input, result, error, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        task_id,
                        payload.get("conversation_id"),
                        CREATED,
                        None,
                        json.dumps(payload, ensure_ascii=False),
                        None,
                        None,
                        now,
                        now,
                    ),
                )
            db.commit()
            return self.get_task(task_id) or self._public_task(task)
        finally:
            db.close()

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        self.ensure_schema()
        if not self._db_available:
            with self._lock:
                task = self._memory_tasks.get(task_id)
                return self._public_task(task) if task else None

        db = get_db()
        try:
            with db.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute("SELECT * FROM agent_tasks WHERE id = %s", (task_id,))
                row = cur.fetchone()
            if not row:
                return None
            row["input"] = self._loads(row.get("input"), {})
            return self._public_task(row)
        finally:
            db.close()

    def get_task_debug(self, task_id: str) -> dict[str, Any] | None:
        """Return the compact task debugging view used by GET /api/tasks/{id}."""
        task = self.get_task(task_id)
        if not task:
            return None
        stats = self.get_event_stats(task_id)
        return {
            "id": task["id"],
            "status": task["status"],
            "node_id": task.get("node_id"),
            "conversation_id": task.get("conversation_id"),
            "event_count": stats["event_count"],
            "last_seq": stats["last_seq"],
            "error": task.get("error"),
        }

    def get_event_stats(self, task_id: str) -> dict[str, int]:
        self.ensure_schema()
        if not self._db_available:
            with self._lock:
                events = self._memory_events.get(task_id, [])
                last_seq = max((event["seq"] for event in events), default=0)
                return {"event_count": len(events), "last_seq": last_seq}

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*), COALESCE(MAX(seq), 0) FROM agent_events WHERE task_id = %s",
                    (task_id,),
                )
                row = cur.fetchone()
            return {"event_count": int(row[0] or 0), "last_seq": int(row[1] or 0)}
        finally:
            db.close()

    def update_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        conversation_id: int | None = None,
        node_id: str | None = None,
        result: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any] | None:
        self.ensure_schema()
        now = datetime.now()
        current = self.get_task(task_id)
        if not current:
            return None
        if status:
            require_transition(current["status"], status)

        if not self._db_available:
            with self._condition:
                task = self._memory_tasks.get(task_id)
                if not task:
                    return None
                if status:
                    task["status"] = status
                if conversation_id is not None:
                    task["conversation_id"] = conversation_id
                if node_id is not None:
                    task["node_id"] = node_id
                if result is not None:
                    task["result"] = result
                if error is not None:
                    task["error"] = error
                task["updated_at"] = now
                self._condition.notify_all()
                return self._public_task(task)

        fields: list[str] = []
        values: list[Any] = []
        if status:
            fields.append("status = %s")
            values.append(status)
        if conversation_id is not None:
            fields.append("conversation_id = %s")
            values.append(conversation_id)
        if node_id is not None:
            fields.append("node_id = %s")
            values.append(node_id)
        if result is not None:
            fields.append("result = %s")
            values.append(result)
        if error is not None:
            fields.append("error = %s")
            values.append(error)
        fields.append("updated_at = %s")
        values.append(now)
        values.append(task_id)

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(f"UPDATE agent_tasks SET {', '.join(fields)} WHERE id = %s", values)
            db.commit()
            with self._condition:
                self._condition.notify_all()
            return self.get_task(task_id)
        finally:
            db.close()

    def mark_cancelled(self, task_id: str) -> dict[str, Any] | None:
        task = self.get_task(task_id)
        if not task:
            return None
        if task["status"] in TERMINAL_STATUSES:
            return task
        updated = self.update_task(task_id, status=CANCELLED)
        self.write_event(task_id, "cancelled", {"message": "任务已取消"})
        return updated

    def is_cancelled(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        return bool(task and task["status"] == CANCELLED)

    def write_event(self, task_id: str, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_schema()
        now = datetime.now()
        payload = payload or {}
        if not self._db_available:
            with self._condition:
                events = self._memory_events.setdefault(task_id, [])
                seq = len(events) + 1
                event = {
                    "id": seq,
                    "task_id": task_id,
                    "type": event_type,
                    "payload": payload,
                    "seq": seq,
                    "created_at": now,
                }
                events.append(event)
                self._condition.notify_all()
                return dict(event)

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM agent_events WHERE task_id = %s", (task_id,))
                seq = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO agent_events (task_id, `type`, payload, seq, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (task_id, event_type, json.dumps(payload, ensure_ascii=False), seq, now),
                )
                event_id = cur.lastrowid
            db.commit()
            event = {
                "id": event_id,
                "task_id": task_id,
                "type": event_type,
                "payload": payload,
                "seq": seq,
                "created_at": now,
            }
            with self._condition:
                self._condition.notify_all()
            return event
        finally:
            db.close()

    def list_events(self, task_id: str, after_seq: int = 0) -> list[dict[str, Any]]:
        self.ensure_schema()
        if not self._db_available:
            with self._lock:
                return [dict(event) for event in self._memory_events.get(task_id, []) if event["seq"] > after_seq]

        db = get_db()
        try:
            with db.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute(
                    "SELECT id, task_id, `type`, payload, seq, created_at FROM agent_events WHERE task_id = %s AND seq > %s ORDER BY seq ASC",
                    (task_id, after_seq),
                )
                rows = cur.fetchall()
            for row in rows:
                row["payload"] = self._loads(row.get("payload"), {})
            return rows
        finally:
            db.close()

    def wait_for_events(self, task_id: str, after_seq: int, timeout: float = 1.0) -> list[dict[str, Any]]:
        events = self.list_events(task_id, after_seq)
        if events:
            return events
        with self._condition:
            self._condition.wait(timeout=timeout)
        return self.list_events(task_id, after_seq)

    def stream_event_dict(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = event.get("payload") or {}
        return {"type": event["type"], **payload, "task_id": event["task_id"], "seq": event["seq"]}

    @staticmethod
    def _loads(raw: Any, fallback: Any) -> Any:
        if raw is None:
            return fallback
        if isinstance(raw, (dict, list)):
            return raw
        try:
            return json.loads(raw)
        except Exception:
            return fallback

    @staticmethod
    def _public_task(task: dict[str, Any] | None) -> dict[str, Any]:
        if not task:
            return {}
        return {
            "id": task["id"],
            "conversation_id": task.get("conversation_id"),
            "status": task["status"],
            "node_id": task.get("node_id"),
            "input": task.get("input"),
            "result": task.get("result"),
            "error": task.get("error"),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
        }


event_store = EventStore()
