---
name: ship
description: >
  Ship a story: commit, push, transition to done. Git plumbing and state
  transition only — all quality work (tests, docs, compliance, drift,
  ship-review) must be completed in /pull Step 4 before invoking /ship.
---

# /ship — Story Ship (Git Plumbing + Transition)

**Usage:** `/ship STORYID` or `/ship Story Title`

> **Argument resolution:** The argument can be a **UUID**, **STORYID** (timestamp `YYYY-MM-DD.HH-MM-SS`), or a **story title** (any other string). Pass the argument directly as a path parameter — the API resolves it server-side (UUID → timestamp → title, case-insensitive with substring fallback). Single match → resolved. Zero matches → 404. Multiple title matches → 409 `AMBIGUOUS_MATCH` with `matches` array — present candidates via AskUserQuestion. URL-encode titles containing `/`, `?`, or `#`.

> **Sources:** CLAUDE.md §Complete Story, §Git Workflow, §Policy 9
>
> **Hub API:** Source `scripts/hub-client.sh` for all API operations. Provides `hub_get()`, `hub_post()`, `hub_patch()`, `hub_transition()` with 3-retry exponential backoff. See `.claude/skills/hub-api-helpers.md` for idempotency notes. Gate stamps are emitted as side effects of `gate-review` and `test-results` endpoints.
>
> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT). Each operation below is classified per-tier.
>
> **Prerequisite:** All quality gates must have passed in `/pull` Step 4 (Quality & Ship Readiness). The `review_ship` stamp must be persisted to DB by ship-review before `/ship` can push.

---

## Step 1: Pre-Flight Checks

1. Look up story using path-based resolution:
   ```bash
   source scripts/hub-client.sh
   hub_get "/api/v1/stories/$ARGUMENT"
   ```
   **200** → story found. **404** → not found, STOP. **409** → ambiguous, parse `error.matches`, present via AskUserQuestion.
2. Extract Type (Story/BUG/Refactor/SDLC/Data), UUID, Title
3. Verify story is in `in_progress` status. If not: STOP with status report
4. Verify `review_ship` stamp exists on story (set by ship-review in `/pull` Step 4h, persisted to DB by Gate Keeper's direct call to `POST /api/v1/stories/{UUID}/gate-review`). If missing: report "Run quality phase in `/pull` first — review_ship stamp required." STOP

---

## Step 1.5: Pre-Flight Stamp Validation

> **Why:** The transition API validates that all required gate stamps exist in the DB before allowing IN_PROGRESS→DONE. If stamps were not persisted during `/pull`, the transition fails AFTER push — leaving the story stuck. This step catches the gap early.
> **Added by:** BUG 2026-03-18.21-57-39

Run the readiness check against the story UUID from Step 1:

```bash
bash scripts/check-ship-readiness.sh "$STORY_UUID"
```

- **Exit 0:** All required stamps and fields present. Proceed to Step 2.
- **Exit 1:** Missing stamps or fields listed on stderr. Report the missing items and STOP. Agent must ensure missing stamps are emitted via `gate-review` (re-run the relevant gate in `/pull`) or fill missing fields via `hub_patch` before re-running `/ship`.
- **Exit 2:** API unreachable or invalid UUID. Report and STOP.

The script checks:
- **Gate stamps:** Type-aware (code types require RED, GREEN, REVIEW_CODE in addition to the base set). Matches `DONE_TRANSITION_CODE_STAMPS` / `DONE_TRANSITION_NON_CODE_STAMPS` from `backend/src/domain/story/enums.py`
- **Required fields:** compliance_checklist, execution_log, drift_review (non-empty)

---

## Step 1.7: Task Reconciliation

> **Why:** Quality tasks that are N/A for this story type (e.g., "BUG runtime verification" on a feature story) remain `pending` in TodoWrite. The backend auto-completes all remaining tasks on DONE transition via `reconcile_tasks_before_done()`, but marking N/A tasks as `skipped` before transition is still preferred for accurate task attribution (agent-skipped vs backend-auto-completed).

1. Review the current TodoWrite task list for any `pending` quality tasks that are N/A for this story
2. Mark N/A quality tasks as `"skipped"` via TodoWrite (update their status to `"skipped"`)
3. Common N/A tasks by story type:
   - Non-BUG stories: "BUG runtime verification" is always N/A
   - Non-code stories (SDLC/Data): "Run all test suites", "Verify gate stamps" may be N/A if no code was modified
4. Do NOT skip tasks that were genuinely incomplete — only tasks that are structurally N/A for this story type

---

## Step 2: Commit

1. **Flush Gate Keeper ledger buffer** — append buffered entries to the persistent ledger:
   ```bash
   source .claude/hooks/lib/hub-query.sh
   BUFFER_FILE="/tmp/claude-gate-keeper-buffer-$(resolve_marker_id).jsonl"
   LEDGER_FILE="docs/governance/gate-keeper-ledger.jsonl"
   if [ -f "$BUFFER_FILE" ]; then
     cat "$BUFFER_FILE" >> "$LEDGER_FILE" && rm -f "$BUFFER_FILE"
   fi
   ```
   The ledger file is gitignored — do NOT stage it.
   If buffer does not exist (no Gate Keeper runs, e.g., SDLC/Data types), skip silently.
   If `cat` fails, STOP and report — do not proceed to commit.

2. **Commit** per CLAUDE.md §Git Workflow: `<type>: <description> — [title] (STORYID)` + `Co-Authored-By: Claude <noreply@anthropic.com>`. Story files are gitignored (DB is source of truth) — do NOT stage `stories/` directories
   > Note: Files may already be staged from `/pull` Step 4g2 (ship-review prep). Re-staging is idempotent — `git add` on already-staged files is a no-op.

---

## Step 3: Push

1. **Pull-rebase → Push** per CLAUDE.md §Git Workflow:
   ```bash
   git fetch origin && git rebase origin/main
   git push origin HEAD:main
   ```
2. `push-gate.sh` verifies `review_ship` stamp via hub API before allowing push

**STOP on code conflicts.** Report conflicting files to user.

---

## Step 4: Transition + Finalize

> **Transition to `done` happens AFTER push** — the story moves to done only when code is on main.

All API calls use `scripts/hub-client.sh` functions.

**Multi-step finalization — verify each step before proceeding:**

1. **Transition to done (WARN tier):**
   ```bash
   source scripts/hub-client.sh
   hub_transition "$STORY_UUID" "done"
   ```
   **If fails:** Output `⚠️ WARNING: hub_transition to done failed ([detail]) — story pushed to main but not transitioned — recovery: hub_transition "$STORY_UUID" "done"`. Continue to Step 4.2.
   **Retry:** Transition is **non-idempotent** — before retry, `hub_get "/api/v1/stories/$STORY_UUID"` to check current status. If already `done`, skip.

2. **Render story file (WARN tier):**
   ```bash
   hub_post "/api/v1/stories/$STORY_UUID/render" '{"worktree_path": "<agent worktree path>", "target_dir": "done"}'
   ```
   **If fails:** Output `⚠️ WARNING: hub_post render failed ([detail]) — story file not rendered in hub — recovery: hub_post "/api/v1/stories/$STORY_UUID/render" '{...}'`. Continue to Step 4.3.
   **Retry:** Render is **idempotent** — safe to retry directly.

3. **Update story with commit hash (WARN tier):**
   ```bash
   hub_patch "/api/v1/stories/$STORY_UUID" "{\"commit_sha\": \"<git commit hash from Step 2>\"}"
   ```
   **If fails:** Output `⚠️ WARNING: hub_patch commit_sha failed ([detail]) — commit hash not recorded — recovery: hub_patch "/api/v1/stories/$STORY_UUID" '{"commit_sha": "<hash>"}'`. Continue to Step 4.4.
   **Retry:** PATCH is **idempotent** — safe to retry directly.

4. **Emit SHIPPED stamp via gate-review (WARN tier):**
   ```bash
   hub_post "/api/v1/stories/$STORY_UUID/gate-review" '{"gate_type": "shipped", "result": "pass", "stamp_values": {"shipped": "<hash>"}}'
   ```
   The entity's `record_gate_verdict(GateType.SHIPPED)` emits the SHIPPED stamp with the commit hash as value.
   **If fails:** Output `⚠️ WARNING: gate-review shipped failed ([detail]) — SHIPPED stamp not emitted — recovery: hub_post "/api/v1/stories/$STORY_UUID/gate-review" '{"gate_type": "shipped", "result": "pass", "stamp_values": {"shipped": "<hash>"}}'.`.

**Errors:** 404/409/422 = permanent failure (exit 1, display API error message). 5xx/network = transient (exit 2, retried by hub-client.sh).

---

## Step 4.5: Session Capture (Best-Effort)

Record a structured recap of the ship phase to the story's chat history. Fail-open — capture failure MUST NOT block cleanup or `/next`.

```bash
source scripts/hub-client.sh
source .claude/hooks/lib/hub-query.sh
MARKER_ID=$(resolve_marker_id)
hub_record_chat_history "$STORY_UUID" "ship" "<recap_content>" "$MARKER_ID"
```

The `<recap_content>` is a markdown recap following the 6-section format defined in `/session-log` Step 3:
1. **Session Summary** — what the ship phase accomplished (commit, push, transition)
2. **Key Decisions** — any conflict resolution choices, rebase decisions
3. **Friction Points** — push failures, rebase conflicts, transition API errors, missing stamps caught by pre-flight
4. **Problems Encountered** — code conflicts, API state mismatches
5. **User Interactions** — conflict resolution requests, if any
6. **Outcomes** — commit hash, push status, final story state, SHIPPED stamp

Keep under 500 words. Be specific (commit SHA, file counts, actual errors). On API failure: log "Failed to record session recap (non-blocking)" and continue to Step 5.

---

## Step 5: Post-Ship Cleanup + Suggest Next Work

1. **End session** — releases the session lock so the next story start doesn't conflict (BUG 2026-04-03.23-11-40). Must run BEFORE `/tmp` cleanup because `resolve_session_id()` reads from `/tmp/claude-session-id-*`:
   ```bash
   source scripts/hub-client.sh
   source .claude/hooks/lib/hub-query.sh
   _SESSION_ID=$(resolve_session_id)
   _MACHINE_ID=$(resolve_machine_id)
   hub_post "/api/v1/agents/by-name/${EUPRAXIS_AGENT_NAME}/sessions/end?machine_id=${_MACHINE_ID}${_SESSION_ID:+&session_id=${_SESSION_ID}}" \
     '{}' >/dev/null 2>&1 || true
   ```
   Fail-open — if the API call fails, the stop hook provides defense-in-depth. The `session_id` parameter is included when available for identity-safe end; omitted gracefully when the `/tmp` file is missing.

1b. **Clear stale `/tmp` session state** — prevents heartbeat from reporting stale phase/signal from the shipped story:
   ```bash
   source .claude/hooks/lib/hub-query.sh
   _MID=$(resolve_marker_id)
   rm -f "/tmp/claude-active-story-uuid-${_MID}" \
         "/tmp/claude-last-signal-${_MID}" \
         "/tmp/claude-last-phase-${_MID}" \
         "/tmp/claude-last-gate-${_MID}" \
         "/tmp/claude-todo-progress-${_MID}" \
         "/tmp/claude-discuss-mode-${_MID}" \
         "/tmp/claude-plan-mode-entered-${_MID}" 2>/dev/null
   ```

1c. **Set explicit IDLE signal** — prevents stale detection when session has no work (BUG 2026-04-03.02-24-42):
   ```bash
   source scripts/hub-client.sh
   source .claude/hooks/lib/hub-query.sh
   _MACHINE_ID=$(resolve_machine_id)
   hub_post "/api/v1/agents/by-name/${EUPRAXIS_AGENT_NAME}/sessions/signal?machine_id=${_MACHINE_ID}" \
     '{"signal": "idle"}' >/dev/null 2>&1 || true
   ```
   This sets the session signal to IDLE so the Cockpit shows the agent as IDLE (not STALE or IDLE_SILENT) while waiting for new work. Fail-open — if the API call fails, agent proceeds normally.

2. Report: "[title] shipped (STORYID). Commit: [hash]. AC: N/N | Tests: [count] | Stamps: [count] | Governance overrides: [N]"
   Read `docs/governance/override-log.md` for override count.

3. Invoke `/next`.

---

## Failure Handling

| Failure | Action |
|---------|--------|
| Hub API unreachable | Report with URL. STOP |
| review_ship stamp missing | "Run quality phase in `/pull` first." STOP |
| Story not in_progress | Report current status. STOP |
| Git conflict on push | STOP. Report conflicting files. Use AskUserQuestion with options: "Resolve conflicts and retry push" / "Abort ship" |
| Missing API stamps (Step 1.5) | Report missing stamps. STOP. Re-run the relevant gate in `/pull` to emit stamps via `gate-review` first |
| Story state changed externally (409/422 on transition) | "Story state changed externally — re-check via API." STOP |

---

## Gate Stamps

> See CLAUDE.md §Policy 9 for the full gate stamp taxonomy (3-class: User, Agent Evidence, Gate Keeper).

During `/ship`, the agent emits `SHIPPED` (Class 2) only. All quality stamps (`SUITES-GREEN`, `DOCS`, `COMPLIANCE`, `DRIFT`, `GATE-SHIP`, `GATE-CODE`) are emitted during `/pull` Step 3 (code-review) and Step 4 (quality phase). Upstream stamps (`PLAN`, `GATE-SPEC`, `GATE-PLAN`, `APPROVED-SPEC`) are emitted by `/spec`.
