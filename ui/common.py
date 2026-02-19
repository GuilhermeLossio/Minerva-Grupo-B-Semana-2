import json
import streamlit as st
from services.auth_service import require_auth
from ui.brand import get_logo_path
from ui.theme import init_theme_state

ROLE_LABEL = {"ADMIN": "Administrador", "NORMAL": "Usuário", "COMPLIANCE": "Compliance"}
NIVEL_LABEL = {0: "ADMIN", 1: "NORMAL", 2: "COMPLIANCE"}

def parse(resp: str) -> dict:
    try:
        return json.loads(resp) if isinstance(resp, str) else {"success": False, "message": "Resposta inválida"}
    except Exception:
        return {"success": False, "message": "JSON inválido", "raw": str(resp)[:500]}

def logout():
    st.session_state.clear()
    st.rerun()

def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in")) and bool(st.session_state.get("token"))

def current_role() -> str:
    return (st.session_state.get("user_info") or {}).get("role", "NORMAL")

def require_session() -> bool:
    """Se token expirou/inválido: derruba sessão."""
    if not is_logged_in():
        return False

    token = st.session_state["token"]
    auth = parse(require_auth(token))
    if not auth.get("success"):
        st.warning("Sessão expirada ou inválida. Faça login novamente.")
        st.session_state.clear()
        st.rerun()

    # mantém user_info sincronizado com payload do token
    st.session_state["user_info"] = auth.get("user", st.session_state.get("user_info", {}))
    return True

def render_session_sidebar():
    user = st.session_state.get("user_info", {})
    role = user.get("role", "NORMAL")

    logo_path = get_logo_path()
    if logo_path:
        st.sidebar.image(str(logo_path), width=120)
        st.sidebar.divider()

    st.sidebar.markdown("### Sessao")
    st.sidebar.write(f"Usuario: {user.get('usuario','-')}")
    st.sidebar.write(f"Email: {user.get('email','-')}")
    st.sidebar.write(f"Perfil: {ROLE_LABEL.get(role, role)}")
    st.sidebar.divider()

    init_theme_state()
    st.sidebar.toggle("Modo escuro", key="dark_mode")
    st.sidebar.divider()

    if st.sidebar.button("Logout"):
        logout()


def guard_role(required: str):
    """Protege UI: se não for o role exigido, barra a página."""
    if current_role() != required:
        st.error(f"Acesso negado. Requer perfil: {required}")
        st.stop()
