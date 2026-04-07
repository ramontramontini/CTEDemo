#!/usr/bin/env bash
# PreToolUse hook: Blocks git push without review_ship stamp when agent has in_progress story.
# Queries hub API — no marker files.
#
# Non-story pushes (spec commits, maintenance — no in_progress story) pass through.
# Fail-closed: if Gate Engine unreachable, denies push.
#
# Migration: 2026-03-26.23-12-00 — API-backed, replaces marker-based push-gate.
# Matcher: Bash

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check git push commands
if ! echo "$COMMAND" | grep -qE '(^|&&\s*|;\s*)git\s+push(\s|$)'; then
  exit 0
fi

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
resolve_env_or_die

HUB_SESSION_ID="$AGENT_ID"

# Query for in_progress stories owned by this agent
story=$(hub_get_active_story "$AGENT_ID")

# No in_progress story — allow push (spec commit, maintenance, etc.)
if [ -z "$story" ]; then
  exit 0
fi

# In_progress story exists — check via Gate Engine API
story_uuid=$(hub_get_story_field "$story" "id")
gate_response=$(hub_check_gate "$story_uuid" "push")
gate_exit=$?

if [ "$gate_exit" -eq 0 ] && [ -n "$gate_response" ]; then
  # Gate Engine responded — use its decision
  allowed=$(printf '%s' "$gate_response" | jq -r '.allowed // empty' 2>/dev/null)
  if [ "$allowed" = "true" ]; then
    exit 0
  fi
  reason=$(printf '%s' "$gate_response" | jq -r '.reason // "Ship-review required before push"' 2>/dev/null)
  cat <<EOFGATE
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: ${reason}. Complete quality gates via /pull Step 4."
  }
}
EOFGATE
  exit 0
fi

# Fallback: Gate Engine unreachable — fail-closed (deny push)
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: Cannot verify ship readiness — Gate Engine unreachable. Retry or check hub API status."
  }
}
EOF
exit 0
