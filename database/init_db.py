from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.connection import get_connection
from services.auth_service import hash_password

DEFAULT_ADMIN_NAME = "Admin"
DEFAULT_ADMIN_EMAIL = "admin@local"
DEFAULT_ADMIN_PASSWORD = "Admin"
DEFAULT_ADMIN_SECTOR = "Admin"


def _create_tables(conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password TEXT NOT NULL,
            nivel INTEGER NOT NULL DEFAULT 1,
            setor TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id_admin INTEGER,
            user_id_target INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY(user_id_admin) REFERENCES users(id),
            FOREIGN KEY(user_id_target) REFERENCES users(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_user_audit_logs_created_at
        ON user_audit_logs(created_at DESC)
        """
    )
    conn.commit()


def _create_triggers(conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS trg_users_set_updated_at
        AFTER UPDATE ON users
        FOR EACH ROW
        BEGIN
            UPDATE users
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        """
    )
    conn.commit()


def _ensure_default_admin(conn) -> None:
    cursor = conn.cursor()
    admin_exists = cursor.execute(
        "SELECT 1 FROM users WHERE nivel = 0 LIMIT 1"
    ).fetchone()
    if admin_exists:
        return

    cursor.execute(
        """
        INSERT INTO users (usuario, email, password, nivel, setor)
        VALUES (?, ?, ?, 0, ?)
        """,
        (
            DEFAULT_ADMIN_NAME,
            DEFAULT_ADMIN_EMAIL,
            hash_password(DEFAULT_ADMIN_PASSWORD),
            DEFAULT_ADMIN_SECTOR,
        ),
    )
    conn.commit()


def init_db() -> None:
    """Initialize SQLite schema and ensure one default admin user exists."""
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to connect to the SQLite database.")

    try:
        _create_tables(conn)
        _create_triggers(conn)
        _ensure_default_admin(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
