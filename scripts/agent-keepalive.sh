#!/usr/bin/env bash
# Background keepalive for Claude CLI sessions.
# Sends POST /agents/by-name/{name}/status every KEEPALIVE_INTERVAL seconds.
# Heartbeat-only payload (todo progress) — signals set by API endpoints.
#
# Env:
#   EUPRAXIS_AGENT_NAME — agent name (required)
#   MARKER_ID          — session identifier for PID file (required)
#   EUPRAXIS_HUB_URL   — hub API base URL (falls back to .env)
#   EUPRAXIS_HUB_TOKEN — auth token (falls back to .env)
#   KEEPALIVE_INTERVAL  — seconds between heartbeats (default: 60)
#   CLAUDE_PROJECT_DIR  — project root for hub-client.sh resolution
#
# PID file: /tmp/claude-keepalive-pid-{MARKER_ID}
# Launched by: session-heartbeat.sh (PostToolUse hook)
# Killed by: stop-keepalive-cleanup.sh (Stop hook) or PID file removal

INTERVAL="${KEEPALIVE_INTERVAL:-60}"
AGENT_NAME="${EUPRAXIS_AGENT_NAME:-}"
SID="${MARKER_ID:-}"
MACHINE_ID=$(resolve_machine_id)

# Source hub-client.sh for API operations
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hub-client.sh"

if [ -z "$AGENT_NAME" ]; then
  AGENT_NAME=$(resolve_marker_id 2>/dev/null)
fi

if [ -z "$AGENT_NAME" ] || [ -z "$SID" ]; then
  exit 1
fi

PID_FILE="/tmp/claude-keepalive-pid-${SID}"

if [ -z "$(_hub_resolve_url)" ]; then
  exit 1
fi

echo $$ > "$PID_FILE"

_cleanup() {
  rm -f "$PID_FILE" 2>/dev/null
  exit 0
}
trap _cleanup SIGTERM SIGINT

while true; do
  if [ ! -f "$PID_FILE" ]; then
    exit 0
  fi
  # Self-check: exit if superseded by a newer keepalive (prevents orphan accumulation)
  # BUG 2026-04-01.13-16-46: without this, overwritten PID files leave orphans alive
  current_pid=$(cat "$PID_FILE" 2>/dev/null)
  if [ "$current_pid" != "$$" ]; then
    exit 0
  fi

  # Read todo progress
  _todo_completed=""
  _todo_total=""
  _todo_file="/tmp/claude-todo-progress-${SID}"
  if [ -f "$_todo_file" ]; then
    _todo_completed=$(jq -r '.todo_completed // empty' "$_todo_file" 2>/dev/null)
    _todo_total=$(jq -r '.todo_total // empty' "$_todo_file" 2>/dev/null)
  fi

  # ─── Idle-silent detection (tool-call inactivity) ───────────────
  # Read last tool-call timestamp written by session-heartbeat.sh
  _idle_silent_threshold="${IDLE_SILENT_THRESHOLD:-120}"
  _signal_field="null"
  _tool_call_file="/tmp/claude-last-tool-call-${SID}"
  if [ -f "$_tool_call_file" ]; then
    _last_tool_call=$(cat "$_tool_call_file" 2>/dev/null)
    if [ -n "$_last_tool_call" ]; then
      _now=$(date +%s)
      _elapsed=$((_now - _last_tool_call))
      # Check if awaiting_input signal is active (higher priority)
      _signal_file="/tmp/claude-last-signal-${SID}"
      _current_signal=""
      if [ -f "$_signal_file" ]; then
        _current_signal=$(cat "$_signal_file" 2>/dev/null)
      fi
      if [ "$_elapsed" -gt "$_idle_silent_threshold" ] && [ "$_current_signal" != "awaiting_input" ] && [ "$_current_signal" != "idle" ]; then
        _signal_field='"idle_silent"'
      fi
    fi
  fi
  # If no file exists: no data, don't emit idle_silent (new session, no tools yet)

  # Collect git worktree state
  _ka_project_dir="${CLAUDE_PROJECT_DIR:-.}"
  _ka_wt_dirty=$(git -C "$_ka_project_dir" status --porcelain 2>/dev/null | head -1)
  _ka_worktree_dirty=$( [ -n "$_ka_wt_dirty" ] && echo "true" || echo "false" )
  _ka_branch=$(git -C "$_ka_project_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
  _ka_behind=$(git -C "$_ka_project_dir" rev-list --count HEAD..origin/main 2>/dev/null || echo "")
  _ka_ahead=$(git -C "$_ka_project_dir" rev-list --count origin/main..HEAD 2>/dev/null || echo "")
  _ka_hash=$(git -C "$_ka_project_dir" rev-parse --short HEAD 2>/dev/null || echo "")
  _ka_msg=$(git -C "$_ka_project_dir" log -1 --format=%s 2>/dev/null || echo "")

  # Build payload with optional signal field + worktree state
  _ka_session_id=$(resolve_session_id "$SID")

  _payload=$(jq -n \
    --arg tc "$_todo_completed" \
    --arg tt "$_todo_total" \
    --argjson sig "$_signal_field" \
    --arg sid "$_ka_session_id" \
    --argjson wd "$_ka_worktree_dirty" \
    --arg br "$_ka_branch" \
    --arg bh "$_ka_behind" \
    --arg ah "$_ka_ahead" \
    --arg ch "$_ka_hash" \
    --arg cm "$_ka_msg" \
    '{
      todo_completed: (if $tc == "" then null else ($tc | tonumber) end),
      todo_total: (if $tt == "" then null else ($tt | tonumber) end),
      signal: $sig,
      session_id: (if $sid == "" then null else $sid end),
      worktree_dirty: $wd,
      branch: (if $br == "" then null else $br end),
      behind_count: (if $bh == "" then null else ($bh | tonumber) end),
      ahead_count: (if $ah == "" then null else ($ah | tonumber) end),
      last_commit_hash: (if $ch == "" then null else $ch end),
      last_commit_message: (if $cm == "" then null else $cm end)
    }')

  hub_post "/api/v1/agents/by-name/${AGENT_NAME}/status?machine_id=${MACHINE_ID}" "$_payload" >/dev/null 2>&1 || true

  sleep "$INTERVAL" &
  wait $! 2>/dev/null || exit 0
done
