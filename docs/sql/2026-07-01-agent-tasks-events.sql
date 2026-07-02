-- Task-driven Agent Runtime persistence tables.
-- Apply before enabling /api/tasks in a production environment.

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
    CONSTRAINT fk_agent_events_task
        FOREIGN KEY (task_id) REFERENCES agent_tasks(id)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

