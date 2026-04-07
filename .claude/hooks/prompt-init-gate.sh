#!/usr/bin/env bash
# UserPromptSubmit hook: Self-executing session init.
# First prompt: runs full bootstrap (git rebase, board-check, sync-agent-status,
# generate-launch-json), sets /tmp marker, injects context via stdout.
# Subsequent prompts: marker check only (fast no-op).
#
# Fail-closed: rebase conflict or unresolvable agent identity → exit 2 (block).
# Fail-open: hub unreachable, validate-env, generate-launch-json → continue.
# Whitelist: /init, /resume, /help pass through regardless of marker state.

set -o pipefail

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh" 2>/dev/null || true

PROJECT_DIR=$(_hub_resolve_project_dir 2>/dev/null || echo ".")

# ─── Resolve agent identity ────────────────────────────────
AGENT_ID=$(resolve_agent_id 2>/dev/null || true)

if [ -z "$AGENT_ID" ]; then
  echo "Agent identity not configured. Set EUPRAXIS_AGENT_NAME in .env, then retry." >&2
  exit 2
fi

# ─── Fast path: already initialized ────────────────────────
MARKER="/tmp/claude-session-init-${AGENT_ID}"

if [ -f "$MARKER" ]; then
  exit 0
fi

# ─── Whitelist: /init, /resume, /help ───────────────────────
if echo "$PROMPT" | grep -qiE '^\s*/init(\s|$)'; then
  # /init will run its own bootstrap — touch marker so second prompt skips
  touch "$MARKER"
  exit 0
fi
if echo "$PROMPT" | grep -qiE '^\s*/(resume|help)(\s|$)'; then
  exit 0
fi

# ─── Run init steps ────────────────────────────────────────
CONTEXT=""

# Step 1: Validate agent environment (fail-open)
bash "$PROJECT_DIR/scripts/validate-agent-env.sh" 2>/dev/null || true

# Step 2: Git fetch + safe rebase (stash-aware, never blocks session)
source "$HOOK_DIR/lib/safe-rebase.sh"

BRANCH=$(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || echo "")
git -C "$PROJECT_DIR" fetch origin 2>/dev/null || true

if [ "$BRANCH" = "main" ]; then
  safe_rebase "$PROJECT_DIR" "origin/main" "pull"
else
  safe_rebase "$PROJECT_DIR" "origin/main"
fi
REBASE_RC=$?

# Capture worktree status for agent display (always report)
WT_STATUS=$(git -C "$PROJECT_DIR" status --porcelain 2>/dev/null | head -20)
STASH_COUNT=$(git -C "$PROJECT_DIR" stash list 2>/dev/null | grep -c "safe-rebase auto-stash" || echo "0")
if [ -n "$WT_STATUS" ]; then
  WT_DIRTY="true"
  WT_COUNT=$(echo "$WT_STATUS" | wc -l | tr -d ' ')
else
  WT_DIRTY="false"
  WT_COUNT="0"
fi

case $REBASE_RC in
  0) ;; # Success (clean rebase, stash+pop, or graceful rebase-conflict fallback)
  1)
    # Pop conflict: rebased but stashed changes conflict with new code
    # Session starts — agent resolves interactively. Stash preserved.
    ;;
esac

# Step 3: Load directives
RULES=$(ls "$PROJECT_DIR"/.claude/rules/*.md 2>/dev/null | xargs -n1 basename 2>/dev/null || echo "(none found)")

# Step 4: Board check (fail-open)
BOARD_OUTPUT=$(bash "$PROJECT_DIR/scripts/board-check.sh" 2>/dev/null || echo "(hub unreachable)")

# Step 5: Sync agent status (fail-open)
bash "$PROJECT_DIR/scripts/sync-agent-status.sh" 2>/dev/null || true

# Step 5b: Agent assignment conflict check (fail-open)
# If agent already has an active story (in_progress or claimed), block session start.
# Defense-in-depth for the "one story at a time" invariant.
ACTIVE_STORY=""
ACTIVE_STATUS=""
for check_status in in_progress claimed; do
  check_response=$(hub_query_stories "$check_status" "$AGENT_ID" 2>/dev/null) || continue
  check_story=$(hub_get_first_story "$check_response" 2>/dev/null)
  if [ -n "$check_story" ]; then
    ACTIVE_STORY="$check_story"
    ACTIVE_STATUS="$check_status"
    break
  fi
done

if [ -n "$ACTIVE_STORY" ]; then
  active_title=$(printf '%s' "$ACTIVE_STORY" | jq -r '.title // "unknown"' 2>/dev/null)
  active_sid=$(printf '%s' "$ACTIVE_STORY" | jq -r '.story_id // "unknown"' 2>/dev/null)
  # Warn but do NOT block — agent needs a live session to /resume or /shelve.
  # Previous exit 2 here created a deadlock: agent can't start session to resume,
  # can't resume without a session.
  ACTIVE_STORY_CONTEXT="WARNING: Agent '$AGENT_ID' has active story: [$ACTIVE_STATUS] $active_title ($active_sid). Use /resume to continue or /shelve to release."
fi

# Step 6: Generate launch.json if missing (fail-open)
if [ ! -f "$PROJECT_DIR/.claude/launch.json" ]; then
  bash "$PROJECT_DIR/scripts/generate-launch-json.sh" 2>/dev/null || true
fi

# ─── Set marker ────────────────────────────────────────────
touch "$MARKER"

# ─── Resolve mode ──────────────────────────────────────────
DATA_MODE="${DATA_MODE:-}"
if [ -z "$DATA_MODE" ] && [ -f "$PROJECT_DIR/.env" ]; then
  DATA_MODE=$(grep -E '^DATA_MODE=' "$PROJECT_DIR/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "unknown")
fi
DATA_MODE="${DATA_MODE:-unknown}"

# ─── Build worktree status line ────────────────────────────
WT_LINE="Worktree: clean"
WT_WARNING=""
if [ "$WT_DIRTY" = "true" ]; then
  WT_LINE="Worktree: dirty ($WT_COUNT files)"
  if [ "$STASH_COUNT" -gt 0 ] 2>/dev/null; then
    WT_LINE="$WT_LINE | Stash: $STASH_COUNT safe-rebase entries"
  fi
fi
if [ "$SAFE_REBASE_CONFLICT" = "rebase" ]; then
  WT_WARNING="WARNING: Rebase conflict — running on stale code. Resolve with 'git fetch origin && git rebase origin/main'."
elif [ "$SAFE_REBASE_CONFLICT" = "pop" ]; then
  WT_WARNING="WARNING: Stash pop conflict — uncommitted changes in git stash. Resolve with 'git stash pop'."
fi

# ─── Emit context to stdout ────────────────────────────────
cat <<EOF
AGENT DISPLAY (MANDATORY): Render the init status below in your FIRST response to the user. The user cannot see system-reminder content — you must relay it.

[Session initialized — directives loaded, board synced]

Rules: $RULES

$BOARD_OUTPUT

$WT_LINE
$([ -n "$WT_WARNING" ] && echo "$WT_WARNING")
$([ -n "$ACTIVE_STORY_CONTEXT" ] && echo "$ACTIVE_STORY_CONTEXT")

Mode: $DATA_MODE | Standards: TDD, story-driven
EOF
