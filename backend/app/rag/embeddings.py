"""Embedding utilities for ChromaDB vector storage.

Provides embedding function configuration for use with ChromaDB collections.
Uses ChromaDB's default embedding function or a custom Nomic-compatible one.
"""

from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

from app.config import settings


def get_embedding_function(
    model_name: Optional[str] = None,
) -> embedding_functions.DefaultEmbeddingFunction:
    """Get the embedding function for ChromaDB.

    Uses ChromaDB's DefaultEmbeddingFunction (all-MiniLM-L6-v2) intentionally
    as a lightweight alternative that works out-of-the-box without requiring
    the Nomic model files to be available locally. The settings.EMBEDDING_MODEL
    config (defaulting to "nomic-embed-text-v1.5") is reserved for future use
    when the Nomic model is deployed locally and can be loaded via
    SentenceTransformer or a custom embedding function.

    Args:
        model_name: Optional model name override. Reserved for future use.

    Returns:
        ChromaDB embedding function instance.
    """
    # Intentionally using DefaultEmbeddingFunction (all-MiniLM-L6-v2) rather
    # than settings.EMBEDDING_MODEL ("nomic-embed-text-v1.5") because the Nomic
    # model requires local model files that may not be available in all environments.
    # To switch to Nomic, replace this with a SentenceTransformerEmbeddingFunction
    # configured with model_name or settings.EMBEDDING_MODEL.
    return embedding_functions.DefaultEmbeddingFunction()


def get_chroma_client(
    persist_directory: Optional[str] = None,
) -> chromadb.ClientAPI:
    """Get a persistent ChromaDB client.

    Creates or connects to a persistent ChromaDB instance stored
    at the configured path.

    Args:
        persist_directory: Optional path override for ChromaDB storage.
                          Defaults to configured CHROMA_DB_PATH.

    Returns:
        ChromaDB persistent client instance.
    """
    if persist_directory is None:
        persist_directory = str(settings.chroma_db_absolute_path)

    return chromadb.PersistentClient(path=persist_directory)


def get_or_create_collection(
    client: chromadb.ClientAPI,
    collection_name: str = "contract_clauses",
    embedding_function: Optional[object] = None,
) -> chromadb.Collection:
    """Get or create a ChromaDB collection.

    Args:
        client: ChromaDB client instance.
        collection_name: Name of the collection.
        embedding_function: Optional embedding function. Uses default if None.

    Returns:
        ChromaDB collection instance.
    """
    if embedding_function is None:
        embedding_function = get_embedding_function()

    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )
