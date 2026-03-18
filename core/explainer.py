"""Linguistic heuristic explainer — no LLM required."""
from __future__ import annotations
import re

# Modal verb patterns
_MODALS_STRONG = {"must", "shall", "will", "required", "obliged", "mandatory", "doit", "devra"}
_MODALS_WEAK = {"may", "might", "can", "could", "should", "optional", "peut", "pourrait"}

# Negation patterns
_NEGATIONS = {"not", "no", "never", "neither", "nor", "without", "non", "ne", "pas", "jamais", "aucun"}

# Quantifier patterns
_QUANTIFIER_EXACT = re.compile(r"\b(\d+\.?\d*)\s*(mg|g|ml|l|mcg|µg|iu|days?|hours?|months?|years?|weeks?|jours?|heures?|mois|ans?|%)\b", re.IGNORECASE)
_QUANTIFIER_VAGUE = re.compile(r"\b(reasonable|appropriate|timely|promptly|raisonnable|approprié|rapidement)\b", re.IGNORECASE)

# Temporal precision patterns
_DEADLINE_EXACT = re.compile(r"\b\d{1,4}\s*(days?|hours?|months?|weeks?)\b", re.IGNORECASE)


def _words(text: str) -> set[str]:
    return set(re.findall(r"\b\w+\b", text.lower()))


def _has_negation(text: str) -> bool:
    return bool(_words(text) & _NEGATIONS)


def _modal_type(text: str) -> str:
    words = _words(text)
    if words & _MODALS_STRONG:
        return "strong"
    elif words & _MODALS_WEAK:
        return "weak"
    return "neutral"


def _extract_quantity(text: str) -> str | None:
    m = _QUANTIFIER_EXACT.search(text)
    return m.group(0) if m else None


def explain_pair(text_a: str, text_b: str, verdict: str) -> str | None:
    """Generate a short 1-sentence explanation of the semantic delta.

    Uses pure heuristics (no LLM). Returns None for identical pairs.
    """
    if verdict == "identical":
        return None
    if verdict == "added":
        return "New content added with no equivalent in the original."
    if verdict == "removed":
        return "Content present in the original has been removed."

    explanations: list[str] = []

    # Modal shift
    modal_a = _modal_type(text_a)
    modal_b = _modal_type(text_b)
    if modal_a != modal_b:
        if modal_a == "strong" and modal_b == "weak":
            explanations.append("A firm obligation ('must/shall') becomes conditional or optional ('may/can').")
        elif modal_a == "weak" and modal_b == "strong":
            explanations.append("An optional clause ('may/can') becomes a firm obligation ('must/shall').")
        elif modal_a == "neutral" and modal_b == "strong":
            explanations.append("A neutral statement gains a mandatory qualifier.")
        elif modal_a == "strong" and modal_b == "neutral":
            explanations.append("A mandatory obligation loses its binding qualifier.")

    # Negation flip
    neg_a = _has_negation(text_a)
    neg_b = _has_negation(text_b)
    if neg_a != neg_b:
        if not neg_a and neg_b:
            explanations.append("A positive statement is negated in the new version.")
        else:
            explanations.append("A negation is removed — the statement becomes affirmative.")

    # Quantity changes
    qty_a = _extract_quantity(text_a)
    qty_b = _extract_quantity(text_b)
    if qty_a and qty_b and qty_a.lower() != qty_b.lower():
        explanations.append(f"A specific quantity changes: '{qty_a}' → '{qty_b}'.")
    elif qty_a and not qty_b:
        if _QUANTIFIER_VAGUE.search(text_b):
            explanations.append(f"A precise deadline ('{qty_a}') becomes vague ('reasonable timeframe').")
        else:
            explanations.append(f"A specific quantity ('{qty_a}') is removed.")
    elif not qty_a and qty_b:
        explanations.append(f"A new specific quantity ('{qty_b}') is introduced.")

    # Contradiction fallback
    if not explanations:
        if verdict == "contradiction":
            explanations.append("The two passages convey contradictory or opposite meanings.")
        else:
            explanations.append("The wording has changed in a way that shifts the overall meaning.")

    return " ".join(explanations)


def explain_all(scored_pairs: list) -> list:
    """Add explanations to all non-identical scored pairs. Returns the same list (mutated)."""
    for pair in scored_pairs:
        if pair.verdict != "identical" and pair.text_a and pair.text_b:
            pair.explanation = explain_pair(pair.text_a, pair.text_b, pair.verdict)
        elif pair.verdict in ("added", "removed"):
            pair.explanation = explain_pair(pair.text_a or "", pair.text_b or "", pair.verdict)
    return scored_pairs
