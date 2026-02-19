import importlib
import streamlit as st
from ui.common import is_logged_in, require_session, render_session_sidebar, current_role
from ui.theme import apply_theme, init_theme_state

# Keep startup light: defer heavy vector DB / embedding initialization
# to the actual app pages (chat/admin) so the login screen opens quickly.


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if not is_logged_in():
    login_page = importlib.import_module("ui.login_page")
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
            options.append("Cadastro de Usuarios")
            options.append("SQL Admin")
        page = st.sidebar.radio("Ir para", options)
        if page == "SQL Admin":
            admin_ui = importlib.import_module("ui.admin_ui")
            admin_ui.main(set_page_config=False)
        elif page == "Cadastro de Usuarios":
            user_registration_ui = importlib.import_module("ui.user_registration_ui")
            user_registration_ui.main(set_page_config=False)
        elif page == "Auditoria":
            compliance_ui = importlib.import_module("ui.compliance_ui")
            compliance_ui.main(set_page_config=False)
        else:
            chat_ui = importlib.import_module("ui.chat_ui")
            chat_ui.main(set_page_config=False)
