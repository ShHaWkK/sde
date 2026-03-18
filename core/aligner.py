"""Optimal alignment using the Hungarian algorithm."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.optimize import linear_sum_assignment
from .chunker import Chunk


@dataclass
class AlignedPair:
    """A pair of aligned chunks (one or both may be None for ins/del)."""
    chunk_a: Chunk | None
    chunk_b: Chunk | None
    score: float  # cosine similarity, or 0.0 for added/removed


def align(
    chunks_a: list[Chunk],
    chunks_b: list[Chunk],
    sim_matrix: np.ndarray | None,
    threshold: float = 0.15,
) -> list[AlignedPair]:
    """Optimally align two lists of chunks using the Hungarian algorithm.

    Chunks that fall below `threshold` similarity are treated as added/removed.
    """
    if not chunks_a and not chunks_b:
        return []
    if not chunks_a:
        return [AlignedPair(None, cb, 0.0) for cb in chunks_b]
    if not chunks_b:
        return [AlignedPair(ca, None, 0.0) for ca in chunks_a]

    # Hungarian minimizes cost; we maximize similarity → invert
    cost_matrix = 1.0 - sim_matrix
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    matched_a: set[int] = set()
    matched_b: set[int] = set()
    pairs: list[AlignedPair] = []

    for r, c in zip(row_ind, col_ind):
        score = sim_matrix[r, c]
        if score >= threshold:
            pairs.append(AlignedPair(chunks_a[r], chunks_b[c], float(score)))
            matched_a.add(r)
            matched_b.add(c)

    # Unmatched → insertions / deletions
    for i, ca in enumerate(chunks_a):
        if i not in matched_a:
            pairs.append(AlignedPair(ca, None, 0.0))
    for j, cb in enumerate(chunks_b):
        if j not in matched_b:
            pairs.append(AlignedPair(None, cb, 0.0))

    # Sort by position in A (then B for insertions)
    pairs.sort(key=lambda p: (p.chunk_a.id if p.chunk_a else float("inf"), p.chunk_b.id if p.chunk_b else float("inf")))
    return pairs
