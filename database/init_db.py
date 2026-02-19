from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.connection import get_connection
from services.auth_service import hash_password

def init_db() -> None:
    """Initialize the SQLite schema and default admin user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nivel INTEGER DEFAULT 1,
                setor TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
            )
            """
        )
        conn.commit()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id_admin INTEGER,
                user_id_target INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
            )
            """
        )
        conn.commit()

    with get_connection() as conn:
        cursor = conn.cursor()
        admin_exists = cursor.execute(
            "SELECT 1 FROM users WHERE nivel = 0"
        ).fetchone()

        if not admin_exists:
            cursor.execute(
                """
                INSERT INTO users (usuario, email, password, nivel, setor)
                VALUES ('Admin', 'Admin', ?, 0, 'Admin')
                """,
                (hash_password("Admin"),),
            )
            conn.commit()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_users_set_updated_at
            AFTER UPDATE ON users
            FOR EACH ROW
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
            """
        )
        conn.commit()


if __name__ == "__main__":
    init_db()
