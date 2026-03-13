"""Configuration management for GitFix_AI."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration loaded from environment variables."""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    REPO_NAME: str = os.getenv("REPO_NAME", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # Directories
    CLONE_DIR: str = os.getenv("CLONE_DIR", "cloned_repos")
    FAISS_INDEX_DIR: str = os.getenv("FAISS_INDEX_DIR", "faiss_index")

    # Embedding settings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # File extensions to index
    INDEXABLE_EXTENSIONS: set[str] = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
        ".rs", ".cpp", ".c", ".h", ".hpp", ".rb", ".php",
        ".swift", ".kt", ".scala", ".sh", ".bash", ".yml",
        ".yaml", ".json", ".toml", ".cfg", ".ini", ".md",
        ".txt", ".html", ".css", ".sql",
    }

    # Directories to skip during indexing
    SKIP_DIRS: set[str] = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        "env", ".env", "dist", "build", ".next", ".nuxt",
        "vendor", ".idea", ".vscode", "target", "bin", "obj",
    }

    @classmethod
    def validate(cls) -> list[str]:
        """Validate that required configuration is present. Returns list of errors."""
        errors = []
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set")
        if not cls.GITHUB_TOKEN:
            errors.append("GITHUB_TOKEN is not set")
        if not cls.REPO_NAME:
            errors.append("REPO_NAME is not set")
        return errors
