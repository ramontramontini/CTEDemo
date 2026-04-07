#!/usr/bin/env bash
# PreToolUse hook: Blocks git commit without suites-green and review-code stamps.
# Queries hub API for gate stamps on the active story.
#
# Gates (only for commits with code paths staged):
#   G1: suites_green stamp present + not stale (emitted_at > last file modification)
#   G2: review_code stamp present (SDLC/Data/Maintenance/Investigation exempt)
#
# Docs-only bypass: if no code paths staged, skip all gates.
# Code paths: backend/src/, frontend/src/, tests/
#
# Migration: 2026-03-26.23-12-00 — API-backed, replaces marker-based pre-commit-test-gate.
# Matcher: Bash

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check git commit commands
if ! echo "$COMMAND" | grep -qE '(^|&&\s*|;\s*)git\s+commit(\s|$)'; then
  exit 0
fi

# Docs-only bypass: skip all gates if no code paths staged
if [ "${STAGED_FILES_OVERRIDE+set}" = "set" ]; then
  _STAGED="$STAGED_FILES_OVERRIDE"
else
  _STAGED=$(git diff --cached --name-only 2>/dev/null || echo "")
fi

if [ -z "$_STAGED" ] || ! echo "$_STAGED" | grep -qE '^(backend/src/|frontend/src/|tests/)'; then
  exit 0
fi

# Get active story from API
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
source "$HOOK_DIR/lib/session-error-capture.sh"
AGENT_ID=$(resolve_agent_id)
if [ -z "$AGENT_ID" ]; then
  exit 0
fi
HUB_SESSION_ID="$AGENT_ID"

story=$(hub_get_active_story "$AGENT_ID")
stype=$(hub_get_story_field "$story" "type")

# Non-code story types: skip review_code (G2) but still enforce suites_green (G1)
SKIP_REVIEW_CODE=false
case "$stype" in
  sdlc*|data*|maintenance*|investigation*)
    SKIP_REVIEW_CODE=true
    ;;
  "")
    # API unreachable or no story — fail-closed
    capture_session_error "api-failure" "critical" "commit-gate.sh" "Hub API unreachable — cannot verify story type"
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: Cannot verify story type (hub API unreachable or no in_progress story). Start backend or verify EUPRAXIS_HUB_URL."
  }
}
EOF
    exit 0
    ;;
esac

# Build query params for Gate Engine API
STAGED_PATHS=$(echo "$_STAGED" | tr '\n' ',' | sed 's/,$//')
LAST_STAGED_EPOCH=0
for staged_file in $(echo "$_STAGED" | grep -E '^(backend/src/|frontend/src/|tests/)'); do
  fe=$(git log -1 --format=%at -- "$staged_file" 2>/dev/null)
  [ -n "$fe" ] && [ "$fe" -gt "$LAST_STAGED_EPOCH" ] 2>/dev/null && LAST_STAGED_EPOCH="$fe"
done

# Try Gate Engine API
story_uuid=$(hub_get_story_field "$story" "id")
gate_response=$(hub_check_gate "$story_uuid" "commit" "staged_paths=${STAGED_PATHS}&last_staged_epoch=${LAST_STAGED_EPOCH}")
gate_exit=$?

if [ "$gate_exit" -eq 0 ] && [ -n "$gate_response" ]; then
  # Gate Engine responded — use its decision
  allowed=$(printf '%s' "$gate_response" | jq -r '.allowed // empty' 2>/dev/null)
  if [ "$allowed" = "true" ]; then
    exit 0
  fi
  reason=$(printf '%s' "$gate_response" | jq -r '.reason // "Commit gate check failed"' 2>/dev/null)
  capture_session_error "gate-fail" "critical" "commit-gate.sh" "$reason"
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

# ── Fallback: Gate Engine disabled (503) or unreachable — legacy stamp checks ──

# G1: Check for suites_green stamp (universal — all story types)
if ! hub_has_gate_stamp "$story" "suites_green"; then
  capture_session_error "test-fail" "critical" "commit-gate.sh" "Tests not run before commit"
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: No suites_green stamp. Run all test suites before committing."
  }
}
EOF
  exit 0
fi

# G1 staleness: compare suites_green emitted_at vs staged file modification times
STAMP_EPOCH=$(hub_get_stamp_emitted_at "$story" "suites_green")
if [ -n "$STAMP_EPOCH" ]; then
  TOLERANCE=2
  STALE_FILE=""
  for staged_file in $(echo "$_STAGED" | grep -E '^(backend/src/|frontend/src/|tests/)'); do
    FILE_EPOCH=$(git log -1 --format=%at -- "$staged_file" 2>/dev/null)
    if [ -n "$FILE_EPOCH" ] && [ "$FILE_EPOCH" -gt $((STAMP_EPOCH - TOLERANCE)) ] 2>/dev/null; then
      if [ "$FILE_EPOCH" -gt "$STAMP_EPOCH" ] 2>/dev/null; then
        STALE_FILE="$staged_file"
        break
      fi
    fi
  done
  if [ -n "$STALE_FILE" ]; then
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: Tests stale — ${STALE_FILE} was modified after last test run. Re-run all test suites."
  }
}
EOF
    exit 0
  fi
fi

# G2: Check for review_code stamp (code types only)
if [ "$SKIP_REVIEW_CODE" = "false" ]; then
  if ! hub_has_gate_stamp "$story" "review_code"; then
    capture_session_error "gate-fail" "critical" "commit-gate.sh" "Code-review not passed before commit"
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: No review_code stamp. Code-review must pass before committing."
  }
}
EOF
    exit 0
  fi
fi

# All gates passed
exit 0
