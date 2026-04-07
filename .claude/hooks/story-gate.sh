#!/usr/bin/env bash
# PreToolUse hook: Blocks production code writes when no story is in_progress.
# Queries hub API — no marker files.
#
# Also blocks writes to story/epic cache files (DB is source of truth).
#
# Migration: 2026-03-26.23-12-00 — API-backed, replaces marker-based story-gate.
# Subsumes: sequential-tasks-gate, pull-transition-gate.
# Matcher: Write, Edit

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# DENY writes to story/epic cache files — DB is source of truth
case "$FILE_PATH" in
  */stories/doing/*|*/stories/done/*|*/stories/todo/*|*/stories/canceled/*|*/stories/archive/*|*/stories/epics/*)
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: DB is source of truth. Use curl to PATCH/POST story content through the API. For local files, use Export button or POST /api/v1/sync/db-to-file."
  }
}
EOF
    exit 0
    ;;
esac

# Only gate production code paths — allow everything else
case "$FILE_PATH" in
  */backend/src/*|*/frontend/src/*|*/tests/*)
    ;;
  *)
    exit 0
    ;;
esac

# Query hub API for in_progress stories
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
source "$HOOK_DIR/lib/session-error-capture.sh"
AGENT_ID=$(resolve_agent_id)
if [ -z "$AGENT_ID" ]; then
  exit 0
fi
HUB_SESSION_ID="$AGENT_ID"

# Get active story (still needed for UUID — gate API requires it)
story=$(hub_get_active_story "$AGENT_ID")

if [ -z "$story" ]; then
  # No in_progress story — block
  capture_session_error "hook-deny" "critical" "story-gate.sh" "No story in_progress — code write blocked"
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: No story in_progress (hub API). Create or start a story before modifying code."
  }
}
EOF
  exit 0
fi

# Try Gate Engine API for code_write gate evaluation
story_uuid=$(hub_get_story_field "$story" "id")
gate_response=$(hub_check_gate "$story_uuid" "code_write")
gate_exit=$?

if [ "$gate_exit" -eq 0 ] && [ -n "$gate_response" ]; then
  # Gate Engine responded — use its decision
  allowed=$(printf '%s' "$gate_response" | jq -r '.allowed // empty' 2>/dev/null)
  if [ "$allowed" = "true" ]; then
    exit 0
  fi
  reason=$(printf '%s' "$gate_response" | jq -r '.reason // "Code write gate check failed"' 2>/dev/null)
  capture_session_error "gate-fail" "critical" "story-gate.sh" "$reason"
  cat <<EOFGATE
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: ${reason}"
  }
}
EOFGATE
  exit 0
fi

# Fail-open: story exists in in_progress — allow write even if Gate Engine is unreachable
exit 0
