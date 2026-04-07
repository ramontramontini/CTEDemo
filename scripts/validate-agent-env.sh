#!/usr/bin/env bash
# Validate agent worktree .env against .env.agent.example (single source of truth).
# Parses REQUIRED fields from the template dynamically.
#
# Exit codes:
#   0 — all required fields present (or not an agent worktree)
#   1 — missing required fields
#
# Usage:
#   bash scripts/validate-agent-env.sh              # uses $CLAUDE_PROJECT_DIR or CWD
#   bash scripts/validate-agent-env.sh /path/to/wt  # explicit worktree path
#
# Story: 2026-03-23.19-26-47 — Standardize Agent Worktree .env

set -euo pipefail

# Resolve project directory
PROJECT_DIR="${1:-${CLAUDE_PROJECT_DIR:-.}}"
ENV_FILE="$PROJECT_DIR/.env"
TEMPLATE_FILE="$PROJECT_DIR/.env.agent.example"

# Check template exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "WARNING: .env.agent.example not found at $PROJECT_DIR — cannot validate"
  exit 0
fi

# Check .env exists
if [ ! -f "$ENV_FILE" ]; then
  echo "WARNING: .env not found at $PROJECT_DIR"
  exit 1
fi

# Check if this is an agent worktree (EUPRAXIS_AGENT_NAME present)
AGENT_NAME=$(grep "^EUPRAXIS_AGENT_NAME=" "$ENV_FILE" 2>/dev/null | cut -d= -f2)
if [ -z "$AGENT_NAME" ]; then
  echo "Not an agent worktree — skipping validation"
  exit 0
fi

# Parse required fields from template (lines with "# REQUIRED:" before the field)
# Template format: "# REQUIRED: <description> — used by <hook/script>\n<FIELD>=<value>"
MISSING=0
PREV_COMMENT=""

while IFS= read -r line; do
  # Capture REQUIRED comment for the description
  if echo "$line" | grep -q "^# REQUIRED:"; then
    PREV_COMMENT="$line"
    continue
  fi

  # Check if this is a field line (KEY=value) following a REQUIRED comment
  if [ -n "$PREV_COMMENT" ] && echo "$line" | grep -qE "^[A-Z_]+="; then
    FIELD_NAME=$(echo "$line" | cut -d= -f1)

    # Extract "used by" from comment
    USED_BY=$(echo "$PREV_COMMENT" | sed -n 's/.*— used by \(.*\)/\1/p')

    # Check if field exists and is non-empty in .env
    FIELD_VALUE=$(grep "^${FIELD_NAME}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
    if [ -z "$FIELD_VALUE" ]; then
      echo "MISSING: ${FIELD_NAME} — required by ${USED_BY}"
      MISSING=$((MISSING + 1))
    fi

    PREV_COMMENT=""
  else
    PREV_COMMENT=""
  fi
done < "$TEMPLATE_FILE"

if [ "$MISSING" -gt 0 ]; then
  echo "ENV validation: $MISSING missing field(s) in $ENV_FILE"
  exit 1
else
  echo "ENV validation: OK ($AGENT_NAME)"
  exit 0
fi
