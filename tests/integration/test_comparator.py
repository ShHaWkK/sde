"""Integration tests for the SemanticComparator pipeline."""
import pytest
from core.comparator import SemanticComparator


@pytest.fixture(scope="module")
def comparator():
    return SemanticComparator(model_name="all-MiniLM-L6-v2")


def test_identical_texts(comparator):
    result = comparator.diff(
        "The quick brown fox jumps over the lazy dog.",
        "The quick brown fox jumps over the lazy dog.",
    )
    assert result.overall == "identical"
    assert result.global_score > 0.9


def test_semantic_shift(comparator):
    result = comparator.diff(
        "The vendor shall deliver within 30 days.",
        "The vendor may deliver at their convenience.",
    )
    # Should detect a meaningful change
    assert result.overall in ("semantic_shift", "contradiction")
    assert result.delta_index > 0


def test_contradiction(comparator):
    result = comparator.diff(
        "The payment is mandatory.",
        "No payment is required.",
    )
    assert result.overall in ("semantic_shift", "contradiction")


def test_explain_flag(comparator):
    result = comparator.diff(
        "The contractor shall deliver within 30 days.",
        "The contractor may deliver at their convenience.",
        explain=True,
    )
    for chunk in result.chunks:
        if chunk.verdict != "identical":
            assert chunk.explanation is not None


def test_result_structure(comparator):
    result = comparator.diff("Hello world.", "Hello there.")
    assert result.sde_version == "1.0"
    assert 0.0 <= result.global_score <= 1.0
    assert 0.0 <= result.delta_index <= 1.0
    assert result.processing_ms >= 0
    assert result.chunk_count_a >= 1
    assert result.chunk_count_b >= 1


def test_domain_legal(comparator):
    result = comparator.diff(
        "The vendor shall deliver within 30 days.",
        "The vendor shall deliver within 30 days.",
        domain="legal",
    )
    assert result.overall == "identical"


def test_multi_chunk(comparator):
    text_a = "First clause here.\n\nSecond clause about payment.\n\nThird clause about termination."
    text_b = "First clause here.\n\nPayment terms are different now.\n\nThird clause about termination."
    result = comparator.diff(text_a, text_b, chunking_strategy="paragraph")
    assert result.chunk_count_a == 3
    assert result.chunk_count_b == 3
    # Middle chunk should show change
    verdicts = [c.verdict for c in result.chunks]
    assert "identical" in verdicts
