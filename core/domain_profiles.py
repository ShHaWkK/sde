"""Domain-specific threshold profiles for SDE."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class DomainProfile:
    """Similarity thresholds and alignment parameters for a domain."""
    name: str
    # Cosine similarity thresholds
    identical_threshold: float    # >= this → identical
    shift_threshold: float        # >= this (and < identical) → semantic_shift
    contradiction_threshold: float  # < this → contradiction (must be <= shift)
    # Alignment
    alignment_threshold: float    # min similarity to consider chunks aligned
    # Description (for documentation)
    rationale: str


_PROFILES: dict[str, DomainProfile] = {
    "default": DomainProfile(
        name="default",
        identical_threshold=0.92,
        shift_threshold=0.75,
        contradiction_threshold=0.40,
        alignment_threshold=0.15,
        rationale="Balanced thresholds for general-purpose text.",
    ),
    "legal": DomainProfile(
        name="legal",
        identical_threshold=0.96,
        shift_threshold=0.85,
        contradiction_threshold=0.50,
        alignment_threshold=0.20,
        rationale=(
            "Legal texts require very high confidence for 'identical' because "
            "small word changes (e.g. 'shall' → 'may', '30 days' → 'reasonable time') "
            "carry significant legal weight. Contradiction threshold is also higher "
            "because semantically opposite clauses are a critical red flag."
        ),
    ),
    "medical": DomainProfile(
        name="medical",
        identical_threshold=0.95,
        shift_threshold=0.82,
        contradiction_threshold=0.45,
        alignment_threshold=0.18,
        rationale=(
            "Medical texts (prescriptions, dosages, contraindications) require "
            "high precision. A dosage change that might seem minor textually can "
            "be clinically significant, so the identical threshold is strict."
        ),
    ),
    "code": DomainProfile(
        name="code",
        identical_threshold=0.90,
        shift_threshold=0.70,
        contradiction_threshold=0.35,
        alignment_threshold=0.12,
        rationale=(
            "Code comparison allows slightly more variation: refactored code with "
            "the same logic may use different variable names or structure. The "
            "contradiction threshold is low because it's common to have low "
            "embedding similarity between semantically different code functions."
        ),
    ),
    "journalism": DomainProfile(
        name="journalism",
        identical_threshold=0.91,
        shift_threshold=0.72,
        contradiction_threshold=0.38,
        alignment_threshold=0.13,
        rationale=(
            "News articles can be rewritten with different framing while preserving "
            "facts. A moderate identical threshold captures paraphrasing as non-identical "
            "while the shift threshold detects spin changes."
        ),
    ),
}


def get_profile(domain: str) -> DomainProfile:
    """Return the threshold profile for the given domain."""
    return _PROFILES.get(domain, _PROFILES["default"])


def list_domains() -> list[str]:
    return list(_PROFILES.keys())
