#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/phase3/runtime/shims:$ROOT/tests/matcher"
export PYTHONHASHSEED="${PYTHONHASHSEED:-0}"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then PYTHON=python; fi
exec "$PYTHON" -m pytest -p phase3.runtime.pytest_guard "$@"
