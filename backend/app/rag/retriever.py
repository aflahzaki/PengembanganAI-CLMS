"""Retriever service for querying contract clauses from ChromaDB.

Provides methods to search and retrieve clauses by template, topic,
mandatory status, and order.
"""

from typing import Any, Dict, List, Optional

import chromadb

from app.rag.embeddings import (
    get_chroma_client,
    get_embedding_function,
    get_or_create_collection,
)


class RetrieverService:
    """Service for retrieving contract clauses from ChromaDB.

    Supports querying by template name, clause topic, mandatory status,
    and retrieving all clauses in proper order.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "contract_clauses",
    ):
        """Initialize the retriever service.

        Args:
            persist_directory: Path for ChromaDB persistence.
            collection_name: Name of the ChromaDB collection to query.
        """
        self.client = get_chroma_client(persist_directory)
        self.embedding_function = get_embedding_function()
        self.collection = get_or_create_collection(
            self.client, collection_name, self.embedding_function
        )

    def query_by_topic(
        self,
        query_text: str,
        template_name: Optional[str] = None,
        n_results: int = 5,
    ) -> Dict[str, Any]:
        """Query clauses by semantic similarity to a topic.

        Args:
            query_text: The search query text.
            template_name: Optional filter by template name.
            n_results: Maximum number of results to return.

        Returns:
            Dictionary with matching documents, metadatas, and distances.
        """
        where_filter = None
        if template_name:
            where_filter = {"template_name": template_name}

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter,
        )

        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    def get_all_clauses_for_template(
        self,
        template_name: str = "KHS Material Ketenagalistrikan",
    ) -> List[Dict[str, Any]]:
        """Get all clauses for a specific template in order.

        Args:
            template_name: Name of the template to retrieve clauses for.

        Returns:
            List of clause dictionaries ordered by their index.
        """
        results = self.collection.get(
            where={"template_name": template_name},
        )

        if not results or not results["ids"]:
            return []

        # Combine documents with metadata
        clauses = []
        for i in range(len(results["ids"])):
            clause = {
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i],
            }
            clauses.append(clause)

        # Sort by order_index
        clauses.sort(key=lambda x: x["metadata"].get("order_index", 0))
        return clauses

    def get_mandatory_clauses(
        self,
        template_name: str = "KHS Material Ketenagalistrikan",
    ) -> List[Dict[str, Any]]:
        """Get only mandatory clauses for a template.

        Args:
            template_name: Name of the template.

        Returns:
            List of mandatory clause dictionaries in order.
        """
        results = self.collection.get(
            where={
                "$and": [
                    {"template_name": template_name},
                    {"is_mandatory": True},
                ]
            },
        )

        if not results or not results["ids"]:
            return []

        clauses = []
        for i in range(len(results["ids"])):
            clause = {
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i],
            }
            clauses.append(clause)

        clauses.sort(key=lambda x: x["metadata"].get("order_index", 0))
        return clauses

    def get_clause_by_pasal(
        self,
        pasal_number: str,
        template_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific clause by its Pasal number.

        Args:
            pasal_number: The Pasal identifier (e.g., 'Pasal 1').
            template_name: Optional template name filter.

        Returns:
            Clause dictionary if found, None otherwise.
        """
        where_filter: Dict[str, Any] = {"pasal_number": pasal_number}
        if template_name:
            where_filter = {
                "$and": [
                    {"pasal_number": pasal_number},
                    {"template_name": template_name},
                ]
            }

        results = self.collection.get(where=where_filter)

        if not results or not results["ids"]:
            return None

        return {
            "id": results["ids"][0],
            "document": results["documents"][0],
            "metadata": results["metadatas"][0],
        }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection.

        Returns:
            Dictionary with collection count and info.
        """
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection.name,
        }
