from __future__ import annotations

import datetime
import os
from functools import lru_cache

DEFAULT_SYSTEM_INSTRUCTION = (
    "Voce e o assistente virtual corporativo 'Alea-Lumen'. "
    "Responda de forma profissional e direta."
)

PROMPT_TEMPLATE = """
{system_instruction}

Use EXCLUSIVAMENTE o contexto abaixo para responder a pergunta do usuario.
Se a resposta nao estiver no contexto, diga que nao encontrou a informacao nos documentos.

--- CONTEXTO ---
{context}
----------------

Pergunta do Usuario: {query}
"""


@lru_cache(maxsize=1)
def _get_prompt_template():
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate.from_template(PROMPT_TEMPLATE)


@lru_cache(maxsize=1)
def _get_output_parser():
    from langchain_core.output_parsers import StrOutputParser

    return StrOutputParser()


@lru_cache(maxsize=2)
def _get_llm_client(api_key: str):
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        google_api_key=api_key,
        max_retries=2,
    )


def _build_context_from_docs(docs) -> tuple[str, str]:
    if not docs:
        return "Nenhum documento especifico encontrado no banco de dados.", ""

    context_text = "\n\n".join(doc.page_content for doc in docs)
    sources = sorted({(doc.metadata or {}).get("source", "Desconhecido") for doc in docs})
    source_note = f"\n\n(Fontes utilizadas: {', '.join(sources)})" if sources else ""
    return context_text, source_note


def get_ai_response(user_query, system_instruction=None, collection_name: str = "corporate_docs"):
    """
    Orquestra o fluxo de RAG:
    1. Busca Contexto no banco vetorial
    2. Monta o Prompt com os documentos encontrados
    3. Envia para o Gemini gerar a resposta
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Erro: GOOGLE_API_KEY nao configurada no arquivo .env"

    normalized_query = (user_query or "").strip()
    if not normalized_query:
        return "Informe uma pergunta para o assistente."

    try:
        from database.vector_store import search_context

        docs = search_context(normalized_query, k=4, collection_name=collection_name)
        context_text, source_note = _build_context_from_docs(docs)

        llm = _get_llm_client(api_key)
        prompt = _get_prompt_template()
        parser = _get_output_parser()
        chain = prompt | llm | parser

        response = chain.invoke(
            {
                "system_instruction": (system_instruction or DEFAULT_SYSTEM_INSTRUCTION),
                "context": context_text,
                "query": normalized_query,
            }
        )
        return response + source_note
    except Exception as exc:
        return f"Erro ao gerar resposta: {str(exc)}"


def log_interaction(user_id=None, context=None, response=None, attachments=None):
    """
    Registra os dados de interacao para fins de observabilidade.
    """
    safe_context = context or ""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": user_id,
        "context_summary": safe_context[:100],
        "full_context": safe_context,
        "response": response,
        "attachments": attachments or [],
        "flagged_inappropriate": False,
    }
    return log_entry
