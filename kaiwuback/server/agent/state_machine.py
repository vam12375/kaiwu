"""Task lifecycle state machine."""

from __future__ import annotations

from dataclasses import dataclass


CREATED = "created"
QUEUED = "queued"
ROUTING = "routing"
RUNNING = "running"
STREAMING = "streaming"
SAVING = "saving"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"

TERMINAL_STATUSES = {COMPLETED, FAILED, CANCELLED}

ALLOWED_TRANSITIONS = {
    CREATED: {QUEUED, ROUTING, CANCELLED, FAILED},
    QUEUED: {ROUTING, RUNNING, CANCELLED, FAILED},
    ROUTING: {RUNNING, STREAMING, SAVING, COMPLETED, CANCELLED, FAILED},
    RUNNING: {STREAMING, SAVING, COMPLETED, CANCELLED, FAILED},
    STREAMING: {SAVING, COMPLETED, CANCELLED, FAILED},
    SAVING: {COMPLETED, CANCELLED, FAILED},
    COMPLETED: set(),
    FAILED: set(),
    CANCELLED: set(),
}


@dataclass(frozen=True)
class TaskTransition:
    old_status: str
    new_status: str


def can_transition(old_status: str, new_status: str) -> bool:
    """Return whether a status transition is valid."""
    if old_status == new_status:
        return True
    return new_status in ALLOWED_TRANSITIONS.get(old_status, set())


def require_transition(old_status: str, new_status: str) -> TaskTransition:
    """Validate and describe a task transition."""
    if not can_transition(old_status, new_status):
        raise ValueError(f"invalid task status transition: {old_status} -> {new_status}")
    return TaskTransition(old_status=old_status, new_status=new_status)

