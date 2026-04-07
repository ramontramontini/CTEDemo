#!/usr/bin/env bash
# Stop hook: Clean worktree enforcement (2026-03-01.18-39-07)
# Blocks session exit if worktree has uncommitted changes that would
# strand the worktree (dirty state prevents sync.sh from rebasing).
#
# Detects: modified/added/deleted tracked files, untracked stories/ docs/ .claude/
# Ignores: .claude/.lock (transient), .gitignore-d files, untracked files outside stories/docs/.claude/
# Exit 1 = dirty (blocks session exit), Exit 0 = clean (allows)

ROOT_DIR="${CLAUDE_PROJECT_DIR:-.}"
cd "$ROOT_DIR" || exit 0

# Graceful fallback: not a git repo or git unavailable
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  exit 0
fi

# Get porcelain status (respects .gitignore automatically)
STATUS=$(git status --porcelain 2>/dev/null)

# No changes at all — clean exit
if [ -z "$STATUS" ]; then
  exit 0
fi

# Modified/added/deleted/renamed tracked files (anything that isn't untracked ??)
# Exclude only .claude/.lock (transient session state) — NOT .claude/hooks/, rules/, settings.json
DIRTY_TRACKED=$(echo "$STATUS" | grep -v '^?? ' | grep -v -E '\.claude/\.lock' || true)

# Untracked files in docs/ and .claude/ (hooks, rules, settings are project files)
# Note: stories/ excluded — story files are gitignored (DB is source of truth)
DIRTY_UNTRACKED=$(echo "$STATUS" | grep -E '^\?\? (docs/|\.claude/)' || true)

# Combine
ALL_DIRTY=$(printf '%s\n%s' "$DIRTY_TRACKED" "$DIRTY_UNTRACKED" | sed '/^$/d')

if [ -z "$ALL_DIRTY" ]; then
  exit 0  # Only irrelevant changes (e.g., .claude/ internal, temp/)
fi

# Count dirty files
COUNT=$(echo "$ALL_DIRTY" | wc -l | tr -d ' ')

echo ""
echo "⚠️  Dirty worktree — $COUNT file(s) uncommitted:"
echo "$ALL_DIRTY" | while read -r line; do
  [ -n "$line" ] && echo "  $line"
done
echo ""
echo "Commit:  git add <files> && git commit -m 'chore: session cleanup'"
echo "Discard: git checkout -- <file> (tracked) or rm <file> (untracked)"
exit 1
