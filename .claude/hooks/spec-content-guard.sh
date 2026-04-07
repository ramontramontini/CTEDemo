#!/usr/bin/env bash
# PreToolUse hook: Blocks curl POST/PATCH to stories API when spec
# contains a plan-file reference instead of actual content.
# (BUG 2026-03-13.15-38-33 AC1-AC3)
#
# Defense-in-depth: backend Pydantic validators also reject these values.
# This hook catches the problem earlier, before the API call is made.
#
# Matcher: Bash

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check curl commands targeting the stories or epics API
if ! echo "$COMMAND" | grep -qE 'curl.*(/api/v1/stories|/api/v1/epics)'; then
  exit 0
fi

# Only check POST/PATCH (case-insensitive for -X flag)
if ! echo "$COMMAND" | grep -qiE '(-X\s*(POST|PATCH)|hub_create_story|hub_patch)'; then
  exit 0
fi

# Extract JSON payload — try -d/--data argument or inline JSON
# Use a simple approach: extract content between the outermost { }
JSON_PAYLOAD=$(echo "$COMMAND" | grep -oE '\{[^}]*("spec")[^}]*\}' | head -1)

if [ -z "$JSON_PAYLOAD" ]; then
  # No spec in payload — allow
  exit 0
fi

# Check each field for plan-file references
for FIELD in spec; do
  # Extract field value (POSIX-compatible — no grep -P, backend validator is safety net)
  FIELD_VALUE=$(echo "$JSON_PAYLOAD" | grep -oE "\"${FIELD}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | sed "s/\"${FIELD}\"[[:space:]]*:[[:space:]]*\"//" | sed 's/"$//')

  if [ -z "$FIELD_VALUE" ]; then
    continue
  fi

  # Check length — only flag short values (≤200 chars)
  VALUE_LEN=${#FIELD_VALUE}
  if [ "$VALUE_LEN" -gt 200 ]; then
    continue
  fi

  # Check for plan-file reference patterns (case-insensitive)
  if echo "$FIELD_VALUE" | grep -qiE '(See plan file|temp/plan-)'; then
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: ${FIELD} contains a plan-file reference instead of actual content. Read the plan file (e.g., temp/plan-[STORYID].md) and pass its FULL content as the ${FIELD} value. The ${FIELD} field must contain the complete spec/plan text, not a pointer to a file."
  }
}
EOF
    exit 0
  fi
done

exit 0
