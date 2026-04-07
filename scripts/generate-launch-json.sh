#!/usr/bin/env bash
# Generates .claude/launch.json from .env values (or sensible defaults).
# Idempotent — safe to re-run. Used by agents.sh and /init bootstrap.
#
# Port resolution priority:
#   Backend:  PORT from .env > default (agent: 8001, main: 8000)
#   Frontend: FRONTEND_PORT > parsed from CORS_ORIGINS > default (agent: 11174, main: 5173)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."
ENV_FILE="${PROJECT_DIR}/.env"
OUTPUT_FILE="${PROJECT_DIR}/.claude/launch.json"

# Source .env if present
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

# Detect agent vs main worktree
IS_AGENT=false
if [ -n "${EUPRAXIS_AGENT_NAME:-}" ]; then
  IS_AGENT=true
fi

# Backend port
if [ -n "${PORT:-}" ]; then
  BACKEND_PORT="$PORT"
elif [ "$IS_AGENT" = true ]; then
  BACKEND_PORT=8001
else
  BACKEND_PORT=8000
fi

# Frontend port (priority: FRONTEND_PORT > CORS_ORIGINS > default)
if [ -n "${FRONTEND_PORT:-}" ]; then
  FE_PORT="$FRONTEND_PORT"
elif [ -n "${CORS_ORIGINS:-}" ]; then
  # Extract port from first CORS origin (e.g., http://localhost:11174)
  FE_PORT=$(echo "$CORS_ORIGINS" | grep -oE ':[0-9]+' | head -1 | tr -d ':')
  if [ -z "$FE_PORT" ]; then
    FE_PORT=$( [ "$IS_AGENT" = true ] && echo 11174 || echo 5173 )
  fi
else
  FE_PORT=$( [ "$IS_AGENT" = true ] && echo 11174 || echo 5173 )
fi

# Data mode
DATA_MODE="${DATA_MODE:-$( [ "$IS_AGENT" = true ] && echo memory || echo db )}"

# API base URL
API_BASE="http://localhost:${BACKEND_PORT}"

# Ensure .claude/ directory exists
mkdir -p "${PROJECT_DIR}/.claude"

# Write launch.json
cat > "$OUTPUT_FILE" <<EOF
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "backend",
      "runtimeExecutable": "bash",
      "runtimeArgs": ["-c", "cd backend && DATA_MODE=${DATA_MODE} CORS_ORIGINS=http://localhost:${FE_PORT},http://127.0.0.1:${FE_PORT} PYTHONPATH=\$(cd .. && pwd):\${PYTHONPATH:-} .venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port ${BACKEND_PORT}"],
      "port": ${BACKEND_PORT}
    },
    {
      "name": "frontend",
      "runtimeExecutable": "bash",
      "runtimeArgs": ["-c", "cd frontend && VITE_DATA_MODE=${DATA_MODE} VITE_API_BASE_URL=${API_BASE} npm run dev -- --port ${FE_PORT}"],
      "port": ${FE_PORT}
    }
  ]
}
EOF

echo "  Generated .claude/launch.json (backend:${BACKEND_PORT}, frontend:${FE_PORT}, mode:${DATA_MODE})"
