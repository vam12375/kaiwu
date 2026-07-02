"""数据库持久化层 —— 对话CRUD + MD文件写入"""
import os
from pathlib import Path
from datetime import datetime
import pymysql

from server.config import DB_CONFIG, MD_STORE


def get_db():
    return pymysql.connect(**DB_CONFIG)


def _safe_filename(title: str) -> str:
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in title)
    return safe[:60]


def _write_md_file(path: Path, title: str, node_id: str, messages: list):
    """写入 .md 对话文件"""
    lines = [
        f"# {title}",
        f"",
        f"- **节点**: {node_id}",
        f"- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **消息数**: {len(messages)}",
        f"",
        "---",
        "",
    ]
    for msg in messages:
        role_label = "👤 用户" if msg["role"] == "user" else "🤖 开物AI"
        lines.append(f"### {role_label}")
        lines.append(f"")
        lines.append(msg["content"])
        lines.append(f"")
        lines.append("---")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def save_conversation(title: str, node_id: str, direction: str, messages: list) -> int:
    """保存对话到 MySQL，同时写入 .md 文件，返回 conversation_id"""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (title, node_id, direction, message_count) VALUES (%s, %s, %s, %s)",
                (title, node_id, direction, len(messages)),
            )
            conv_id = cur.lastrowid

            for msg in messages:
                cur.execute(
                    "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
                    (conv_id, msg["role"], msg["content"]),
                )
            db.commit()

        md_path = MD_STORE / f"{conv_id}_{_safe_filename(title)}.md"
        _write_md_file(md_path, title, node_id, messages)

        with db.cursor() as cur:
            cur.execute("UPDATE conversations SET md_file_path = %s WHERE id = %s", (str(md_path), conv_id))
            db.commit()

        return conv_id
    finally:
        db.close()


def append_conversation_messages(conv_id: int, new_messages: list):
    """追加新消息到已有对话（不删除旧消息）"""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(message_count), 0) FROM conversations WHERE id = %s", (conv_id,))
            existing_count = cur.fetchone()[0] or 0
            for msg in new_messages:
                cur.execute(
                    "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
                    (conv_id, msg["role"], msg["content"]),
                )
            cur.execute(
                "UPDATE conversations SET message_count = %s, updated_at = NOW() WHERE id = %s",
                (existing_count + len(new_messages), conv_id),
            )
            db.commit()
    finally:
        db.close()


def update_conversation_messages(conv_id: int, messages: list):
    """更新已有对话的消息（完全替换）"""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM messages WHERE conversation_id = %s", (conv_id,))
            for msg in messages:
                cur.execute(
                    "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
                    (conv_id, msg["role"], msg["content"]),
                )
            cur.execute(
                "UPDATE conversations SET message_count = %s, updated_at = NOW() WHERE id = %s",
                (len(messages), conv_id),
            )
            db.commit()

        cur = db.cursor()
        cur.execute("SELECT title, node_id FROM conversations WHERE id = %s", (conv_id,))
        row = cur.fetchone()
        if row:
            md_path = MD_STORE / f"{conv_id}_{_safe_filename(row[0])}.md"
            _write_md_file(md_path, row[0], row[1], messages)
    finally:
        db.close()


def list_conversations() -> list:
    """列出所有对话历史"""
    db = get_db()
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                "SELECT id, title, node_id, direction, message_count, created_at, updated_at, md_file_path FROM conversations ORDER BY updated_at DESC LIMIT 50"
            )
            return cur.fetchall()
    finally:
        db.close()


def load_conversation(conv_id: int) -> dict | None:
    """加载指定对话的完整内容"""
    db = get_db()
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT * FROM conversations WHERE id = %s", (conv_id,))
            conv = cur.fetchone()
            if not conv:
                return None
            cur.execute(
                "SELECT role, content, created_at FROM messages WHERE conversation_id = %s ORDER BY id ASC",
                (conv_id,),
            )
            conv["messages"] = cur.fetchall()
            return conv
    finally:
        db.close()


def delete_conversation(conv_id: int):
    """删除对话"""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT md_file_path FROM conversations WHERE id = %s", (conv_id,))
            row = cur.fetchone()
            if row and row[0] and Path(row[0]).exists():
                Path(row[0]).unlink()
            cur.execute("DELETE FROM conversations WHERE id = %s", (conv_id,))
            db.commit()
    finally:
        db.close()
