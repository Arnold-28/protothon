"""Vector Store - FAISS-based vector storage for code embeddings."""

import logging
import os
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from rag.embedder import CodeEmbedder
from config import Config

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages a FAISS vector store for repository code embeddings."""

    def __init__(self) -> None:
        self.embedder = CodeEmbedder()
        self.store: FAISS | None = None

    def build_index(self, repo_path: str) -> None:
        """Build a FAISS index from repository source files.

        Args:
            repo_path: Path to the cloned repository.
        """
        documents = self.embedder.load_repository(repo_path)
        if not documents:
            logger.warning("No documents found in repository at %s", repo_path)
            return

        chunks = self.embedder.chunk_documents(documents)
        logger.info("Building FAISS index from %d chunks...", len(chunks))

        self.store = FAISS.from_documents(chunks, self.embedder.embeddings)
        logger.info("FAISS index built successfully")

    def save_index(self, path: str | None = None) -> None:
        """Save the FAISS index to disk.

        Args:
            path: Directory to save the index. Defaults to Config.FAISS_INDEX_DIR.
        """
        if self.store is None:
            logger.error("No index to save. Build the index first.")
            return

        save_path = path or Config.FAISS_INDEX_DIR
        os.makedirs(save_path, exist_ok=True)
        self.store.save_local(save_path)
        logger.info("FAISS index saved to %s", save_path)

    def load_index(self, path: str | None = None) -> None:
        """Load a FAISS index from disk.

        Args:
            path: Directory to load the index from. Defaults to Config.FAISS_INDEX_DIR.
        """
        load_path = path or Config.FAISS_INDEX_DIR
        if not Path(load_path).exists():
            logger.error("No index found at %s", load_path)
            return

        self.store = FAISS.load_local(
            load_path,
            self.embedder.embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info("FAISS index loaded from %s", load_path)

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        """Search for code chunks most relevant to the query.

        Args:
            query: Natural language query describing the code to find.
            k: Number of results to return.

        Returns:
            List of the most relevant Document chunks.
        """
        if self.store is None:
            logger.error("No index loaded. Build or load the index first.")
            return []

        results = self.store.similarity_search(query, k=k)
        logger.info("Found %d relevant chunks for query", len(results))
        return results
