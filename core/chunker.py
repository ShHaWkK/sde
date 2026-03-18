"""Semantic chunking strategies for SDE."""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """A single semantic unit of text."""
    id: int
    text: str
    source: str  # "a" or "b"
    start_char: int
    end_char: int


def _ensure_nltk():
    import nltk
    for pkg in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{pkg}")
        except LookupError:
            nltk.download(pkg, quiet=True)


def chunk_sentence(text: str, source: str = "a", min_words: int = 5) -> list[Chunk]:
    """Split by sentences; merge short sentences (<min_words) with the next."""
    if not text.strip():
        return []
    _ensure_nltk()
    import nltk
    raw_sentences = [s for s in nltk.sent_tokenize(text) if s.strip()]
    merged: list[str] = []
    buf = ""
    for sent in raw_sentences:
        if buf:
            candidate = buf + " " + sent
        else:
            candidate = sent
        if len(candidate.split()) < min_words and len(raw_sentences) > 1:
            buf = candidate
        else:
            if buf and len(buf.split()) < min_words:
                # flush short buffer by appending to last merged if possible
                if merged:
                    merged[-1] += " " + buf
                else:
                    merged.append(buf)
                buf = sent
            else:
                if buf:
                    merged.append(buf)
                    buf = ""
                merged.append(candidate) if not buf else None
                buf = ""
    if buf:
        if merged:
            merged[-1] += " " + buf
        else:
            merged.append(buf)

    return _to_chunks(merged, text, source)


def chunk_paragraph(text: str, source: str = "a") -> list[Chunk]:
    """Split on blank lines (\\n\\n)."""
    if not text.strip():
        return []
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return _to_chunks(paras, text, source)


def chunk_sliding_window(text: str, source: str = "a", window: int = 3, step: int = 1) -> list[Chunk]:
    """Overlapping windows of `window` sentences, stepping by `step`."""
    if not text.strip():
        return []
    _ensure_nltk()
    import nltk
    sentences = [s for s in nltk.sent_tokenize(text) if s.strip()]
    windows: list[str] = []
    for i in range(0, len(sentences), step):
        w = sentences[i : i + window]
        if w:
            windows.append(" ".join(w))
    return _to_chunks(windows, text, source)


def _to_chunks(parts: list[str], original: str, source: str) -> list[Chunk]:
    chunks = []
    search_start = 0
    for i, part in enumerate(parts):
        start = original.find(part, search_start)
        if start == -1:
            start = search_start
        end = start + len(part)
        search_start = end
        chunks.append(Chunk(id=i, text=part, source=source, start_char=start, end_char=end))
    return chunks


def auto_strategy(text: str) -> str:
    """Auto-select chunking strategy based on document length."""
    words = len(text.split())
    newlines = text.count("\n\n")
    if newlines >= 3:
        return "paragraph"
    elif words > 500:
        return "sliding_window"
    else:
        return "sentence"


def chunk_text(
    text: str,
    source: str = "a",
    strategy: str = "auto",
) -> list[Chunk]:
    """Main entry point. strategy: 'sentence'|'paragraph'|'sliding_window'|'auto'."""
    if strategy == "auto":
        strategy = auto_strategy(text)
    if strategy == "sentence":
        return chunk_sentence(text, source)
    elif strategy == "paragraph":
        return chunk_paragraph(text, source)
    elif strategy == "sliding_window":
        return chunk_sliding_window(text, source)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
