#!/usr/bin/env bash
# Start backend and frontend concurrently
set -euo pipefail

cleanup() {
    echo "Shutting down..."
    kill 0
}
trap cleanup EXIT

echo "Starting backend on :8000..."
cd backend && DATA_MODE=memory PYTHONPATH=. uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &

echo "Starting frontend on :5173..."
cd frontend && VITE_DATA_MODE=memory npm run dev &

wait
