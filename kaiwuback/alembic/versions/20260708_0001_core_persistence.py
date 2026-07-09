"""core persistence schema

Revision ID: 20260708_0001
Revises:
Create Date: 2026-07-08

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.mysql import LONGTEXT

revision: str = "20260708_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in set(_inspector().get_table_names())


def _column_names(table: str) -> set[str]:
    return {column["name"] for column in _inspector().get_columns(table)}


def _index_names(table: str) -> set[str]:
    inspector = _inspector()
    names = {index["name"] for index in inspector.get_indexes(table)}
    names.update(constraint["name"] for constraint in inspector.get_unique_constraints(table))
    return names


def _foreign_key_names(table: str) -> set[str]:
    return {fk["name"] for fk in _inspector().get_foreign_keys(table)}


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    if column.name not in _column_names(table):
        op.add_column(table, column)


def _create_index_if_missing(table: str, name: str, columns: list[str], unique: bool = False) -> None:
    if name not in _index_names(table):
        op.create_index(name, table, columns, unique=unique)


def _create_fk_if_missing(
    table: str,
    name: str,
    referent_table: str,
    local_cols: list[str],
    remote_cols: list[str],
    ondelete: str | None = None,
) -> None:
    if name not in _foreign_key_names(table):
        op.create_foreign_key(name, table, referent_table, local_cols, remote_cols, ondelete=ondelete)


def _create_base_tables() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            node_id VARCHAR(64) NOT NULL DEFAULT '',
            direction VARCHAR(255) NOT NULL DEFAULT '',
            message_count INT NOT NULL DEFAULT 0,
            md_file_path TEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            conversation_id BIGINT NOT NULL,
            role VARCHAR(32) NOT NULL,
            content LONGTEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id VARCHAR(36) PRIMARY KEY,
            conversation_id BIGINT NULL,
            status VARCHAR(32) NOT NULL,
            node_id VARCHAR(32) NULL,
            input LONGTEXT NOT NULL,
            result LONGTEXT NULL,
            error TEXT NULL,
            event_seq INT NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_events (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            task_id VARCHAR(36) NOT NULL,
            `type` VARCHAR(64) NOT NULL,
            payload LONGTEXT NOT NULL,
            seq INT NOT NULL,
            created_at DATETIME NOT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
    )


def _ensure_conversations() -> None:
    _add_column_if_missing("conversations", sa.Column("title", sa.String(length=255), nullable=False, server_default=""))
    _add_column_if_missing("conversations", sa.Column("node_id", sa.String(length=64), nullable=False, server_default=""))
    _add_column_if_missing("conversations", sa.Column("direction", sa.String(length=255), nullable=False, server_default=""))
    _add_column_if_missing("conversations", sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"))
    _add_column_if_missing("conversations", sa.Column("md_file_path", sa.Text(), nullable=True))
    _add_column_if_missing(
        "conversations",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    _add_column_if_missing(
        "conversations",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ),
    )
    _create_index_if_missing("conversations", "idx_conversations_updated", ["updated_at"])
    _create_index_if_missing("conversations", "idx_conversations_node_updated", ["node_id", "updated_at"])


def _ensure_messages() -> None:
    _add_column_if_missing("messages", sa.Column("conversation_id", sa.BigInteger(), nullable=False))
    _add_column_if_missing("messages", sa.Column("role", sa.String(length=32), nullable=False, server_default=""))
    _add_column_if_missing("messages", sa.Column("content", LONGTEXT(), nullable=False))
    _add_column_if_missing("messages", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    _create_index_if_missing("messages", "idx_messages_conversation", ["conversation_id", "id"])
    _create_index_if_missing("messages", "idx_messages_conversation_created", ["conversation_id", "created_at"])
    _create_fk_if_missing(
        "messages",
        "fk_messages_conversation",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )


def _ensure_agent_tasks() -> None:
    _add_column_if_missing("agent_tasks", sa.Column("conversation_id", sa.BigInteger(), nullable=True))
    _add_column_if_missing("agent_tasks", sa.Column("status", sa.String(length=32), nullable=False, server_default="created"))
    _add_column_if_missing("agent_tasks", sa.Column("node_id", sa.String(length=32), nullable=True))
    _add_column_if_missing("agent_tasks", sa.Column("input", LONGTEXT(), nullable=False))
    _add_column_if_missing("agent_tasks", sa.Column("result", LONGTEXT(), nullable=True))
    _add_column_if_missing("agent_tasks", sa.Column("error", sa.Text(), nullable=True))
    _add_column_if_missing("agent_tasks", sa.Column("event_seq", sa.Integer(), nullable=False, server_default="0"))
    _add_column_if_missing("agent_tasks", sa.Column("created_at", sa.DateTime(), nullable=False))
    _add_column_if_missing("agent_tasks", sa.Column("updated_at", sa.DateTime(), nullable=False))
    _create_index_if_missing("agent_tasks", "idx_agent_tasks_conversation", ["conversation_id"])
    _create_index_if_missing("agent_tasks", "idx_agent_tasks_status", ["status"])
    _create_index_if_missing("agent_tasks", "idx_agent_tasks_updated", ["updated_at"])
    _create_index_if_missing("agent_tasks", "idx_agent_tasks_status_updated", ["status", "updated_at"])
    _create_index_if_missing("agent_tasks", "idx_agent_tasks_conv_updated", ["conversation_id", "updated_at"])


def _ensure_agent_events() -> None:
    _add_column_if_missing("agent_events", sa.Column("task_id", sa.String(length=36), nullable=False))
    _add_column_if_missing("agent_events", sa.Column("type", sa.String(length=64), nullable=False, server_default=""))
    _add_column_if_missing("agent_events", sa.Column("payload", LONGTEXT(), nullable=False))
    _add_column_if_missing("agent_events", sa.Column("seq", sa.Integer(), nullable=False))
    _add_column_if_missing("agent_events", sa.Column("created_at", sa.DateTime(), nullable=False))
    _create_index_if_missing("agent_events", "uniq_agent_events_task_seq", ["task_id", "seq"], unique=True)
    _create_index_if_missing("agent_events", "idx_agent_events_task", ["task_id", "seq"])
    _create_index_if_missing("agent_events", "idx_agent_events_type_created", ["type", "created_at"])
    _create_fk_if_missing(
        "agent_events",
        "fk_agent_events_task",
        "agent_tasks",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )


def upgrade() -> None:
    _create_base_tables()
    _ensure_conversations()
    _ensure_messages()
    _ensure_agent_tasks()
    _ensure_agent_events()


def downgrade() -> None:
    # Baseline migration is intentionally non-destructive because existing
    # deployments may already have production data before Alembic adoption.
    pass
