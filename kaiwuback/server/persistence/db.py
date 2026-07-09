"""SQLAlchemy Core database infrastructure.

The app still exposes get_db() for existing PyMySQL-style cursor callers,
while new database code can use the SQLAlchemy engine and transaction helper.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine, URL

from server.config import DB_CONFIG, DB_CONNECT_ARGS, DB_POOL_CONFIG

_engine: Engine | None = None
_engine_lock = threading.Lock()


def database_url() -> URL:
    return URL.create(
        "mysql+pymysql",
        username=str(DB_CONFIG.get("user") or ""),
        password=str(DB_CONFIG.get("password") or ""),
        host=str(DB_CONFIG.get("host") or "localhost"),
        port=int(DB_CONFIG.get("port") or 3306),
        database=str(DB_CONFIG.get("database") or "kaiwu"),
        query={"charset": str(DB_CONFIG.get("charset") or "utf8mb4")},
    )


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = create_engine(
                    database_url(),
                    pool_pre_ping=True,
                    pool_size=int(DB_POOL_CONFIG["pool_size"]),
                    max_overflow=int(DB_POOL_CONFIG["max_overflow"]),
                    pool_timeout=int(DB_POOL_CONFIG["pool_timeout"]),
                    pool_recycle=int(DB_POOL_CONFIG["pool_recycle"]),
                    connect_args=dict(DB_CONNECT_ARGS),
                    future=True,
                )
    return _engine


def get_db():
    """Return a pooled DB-API connection compatible with PyMySQL callers."""
    return get_engine().raw_connection()


@contextmanager
def transaction() -> Iterator[Connection]:
    """Run SQLAlchemy Core statements inside one committed transaction."""
    with get_engine().begin() as conn:
        yield conn


def dispose_engine() -> None:
    global _engine
    with _engine_lock:
        if _engine is not None:
            _engine.dispose()
            _engine = None
