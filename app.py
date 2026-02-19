from __future__ import annotations

import importlib

import streamlit as st

from ui.common import current_role, is_logged_in, render_session_sidebar, require_session
from ui.theme import apply_theme, init_theme_state

ROUTE_TO_LABEL = {
    "index": "App",
    "audit": "Auditoria",
    "users": "Cadastro de Usuarios",
    "admin": "SQL Admin",
}
LABEL_TO_ROUTE = {label: route for route, label in ROUTE_TO_LABEL.items()}


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
        elif name in st.query_params:
            del st.query_params[name]
    except Exception:
        params = st.experimental_get_query_params()
        if value:
            params[name] = value
        else:
            params.pop(name, None)
        st.experimental_set_query_params(**params)


def _resolve_initial_page(options: list[str]) -> str:
    requested_route = _get_query_param("page")
    requested_label = ROUTE_TO_LABEL.get(requested_route, requested_route)
    if requested_label in options:
        return requested_label
    return "App"


def _hide_default_page_navigation() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="stSidebarNavSeparator"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Alea Lumen", page_icon="🦁", layout="wide")
    init_theme_state()
    apply_theme()
    _hide_default_page_navigation()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not is_logged_in():
        public_page = _get_query_param("page")
        if public_page == "signup":
            signup_ui = importlib.import_module("ui.signup_ui")
            signup_ui.main(set_page_config=False)
        else:
            _set_query_param("page", "login")
            login_page = importlib.import_module("ui.login_page")
            login_page.render()
        return

    if not require_session():
        return

    render_session_sidebar()
    role = current_role()

    st.sidebar.markdown("### Navegacao")
    options = ["App"]
    if role == "ADMIN":
        options.append("Auditoria")
    if role == "ADMIN":
        options.append("Cadastro de Usuarios")
        options.append("SQL Admin")

    initial_page = _resolve_initial_page(options)
    page_label = st.sidebar.radio("Ir para", options, index=options.index(initial_page))

    route_key = LABEL_TO_ROUTE.get(page_label, "index")
    _set_query_param("page", route_key)

    if route_key == "admin":
        admin_ui = importlib.import_module("ui.admin_ui")
        admin_ui.main(set_page_config=False)
    elif route_key == "users":
        user_registration_ui = importlib.import_module("ui.user_registration_ui")
        user_registration_ui.main(set_page_config=False)
    elif route_key == "audit":
        compliance_ui = importlib.import_module("ui.compliance_ui")
        compliance_ui.main(set_page_config=False)
    else:
        chat_ui = importlib.import_module("ui.chat_ui")
        chat_ui.main(set_page_config=False)


if __name__ == "__main__":
    main()
