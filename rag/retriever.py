"""Code Retriever - Retrieves relevant code context from the vector store for a given issue."""

import logging

from langchain.schema import Document

from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class CodeRetriever:
    """Retrieves relevant code snippets from the indexed repository using RAG search."""

    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    def retrieve_context(self, query: str, k: int = 5) -> list[Document]:
        """Retrieve the most relevant code snippets for a given query.

        Args:
            query: Search query (typically the interpreted issue description).
            k: Number of code chunks to retrieve.

        Returns:
            List of relevant Document chunks with source metadata.
        """
        results = self.vector_store.similarity_search(query, k=k)
        logger.info(
            "Retrieved %d code chunks for query: %.80s...",
            len(results),
            query,
        )
        return results

    def format_context(self, documents: list[Document]) -> str:
        """Format retrieved documents into a context string for the LLM.

        Args:
            documents: List of retrieved Document chunks.

        Returns:
            Formatted string containing file paths and code content.
        """
        if not documents:
            return "No relevant code context found."

        context_parts: list[str] = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "unknown")
            context_parts.append(
                f"--- File: {source} (chunk {i}) ---\n{doc.page_content}"
            )

        return "\n\n".join(context_parts)
