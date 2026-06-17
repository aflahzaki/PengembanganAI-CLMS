"""Ingest service for loading parsed clauses into ChromaDB.

Takes parsed clauses from excel_parser, chunks them by clause/pasal,
creates metadata, and stores them in the ChromaDB vector store.
"""

from typing import Any, Dict, List, Optional

import chromadb

from app.rag.embeddings import (
    get_chroma_client,
    get_embedding_function,
    get_or_create_collection,
)
from app.utils.excel_parser import ClauseData
from app.utils.text_processing import format_clause_for_embedding


class IngestService:
    """Service for ingesting contract clauses into ChromaDB.

    Handles the transformation of parsed clause data into vector embeddings
    stored in ChromaDB for later retrieval.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "contract_clauses",
    ):
        """Initialize the ingest service.

        Args:
            persist_directory: Path for ChromaDB persistence.
            collection_name: Name of the ChromaDB collection to use.
        """
        self.client = get_chroma_client(persist_directory)
        self.embedding_function = get_embedding_function()
        self.collection_name = collection_name
        self.collection = get_or_create_collection(
            self.client, collection_name, self.embedding_function
        )

    def ingest_clauses(
        self,
        clauses: List[ClauseData],
        template_name: str = "KHS Material Ketenagalistrikan",
    ) -> Dict[str, Any]:
        """Ingest a list of clauses into ChromaDB.

        Each clause is stored as a separate document with metadata
        for filtering and retrieval.

        Args:
            clauses: List of ClauseData objects to ingest.
            template_name: Name of the source template.

        Returns:
            Dictionary with ingestion statistics.
        """
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        for idx, clause in enumerate(clauses):
            # Format the clause text for embedding
            doc_text = format_clause_for_embedding(
                pasal_number=clause.pasal_number,
                section_name=clause.section_name,
                clause_text=clause.clause_text,
                variables=clause.variables,
            )

            # Create metadata for filtering
            metadata = {
                "pasal_number": clause.pasal_number,
                "section_name": clause.section_name,
                "template_name": template_name,
                "is_mandatory": clause.is_mandatory,
                "variables_count": len(clause.variables),
                "variables_list": ", ".join(clause.variables) if clause.variables else "",
                "order_index": idx,
            }

            # Create unique ID
            doc_id = f"{template_name}_{clause.pasal_number}_{idx}".replace(" ", "_")

            documents.append(doc_text)
            metadatas.append(metadata)
            ids.append(doc_id)

        # Clear existing documents for this template before re-ingesting
        try:
            existing = self.collection.get(
                where={"template_name": template_name}
            )
            if existing and existing["ids"]:
                self.collection.delete(ids=existing["ids"])
        except Exception:
            # Collection might be empty or filter might not match
            pass

        # Add documents in batches to avoid memory issues
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch_end = min(i + batch_size, len(documents))
            self.collection.add(
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
                ids=ids[i:batch_end],
            )

        return {
            "total_ingested": len(documents),
            "template_name": template_name,
            "collection_name": self.collection_name,
            "collection_count": self.collection.count(),
        }

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        # Delete and recreate the collection
        self.client.delete_collection(self.collection_name)
        self.collection = get_or_create_collection(
            self.client, self.collection_name, self.embedding_function
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with collection count and metadata.
        """
        return {
            "collection_name": self.collection_name,
            "document_count": self.collection.count(),
        }
