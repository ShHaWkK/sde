# Contributing to SDE

## Development Setup

```bash
git clone https://github.com/semantic-diff/sde
cd sde
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/unit/          # fast unit tests
pytest tests/integration/   # requires model download (~80MB first run)
pytest tests/e2e/           # full API tests
pytest tests/               # all tests
```

## Project Structure

- `core/` — pure Python engine, no API dependencies
- `api/` — FastAPI application
- `cli/` — Typer CLI
- `sdk/` — language SDKs
- `spec/` — formal protocol specification
- `benchmarks/` — evaluation datasets and runner
- `tests/` — unit, integration, e2e

## Adding a New Domain

1. Add a new `DomainProfile` in `core/domain_profiles.py`
2. Add threshold justification in `docs/DOMAINS.md`
3. Create benchmark fixtures in `benchmarks/datasets/<domain>/`
4. Add the domain to the Pydantic enum in `api/schemas.py`

## Implementing SDE in Another Language

See `spec/SDE-SPEC-v1.md` for the full protocol specification.
The spec is self-contained — you can implement SDE in Go, Rust, Java, etc.
by following the spec alone.

Key requirements for conformance:
1. Accept the input format defined in §2
2. Return the output format defined in §3
3. Apply domain thresholds from §4
4. Use optimal (Hungarian) alignment from §5

## Submitting Changes

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Write tests for your changes
4. Run the full test suite: `pytest tests/`
5. Open a pull request with a clear description

## Reporting Issues

Please include:
- Python version and OS
- The input texts (or a minimal repro)
- Expected vs. actual output
- `semantic-diff diff a.txt b.txt --json` output
