#!/usr/bin/env bash
# Sync all worktrees with origin/main
# Lives in main/ worktree. Auto-detects repo root (parent of .bare/).
#
# Usage:
#   ./sync.sh              # Safe sync (skips dirty worktrees), once
#   ./sync.sh --force      # Force sync (stash dirty worktrees, rebase, restore), once
#   ./sync.sh --force-hard # Nuclear option (discard uncommitted changes, rebase), once
#   ./sync.sh --loop       # Safe sync every 10 seconds
#   ./sync.sh --loop --force  # Force sync every 10 seconds

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -d "$ROOT/.bare" ]; then
  echo "Error: cannot find .bare/ repo root (expected at $ROOT/.bare)" >&2
  exit 1
fi

cd "$ROOT"

MODE="safe"
LOOP=false

for arg in "$@"; do
  case "$arg" in
    --loop)      LOOP=true ;;
    --force)     MODE="force" ;;
    --force-hard) MODE="force-hard" ;;
  esac
done

# Cross-platform helpers (colors, etc.)
source "$SCRIPT_DIR/scripts/lib/portable.sh"

# Colors (from portable.sh — respects NO_COLOR and terminal detection)
GREEN="$PORTABLE_GREEN"
YELLOW="$PORTABLE_YELLOW"
RED="$PORTABLE_RED"
CYAN="$PORTABLE_CYAN"
NC="$PORTABLE_NC"

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
info() { echo -e "  ${CYAN}→${NC} $1"; }

# ─── Pre-flight: check for active Claude sessions ───
check_claude_lock() {
  local dir="$1"
  local lock_file="${dir}/.claude/.lock"
  if [ -f "$lock_file" ]; then
    local lock_age=$(( $(date +%s) - $(stat -f %m "$lock_file" 2>/dev/null || stat -c %Y "$lock_file" 2>/dev/null || echo 0) ))
    if [ "$lock_age" -lt 300 ]; then
      return 0  # Active (lock < 5 min old)
    fi
  fi
  return 1  # Not active
}

run_sync() {

# ─── Single fetch for all worktrees (shared .bare) ───
echo -e "\n${CYAN}Fetching origin...${NC}"
git --git-dir=.bare fetch origin
ok "Fetch complete"

# ─── Prune dead worktrees (directory deleted but git still tracks) ───
prune_output=$(git --git-dir=.bare worktree prune -v 2>&1)
if [ -n "$prune_output" ]; then
  echo -e "\n${CYAN}Pruned dead worktrees:${NC}"
  echo "$prune_output" | while read -r line; do
    warn "$line"
  done
fi

# ─── Auto-detect worktrees (main first, then agents sorted) ───
ALL_DIRS=$(git --git-dir=.bare worktree list --porcelain \
  | grep '^worktree ' | sed 's|^worktree ||' \
  | xargs -I{} basename {} | grep -v '\.bare' | sort)
WORKTREE_DIRS="$(echo "$ALL_DIRS" | grep '^main$' || true) $(echo "$ALL_DIRS" | grep -v '^main$' | sort || true)"
WORKTREE_DIRS=$(echo $WORKTREE_DIRS)  # normalize whitespace

# ─── Status report ───
echo -e "\n${CYAN}Worktree status:${NC}"
for dir in $WORKTREE_DIRS; do
  if [ ! -d "$dir" ]; then
    fail "${dir}: directory missing (pruned above or remove manually)"
    continue
  fi

  dirty=$(git -C "$dir" status --porcelain 2>/dev/null | head -1)
  branch=$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null)
  behind=$(git -C "$dir" rev-list --count HEAD..origin/main 2>/dev/null || echo "?")

  status=""
  if [ -n "$dirty" ]; then
    status="${YELLOW}dirty${NC}"
  else
    status="${GREEN}clean${NC}"
  fi

  if [ "$behind" = "0" ]; then
    sync_status="${GREEN}up-to-date${NC}"
  else
    sync_status="${YELLOW}${behind} behind${NC}"
  fi

  echo -e "  ${dir}: [${status}] [${sync_status}] on ${branch}"
done

# ─── Sync each worktree ───
echo -e "\n${CYAN}Syncing (mode: ${MODE})...${NC}"

synced=0
skipped=0
failed=0
stashed=0

for dir in $WORKTREE_DIRS; do
  if [ ! -d "$dir" ]; then
    continue
  fi

  echo -e "\n${CYAN}${dir}:${NC}"

  dirty=$(git -C "$dir" status --porcelain 2>/dev/null | head -1)
  behind=$(git -C "$dir" rev-list --count HEAD..origin/main 2>/dev/null || echo "0")

  # Already up to date
  if [ "$behind" = "0" ] && [ -z "$dirty" ]; then
    ok "Already up to date"
    synced=$((synced + 1))
    continue
  fi

  # Clean worktree — rebase directly
  if [ -z "$dirty" ]; then
    if git -C "$dir" rebase origin/main 2>/dev/null; then
      ok "Rebased (${behind} commits)"
      synced=$((synced + 1))
    else
      git -C "$dir" rebase --abort 2>/dev/null
      fail "Rebase failed — conflicts (aborted, no changes made)"
      failed=$((failed + 1))
    fi
    continue
  fi

  # ─── Dirty worktree handling ───
  case "$MODE" in
    safe)
      warn "Dirty worktree — skipped (use --force to stash+rebase)"
      skipped=$((skipped + 1))
      ;;

    force)
      # Check for active Claude session
      if check_claude_lock "$dir"; then
        warn "Active Claude session detected — skipped (use --force-hard to override)"
        skipped=$((skipped + 1))
        continue
      fi

      info "Stashing uncommitted changes..."
      stash_msg="sync.sh auto-stash $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      if git -C "$dir" stash push -m "$stash_msg" --include-untracked 2>/dev/null; then
        stashed=$((stashed + 1))

        if git -C "$dir" rebase origin/main 2>/dev/null; then
          ok "Rebased (${behind} commits)"
          synced=$((synced + 1))

          # Restore stash
          if git -C "$dir" stash pop 2>/dev/null; then
            ok "Stash restored"
          else
            git -C "$dir" checkout -- . 2>/dev/null
            warn "Stash restore had conflicts — stash preserved, run 'git -C ${dir} stash pop' manually"
          fi
        else
          git -C "$dir" rebase --abort 2>/dev/null
          git -C "$dir" stash pop 2>/dev/null
          fail "Rebase failed — conflicts (aborted, stash restored)"
          failed=$((failed + 1))
        fi
      else
        warn "Stash failed — skipped"
        skipped=$((skipped + 1))
      fi
      ;;

    force-hard)
      warn "Discarding uncommitted changes..."
      git -C "$dir" checkout -- . 2>/dev/null
      git -C "$dir" clean -fd 2>/dev/null

      if git -C "$dir" rebase origin/main 2>/dev/null; then
        ok "Rebased (${behind} commits) — uncommitted changes discarded"
        synced=$((synced + 1))
      else
        git -C "$dir" rebase --abort 2>/dev/null
        fail "Rebase failed even after clean — resolve manually"
        failed=$((failed + 1))
      fi
      ;;
  esac
done

# ─── Summary ───
echo -e "\n${CYAN}Summary:${NC}"
echo -e "  Synced: ${GREEN}${synced}${NC} | Skipped: ${YELLOW}${skipped}${NC} | Failed: ${RED}${failed}${NC} | Stashed: ${CYAN}${stashed}${NC}"

if [ "$skipped" -gt 0 ] && [ "$MODE" = "safe" ]; then
  echo -e "\n  ${YELLOW}Tip:${NC} Run ${CYAN}./sync.sh --force${NC} to stash dirty worktrees and sync them"
fi
if [ "$failed" -gt 0 ]; then
  echo -e "\n  ${RED}Some worktrees had conflicts. Resolve manually.${NC}"
fi

if [ "$synced" -gt 0 ]; then
  echo -e "\n  ${CYAN}Reload:${NC} Active agents should reload directives:"
  echo -e "  ${CYAN}  ls .claude/rules/*.md${NC}"
fi

echo ""

} # end run_sync

# ─── Execute ───
if [ "$LOOP" = true ]; then
  echo -e "${CYAN}Loop mode: syncing every 10 seconds (Ctrl+C to stop)${NC}"
  while true; do
    run_sync
    echo -e "\n${CYAN}Next sync in 10 seconds... (Ctrl+C to stop)${NC}"
    sleep 10
  done
else
  run_sync
fi
