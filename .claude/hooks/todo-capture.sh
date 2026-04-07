#!/usr/bin/env bash
# PostToolUse hook: Capture TodoWrite task progress and push to story via hub API
# (Story: 2026-03-14.02-26-53 — Todo Progress Plumbing, AC1)
# (BUG: 2026-03-14.20-24-09 — Todo Progress on Story Entity, AC2)
#
# Fires on TodoWrite tool completion. Counts completed/total todos,
# writes to /tmp/claude-todo-progress-{SESSION_ID} (backward compat),
# then PATCHes the active story with {todo_completed, todo_total} via hub API.
#
# Matcher: TodoWrite

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Only process TodoWrite calls
if [ "$TOOL_NAME" != "TodoWrite" ]; then
  exit 0
fi

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
MARKER_ID=$(resolve_marker_id)
if [ -z "$MARKER_ID" ]; then
  exit 0
fi

# Count completed and total from tool_input.todos array
# Count resolved tasks (completed + skipped) — matches RESOLVED_TASK_STATUSES in entity.py
completed=$(echo "$INPUT" | jq '[.tool_input.todos[] | select(.status == "completed" or .status == "skipped")] | length')
total=$(echo "$INPUT" | jq '.tool_input.todos | length')

# Atomic write: temp file then mv (backward compat for keepalive)
PROGRESS_FILE="/tmp/claude-todo-progress-${MARKER_ID}"
TEMP_FILE="${PROGRESS_FILE}.tmp.$$"
jq -n --argjson c "$completed" --argjson t "$total" \
  '{todo_completed: $c, todo_total: $t}' > "$TEMP_FILE"
mv "$TEMP_FILE" "$PROGRESS_FILE"

# ─── Batch mode advisory validation (2026-03-31.15-29-27) ────
# When in batch mode, warn on TodoWrite items that don't match AC or quality patterns.
# Advisory only — never blocks the TodoWrite operation.
EXEC_MODE_FILE="/tmp/claude-sticky-exec-mode-${MARKER_ID}"
if [ -f "$EXEC_MODE_FILE" ] && [ "$(cat "$EXEC_MODE_FILE" 2>/dev/null)" = "batch" ]; then
  echo "$INPUT" | jq -r '.tool_input.todos[] | select(.status != "completed" and .status != "skipped") | .content' 2>/dev/null | while read -r item; do
    [ -z "$item" ] && continue
    # Allow [ACN] prefix pattern (from /pull per-AC tracking)
    echo "$item" | grep -qE '^\[AC[0-9]+\]' && continue
    # Allow known quality-phase items from /pull Step 4
    case "$item" in
      "Run all test suites"|"Verify gate stamps"|"Update documentation"|\
      "Fill compliance checklist"|"Fill drift review"|\
      "PATCH downstream content to DB"|"Epic write-back (if applicable)"|\
      "Ship review (Gate Keeper)"|"Record session recap"|\
      "Stage files for ship-review"|"BUG runtime verification"|\
      "Code review (Gate Keeper)"|"PATCH downstream + compliance") continue ;;
    esac
    echo "todo-capture: WARNING — batch mode: non-AC item detected: $item" >&2
  done
fi

# ─── Resolve active story UUID (BUG 2026-03-18.21-30-08) ────
# API-first: query hub for agent's in-progress story.
# Fallback: read from temp file (when API unreachable).
# Handles missing files AND stale files (pointing to old stories).

STORY_UUID_FILE="/tmp/claude-active-story-uuid-${MARKER_ID}"

resolve_active_story_uuid() {
  # Primary: query hub API for agent's in-progress story
  local response api_uuid
  response=$(hub_query_stories "in_progress" "$MARKER_ID" 2>/dev/null)
  api_uuid=$(printf '%s' "$response" | jq -r '.data[0].id // empty' 2>/dev/null)
  if [ -n "$api_uuid" ]; then
    # Cache resolved UUID to file for subsequent calls
    echo "$api_uuid" > "$STORY_UUID_FILE"
    echo "$api_uuid"
    return 0
  fi
  # Fallback: read from file (API unreachable)
  if [ -f "$STORY_UUID_FILE" ]; then
    cat "$STORY_UUID_FILE"
    return 0
  fi
  # Both failed — no story to PATCH
  return 1
}

story_uuid=$(resolve_active_story_uuid) || exit 0

# Resolve hub URL and token
hub_url=$(_hub_resolve_url)
token=$(_hub_resolve_token)

# PATCH story with todo progress + enriched task list
# - [ACN] prefix in content → ac_index=N, prefix stripped
# - created_at = current UTC timestamp
# - session_id = MARKER_ID (session identifier)
NOW=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
payload=$(echo "$INPUT" | jq --arg sid "$MARKER_ID" --arg now "$NOW" '{
  tasks: [.tool_input.todos[] | {
    content: (if (.content | test("^\\[AC[0-9]+\\]\\s*")) then (.content | sub("^\\[AC[0-9]+\\]\\s*"; "")) else .content end),
    status: .status,
    ac_index: (if (.content | test("^\\[AC[0-9]+\\]")) then (.content | capture("^\\[AC(?<n>[0-9]+)\\]") | .n | tonumber) else null end),
    created_at: $now,
    session_id: $sid
  }],
  todo_completed: ([.tool_input.todos[] | select(.status == "completed" or .status == "skipped")] | length),
  todo_total: (.tool_input.todos | length)
}')

if [ -n "$token" ]; then
  curl -sf --connect-timeout 3 --max-time 5 \
    -X PATCH \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $token" \
    -d "$payload" \
    "${hub_url}/api/v1/stories/${story_uuid}" \
    >/dev/null 2>&1 || true
else
  curl -sf --connect-timeout 3 --max-time 5 \
    -X PATCH \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "${hub_url}/api/v1/stories/${story_uuid}" \
    >/dev/null 2>&1 || true
fi

exit 0
