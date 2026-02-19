from __future__ import annotations

import atexit
import os
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

import chromadb
import streamlit as st
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from utils.debug import log

DEFAULT_COLLECTION_NAME = "corporate_docs"
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)
PERSIST_DIRECTORY = Path(os.getenv("CHROMA_PERSIST_DIR", "chroma_db"))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


class SentenceTransformerEmbeddings(Embeddings):
    """LangChain-compatible wrapper for sentence-transformers embeddings."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            log(f"vector_store: loading embedding model '{self.model_name}'")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = self._ensure_model()
        return model.encode(texts).tolist()

    def embed_query(self, text: str) -> list[float]:
        model = self._ensure_model()
        return model.encode(text).tolist()


def _normalize_collection_name(collection_name: str | None) -> str:
    name = (collection_name or DEFAULT_COLLECTION_NAME).strip()
    return name or DEFAULT_COLLECTION_NAME


def _ensure_persist_dir() -> None:
    PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)


def _normalize_texts(texts: Sequence[str]) -> list[str]:
    if isinstance(texts, str):
        texts = [texts]
    return [text.strip() for text in texts if isinstance(text, str) and text.strip()]


def _normalize_metadatas(
    metadatas: Sequence[Mapping[str, Any]] | None, total: int
) -> list[dict[str, Any]]:
    if metadatas is None:
        return [{} for _ in range(total)]

    normalized: list[dict[str, Any]] = []
    for metadata in metadatas[:total]:
        normalized.append(dict(metadata) if metadata else {})

    missing = total - len(normalized)
    if missing > 0:
        normalized.extend({} for _ in range(missing))

    return normalized


@st.cache_resource
def get_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> Embeddings:
    """Return a cached embedding model instance."""
    return SentenceTransformerEmbeddings(model_name=model_name)


@st.cache_resource
def get_chroma_client() -> chromadb.PersistentClient:
    """Return a cached Chroma persistent client with telemetry disabled."""
    _ensure_persist_dir()
    return chromadb.PersistentClient(
        path=str(PERSIST_DIRECTORY),
        settings=Settings(anonymized_telemetry=False),
    )


@st.cache_resource
def get_vectorstore(collection_name: str = DEFAULT_COLLECTION_NAME) -> Chroma:
    """Return a cached Chroma store for the target collection."""
    normalized_collection = _normalize_collection_name(collection_name)
    embedding_function = get_embedding_model()
    client = get_chroma_client()
    return Chroma(
        client=client,
        collection_name=normalized_collection,
        embedding_function=embedding_function,
    )


def add_documents_to_db(
    texts: Sequence[str],
    metadatas: Sequence[Mapping[str, Any]] | None = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> bool:
    """Persist text chunks and optional metadata into the vector store."""
    cleaned_texts = _normalize_texts(texts)
    if not cleaned_texts:
        log("vector_store: no valid texts to add")
        return False

    normalized_metadatas = _normalize_metadatas(metadatas, len(cleaned_texts))
    docs = [
        Document(page_content=text, metadata=metadata)
        for text, metadata in zip(cleaned_texts, normalized_metadatas)
    ]

    try:
        db = get_vectorstore(collection_name)
        db.add_documents(docs)
        log(
            "vector_store: added "
            f"{len(docs)} docs to '{_normalize_collection_name(collection_name)}'"
        )
        return True
    except Exception as exc:
        log(f"vector_store: add_documents_to_db error: {exc}")
        return False


def search_context(
    query: str, k: int = 4, collection_name: str = DEFAULT_COLLECTION_NAME
) -> list:
    """Return top-k similar chunks for the query."""
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []

    try:
        top_k = max(1, int(k))
    except Exception:
        top_k = 4

    try:
        db = get_vectorstore(collection_name)
        return db.similarity_search(normalized_query, k=top_k)
    except Exception as exc:
        log(f"vector_store: search_context error: {exc}")
        return []


def clear_database() -> None:
    """Delete persisted Chroma data and clear related Streamlit resource caches."""
    _clear_vector_resources()
    if PERSIST_DIRECTORY.exists():
        shutil.rmtree(PERSIST_DIRECTORY, ignore_errors=True)
        log(f"vector_store: cleared '{PERSIST_DIRECTORY}'")


def _clear_vector_resources() -> None:
    try:
        get_vectorstore.clear()
    except Exception:
        pass

    try:
        get_chroma_client.clear()
    except Exception:
        pass

    try:
        get_embedding_model.clear()
    except Exception:
        pass


def _shutdown_chroma_client() -> None:
    try:
        client = get_chroma_client()
    except Exception:
        return

    try:
        system = getattr(client, "_system", None)
        if system is not None and hasattr(system, "stop"):
            system.stop()
            log("vector_store: chroma system stopped")
    except Exception:
        pass


def _cleanup_on_exit() -> None:
    _shutdown_chroma_client()
    _clear_vector_resources()


atexit.register(_cleanup_on_exit)
