#!/usr/bin/env bash
# PreToolUse hook: Push awaiting_input signal when agent needs user attention.
#
# Only fires for tools that ALWAYS wait for user input:
#   AskUserQuestion: immediate push (user must answer question)
#   ExitPlanMode: immediate push (user must approve/reject plan)
#
# Uses sessions/signal endpoint (API-centric signal architecture).
#
# Matcher: AskUserQuestion, ExitPlanMode (PreToolUse)

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "AskUserQuestion"')

# Agent identity from env with .env fallback
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/hub-query.sh"
AGENT_NAME=$(resolve_agent_id)
if [ -z "$AGENT_NAME" ]; then
  exit 0
fi
MACHINE_ID=$(resolve_machine_id)

# ─── Route by tool type ───────────────────────────────────────
case "$TOOL_NAME" in
  AskUserQuestion|ExitPlanMode)
    # Push awaiting_input via sessions/signal endpoint (by-name)
    hub_url=$(_hub_resolve_url)
    token=$(_hub_resolve_token)
    payload='{"signal": "awaiting_input"}'

    if [ -n "$token" ]; then
      curl -sf --connect-timeout 3 --max-time 5 \
        -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -d "$payload" \
        "${hub_url}/api/v1/agents/by-name/${AGENT_NAME}/sessions/signal?machine_id=${MACHINE_ID}" >/dev/null 2>&1
    else
      curl -sf --connect-timeout 3 --max-time 5 \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "${hub_url}/api/v1/agents/by-name/${AGENT_NAME}/sessions/signal?machine_id=${MACHINE_ID}" >/dev/null 2>&1
    fi
    ;;
esac

# Invalidate heartbeat throttle — next PostToolUse must fire to clear awaiting_input
# BUG 2026-04-03.03-34-39: without this, the 30s throttle in session-heartbeat.sh
# prevents push_status() from clearing the awaiting_input signal
_mid=$(resolve_marker_id 2>/dev/null)
if [ -n "$_mid" ]; then
  rm -f "/tmp/claude-heartbeat-last-${_mid}" 2>/dev/null
fi

# Always exit 0 — fail-open
exit 0
