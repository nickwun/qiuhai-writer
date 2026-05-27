#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
OUT="$ROOT/xhs-pipeline/workspace/topic-reports"
SCRIPT="$ROOT/scripts/discover_running_materials.py"

mkdir -p "$OUT"

ARGS=(
  --limit 30
  --per-source-limit 3
  --youtube-query-budget 48
  --youtube-per-query-limit 3
  --web-query-budget 20
  --min-youtube-ratio 0.6
  --output-dir "$OUT"
)

if [ "$#" -gt 0 ]; then
  for keyword in "$@"; do
    ARGS+=(--keyword "$keyword")
  done
fi

python3 "$SCRIPT" "${ARGS[@]}"
