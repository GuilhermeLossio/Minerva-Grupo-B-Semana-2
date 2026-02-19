import os
import shutil
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Carrega ambiente
load_dotenv()
KEY = os.getenv("GOOGLE_API_KEY")

print("--- 🕵️‍♂️ INICIANDO DIAGNÓSTICO DO BANCO ---")

if not KEY:
    print("❌ ERRO: Arquivo .env não encontrado ou sem chave.")
    exit()

print(f"🔑 Chave detectada: {KEY[:5]}... (OK)")

# TESTE 1: Tentar gerar um embedding (Sem banco de dados)
print("\n1. Testando conexão com API de Embeddings do Google...")
try:
    # Vamos tentar o modelo mais antigo e compatível primeiro
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", # Modelo V1 (mais garantido de funcionar)
        google_api_key=KEY
    )
    vetor = embeddings.embed_query("Teste de conexão")
    print(f"✅ SUCESSO! A API gerou um vetor de tamanho {len(vetor)}.")
except Exception as e:
    print(f"❌ FALHA NA API DO GOOGLE: {e}")
    print("👉 Solução: Sua chave API não está habilitada para Embeddings ou o modelo está errado.")
    exit()

# TESTE 2: Tentar criar a pasta e salvar (ChromaDB)
print("\n2. Testando criação da pasta 'chroma_db'...")
pasta_banco = "./chroma_db_teste"

# Limpa teste anterior se existir
if os.path.exists(pasta_banco):
    shutil.rmtree(pasta_banco)

try:
    vectorstore = Chroma(
        collection_name="teste_diagnostico",
        embedding_function=embeddings,
        persist_directory=pasta_banco
    )
    
    doc = Document(page_content="Isso é um teste.", metadata={"fonte": "teste"})
    vectorstore.add_documents([doc])
    
    if os.path.exists(pasta_banco):
        print(f"✅ SUCESSO! Pasta '{pasta_banco}' criada com sucesso.")
        print("🎉 O problema foi resolvido usando o modelo 'models/embedding-001'.")
    else:
        print("❌ ERRO: O código rodou sem erro, mas a pasta não apareceu.")

except Exception as e:
    print(f"❌ FALHA NO CHROMADB (Instalação ou Permissão): {e}")
    print("👉 Solução: Tente rodar 'pip install langchain-chroma chromadb --upgrade'")