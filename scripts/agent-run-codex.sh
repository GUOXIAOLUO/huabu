#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT}" ]]; then
  echo "ERROR: run this script inside the xinhuabu git repository." >&2
  exit 1
fi
cd "$ROOT"

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: 'codex' command not found." >&2
  exit 1
fi

PROMPT=".agent/prompts/run-current-task.md"
if [[ ! -f "$PROMPT" ]]; then
  echo "ERROR: missing $PROMPT" >&2
  exit 1
fi

echo "== Local truth before Codex =="
git status --short
echo "branch: $(git branch --show-current)"
echo "HEAD:   $(git rev-parse HEAD)"
echo
echo "== Starting exactly one active Xinhuabu task =="

cat "$PROMPT" | codex exec
