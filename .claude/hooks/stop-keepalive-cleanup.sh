#!/usr/bin/env bash
# Stop hook: Session exit cleanup — kills keepalive, clears agent signal,
# removes session-init marker.
#
# Two responsibilities:
#   1. Kill keepalive background process + remove PID/heartbeat files
#   2. Clear agent signal + story linkage via API
#
# Migration: 2026-03-26.23-12-00 — API-backed, removed marker cleanup.
# Always exits 0 (fail-open, best-effort cleanup).

INPUT=$(cat)
_project_dir="${CLAUDE_PROJECT_DIR:-.}"
source "$_project_dir/.claude/hooks/lib/hub-query.sh"
AGENT_ID=$(resolve_agent_id)
if [ -z "$AGENT_ID" ]; then
  exit 0
fi

# 1. Kill ALL keepalive processes for this agent + remove PID/heartbeat files
# BUG 2026-04-01.13-16-46: single-PID kill left orphaned keepalives from prior sessions.
# pkill targets all processes matching this agent's worktree path.
pkill -f "${_project_dir}/scripts/agent-keepalive.sh" 2>/dev/null || true
rm -f "/tmp/claude-keepalive-pid-${AGENT_ID}" 2>/dev/null
rm -f "/tmp/claude-heartbeat-last-${AGENT_ID}" 2>/dev/null

# Clean up test suite tracking (lightweight /tmp files from test-emitter.sh)
rm -rf "/tmp/claude-test-suites-${AGENT_ID}" 2>/dev/null

# Clean up TDD phase tracking (from tdd-gate.sh / test-emitter.sh)
rm -f "/tmp/tdd-phase-${AGENT_ID}" 2>/dev/null
rm -f "/tmp/tdd-story-type-${AGENT_ID}" 2>/dev/null

# Clean up session-init marker (from prompt-init-gate.sh)
rm -f "/tmp/claude-session-init-${AGENT_ID}" 2>/dev/null

# Clean up execution mode sticky file
rm -f "/tmp/claude-sticky-exec-mode-${AGENT_ID}" 2>/dev/null

# Clean up orphaned signal/phase/gate files (pre-refactor carry-forward files)
rm -f "/tmp/claude-last-signal-${AGENT_ID}" 2>/dev/null
rm -f "/tmp/claude-last-phase-${AGENT_ID}" 2>/dev/null
rm -f "/tmp/claude-last-gate-${AGENT_ID}" 2>/dev/null

# Clean up tool-call inactivity tracking (from session-heartbeat.sh, used by keepalive)
rm -f "/tmp/claude-last-tool-call-${AGENT_ID}" 2>/dev/null

# Clean up session exclusivity files (from prompt-init-gate.sh)
SESSION_ID=$(resolve_session_id "$AGENT_ID")
rm -f "/tmp/claude-session-id-${AGENT_ID}" 2>/dev/null
rm -f "/tmp/claude-session-pid-${AGENT_ID}" 2>/dev/null

# 2. End agent session via API (clears all signals)
# Include session_id for identity-safe end (2026-04-02.23-17-13)
_SIGNAL_HUB_URL=$(_hub_resolve_url)
_SIGNAL_MACHINE_ID=$(resolve_machine_id)
if [ -n "$_SIGNAL_HUB_URL" ] && [ -n "$AGENT_ID" ]; then
  _end_params="machine_id=${_SIGNAL_MACHINE_ID}"
  if [ -n "$SESSION_ID" ]; then
    _end_params="${_end_params}&session_id=${SESSION_ID}"
  fi
  curl -s -X POST "${_SIGNAL_HUB_URL}/api/v1/agents/by-name/${AGENT_ID}/sessions/end?${_end_params}" \
    -H "Content-Type: application/json" >/dev/null 2>&1 || true
fi

exit 0
