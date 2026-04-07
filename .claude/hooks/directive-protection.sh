#!/usr/bin/env bash
# PreToolUse hook: Blocks Write/Edit to protected directive files (Rule 7)
# (2026-03-16.09-59-57 — GOVOPT | Directive Protection Write Hook)
#
# Protected files (CLAUDE.md §Rule 7):
#   CLAUDE.md, .claude/rules/*.md, docs/templates/*, docs/architecture/*
# NOT protected: docs/domain/*, docs/research/*, story files
#
# AC1: Detects protected paths via case-statement, fast-path exit for non-protected
# AC2: HARD DENY when no sdlc/maintenance story in_progress
# AC3: Advisory (not deny) when sdlc/maintenance story IS in_progress
# AC5: Fail-closed on API errors (cannot verify exemption → DENY)
#
# Matcher: Write, Edit

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Only check Write and Edit tools
if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# AC1: Fast-path — only gate protected directive files
case "$FILE_PATH" in
  */CLAUDE.md|*/.claude/rules/*.md|*/docs/templates/*|*/docs/architecture/*)
    # Protected path — proceed to authorization check
    ;;
  *)
    # Not protected — exit immediately (no API call)
    exit 0
    ;;
esac

# ─── Authorization check: SDLC/maintenance story exemption ────────

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
MARKER_ID=$(resolve_marker_id)
if [ -z "$MARKER_ID" ]; then
  # No agent identity — fail-closed (AC5)
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: Protected directive file (Rule 7). Cannot verify agent identity — no EUPRAXIS_AGENT_NAME."
  }
}
EOF
  exit 0
fi

# AC3: Single API call replaces hub_has_story_of_type multi-query logic
# hub-query.sh already sourced above — use its URL and token resolution
if [ -z "$EUPRAXIS_HUB_URL" ]; then
  EUPRAXIS_HUB_URL=$(_hub_resolve_url 2>/dev/null)
fi
EUPRAXIS_HUB_URL="${EUPRAXIS_HUB_URL:-http://localhost:8000}"

MACHINE_ID=$(resolve_machine_id)
_TOKEN=$(_hub_resolve_token)
if [ -n "$_TOKEN" ]; then
  CHECK_RESP=$(curl -s --max-time 3 -H "Authorization: Bearer $_TOKEN" "$EUPRAXIS_HUB_URL/api/v1/agents/by-name/$MARKER_ID/checks/directive-write?machine_id=$MACHINE_ID" 2>/dev/null)
else
  CHECK_RESP=$(curl -s --max-time 3 "$EUPRAXIS_HUB_URL/api/v1/agents/by-name/$MARKER_ID/checks/directive-write?machine_id=$MACHINE_ID" 2>/dev/null)
fi
ALLOWED=$(printf '%s' "$CHECK_RESP" | jq -r '.allowed // empty' 2>/dev/null)

# AC3: Qualifying story found → advisory (allow with warning)
if [ "$ALLOWED" = "true" ]; then
  STORY_TITLE=$(printf '%s' "$CHECK_RESP" | jq -r '.story_title // "unknown"' 2>/dev/null)
  jq -n --arg title "$STORY_TITLE" --arg fp "$FILE_PATH" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      additionalContext: ("Protected file modification (Rule 7): " + $fp + ". SDLC/maintenance story in progress (" + $title + ") — proceeding with advisory.")
    }
  }'
  exit 0
fi

# AC5 (2026-04-02.02-52-41): Emit awaiting_input before deny — agent is blocked, needs user attention
MACHINE_ID=$(resolve_machine_id)
_signal_payload='{"signal": "awaiting_input"}'
if [ -n "$_TOKEN" ]; then
  curl -sf --connect-timeout 2 --max-time 3 \
    -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $_TOKEN" \
    -d "$_signal_payload" \
    "${EUPRAXIS_HUB_URL}/api/v1/agents/by-name/${MARKER_ID}/sessions/signal?machine_id=${MACHINE_ID}" \
    >/dev/null 2>&1
else
  curl -sf --connect-timeout 2 --max-time 3 \
    -X POST -H "Content-Type: application/json" \
    -d "$_signal_payload" \
    "${EUPRAXIS_HUB_URL}/api/v1/agents/by-name/${MARKER_ID}/sessions/signal?machine_id=${MACHINE_ID}" \
    >/dev/null 2>&1
fi

# AC2 + AC5: No SDLC story (or API unreachable) → HARD DENY
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: Protected directive file (Rule 7). Modifying CLAUDE.md, .claude/rules/, docs/templates/, or docs/architecture/ requires an SDLC story or maint: workflow with user approval. See CLAUDE.md §Rule 7."
  }
}
EOF
exit 0
