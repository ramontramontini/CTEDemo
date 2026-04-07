---
name: batch
description: >
  Execute an epic's stories in batch mode. Stories may be in ready_to_pull (upstream complete)
  or specifying (skeleton — upstream runs inline). All quality gates structurally enforced.
  See CLAUDE.md §Policy 19.
---

# /batch — Epic Batch Execution Mode

**Usage:**
- `/batch EPICNAME` — execute all stories in the epic
- `/batch EPICNAME STORYID-STORYID` or `/batch EPICNAME Title-Title` — execute a subset (partial batch)
- `/batch EPICNAME --resume STORYID` or `/batch EPICNAME --resume Story Title` — resume after a failure fix

> **Argument resolution:** EPICNAME is resolved via path-based lookup: `GET /api/v1/epics/$EPICNAME` — the API resolves by UUID or name server-side. **200** → epic found. **404** → not found. Story arguments (subset range, resume target) can be a **UUID**, **STORYID** (timestamp `YYYY-MM-DD.HH-MM-SS`), or a **story title** (any other string). Pass story arguments as path parameters: `GET /api/v1/stories/$ARGUMENT` — the API resolves server-side (UUID → timestamp → title, case-insensitive with substring fallback). **409** → ambiguous title match with `matches` array — present candidates via AskUserQuestion. URL-encode titles containing `/`, `?`, or `#`.

> **Hub API:** Source `scripts/hub-client.sh` for all API operations. Provides `hub_get()`, `hub_post()`, `hub_patch()`, `hub_claim()`, `hub_transition()` with 3-retry exponential backoff. See `.claude/skills/hub-api-helpers.md` for idempotency notes. Gate stamps are emitted as side effects of `gate-review` and `test-results` endpoints.
>
> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT). Each operation below is classified per-tier.

---

## Pre-Execution Validation

### 1. Resolve Epic via API

```bash
source scripts/hub-client.sh
hub_get "/api/v1/epics/$EPICNAME"
```

- **200** → epic found. Extract UUID (`data.id`).
- **404** → no epic found matching EPICNAME. Report not found. STOP.

### 2. Get Stories for Epic

```bash
hub_get "/api/v1/stories?epic_id=$EPIC_UUID"
```

Verify each story's status. Allowed statuses for batch:
- **`ready_to_pull`** — upstream complete, ready for downstream execution
- **`specifying`** — skeleton story (auto-created by epic ceremony with mandatory fields: title, type, goal, epic_id, dependencies). Will run `/spec` upstream ceremony inline before downstream

**Reject batch (STOP tier)** if any story is in `spec_complete`, `claimed`, `in_progress`, `done`, or `canceled` status. Output: `❌ STOP: Story [STORYID] "[title]" is in unexpected status [status] — batch cannot proceed. Expected: ready_to_pull or specifying. Fix the story's status before re-running /batch.`

### 3. Dependency Validation + Ordering

Build DAG from story dependencies. Reject if cycles detected. Compute topological execution order (FIFO tiebreaker).

Output plan:
```
Batch Execution — EPICNAME
Stories: [count] | All specs validated | No cycles detected
Execution Order:
1. STORYID — Title (no deps)
2. STORYID — Title (← STORYID)
```

### 4. Execution Mode Signal

Before entering the per-story loop, signal batch mode to the hook layer:

```bash
source .claude/hooks/lib/hub-query.sh
echo "batch" > "/tmp/claude-sticky-exec-mode-$(resolve_marker_id)"
```

This enables `session-heartbeat.sh` to push `execution_mode: "batch"` and `todo-capture.sh` to enforce TodoWrite scoping structurally.

---

## Per-Story Execution

> Execute per CLAUDE.md §Lifecycle Downstream + §Complete Story. Structural hooks enforce gates.
> Execution plan is written during upstream (`/spec`) — batch prerequisite requires upstream complete. `plan-review-gate.sh` marker is set by combined upstream review.

> **TodoWrite Scoping (MANDATORY):** TodoWrite MUST only contain the **current story's ACs** — managed by `/pull`, which creates per-story task lists. The batch queue, execution order, and overall epic progress MUST NOT be tracked via TodoWrite. Track batch position through console output only (e.g., `📋 Story 3/7: [title]`). Rationale: if a session ends mid-batch, stale batch-queue items in TodoWrite create false process drift signals.

For each story in topological order:

0. **Skeleton check (STOP tier on failure):** If story status is `specifying` (no spec), run `/spec STORYID` inline for upstream ceremony. After /spec completes (APPROVED-SPEC emitted, story updated via PATCH), re-query to confirm `ready_to_pull` status before proceeding. **If re-query shows story is NOT `ready_to_pull`:** Output `❌ STOP: Inline /spec for [STORYID] completed but story is in [status] — expected ready_to_pull. Resume: /batch EPICNAME --resume STORYID`. If /spec fails or user rejects: STOP batch with `❌ STOP: Upstream failed for [STORYID] "[title]" — /spec did not complete successfully. Resume: /batch EPICNAME --resume STORYID`
1. **Setup:** Pull-rebase, claim + transition story to in_progress:
   ```bash
   source scripts/hub-client.sh
   hub_claim "$STORY_UUID" "$EUPRAXIS_AGENT_NAME"
   hub_transition "$STORY_UUID" "in_progress"
   ```
2. **Execute:** TDD per AC (Story/BUG/Refactor) or direct (SDLC/Data). Run all test suites per AC
   - **Complexity + Model Advisory (BLOCKED):** `BLOCKED: Sonnet benchmark failed — per-story complexity classification deferred. All stories execute on Opus. See docs/research/logs/RESEARCH-LOG-2026-04-06.12-09-19-MODEL-TIERING-COMPLEXITY.md`
3. **Code Review:** Run **code-review** (Gate Keeper MODE 3) for code types — critical = STOP batch
4. **Quality & Ship Readiness** (matches `/pull` Step 4):
   - Run all test suites (final run). Emit SUITES-GREEN
   - Verify gate stamps (upstream + downstream)
   - Update documentation per Rule 5
   - Fill compliance checklist + drift review
   - BUG runtime verification gate (BUG stories only)
   - PATCH downstream content to DB
   - **For capstone stories:** `/pull` Step 4g4 invokes Gate Keeper MODE 5 (epic-review) before ship-review. On FAIL, auto-BUG creation fires (see `.claude/agents/gate-keeper.md` §Auto-Create Follow-up BUG Stories) and batch STOPs
   - Run **ship-review** (Gate Keeper MODE 4, `.claude/agents/gate-keeper.md`) — critical = STOP batch. Gate Keeper emits DOCS, COMPLIANCE, DRIFT, GATE-SHIP. `push-gate.sh` enforces `gate-ship` marker before push
5. **Ship** (invoke `/ship STORYID` — git plumbing only):
   - `echo SHIP_COMPLETE` + commit per CLAUDE.md §Git Workflow
   - Pull-rebase → push → transition to `done` (after push) → emit `SHIPPED:`
   - Proceed to next story

---

## Epic Auto-Complete (Capstone Detection)

After each story ships, check if the shipped story is the **capstone** (title matches regex `^S\d+ .+ \| Story \| Capstone$`). If so:

1. Resolve epic UUID from the story's `epic_id`
2. Call `POST /api/v1/epics/{epic_id}/complete` to transition epic to COMPLETE status
3. Log: `✅ Epic [EPICNAME] auto-completed. All stories done + capstone verified.`

**Skip if:** Story title does not match capstone convention, or story has no `epic_id`.

```bash
source scripts/hub-client.sh
# After capstone ships:
if echo "$STORY_TITLE" | grep -qE "\| Story \| Capstone$"; then
  hub_post "/api/v1/epics/$EPIC_UUID/complete" '{}'
fi
```

---

## Stop-on-Failure + Resumption

STOP on: persistent test failure, code-review critical, ship-review critical, **epic-review critical (MODE 5 FAIL on capstone)**, git conflict, dependency not met. Report status and `Resume: /batch EPICNAME --resume STORYID`.

**After MODE 5 FAIL (capstone stories):** Gate Keeper auto-creates BUG story skeletons (see `.claude/agents/gate-keeper.md` §Auto-Create Follow-up BUG Stories). Resume procedure: fix each BUG via `/spec` + `/pull`, then retry capstone with `/batch EPICNAME --resume [CAPSTONE_STORYID]`. MODE 5 re-runs on the capstone and verifies fixes.

**On batch completion or failure stop**, remove the execution mode marker:
```bash
source .claude/hooks/lib/hub-query.sh
rm -f "/tmp/claude-sticky-exec-mode-$(resolve_marker_id)"
```

**Resumption:** Verify fix, continue from STORYID. Skip stories already done. The batch skill re-creates the sticky exec-mode file on resume (Step 4 runs again).

---

## Gate Summary

**Structurally enforced (Gate Keeper, `.claude/agents/gate-keeper.md`):**
- combined upstream review (MODE 1) — `plan-review-gate.sh` blocks code before approval (marker set during `/spec`)
- code-review (MODE 3) + tests — `pre-commit-test-gate.sh` blocks commit
- ship-review (MODE 4) — `push-gate.sh` blocks push without `gate-ship` marker

**Preserved:** TDD, compliance, drift, git discipline, gate stamps, per-story commits, stop-on-failure, transition to done after push
