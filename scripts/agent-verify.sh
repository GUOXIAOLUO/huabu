#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT}" ]]; then
  echo "ERROR: not inside a git repository" >&2
  exit 1
fi
cd "$ROOT"

# The documented repository baseline runs under the project virtualenv;
# plain PATH python3 lacks the project dependencies (e.g. pydantic).
if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi
export PYTHONDONTWRITEBYTECODE=1

FAILED=0

section() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

run_check() {
  local name="$1"
  shift
  section "$name"
  if "$@"; then
    echo "PASS: $name"
  else
    echo "FAIL: $name" >&2
    FAILED=1
  fi
}

if [[ -d tests ]]; then
  run_check "Python unit tests" "$PYTHON" -m unittest discover -s tests -p 'test_*.py'
else
  echo "SKIP: tests/ not found"
fi

section "Python AST parse"
if "$PYTHON" - <<'PY'
from pathlib import Path
import ast, sys

skip = {'.git', '.venv', 'venv', 'node_modules', 'vendor'}
bad = []
count = 0
for p in Path('.').rglob('*.py'):
    if any(part in skip for part in p.parts):
        continue
    try:
        ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
        count += 1
    except Exception as e:
        bad.append((str(p), repr(e)))

print(f"Parsed {count} Python files")
for path, err in bad:
    print(f"FAIL {path}: {err}", file=sys.stderr)
sys.exit(1 if bad else 0)
PY
then
  echo "PASS: Python AST parse"
else
  echo "FAIL: Python AST parse" >&2
  FAILED=1
fi

if command -v node >/dev/null 2>&1 && [[ -d static/js ]]; then
  section "JavaScript syntax"
  JS_FAILED=0
  JS_COUNT=0
  while IFS= read -r -d '' f; do
    JS_COUNT=$((JS_COUNT + 1))
    if ! node --check "$f" >/dev/null; then
      echo "FAIL: $f" >&2
      JS_FAILED=1
    fi
  done < <(find static/js -type f -name '*.js' -print0)
  echo "Checked $JS_COUNT JavaScript files"
  if [[ "$JS_FAILED" -eq 0 ]]; then
    echo "PASS: JavaScript syntax"
  else
    FAILED=1
  fi
else
  echo "SKIP: node or static/js not available"
fi

# Run a focused architecture guard if the repository has one.
if [[ -f tests/test_architecture_guards.py ]]; then
  run_check "Architecture guards" "$PYTHON" -m unittest tests.test_architecture_guards
else
  echo "SKIP: tests/test_architecture_guards.py not found"
fi

run_check "git diff --check" git diff --check

section "Result"
if [[ "$FAILED" -ne 0 ]]; then
  echo "AGENT VERIFY: FAIL" >&2
  exit 1
fi
echo "AGENT VERIFY: PASS"
