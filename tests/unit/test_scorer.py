"""Unit tests for scorer module."""
import pytest
from core.scorer import classify, compute_delta_index, compute_global_score, compute_overall, VERDICT_IDENTICAL, VERDICT_SHIFT, VERDICT_CONTRADICTION, VERDICT_ADDED, VERDICT_REMOVED
from core.domain_profiles import get_profile
from core.scorer import ScoredPair


def _make_pair(verdict: str, score: float = 0.5) -> ScoredPair:
    return ScoredPair(id=0, text_a="a", text_b="b", score=score, verdict=verdict, confidence=0.9)


def test_classify_identical():
    profile = get_profile("default")
    verdict, conf = classify(0.95, profile)
    assert verdict == VERDICT_IDENTICAL
    assert conf > 0.5


def test_classify_shift():
    profile = get_profile("default")
    verdict, conf = classify(0.80, profile)
    assert verdict == VERDICT_SHIFT


def test_classify_contradiction():
    profile = get_profile("default")
    verdict, conf = classify(0.20, profile)
    assert verdict == VERDICT_CONTRADICTION


def test_delta_index_zero():
    pairs = [_make_pair(VERDICT_IDENTICAL, 0.95), _make_pair(VERDICT_IDENTICAL, 0.97)]
    assert compute_delta_index(pairs) == 0.0


def test_delta_index_full():
    pairs = [_make_pair(VERDICT_CONTRADICTION, 0.1), _make_pair(VERDICT_SHIFT, 0.6)]
    assert compute_delta_index(pairs) == 1.0


def test_delta_index_partial():
    pairs = [_make_pair(VERDICT_IDENTICAL, 0.95), _make_pair(VERDICT_SHIFT, 0.7), _make_pair(VERDICT_IDENTICAL, 0.93)]
    assert compute_delta_index(pairs) == pytest.approx(1 / 3, abs=0.01)


def test_global_score_ignores_added_removed():
    pairs = [
        _make_pair(VERDICT_IDENTICAL, 0.95),
        _make_pair(VERDICT_ADDED, 0.0),
        _make_pair(VERDICT_REMOVED, 0.0),
    ]
    score = compute_global_score(pairs)
    assert score == pytest.approx(0.95, abs=0.01)


def test_compute_overall_identical():
    assert compute_overall(0.97, 0.0, "default") == "identical"


def test_compute_overall_contradiction():
    assert compute_overall(0.1, 0.9, "default") == "contradiction"


def test_legal_profile_stricter():
    legal = get_profile("legal")
    default = get_profile("default")
    assert legal.identical_threshold > default.identical_threshold
