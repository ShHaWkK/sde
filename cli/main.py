"""Semantic Diff Engine CLI."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="semantic-diff",
    help="Semantic Diff Engine — the semantic layer for your pipeline.",
    no_args_is_help=True,
)
console = Console()


def _load_comparator(model: str):
    from core.comparator import SemanticComparator
    return SemanticComparator(model_name=model)


@app.command()
def diff(
    file_a: Path = typer.Argument(..., help="Original file"),
    file_b: Path = typer.Argument(..., help="Revised file"),
    domain: str = typer.Option("default", "--domain", "-d", help="Domain profile: default|legal|medical|code|journalism"),
    explain: bool = typer.Option(False, "--explain", "-e", help="Generate natural-language explanations"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
    html: Optional[Path] = typer.Option(None, "--html", help="Export HTML report to this path"),
    model: str = typer.Option("all-MiniLM-L6-v2", "--model", "-m", help="Embedding model"),
    strategy: str = typer.Option("auto", "--strategy", "-s", help="Chunking: auto|sentence|paragraph|sliding_window"),
):
    """Compare two files semantically."""
    if not file_a.exists():
        console.print(f"[red]File not found: {file_a}[/]")
        raise typer.Exit(1)
    if not file_b.exists():
        console.print(f"[red]File not found: {file_b}[/]")
        raise typer.Exit(1)

    text_a = file_a.read_text(encoding="utf-8")
    text_b = file_b.read_text(encoding="utf-8")

    comparator = _load_comparator(model)
    result = comparator.diff(text_a, text_b, domain=domain, chunking_strategy=strategy, explain=explain)

    if output_json:
        data = {
            "sde_version": result.sde_version,
            "overall": result.overall,
            "global_score": result.global_score,
            "delta_index": result.delta_index,
            "chunks": [
                {
                    "id": c.id,
                    "a": c.text_a,
                    "b": c.text_b,
                    "score": c.score,
                    "verdict": c.verdict,
                    "explanation": c.explanation,
                    "confidence": c.confidence,
                }
                for c in result.chunks
            ],
            "metadata": {
                "model": result.model,
                "processing_ms": result.processing_ms,
                "chunk_count_a": result.chunk_count_a,
                "chunk_count_b": result.chunk_count_b,
            },
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    from cli.formatter import print_result, export_html
    print_result(result, explain=explain)

    if html:
        export_html(result, html)


@app.command()
def batch(
    input_file: Path = typer.Argument(..., help="JSONL file with pairs: {text_a, text_b, domain?, options?}"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output JSONL file"),
    model: str = typer.Option("all-MiniLM-L6-v2", "--model", "-m"),
):
    """Diff multiple pairs from a JSONL file."""
    if not input_file.exists():
        console.print(f"[red]File not found: {input_file}[/]")
        raise typer.Exit(1)

    comparator = _load_comparator(model)
    out = sys.stdout if not output_file else output_file.open("w", encoding="utf-8")

    with input_file.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                result = comparator.diff(
                    item["text_a"],
                    item["text_b"],
                    domain=item.get("domain", "default"),
                    explain=item.get("explain", False),
                )
                record = {
                    "id": item.get("id", i),
                    "overall": result.overall,
                    "global_score": result.global_score,
                    "delta_index": result.delta_index,
                    "processing_ms": result.processing_ms,
                }
                print(json.dumps(record), file=out)
            except Exception as e:
                print(json.dumps({"id": item.get("id", i), "error": str(e)}), file=out)

    if output_file:
        out.close()
        console.print(f"[green]Results written to {output_file}[/]")


@app.command()
def watch(
    file_a: Path = typer.Argument(..., help="Original file"),
    file_b: Path = typer.Argument(..., help="Revised file (watched for changes)"),
    domain: str = typer.Option("default", "--domain", "-d"),
    explain: bool = typer.Option(False, "--explain", "-e"),
    model: str = typer.Option("all-MiniLM-L6-v2", "--model", "-m"),
    interval: float = typer.Option(2.0, "--interval", "-i", help="Poll interval in seconds"),
):
    """Re-diff every time file_b is saved. Ctrl+C to stop."""
    import os
    comparator = _load_comparator(model)
    from cli.formatter import print_result
    last_mtime = None

    console.print(f"[bold]Watching {file_b} for changes... (Ctrl+C to stop)[/]")
    try:
        while True:
            try:
                mtime = os.path.getmtime(file_b)
                if mtime != last_mtime:
                    last_mtime = mtime
                    console.clear()
                    console.print(f"[dim]{time.strftime('%H:%M:%S')} — change detected[/]")
                    text_a = file_a.read_text(encoding="utf-8")
                    text_b = file_b.read_text(encoding="utf-8")
                    result = comparator.diff(text_a, text_b, domain=domain, explain=explain)
                    print_result(result, explain=explain)
            except FileNotFoundError:
                pass
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[dim]Watch stopped.[/]")


@app.command()
def benchmark(
    dataset: str = typer.Option("all", "--dataset", help="Dataset: all|legal|medical|code|journalism|ai_outputs"),
    model: str = typer.Option("all-MiniLM-L6-v2", "--model", "-m"),
):
    """Run benchmark against annotated fixtures."""
    bench_path = Path(__file__).parent.parent / "benchmarks"
    script = bench_path / "run_benchmark.py"
    if not script.exists():
        console.print("[red]Benchmark script not found.[/]")
        raise typer.Exit(1)
    import subprocess
    args = [sys.executable, str(script), "--dataset", dataset, "--model", model]
    subprocess.run(args)


@app.command()
def serve(
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (development)"),
):
    """Start the SDE API server."""
    import uvicorn
    console.print(f"[green]Starting SDE API on http://{host}:{port}[/]")
    uvicorn.run("api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
