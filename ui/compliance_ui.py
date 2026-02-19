"""Audit UI for viewing users audit trail."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from database.connection import DB_PATH, get_connection
from database.init_db import init_db
from ui.theme import apply_theme, init_theme_state
from utils.debug import time_block

APP_TITLE = "Alea Lumen - Auditoria"


def _ensure_db_initialized() -> None:
    if st.session_state.get("db_initialized"):
        return
    with time_block("audit: init_db"):
        init_db()
    st.session_state["db_initialized"] = True


def _load_action_options() -> list[str]:
    conn = get_connection()
    if conn is None:
        return []
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT action
            FROM user_audit_logs
            WHERE action IS NOT NULL AND trim(action) <> ''
            ORDER BY action
            """
        ).fetchall()
        return [row["action"] for row in rows]
    except Exception:
        return []
    finally:
        conn.close()


def _load_audit_rows(limit: int, action_filter: str | None = None) -> pd.DataFrame:
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                a.id,
                a.action,
                a.user_id_admin,
                admin_user.usuario AS admin_usuario,
                admin_user.email AS admin_email,
                a.user_id_target,
                target_user.usuario AS alvo_usuario,
                target_user.email AS alvo_email,
                a.details,
                a.created_at
            FROM user_audit_logs a
            LEFT JOIN users admin_user ON admin_user.id = a.user_id_admin
            LEFT JOIN users target_user ON target_user.id = a.user_id_target
        """
        params: list[object] = []

        if action_filter and action_filter != "Todos":
            query += " WHERE a.action = ?"
            params.append(action_filter)

        query += " ORDER BY a.created_at DESC"
        if limit > 0:
            query += " LIMIT ?"
            params.append(limit)

        return pd.read_sql_query(query, conn, params=tuple(params))
    finally:
        conn.close()


def _format_details(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "details" not in df.columns:
        return df

    formatted = df.copy()

    def _pretty(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ""
            try:
                parsed = json.loads(stripped)
            except Exception:
                return stripped
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        return str(value)

    formatted["details"] = formatted["details"].map(_pretty)
    return formatted


def main(set_page_config: bool = True) -> None:
    _ensure_db_initialized()
    if set_page_config:
        st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_theme_state()
    apply_theme(st.session_state.get("dark_mode", True))

    role = st.session_state.get("role")
    if role not in {"ADMIN", "COMPLIANCE"}:
        st.error("Acesso restrito a administradores e compliance.")
        return

    st.title("Auditoria de Usuarios")
    st.caption(f"Banco local: {DB_PATH}")

    available_actions = _load_action_options()
    action_options = ["Todos", *available_actions]

    col_limit, col_action = st.columns([1, 2])
    with col_limit:
        limit = st.number_input(
            "Limite de registros",
            min_value=10,
            max_value=1000,
            value=200,
            step=10,
        )
    with col_action:
        action_filter = st.selectbox("Filtrar por acao", options=action_options)

    with time_block("audit: load"):
        df = _load_audit_rows(int(limit), action_filter)

    if df.empty:
        st.info("Nenhum evento de auditoria encontrado.")
        return

    df = _format_details(df)
    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
