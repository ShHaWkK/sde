# Semantic Diff Engine

**The semantic layer missing from your pipeline.**

`git diff` tells you what characters changed. SDE tells you what *meaning* changed.

```bash
pip install semantic-diff
semantic-diff diff v1.txt v2.txt --domain legal --explain
```

```
╭─────────────────────────────────────────────────────╮
│ Overall: SEMANTIC_SHIFT | Score: ███████░░░ 0.72     │
│ Delta index: 66.7% of content changed | 142ms        │
╰─────────────────────────────────────────────────────╯
┌─────────────────────────┬─────────────────────────┬────────────┬────────────┐
│ Version A               │ Version B               │ Score      │ Verdict    │
├─────────────────────────┼─────────────────────────┼────────────┼────────────┤
│ Vendor shall deliver    │ Vendor may deliver at   │ ████░ 0.74 │ ◐ shift    │
│ within 30 days.         │ their convenience.      │            │            │
│ Payment must be made    │ Payment may be made in  │ ███░░ 0.68 │ ◐ shift    │
│ in full.                │ installments.           │            │            │
│ Liability is limited    │ Party is liable for all │ ██░░░ 0.32 │ ✕ contra   │
│ to direct damages.      │ damages including punit │            │            │
└─────────────────────────┴─────────────────────────┴────────────┴────────────┘
```

## Why SDE?

`git diff` was designed in 1974 for line-by-line text comparison. It cannot tell you that:
- A contract clause changed from "shall" (mandatory) to "may" (optional)
- A medical dosage was quietly doubled
- A news article was rewritten with opposite spin while preserving facts

SDE fills this gap. It operates on **meaning**, not characters.

## Installation

```bash
pip install semantic-diff          # CLI + API + Python SDK
npm install @semantic-diff/core    # TypeScript SDK
docker compose up                  # API + playground
```

## Quick Start

### CLI

```bash
semantic-diff diff before.txt after.txt --domain legal --explain
semantic-diff diff a.txt b.txt --json | jq .overall
semantic-diff watch contract_v1.txt contract_v2.txt  # live re-diff on save
semantic-diff serve                                   # start API on :8000
```

### API

```bash
curl -X POST http://localhost:8000/diff \
  -H "Content-Type: application/json" \
  -d '{"text_a": "You must pay within 30 days.", "text_b": "You may pay at your convenience.", "domain": "legal", "options": {"explain": true}}'
```

### TypeScript SDK

```typescript
import { SemanticDiff } from '@semantic-diff/core'

const sde = new SemanticDiff({ baseUrl: 'http://localhost:8000' })
const result = await sde.diff(textA, textB, { domain: 'legal', explain: true })

console.log(result.overall)       // "semantic_shift"
console.log(result.global_score)  // 0.7234
console.log(result.delta_index)   // 0.6667

for (const chunk of result.chunks) {
  if (chunk.verdict !== 'identical') {
    console.log(`[${chunk.verdict}] ${chunk.explanation}`)
  }
}
```

### GitHub Action

```yaml
- name: Semantic diff check
  uses: semantic-diff/sde-action@v1
  with:
    file_a: docs/v1/TERMS.md
    file_b: docs/v2/TERMS.md
    domain: legal
    fail_on: contradiction
    explain: true
```

## Use Cases

| Domain | Problem | SDE Command |
|--------|---------|-------------|
| Legal | Detect silent contract changes | `semantic-diff diff v1.md v2.md --domain legal` |
| Medical | Flag dosage or contraindication changes | `semantic-diff diff rx_old.txt rx_new.txt --domain medical` |
| Code | Detect logic changes across refactors | `semantic-diff diff old.py new.py --domain code` |
| Journalism | Identify spin vs. factual changes | `semantic-diff diff draft1.txt draft2.txt --domain journalism` |
| AI pipelines | Evaluate LLM output drift | `semantic-diff batch pairs.jsonl --output results.jsonl` |

## Architecture

```
Input texts
    → Chunker (sentence | paragraph | sliding_window)
    → Embedder (sentence-transformers | OpenAI | Ollama)
    → N×M Similarity Matrix
    → Hungarian Algorithm (optimal alignment)
    → Domain-aware scorer (thresholds per domain)
    → Explainer (linguistic heuristics, no LLM)
    → DiffResult {overall, global_score, delta_index, chunks[]}
```

## Open Standard

SDE is built around a **formal specification** (`spec/SDE-SPEC-v1.md`). Any team can implement SDE in Go, Rust, Java, or any other language by following the spec alone.

The output format is standardized — tools can consume SDE results regardless of which implementation produced them.

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md). PRs welcome.

## License

MIT

---

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)
![npm](https://img.shields.io/badge/npm-%40semantic--diff%2Fcore-red)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)
