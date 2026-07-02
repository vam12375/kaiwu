"""Event API routes.

Currently task-scoped events are exposed at /api/tasks/{id}/events.
This module exists as the API boundary for future cross-task event queries.
"""

from __future__ import annotations

from fastapi import FastAPI


def register_event_routes(app: FastAPI):
    """Register event routes when global event APIs are introduced."""
    return app

