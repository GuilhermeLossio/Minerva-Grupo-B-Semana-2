
"""Admin UI for running SQL queries against the local SQLite database."""

from __future__ import annotations

import os
import sqlite3
import time
from typing import List

import pandas as pd
import streamlit as st

from database.connection import DB_PATH, get_connection
from database.init_db import init_db
from ui.theme import apply_theme, init_theme_state
from utils.debug import log, time_block

APP_TITLE = "Alea Lumen - Admin SQL"
DB_TIMEOUT_SECONDS = 1.0
SQL_TIMEOUT_SECONDS = float(os.getenv("SQL_TIMEOUT_SECONDS", "5"))


def _strip_leading_comments(sql: str) -> str:
    text = sql.lstrip()
    while True:
        if text.startswith("--"):
            newline = text.find("\n")
            if newline == -1:
                return ""
            text = text[newline + 1 :].lstrip()
            continue
        if text.startswith("/*"):
            end = text.find("*/")
            if end == -1:
                return ""
            text = text[end + 2 :].lstrip()
            continue
        return text


def _first_keyword(sql: str) -> str:
    text = _strip_leading_comments(sql)
    if not text:
        return ""
    return text.split(None, 1)[0].lower()


def _split_statements(sql: str) -> List[str]:
    return [chunk.strip() for chunk in sql.split(";") if chunk.strip()]


def _is_query_statement(keyword: str) -> bool:
    return keyword in {"select", "with", "pragma", "explain"}


def _get_connection(readonly: bool) -> sqlite3.Connection:
    if readonly:
        db_uri = f"file:{DB_PATH.as_posix()}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True, timeout=DB_TIMEOUT_SECONDS)
    else:
        conn = get_connection()
        if conn is None:
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT_SECONDS)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 1000")
    return conn


def _run_sql(sql: str, readonly: bool) -> None:
    statements = _split_statements(sql)
    if not statements:
        st.error("Informe uma instrucao SQL.")
        return
    if len(statements) > 1:
        st.error("Use apenas uma instrucao por vez.")
        return

    statement = statements[0]
    keyword = _first_keyword(statement)
    if not keyword:
        st.error("SQL vazio ou apenas comentarios.")
        return

    if readonly and keyword not in {"select", "with", "pragma", "explain"}:
        st.error("Modo somente leitura. Use SELECT, WITH, PRAGMA ou EXPLAIN.")
        return

    conn = _get_connection(readonly)
    if SQL_TIMEOUT_SECONDS > 0:
        start_time = time.perf_counter()

        def _progress_handler() -> int:
            elapsed = time.perf_counter() - start_time
            if elapsed > SQL_TIMEOUT_SECONDS:
                return 1
            return 0

        conn.set_progress_handler(_progress_handler, 10000)
    try:
        with time_block("admin_sql: run_query"):
            if _is_query_statement(keyword):
                df = pd.read_sql_query(statement, conn)
                st.success(f"{len(df)} linha(s) retornada(s).")
                st.dataframe(df, use_container_width=True)
            else:
                cursor = conn.execute(statement)
                conn.commit()
                rows = cursor.rowcount
                if rows == -1:
                    st.success("Comando executado.")
                else:
                    st.success(f"Comando executado. Linhas afetadas: {rows}.")
    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc).lower():
            st.error(
                f"Consulta excedeu o tempo limite de {SQL_TIMEOUT_SECONDS:.0f}s."
            )
        else:
            st.error(f"Erro ao executar SQL: {exc}")
        log(f"admin_sql error: {exc}")
    except Exception as exc:
        st.error(f"Erro ao executar SQL: {exc}")
        log(f"admin_sql error: {exc}")
    finally:
        conn.set_progress_handler(None, 0)
        conn.close()


def _ensure_db_initialized() -> None:
    if st.session_state.get("db_initialized"):
        return
    with time_block("admin_sql: init_db"):
        init_db()
    st.session_state["db_initialized"] = True


def main(set_page_config: bool = True) -> None:
    _ensure_db_initialized()
    if set_page_config:
        st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_theme_state()
    apply_theme(st.session_state.get("dark_mode", True))
    role = st.session_state.get("role")
    if role != "ADMIN":
        st.error("Acesso restrito a administradores.")
        return
    st.title("Alea Lumen - Admin SQL")
    st.caption(f"Banco local: {DB_PATH}")

    st.warning("Use com cuidado. Este painel executa SQL direto no banco local.")

    allow_write = st.toggle("Permitir comandos de escrita", value=False)
    readonly = not allow_write

    default_sql = "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;"
    sql = st.text_area("SQL", value=default_sql, height=200)

    if st.button("Executar", type="primary"):
        _run_sql(sql, readonly=readonly)


if __name__ == "__main__":
    main()
