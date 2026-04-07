#!/usr/bin/env bash
# Board state check — queries hub API for story status.
# Replaces: ls stories/doing/*.md stories/todo/*.md 2>/dev/null
#
# Used by bootstrap and post-push reload sequences.
# Hooks detect "board-check" in the command to mark the step complete.

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$SCRIPT_DIR/.claude/hooks/lib/hub-query.sh"
CLAUDE_PROJECT_DIR="$SCRIPT_DIR"

echo "=== Board State (from hub API) ==="

# Single API call for board summary
hub_url=$(_hub_resolve_url)
token=$(_hub_resolve_token)
project_id=$(_hub_resolve_project_id)
board_url="${hub_url}/api/v1/queue/board-summary"
[ -n "$project_id" ] && board_url="${board_url}?project_id=${project_id}"

if [ -n "$token" ]; then
  response=$(curl -sf --connect-timeout 3 --max-time 5 \
    -H "Authorization: Bearer $token" \
    "$board_url" 2>/dev/null)
else
  response=$(curl -sf --connect-timeout 3 --max-time 5 \
    "$board_url" 2>/dev/null)
fi

if [ $? -ne 0 ] || [ -z "$response" ]; then
  echo ""
  echo "Hub API unreachable at $hub_url"
  echo ""
  exit 0
fi

# In-progress stories
ip_count=$(echo "$response" | jq -r '.in_progress | length' 2>/dev/null)
ip_count=${ip_count:-0}
echo ""
echo "Doing: $ip_count"
if [ "$ip_count" -gt 0 ]; then
  echo "$response" | jq -r '.in_progress[] | "  \(.story_id) | \(.type) | \(.title)"' 2>/dev/null
fi

# Available stories
avail_count=$(echo "$response" | jq -r '.available_count // 0' 2>/dev/null)
avail_count=${avail_count:-0}
echo ""
echo "Todo: $avail_count"
if [ "$avail_count" -gt 0 ]; then
  echo "$response" | jq -r '.available[] | "  \(.story_id) | \(.type) | \(.title)"' 2>/dev/null
fi

echo ""
