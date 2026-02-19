"""Public sign-up page for low-priority user creation."""

from __future__ import annotations

import json

import streamlit as st

from database.init_db import init_db
from services.auth_service import cadastro_publico_usuario
from ui.brand import get_logo_path
from ui.theme import apply_theme, init_theme_state
from utils.debug import time_block
from utils.rerun import safe_rerun

LOGIN_ROUTE = "login"


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


def _parse_response(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        return {"success": False, "message": "Resposta invalida do servico"}


def _redirect_to_login() -> None:
    _set_query_param("page", LOGIN_ROUTE)
    _set_query_param("next", "")
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


def _apply_auth_card_styles() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stForm"] {
            background: #d9d9d9 !important;
            border: 1px solid #d7dbe3 !important;
            border-radius: 0 !important;
            padding: 1rem !important;
            box-shadow: none !important;
        }

        div[data-testid="stForm"] div[data-testid="stTextInput"] input,
        div[data-testid="stForm"] div[data-testid="stPasswordInput"] input {
            color: #ffffff !important;
            background-color: #2f3745 !important;
            border: 1px solid #6a7486 !important;
            caret-color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        div[data-testid="stForm"] div[data-testid="stTextInput"] input::placeholder,
        div[data-testid="stForm"] div[data-testid="stPasswordInput"] input::placeholder {
            color: #ffffff !important;
            opacity: 0.85 !important;
        }

        div[data-testid="stForm"] div[data-testid="stTextInput"] input:-webkit-autofill,
        div[data-testid="stForm"] div[data-testid="stPasswordInput"] input:-webkit-autofill {
            -webkit-text-fill-color: #ffffff !important;
            -webkit-box-shadow: 0 0 0 1000px #2f3745 inset !important;
            transition: background-color 9999s ease-in-out 0s !important;
        }

        div[data-testid="stForm"] div[data-testid="stTextInput"] input:focus,
        div[data-testid="stForm"] div[data-testid="stPasswordInput"] input:focus {
            color: #000000 !important;
            background-color: #c6ccd7 !important;
            border: 1px solid #939dad !important;
            caret-color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }

        div[data-testid="stForm"] div[data-testid="stTextInput"] input:-webkit-autofill:focus,
        div[data-testid="stForm"] div[data-testid="stPasswordInput"] input:-webkit-autofill:focus {
            -webkit-text-fill-color: #000000 !important;
            -webkit-box-shadow: 0 0 0 1000px #c6ccd7 inset !important;
        }

        div[data-testid="stForm"] button[kind="primary"] {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _ensure_db_initialized() -> None:
    if st.session_state.get("db_initialized"):
        return
    with time_block("signup: init_db"):
        init_db()
    st.session_state["db_initialized"] = True


def main(set_page_config: bool = True) -> None:
    if set_page_config:
        st.set_page_config(page_title="Criar Conta", layout="centered")
    _hide_sidebar()
    _apply_auth_card_styles()
    init_theme_state()
    apply_theme()
    _ensure_db_initialized()

    logo_path = get_logo_path()
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        if logo_path:
            st.image(str(logo_path), width=160)
        st.markdown(
            '<h3 style="color:#000000; margin-bottom:0.2rem; '
            'font-family:\'Trebuchet MS\', \'Segoe UI\', \'Gill Sans\', sans-serif; '
            'font-weight:700; letter-spacing:0.02em;">Criar Conta</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#000000; margin-top:0; '
            'font-family:\'Trebuchet MS\', \'Segoe UI\', \'Gill Sans\', sans-serif;">'
            'Cadastro com acesso inicial.</p>',
            unsafe_allow_html=True,
        )

    _, card_col, _ = st.columns([3, 4, 3])
    with card_col:
        with st.form("public_signup_screen_form", clear_on_submit=True):
            usuario = st.text_input("Nome completo", max_chars=60)
            email = st.text_input("Email", max_chars=120, placeholder="email@empresa.com")
            setor = st.text_input("Setor", max_chars=80)
            password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirmar senha", type="password")
            submitted = st.form_submit_button("Criar conta", type="primary")

        if submitted:
            if not usuario.strip() or not email.strip() or not setor.strip():
                st.warning("Preencha nome, email e setor.")
            elif password != confirm_password:
                st.warning("As senhas nao conferem.")
            else:
                result = _parse_response(
                    cadastro_publico_usuario(
                        usuario=usuario.strip(),
                        email=email.strip(),
                        password=password,
                        setor=setor.strip(),
                    )
                )
                if result.get("success"):
                    st.success(result.get("message", "Conta criada com sucesso."))
                    if st.button("Ir para login", type="secondary"):
                        _redirect_to_login()
                else:
                    st.error(result.get("message", "Falha ao criar conta."))

        if st.button("Voltar para login", type="secondary"):
            _redirect_to_login()


if __name__ == "__main__":
    main()
