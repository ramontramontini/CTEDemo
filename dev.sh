#!/usr/bin/env bash
# Start backend and frontend concurrently
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Source .env for port configuration
if [[ -f "$SCRIPT_DIR/.env" ]]; then
  set -a
  source "$SCRIPT_DIR/.env"
  set +a
fi

BACKEND_PORT="${PORT:-9000}"

# Derive frontend port from CORS_ORIGINS (e.g. http://localhost:5174 → 5174)
if [[ -n "${CORS_ORIGINS:-}" ]]; then
  FRONTEND_PORT="$(echo "$CORS_ORIGINS" | sed 's|.*:\([0-9]*\)$|\1|')"
else
  FRONTEND_PORT=12173
fi

cleanup() {
    echo "Shutting down..."
    kill 0
}
trap cleanup EXIT

echo "Starting backend on :${BACKEND_PORT}..."
if [[ -f "$SCRIPT_DIR/backend/.venv/bin/uvicorn" ]]; then
  cd backend && DATA_MODE=memory PYTHONPATH=. .venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" &
elif command -v poetry &>/dev/null; then
  cd backend && DATA_MODE=memory PYTHONPATH=. poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" &
else
  echo "ERROR: No uvicorn found. Run 'cd backend && poetry install' first." >&2
  exit 1
fi

echo "Starting frontend on :${FRONTEND_PORT}..."
cd "$SCRIPT_DIR/frontend" && VITE_PORT="$FRONTEND_PORT" npx vite --port "$FRONTEND_PORT" &

wait
