#!/usr/bin/env bash
# Shared hub API query helper for governance hooks.
# Provides cached, authenticated queries to the story API.
#
# Usage: source this file, then call functions:
#   hub_query_stories "in_progress"   → JSON array of stories
#   hub_get_story_field "$json" "type" → field value
#   hub_has_gate_stamp "$story" "review_plan" → 0 if present, 1 if not
#   hub_get_active_story "$agent_name" → story JSON (cached)
#   _hub_resolve_project_id → EUPRAXIS_PROJECT_ID from env/.env (empty if unset)
#
# Cache: 5-second TTL per session+status. Multiple hooks on same
# tool invocation share the cached response.
#
# Fail-open: Returns empty on API errors (hooks treat empty as "no story").
#
# Migration: 2026-03-26.23-12-00 — API-Backed Hook Enforcement
# Removed: marker cleanup functions, marker provenance (nonce/create/verify).
# All governance state now in DB via gate_stamps on stories.

# ─── Project dir resolution (BUG 2026-03-18.22-03-14) ────────
# Priority: CLAUDE_PROJECT_DIR > HOOK_DIR derivation > CWD
# HOOK_DIR is set by every hook before sourcing this file.
# Project root is HOOK_DIR/../.. (hooks live at .claude/hooks/).

_hub_resolve_project_dir() {
  if [ -n "$CLAUDE_PROJECT_DIR" ]; then
    echo "$CLAUDE_PROJECT_DIR"
    return
  fi
  if [ -n "$HOOK_DIR" ]; then
    echo "$HOOK_DIR/../.."
    return
  fi
  echo "."
}

# ─── Agent ID resolution ─────────────────────────────────────

resolve_agent_id() {
  # Returns agent name for API queries and namespacing.
  # Priority: EUPRAXIS_AGENT_NAME from env → .env file → FATAL ERROR
  if [ -n "$EUPRAXIS_AGENT_NAME" ]; then
    echo "$EUPRAXIS_AGENT_NAME"
    return 0
  fi
  local project_dir
  project_dir=$(_hub_resolve_project_dir)
  if [ -f "$project_dir/.env" ]; then
    local name
    name=$(grep "^EUPRAXIS_AGENT_NAME=" "$project_dir/.env" 2>/dev/null | cut -d= -f2)
    if [ -n "$name" ]; then
      echo "$name"
      return 0
    fi
  fi
  echo >&2 "hub-query: EUPRAXIS_AGENT_NAME unresolved — agent identity unknown (check .env)"
  echo ""
  return 1
}

# Backward-compat alias (retained hooks may still call this)
resolve_marker_id() { resolve_agent_id "$@"; }

resolve_session_id() {
  # Returns session_id from /tmp file (written by prompt-init-gate.sh at session start).
  local agent_id="${1:-$(resolve_agent_id 2>/dev/null)}"
  local sid_file="/tmp/claude-session-id-${agent_id}"
  if [ -f "$sid_file" ]; then
    cat "$sid_file" 2>/dev/null
  fi
}

resolve_machine_id() {
  # Returns machine identifier for API queries (natural key component).
  # Priority: EUPRAXIS_MACHINE_ID from env → .env file → "local" (safe default)
  if [ -n "$EUPRAXIS_MACHINE_ID" ]; then
    echo "$EUPRAXIS_MACHINE_ID"
    return 0
  fi
  local project_dir
  project_dir=$(_hub_resolve_project_dir)
  if [ -f "$project_dir/.env" ]; then
    local mid
    mid=$(grep "^EUPRAXIS_MACHINE_ID=" "$project_dir/.env" 2>/dev/null | cut -d= -f2)
    if [ -n "$mid" ]; then
      echo "$mid"
      return 0
    fi
  fi
  echo "local"
  return 0
}

resolve_env_or_die() {
  # Resolves AGENT_ID or emits a fatal deny response and exits.
  # Call this in PreToolUse gate hooks that must deny on missing config.
  AGENT_ID=$(resolve_agent_id)
  if [ -z "$AGENT_ID" ]; then
    cat <<'FATAL'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "FATAL: EUPRAXIS_AGENT_NAME not set. Add EUPRAXIS_AGENT_NAME=<name> to .env or export it in your shell. Governance hooks cannot function without agent identity."
  }
}
FATAL
    exit 0
  fi
  # Backward-compat alias
  MARKER_ID="$AGENT_ID"
  # Resolve machine_id alongside agent_id (Story 2026-04-02.21-54-47)
  MACHINE_ID=$(resolve_machine_id)
}

# ─── Auth resolution ─────────────────────────────────────────

_hub_resolve_url() {
  if [ -n "$EUPRAXIS_HUB_URL" ]; then
    echo "$EUPRAXIS_HUB_URL"
    return
  fi
  local project_dir
  project_dir=$(_hub_resolve_project_dir)
  if [ -f "$project_dir/.env" ]; then
    local url
    url=$(grep "^EUPRAXIS_HUB_URL=" "$project_dir/.env" 2>/dev/null | cut -d= -f2)
    if [ -n "$url" ]; then
      echo "$url"
      return
    fi
  fi
  echo >&2 "hub-query: EUPRAXIS_HUB_URL resolved from fallback (localhost:8000) — may be hitting wrong server"
  echo "http://localhost:8000"
}

_hub_resolve_token() {
  if [ -n "$EUPRAXIS_HUB_TOKEN" ]; then
    echo "$EUPRAXIS_HUB_TOKEN"
    return
  fi
  local project_dir
  project_dir=$(_hub_resolve_project_dir)
  if [ -f "$project_dir/.env" ]; then
    local token
    token=$(grep "^EUPRAXIS_HUB_TOKEN=" "$project_dir/.env" 2>/dev/null | cut -d= -f2)
    if [ -n "$token" ]; then
      echo "$token"
      return
    fi
    token=$(grep "^VITE_API_TOKEN=" "$project_dir/.env" 2>/dev/null | cut -d= -f2)
    if [ -n "$token" ]; then
      echo "$token"
      return
    fi
  fi
  echo ""
}

_hub_resolve_project_id() {
  if [ -n "$EUPRAXIS_PROJECT_ID" ]; then
    echo "$EUPRAXIS_PROJECT_ID"
    return
  fi
  local project_dir
  project_dir=$(_hub_resolve_project_dir)
  if [ -f "$project_dir/.env" ]; then
    local pid
    pid=$(grep "^EUPRAXIS_PROJECT_ID=" "$project_dir/.env" 2>/dev/null | cut -d= -f2)
    if [ -n "$pid" ]; then
      echo "$pid"
      return
    fi
  fi
  echo ""
}

# ─── Authenticated curl helper ────────────────────────────────

_hub_curl() {
  # Authenticated curl to hub API. Args: method, path, [data]
  local method="$1" path="$2" data="${3:-}"
  local hub_url token
  hub_url=$(_hub_resolve_url)
  token=$(_hub_resolve_token)
  local auth_header=""
  [ -n "$token" ] && auth_header="-H \"Authorization: Bearer $token\""

  if [ -n "$data" ]; then
    eval curl -4 -sf --connect-timeout 3 --max-time 5 \
      -X "$method" \
      -H "Content-Type: application/json" \
      $auth_header \
      -d "'$data'" \
      "'${hub_url}${path}'" 2>/dev/null
  else
    eval curl -4 -sf --connect-timeout 3 --max-time 5 \
      $auth_header \
      "'${hub_url}${path}'" 2>/dev/null
  fi
}

# ─── Cached query ─────────────────────────────────────────────

hub_query_stories() {
  # Args: story_status (e.g. "in_progress", "done"), [agent_name] (optional)
  # Returns: JSON response body (or empty string on failure)
  local story_status="$1"
  local agent_name="${2:-}"
  local sid="${HUB_SESSION_ID:-$(resolve_agent_id 2>/dev/null)}"
  [ -z "$sid" ] && sid="unknown"

  # Check cache (5-second TTL) — include agent_name and project_id in key to avoid stale hits
  local project_id
  project_id=$(_hub_resolve_project_id)
  local cache_suffix="${sid}-${story_status}"
  [ -n "$agent_name" ] && cache_suffix="${cache_suffix}-${agent_name}"
  [ -n "$project_id" ] && cache_suffix="${cache_suffix}-${project_id}"
  local cache_file="/tmp/claude-hub-cache-${cache_suffix}"
  if [ -f "$cache_file" ]; then
    local now cache_mtime age
    now=$(date +%s)
    # macOS stat
    cache_mtime=$(stat -f %m "$cache_file" 2>/dev/null)
    if [ -z "$cache_mtime" ]; then
      # Linux stat
      cache_mtime=$(stat -c %Y "$cache_file" 2>/dev/null || echo 0)
    fi
    age=$((now - cache_mtime))
    if [ "$age" -lt 5 ]; then
      cat "$cache_file"
      return 0
    fi
  fi

  # Query API
  local hub_url token response query_url
  hub_url=$(_hub_resolve_url)
  token=$(_hub_resolve_token)
  query_url="${hub_url}/api/v1/stories?status=${story_status}"
  [ -n "$agent_name" ] && query_url="${query_url}&agent_name=${agent_name}"
  [ -n "$project_id" ] && query_url="${query_url}&project_id=${project_id}"

  if [ -n "$token" ]; then
    response=$(curl -4 -sf --connect-timeout 3 --max-time 5 \
      -H "Authorization: Bearer $token" \
      "$query_url" 2>/dev/null)
  else
    response=$(curl -4 -sf --connect-timeout 3 --max-time 5 \
      "$query_url" 2>/dev/null)
  fi

  if [ $? -ne 0 ] || [ -z "$response" ]; then
    echo ""
    return 1
  fi

  # Cache response
  printf '%s' "$response" > "$cache_file" 2>/dev/null
  printf '%s' "$response"
  return 0
}

# ─── Field extraction ─────────────────────────────────────────

hub_get_first_story() {
  local response="$1"
  if [ -z "$response" ]; then
    echo ""
    return 1
  fi
  printf '%s' "$response" | jq -r '.data[0] // empty' 2>/dev/null
}

hub_get_story_field() {
  local story="$1"
  local field="$2"
  if [ -z "$story" ]; then
    echo ""
    return 1
  fi
  printf '%s' "$story" | jq -r ".${field} // empty" 2>/dev/null
}

hub_story_count() {
  local response="$1"
  if [ -z "$response" ]; then
    echo "0"
    return
  fi
  printf '%s' "$response" | jq -r '.data | length' 2>/dev/null || echo "0"
}

hub_get_story_type() {
  local agent_name="${1:-}"
  local response story stype
  response=$(hub_query_stories "in_progress" "$agent_name")
  story=$(hub_get_first_story "$response")
  stype=$(hub_get_story_field "$story" "type")
  if [ -z "$stype" ]; then
    response=$(hub_query_stories "done" "$agent_name")
    story=$(hub_get_first_story "$response")
    stype=$(hub_get_story_field "$story" "type")
  fi
  echo "$stype"
}

hub_has_story_of_type() {
  local response count i story stype stitle
  response=$(hub_query_stories "in_progress")
  count=$(hub_story_count "$response")
  [ "$count" -eq 0 ] && return 1
  for i in $(seq 0 $((count - 1))); do
    story=$(printf '%s' "$response" | jq -r ".data[$i]" 2>/dev/null)
    stype=$(printf '%s' "$story" | jq -r '.type // empty' 2>/dev/null)
    for target_type in "$@"; do
      if [ "$stype" = "$target_type" ]; then
        stitle=$(printf '%s' "$story" | jq -r '.title // "unknown"' 2>/dev/null)
        echo "$stitle"
        return 0
      fi
    done
  done
  return 1
}

hub_has_compliance_checked() {
  local story="$1"
  if [ -z "$story" ]; then
    echo "false"
    return
  fi
  local count
  count=$(printf '%s' "$story" | jq '[.compliance[] | select(.checked == true)] | length' 2>/dev/null || echo "0")
  if [ "$count" -gt 0 ]; then
    echo "true"
  else
    echo "false"
  fi
}

# ─── Gate stamp queries (2026-03-26.23-12-00) ─────────────────

hub_get_active_story() {
  # Returns the agent's in_progress story JSON (cached via hub_query_stories).
  # Args: agent_name (required)
  # Returns: story JSON object or empty string
  local agent_name="$1"
  if [ -z "$agent_name" ]; then
    echo ""
    return 1
  fi
  local response
  response=$(hub_query_stories "in_progress" "$agent_name")
  hub_get_first_story "$response"
}

hub_has_gate_stamp() {
  # Check if a story has a specific gate stamp type.
  # Args: story_json (required), stamp_type (required, e.g. "review_plan")
  # Returns: 0 if stamp exists, 1 if not
  local story="$1"
  local stamp_type="$2"
  if [ -z "$story" ] || [ -z "$stamp_type" ]; then
    return 1
  fi
  local found
  found=$(printf '%s' "$story" | jq -r \
    --arg t "$stamp_type" \
    '[.gate_stamps[] | select(.token_type == $t)] | length' 2>/dev/null)
  [ "$found" -gt 0 ] 2>/dev/null && return 0
  return 1
}

hub_get_stamp_emitted_at() {
  # Get emitted_at timestamp (unix epoch) for a specific gate stamp.
  # Args: story_json (required), stamp_type (required)
  # Returns: unix epoch seconds or empty string
  local story="$1"
  local stamp_type="$2"
  if [ -z "$story" ] || [ -z "$stamp_type" ]; then
    echo ""
    return 1
  fi
  local emitted_at
  emitted_at=$(printf '%s' "$story" | jq -r \
    --arg t "$stamp_type" \
    '[.gate_stamps[] | select(.token_type == $t)] | last | .emitted_at // empty' 2>/dev/null)
  if [ -z "$emitted_at" ]; then
    echo ""
    return 1
  fi
  # Convert ISO 8601 to epoch
  date -j -f "%Y-%m-%dT%H:%M:%S" "${emitted_at%%.*}" "+%s" 2>/dev/null || \
    date -d "$emitted_at" "+%s" 2>/dev/null || \
    echo ""
}

hub_emit_gate_stamp() {
  # POST a gate stamp to a story via API. Fire-and-forget.
  # Args: story_uuid (required), token_type (required, display format e.g. "GATE-CODE"), value (required)
  # Returns: 0 on success, 1 on failure
  local story_uuid="$1"
  local token_type="$2"
  local value="$3"
  if [ -z "$story_uuid" ] || [ -z "$token_type" ]; then
    return 1
  fi
  local hub_url token
  hub_url=$(_hub_resolve_url)
  token=$(_hub_resolve_token)
  local auth=""
  [ -n "$token" ] && auth="-H \"Authorization: Bearer $token\""
  eval curl -4 -sf --connect-timeout 3 --max-time 5 \
    -X POST \
    -H "Content-Type: application/json" \
    $auth \
    -d "'{\"token_type\": \"$token_type\", \"value\": \"$value\"}'" \
    "'${hub_url}/api/v1/stories/${story_uuid}/gate-stamps'" >/dev/null 2>&1
}

hub_record_test_results() {
  # POST test results to a story via API. Entity emits SUITES-GREEN when all 3 suites pass.
  # Args: story_uuid (required), suites_csv (required, e.g. "backend,api,frontend"), origin_sha (required)
  # Returns: 0 on success, 1 on failure
  local story_uuid="$1"
  local suites_csv="$2"
  local origin_sha="$3"
  if [ -z "$story_uuid" ] || [ -z "$suites_csv" ]; then
    return 1
  fi
  # Convert CSV to JSON array
  local suites_json
  suites_json=$(echo "$suites_csv" | tr ',' '\n' | jq -R . | jq -s .)
  local hub_url token
  hub_url=$(_hub_resolve_url)
  token=$(_hub_resolve_token)
  local auth=""
  [ -n "$token" ] && auth="-H \"Authorization: Bearer $token\""
  eval curl -4 -sf --connect-timeout 3 --max-time 5 \
    -X POST \
    -H "Content-Type: application/json" \
    $auth \
    -d "'$(jq -n --argjson suites "$suites_json" --arg sha "$origin_sha" '{suites_passed: $suites, origin_sha: $sha}')'" \
    "'${hub_url}/api/v1/stories/${story_uuid}/test-results'" >/dev/null 2>&1
}

# hub_emit_signal, hub_has_signal, hub_has_evidence — REMOVED (Signal-Then-Mint removed)
# Use hub_has_gate_stamp() for evidence checks. POST /signals returns 410.

hub_post_gate_verdict() {
  # POST a gate verdict to a story via API. Fire-and-forget.
  # Args: story_uuid (required), gate_type (required), result (required: "pass"/"fail")
  local story_uuid="$1"
  local gate_type="$2"
  local result="$3"
  if [ -z "$story_uuid" ] || [ -z "$gate_type" ]; then
    return 1
  fi
  local hub_url token
  hub_url=$(_hub_resolve_url)
  token=$(_hub_resolve_token)
  local auth=""
  [ -n "$token" ] && auth="-H \"Authorization: Bearer $token\""
  eval curl -4 -sf --connect-timeout 3 --max-time 5 \
    -X POST \
    -H "Content-Type: application/json" \
    $auth \
    -d "'{\"gate_type\": \"$gate_type\", \"result\": \"$result\"}'" \
    "'${hub_url}/api/v1/stories/${story_uuid}/gate-verdicts'" >/dev/null 2>&1
}

# ─── Gate Engine API (2026-03-27.12-04-53) ────────────────────

hub_check_gate() {
  # Query Gate Engine API for a gate decision.
  # Args: story_uuid (required), gate_name (required), query_params (optional)
  # Returns: JSON response body on success, empty string on failure
  # Exit codes: 0=success, 1=general failure, 2=gate engine disabled (503)
  local story_uuid="$1"
  local gate_name="$2"
  local query_params="${3:-}"
  if [ -z "$story_uuid" ] || [ -z "$gate_name" ]; then
    echo ""
    return 1
  fi
  local hub_url token
  hub_url=$(_hub_resolve_url)
  token=$(_hub_resolve_token)
  local auth_args=""
  [ -n "$token" ] && auth_args="-H \"Authorization: Bearer $token\""
  local url="${hub_url}/api/v1/stories/${story_uuid}/gates/${gate_name}"
  [ -n "$query_params" ] && url="${url}?${query_params}"
  local tmp_file="/tmp/claude-gate-response-$$"
  local http_code
  http_code=$(eval curl -4 -s --connect-timeout 3 --max-time 5 \
    -w "'%{http_code}'" \
    -o "'$tmp_file'" \
    $auth_args \
    "'$url'" 2>/dev/null) || {
    rm -f "$tmp_file"
    echo ""
    return 1
  }
  # Strip quotes from http_code if present
  http_code="${http_code//\'/}"
  case "$http_code" in
    200)
      cat "$tmp_file" 2>/dev/null
      rm -f "$tmp_file"
      return 0
      ;;
    503)
      rm -f "$tmp_file"
      echo ""
      return 2
      ;;
    *)
      rm -f "$tmp_file"
      echo ""
      return 1
      ;;
  esac
}
