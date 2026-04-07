#!/usr/bin/env bash
# PostToolUse hook: Intervention poll — surfaces pending interventions as system context
# (EXTSESSION Story: 2026-03-06.04-05-28)
#
# Polls GET /agents/by-name/{AGENT_NAME}/interventions for pending items
# and outputs them as additionalContext so Claude sees queued interventions
# on the next tool call. Clear-on-read semantics on the API side.
#
# AC1: Fires on Bash, Write, Edit, Agent tool completions
# AC2: Outputs [INTERVENTION] {type}: {message} (queued: {queued_at}) per item
# AC3: Clear-on-read preserved by GET endpoint
# AC4: 10-second throttle via /tmp/claude-intervention-poll-last-{SESSION_ID}
# AC5: Silent skip when no EUPRAXIS_AGENT_NAME or SESSION_ID
# AC6: Fail-open on API errors
# AC7: No-op when no interventions pending
#
# Marker: /tmp/claude-intervention-poll-last-{SESSION_ID} (throttle)
# Cleared by: post-ship-cleanup.sh
#
# Matcher: Bash, Write, Edit, Agent

INPUT=$(cat)

# Agent identity from env (2026-03-15.03-24-22 — name-based, no UUID resolution)
AGENT_NAME="${EUPRAXIS_AGENT_NAME:-}"
if [ -z "$AGENT_NAME" ]; then
  exit 0
fi

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
MACHINE_ID=$(resolve_machine_id)
MARKER_ID=$(resolve_marker_id)
if [ -z "$MARKER_ID" ]; then
  exit 0
fi

# AC4: 10-second throttle
THROTTLE_FILE="/tmp/claude-intervention-poll-last-${MARKER_ID}"
if [ -f "$THROTTLE_FILE" ]; then
  now=$(date +%s)
  # macOS stat
  last_poll=$(stat -f %m "$THROTTLE_FILE" 2>/dev/null)
  if [ -z "$last_poll" ]; then
    # Linux stat
    last_poll=$(stat -c %Y "$THROTTLE_FILE" 2>/dev/null || echo 0)
  fi
  elapsed=$((now - last_poll))
  if [ "$elapsed" -lt 10 ]; then
    exit 0
  fi
fi

# ─── Poll hub API for interventions ─────────────────────────

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"

hub_url=$(_hub_resolve_url)
token=$(_hub_resolve_token)

if [ -n "$token" ]; then
  response=$(curl -sf --connect-timeout 3 --max-time 5 \
    -H "Authorization: Bearer $token" \
    "${hub_url}/api/v1/agents/by-name/${AGENT_NAME}/interventions?machine_id=${MACHINE_ID}" 2>/dev/null)
else
  response=$(curl -sf --connect-timeout 3 --max-time 5 \
    "${hub_url}/api/v1/agents/by-name/${AGENT_NAME}/interventions?machine_id=${MACHINE_ID}" 2>/dev/null)
fi

# AC6: Fail-open — if curl failed, exit silently
if [ $? -ne 0 ] || [ -z "$response" ]; then
  exit 0
fi

# Update throttle marker on successful poll
touch "$THROTTLE_FILE" 2>/dev/null

# ─── Parse interventions ────────────────────────────────────

count=$(echo "$response" | jq -r '.interventions | length' 2>/dev/null)

# AC7: No-op when no interventions pending
if [ -z "$count" ] || [ "$count" -eq 0 ]; then
  exit 0
fi

# AC2: Build [INTERVENTION] lines — one per item, FIFO order
lines=""
for i in $(seq 0 $((count - 1))); do
  iv_type=$(echo "$response" | jq -r ".interventions[$i].type // empty")
  iv_message=$(echo "$response" | jq -r ".interventions[$i].message // empty")
  iv_queued=$(echo "$response" | jq -r ".interventions[$i].queued_at // empty")
  line="[INTERVENTION] ${iv_type}: ${iv_message} (queued: ${iv_queued})"
  if [ -z "$lines" ]; then
    lines="$line"
  else
    lines="${lines}\n${line}"
  fi
done

# Output as additionalContext so Claude sees it as system context
# Use jq for proper JSON escaping of the intervention text
context=$(printf '%b' "$lines")
jq -n --arg ctx "$context" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: $ctx
  }
}'

exit 0
