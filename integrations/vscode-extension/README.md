# SDE VS Code Extension

Detect semantic changes in text files directly in your editor.

## Features

- **Inline highlights**: semantic shifts (orange underline) and contradictions (red underline)
- **Tooltips**: hover over highlights to see score + explanation
- **Summary panel**: full diff report in a side panel
- **Multi-domain**: legal, medical, code, journalism

## Usage

1. Open the file you want to compare (Version B)
2. Run `SDE: Compare with...` from the command palette (`Cmd+Shift+P`)
3. Select the original file (Version A)
4. View inline highlights and the summary panel

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `sde.apiUrl` | `http://localhost:8000` | SDE API URL |
| `sde.domain` | `default` | Domain profile |
| `sde.explain` | `true` | Show explanations in tooltips |

## Requirements

The SDE API must be running:
```bash
docker compose up sde-api
# or
semantic-diff serve
```
