#!/usr/bin/env bash
# PreToolUse hook: HARD DENY for story creation when epic ceremony is incomplete.
# (2026-03-26.13-05-02 — upgraded from advisory to HARD DENY)
#
# Detects curl POST to /api/v1/stories with an epic_id, queries the epic via
# hub API, and enforces the ceremony requirement (Policy 7: epics require
# macro-requirements ceremony before adding ANY stories).
#
# Epic ceremony must populate ALL fields — spec AND acceptance_criteria at minimum.
# Skeleton stories are created during ceremony with minimal info + dependencies;
# each story gets its own spec ceremony later.
#
# Behavior matrix:
#   - No epic_id in payload → allow (no epic = no ceremony needed)
#   - epic_id present, spec AND acceptance_criteria populated → allow
#   - epic_id present, spec OR acceptance_criteria missing → HARD DENY
#   - Hub API unreachable → allow (fail-open — API is the safety net with 422)
#
# Matcher: Bash
# Performance: fast-path exits for non-Bash tools and non-curl commands.

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Fast-path: only check Bash tools
if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Fast-path: only check curl commands targeting story creation endpoint
if ! echo "$COMMAND" | grep -qiE 'curl.*(POST|-X\s*POST).*(/api/v1/stories)'; then
  if ! echo "$COMMAND" | grep -qiE 'curl.*(/api/v1/stories).*(POST|-X\s*POST)'; then
    if ! echo "$COMMAND" | grep -qE 'hub_create_story'; then
      exit 0
    fi
  fi
fi

# Extract epic_id from the payload
EPIC_ID=$(echo "$COMMAND" | grep -oE '"epic_id"\s*:\s*"[^"]*"' | head -1 | sed 's/"epic_id"\s*:\s*"//' | sed 's/"$//')

# No epic_id → allow (no epic = no ceremony needed)
if [ -z "$EPIC_ID" ]; then
  exit 0
fi

# Resolve hub URL from .env or environment
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "$EUPRAXIS_HUB_URL" ]; then
  if [ -f "$REPO_ROOT/.env" ]; then
    EUPRAXIS_HUB_URL=$(grep -E '^EUPRAXIS_HUB_URL=' "$REPO_ROOT/.env" | cut -d= -f2- | tr -d '"' | tr -d "'")
  fi
fi
EUPRAXIS_HUB_URL="${EUPRAXIS_HUB_URL:-http://localhost:8000}"

# Resolve auth token for API call
_TOKEN=""
if [ -n "$EUPRAXIS_HUB_TOKEN" ]; then
  _TOKEN="$EUPRAXIS_HUB_TOKEN"
elif [ -f "$REPO_ROOT/.env" ]; then
  _TOKEN=$(grep "^EUPRAXIS_HUB_TOKEN=" "$REPO_ROOT/.env" 2>/dev/null | cut -d= -f2)
fi

# Single API call replaces inline curl + field validation
if [ -n "$_TOKEN" ]; then
  CHECK_RESP=$(curl -s --max-time 3 -H "Authorization: Bearer $_TOKEN" "$EUPRAXIS_HUB_URL/api/v1/epics/$EPIC_ID/checks/ceremony-ready" 2>/dev/null)
else
  CHECK_RESP=$(curl -s --max-time 3 "$EUPRAXIS_HUB_URL/api/v1/epics/$EPIC_ID/checks/ceremony-ready" 2>/dev/null)
fi
CURL_EXIT=$?

# Hub API unreachable → allow (fail-open, matches existing behavior)
if [ $CURL_EXIT -ne 0 ] || [ -z "$CHECK_RESP" ]; then
  exit 0
fi

ALLOWED=$(printf '%s' "$CHECK_RESP" | jq -r '.allowed // empty' 2>/dev/null)

# Ceremony complete or not required → allow
if [ "$ALLOWED" = "true" ]; then
  exit 0
fi

# If allowed field is absent (unexpected format) → fail-open
if [ -z "$ALLOWED" ]; then
  exit 0
fi

# Ceremony incomplete → HARD DENY with details from check response
MISSING=$(printf '%s' "$CHECK_RESP" | jq -r '.missing_fields // [] | join(", ")' 2>/dev/null)
STORY_COUNT=$(printf '%s' "$CHECK_RESP" | jq -r '.story_count // 0' 2>/dev/null)
REASON=$(printf '%s' "$CHECK_RESP" | jq -r '.reason // "Ceremony incomplete"' 2>/dev/null)
NEXT_NUM=$((STORY_COUNT + 1))

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Epic requires macro-requirements ceremony before adding story #${NEXT_NUM}. ${REASON}. Complete the epic ceremony (EPIC_APPROVED) first."
  }
}
EOF
exit 0
