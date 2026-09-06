#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$ROOT" ]] || { echo "ERROR: not inside a git repository" >&2; exit 1; }
cd "$ROOT"

TASK_ID="${1:-}"
if [[ -z "$TASK_ID" ]]; then
  echo "Usage: $0 R5-01" >&2
  exit 1
fi

matches=(docs/tasks/backlog/"$TASK_ID"-*.md)
if [[ ! -e "${matches[0]}" ]]; then
  echo "ERROR: backlog card $TASK_ID not found" >&2
  exit 1
fi
if [[ ${#matches[@]} -ne 1 ]]; then
  echo "ERROR: expected exactly one backlog card for $TASK_ID" >&2
  exit 1
fi

active=(docs/tasks/active/*.md)
if [[ -e "${active[0]}" ]]; then
  echo "ERROR: active task directory is not empty." >&2
  echo "Review/move the completed active card to docs/tasks/done/ first." >&2
  exit 1
fi

CARD="${matches[0]}"
mv "$CARD" docs/tasks/active/
BASENAME="$(basename "$CARD")"

python3 - "$TASK_ID" "$BASENAME" <<'PY'
from pathlib import Path
import sys, re
task_id, basename = sys.argv[1], sys.argv[2]
p = Path("AGENT_NEXT_TASK.md")
text = p.read_text(encoding="utf-8")
text = re.sub(r"- Task ID: `[^`]+`", f"- Task ID: `{task_id}`", text)
text = re.sub(r"- Task Card: `[^`]+`", f"- Task Card: `docs/tasks/active/{basename}`", text)
text = re.sub(r"- Status: `[^`]+`", "- Status: `READY`", text, count=1)
p.write_text(text, encoding="utf-8")
PY

echo "Activated $TASK_ID"
echo "IMPORTANT: inspect AGENT_NEXT_TASK.md and dependencies before running an Agent."
