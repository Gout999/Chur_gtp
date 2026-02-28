#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "[init] EduGuide environment bootstrap"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "[init] ERROR: python not found"
  exit 1
fi

echo "[init] Using Python: $PYTHON_BIN"
"$PYTHON_BIN" -m pip install -r requirements.txt

if [ -d "frontend" ] && command -v npm >/dev/null 2>&1; then
  echo "[init] Installing frontend dependencies"
  (cd frontend && npm install)
fi

echo "[init] Running baseline tests"
"$PYTHON_BIN" -m pytest -q tests/unit/test_architect.py tests/integration/test_memory.py tests/e2e/test_teaching_flow.py

echo "[init] Done"
echo "[init] Start API manually with:"
echo "       uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
