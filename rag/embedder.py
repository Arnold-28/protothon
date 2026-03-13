"""Code Embedder - Converts repository source code into embeddings for semantic search."""

import os
import logging
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from config import Config

logger = logging.getLogger(__name__)


class CodeEmbedder:
    """Reads repository files, splits them into chunks, and generates embeddings."""

    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            openai_api_key=Config.OPENAI_API_KEY,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""],
        )

    def load_repository(self, repo_path: str) -> list[Document]:
        """Load all indexable files from a repository directory into LangChain Documents.

        Args:
            repo_path: Path to the cloned repository.

        Returns:
            List of Document objects with file content and metadata.
        """
        documents: list[Document] = []
        repo_root = Path(repo_path)

        for root, dirs, files in os.walk(repo_root):
            # Skip excluded directories (modify in-place to prevent os.walk descent)
            dirs[:] = [d for d in dirs if d not in Config.SKIP_DIRS]

            for filename in files:
                filepath = Path(root) / filename
                extension = filepath.suffix.lower()

                if extension not in Config.INDEXABLE_EXTENSIONS:
                    continue

                try:
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    if not content.strip():
                        continue

                    relative_path = str(filepath.relative_to(repo_root))
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": relative_path,
                            "extension": extension,
                            "filename": filename,
                        },
                    )
                    documents.append(doc)
                    logger.debug("Loaded file: %s", relative_path)
                except Exception as exc:
                    logger.warning("Failed to read %s: %s", filepath, exc)

        logger.info("Loaded %d files from repository", len(documents))
        return documents

    def chunk_documents(self, documents: list[Document]) -> list[Document]:
        """Split documents into smaller chunks for embedding.

        Args:
            documents: List of full-file Documents.

        Returns:
            List of chunked Documents with preserved metadata.
        """
        chunks = self.text_splitter.split_documents(documents)
        logger.info("Split %d documents into %d chunks", len(documents), len(chunks))
        return chunks
