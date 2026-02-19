"""Authentication guard for Streamlit pages."""

from __future__ import annotations

import json

import streamlit as st

from routes.routes import DEFAULT_ROUTE, ROUTES
from services.auth_service import require_auth
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


def _clear_auth_state() -> None:
    for key in ("token", "user", "role"):
        st.session_state.pop(key, None)
    st.session_state["authenticated"] = False


def _is_authenticated() -> bool:
    token = st.session_state.get("token")
    if not token:
        log("auth_guard: missing token")
        st.session_state["authenticated"] = False
        return False
    try:
        with time_block("auth_guard: require_auth"):
            result = json.loads(require_auth(token))
    except Exception as exc:
        log(f"auth_guard: require_auth error: {exc}")
        _clear_auth_state()
        return False
    if not result.get("success"):
        log("auth_guard: token invalid or expired")
        _clear_auth_state()
        return False
    st.session_state["user"] = result.get("user")
    st.session_state["role"] = result.get("user", {}).get("role")
    st.session_state["authenticated"] = True
    log("auth_guard: ok")
    return True


def _can_access_page(current_page: str) -> bool:
    route = ROUTES.get(current_page or "")
    if not route:
        return True

    required_roles = route.get("roles")
    if not required_roles:
        return True

    role = st.session_state.get("role")
    return role in set(required_roles)


def ensure_authenticated(current_page: str) -> bool:
    """Return True when authenticated; otherwise redirect to login and stop."""
    if _is_authenticated():
        if _can_access_page(current_page):
            return True
        log(f"auth_guard: access denied to page '{current_page}'")
        _set_query_param("next", "")
        _set_query_param("page", DEFAULT_ROUTE)
        safe_rerun()
        st.stop()

    log(f"auth_guard: redirect to login (from {current_page})")
    _set_query_param("next", current_page or DEFAULT_ROUTE)
    _set_query_param("page", "login")
    safe_rerun()
    st.stop()
