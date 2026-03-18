#!/bin/bash
set -euo pipefail

pip install semantic-diff --quiet

semantic-diff diff \
  "$INPUT_FILE_A" \
  "$INPUT_FILE_B" \
  --domain "$INPUT_DOMAIN" \
  --model "$INPUT_MODEL" \
  ${INPUT_EXPLAIN:+--explain} \
  --html /tmp/sde-report.html

echo "report_path=/tmp/sde-report.html" >> "$GITHUB_OUTPUT"
