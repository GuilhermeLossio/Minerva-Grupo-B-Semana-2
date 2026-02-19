"""Login page entrypoint."""

from __future__ import annotations

import json

import streamlit as st

from routes.routes import DEFAULT_ROUTE
from database.init_db import init_db
from services.auth_service import login as auth_login, require_auth
from ui.brand import get_logo_path
from ui.theme import apply_theme, init_theme_state
from utils.debug import log, time_block
from utils.rerun import safe_rerun


def _get_query_param(name: str) -> str:
    try:
        value = st.query_params.get(name)
    except Exception:
        value = st.experimental_get_query_params().get(name)
    if isinstance(value, list):
        return value[0] if value else ""
    return value or ""


def _clear_auth_state() -> None:
    for key in ("token", "user", "role", "logged_in", "user_info"):
        st.session_state.pop(key, None)
    st.session_state["authenticated"] = False


def _is_authenticated() -> bool:
    token = st.session_state.get("token")
    if not token:
        st.session_state["authenticated"] = False
        return False

    try:
        result = json.loads(require_auth(token))
    except Exception:
        st.session_state["authenticated"] = False
        return False

    authenticated = bool(result.get("success"))
    st.session_state["authenticated"] = authenticated
    if authenticated:
        st.session_state["logged_in"] = True
        st.session_state["user_info"] = result.get("user")
    return authenticated


def _set_query_param(name: str, value: str) -> None:
    try:
        if value:
            st.query_params[name] = value
        else:
            if name in st.query_params:
                del st.query_params[name]
    except Exception:
        params = st.experimental_get_query_params()
        if value:
            params[name] = value
        else:
            params.pop(name, None)
        st.experimental_set_query_params(**params)


def _redirect_to(page: str) -> None:
    _set_query_param("page", page)
    _set_query_param("next", "")
    safe_rerun()
    st.stop()


def _logout() -> None:
    _clear_auth_state()
    _set_query_param("next", "")
    _set_query_param("page", "login")
    safe_rerun()
    st.stop()


def _hide_sidebar() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _ensure_db_initialized() -> None:
    if st.session_state.get("db_initialized"):
        return
    with time_block("login: init_db"):
        init_db()
    st.session_state["db_initialized"] = True


def main(set_page_config: bool = True) -> None:
    if set_page_config:
        st.set_page_config(page_title="Login", layout="centered")
    _hide_sidebar()
    init_theme_state()
    apply_theme(st.session_state.get("dark_mode", True))
    _ensure_db_initialized()

    logo_path = get_logo_path()
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        if logo_path:
            st.image(str(logo_path), width=160)
        st.markdown("### Alea Lumen")
        st.caption("Acesso seguro a inteligencia corporativa.")

    if _is_authenticated():
        log("login: user already authenticated")
        st.success("Voce ja esta logado.")
        next_page = _get_query_param("next") or DEFAULT_ROUTE
        col_primary, col_secondary = st.columns([1, 1])
        with col_primary:
            if st.button("Ir para o app", type="primary"):
                _redirect_to(next_page)
        with col_secondary:
            if st.button("Logout", type="secondary"):
                _logout()
        return

    email = st.text_input("Email", placeholder="email@empresa.com")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar", type="primary"):
        if not email or not password:
            st.warning("Informe email e senha.")
            return

        try:
            with time_block("login: auth_login"):
                result = json.loads(auth_login(email, password))
        except Exception:
            st.error("Erro interno ao processar login.")
            return
        if not result.get("success"):
            log("login: invalid credentials")
            st.error(result.get("message", "Falha ao realizar login."))
            return

        st.session_state["token"] = result.get("token")
        st.session_state["user"] = result.get("user")
        st.session_state["role"] = result.get("role")
        st.session_state["authenticated"] = True
        st.session_state["logged_in"] = True
        st.session_state["user_info"] = result.get("user")

        log("login: success")
        next_page = _get_query_param("next") or DEFAULT_ROUTE
        _redirect_to(next_page)


if __name__ == "__main__":
    main()
