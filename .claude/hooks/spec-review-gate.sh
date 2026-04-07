#!/usr/bin/env bash
# PreToolUse hook: Blocks ExitPlanMode until spec-review passes.
# Queries hub API for review_spec stamp on specifying/spec_complete stories.
# NO escape hatch — spec-review is mandatory.
# EXCEPTION: discuss-mode (no specifying/spec_complete story) exempts ExitPlanMode.
#
# Migration: 2026-03-26.23-12-00 — API-backed, replaces marker-based spec-review-gate.
# Matcher: ExitPlanMode

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "ExitPlanMode" ]; then
  exit 0
fi

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
resolve_env_or_die

HUB_SESSION_ID="$AGENT_ID"

# Find candidate stories (specifying + spec_complete)
response_specifying=$(hub_query_stories "specifying" "$AGENT_ID")
story_specifying=$(hub_get_first_story "$response_specifying")

response_sc=$(hub_query_stories "spec_complete" "$AGENT_ID")
story_sc=$(hub_get_first_story "$response_sc")

# Discuss-mode: no specifying/spec_complete story = ungated exploration, allow ExitPlanMode
if [ -z "$story_specifying" ] && [ -z "$story_sc" ]; then
  exit 0
fi

# Check candidates via Gate Engine API, then fall back to stamp check
_check_spec_gate() {
  local candidate="$1"
  [ -z "$candidate" ] && return 1
  local uuid
  uuid=$(hub_get_story_field "$candidate" "id")
  local gate_resp
  gate_resp=$(hub_check_gate "$uuid" "spec")
  local ge=$?
  if [ "$ge" -eq 0 ] && [ -n "$gate_resp" ]; then
    local allowed
    allowed=$(printf '%s' "$gate_resp" | jq -r '.allowed // empty' 2>/dev/null)
    [ "$allowed" = "true" ] && return 0
    return 1
  fi
  # Fallback: Gate Engine unreachable — fail-closed (deny ExitPlanMode)
  return 1
}

if [ -n "$story_specifying" ] && _check_spec_gate "$story_specifying"; then
  exit 0
fi

if [ -n "$story_sc" ] && _check_spec_gate "$story_sc"; then
  exit 0
fi

# Specifying/spec_complete story exists but no review_spec stamp — DENY
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: No review_spec stamp. ExitPlanMode requires spec-review to pass first. Run Gate Keeper spec-review (Agent tool, subagent_type: gate-keeper), then retry ExitPlanMode."
  }
}
EOF
exit 0
