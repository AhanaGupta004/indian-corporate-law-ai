from typing import Protocol
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingProvider(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray:
        ...

class SentenceTransformerProvider:
    _instance = None
    _model = None

    def __new__(cls, model_name: str = "all-MiniLM-L6-v2"):
        if cls._instance is None:
            cls._instance = super(SentenceTransformerProvider, cls).__new__(cls)
            cls._model = SentenceTransformer(model_name)
        return cls._instance

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(texts).astype("float32")
