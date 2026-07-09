-- Core Kaiwu persistence schema.
-- Prefer applying this through Alembic from kaiwuback/:
--   python -m alembic upgrade head

CREATE TABLE IF NOT EXISTS conversations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    node_id VARCHAR(64) NOT NULL DEFAULT '',
    direction VARCHAR(255) NOT NULL DEFAULT '',
    message_count INT NOT NULL DEFAULT 0,
    md_file_path TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_conversations_updated (updated_at),
    INDEX idx_conversations_node_updated (node_id, updated_at)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT NOT NULL,
    role VARCHAR(32) NOT NULL,
    content LONGTEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_messages_conversation (conversation_id, id),
    INDEX idx_messages_conversation_created (conversation_id, created_at),
    CONSTRAINT fk_messages_conversation
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

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
    updated_at DATETIME NOT NULL,
    INDEX idx_agent_tasks_conversation (conversation_id),
    INDEX idx_agent_tasks_status (status),
    INDEX idx_agent_tasks_updated (updated_at),
    INDEX idx_agent_tasks_status_updated (status, updated_at),
    INDEX idx_agent_tasks_conv_updated (conversation_id, updated_at)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS agent_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    `type` VARCHAR(64) NOT NULL,
    payload LONGTEXT NOT NULL,
    seq INT NOT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY uniq_agent_events_task_seq (task_id, seq),
    INDEX idx_agent_events_task (task_id, seq),
    INDEX idx_agent_events_type_created (`type`, created_at),
    CONSTRAINT fk_agent_events_task
        FOREIGN KEY (task_id) REFERENCES agent_tasks(id)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
