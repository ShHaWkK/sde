"""Scoring and classification of aligned chunk pairs."""
from __future__ import annotations
from dataclasses import dataclass
from .aligner import AlignedPair
from .domain_profiles import DomainProfile, get_profile


VERDICT_IDENTICAL = "identical"
VERDICT_SHIFT = "semantic_shift"
VERDICT_CONTRADICTION = "contradiction"
VERDICT_ADDED = "added"
VERDICT_REMOVED = "removed"


@dataclass
class ScoredPair:
    """Scored and classified chunk pair."""
    id: int
    text_a: str | None
    text_b: str | None
    score: float
    verdict: str
    confidence: float
    explanation: str | None = None


def classify(score: float, profile: DomainProfile) -> tuple[str, float]:
    """Classify a similarity score into a verdict + confidence."""
    if score >= profile.identical_threshold:
        confidence = min(1.0, (score - profile.identical_threshold) / (1.0 - profile.identical_threshold + 1e-9) + 0.7)
        return VERDICT_IDENTICAL, round(confidence, 3)
    elif score >= profile.shift_threshold:
        # Map to [0.5, 1.0] confidence range
        confidence = 0.5 + 0.5 * (score - profile.shift_threshold) / (profile.identical_threshold - profile.shift_threshold + 1e-9)
        return VERDICT_SHIFT, round(confidence, 3)
    elif score < profile.contradiction_threshold:
        # Very low similarity → contradiction
        confidence = min(1.0, 1.0 - score / (profile.contradiction_threshold + 1e-9))
        return VERDICT_CONTRADICTION, round(confidence, 3)
    else:
        # Between contradiction_threshold and shift_threshold → semantic shift (moderate)
        band = profile.shift_threshold - profile.contradiction_threshold + 1e-9
        confidence = 0.5 + 0.3 * (score - profile.contradiction_threshold) / band
        return VERDICT_SHIFT, round(confidence, 3)


def score_alignment(
    pairs: list[AlignedPair],
    domain: str = "default",
) -> list[ScoredPair]:
    """Convert aligned pairs to scored pairs with verdicts."""
    profile = get_profile(domain)
    scored: list[ScoredPair] = []

    for i, pair in enumerate(pairs):
        if pair.chunk_a is None:
            scored.append(ScoredPair(
                id=i,
                text_a=None,
                text_b=pair.chunk_b.text if pair.chunk_b else None,
                score=0.0,
                verdict=VERDICT_ADDED,
                confidence=1.0,
            ))
        elif pair.chunk_b is None:
            scored.append(ScoredPair(
                id=i,
                text_a=pair.chunk_a.text,
                text_b=None,
                score=0.0,
                verdict=VERDICT_REMOVED,
                confidence=1.0,
            ))
        else:
            verdict, confidence = classify(pair.score, profile)
            scored.append(ScoredPair(
                id=i,
                text_a=pair.chunk_a.text,
                text_b=pair.chunk_b.text,
                score=round(float(pair.score), 4),
                verdict=verdict,
                confidence=confidence,
            ))

    return scored


def compute_global_score(scored: list[ScoredPair]) -> float:
    """Weighted average score across all pairs."""
    if not scored:
        return 1.0
    total = sum(p.score for p in scored if p.verdict not in (VERDICT_ADDED, VERDICT_REMOVED))
    count = sum(1 for p in scored if p.verdict not in (VERDICT_ADDED, VERDICT_REMOVED))
    if count == 0:
        return 0.0
    return round(total / count, 4)


def compute_delta_index(scored: list[ScoredPair]) -> float:
    """Fraction of chunks whose meaning has drifted."""
    if not scored:
        return 0.0
    drifted = sum(1 for p in scored if p.verdict in (VERDICT_SHIFT, VERDICT_CONTRADICTION, VERDICT_ADDED, VERDICT_REMOVED))
    return round(drifted / len(scored), 4)


def compute_overall(global_score: float, delta_index: float, domain: str = "default") -> str:
    """Map scores to top-level verdict."""
    profile = get_profile(domain)
    if global_score >= profile.identical_threshold and delta_index < 0.1:
        return "identical"
    elif global_score < profile.contradiction_threshold:
        return "contradiction"
    elif global_score < profile.shift_threshold:
        return "semantic_shift"
    else:
        return "semantic_shift"
