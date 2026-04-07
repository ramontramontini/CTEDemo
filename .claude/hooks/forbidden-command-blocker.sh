#!/usr/bin/env bash
# PreToolUse hook: Blocks forbidden DB commands in agent worktrees (001047 AC3, DBMAIN Rule 0)
# Catches alembic, docker-compose, psql even in chained commands (&&, ;, |).
#
# Matcher: Bash
# Performance: single grep, exits immediately on no match.

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Check for forbidden commands (handles chaining with &&, ;, |, and line starts)
if echo "$COMMAND" | grep -qE '(^|&&|;|\|)\s*(alembic|docker-compose|psql|pg_dump|pg_restore|createdb|dropdb)\b'; then
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: DB commands forbidden in agent worktrees. Agents use DATA_MODE=memory. See Rule 0 (Main=db, Agents=memory)."
  }
}
EOF
fi

exit 0
