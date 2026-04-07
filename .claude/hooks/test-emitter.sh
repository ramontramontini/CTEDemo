#!/usr/bin/env bash
# PostToolUse hook: Emits SUITES-GREEN via POST /test-results when all test suites pass.
# Also manages TDD phase transitions (idle → red → green → refactor).
#
# Detects pytest/vitest commands, tracks per-suite pass state in memory,
# calls POST /test-results when all 3 suites have passed (entity emits SUITES-GREEN).
#
# TDD Phase Transitions (AC6):
#   On test FAILURE (any phase): set phase=red
#   On test PASS (phase=red): set phase=green
#   On test PASS (phase=green): set phase=refactor
#   On test PASS (phase=refactor): keep refactor
#   On SUITES-GREEN: clear phase file (quality phase — gate bypassed via stamp)
#
# Per-suite tracking uses /tmp cache files (not governance markers — just
# lightweight state for the "all 3 passed" aggregation within a session).
#
# Migration: 2026-04-03.03-55-43 — POST /test-results replaces hub_emit_gate_stamp.
# Matcher: Bash

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
AGENT_ID=$(resolve_agent_id)
if [ -z "$AGENT_ID" ]; then
  exit 0
fi

# Only process test commands
HAS_PYTEST=$(echo "$COMMAND" | grep -c "pytest")
HAS_VITEST=$(echo "$COMMAND" | grep -c "vitest")

if [ "$HAS_PYTEST" -eq 0 ] && [ "$HAS_VITEST" -eq 0 ]; then
  exit 0
fi

# ─── TDD phase marker file ──────────────────────────────────────
PHASE_FILE="/tmp/tdd-phase-${AGENT_ID}"

# Check for success
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // .tool_response.exitCode // empty' 2>/dev/null)

if [ -z "$EXIT_CODE" ]; then
  RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // empty' 2>/dev/null)
  if echo "$RESPONSE" | grep -qiE '(passed|0 failed|tests? (passed|completed)|All tests passed)'; then
    if echo "$RESPONSE" | grep -qiE '[0-9]+ failed'; then
      EXIT_CODE=""
    else
      EXIT_CODE="0"
    fi
  fi
fi

# ─── TDD phase transitions ──────────────────────────────────────
CURRENT_PHASE=""
if [ -f "$PHASE_FILE" ]; then
  CURRENT_PHASE=$(cat "$PHASE_FILE" 2>/dev/null)
fi

if [ "$EXIT_CODE" != "0" ]; then
  # Test FAILURE → set phase to red (any phase, including idle)
  echo "red" > "$PHASE_FILE"
  exit 0
fi

# Test PASSED — advance TDD phase
case "$CURRENT_PHASE" in
  red)
    echo "green" > "$PHASE_FILE"
    ;;
  green)
    echo "refactor" > "$PHASE_FILE"
    ;;
  refactor)
    # Stay in refactor (stable state, awaiting next RED or SUITES-GREEN)
    ;;
  *)
    # idle → first test pass without prior failure = green (lenient: allow starting from pass)
    echo "green" > "$PHASE_FILE"
    ;;
esac

# Track which suite passed (lightweight /tmp files — not governance markers)
SUITE_SET=""
SUITE_DIR="/tmp/claude-test-suites-${AGENT_ID}"
mkdir -p "$SUITE_DIR" 2>/dev/null

if echo "$COMMAND" | grep -q "tests/backend"; then
  touch "$SUITE_DIR/backend"
  SUITE_SET="backend"
fi

if echo "$COMMAND" | grep -q "tests/api"; then
  touch "$SUITE_DIR/api"
  SUITE_SET="api"
fi

if [ "$HAS_VITEST" -gt 0 ]; then
  touch "$SUITE_DIR/frontend"
  SUITE_SET="frontend"
fi

# Check if ALL 3 suites have passed
if [ -f "$SUITE_DIR/backend" ] && [ -f "$SUITE_DIR/api" ] && [ -f "$SUITE_DIR/frontend" ]; then
  # All 3 passed — call POST /test-results (entity emits SUITES-GREEN)
  HUB_SESSION_ID="$AGENT_ID"
  story=$(hub_get_active_story "$AGENT_ID")
  STORY_UUID=$(hub_get_story_field "$story" "id")

  if [ -n "$STORY_UUID" ]; then
    ORIGIN_SHA=$(git rev-parse origin/main 2>/dev/null || echo "unknown")
    hub_record_test_results "$STORY_UUID" "backend,api,frontend" "$ORIGIN_SHA"
  fi

  # Clear suite tracking for next cycle
  rm -rf "$SUITE_DIR" 2>/dev/null

  # Clear TDD phase (quality/ship phase — gate bypassed via stamp)
  rm -f "$PHASE_FILE" 2>/dev/null
  rm -f "/tmp/tdd-story-type-${AGENT_ID}" 2>/dev/null

  ORIGIN_SHA_SHORT=$(git rev-parse --short origin/main 2>/dev/null || echo "unknown")
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "ALL TEST SUITES PASSED: backend + api + frontend. SUITES-GREEN stamp emitted to API (origin/main: ${ORIGIN_SHA_SHORT})."
  }
}
EOF
elif [ -n "$SUITE_SET" ]; then
  DONE=""
  MISSING=""
  [ -f "$SUITE_DIR/backend" ] && DONE="${DONE}backend " || MISSING="${MISSING}backend "
  [ -f "$SUITE_DIR/api" ] && DONE="${DONE}api " || MISSING="${MISSING}api "
  [ -f "$SUITE_DIR/frontend" ] && DONE="${DONE}frontend " || MISSING="${MISSING}frontend "
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "TEST SUITE PASSED: ${SUITE_SET}. Done: [${DONE}]. Remaining: [${MISSING}]. SUITES-GREEN stamp NOT emitted until all 3 pass."
  }
}
EOF
fi

exit 0
