from typing import Protocol, Optional
import faiss
import numpy as np
import pickle
import os
import logging
from shared.config.settings import get_settings

logger = logging.getLogger(__name__)

class VectorStore(Protocol):
    def add(self, vectors: np.ndarray, metadata: list[dict]): ...
    def search(self, vector: np.ndarray, top_k: int) -> tuple[list[float], list[int]]: ...
    def get_metadata(self, idx: int) -> dict: ...
    def is_loaded(self) -> bool: ...


class FAISSVectorStore:
    def __init__(self, index_path: str, metadata_path: str):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self._faiss_index: Optional[faiss.Index] = None
        self._metadata: Optional[list] = None

    def load(self) -> bool:
        if self._faiss_index is not None:
            return True
        if not os.path.exists(self.index_path) or not os.path.exists(self.metadata_path):
            logger.warning(f"[WARN] FAISS not found at {self.index_path}")
            return False
        try:
            self._faiss_index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "rb") as fh:
                self._metadata = pickle.load(fh)
            logger.info(f"[OK] FAISS index loaded: {self._faiss_index.ntotal} vectors")
            return True
        except Exception as exc:
            logger.error(f"[FAIL] Failed to load FAISS index: {exc}", exc_info=True)
            self._faiss_index = self._metadata = None
            return False

    def is_loaded(self) -> bool:
        return self._faiss_index is not None

    def add(self, vectors: np.ndarray, metadata: list[dict]):
        raise NotImplementedError("Global index is read-only.")

    def search(self, vector: np.ndarray, top_k: int) -> tuple[list[float], list[int]]:
        if not self.is_loaded():
            self.load()
            if not self.is_loaded():
                return [], []
        faiss.normalize_L2(vector)
        k = min(top_k, self._faiss_index.ntotal)
        distances, indices = self._faiss_index.search(vector, k)
        return distances[0], indices[0]

    def get_metadata(self, idx: int) -> dict:
        if self._metadata and 0 <= idx < len(self._metadata):
            return self._metadata[idx]
        return {}


class LocalFAISSVectorStore:
    """Ephemeral in-memory vector store for document chunks."""
    def __init__(self, d: int):
        self._index = faiss.IndexHNSWFlat(d, 32)

    def add(self, vectors: np.ndarray, metadata: list[dict] = None):
        self._index.add(vectors)

    def search(self, vector: np.ndarray, top_k: int) -> tuple[list[float], list[int]]:
        distances, indices = self._index.search(vector, min(top_k, self._index.ntotal))
        return distances[0], indices[0]

    def get_metadata(self, idx: int) -> dict:
        return {}

    def is_loaded(self) -> bool:
        return True
