"""Unit tests for the explainer module."""
import pytest
from core.explainer import explain_pair


def test_explain_modal_shift():
    a = "The vendor shall deliver within 30 days."
    b = "The vendor may deliver within a reasonable timeframe."
    exp = explain_pair(a, b, "semantic_shift")
    assert exp is not None
    assert len(exp) > 10


def test_explain_negation_flip():
    a = "The contractor shall not subcontract any work."
    b = "The contractor may subcontract work freely."
    exp = explain_pair(a, b, "contradiction")
    assert exp is not None


def test_explain_quantity_change():
    a = "Administer 10mg twice daily."
    b = "Administer 100mg twice daily."
    exp = explain_pair(a, b, "semantic_shift")
    assert "10mg" in exp or "100mg" in exp or "quantity" in exp.lower()


def test_explain_added():
    exp = explain_pair("", "New clause added.", "added")
    assert "added" in exp.lower() or "new content" in exp.lower()


def test_explain_removed():
    exp = explain_pair("Removed clause.", "", "removed")
    assert "removed" in exp.lower()


def test_explain_identical_returns_none():
    exp = explain_pair("Same text.", "Same text.", "identical")
    assert exp is None


def test_explain_contradiction_fallback():
    a = "The sky is blue."
    b = "The ocean is deep."
    exp = explain_pair(a, b, "contradiction")
    assert exp is not None
    assert len(exp) > 5
