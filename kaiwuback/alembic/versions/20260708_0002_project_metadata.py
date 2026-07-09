"""project metadata schema

Revision ID: 20260708_0002
Revises: 20260708_0001
Create Date: 2026-07-08

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "20260708_0002"
down_revision: Union[str, None] = "20260708_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS project_folder_metadata (
            folder_name VARCHAR(255) PRIMARY KEY,
            description TEXT NULL,
            hidden TINYINT(1) NOT NULL DEFAULT 0,
            display_name VARCHAR(255) NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_project_folder_metadata_hidden (hidden)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS project_file_metadata (
            folder_name VARCHAR(255) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            metadata LONGTEXT NOT NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (folder_name, filename),
            INDEX idx_project_file_metadata_folder (folder_name)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS project_image_metadata (
            filename VARCHAR(255) PRIMARY KEY,
            metadata LONGTEXT NOT NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
    )


def downgrade() -> None:
    # Project metadata migration is intentionally non-destructive. Runtime code
    # still understands sidecar files, so rollback should be handled manually
    # after exporting any needed table data.
    pass
