"""Admin UI for registering low-access users."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from database.init_db import init_db
from services.auth_service import (
    LOW_ACCESS_LEVEL,
    ROLE_MAP,
    alterar_nivel_acesso,
    criar_usuario,
    listar_usuarios,
)
from ui.theme import apply_theme, init_theme_state
from utils.debug import time_block

APP_TITLE = "Alea Lumen - Cadastro de Usuarios"


def _ensure_db_initialized() -> None:
    if st.session_state.get("db_initialized"):
        return
    with time_block("user_registration: init_db"):
        init_db()
    st.session_state["db_initialized"] = True


def _parse_response(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        return {"success": False, "message": "Resposta invalida do servico"}


def _require_admin() -> bool:
    if st.session_state.get("role") != "ADMIN":
        st.error("Acesso restrito a administradores.")
        return False
    if not st.session_state.get("token"):
        st.error("Sessao invalida. Faca login novamente.")
        return False
    return True


def _render_registration_form(token: str) -> None:
    st.subheader("Novo usuario de baixo acesso")
    st.caption("Este formulario cria apenas usuarios com perfil NORMAL.")
    with st.form("low_access_registration_form", clear_on_submit=True):
        usuario = st.text_input("Nome do usuario", max_chars=60)
        email = st.text_input("Email corporativo", max_chars=120, placeholder="nome@empresa.com")
        setor = st.text_input("Setor", max_chars=80)
        password = st.text_input("Senha", type="password")
        confirm_password = st.text_input("Confirmar senha", type="password")
        submitted = st.form_submit_button("Cadastrar usuario", type="primary")

    if not submitted:
        return
    if password != confirm_password:
        st.error("As senhas nao conferem.")
        return
    if not usuario.strip() or not email.strip() or not setor.strip():
        st.error("Preencha usuario, email e setor.")
        return

    response = _parse_response(
        criar_usuario(
            token=token,
            usuario=usuario.strip(),
            email=email.strip(),
            password=password,
            nivel=LOW_ACCESS_LEVEL,
            setor=setor.strip(),
        )
    )
    if response.get("success"):
        st.success("Usuario de baixo acesso criado com sucesso.")
    else:
        st.error(response.get("message", "Nao foi possivel criar o usuario."))


def _load_low_access_users(token: str) -> pd.DataFrame:
    response = _parse_response(listar_usuarios(token))
    if not response.get("success"):
        st.error(response.get("message", "Falha ao listar usuarios."))
        return pd.DataFrame()

    rows = response.get("data", [])
    low_access_rows = [row for row in rows if row.get("nivel") == LOW_ACCESS_LEVEL]
    if not low_access_rows:
        return pd.DataFrame()

    df = pd.DataFrame(low_access_rows)
    df["perfil"] = df["nivel"].map(lambda nivel: ROLE_MAP.get(nivel, "NORMAL"))
    cols = ["id", "usuario", "email", "setor", "perfil", "created_at", "updated_at"]
    keep_cols = [col for col in cols if col in df.columns]
    return df[keep_cols].sort_values(by="id", ascending=False)


def _render_access_level_editor(token: str) -> None:
    st.subheader("Alterar nivel de acesso")
    st.caption("Somente administradores podem alterar nivel de acesso de usuarios.")

    response = _parse_response(listar_usuarios(token))
    if not response.get("success"):
        st.error(response.get("message", "Falha ao listar usuarios."))
        return

    rows = response.get("data", [])
    if not rows:
        st.info("Nenhum usuario encontrado para alteracao de nivel.")
        return

    level_options = [1, 2, 0]
    level_labels = {
        0: "ADMIN",
        1: "NORMAL (Baixo)",
        2: "COMPLIANCE",
    }
    user_options = sorted(rows, key=lambda user: user.get("id", 0))
    user_ids = [user["id"] for user in user_options]
    user_labels = {
        user["id"]: (
            f"#{user['id']} - {user.get('usuario', '-')}"
            f" ({user.get('email', '-')}) [{ROLE_MAP.get(user.get('nivel'), 'NORMAL')}]"
        )
        for user in user_options
    }

    with st.form("change_user_access_level_form"):
        target_user_id = st.selectbox(
            "Usuario alvo",
            options=user_ids,
            format_func=lambda user_id: user_labels.get(user_id, str(user_id)),
        )
        novo_nivel = st.selectbox(
            "Novo nivel de acesso",
            options=level_options,
            format_func=lambda nivel: level_labels[nivel],
        )
        submitted = st.form_submit_button("Atualizar nivel", type="secondary")

    if not submitted:
        return

    result = _parse_response(alterar_nivel_acesso(token, int(target_user_id), int(novo_nivel)))
    if result.get("success"):
        st.success(result.get("message", "Nivel de acesso atualizado."))
        st.rerun()
    else:
        st.error(result.get("message", "Nao foi possivel atualizar o nivel de acesso."))


def main(set_page_config: bool = True) -> None:
    _ensure_db_initialized()
    if set_page_config:
        st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_theme_state()
    apply_theme()

    if not _require_admin():
        return

    token = st.session_state["token"]

    st.title("Cadastro de Usuarios")
    st.caption("Crie usuarios com acesso baixo e gerencie niveis com permissao de administrador.")
    _render_registration_form(token)
    st.divider()
    _render_access_level_editor(token)

    st.divider()
    st.subheader("Usuarios de baixo acesso cadastrados")
    df = _load_low_access_users(token)
    if df.empty:
        st.info("Nenhum usuario de baixo acesso cadastrado.")
        return
    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
