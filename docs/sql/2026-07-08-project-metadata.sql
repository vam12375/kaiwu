-- Project library metadata schema.
-- Prefer applying this through Alembic from kaiwuback/:
--   python -m alembic upgrade head
-- Legacy JSON sidecars are backfilled by runtime metadata access when these
-- tables are empty; this file only defines the schema.

CREATE TABLE IF NOT EXISTS project_folder_metadata (
    folder_name VARCHAR(255) PRIMARY KEY,
    description TEXT NULL,
    hidden TINYINT(1) NOT NULL DEFAULT 0,
    display_name VARCHAR(255) NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_project_folder_metadata_hidden (hidden)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS project_file_metadata (
    folder_name VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    metadata LONGTEXT NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (folder_name, filename),
    INDEX idx_project_file_metadata_folder (folder_name)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS project_image_metadata (
    filename VARCHAR(255) PRIMARY KEY,
    metadata LONGTEXT NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
