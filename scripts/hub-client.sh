#!/usr/bin/env bash
# Unified hub API client library for EuPraxis SDLC operations.
#
# Provides hub_get(), hub_post(), hub_patch() with:
#   - URL/token resolution via hub-query.sh (_hub_resolve_url, _hub_resolve_token)
#   - 3-retry exponential backoff (1s, 2s, 4s) on transient failures (5xx, network)
#   - Permanent failure on 4xx (no retry)
#   - Structured exit codes: 0=success, 1=permanent failure, 2=transient exhausted
#   - Response body on stdout, error details on stderr
#
# Usage:
#   source scripts/hub-client.sh
#   hub_post "/api/v1/stories" '{"title": "My Story", ...}'
#   hub_get "/api/v1/stories?status=ready_to_pull"
#   hub_patch "/api/v1/stories/$UUID" '{"execution_plan": "..."}'
#
# Convenience wrappers:
#   hub_transition "$UUID" "$target_status"
#   hub_claim "$STORY_UUID" "$AGENT_NAME"
#   hub_record_test_results "$UUID" "$suites_json" "$origin_sha"
#   hub_create_story "$json_body"
#   hub_jq "$jq_filter" command [args...]  — exit-code-aware jq piping
#   hub_emit_stamp — DEPRECATED (POST /gate-stamps returns 410 Gone)
#   hub_approve_spec — DEPRECATED (POST /approve-spec returns 410 Gone)
#
# NOTE: This library is for agent-initiated operations (skills, scripts).
# Hooks continue using hub-query.sh directly (fail-open, cached, no retry).

# ─── Source hub-query.sh for URL/token resolution ────────────────
# Cross-directory source — same pattern as emit-gate-stamp.sh
_HUB_CLIENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
_HUB_CLIENT_PROJECT_DIR="$(cd "$_HUB_CLIENT_DIR/.." && pwd)"

# Ensure env vars exist before sourcing (nounset-safe)
: "${EUPRAXIS_HUB_URL:=}"
: "${EUPRAXIS_HUB_TOKEN:=}"
: "${CLAUDE_PROJECT_DIR:=$_HUB_CLIENT_PROJECT_DIR}"

if [ -f "$_HUB_CLIENT_PROJECT_DIR/.claude/hooks/lib/hub-query.sh" ]; then
  source "$_HUB_CLIENT_PROJECT_DIR/.claude/hooks/lib/hub-query.sh"
else
  # Fallback: inline defaults if hub-query.sh not found
  _hub_resolve_url() { echo "${EUPRAXIS_HUB_URL:-http://localhost:8000}"; }
  _hub_resolve_token() { echo "${EUPRAXIS_HUB_TOKEN:-}"; }
fi

# ─── Core: HTTP request with retry ──────────────────────────────

# Internal: execute a single curl request, classify response.
# Args: method endpoint [body]
# Returns: exit 0 (2xx), exit 1 (4xx), exit 2 (5xx/network)
# Stdout: response body (on success)
# Stderr: error details (on failure)
_hub_request() {
  local method="$1"
  local endpoint="$2"
  local body="${3:-}"

  local hub_url token
  hub_url=$(_hub_resolve_url)
  token=$(_hub_resolve_token)

  local url="${hub_url}${endpoint}"
  local -a curl_args=(
    -4 -s -w "\n%{http_code}"
    --connect-timeout 3 --max-time 10
    -X "$method"
    -H "Content-Type: application/json"
  )

  if [ -n "$token" ]; then
    curl_args+=(-H "Authorization: Bearer $token")
  fi

  # Send agent identity header for project_id auto-resolution (BUG 2026-04-06.15-04-53)
  local agent_name="${EUPRAXIS_AGENT_NAME:-}"
  if [ -z "$agent_name" ]; then
    local project_dir
    project_dir=$(_hub_resolve_project_dir 2>/dev/null) || true
    if [ -n "$project_dir" ] && [ -f "$project_dir/.env" ]; then
      agent_name=$(grep "^EUPRAXIS_AGENT_NAME=" "$project_dir/.env" 2>/dev/null | cut -d= -f2)
    fi
  fi
  if [ -n "$agent_name" ]; then
    curl_args+=(-H "X-Agent-Name: $agent_name")
  fi

  if [ -n "$body" ]; then
    curl_args+=(-d "$body")
  fi

  local raw_response http_code response_body
  raw_response=$(curl "${curl_args[@]}" "$url" 2>/dev/null) || {
    echo "hub-client: network error — $method $endpoint" >&2
    return 2
  }

  http_code=$(printf '%s' "$raw_response" | tail -1)
  response_body=$(printf '%s' "$raw_response" | sed '$d')

  if [ "$http_code" -ge 200 ] 2>/dev/null && [ "$http_code" -lt 300 ] 2>/dev/null; then
    printf '%s' "$response_body"
    return 0
  elif [ "$http_code" -ge 400 ] 2>/dev/null && [ "$http_code" -lt 500 ] 2>/dev/null; then
    echo "hub-client: HTTP $http_code — $method $endpoint" >&2
    # Extract error message from API response if JSON
    local err_msg
    err_msg=$(printf '%s' "$response_body" | jq -r '.error.message // .detail // empty' 2>/dev/null)
    if [ -n "$err_msg" ]; then
      echo "hub-client: $err_msg" >&2
    fi
    return 1
  else
    # 5xx or unparseable status — transient
    echo "hub-client: HTTP $http_code (transient) — $method $endpoint" >&2
    return 2
  fi
}

# Internal: execute request with 3-retry exponential backoff on transient failure.
# Args: method endpoint [body]
# Exit codes: 0=success, 1=permanent failure, 2=transient exhausted
_hub_request_with_retry() {
  local method="$1"
  local endpoint="$2"
  local body="${3:-}"
  local delays=(1 2 4)

  # First attempt
  _hub_request "$method" "$endpoint" "$body"
  local rc=$?
  [ "$rc" -ne 2 ] && return "$rc"

  # Retry on transient failure
  for i in "${!delays[@]}"; do
    local attempt=$((i + 1))
    echo "hub-client: retry $((attempt))/3 — waiting ${delays[$i]}s — $method $endpoint" >&2
    sleep "${delays[$i]}"
    _hub_request "$method" "$endpoint" "$body"
    rc=$?
    [ "$rc" -ne 2 ] && return "$rc"
  done

  echo "hub-client: all retries exhausted — $method $endpoint" >&2
  return 2
}

# ─── Public API ──────────────────────────────────────────────────

# GET request (no retry — agent-initiated, not cached like hub_query_stories)
# Args: endpoint (including query params, e.g. "/api/v1/stories?status=ready_to_pull")
# Exit codes: 0=success, 1=permanent, 2=transient exhausted
hub_get() {
  _hub_request_with_retry "GET" "$1"
}

# POST request with retry
# Args: endpoint body
hub_post() {
  _hub_request_with_retry "POST" "$1" "$2"
}

# PATCH request with retry
# Args: endpoint [body]
hub_patch() {
  _hub_request_with_retry "PATCH" "$1" "${2:-}"
}

# ─── Convenience Wrappers ───────────────────────────────────────

# Transition a story to a target status
# Args: story_uuid target_status
hub_transition() {
  local uuid="$1"
  local target="$2"
  hub_post "/api/v1/stories/${uuid}/transition" "{\"target_status\": \"$target\"}"
}

# Claim a story for an agent (by name)
# Args: story_uuid agent_name
hub_claim() {
  local uuid="$1"
  local name="$2"
  [ -z "$name" ] && echo "hub-client: hub_claim requires agent_name" >&2 && return 1
  local machine_id=$(resolve_machine_id)
  hub_post "/api/v1/stories/${uuid}/claim" "{\"agent_name\": \"$name\", \"machine_id\": \"$machine_id\"}"
}

# Atomically claim and transition a story to in_progress (Story 2026-03-25.02-38-43)
# Args: story_uuid agent_name
hub_claim_and_transition() {
  local uuid="$1"
  local name="$2"
  [ -z "$name" ] && echo "hub-client: hub_claim_and_transition requires agent_name" >&2 && return 1
  local machine_id=$(resolve_machine_id)
  hub_post "/api/v1/stories/${uuid}/claim-and-transition" "{\"agent_name\": \"$name\", \"machine_id\": \"$machine_id\", \"target_status\": \"in_progress\"}"
}

# Push status for an agent (by name)
# Args: agent_name payload_json
hub_push_status() {
  local name="$1"
  local payload="$2"
  local machine_id=$(resolve_machine_id)
  hub_post "/api/v1/agents/by-name/${name}/status?machine_id=${machine_id}" "$payload"
}

# Poll interventions for an agent (by name)
# Args: agent_name
hub_poll_interventions() {
  local name="$1"
  local machine_id=$(resolve_machine_id)
  hub_get "/api/v1/agents/by-name/${name}/interventions?machine_id=${machine_id}"
}

# Assign agent to a story during upstream work (SPECIFYING/SPEC_COMPLETE)
# Args: story_uuid agent_name
hub_assign_upstream() {
  local uuid="$1"
  local name="${2:-${EUPRAXIS_AGENT_NAME:-}}"
  [ -z "$name" ] && echo "hub-client: hub_assign_upstream requires agent_name" >&2 && return 1
  local machine_id=$(resolve_machine_id)
  hub_post "/api/v1/stories/${uuid}/assign-upstream" "{\"agent_name\": \"$name\", \"machine_id\": \"$machine_id\"}"
}

# DEPRECATED: hub_emit_stamp — POST /api/v1/stories/{id}/gate-stamps returns 410 Gone.
# All stamp emission now goes through:
#   - POST /api/v1/stories/{id}/gate-review (Gate Keeper stamps)
#   - POST /api/v1/stories/{id}/test-results (SUITES-GREEN stamp)
#
# This function is preserved for backward compatibility but will fail with 410.
# Callers should migrate to hub_record_test_results() or direct gate-review calls.
hub_emit_stamp() {
  local uuid="$1"
  local token_type="$2"
  local value="$3"
  local emitted_at="${4:-}"
  echo "hub-client: WARNING — hub_emit_stamp is deprecated. POST /gate-stamps returns 410 Gone." >&2
  echo "hub-client: Use POST /gate-review or POST /test-results instead." >&2
  local payload
  if [ -n "$emitted_at" ]; then
    payload="{\"token_type\": \"$token_type\", \"value\": $(printf '%s' "$value" | jq -Rs .), \"emitted_at\": \"$emitted_at\"}"
  else
    payload="{\"token_type\": \"$token_type\", \"value\": $(printf '%s' "$value" | jq -Rs .)}"
  fi
  hub_post "/api/v1/stories/${uuid}/gate-stamps" "$payload"
}

# Record test results — entity internally emits SUITES-GREEN stamp.
# Replaces direct hub_emit_stamp for SUITES-GREEN.
# Args: story_uuid suites_json origin_sha
#   suites_json: JSON array of passed suite names, e.g. '["backend","api","frontend"]'
#   origin_sha: origin/main SHA for audit trail
hub_record_test_results() {
  local uuid="$1"
  local suites_json="$2"
  local origin_sha="$3"
  local payload
  payload="{\"suites_passed\": $suites_json, \"origin_sha\": \"$origin_sha\"}"
  hub_post "/api/v1/stories/${uuid}/test-results" "$payload"
}

# PATCH execution_log with properly formatted bullet entries (SILENT_FAIL S1)
# Args: story_uuid entry1 [entry2 entry3 ...]
# Formats entries as markdown bullets: "- entry1\n- entry2\n- entry3"
hub_patch_execution_log() {
  local uuid="$1"
  shift
  local formatted=""
  for entry in "$@"; do
    [ -n "$formatted" ] && formatted="${formatted}\n"
    formatted="${formatted}- ${entry}"
  done
  local payload
  payload="{\"execution_log\": $(printf '%s' "$formatted" | jq -Rs .)}"
  hub_patch "/api/v1/stories/${uuid}" "$payload"
}

# DEPRECATED: hub_approve_spec — POST /api/v1/stories/{id}/approve-spec returns 410 Gone.
# Use POST /api/v1/stories/{id}/gate-review with gate_type=approval instead.
hub_approve_spec() {
  local uuid="$1"
  local summary="$2"
  echo "hub-client: WARNING — hub_approve_spec is deprecated. POST /approve-spec returns 410 Gone." >&2
  echo "hub-client: Use POST /gate-review with gate_type=approval instead." >&2
  local payload
  payload="{\"gate_type\": \"approval\", \"result\": \"pass\", \"stamp_values\": {\"approved_spec\": $(printf '%s' "$summary" | jq -Rs .)}}"
  hub_post "/api/v1/stories/${uuid}/gate-review" "$payload"
}

# Emit a signal (Signal-Then-Mint dual-write companion to hub_emit_stamp)
# Args: story_uuid signal_type value
hub_emit_signal() {
  local uuid="$1"
  local signal_type="$2"
  local value="$3"
  local payload
  payload="{\"signal_type\": \"$signal_type\", \"value\": $(printf '%s' "$value" | jq -Rs .)}"
  hub_post "/api/v1/stories/${uuid}/signals" "$payload"
}

# Record a chat history entry for a story
# Args: story_uuid phase content session_id
hub_record_chat_history() {
  local uuid="$1"
  local phase="$2"
  local content="$3"
  local session_id="$4"
  local payload
  payload=$(jq -n --arg p "$phase" --arg c "$content" --arg s "$session_id" \
    '{phase: $p, content: $c, session_id: $s}')
  hub_post "/api/v1/stories/${uuid}/chat-history" "$payload"
}

# Create a new story with dedup-aware retry.
# POST /api/v1/stories is non-idempotent — blind retries create duplicates.
# On transient failure (exit 2), checks for an existing story with the same
# title in recent stories before retrying.
# Args: json_body (full story creation payload)
hub_create_story() {
  local body="$1"
  local title
  title=$(printf '%s' "$body" | jq -r '.title // empty')
  local delays=(1 2 4)

  # Dedup helper: check if a story with matching title was recently created
  # Uses server-side ?title= filter to avoid pagination limits (was ?per_page=20 + client-side jq)
  _hub_create_dedup_check() {
    [ -z "$title" ] && return 1
    local encoded_title
    encoded_title=$(printf '%s' "$title" | jq -sRr @uri)
    local recent
    recent=$(_hub_request "GET" "/api/v1/stories?title=${encoded_title}" 2>/dev/null) || return 1
    [ -z "$recent" ] && return 1
    local match
    match=$(printf '%s' "$recent" | jq --arg t "$title" \
      '[.data[] | select(.title == $t)] | if length > 0 then .[0] else empty end' 2>/dev/null)
    if [ -n "$match" ] && [ "$match" != "null" ]; then
      echo "hub-client: dedup — found existing story '$title', skipping create" >&2
      printf '{"data":%s}' "$match"
      return 0
    fi
    return 1
  }

  # First attempt
  _hub_request "POST" "/api/v1/stories" "$body"
  local rc=$?
  [ "$rc" -ne 2 ] && return "$rc"

  # Transient failure — check for dedup before each retry
  for i in "${!delays[@]}"; do
    local attempt=$((i + 1))

    # Check if the story was actually created despite the transient error
    _hub_create_dedup_check && return 0

    echo "hub-client: retry $((attempt))/3 — waiting ${delays[$i]}s — POST /api/v1/stories" >&2
    sleep "${delays[$i]}"
    _hub_request "POST" "/api/v1/stories" "$body"
    rc=$?
    [ "$rc" -ne 2 ] && return "$rc"
  done

  # Final dedup check after all retries exhausted
  _hub_create_dedup_check && return 0

  echo "hub-client: all retries exhausted — POST /api/v1/stories" >&2
  return 2
}

# Pipe a hub API call result through jq (only on success; propagates exit code on failure).
# Avoids the common mistake of `hub_post ... 2>&1 | jq` which breaks on non-JSON error output.
# Args: jq_filter command [args...]
# Usage: hub_jq '.data.status' hub_post "/api/..." '{...}'
hub_jq() {
  local jq_filter="${1:-.}"
  shift
  local result
  result=$("$@") || return $?
  printf '%s' "$result" | jq -r "$jq_filter"
}
