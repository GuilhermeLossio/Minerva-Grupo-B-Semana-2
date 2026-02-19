import getpass
import os
from dotenv import load_dotenv
import shutil
import chromadb
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import streamlit as st
from typing import List

PERSIST_DIRECTORY = "./chroma_db"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()


@st.cache_resource
def get_vectorstore(collection_name: str = "corporate_docs"):
  """
    Inicializa ou carrega o banco de dados vetorial (ChromaDB). Usando modelo local
    Não precisa de API Key, não tem limite de cota, funciona offline.
    """
  print(f"Carregando modelo de Embeddings Local")

  embedding_function = SentenceTransformerEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


  vectorstore = Chroma(
    collection_name=collection_name,
    embedding_function=embedding_function,
    persist_directory=PERSIST_DIRECTORY
  )

  return vectorstore

def add_documents_to_db(texts, metadatas=None, collection_name: str = "corporate_docs"):
  '''
    Recebe uma lista de textos e salva no banco.
  '''
  try:
        db = get_vectorstore(collection_name)
        
        # Se não houver metadados, cria lista vazia para evitar erro
        if metadatas is None:
            metadatas = [{} for _ in texts]

        # Cria objetos Document do LangChain
        docs = [
            Document(page_content=t, metadata=m) 
            for t, m in zip(texts, metadatas)
        ]
        
        # Adiciona ao banco (Isso gera os arquivos na pasta chroma_db)
        db.add_documents(docs)
        print(f"Sucesso: {len(texts)} chunks adicionados ao banco vetorial.")
        return True
  except Exception as e:
        print(f"Erro ao adicionar documentos: {e}")
        return False
  
def search_context(query, k=4, collection_name: str = "corporate_docs"):
  '''
  Busca os 4 trechos mais parecidos com a pergunta do usuário
  '''
  try:
        db = get_vectorstore(collection_name)
        results = db.similarity_search(query, k=k)
        return results
  except Exception as e:
      print(f"Erro na busca vetorial: {e}")
      return []
  
def clear_database():
    '''
    Utilitário: apaga o banco para resetar dados.
    '''
    if os.path.exists(PERSIST_DIRECTORY):
        shutil.rmtree(PERSIST_DIRECTORY)
        print("Banco de dados limpo")
