"""
semantic-diff Python SDK — thin client wrapper around the SDE API.

For direct usage without the API, import from `core` instead.
"""
from __future__ import annotations
import httpx
from typing import Iterator


class SemanticDiffClient:
    """HTTP client for the SDE API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def diff(
        self,
        text_a: str,
        text_b: str,
        domain: str = "default",
        explain: bool = False,
        chunking_strategy: str = "auto",
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> dict:
        """Compare two texts. Returns the full SDE result dict."""
        payload = {
            "version": "1.0",
            "text_a": text_a,
            "text_b": text_b,
            "domain": domain,
            "options": {
                "chunking_strategy": chunking_strategy,
                "embedding_model": embedding_model,
                "explain": explain,
            },
        }
        resp = self._client.post("/diff", json=payload)
        resp.raise_for_status()
        return resp.json()

    def batch(self, items: list[dict]) -> dict:
        """Compare multiple pairs. Each item: {text_a, text_b, domain?, options?}"""
        resp = self._client.post("/batch", json={"items": items})
        resp.raise_for_status()
        return resp.json()

    def health(self) -> dict:
        resp = self._client.get("/health")
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
