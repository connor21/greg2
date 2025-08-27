import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "docs")

    DATA_ROOT: str = os.getenv("DATA_ROOT", "./data")

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    RERANK_MODEL: str = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-base")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.1:8b")

    CHUNK_SIZE_TOKENS: int = int(os.getenv("CHUNK_SIZE_TOKENS", "600"))
    CHUNK_OVERLAP_TOKENS: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "80"))
    TOP_K: int = int(os.getenv("TOP_K", "30"))
    TOP_N: int = int(os.getenv("TOP_N", "6"))

    @property
    def DOCS_DIR(self) -> Path:
        return Path(self.DATA_ROOT).joinpath("docs")

    @property
    def CACHE_DIR(self) -> Path:
        return Path(self.DATA_ROOT).joinpath("cache")
