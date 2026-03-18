import * as vscode from 'vscode';
import * as path from 'path';

interface SdeChunk {
  id: number;
  a: string | null;
  b: string | null;
  score: number;
  verdict: string;
  explanation: string | null;
  confidence: number;
}

interface SdeDiffResult {
  overall: string;
  global_score: number;
  delta_index: number;
  chunks: SdeChunk[];
  metadata: { model: string; processing_ms: number };
}

// Decoration types for different verdicts
let shiftDecoration: vscode.TextEditorDecorationType;
let contradictionDecoration: vscode.TextEditorDecorationType;

function getDecorationTypes() {
  shiftDecoration = vscode.window.createTextEditorDecorationType({
    borderBottom: '2px solid #d29922',
    textDecoration: 'underline wavy #d29922',
    light: { borderColor: '#9a6700' },
  });
  contradictionDecoration = vscode.window.createTextEditorDecorationType({
    borderBottom: '2px solid #f85149',
    textDecoration: 'underline wavy #f85149',
    gutterIconPath: undefined,
    light: { borderColor: '#d1242f' },
  });
}

async function runSemanticDiff(
  textA: string,
  textB: string,
  apiUrl: string,
  domain: string,
  explain: boolean
): Promise<SdeDiffResult> {
  const response = await fetch(`${apiUrl}/diff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      version: '1.0',
      text_a: textA,
      text_b: textB,
      domain,
      options: { explain },
    }),
  });

  if (!response.ok) {
    throw new Error(`SDE API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<SdeDiffResult>;
}

function applyDecorations(editor: vscode.TextEditor, result: SdeDiffResult): void {
  const shiftRanges: vscode.DecorationOptions[] = [];
  const contradictionRanges: vscode.DecorationOptions[] = [];

  const text = editor.document.getText();

  for (const chunk of result.chunks) {
    if (chunk.verdict === 'identical') continue;

    const searchText = chunk.b || chunk.a;
    if (!searchText) continue;

    const idx = text.indexOf(searchText);
    if (idx === -1) continue;

    const startPos = editor.document.positionAt(idx);
    const endPos = editor.document.positionAt(idx + searchText.length);
    const range = new vscode.Range(startPos, endPos);

    const tooltip = new vscode.MarkdownString(
      `**SDE:** ${chunk.verdict.replace('_', ' ')} (score: ${chunk.score.toFixed(3)})`
      + (chunk.explanation ? `\n\n${chunk.explanation}` : '')
    );

    const decoration: vscode.DecorationOptions = { range, hoverMessage: tooltip };

    if (chunk.verdict === 'contradiction') {
      contradictionRanges.push(decoration);
    } else {
      shiftRanges.push(decoration);
    }
  }

  editor.setDecorations(shiftDecoration, shiftRanges);
  editor.setDecorations(contradictionDecoration, contradictionRanges);
}

function showSummaryPanel(result: SdeDiffResult): void {
  const panel = vscode.window.createWebviewPanel(
    'sdeSummary',
    'Semantic Diff Report',
    vscode.ViewColumn.Beside,
    {}
  );

  const scoreColor = result.global_score >= 0.92 ? '#3fb950' : result.global_score >= 0.75 ? '#d29922' : '#f85149';

  const chunksHtml = result.chunks
    .filter(c => c.verdict !== 'identical')
    .map(c => `
      <tr>
        <td>${(c.a || '—').substring(0, 60)}</td>
        <td>${(c.b || '—').substring(0, 60)}</td>
        <td>${c.score.toFixed(3)}</td>
        <td><span class="badge badge-${c.verdict}">${c.verdict.replace('_', ' ')}</span></td>
        <td>${c.explanation || ''}</td>
      </tr>`)
    .join('');

  panel.webview.html = `<!DOCTYPE html><html><head><style>
    body{font-family:system-ui;padding:20px;background:#1a1a2e;color:#e0e0e0}
    h2{color:#00d4ff}
    .summary{display:flex;gap:30px;margin-bottom:20px;flex-wrap:wrap}
    .metric{text-align:center}
    .value{font-size:1.8em;font-weight:bold;color:${scoreColor}}
    .label{font-size:0.8em;color:#aaa}
    table{width:100%;border-collapse:collapse}
    th,td{padding:8px;border-bottom:1px solid #333;text-align:left;font-size:0.85em}
    th{background:#16213e;color:#aaa}
    .badge{padding:2px 8px;border-radius:10px;font-size:0.75em}
    .badge-semantic_shift{background:#856404;color:#fff3cd}
    .badge-contradiction{background:#721c24;color:#f8d7da}
    .badge-added{background:#004085;color:#cce5ff}
    .badge-removed{background:#383d41;color:#e2e3e5}
  </style></head><body>
  <h2>Semantic Diff Report</h2>
  <div class="summary">
    <div class="metric"><div class="value">${result.overall.replace('_',' ')}</div><div class="label">Overall</div></div>
    <div class="metric"><div class="value">${(result.global_score*100).toFixed(1)}%</div><div class="label">Score</div></div>
    <div class="metric"><div class="value">${(result.delta_index*100).toFixed(1)}%</div><div class="label">Delta</div></div>
    <div class="metric"><div class="value">${result.metadata.processing_ms}ms</div><div class="label">Time</div></div>
  </div>
  <table>
    <thead><tr><th>Original</th><th>Revised</th><th>Score</th><th>Verdict</th><th>Explanation</th></tr></thead>
    <tbody>${chunksHtml || '<tr><td colspan="5" style="text-align:center;color:#aaa">No semantic changes detected.</td></tr>'}</tbody>
  </table>
  </body></html>`;
}

export function activate(context: vscode.ExtensionContext) {
  getDecorationTypes();

  const compareCommand = vscode.commands.registerCommand('sde.compare', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage('Open a file first.');
      return;
    }

    const fileUris = await vscode.window.showOpenDialog({
      canSelectMany: false,
      openLabel: 'Compare with',
      filters: { 'Text files': ['txt', 'md', 'json', 'py', 'ts', 'js'] },
    });

    if (!fileUris || fileUris.length === 0) return;

    const config = vscode.workspace.getConfiguration('sde');
    const apiUrl = config.get<string>('apiUrl', 'http://localhost:8000');
    const domain = config.get<string>('domain', 'default');
    const explain = config.get<boolean>('explain', true);

    const textA = editor.document.getText();
    const textBDoc = await vscode.workspace.openTextDocument(fileUris[0]);
    const textB = textBDoc.getText();

    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: 'Running semantic diff...' },
      async () => {
        try {
          const result = await runSemanticDiff(textA, textB, apiUrl, domain, explain);
          applyDecorations(editor, result);
          showSummaryPanel(result);
          vscode.window.showInformationMessage(
            `SDE: ${result.overall} | Score: ${result.global_score.toFixed(3)} | Delta: ${(result.delta_index * 100).toFixed(1)}%`
          );
        } catch (e) {
          vscode.window.showErrorMessage(`SDE error: ${e instanceof Error ? e.message : String(e)}`);
        }
      }
    );
  });

  const clearCommand = vscode.commands.registerCommand('sde.clearDecorations', () => {
    const editor = vscode.window.activeTextEditor;
    if (editor) {
      editor.setDecorations(shiftDecoration, []);
      editor.setDecorations(contradictionDecoration, []);
    }
  });

  context.subscriptions.push(compareCommand, clearCommand);
}

export function deactivate() {
  if (shiftDecoration) shiftDecoration.dispose();
  if (contradictionDecoration) contradictionDecoration.dispose();
}
