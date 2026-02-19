import os
import json
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd

def _split_text(text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return text_splitter.split_text(text)


def _save_chunks(chunks, filename: str, collection_name: str):
    if not chunks:
        return {"status": "error", "message": "Não foi possível dividir o texto em chunks."}
    metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]
    from database.vector_store import add_documents_to_db
    success = add_documents_to_db(chunks, metadatas, collection_name=collection_name)
    if success:
        return {
            "status": "success",
            "message": "Processado com Sucesso!",
            "details": f"Arquivo '{filename}' gerou {len(chunks)} fragmentos de conhecimento."
        }
    return {"status": "error", "message": "Falha ao salvar no banco de dados."}


def process_uploaded_file(uploaded_file, collection_name: str = "corporate_docs"):
    '''
    Lê um arquivo em PDF (Upload do Streamlit), extrai o texto e salva no banco.
    '''
    try:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if not text.strip():
            return {"status": "error", "message": "O PDF parece estar vazio ou é uma imagem (sem texto selecionável)."}
        chunks = _split_text(text)
        filename = uploaded_file.name
        return _save_chunks(chunks, filename, collection_name)
    except Exception as e:
        return {"status": "error", "message": f"Erro interno ao processar PDF: {str(e)}"}


def process_uploaded_csv(uploaded_file, collection_name: str = "corporate_docs"):
    try:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file)
        text = df.to_csv(index=False)
        chunks = _split_text(text)
        filename = uploaded_file.name
        return _save_chunks(chunks, filename, collection_name)
    except Exception as e:
        return {"status": "error", "message": f"Erro ao processar CSV: {str(e)}"}


def process_uploaded_json(uploaded_file, collection_name: str = "corporate_docs"):
    try:
        uploaded_file.seek(0)
        raw = uploaded_file.read()
        try:
            text = raw.decode("utf-8")
        except Exception:
            text = raw.decode("latin-1", errors="ignore")
        try:
            parsed = json.loads(text)
            text = json.dumps(parsed, ensure_ascii=False, indent=2)
        except Exception:
            pass
        chunks = _split_text(text)
        filename = uploaded_file.name
        return _save_chunks(chunks, filename, collection_name)
    except Exception as e:
        return {"status": "error", "message": f"Erro ao processar JSON: {str(e)}"}
