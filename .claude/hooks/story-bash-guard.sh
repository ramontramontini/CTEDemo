#!/usr/bin/env bash
# PreToolUse hook: Blocks Bash commands that write to story cache directories
# (2026-03-07.00-47-21 AC6)
#
# DB is source of truth. Use Export button or POST /api/v1/sync/db-to-file for local files.
# This hook blocks direct Bash writes (redirects, cp, mv, etc.) to story/epic directories.
# Defense-in-depth alongside story-gate.sh Write/Edit blocking.
#
# Blocked directories: stories/(doing|done|todo|canceled|archive|epics)/
#
# Matcher: Bash

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Check for write operations targeting story cache directories
# Patterns: >, >>, cp, mv, sed -i, tee, touch, rm, echo...>
# Target: stories/(doing|done|todo|canceled|archive)/
if echo "$COMMAND" | grep -qE '(>|>>|cp\s|mv\s|sed\s+-i|tee\s|touch\s|rm\s|mkdir\s).*stories/(doing|done|todo|canceled|archive|epics)/'; then
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: DB is source of truth. Use curl to PATCH/POST story content through the API. For local files, use Export button or POST /api/v1/sync/db-to-file. Do not write, copy, move, or delete files in stories/doing/, stories/done/, stories/todo/, stories/canceled/, stories/archive/, or stories/epics/ directly."
  }
}
EOF
  exit 0
fi

exit 0
