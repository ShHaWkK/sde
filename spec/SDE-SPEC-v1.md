# SDE-SPEC-v1 — Semantic Diff Engine Specification

**Version:** 1.0
**Status:** Draft
**License:** MIT

---

## Overview

The Semantic Diff Engine (SDE) is an open protocol for computing **semantic differences** between text documents. Unlike character-level or token-level diff algorithms (e.g., `git diff`, `diff`), SDE operates on **meaning**: it detects when two texts say the same thing differently, when a subtle meaning shift has occurred, or when two passages actively contradict each other.

SDE is designed as a **primitive** — a composable building block that any pipeline processing natural language or code can integrate.

---

## 1. Protocol Version

All requests and responses carry a `version` / `sde_version` field set to `"1.0"`.
Implementations MUST reject requests with incompatible versions.

---

## 2. Input Format

```json
{
  "version": "1.0",
  "text_a": "<string — original text>",
  "text_b": "<string — revised text>",
  "domain": "default",
  "options": {
    "chunking_strategy": "auto",
    "embedding_model": "all-MiniLM-L6-v2",
    "explain": false,
    "language": "en"
  }
}
```

### 2.1 Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `version` | string | No | `"1.0"` | Protocol version |
| `text_a` | string | **Yes** | — | The original (reference) text |
| `text_b` | string | **Yes** | — | The revised text to compare against |
| `domain` | enum | No | `"default"` | Domain profile affecting thresholds |
| `options.chunking_strategy` | enum | No | `"auto"` | How to split texts into chunks |
| `options.embedding_model` | string | No | `"all-MiniLM-L6-v2"` | Embedding model identifier |
| `options.explain` | boolean | No | `false` | Include natural-language explanations |
| `options.language` | string (ISO 639-1) | No | `"en"` | Text language hint |

### 2.2 Domain Values

| Value | Description |
|-------|-------------|
| `default` | General-purpose text |
| `legal` | Legal documents, contracts |
| `medical` | Medical records, prescriptions |
| `code` | Source code |
| `journalism` | News articles, reports |

### 2.3 Chunking Strategy Values

| Value | Description |
|-------|-------------|
| `sentence` | Split on sentence boundaries, merge very short sentences |
| `paragraph` | Split on blank lines (`\n\n`) |
| `sliding_window` | Overlapping windows of N sentences |
| `auto` | Implementation selects best strategy based on document length |

---

## 3. Output Format

```json
{
  "sde_version": "1.0",
  "overall": "semantic_shift",
  "global_score": 0.7823,
  "delta_index": 0.3333,
  "chunks": [
    {
      "id": 0,
      "a": "The vendor shall deliver within 30 days.",
      "b": "The vendor may deliver within a reasonable timeframe.",
      "score": 0.7412,
      "verdict": "semantic_shift",
      "explanation": "A firm obligation ('shall') becomes conditional ('may'). A precise deadline ('30 days') becomes vague ('reasonable timeframe').",
      "confidence": 0.8821
    }
  ],
  "metadata": {
    "model": "all-MiniLM-L6-v2",
    "processing_ms": 142,
    "chunk_count_a": 3,
    "chunk_count_b": 3
  }
}
```

### 3.1 Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `sde_version` | string | Protocol version used |
| `overall` | enum | Document-level verdict |
| `global_score` | float [0.0–1.0] | Weighted average semantic similarity |
| `delta_index` | float [0.0–1.0] | Fraction of chunks that changed meaning |
| `chunks` | array | Per-chunk comparison results |
| `metadata` | object | Processing metadata |

### 3.2 Overall Verdict Values

| Value | Meaning |
|-------|---------|
| `identical` | Texts are semantically equivalent (same meaning, possibly different wording) |
| `semantic_shift` | One or more chunks show meaningful drift |
| `contradiction` | Texts contain directly opposing claims |
| `unrelated` | Texts share no meaningful semantic overlap |

### 3.3 Chunk Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Zero-based chunk index |
| `a` | string \| null | Chunk from text_a (null if chunk is added in b) |
| `b` | string \| null | Chunk from text_b (null if chunk was removed from a) |
| `score` | float [0.0–1.0] | Cosine similarity between embeddings |
| `verdict` | enum | Chunk-level classification |
| `explanation` | string \| null | Natural-language explanation (only if `explain=true`) |
| `confidence` | float [0.0–1.0] | Model's confidence in the verdict |

### 3.4 Chunk Verdict Values

| Value | Meaning |
|-------|---------|
| `identical` | Chunks have the same meaning |
| `semantic_shift` | Meaning has drifted but not reversed |
| `contradiction` | Chunks express opposite claims |
| `added` | Chunk exists only in text_b (new content) |
| `removed` | Chunk exists only in text_a (deleted content) |

---

## 4. Domain Threshold Profiles

Each domain defines three cosine-similarity thresholds that govern classification:

| Domain | identical ≥ | shift ≥ | contradiction < | Rationale |
|--------|-------------|---------|-----------------|-----------|
| `default` | 0.92 | 0.75 | 0.40 | Balanced for general text |
| `legal` | 0.96 | 0.85 | 0.50 | Single word changes carry legal weight |
| `medical` | 0.95 | 0.82 | 0.45 | Clinical precision required |
| `code` | 0.90 | 0.70 | 0.35 | Refactored code has natural variation |
| `journalism` | 0.91 | 0.72 | 0.38 | Spin vs. facts distinction |

### 4.1 Threshold Semantics

```
score >= identical_threshold    → verdict = "identical"
score >= shift_threshold        → verdict = "semantic_shift"
score < contradiction_threshold → verdict = "contradiction"
otherwise                       → verdict = "semantic_shift"
```

### 4.2 Legal Domain Rationale

Legal documents use the highest thresholds because:
- Modal verbs matter: "shall" vs. "may" changes binding force
- Quantifiers matter: "30 days" vs. "reasonable time" is legally distinct
- Scope words matter: "including" vs. "limited to" inverts applicability
- A 0.96 identical threshold ensures even small but legally significant changes are flagged

### 4.3 Medical Domain Rationale

Medical texts require high precision because:
- Dosage changes (e.g., "10mg" → "100mg") may embed similarly but are dangerous
- Contraindications: "not recommended for" → "contraindicated in" is a clinical shift
- High contradiction threshold (0.45) catches dosage inversions

---

## 5. Alignment Algorithm

Implementations MUST use optimal alignment (Hungarian algorithm) rather than greedy nearest-neighbor:

1. Compute NxM cosine similarity matrix between all chunk pairs
2. Apply `scipy.optimize.linear_sum_assignment` (or equivalent) to find optimal 1-to-1 matching
3. Discard matches below `alignment_threshold` (domain-specific)
4. Unmatched chunks from A → verdict `removed`
5. Unmatched chunks from B → verdict `added`

This ensures global optimality: a chunk in A matches the best available chunk in B even if there are closer local matches.

---

## 6. Delta Index

```
delta_index = count(chunks where verdict in {semantic_shift, contradiction, added, removed})
              ────────────────────────────────────────────────────────────────────────────
                                    total chunk count
```

Range: 0.0 (no change) → 1.0 (everything changed).

---

## 7. Explainer Heuristics

When `explain=true`, implementations SHOULD generate a 1-sentence natural-language explanation using linguistic heuristics (no LLM required):

- **Modal shift**: detect strong modals (must/shall/doit) vs. weak modals (may/can/peut)
- **Negation flip**: detect presence/absence of negation words (not/no/never/non/pas)
- **Quantity change**: detect numeric quantities with units and flag changes
- **Vagueness shift**: detect shift from precise quantity to vague qualifier (reasonable, appropriate)
- **Fallback**: generic explanation for contradiction or semantic shift

Explanations MUST be in the same language as the input text when possible.

---

## 8. HTTP API

### 8.1 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/spec` | Return this specification |
| POST | `/diff` | Compare two texts |
| POST | `/diff/stream` | Stream chunks via SSE |
| POST | `/batch` | Compare multiple pairs |

### 8.2 POST /diff

Request body: Input Format (§2)
Response body: Output Format (§3)
Status codes: 200 OK, 400 Bad Request, 429 Too Many Requests, 500 Internal Server Error

### 8.3 POST /diff/stream

Server-Sent Events stream. Each event is a JSON-encoded `ChunkResult` object.
Final event: `{"event": "done", "overall": "...", "global_score": ..., "delta_index": ...}`

### 8.4 POST /batch

```json
{
  "items": [
    {"id": "clause-1", "text_a": "...", "text_b": "...", "domain": "legal"},
    {"id": "clause-2", "text_a": "...", "text_b": "..."}
  ]
}
```

Response:
```json
{
  "results": [
    {"id": "clause-1", "result": {/* DiffResponse */}, "error": null},
    {"id": "clause-2", "result": null, "error": "error message"}
  ],
  "total": 2,
  "failed": 0
}
```

---

## 9. Conformance

An implementation is SDE-conformant if:
1. It accepts the input format defined in §2
2. It returns the output format defined in §3
3. It applies domain-appropriate thresholds as defined in §4
4. It uses optimal (Hungarian) alignment as defined in §5
5. It correctly computes delta_index as defined in §6
6. It exposes the HTTP API defined in §8

Implementations MAY use any embedding model; they SHOULD document which model is used in `metadata.model`.

---

## 10. Versioning

- Minor changes (new optional fields): increment patch version (1.0.1)
- Breaking changes (field renames, semantic changes): increment major version (2.0)
- The `sde_version` field in responses reflects the spec version implemented

---

*SDE-SPEC-v1 — Open specification, MIT License — Contributions welcome*
