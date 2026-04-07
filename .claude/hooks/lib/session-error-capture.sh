#!/usr/bin/env bash
# Session Error Capture — L1 Operational Friction (Policy 15)
#
# Fire-and-forget POST of operational errors to the hub API.
# Sources hub-query.sh for URL/agent resolution.
#
# Usage:
#   source "$HOOK_DIR/lib/session-error-capture.sh"
#   capture_session_error "hook-deny" "critical" "story-gate.sh" "No story in_progress"
#   capture_session_error "gate-fail" "critical" "pre-commit-test-gate.sh" "Tests not run" "story-id" '{"cmd":"git commit"}'
#
# RULES:
# - MUST never block the calling hook (fire-and-forget)
# - MUST never exit non-zero (all errors swallowed)
# - MUST run in background subshell to avoid latency

# Ensure hub-query.sh is sourced (idempotent — functions already exist if sourced)
if ! type resolve_marker_id &>/dev/null; then
  _SEC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  source "$_SEC_DIR/hub-query.sh"
fi

capture_session_error() {
  # Args: error_type severity source message [story_id] [context]
  local error_type="${1:?error_type required}"
  local severity="${2:?severity required}"
  local source_name="${3:?source required}"
  local message="${4:?message required}"
  local story_id="${5:-}"
  local context="${6:-}"

  # Fire-and-forget in background subshell
  (
    local agent_name
    agent_name=$(resolve_marker_id 2>/dev/null) || true
    [ -z "$agent_name" ] && exit 0

    local hub_url
    hub_url=$(_hub_resolve_url 2>/dev/null) || true
    [ -z "$hub_url" ] && exit 0

    # Build JSON payload with printf to avoid jq dependency
    local payload
    payload=$(printf '{"error_type":"%s","severity":"%s","source":"%s","message":"%s"' \
      "$error_type" "$severity" "$source_name" "$(echo "$message" | head -c 500 | sed 's/\\/\\\\/g; s/"/\\"/g')")

    if [ -n "$story_id" ]; then
      payload="${payload},\"story_id\":\"$story_id\""
    fi
    if [ -n "$context" ]; then
      payload="${payload},\"context\":\"$(echo "$context" | head -c 1000 | sed 's/"/\\"/g')\""
    fi
    payload="${payload}}"

    curl -s -o /dev/null -m 2 \
      -X POST "${hub_url}/api/v1/agents/by-name/${agent_name}/session-errors" \
      -H "Content-Type: application/json" \
      -d "$payload" 2>/dev/null || true
  ) &
}
