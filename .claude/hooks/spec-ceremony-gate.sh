#!/usr/bin/env bash
# PreToolUse hook: HARD DENY on POST /api/v1/stories without review_spec stamp.
# Ensures every story passes through /spec ceremony before creation.
#
# Only gates story CREATION (POST /api/v1/stories with non-empty spec). Allows:
#   - PATCH (updates), sub-path POSTs (/transition, /claim, /gate-stamps, /mark-ac-met)
#   - Early creation (null/empty spec = specifying skeleton)
#
# Migration: 2026-03-26.23-12-00 — API-backed, replaces marker-based spec-ceremony-gate.
# Matcher: Bash

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check curl commands targeting the stories API
if ! echo "$COMMAND" | grep -qE 'curl.*(/api/v1/stories)'; then
  exit 0
fi

# Only gate POST creation
if ! echo "$COMMAND" | grep -qiE '(-X\s*POST|hub_post|hub_create_story)'; then
  exit 0
fi

# Exclude sub-path POSTs (transition, claim, gate-stamps, mark-ac-met, sync)
if echo "$COMMAND" | grep -qE '/api/v1/stories/[^"'\''[:space:]]+/(transition|claim|gate-stamps|mark-ac-met)'; then
  exit 0
fi
if echo "$COMMAND" | grep -qE '/api/v1/sync/'; then
  exit 0
fi

# Early creation exception: allow POST with null/absent/empty spec (specifying skeleton)
if ! echo "$COMMAND" | grep -qE '"spec"\s*:\s*"[^"]'; then
  exit 0
fi

# Full creation with non-empty spec — check review_spec stamp via backend check endpoint
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
resolve_env_or_die

# Single API call replaces 2x hub_query_stories + hub_has_gate_stamp checks
_TOKEN=$(_hub_resolve_token)
if [ -n "$_TOKEN" ]; then
  CHECK_RESP=$(curl -s --max-time 3 -H "Authorization: Bearer $_TOKEN" "$EUPRAXIS_HUB_URL/api/v1/agents/by-name/$AGENT_ID/checks/spec-ceremony" 2>/dev/null)
else
  CHECK_RESP=$(curl -s --max-time 3 "$EUPRAXIS_HUB_URL/api/v1/agents/by-name/$AGENT_ID/checks/spec-ceremony" 2>/dev/null)
fi
ALLOWED=$(printf '%s' "$CHECK_RESP" | jq -r '.allowed // empty' 2>/dev/null)

if [ "$ALLOWED" = "true" ]; then
  exit 0
fi

# No review_spec stamp found — block
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "HARD DENY: Story creation requires /spec ceremony. Run /spec first — spec-review must pass (VERDICT: PASS) before creating a story."
  }
}
EOF
exit 0
