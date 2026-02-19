import json

import streamlit as st

from services.auth_service import require_auth
from ui.brand import get_logo_path

ROLE_LABEL = {"ADMIN": "Administrador", "NORMAL": "Usuario", "COMPLIANCE": "Compliance"}
NIVEL_LABEL = {0: "ADMIN", 1: "NORMAL", 2: "COMPLIANCE"}


def parse(resp: str) -> dict:
    try:
        return json.loads(resp) if isinstance(resp, str) else {"success": False, "message": "Resposta invalida"}
    except Exception:
        return {"success": False, "message": "JSON invalido", "raw": str(resp)[:500]}


def logout():
    st.session_state.clear()
    st.rerun()


def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in")) and bool(st.session_state.get("token"))


def current_role() -> str:
    return (st.session_state.get("user_info") or {}).get("role", "NORMAL")


def _format_display_name(user: dict) -> str:
    """Avoid showing email in the username field."""
    usuario = str(user.get("usuario", "") or "").strip()
    email = str(user.get("email", "") or "").strip()

    if usuario and "@" not in usuario:
        return usuario

    if usuario and email and usuario.lower() != email.lower():
        return usuario

    if email:
        local_part = email.split("@", 1)[0]
        cleaned = local_part.replace(".", " ").replace("_", " ").replace("-", " ")
        cleaned = " ".join(cleaned.split()).strip()
        return cleaned.title() if cleaned else email

    return usuario or "-"


def require_session() -> bool:
    """Se token expirou/invalido: derruba sessao."""
    if not is_logged_in():
        return False

    token = st.session_state["token"]
    auth = parse(require_auth(token))
    if not auth.get("success"):
        st.warning("Sessao expirada ou invalida. Faca login novamente.")
        st.session_state.clear()
        st.rerun()

    st.session_state["user_info"] = auth.get("user", st.session_state.get("user_info", {}))
    return True


def render_session_sidebar():
    """Render user session info and logout button in sidebar."""
    user = st.session_state.get("user_info", {})
    role = user.get("role", "NORMAL")
    display_name = _format_display_name(user)

    logo_path = get_logo_path()
    if logo_path:
        st.sidebar.image(str(logo_path), width=120)
        st.sidebar.divider()

    st.sidebar.markdown("### Sessao")
    st.sidebar.write(f"**Usuario:** {display_name}")
    st.sidebar.write(f"**Email:** {user.get('email', '-')}")
    st.sidebar.write(f"**Perfil:** {ROLE_LABEL.get(role, role)}")
    st.sidebar.divider()

    col1, col2 = st.sidebar.columns([1, 1])
    if col1.button("Logout", type="secondary", use_container_width=True):
        logout()
    if col2.button("Preferencias", type="secondary", use_container_width=True):
        st.info("Preferencias em breve!")


def guard_role(required: str):
    """Protege UI: se nao for o role exigido, barra a pagina."""
    if current_role() != required:
        st.error(f"Acesso negado. Requer perfil: {required}")
        st.stop()
