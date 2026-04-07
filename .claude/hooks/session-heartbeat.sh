#!/usr/bin/env bash
# PostToolUse hook: Session heartbeat — heartbeat-only push
#
# Sends heartbeat payload (current_action + todo progress) to hub API.
# Signal derivation removed — signals are now set by API endpoints
# via SDLCEvent + SignalEmitter (API-centric signal architecture).
#
# Matcher: Bash, Write, Edit, Agent, TodoWrite, Skill

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Agent identity
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
AGENT_NAME="${EUPRAXIS_AGENT_NAME:-}"
if [ -z "$AGENT_NAME" ]; then
  AGENT_NAME=$(resolve_marker_id)
  if [ -z "$AGENT_NAME" ]; then
    exit 0
  fi
fi
MACHINE_ID=$(resolve_machine_id)
MARKER_ID=$(resolve_marker_id)
if [ -z "$MARKER_ID" ]; then
  exit 0
fi

# ─── Launch keepalive background process ─────────────────────────
KEEPALIVE_PID_FILE="/tmp/claude-keepalive-pid-${MARKER_ID}"
_keepalive_running=false
if [ -f "$KEEPALIVE_PID_FILE" ]; then
  _ka_pid=$(cat "$KEEPALIVE_PID_FILE" 2>/dev/null)
  if [ -n "$_ka_pid" ] && kill -0 "$_ka_pid" 2>/dev/null; then
    _keepalive_running=true
  fi
fi
if [ "$_keepalive_running" = "false" ]; then
  _project_dir="${CLAUDE_PROJECT_DIR:-.}"
  _keepalive_script="$_project_dir/scripts/agent-keepalive.sh"
  if [ -x "$_keepalive_script" ]; then
    EUPRAXIS_AGENT_NAME="$AGENT_NAME" \
      EUPRAXIS_MACHINE_ID="${MACHINE_ID}" \
      MARKER_ID="$MARKER_ID" \
      EUPRAXIS_HUB_URL="${EUPRAXIS_HUB_URL:-}" \
      EUPRAXIS_HUB_TOKEN="${EUPRAXIS_HUB_TOKEN:-}" \
      CLAUDE_PROJECT_DIR="$_project_dir" \
      KEEPALIVE_INTERVAL="${KEEPALIVE_INTERVAL:-60}" \
      nohup bash "$_keepalive_script" >/dev/null 2>&1 &
    disown 2>/dev/null || true
  fi
fi

# ─── Record last tool-call timestamp (always, before throttle) ──
# Used by agent-keepalive.sh to detect tool-call inactivity (IDLE_SILENT).
date +%s > "/tmp/claude-last-tool-call-${MARKER_ID}"

# ─── 30-second throttle ─────────────────────────────────────────
THROTTLE_FILE="/tmp/claude-heartbeat-last-${MARKER_ID}"
if [ -f "$THROTTLE_FILE" ]; then
  now=$(date +%s)
  last_push=$(stat -f %m "$THROTTLE_FILE" 2>/dev/null)
  if [ -z "$last_push" ]; then
    last_push=$(stat -c %Y "$THROTTLE_FILE" 2>/dev/null || echo 0)
  fi
  elapsed=$((now - last_push))
  if [ "$elapsed" -lt 30 ]; then
    exit 0
  fi
fi

# ─── Derive current_action for display ──────────────────────────
case "$TOOL_NAME" in
  Bash)  _summary=$(echo "$INPUT" | jq -r '.tool_input.command // empty' | tr '\n\r\t' '   ')
         current_action="Bash: ${_summary:0:80}" ;;
  Write) current_action="Write: $(echo "$INPUT" | jq -r '.tool_input.file_path // empty')" ;;
  Edit)  current_action="Edit: $(echo "$INPUT" | jq -r '.tool_input.file_path // empty')" ;;
  Agent) current_action="Agent: $(echo "$INPUT" | jq -r '.tool_input.description // empty')" ;;
  Skill) current_action="Skill: $(echo "$INPUT" | jq -r '.tool_input.skill // empty')" ;;
  *)     current_action="$TOOL_NAME" ;;
esac
current_action="${current_action:0:80}"

# ─── Read todo progress ─────────────────────────────────────────
todo_completed=""
todo_total=""
TODO_PROGRESS_FILE="/tmp/claude-todo-progress-${MARKER_ID}"
if [ -f "$TODO_PROGRESS_FILE" ]; then
  todo_completed=$(jq -r '.todo_completed // empty' "$TODO_PROGRESS_FILE" 2>/dev/null)
  todo_total=$(jq -r '.todo_total // empty' "$TODO_PROGRESS_FILE" 2>/dev/null)
fi

# ─── Build heartbeat-only JSON payload (no signal fields) ───────
SESSION_ID=$(resolve_session_id "$MARKER_ID")

payload=$(jq -n \
  --arg ca "$current_action" \
  --arg tc "$todo_completed" \
  --arg tt "$todo_total" \
  --arg sid "$SESSION_ID" \
  '{
    current_action: $ca,
    session_id: (if $sid == "" then null else $sid end),
    todo_completed: (if $tc == "" then null else ($tc | tonumber) end),
    todo_total: (if $tt == "" then null else ($tt | tonumber) end)
  }')

# ─── Push to hub API (fail-open) ────────────────────────────────
hub_url=$(_hub_resolve_url)
token=$(_hub_resolve_token)

if [ -n "$token" ]; then
  curl -sf --connect-timeout 3 --max-time 5 \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $token" \
    -d "$payload" \
    "${hub_url}/api/v1/agents/by-name/${AGENT_NAME}/status?machine_id=${MACHINE_ID}" >/dev/null 2>&1
else
  curl -sf --connect-timeout 3 --max-time 5 \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "${hub_url}/api/v1/agents/by-name/${AGENT_NAME}/status?machine_id=${MACHINE_ID}" >/dev/null 2>&1
fi

if [ $? -eq 0 ]; then
  touch "$THROTTLE_FILE" 2>/dev/null
fi

exit 0
