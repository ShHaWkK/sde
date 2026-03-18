from .base import AbstractEmbedder
from .sentence_transformers import SentenceTransformerEmbedder

__all__ = ["AbstractEmbedder", "SentenceTransformerEmbedder"]

def get_embedder(model_name: str = "all-MiniLM-L6-v2") -> AbstractEmbedder:
    """Factory: return the best available embedder for the given model name."""
    if model_name.startswith("text-embedding"):
        from .openai import OpenAIEmbedder
        return OpenAIEmbedder(model_name)
    elif model_name.startswith("ollama:"):
        from .local_llm import OllamaEmbedder
        return OllamaEmbedder(model_name.removeprefix("ollama:"))
    else:
        return SentenceTransformerEmbedder(model_name)
