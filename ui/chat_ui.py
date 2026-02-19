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
    logo_path = get_logo_path()
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        if logo_path:
            st.image(str(logo_path), width=72)
    with col_title:
        st.markdown("## Alea Lumen")
        st.caption("Chat corporativo com contexto inteligente.")

    # --- 1. IDENTIFICAÇÃO DO USUÁRIO (CONTEXTO) ---
    # Tenta pegar os dados reais do login (se auth estiver implementado)
    user_session = st.session_state.get("user", {})
    
    # Se não houver login real, usamos valores de "Convidado" para não quebrar o log
    # (Ou você pode manter os inputs na sidebar para teste manual, como deixei comentado abaixo)
    _ = user_session.get("id", None)

    # --- DEBUG/SIMULAÇÃO (Opcional: Descomente se quiser testar setores sem fazer login) ---
    # with st.sidebar:
    #     st.divider()
    #     st.caption("👤 Simulação de Identidade")
    #     user_name = st.text_input("Nome", user_name)
    #     user_sector = st.selectbox("Setor", ["TI", "RH", "Financeiro", "Jurídico"], index=0)
    # -------------------------------------------------------------------------------------

    # --- 2. SELEÇÃO DO AGENTE ---
    agents = load_agents()
    if not agents:
        st.error("⚠️ Nenhum agente configurado. Vá na aba 'Admin' para criar um.")
        return

    # Mapeia ID -> Nome para o Selectbox
    agent_options = {agent_id: data['name'] for agent_id, data in agents.items()}
    
    col_sel, col_info = st.columns([3, 1])
    
    with col_sel:
        # O usuário escolhe com quem quer falar
        selected_agent_id = st.selectbox(
            "Falar com:", 
            options=list(agent_options.keys()), 
            format_func=lambda x: agent_options[x]
        )
    
    # Recupera os dados completos do agente escolhido
    current_agent = agents[selected_agent_id]
    
    with col_info:
        # Mostra cargo/função do agente
        st.info(f"**{current_agent.get('role', 'Assistente')}**")

    st.divider()

    # --- Upload de Contexto (CSV/JSON/PDF) ---
    with st.sidebar:
        st.markdown("### Contexto do Agente")
        uploaded_files = st.file_uploader(
            "Enviar arquivos (CSV, JSON, PDF)",
            type=["csv", "json", "pdf"],
            accept_multiple_files=True,
            key="chat_context_files",
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
    apply_theme(st.session_state.get("dark_mode", True))
    # Initialize heavy vector/embedding resources only when entering the chat
    _ensure_embedding_model()
    exibir_chat()
