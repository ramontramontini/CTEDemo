#!/usr/bin/env bash
# Stop hook: Capture session token usage and POST to story via hub API.
# (Story: 2026-03-30.20-30-27, BUG fix: 2026-03-30.23-01-52)
#
# Fires at session end. Detects active in_progress story, determines phase,
# and POSTs token usage data.
#
# Data sources (checked in order):
#   1. Env var: CLAUDE_SESSION_TOKENS (JSON — legacy, checked first for speed)
#   2. File: /tmp/claude-session-tokens-{AGENT_ID} (legacy fallback)
#   3. JSONL: ~/.claude/projects/{hash}/{session}.jsonl (primary — parses
#      Claude Code conversation files via aggregate-session-tokens.sh)
#
# Always exits 0 (fail-open, best-effort). Must run BEFORE
# stop-keepalive-cleanup.sh which clears agent's story linkage.

INPUT=$(cat)
_project_dir="${CLAUDE_PROJECT_DIR:-.}"
source "$_project_dir/.claude/hooks/lib/hub-query.sh"

AGENT_ID=$(resolve_agent_id)
if [ -z "$AGENT_ID" ]; then
  exit 0
fi

# 1. Get active in_progress story for this agent
story=$(hub_get_active_story "$AGENT_ID")
if [ -z "$story" ]; then
  exit 0
fi

story_uuid=$(hub_get_story_field "$story" "id")
story_phase=$(hub_get_story_field "$story" "phase")
if [ -z "$story_uuid" ]; then
  exit 0
fi

# 2. Check for token data source (legacy first, then JSONL)
TOKEN_DATA=""
TOKEN_DATA_FILE="/tmp/claude-session-tokens-${AGENT_ID}"

if [ -n "${CLAUDE_SESSION_TOKENS:-}" ]; then
  if echo "$CLAUDE_SESSION_TOKENS" | jq -e '.input_tokens and .output_tokens' >/dev/null 2>&1; then
    TOKEN_DATA="$CLAUDE_SESSION_TOKENS"
  fi
elif [ -f "$TOKEN_DATA_FILE" ]; then
  local_data=$(cat "$TOKEN_DATA_FILE" 2>/dev/null)
  if echo "$local_data" | jq -e '.input_tokens and .output_tokens' >/dev/null 2>&1; then
    TOKEN_DATA="$local_data"
  fi
fi

# 3. JSONL aggregation (primary data source — BUG 2026-03-30.23-01-52)
if [ -z "$TOKEN_DATA" ]; then
  AGGREGATOR="$_project_dir/.claude/hooks/lib/aggregate-session-tokens.sh"
  if [ -x "$AGGREGATOR" ]; then
    TOKEN_DATA=$(bash "$AGGREGATOR" 2>/dev/null) || TOKEN_DATA=""
  fi
fi

# No data source available — exit cleanly (no zero-token placeholders)
if [ -z "$TOKEN_DATA" ]; then
  exit 0
fi

# 4. Extract token counts from data source
input_tokens=$(echo "$TOKEN_DATA" | jq -r '.input_tokens // 0')
output_tokens=$(echo "$TOKEN_DATA" | jq -r '.output_tokens // 0')
cache_read_tokens=$(echo "$TOKEN_DATA" | jq -r '.cache_read_tokens // 0')
cache_write_tokens=$(echo "$TOKEN_DATA" | jq -r '.cache_write_tokens // 0')

# Skip if all tokens are zero (no meaningful data)
if [ "$input_tokens" = "0" ] && [ "$output_tokens" = "0" ]; then
  exit 0
fi

# Map story phase to token-usage phase value
phase="downstream"
if [ "$story_phase" = "upstream" ]; then
  phase="upstream"
fi

# 5. POST token usage to hub API
hub_url=$(_hub_resolve_url)
token=$(_hub_resolve_token)
auth_header=""
[ -n "$token" ] && auth_header="-H \"Authorization: Bearer $token\""

eval curl -sf --connect-timeout 3 --max-time 5 \
  -X POST \
  -H "Content-Type: application/json" \
  $auth_header \
  -d "'{
    \"input_tokens\": $input_tokens,
    \"output_tokens\": $output_tokens,
    \"cache_read_tokens\": $cache_read_tokens,
    \"cache_write_tokens\": $cache_write_tokens,
    \"phase\": \"$phase\",
    \"session_id\": \"$AGENT_ID\"
  }'" \
  "'${hub_url}/api/v1/stories/${story_uuid}/token-usage'" >/dev/null 2>&1 || true

# Clean up legacy token data file if it was used
rm -f "$TOKEN_DATA_FILE" 2>/dev/null

exit 0
