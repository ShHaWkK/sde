"""Ollama local LLM embedding backend."""
import numpy as np
import httpx
from .base import AbstractEmbedder


class OllamaEmbedder(AbstractEmbedder):
    """Uses a local Ollama instance for embeddings (offline fallback)."""

    def __init__(self, model_name: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")

    @property
    def model_name(self) -> str:
        return f"ollama:{self._model_name}"

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 768))
        embeddings = []
        with httpx.Client(timeout=60.0) as client:
            for text in texts:
                resp = client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._model_name, "prompt": text},
                )
                resp.raise_for_status()
                embeddings.append(resp.json()["embedding"])
        return np.array(embeddings, dtype=np.float32)
