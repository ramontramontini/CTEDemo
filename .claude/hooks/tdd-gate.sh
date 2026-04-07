#!/usr/bin/env bash
# PreToolUse hook: TDD 3-phase enforcement gate.
# Blocks production code writes without active TDD phase marker.
# Phases: idle (no marker) → red → green → refactor
#
# Write/Edit gate:
# - Test files (tests/, __tests__/): always allowed (any phase)
# - Production code (backend/src/, frontend/src/): blocked only in idle
# - Non-code stories (sdlc/data/maintenance/investigation): bypass entirely
# - Post-TDD (SUITES-GREEN stamp present): bypass (quality/ship phase)
#
# Story: 2026-04-03.03-55-43 — Stamp Authority Internalization (AC6)
# Matcher: Write, Edit

INPUT=$(cat)

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
AGENT_ID=$(resolve_agent_id)
if [ -z "$AGENT_ID" ]; then
  exit 0
fi

# Extract file path from tool input
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
if [ "$TOOL_NAME" = "Write" ]; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
elif [ "$TOOL_NAME" = "Edit" ]; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
else
  exit 0
fi

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# ─── Always allow test files ────────────────────────────────────
if echo "$FILE_PATH" | grep -qE '(tests/|__tests__/)'; then
  exit 0
fi

# ─── Only gate production code ──────────────────────────────────
IS_PROD=0
if echo "$FILE_PATH" | grep -qE '(backend/src/|frontend/src/)'; then
  IS_PROD=1
fi

if [ "$IS_PROD" -eq 0 ]; then
  exit 0
fi

# ─── Check story type — non-code stories bypass TDD gate ────────
STORY_TYPE_CACHE="/tmp/tdd-story-type-${AGENT_ID}"
STORY_TYPE=""

if [ -f "$STORY_TYPE_CACHE" ]; then
  STORY_TYPE=$(cat "$STORY_TYPE_CACHE" 2>/dev/null)
fi

if [ -z "$STORY_TYPE" ]; then
  # Query hub API for active story type
  story=$(hub_get_active_story "$AGENT_ID" 2>/dev/null)
  if [ -n "$story" ]; then
    STORY_TYPE=$(hub_get_story_field "$story" "type" 2>/dev/null)
    if [ -n "$STORY_TYPE" ]; then
      echo "$STORY_TYPE" > "$STORY_TYPE_CACHE"
    fi
  fi
fi

# Fail-open: if we can't determine story type, allow
if [ -z "$STORY_TYPE" ]; then
  exit 0
fi

# Non-code story types bypass TDD gate entirely
case "$STORY_TYPE" in
  sdlc|data|maintenance|investigation)
    exit 0
    ;;
esac

# ─── Check SUITES-GREEN stamp — post-TDD bypass ────────────────
if [ -n "$story" ]; then
  if hub_has_gate_stamp "$story" "suites_green" 2>/dev/null; then
    exit 0
  fi
fi

# ─── Check TDD phase marker ────────────────────────────────────
PHASE_FILE="/tmp/tdd-phase-${AGENT_ID}"
PHASE=""
if [ -f "$PHASE_FILE" ]; then
  PHASE=$(cat "$PHASE_FILE" 2>/dev/null)
fi

case "$PHASE" in
  red|green|refactor)
    # Active TDD phase — allow production code writes
    exit 0
    ;;
  *)
    # idle (no marker or unknown) — block
    cat <<'EOF'
{
  "decision": "block",
  "reason": "TDD: write a failing test first. Production code writes are blocked until a test has been run. Write a test in tests/ and run it to enter the RED phase."
}
EOF
    exit 0
    ;;
esac
