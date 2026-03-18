"""Embedding layer — thin wrapper that delegates to models."""
from __future__ import annotations
import numpy as np
from .chunker import Chunk
from .models import get_embedder, AbstractEmbedder


def embed_chunks(
    chunks: list[Chunk],
    model_name: str = "all-MiniLM-L6-v2",
    embedder: AbstractEmbedder | None = None,
) -> np.ndarray:
    """Embed a list of chunks. Returns ndarray of shape (len(chunks), dim)."""
    if not chunks:
        return np.empty((0, 384))
    emb = embedder or get_embedder(model_name)
    texts = [c.text for c in chunks]
    return emb.encode(texts)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two 1-D vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def similarity_matrix(emb_a: np.ndarray, emb_b: np.ndarray) -> np.ndarray:
    """Compute NxM cosine similarity matrix between two embedding matrices."""
    # Normalize rows
    norms_a = np.linalg.norm(emb_a, axis=1, keepdims=True)
    norms_b = np.linalg.norm(emb_b, axis=1, keepdims=True)
    norms_a = np.where(norms_a == 0, 1e-10, norms_a)
    norms_b = np.where(norms_b == 0, 1e-10, norms_b)
    a_norm = emb_a / norms_a
    b_norm = emb_b / norms_b
    return a_norm @ b_norm.T
