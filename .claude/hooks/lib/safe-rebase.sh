#!/usr/bin/env bash
# Stash-aware git rebase — shared library for hooks and skills.
#
# Usage: safe_rebase <project_dir> [target_ref] [mode]
#   project_dir: git working directory
#   target_ref:  ref to rebase onto (default: origin/main)
#   mode:        "pull" for main branch (git pull --rebase origin main)
#                "rebase" for agent branches (default)
#
# Returns:
#   0 = success (or graceful degradation on rebase conflict)
#   1 = stash pop conflict (rebased but uncommitted changes conflict)
#
# Sets shell variables (for caller inspection):
#   SAFE_REBASE_STASHED   — "true" if changes were stashed, "false" otherwise
#   SAFE_REBASE_CONFLICT  — "none", "rebase" (aborted, stash restored), or "pop" (stash preserved)
#
# Stderr: diagnostic messages for hook context injection.
# Never exits non-zero fatally — all failure modes are recoverable.

safe_rebase() {
  local dir="${1:-.}"
  local target="${2:-origin/main}"
  local mode="${3:-rebase}"

  SAFE_REBASE_STASHED="false"
  SAFE_REBASE_CONFLICT="none"

  # ── Step 0: Detect and abort in-progress rebase ──────────────
  if [ -d "$dir/.git/rebase-apply" ] || [ -d "$dir/.git/rebase-merge" ]; then
    echo "safe-rebase: Aborting in-progress rebase from previous session." >&2
    git -C "$dir" rebase --abort 2>/dev/null || true
  fi

  # ── Step 1: Detect dirty worktree ────────────────────────────
  local status
  status=$(git -C "$dir" status --porcelain 2>/dev/null)

  if [ -n "$status" ]; then
    # ── Step 2: Stash uncommitted changes ──────────────────────
    local stash_msg="safe-rebase auto-stash $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    local stash_output
    stash_output=$(git -C "$dir" stash push -m "$stash_msg" --include-untracked 2>&1)

    if [ $? -ne 0 ]; then
      echo "safe-rebase: Stash push failed — skipping rebase (fail-open)." >&2
      echo "safe-rebase: $stash_output" >&2
      return 0
    fi

    # Verify something was actually stashed (not "No local changes to save")
    if echo "$stash_output" | grep -qi "no local changes"; then
      SAFE_REBASE_STASHED="false"
    else
      SAFE_REBASE_STASHED="true"
      echo "safe-rebase: Stashed uncommitted changes." >&2
    fi
  fi

  # ── Step 3: Rebase ──────────────────────────────────────────
  local rebase_output
  if [ "$mode" = "pull" ]; then
    rebase_output=$(git -C "$dir" pull --rebase origin main 2>&1)
  else
    rebase_output=$(git -C "$dir" rebase "$target" 2>&1)
  fi

  if [ $? -ne 0 ]; then
    # Check for conflict
    if echo "$rebase_output" | grep -qiE 'conflict|could not apply|merge conflict'; then
      git -C "$dir" rebase --abort 2>/dev/null || true
      echo "safe-rebase: Rebase conflict detected — aborted." >&2

      # Restore stash if we stashed
      if [ "$SAFE_REBASE_STASHED" = "true" ]; then
        git -C "$dir" stash pop 2>/dev/null || true
        echo "safe-rebase: Stash restored — worktree back to pre-rebase state." >&2
      fi

      SAFE_REBASE_CONFLICT="rebase"
      echo "safe-rebase: Running on stale code. Resolve with 'git rebase origin/main'." >&2
      return 0  # Let session start — agent can help resolve
    fi

    # Non-conflict rebase error (e.g., dirty worktree that slipped through)
    if [ "$SAFE_REBASE_STASHED" = "true" ]; then
      git -C "$dir" stash pop 2>/dev/null || true
    fi
    echo "safe-rebase: Rebase failed (non-conflict) — continuing." >&2
    return 0
  fi

  # ── Step 4: Pop stash if needed ─────────────────────────────
  if [ "$SAFE_REBASE_STASHED" = "true" ]; then
    local pop_output
    pop_output=$(git -C "$dir" stash pop 2>&1)

    if [ $? -ne 0 ] || echo "$pop_output" | grep -qiE 'conflict|CONFLICT'; then
      # Pop conflict — DO NOT checkout. Leave conflict markers. Preserve stash.
      SAFE_REBASE_CONFLICT="pop"
      echo "safe-rebase: Stash pop conflict — changes preserved in git stash." >&2
      echo "safe-rebase: Resolve conflicts or run 'git stash pop' to retry." >&2
      return 1
    fi

    echo "safe-rebase: Stash restored — uncommitted changes intact." >&2
  fi

  return 0
}
