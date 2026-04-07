#!/usr/bin/env bash
# Start backend and frontend concurrently
set -euo pipefail

cleanup() {
    echo "Shutting down..."
    kill 0
}
trap cleanup EXIT

BACKEND_PORT="${PORT:-8000}"
echo "Starting backend on :${BACKEND_PORT}..."
cd backend && DATA_MODE=memory CORS_ORIGINS="http://localhost:5173" PYTHONPATH=. uvicorn src.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" &

echo "Starting frontend on :5173..."
cd frontend && VITE_DATA_MODE=memory npm run dev &

wait
