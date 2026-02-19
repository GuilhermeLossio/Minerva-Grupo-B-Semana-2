"""UI do chat do Alea Lumen.

Responsabilidades principais:
- Gerenciar estado de sessao e preferencias do usuario.
- Aplicar o tema via CSS (gerado em ui.chat_markup).
- Renderizar sidebar, chat e avisos.
- Carregar CSV e montar contexto.
- Encaminhar mensagens para o LLM quando disponivel.

O HTML/CSS esta centralizado em ui/chat_markup.py.
"""
from pathlib import Path

import streamlit as st

from services.llm_service import get_ai_response
from services.agent_service import load_agents
from services.document_service import (
    process_uploaded_file,
    process_uploaded_csv,
    process_uploaded_json,
)
from ui.brand import get_logo_path
from ui.theme import apply_theme, init_theme_state


def _ensure_embedding_model():
    try:
        from database.vector_store import get_embedding_model

        with st.spinner("Carregando modelo de embeddings..."):
            # calling this will trigger the cached resource initialization
            get_embedding_model()
    except Exception:
        # fail silently so UI still renders and shows errors where appropriate
        pass

def exibir_chat():
    """Render main chat interface with improved styling and responsiveness."""
    logo_path = get_logo_path()
    
    # Responsive header with flexbox-like behavior
    col_logo, col_title = st.columns([1, 4], gap="medium")
    with col_logo:
        if logo_path:
            st.image(str(logo_path), width=72)
    with col_title:
        st.markdown(
            '<h2 style="margin:0; color:#e9f2ff;">Alea Lumen <span style="color:#4cc3ff;">Chat</span></h2>',
            unsafe_allow_html=True
        )
        st.caption("💬 Inteligência corporativa com contexto seguro.")

    # --- 1. IDENTIFICAÇÃO DO USUÁRIO (CONTEXTO) ---
    user_session = st.session_state.get("user", {})
    _ = user_session.get("id", None)

    # --- 2. SELEÇÃO DO AGENTE ---
    agents = load_agents()
    if not agents:
        st.error("⚠️ Nenhum agente configurado. Vá na aba 'Admin' para criar um.")
        return

    agent_options = {agent_id: data['name'] for agent_id, data in agents.items()}
    
    col_sel, col_role = st.columns([3, 1], gap="medium")
    
    with col_sel:
        selected_agent_id = st.selectbox(
            "🤖 Falar com:", 
            options=list(agent_options.keys()), 
            format_func=lambda x: agent_options[x],
            help="Selecione com qual assistente deseja conversar"
        )
    
    current_agent = agents[selected_agent_id]
    
    with col_role:
        role_badge = current_agent.get('role', 'Assistente')
        st.markdown(
            f'<div style="background:rgba(76,195,255,0.15); padding:0.5rem 0.75rem; '
            f'border-radius:8px; text-align:center; color:#4cc3ff; font-weight:600;">{role_badge}</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # --- Upload de Contexto (CSV/JSON/PDF) ---
    with st.sidebar:
        st.markdown("### 📎 Contexto do Agente")
        uploaded_files = st.file_uploader(
            "Enviar arquivos (CSV, JSON, PDF)",
            type=["csv", "json", "pdf"],
            accept_multiple_files=True,
            key="chat_context_files",
            help="Carregue arquivos para treinar o contexto do assistente"
        )
        if st.button("Processar arquivos", type="secondary"):
            if not uploaded_files:
                st.warning("Selecione ao menos um arquivo.")
            else:
                for uploaded in uploaded_files:
                    suffix = Path(uploaded.name).suffix.lower()
                    if suffix == ".pdf":
                        result = process_uploaded_file(
                            uploaded, collection_name=current_agent["collection_name"]
                        )
                    elif suffix == ".csv":
                        result = process_uploaded_csv(
                            uploaded, collection_name=current_agent["collection_name"]
                        )
                    elif suffix == ".json":
                        result = process_uploaded_json(
                            uploaded, collection_name=current_agent["collection_name"]
                        )
                    else:
                        result = {"status": "error", "message": "Tipo de arquivo não suportado."}

                    if result.get("status") == "success":
                        st.success(f"{uploaded.name}: {result.get('message')}")
                    else:
                        st.error(f"{uploaded.name}: {result.get('message')}")

    # --- 3. HISTÓRICO DE MENSAGENS ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Botão para limpar histórico visual (não apaga o banco de logs)
    if st.sidebar.button("🗑️ Limpar Conversa Atual"):
        st.session_state.messages = []
        st.rerun()

    # Renderiza mensagens anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- 4. INPUT E RESPOSTA ---
    if prompt := st.chat_input(f"Digite sua dúvida para {current_agent['name']}..."):
        
        # 4.1. Exibe e salva mensagem do usuário
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 4.2. Gera resposta da IA
        with st.chat_message("assistant"):
            with st.spinner(f"{current_agent['name']} está analisando..."):
                
                # CHAMADA AO LLM SERVICE
                # Passamos TODOS os dados necessários para o RAG e para o LOG
                resposta = get_ai_response(
                    user_query=prompt,
                    system_instruction=current_agent['system_prompt'],
                    collection_name=current_agent['collection_name'],
                )
                
                st.markdown(resposta)
        
        # 4.3. Salva resposta no histórico
        st.session_state.messages.append({"role": "assistant", "content": resposta})


def main(set_page_config: bool = True) -> None:
    if set_page_config:
        st.set_page_config(page_title="Chat", layout="wide")
    init_theme_state()
    apply_theme()
    # Initialize heavy vector/embedding resources only when entering the chat
    _ensure_embedding_model()
    exibir_chat()
