#!/usr/bin/env bash
# Start backend + frontend for local development.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

cleanup() {
  trap - INT TERM EXIT
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# Backend venv
if [[ ! -d "$BACKEND/.venv" ]]; then
  echo "Creating Python venv…"
  python3 -m venv "$BACKEND/.venv"
  "$BACKEND/.venv/bin/pip" install --upgrade pip setuptools wheel
  "$BACKEND/.venv/bin/pip" install -r "$BACKEND/requirements.txt"
fi

# Frontend deps
if [[ ! -d "$FRONTEND/node_modules" ]]; then
  echo "Installing frontend dependencies…"
  (cd "$FRONTEND" && npm install)
fi

echo "Starting backend on http://127.0.0.1:8000"
(cd "$BACKEND" && .venv/bin/uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

echo "Starting frontend on http://127.0.0.1:5173"
(cd "$FRONTEND" && npm run dev -- --host 127.0.0.1) &
FRONTEND_PID=$!

echo ""
echo "  UI:      http://127.0.0.1:5173"
echo "  API:     http://127.0.0.1:8000"
echo "  Docs:    http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop both."

wait
