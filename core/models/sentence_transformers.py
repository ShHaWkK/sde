"""Sentence Transformers embedding backend."""
import numpy as np
from .base import AbstractEmbedder

_CACHE: dict[str, "SentenceTransformerEmbedder"] = {}


class SentenceTransformerEmbedder(AbstractEmbedder):
    """Uses sentence-transformers for local, offline embedding."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        if model_name not in _CACHE:
            from sentence_transformers import SentenceTransformer
            _CACHE[model_name] = SentenceTransformer(model_name)
        self._model = _CACHE[model_name]

    @property
    def model_name(self) -> str:
        return self._model_name

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 384))
        return self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
