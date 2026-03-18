"""Abstract embedder interface."""
from abc import ABC, abstractmethod
import numpy as np


class AbstractEmbedder(ABC):
    """Base class for all embedding backends."""

    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of texts into embeddings.

        Args:
            texts: List of text strings to embed.

        Returns:
            2D numpy array of shape (len(texts), embedding_dim).
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier string."""
        ...

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text. Convenience wrapper."""
        return self.encode([text])[0]
