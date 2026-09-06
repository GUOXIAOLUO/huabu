#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT}" ]]; then
  echo "ERROR: not inside a git repository" >&2
  exit 1
fi
cd "$ROOT"

echo "== Xinhuabu Agent Status =="
echo
echo "Repository: $ROOT"
echo "Branch:     $(git branch --show-current)"
echo "HEAD:       $(git rev-parse HEAD)"
echo
echo "-- Working tree --"
git status --short || true
echo
echo "-- Active task --"
if [[ -f AGENT_NEXT_TASK.md ]]; then
  sed -n '1,80p' AGENT_NEXT_TASK.md
else
  echo "AGENT_NEXT_TASK.md missing"
fi
echo
echo "-- Required files --"
for f in \
  AGENTS.md \
  .agent/AGENT_CONTRACT.md \
  docs/status/CURRENT_EXECUTION_STATUS.md \
  AGENT_NEXT_TASK.md
do
  if [[ -f "$f" ]]; then
    echo "OK   $f"
  else
    echo "MISS $f"
  fi
done
