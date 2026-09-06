#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$ROOT" ]] || { echo "Not in a git repository" >&2; exit 1; }
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re

p = Path("AGENT_NEXT_TASK.md")
if not p.exists():
    raise SystemExit("AGENT_NEXT_TASK.md not found")

text = p.read_text(encoding="utf-8")
m = re.search(r'Task Card:\s*`([^`]+)`', text)
if not m:
    raise SystemExit("Could not resolve Task Card from AGENT_NEXT_TASK.md")

task = Path(m.group(1))
print(f"== {task} ==")
print(task.read_text(encoding="utf-8"))
PY
