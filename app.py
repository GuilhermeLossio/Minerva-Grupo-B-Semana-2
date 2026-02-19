import streamlit as st
from ui.common import is_logged_in, require_session, render_session_sidebar, current_role
from ui import admin_ui, compliance_ui, chat_ui, login_page
from ui.theme import apply_theme, init_theme_state


st.set_page_config(page_title="Alea Lumen", page_icon="🦁", layout="wide")
init_theme_state()
apply_theme(st.session_state.get("dark_mode", True))


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if not is_logged_in():
    login_page.render()
else:
    if require_session():
        render_session_sidebar()
        role = current_role()
        st.sidebar.markdown("### Navegação")
        options = ["App"]
        if role in {"ADMIN", "COMPLIANCE"}:
            options.append("Auditoria")
        if role == "ADMIN":
            options.append("SQL Admin")
        page = st.sidebar.radio("Ir para", options)
        if page == "SQL Admin":
            admin_ui.main(set_page_config=False)
        elif page == "Auditoria":
            compliance_ui.main(set_page_config=False)
        else:
            chat_ui.main(set_page_config=False)
