"""High-level comparator — orchestrates the full SDE pipeline."""
from __future__ import annotations
import time
from dataclasses import dataclass, field

from .chunker import chunk_text, Chunk
from .embedder import embed_chunks, similarity_matrix
from .aligner import align
from .scorer import score_alignment, compute_global_score, compute_delta_index, compute_overall, ScoredPair
from .explainer import explain_all
from .models import get_embedder, AbstractEmbedder
from .domain_profiles import get_profile


@dataclass
class DiffResult:
    """Complete SDE diff result."""
    sde_version: str = "1.0"
    overall: str = "identical"
    global_score: float = 1.0
    delta_index: float = 0.0
    chunks: list[ScoredPair] = field(default_factory=list)
    model: str = "all-MiniLM-L6-v2"
    processing_ms: int = 0
    chunk_count_a: int = 0
    chunk_count_b: int = 0


class SemanticComparator:
    """Main entry point for SDE comparisons."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        embedder: AbstractEmbedder | None = None,
    ):
        self._model_name = model_name
        self._embedder = embedder or get_embedder(model_name)

    def diff(
        self,
        text_a: str,
        text_b: str,
        domain: str = "default",
        chunking_strategy: str = "auto",
        explain: bool = False,
    ) -> DiffResult:
        """Run a full semantic diff between text_a and text_b."""
        t0 = time.perf_counter()

        chunks_a = chunk_text(text_a, source="a", strategy=chunking_strategy)
        chunks_b = chunk_text(text_b, source="b", strategy=chunking_strategy)

        if not chunks_a and not chunks_b:
            return DiffResult()

        profile = get_profile(domain)

        # Handle one-sided empties without embedding
        if not chunks_a or not chunks_b:
            pairs = align(chunks_a, chunks_b, None, threshold=profile.alignment_threshold)
        else:
            emb_a = embed_chunks(chunks_a, embedder=self._embedder)
            emb_b = embed_chunks(chunks_b, embedder=self._embedder)
            sim = similarity_matrix(emb_a, emb_b)
            pairs = align(chunks_a, chunks_b, sim, threshold=profile.alignment_threshold)

        scored = score_alignment(pairs, domain=domain)

        if explain:
            explain_all(scored)

        global_score = compute_global_score(scored)
        delta_index = compute_delta_index(scored)
        overall = compute_overall(global_score, delta_index, domain)

        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        return DiffResult(
            sde_version="1.0",
            overall=overall,
            global_score=global_score,
            delta_index=delta_index,
            chunks=scored,
            model=self._embedder.model_name,
            processing_ms=elapsed_ms,
            chunk_count_a=len(chunks_a),
            chunk_count_b=len(chunks_b),
        )
