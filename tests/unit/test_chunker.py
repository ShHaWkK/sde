"""Unit tests for the chunker module."""
import pytest
from core.chunker import chunk_sentence, chunk_paragraph, chunk_sliding_window, chunk_text, auto_strategy


def test_chunk_sentence_basic():
    text = "The cat sat on the mat. The dog ran in the park. The bird flew over the hill."
    chunks = chunk_sentence(text)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.text
        assert c.source == "a"


def test_chunk_paragraph():
    text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
    chunks = chunk_paragraph(text)
    assert len(chunks) == 3
    assert chunks[0].text == "First paragraph here."
    assert chunks[1].text == "Second paragraph here."


def test_chunk_paragraph_source():
    text = "Para one.\n\nPara two."
    chunks = chunk_paragraph(text, source="b")
    assert all(c.source == "b" for c in chunks)


def test_chunk_ids_sequential():
    text = "Sentence one. Sentence two. Sentence three."
    chunks = chunk_sentence(text)
    assert [c.id for c in chunks] == list(range(len(chunks)))


def test_chunk_sliding_window():
    text = "A. B. C. D. E. F."
    chunks = chunk_sliding_window(text, window=2, step=1)
    assert len(chunks) >= 3


def test_auto_strategy_paragraph():
    text = "Para one.\n\nPara two.\n\nPara three.\n\nPara four."
    assert auto_strategy(text) == "paragraph"


def test_auto_strategy_short():
    text = "Short text here. This is brief."
    assert auto_strategy(text) == "sentence"


def test_chunk_text_auto():
    text = "One sentence here. Another sentence follows."
    chunks = chunk_text(text, strategy="auto")
    assert len(chunks) >= 1


def test_chunk_text_invalid_strategy():
    with pytest.raises(ValueError):
        chunk_text("text", strategy="invalid_strategy")


def test_empty_text():
    chunks = chunk_sentence("")
    assert chunks == []
