"""OpenAI embeddings backend (optional)."""
import numpy as np
from .base import AbstractEmbedder


class OpenAIEmbedder(AbstractEmbedder):
    """Uses the OpenAI API for embeddings. Requires OPENAI_API_KEY env var."""

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self._model_name = model_name
        try:
            from openai import OpenAI
            self._client = OpenAI()
        except ImportError:
            raise ImportError("Install openai: pip install semantic-diff[openai]")

    @property
    def model_name(self) -> str:
        return self._model_name

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 1536))
        # OpenAI API accepts up to 2048 inputs per request
        response = self._client.embeddings.create(model=self._model_name, input=texts)
        return np.array([d.embedding for d in response.data], dtype=np.float32)
