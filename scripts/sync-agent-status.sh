#!/usr/bin/env bash
# Sync agent status: start session and send heartbeat.
# Calls POST /sessions/start to initialize session lifecycle (API-centric signals).
# Recovers agent from STALE to WORKING/syncing.
#
# Story: 2026-03-14.15-05-07 — Agent Heartbeat Recovery from Offline
# BUG: 2026-04-01.20-06-04 AC2 — sessions/start never called by init hook
# Refactored: 2026-03-15.22-33-53 — Hub Client Shell Consolidation
#
# Usage: bash scripts/sync-agent-status.sh
#   Called by /init skill after board-check (AC4).
#
# Env (natural key):
#   EUPRAXIS_AGENT_NAME  — agent name (from .env)
#   EUPRAXIS_MACHINE_ID  — machine identifier (from .env, default: local)
#
# Env (shared):
#   EUPRAXIS_HUB_URL     — hub API base URL (from .env)
#   EUPRAXIS_HUB_TOKEN   — auth token (from .env)
#   SESSION_ID           — session identifier for UUID cache
#   CLAUDE_PROJECT_DIR   — project root for .env fallback
#
# Fail-open: always exits 0. Session conflicts output to stdout for agent-mediated resolution.

# Source hub-client.sh for API operations (handles URL/token resolution + retry)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hub-client.sh"

# Agent identity from env with .env fallback via resolve_marker_id (BUG 2026-03-19.14-56-30)
AGENT_NAME="${EUPRAXIS_AGENT_NAME:-}"
if [ -z "$AGENT_NAME" ]; then
  AGENT_NAME=$(resolve_marker_id 2>/dev/null)
fi
if [ -z "$AGENT_NAME" ]; then
  echo "  [sync] Skipped — no EUPRAXIS_AGENT_NAME"
  exit 0
fi
MACHINE_ID=$(resolve_machine_id)

# Start session via sessions/start endpoint (BUG 2026-04-01.20-06-04 AC2)
# This initializes the session lifecycle, sets SYNCING signal, and updates heartbeat.
# Raw curl used instead of hub_post because hub_post discards response body on 4xx,
# but we need the 409 body for SESSION_CONFLICT handling (AC4).
_hub_url=$(_hub_resolve_url)
_hub_token=$(_hub_resolve_token)
_start_url="${_hub_url}/api/v1/agents/by-name/${AGENT_NAME}/sessions/start?machine_id=${MACHINE_ID}"
_auth_header=""
if [ -n "$_hub_token" ]; then
  _auth_header="Authorization: Bearer $_hub_token"
fi

_raw=$(curl -4 -s -w "\n%{http_code}" -X POST "$_start_url" \
  -H "Content-Type: application/json" \
  ${_auth_header:+-H "$_auth_header"} \
  -d '{}' 2>/dev/null)
_http_code=$(echo "$_raw" | tail -1)
response=$(echo "$_raw" | sed '$d')

_write_session_id() {
  local sid
  sid=$(echo "$1" | jq -r '.session_id // ""' 2>/dev/null)
  if [ -n "$sid" ] && [ "$sid" != "null" ]; then
    echo "$sid" > "/tmp/claude-session-id-${AGENT_NAME}"
  fi
}

case "$_http_code" in
  200|201)
    status=$(echo "$response" | jq -r '.data.status // "unknown"' 2>/dev/null)
    _write_session_id "$response"
    echo "  [sync] Agent ${AGENT_NAME} → ${status}"
    ;;
  409)
    error_code=$(echo "$response" | jq -r '.error.code // ""' 2>/dev/null)
    if [ "$error_code" = "SESSION_CONFLICT" ]; then
      # Output conflict info for agent-mediated resolution (AC1: no TTY prompt).
      # The agent reads this from system-reminder and presents AskUserQuestion.
      conflict_sid=$(echo "$response" | jq -r '.error.session_id // "unknown"' 2>/dev/null)
      conflict_started=$(echo "$response" | jq -r '.error.started_at // "unknown"' 2>/dev/null)
      conflict_hb=$(echo "$response" | jq -r '.error.last_heartbeat // "unknown"' 2>/dev/null)
      echo ""
      echo "  ⚠️  SESSION CONFLICT — another session is active for ${AGENT_NAME}"
      echo "  Session ID:     ${conflict_sid}"
      echo "  Started at:     ${conflict_started}"
      echo "  Last heartbeat: ${conflict_hb}"
      echo "  Machine ID:     ${MACHINE_ID}"
      echo ""
      echo "  Agent must resolve via AskUserQuestion: force takeover or abort."
    else
      echo "  [sync] Warning — session start returned 409 (unexpected code: ${error_code})"
    fi
    ;;
  *)
    echo "  [sync] Warning — session start failed (HTTP ${_http_code})"
    ;;
esac

exit 0
