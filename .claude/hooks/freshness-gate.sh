#!/usr/bin/env bash
# PreToolUse hook: Directive freshness verification before git push.
# Compares HEAD directives against origin/main. Blocks push when stale.
# Stateless — no markers, pure git comparison.
#
# Migration: 2026-03-26.23-12-00 — renamed from directive-freshness-check.sh
# Matcher: Bash
# Performance: only activates on git push commands.

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check git push commands (not substrings in echo/heredoc)
if ! echo "$COMMAND" | grep -qE '(^|&&\s*|;\s*)git\s+push(\s|$)'; then
  exit 0
fi

# Fail open if origin/main is unreachable
if ! git rev-parse origin/main >/dev/null 2>&1; then
  exit 0
fi

# Allow push when origin/main is ancestor of HEAD (agent's own directive changes)
if git merge-base --is-ancestor origin/main HEAD 2>/dev/null; then
  exit 0
fi

STALE_FILES=""

# Compare CLAUDE.md
LOCAL_CLAUDE=$(git rev-parse HEAD:CLAUDE.md 2>/dev/null)
ORIGIN_CLAUDE=$(git rev-parse origin/main:CLAUDE.md 2>/dev/null)
if [ -n "$LOCAL_CLAUDE" ] && [ -n "$ORIGIN_CLAUDE" ] && [ "$LOCAL_CLAUDE" != "$ORIGIN_CLAUDE" ]; then
  STALE_FILES="CLAUDE.md"
fi

# Compare .claude/rules/*.md
for RULE_FILE in .claude/rules/*.md; do
  [ -f "$RULE_FILE" ] || continue
  LOCAL_HASH=$(git rev-parse "HEAD:$RULE_FILE" 2>/dev/null)
  ORIGIN_HASH=$(git rev-parse "origin/main:$RULE_FILE" 2>/dev/null)
  [ -z "$ORIGIN_HASH" ] && continue
  if [ -n "$LOCAL_HASH" ] && [ "$LOCAL_HASH" != "$ORIGIN_HASH" ]; then
    STALE_FILES="${STALE_FILES:+$STALE_FILES, }$RULE_FILE"
  fi
done

# Check for files deleted locally but present on origin
for ORIGIN_RULE in $(git ls-tree --name-only origin/main .claude/rules/ 2>/dev/null | grep '\.md$'); do
  LOCAL_EXISTS=$(git rev-parse "HEAD:.claude/rules/$ORIGIN_RULE" 2>/dev/null)
  if [ -z "$LOCAL_EXISTS" ]; then
    STALE_FILES="${STALE_FILES:+$STALE_FILES, }.claude/rules/$ORIGIN_RULE (removed locally)"
  fi
done

if [ -z "$STALE_FILES" ]; then
  exit 0
fi

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "STALE DIRECTIVES: ${STALE_FILES} differ from origin/main. Run 'git fetch origin && git rebase origin/main' before pushing."
  }
}
EOF
exit 0
