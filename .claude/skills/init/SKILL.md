---
name: init
description: >
  Bootstrap or reload the agent session. Executes the mandatory 3-step sequence:
  pull-rebase, load directives, board-check. Lightweight — no markers to manage.
---

# /init -- Bootstrap and Reload

**Usage:** `/init`

> **Sources:** CLAUDE.md SS Session Initialization, SS Core Rules (Rule 0)
> **Error Handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT).

---

## Step 0.5: Validate Agent Environment

Check that all required `.env` fields are present for hook infrastructure:

```bash
ENV_OUTPUT=$(bash scripts/validate-agent-env.sh 2>&1)
ENV_EXIT=$?
if [ $ENV_EXIT -ne 0 ]; then
  echo "⚠️ WARNING: validate-agent-env.sh failed (exit $ENV_EXIT) — missing env vars may cause silent API failures downstream"
  echo "$ENV_OUTPUT"
  echo "Recovery: check .env against .env.agent.example"
fi
```

**WARN tier:** Validation failure outputs a visible warning listing missing vars. Bootstrap continues — but the user sees exactly what's missing. Non-agent worktrees (main) are detected and skipped automatically.

---

## Step 1: Pull and Rebase (Stash-Aware)

Sync with origin to ensure directive freshness. Uses `safe_rebase` for dirty-worktree safety:

```bash
source .claude/hooks/lib/safe-rebase.sh
git fetch origin
# On main branch:
safe_rebase . origin/main pull
# In a worktree (agent session):
safe_rebase . origin/main
```

If the worktree has uncommitted changes, `safe_rebase` stashes them, rebases, and restores. All failure modes let the session continue:
- **Rebase conflict:** Aborted, stash restored. Output `⚠️ WARNING: rebase conflict — running on stale code — recovery: resolve conflicts manually then git rebase origin/main` (WARN tier).
- **Pop conflict:** Rebased but stashed changes conflict. Stash preserved. Output `⚠️ WARNING: stash pop conflict — rebased successfully but local changes could not be restored — recovery: git stash show && git stash pop` (WARN tier).
- **Clean:** No stash needed, direct rebase.

---

## Step 2: Load Directives

List all rule files to confirm they are present and trigger directive loading:

```bash
ls .claude/rules/*.md
```

---

## Step 3: Board Check

Query the hub API for current board state:

```bash
bash scripts/board-check.sh
```

This queries `$EUPRAXIS_HUB_URL` (from `.env`, default `http://localhost:8000`) for story counts by status.

**If fails:** output `⚠️ WARNING: board-check.sh failed — board state unavailable, working without board context — recovery: bash scripts/board-check.sh` (WARN tier). Bootstrap continues.

---

## Step 3.5: Agent Status Sync

Announce this agent as alive to the hub API:

```bash
bash scripts/sync-agent-status.sh
```

This resolves the agent's identity via natural key (`EUPRAXIS_AGENT_NAME` + `EUPRAXIS_MACHINE_ID` from `.env`), sends a heartbeat to the hub, and recovers from STALE or OFFLINE status to IDLE.

**If fails:** output `⚠️ WARNING: sync-agent-status.sh failed — hub may not know this session exists — recovery: bash scripts/sync-agent-status.sh` (WARN tier). Bootstrap continues.

---

## Step 3.6: Session Conflict Resolution (Agent-Mediated)

> **Story:** 2026-04-03.21-43-09 — Agent-Mediated Session Conflict Resolution

**Trigger condition:** The `sync-agent-status.sh` output (injected into system-reminder by `prompt-init-gate.sh`) contains `SESSION CONFLICT`. If no conflict detected, skip this step.

**When detected:** Present AskUserQuestion with two options:

| Option | Description |
|--------|-------------|
| **Force takeover** | "Replace the existing session — this is the only active session for this agent" |
| **Abort (degraded session)** | "Continue without a session — heartbeats, signals, and cockpit visibility will not function" |

**On "Force takeover":** Execute via Bash:

```bash
source scripts/hub-client.sh
AGENT_NAME=$(resolve_marker_id)
MACHINE_ID=$(resolve_machine_id)
_hub_url=$(_hub_resolve_url)
_hub_token=$(_hub_resolve_token)
_raw=$(curl -4 -s -w "\n%{http_code}" -X POST \
  "${_hub_url}/api/v1/agents/by-name/${AGENT_NAME}/sessions/start?machine_id=${MACHINE_ID}&force=true" \
  -H "Content-Type: application/json" \
  ${_hub_token:+-H "Authorization: Bearer $_hub_token"} \
  -d '{}' 2>/dev/null)
_http_code=$(echo "$_raw" | tail -1)
_response=$(echo "$_raw" | sed '$d')
if [ "$_http_code" = "200" ] || [ "$_http_code" = "201" ]; then
  _sid=$(echo "$_response" | jq -r '.session_id // ""' 2>/dev/null)
  [ -n "$_sid" ] && [ "$_sid" != "null" ] && echo "$_sid" > "/tmp/claude-session-id-${AGENT_NAME}"
  echo "Session takeover succeeded — session_id persisted"
else
  echo "Session takeover failed (HTTP ${_http_code}) — session degraded"
fi
```

**On "Abort":** Output: `⚠️ WARNING: Session running without session_id — heartbeats, signals, and cockpit visibility will not function. Use /init to retry.`

**If force endpoint fails:** Output warning, continue with degraded session. Fail-open.

---

## Step 3.7: Generate Launch Config

Generate `.claude/launch.json` if missing (gitignored, per-worktree):

```bash
[ -f .claude/launch.json ] || bash scripts/generate-launch-json.sh
```

This creates the Claude Preview MCP config (`preview_start`) with correct ports from `.env`. Idempotent — skips if file already exists.

**If fails:** output `⚠️ WARNING: generate-launch-json.sh failed — preview tools need manual config — recovery: bash scripts/generate-launch-json.sh` (WARN tier). Bootstrap continues.

---

## Step 4: Report

After all steps complete, report:

```
Initialized. Standards: TDD, story-driven. Mode: [memory|db].
Doing: [count] | Todo: [count]
[Query API for available stories or "What should I work on?"]
```

- **Mode:** Read from `DATA_MODE` environment variable (or `.env`). Agent worktrees default to `memory`. Main uses `db`.
- **Doing/Todo counts:** From `board-check.sh` output.
- **Available stories:** Query via `GET $EUPRAXIS_HUB_URL/api/v1/queue/ready_to_pull` or present the board-check summary.

---

## Failure Handling

| Failure | Tier | Action |
|---------|------|--------|
| Rebase conflict | WARN | `⚠️ WARNING: rebase conflict — running on stale code`. Continue |
| Pop conflict | WARN | `⚠️ WARNING: stash pop conflict — changes preserved in stash`. Continue |
| Directive files missing | WARN | `⚠️ WARNING: directive files missing — [list]`. Investigate |
| Hub API unreachable | WARN | `⚠️ WARNING: hub unreachable ([URL]) — board state unavailable`. Continue |
| Origin unreachable | WARN | `⚠️ WARNING: git fetch failed — working with local state`. Continue |
| Env validation fails | WARN | `⚠️ WARNING: missing env vars — [list]`. Continue |
| Agent status sync fails | WARN | `⚠️ WARNING: agent status not synced`. Continue |
| Launch config fails | WARN | `⚠️ WARNING: launch.json not generated`. Continue |

---

## Notes

- No gate stamps emitted by this skill (bootstrap is infrastructure, not governance)
- Governance enforcement is API-backed: hooks query gate stamps on stories, not filesystem markers
- Session resume detection (in_progress stories from previous sessions) happens during board-check -- if detected, report and offer to resume
