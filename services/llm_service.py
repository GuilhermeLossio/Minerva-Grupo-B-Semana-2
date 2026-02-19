import datetime
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def get_ai_response(user_query, system_instruction=None, collection_name: str = "corporate_docs"):
    '''
    Orquestra o fluxo de RAG:
    1. Busca Contexto no banco vetorial
    2. Monta o Prompt com os documentos encontrados
    3. Envia para o Gemini gerar a resposta
    '''
    API_KEY = os.getenv("GOOGLE_API_KEY")
    if not API_KEY:
        return "Erro: GOOGLE_API_KEY não configurada no arquivo .env"
    try:
        from database.vector_store import search_context
        # 1. Busca o contexto a partir dos 4 trechos mais relevantes      
        docs = search_context(user_query, k=4, collection_name=collection_name)
        if docs:
            context_text = "\n\n".join([doc.page_content for doc in docs])
            sources = list(set([doc.metadata.get('source', 'Desconhecido') for doc in docs]))
            source_note = f"\n\n(Fontes utilizadas: {', '.join(sources)})"
        else:
            context_text = "Nenhum documento específico encontrado no banco de dados."
            source_note = ""

        #2. Configuração do modelo (Google Gemini)
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,
            google_api_key=API_KEY,
            max_retries=2
        )

        #3. Definição do Prompt.
        if not system_instruction:
            system_instruction = (
                "Você é o assistente virtual corporativo 'Alea-Lumen'. "
                "Responda de forma profissional e direta."
            )
        
        template = """
        {system_instruction}

        Use EXCLUSIVAMENTE o contexto abaixo para responder à pergunta do usuário.
        Se a resposta não estiver no contexto, diga que não encontrou a informação nos documentos.
        
        --- CONTEXTO ---
        {context}
        ----------------
        
        Pergunta do Usuário: {query}
        """

        prompt = ChatPromptTemplate.from_template(template)

        #4. Execução
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({
            "system_instruction": system_instruction,
            "context": context_text,
            "query": user_query
        })
        return response + source_note
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"


def log_interaction(user_id=None, context=None, response=None, attachments=None):
    """
    Registra os dados de interação para fins de observabilidade.
    """

    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": user_id, #Usuário que está usando 
        "context_summary": context[:100], # Contexto do usuário
        "full_context": context,           # Para investigação
        "attachments": attachments or [],
        "flagged_inappropriate": False 
    }
    # Banco de dados
    # save_to_db(log_entry) 
    return log_entry
