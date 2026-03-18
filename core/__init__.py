"""Semantic Diff Engine — core package."""
from .comparator import SemanticComparator
from .scorer import score_alignment
from .chunker import chunk_text

__all__ = ["SemanticComparator", "score_alignment", "chunk_text"]
