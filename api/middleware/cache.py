"""Redis-backed embedding cache."""
from __future__ import annotations
import hashlib
import json
import os
import numpy as np


def _cache_key(text: str, model: str) -> str:
    h = hashlib.sha256(f"{model}:{text}".encode()).hexdigest()
    return f"sde:emb:{h}"


class EmbeddingCache:
    """Cache embeddings in Redis by (model, text) hash."""

    def __init__(self, redis_url: str | None = None, ttl: int = 86400):
        self.ttl = ttl
        self._redis = None
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            import redis
            self._redis = redis.from_url(url, decode_responses=False)
            self._redis.ping()
        except Exception:
            # Redis not available — operate without cache
            self._redis = None

    def get(self, text: str, model: str) -> np.ndarray | None:
        if not self._redis:
            return None
        key = _cache_key(text, model)
        try:
            data = self._redis.get(key)
            if data:
                return np.frombuffer(data, dtype=np.float32)
        except Exception:
            pass
        return None

    def set(self, text: str, model: str, embedding: np.ndarray) -> None:
        if not self._redis:
            return
        key = _cache_key(text, model)
        try:
            self._redis.setex(key, self.ttl, embedding.astype(np.float32).tobytes())
        except Exception:
            pass

    @property
    def available(self) -> bool:
        return self._redis is not None
