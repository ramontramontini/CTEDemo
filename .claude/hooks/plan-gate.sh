#!/usr/bin/env bash
# PreToolUse hook: Blocks production code writes until upstream review passes.
# Queries hub API for review_plan gate stamp on the active story.
# Cross-session fallback: if no stamp, checks spec + ACs + status >= in_progress.
#
# Migration: 2026-03-26.23-12-00 — API-backed, replaces marker-based plan-review-gate.
# Matcher: Write, Edit

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only gate production code paths
case "$FILE_PATH" in
  */backend/src/*|*/frontend/src/*|*/tests/*)
    ;;
  *)
    exit 0
    ;;
esac

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
AGENT_ID=$(resolve_agent_id)
if [ -z "$AGENT_ID" ]; then
  exit 0
fi
HUB_SESSION_ID="$AGENT_ID"

# Get active story
story=$(hub_get_active_story "$AGENT_ID")
if [ -z "$story" ]; then
  # No in_progress story — story-gate handles this, let it pass here
  exit 0
fi

# Try Gate Engine API for plan gate evaluation
story_uuid=$(hub_get_story_field "$story" "id")
gate_response=$(hub_check_gate "$story_uuid" "plan")
gate_exit=$?

if [ "$gate_exit" -eq 0 ] && [ -n "$gate_response" ]; then
  # Gate Engine responded — use its decision
  allowed=$(printf '%s' "$gate_response" | jq -r '.allowed // empty' 2>/dev/null)
  if [ "$allowed" = "true" ]; then
    advisory=$(printf '%s' "$gate_response" | jq -r '.advisory // empty' 2>/dev/null)
    if [ -n "$advisory" ]; then
      cat <<EOFADV
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "${advisory}"
  }
}
EOFADV
    fi
    exit 0
  fi
  reason=$(printf '%s' "$gate_response" | jq -r '.reason // "Plan gate check failed"' 2>/dev/null)
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

# ── Fallback: Gate Engine disabled (503) or unreachable — legacy logic ──

# Check for review_plan gate stamp
if hub_has_gate_stamp "$story" "review_plan"; then
  g3_context=$(hub_get_story_field "$story" "context")
  g3_goal=$(hub_get_story_field "$story" "goal")
  G3_MISSING=""
  [ -z "$g3_context" ] && G3_MISSING="${G3_MISSING}context, "
  [ -z "$g3_goal" ] && G3_MISSING="${G3_MISSING}goal, "
  if [ -n "$G3_MISSING" ]; then
    G3_MISSING="${G3_MISSING%, }"
    cat <<EOFG3
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: Mandatory fields null: ${G3_MISSING}. Story spec must have ## Context and ## Goal."
  }
}
EOFG3
    exit 0
  fi
  exit 0
fi

# No review_plan stamp — cross-session fallback
spec=$(hub_get_story_field "$story" "spec")
ac_count=$(printf '%s' "$story" | jq '.acceptance_criteria | length' 2>/dev/null || echo "0")
status=$(hub_get_story_field "$story" "status")

CROSS_SESSION_PASS=true
[ -z "$spec" ] && CROSS_SESSION_PASS=false
[ "$ac_count" -le 0 ] && CROSS_SESSION_PASS=false
case "$status" in
  ready_to_pull|claimed|in_progress) ;;
  *) CROSS_SESSION_PASS=false ;;
esac

if [ "$CROSS_SESSION_PASS" = true ]; then
  g3_context=$(hub_get_story_field "$story" "context")
  g3_goal=$(hub_get_story_field "$story" "goal")
  G3_MISSING=""
  [ -z "$g3_context" ] && G3_MISSING="${G3_MISSING}context, "
  [ -z "$g3_goal" ] && G3_MISSING="${G3_MISSING}goal, "
  if [ -n "$G3_MISSING" ]; then
    G3_MISSING="${G3_MISSING%, }"
    cat <<EOFG3
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: Mandatory fields null: ${G3_MISSING}. Story spec must have ## Context and ## Goal."
  }
}
EOFG3
    exit 0
  fi
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "REVIEW-PLAN stamp not found (cross-session). Story has spec + ACs + proper status — proceeding."
  }
}
EOF
  exit 0
fi

# No stamp, insufficient upstream evidence — block
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: No review_plan stamp and insufficient upstream evidence (spec: $([ -n "$spec" ] && echo 'present' || echo 'MISSING'), ACs: ${ac_count}, status: ${status}). Run upstream ceremony first."
  }
}
EOF
exit 0
