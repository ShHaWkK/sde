"""Rich terminal formatter and HTML exporter for SDE results."""
from __future__ import annotations
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import BarColumn, Progress
from rich import box
from rich.text import Text
from rich.panel import Panel
from rich.markup import escape

from core.comparator import DiffResult
from core.scorer import VERDICT_IDENTICAL, VERDICT_SHIFT, VERDICT_CONTRADICTION, VERDICT_ADDED, VERDICT_REMOVED

console = Console()

_VERDICT_COLORS = {
    VERDICT_IDENTICAL: "green",
    VERDICT_SHIFT: "yellow",
    VERDICT_CONTRADICTION: "red",
    VERDICT_ADDED: "blue",
    VERDICT_REMOVED: "dim",
}

_VERDICT_BADGES = {
    VERDICT_IDENTICAL: "[green]● identical[/]",
    VERDICT_SHIFT: "[yellow]◐ shift[/]",
    VERDICT_CONTRADICTION: "[red]✕ contradiction[/]",
    VERDICT_ADDED: "[blue]+ added[/]",
    VERDICT_REMOVED: "[dim]- removed[/]",
}

_OVERALL_COLORS = {
    "identical": "green",
    "semantic_shift": "yellow",
    "contradiction": "red",
    "unrelated": "magenta",
}


def _truncate(text: str | None, max_len: int = 60) -> str:
    if not text:
        return "[dim]—[/]"
    text = text.replace("\n", " ")
    if len(text) > max_len:
        return escape(text[:max_len - 1]) + "…"
    return escape(text)


def _score_bar(score: float, width: int = 10) -> str:
    filled = round(score * width)
    bar = "█" * filled + "░" * (width - filled)
    color = "green" if score >= 0.92 else ("yellow" if score >= 0.75 else "red")
    return f"[{color}]{bar}[/] {score:.2f}"


def print_result(result: DiffResult, explain: bool = False) -> None:
    """Print a rich formatted diff result to the terminal."""
    overall_color = _OVERALL_COLORS.get(result.overall, "white")

    # Header panel
    header_lines = [
        f"[bold {overall_color}]Overall: {result.overall.upper()}[/]",
        f"Global score: {_score_bar(result.global_score)}",
        f"Delta index: [bold]{result.delta_index:.1%}[/] of content changed",
        f"Chunks: {result.chunk_count_a} → {result.chunk_count_b} | Model: {result.model} | {result.processing_ms}ms",
    ]
    console.print(Panel("\n".join(header_lines), title="[bold]Semantic Diff Engine[/]", border_style=overall_color))

    if not result.chunks:
        console.print("[dim]No chunks to display.[/]")
        return

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold", expand=True)
    table.add_column("Version A", ratio=35)
    table.add_column("Version B", ratio=35)
    table.add_column("Score", ratio=15, justify="center")
    table.add_column("Verdict", ratio=10, justify="center")
    if explain:
        table.add_column("Explanation", ratio=30)

    for chunk in result.chunks:
        color = _VERDICT_COLORS.get(chunk.verdict, "white")
        row = [
            Text.from_markup(f"[{color}]{_truncate(chunk.text_a)}[/]"),
            Text.from_markup(f"[{color}]{_truncate(chunk.text_b)}[/]"),
            Text.from_markup(_score_bar(chunk.score) if chunk.score > 0 else "[dim]—[/]"),
            Text.from_markup(_VERDICT_BADGES.get(chunk.verdict, chunk.verdict)),
        ]
        if explain:
            row.append(Text.from_markup(f"[dim]{escape(chunk.explanation or '')}[/]"))
        table.add_row(*row)

    console.print(table)

    # Footer stats
    counts = {}
    for c in result.chunks:
        counts[c.verdict] = counts.get(c.verdict, 0) + 1

    parts = [f"[{_VERDICT_COLORS[v]}]{v}: {n}[/]" for v, n in counts.items()]
    console.print("  " + " | ".join(parts))


def export_html(result: DiffResult, output_path: Path) -> None:
    """Export a standalone HTML diff report."""
    _VERDICT_BG = {
        VERDICT_IDENTICAL: "#d4edda",
        VERDICT_SHIFT: "#fff3cd",
        VERDICT_CONTRADICTION: "#f8d7da",
        VERDICT_ADDED: "#cce5ff",
        VERDICT_REMOVED: "#e2e3e5",
    }

    rows_html = ""
    for chunk in result.chunks:
        bg = _VERDICT_BG.get(chunk.verdict, "#fff")
        a_text = (chunk.text_a or "").replace("<", "&lt;").replace(">", "&gt;")
        b_text = (chunk.text_b or "").replace("<", "&lt;").replace(">", "&gt;")
        expl = (chunk.explanation or "").replace("<", "&lt;").replace(">", "&gt;")
        score_pct = int(chunk.score * 100)
        rows_html += f"""
        <tr style="background:{bg}">
          <td title="{expl}">{a_text}</td>
          <td title="{expl}">{b_text}</td>
          <td>
            <div class="bar"><div class="fill" style="width:{score_pct}%"></div></div>
            {chunk.score:.2f}
          </td>
          <td><span class="badge badge-{chunk.verdict}">{chunk.verdict}</span></td>
          <td class="expl">{expl}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SDE Diff Report</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 20px; background: #1a1a2e; color: #e0e0e0; }}
  h1 {{ color: #00d4ff; }}
  .summary {{ background: #16213e; border-radius: 8px; padding: 20px; margin-bottom: 20px; display: flex; gap: 40px; flex-wrap: wrap; }}
  .metric {{ text-align: center; }}
  .metric .value {{ font-size: 2em; font-weight: bold; color: #00d4ff; }}
  .metric .label {{ font-size: 0.85em; color: #aaa; }}
  .gauge {{ width: 80px; height: 80px; border-radius: 50%; background: conic-gradient(#00d4ff {int(result.global_score*360)}deg, #333 0deg); display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; font-weight: bold; }}
  table {{ width: 100%; border-collapse: collapse; background: #16213e; border-radius: 8px; overflow: hidden; }}
  th {{ background: #0f3460; padding: 10px; text-align: left; }}
  td {{ padding: 10px; border-bottom: 1px solid #0f3460; vertical-align: top; font-size: 0.9em; }}
  .bar {{ background: #333; height: 8px; border-radius: 4px; width: 80px; display: inline-block; vertical-align: middle; margin-right: 6px; }}
  .fill {{ background: #00d4ff; height: 100%; border-radius: 4px; }}
  .badge {{ padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }}
  .badge-identical {{ background: #155724; color: #d4edda; }}
  .badge-semantic_shift {{ background: #856404; color: #fff3cd; }}
  .badge-contradiction {{ background: #721c24; color: #f8d7da; }}
  .badge-added {{ background: #004085; color: #cce5ff; }}
  .badge-removed {{ background: #383d41; color: #e2e3e5; }}
  .expl {{ color: #aaa; font-style: italic; font-size: 0.85em; }}
  @media (prefers-color-scheme: light) {{
    body {{ background: #f8f9fa; color: #212529; }}
    .summary, table {{ background: #fff; }}
    th {{ background: #e9ecef; }}
    td {{ border-bottom: 1px solid #dee2e6; }}
  }}
</style>
</head>
<body>
<h1>Semantic Diff Engine — Report</h1>
<div class="summary">
  <div class="metric">
    <div class="gauge">{result.global_score:.0%}</div>
    <div class="label">Global Score</div>
  </div>
  <div class="metric">
    <div class="value" style="color:{'#28a745' if result.overall=='identical' else '#ffc107' if result.overall=='semantic_shift' else '#dc3545'}">{result.overall.upper()}</div>
    <div class="label">Overall Verdict</div>
  </div>
  <div class="metric">
    <div class="value">{result.delta_index:.0%}</div>
    <div class="label">Delta Index</div>
  </div>
  <div class="metric">
    <div class="value">{result.processing_ms}ms</div>
    <div class="label">Processing time</div>
  </div>
  <div class="metric">
    <div class="value">{result.model}</div>
    <div class="label">Model</div>
  </div>
</div>
<table>
<thead>
  <tr><th>Version A</th><th>Version B</th><th>Score</th><th>Verdict</th><th>Explanation</th></tr>
</thead>
<tbody>{rows_html}</tbody>
</table>
<p style="color:#666;font-size:0.8em;margin-top:20px">Generated by Semantic Diff Engine v1.0 — <a href="https://github.com/semantic-diff/sde" style="color:#00d4ff">github.com/semantic-diff/sde</a></p>
</body>
</html>"""
    output_path.write_text(html, encoding="utf-8")
    console.print(f"[green]HTML report written to {output_path}[/]")
