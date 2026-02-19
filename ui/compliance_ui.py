
"""Audit UI for viewing users data."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from database.connection import DB_PATH, get_connection
from database.init_db import init_db
from ui.theme import apply_theme, init_theme_state
from utils.debug import log, time_block

APP_TITLE = "Alea Lumen - Auditoria"


def _ensure_db_initialized() -> None:
    if st.session_state.get("audit_db_initialized"):
        return
    with time_block("audit: init_db"):
        init_db()
    st.session_state["audit_db_initialized"] = True


def _get_user_columns(conn) -> list[str]:
    rows = conn.execute("PRAGMA table_info(users)").fetchall()
    return [row[1] for row in rows]


def _load_audit_rows(limit: int) -> pd.DataFrame:
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    available = _get_user_columns(conn)
    desired = ["id", "usuario", "email", "setor", "nivel", "created_at", "updated_at"]
    columns = [col for col in desired if col in available]
    if not columns:
        return pd.DataFrame()

    order_by = "created_at" if "created_at" in available else "id"
    query = (
        f"SELECT {', '.join(columns)} "
        f"FROM users ORDER BY {order_by} DESC"
    )
    params = None
    if limit > 0:
        query += " LIMIT ?"
        params = (limit,)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def _format_details(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "details" not in df.columns:
        return df
    df = df.copy()

    def _pretty(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ""
            try:
                parsed = json.loads(value)
            except Exception:
                return value
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        return str(value)

    df["details"] = df["details"].map(_pretty)
    return df


def main(set_page_config: bool = True) -> None:
    _ensure_db_initialized()
    if set_page_config:
        st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_theme_state()
    apply_theme(st.session_state.get("dark_mode", True))

    st.title("Auditoria de Usuários")
    st.caption(f"Banco local: {DB_PATH}")

    limit = st.number_input(
        "Limite de registros",
        min_value=10,
        max_value=1000,
        value=200,
        step=10,
    )

    with time_block("audit: load"):
        df = _load_audit_rows(int(limit))

    if df.empty:
        st.info("Nenhum registro encontrado em users.")
        return

    df = _format_details(df)
    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
