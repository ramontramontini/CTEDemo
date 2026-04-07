---
name: pull
description: >
  Pull and execute a single story end-to-end: claim, TDD, code-review, quality
  verification (tests, docs, compliance, drift, ship-review), then ship.
  Covers full downstream from ready_to_pull to done. All gates structurally enforced.
---

# /pull — Single Story Downstream Execution

**Usage:**
- `/pull STORYID` or `/pull Story Title` — execute story from ready_to_pull through done
- `/pull STORYID --resume` or `/pull Story Title --resume` — resume an in_progress story (skip claim)

> **Argument resolution:** The argument can be a **UUID**, **STORYID** (timestamp `YYYY-MM-DD.HH-MM-SS`), or a **story title** (any other string). Pass the argument directly as a path parameter — the API resolves it server-side (UUID → timestamp → title, case-insensitive with substring fallback). Single match → resolved. Zero matches → 404. Multiple title matches → 409 `AMBIGUOUS_MATCH` with `matches` array — present candidates via AskUserQuestion. URL-encode titles containing `/`, `?`, or `#`. If no story found (404), try epic resolution via `GET /api/v1/epics/$ARGUMENT` — if found, fall back to `/batch EPICNAME`.

> **Sources:** CLAUDE.md §Lifecycle Downstream, §TDD Standards, §Git Workflow, §Policy 9
>
> **Hub API:** Source `scripts/hub-client.sh` for all API operations. Provides `hub_get()`, `hub_post()`, `hub_patch()`, `hub_claim()`, `hub_transition()` with 3-retry exponential backoff. See `.claude/skills/hub-api-helpers.md` for idempotency notes. Gate stamps are emitted as side effects of `gate-review` and `test-results` endpoints — no direct `hub_emit_stamp()` needed.
>
> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT). Each operation below is classified per-tier.
>
> **Prerequisite:** Upstream must be complete — APPROVED-SPEC emitted, execution plan approved, story in `ready_to_pull` status (or `in_progress` with `--resume`).

---

## Step 1: Lookup + Validate

1. Validate argument is present. If missing: report usage hint and stop
2. Look up story using path-based resolution (single call replaces 3 status-filtered queries):
   ```bash
   source scripts/hub-client.sh
   hub_get "/api/v1/stories/$ARGUMENT"
   ```
   - **200** → story found. Route based on `data.status` field (see Status Routing table below).
   - **404** → no story found. Try epic fallback: `hub_get "/api/v1/epics/$ARGUMENT"`. If 200 → fall back to `/batch EPICNAME`. If 404 → report not found. STOP.
   - **409** → ambiguous title match. Parse `error.matches` array, present candidates via AskUserQuestion.
3. Extract: UUID (`id`), Type, Title, ACs, Spec (contains Execution Plan section), Execution Log (if resuming)

### Status Routing

| Status | `--resume` | Action |
|--------|-----------|--------|
| `ready_to_pull` | — | Proceed to Step 2 (Claim) |
| `in_progress` | Yes | Proceed to Step 2b (Resume) |
| `in_progress` | No | Report: "[title] (STORYID) is in_progress. Use `/pull STORYID --resume` to continue." STOP |
| `claimed` | — | Report: "Story claimed by another agent. Use `--resume` if authorized to take over." STOP |
| `specifying` | — | **Skeleton story detected.** Run `/spec STORYID` inline for upstream ceremony, then continue with downstream (claim, execute, ship). See Step 2c below |
| `spec_complete` | — | Report: "Upstream incomplete. Run `/spec` first." STOP |
| `done` / `canceled` | — | Report: "Story in terminal state [status]. No action." STOP |
| Not found | — | Report: "Story STORYID not found." STOP |

**API unreachable:** Report: "Hub API unreachable at $EUPRAXIS_HUB_URL — is main running?" STOP.

---

## Step 2: Claim + Transition

### 2a: Fresh Start (status = `ready_to_pull`)

1. Pull-rebase (stash-aware): `source .claude/hooks/lib/safe-rebase.sh && git fetch origin && safe_rebase . origin/main`
2. **Structured field recovery (MANDATORY — BUG 2026-03-13.18-38-08 AC7):** Check ALL 10 upstream content fields (context, goal, user_journey, wireframes, edge_cases, risks, data_model_changes, api_contract_changes, business_rules, verification_criteria) for null values. If ANY are null and the story has a non-null `spec` field, PATCH the spec to trigger backend auto-extraction:
   ```bash
   source scripts/hub-client.sh
   # PATCH spec field to itself — backend auto-extract fills null structured fields
   hub_patch "/api/v1/stories/$STORY_UUID" "{\"spec\": $(echo "$STORY_SPEC" | jq -Rs .)}"
   ```
   The backend `_auto_extract_upstream_fields()` parses `## Section` headers from spec and fills only null fields (preserves non-null). This also handles acceptance_criteria via VO hydration.
   **Skip if:** All 10 fields are already non-null, or `spec` is null (skeleton story).
   **If PATCH fails:** Output `⚠️ WARNING: structured field recovery PATCH failed ([detail]) — ACs may be incomplete in DB — recovery: hub_patch "/api/v1/stories/$STORY_UUID" with spec field`. Continue to Step 2a.3.
   **If extraction finds nothing:** Log warning and continue — fields stay null (auditable via SDLC audit).
   **Inherited by /batch:** /batch invokes /pull per story, so recovery applies automatically.
3. **Spec check (old-flow detection):** Verify `spec` is non-null. If null: Report: "Upstream incomplete. Run `/spec` first." STOP.
4. Claim story:
   ```bash
   source scripts/hub-client.sh
   hub_claim "$STORY_UUID" "$EUPRAXIS_AGENT_NAME"
   ```
   **409 conflict (exit 1):** "Story already claimed by another agent." STOP.
   **Retry:** Non-idempotent — check if already claimed by this agent before retry.
5. Transition to in_progress:
   ```bash
   hub_transition "$STORY_UUID" "in_progress"
   ```
   **Retry:** Non-idempotent — check current status before retry.
6. Create active-story tracking files (enables todo-capture.sh progress + prevents marker over-clearing on upstream→downstream transition — BUG 2026-03-26.17-22-46):
   ```bash
   source .claude/hooks/lib/hub-query.sh
   echo "$STORY_ID" > "/tmp/claude-active-story-$(resolve_marker_id)"
   echo "$STORY_UUID" > "/tmp/claude-active-story-uuid-$(resolve_marker_id)"
   ```

### 2a.7: Spec Context Display (MANDATORY)

> Ensures the full story spec enters the agent's context window before any code work begins. Prevents misaligned implementations by front-loading comprehension. Gate Keeper code-review (MODE 3) verifies coherence downstream; this step reduces wasted work from late detection.

1. Re-fetch story from API for fresh post-claim state:
   ```bash
   source scripts/hub-client.sh
   STORY_DATA=$(hub_get "/api/v1/stories/$STORY_UUID")
   ```
   **If API call fails:** Fall back to story data from Step 1 response. Log: `⚠️ WARNING: fresh fetch failed — using Step 1 data for spec context display.`

2. Render the full spec in a structured block. Extract each field from the API response and output:
   ```
   === SPEC CONTEXT ===
   Title: [title] | Type: [type] | Epic: [epic_id or "none"] | Dependencies: [count]

   **Goal:** [goal field]

   **Context:** [context field]

   **Acceptance Criteria:**
   [Full GWT per AC from acceptance_criteria array — Given/When/Then]

   **User Journey:** [user_journey field]

   **Edge Cases:** [edge_cases field]

   **Risks:** [risks field]

   **Execution Plan:**
   [Extract the "## Execution Plan" section from the spec field]
   === END SPEC CONTEXT ===
   ```

3. If any field is null, render it as `[not specified]`. The spec field itself was already validated as non-null in Step 2a.3.

4. **Complexity Classification (BLOCKED):** `BLOCKED: Sonnet benchmark failed — complexity-based model selection deferred. See docs/research/logs/RESEARCH-LOG-2026-04-06.12-09-19-MODEL-TIERING-COMPLEXITY.md`. All sessions execute on Opus until benchmark passes.

### 2b: Resume (status = `in_progress`, `--resume` flag)

1. Pull-rebase (stash-aware): `source .claude/hooks/lib/safe-rebase.sh && git fetch origin && safe_rebase . origin/main`
2. **Spec check (old-flow detection):** Verify `spec` is non-null. If null: Report: "Upstream incomplete. Run `/spec` first." STOP.
3. Read Execution Plan section from spec and Execution Log from the story (via GET response from Step 1)
4. Report: "Resuming [title] (STORYID). Last action: [from log]. Next task: [from plan]."
5. Update lock timestamp if stale (>4h):
   ```bash
   hub_claim "$STORY_UUID" "$EUPRAXIS_AGENT_NAME"
   ```
6. Create active-story tracking files (same as Step 2a.6 — prevents marker over-clearing on resume):
   ```bash
   source .claude/hooks/lib/hub-query.sh
   echo "$STORY_ID" > "/tmp/claude-active-story-$(resolve_marker_id)"
   echo "$STORY_UUID" > "/tmp/claude-active-story-uuid-$(resolve_marker_id)"
   ```
### 2b.6a: Spec Context Display (MANDATORY — same as Step 2a.7)

Render the same `=== SPEC CONTEXT ===` block as Step 2a.7, using the story data from the Step 1 GET response. Additionally, append the Execution Log showing completed work:

```
=== RESUME CONTEXT ===
**Execution Log (completed work):**
[execution_log entries from API response]

**Last Action:** [most recent log entry]
**Next Task:** [from execution plan, first incomplete step]
=== END RESUME CONTEXT ===
```

7. Determine resume point from execution log and skip completed steps

### 2c: Skeleton Story (status = `specifying`, no `--resume`)

1. Pull-rebase (stash-aware): `source .claude/hooks/lib/safe-rebase.sh && git fetch origin && safe_rebase . origin/main`
2. Verify story has null/empty `spec` (confirms skeleton created by epic auto-creation)
3. Log: "Skeleton story detected — running upstream ceremony before downstream."
4. Invoke `/spec STORYID` — this triggers skeleton update mode in /spec (Step 1 detects existing specifying story, runs full ceremony, PATCHes spec content). After /spec completes: APPROVED-SPEC emitted, story spec populated, story transitions through `spec_complete` → `ready_to_pull`
5. Re-query story from API to confirm `ready_to_pull` status. If not ready_to_pull: STOP with error
6. Proceed to Step 2a (Fresh Start) — claim and execute downstream

---

## Step 3: Execute (Type-Discriminated)

> **AC progress rule (all types):** Each AC MUST be marked met individually via **separate** `mark-ac-met` API calls. After each call, update TodoWrite and output `✅ AC[K]/[total] met: [AC name]` before proceeding to the next AC's work. Do NOT batch multiple `mark-ac-met` calls in a single Bash command — the WebSocket broadcast that drives the progress bar fires per call, so batching produces a single jump instead of incremental progress visible to the user.

### Code Types: feature, bug, refactoring

**Before starting TDD:** Create a TodoWrite task list with one item per AC. For resume (`--resume`), initialize already-met ACs (where `acceptance_criteria[K-1].met == true`) as `completed`:

```
TodoWrite: [
  {content: "AC1: [name]", status: "pending", activeForm: "Implementing AC1: [name]"},
  {content: "AC2: [name]", status: "pending", activeForm: "Implementing AC2: [name]"},
  ...
]
```

TDD cycle per AC — for each acceptance criterion (track 1-based AC number K: AC1=1, AC2=2, AC3=3, etc.):

0. **TodoWrite:** Mark AC[K] as `in_progress` (all others remain pending or completed)
1. **RED:** Write failing test that validates the AC. Emit `RED: [test path]`. Evidence stamps (RED, GREEN) are now recorded as side effects of gate-review — no separate stamp emission call needed.
2. **GREEN:** Write minimal implementation to pass. Run only the TDD test file(s) for this AC — not the full suite. Cross-suite and intra-suite regression deferred to Step 4a (pre-commit gate, all 3 suites). Emit `GREEN: [count] tests passing`.
   ```
3. **Mark AC met (real-time progress — WARN tier):** Call the hub API to mark this AC as completed. This triggers a WebSocket broadcast so users see progress bars update in real-time on Story Cards and Story Detail views. Non-blocking — if the call fails, output a visible warning and continue execution.
   ```bash
   source scripts/hub-client.sh
   hub_post "/api/v1/stories/$STORY_UUID/mark-ac-met" "{\"ac_number\": $K}" \
     && echo "AC$K marked met" \
     || echo "WARNING: mark-ac-met failed for AC$K (non-blocking)"
   ```
   Where `$K` is the AC's position in the story's AC list (1-based). Determine K from the AC heading number, not from iteration sequence.
   **If fails:** Output `⚠️ WARNING: mark-ac-met failed for AC$K ([HTTP status]) — progress bar won't update — recovery: hub_post "/api/v1/stories/$STORY_UUID/mark-ac-met" '{"ac_number": $K}'`. Continue to next step.
4. **TodoWrite + Progress:** Mark AC[K] as `completed` in TodoWrite. Output progress to user:
   - On success: `✅ AC[K]/[total] met: [AC name]`
   - On mark-ac-met failure: `⚠️ WARNING: mark-ac-met failed for AC[K] ([detail]) — progress bar won't update — recovery: hub_post mark-ac-met` — still mark TodoWrite as completed
5. **REFACTOR:** Clean up if needed. Re-run TDD test file(s) to confirm

**Test failure:** STOP. Analyze root cause (test bug vs code bug). Fix. Re-run TDD test file(s). Zero failures required. All suites run once at Step 4a (pre-commit gate).

Then run **code-review** (Gate Keeper MODE 3):

```
Agent tool:
  subagent_type: gate-keeper
  model: "opus"
  prompt: "code-review for story [STORYID]. Story UUID: $STORY_UUID. [Summary of changes + test results]"
```

**On VERDICT: PASS:** Proceed to Step 4.
**On VERDICT: FAIL:** Fix critical issues, then re-run code-review in **Retry Mode** — capture the `gate-keeper-summary` JSON block from the FAIL report and include it in the retry prompt:
```
Agent tool:
  subagent_type: gate-keeper
  model: "opus"
  prompt: "code-review for story [STORYID]. Story UUID: $STORY_UUID. [Summary of changes + test results]

PRIOR_REVIEW
[paste the full gate-keeper-summary JSON from the FAIL verdict, verbatim]
END_PRIOR_REVIEW"
```
Gate Keeper re-evaluates only categories with CRITICAL findings, carrying forward clean categories. See `.claude/agents/gate-keeper.md` §Retry Mode.
**On subagent failure:** Retry once. If still fails, manual review using MODE 3 checklist. Gate Keeper persists `review_code` stamp via `POST /gate-review` on PASS.

**Gate friction summary:** Recorded structurally — Gate Keeper includes `friction_summary` + `session_id` in the `POST /gate-review` payload. The backend auto-creates the `ChatHistoryEntry`. No separate `hub_record_chat_history` call needed.

> **Note:** `POST /api/v1/stories/{id}/gate-stamps` returns 410 Gone. All stamp emission goes through `POST /gate-review` (Gate Keeper) or `POST /test-results` (test-emitter.sh).

### Non-Code Types: sdlc, data, maintenance, investigation

Direct execution — no TDD cycle, no code-review.

**Before starting execution:** Create a TodoWrite task list with one item per AC (same format as code types). For resume (`--resume`), initialize already-met ACs (where `acceptance_criteria[K-1].met == true`) as `completed`:

```
TodoWrite: [
  {content: "AC1: [name]", status: "pending", activeForm: "Executing AC1: [name]"},
  {content: "AC2: [name]", status: "pending", activeForm: "Executing AC2: [name]"},
  ...
]
```

Per-AC execution — for each acceptance criterion (track 1-based AC number K):

0. **TodoWrite:** Mark AC[K] as `in_progress` (all others remain pending or completed)
1. **Execute:** Complete task(s) for this AC per the execution plan
2. **Mark AC met (real-time progress — WARN tier):** Call the hub API to mark this AC as completed. This triggers a WebSocket broadcast so users see progress bars update in real-time. Non-blocking — if the call fails, output a visible warning and continue.
   ```bash
   source scripts/hub-client.sh
   hub_post "/api/v1/stories/$STORY_UUID/mark-ac-met" "{\"ac_number\": $K}" \
     && echo "AC$K marked met" \
     || echo "WARNING: mark-ac-met failed for AC$K (non-blocking)"
   ```
   **If fails:** Output `⚠️ WARNING: mark-ac-met failed for AC$K ([HTTP status]) — progress bar won't update — recovery: hub_post "/api/v1/stories/$STORY_UUID/mark-ac-met" '{"ac_number": $K}'`. Continue to next step.
3. **TodoWrite + Progress:** Mark AC[K] as `completed` in TodoWrite. Output progress to user:
   - On success: `✅ AC[K]/[total] met: [AC name]`
   - On mark-ac-met failure: `⚠️ WARNING: mark-ac-met failed for AC[K] ([detail]) — progress bar won't update — recovery: hub_post mark-ac-met` — still mark TodoWrite as completed

After all ACs: Run applicable test suites if any code was modified (even for non-code types, tests must pass)

---

## Step 4: Quality & Ship Readiness

> All quality work happens here — BEFORE commit and BEFORE transition to done. This ensures stories only move to "done" when everything is truly verified. Each substep is tracked via TodoWrite for board visibility.

**TodoWrite:** Append quality items after AC items when entering Step 4:

```
TodoWrite: [
  ...existing AC items (completed)...,
  {content: "Run all test suites", status: "pending", activeForm: "Running all test suites"},
  {content: "Verify gate stamps", status: "pending", activeForm: "Verifying gate stamps"},
  {content: "Update documentation", status: "pending", activeForm: "Updating documentation"},
  {content: "Fill compliance checklist", status: "pending", activeForm: "Filling compliance checklist"},
  {content: "Fill drift review", status: "pending", activeForm: "Filling drift review"},
  {content: "PATCH downstream content to DB", status: "pending", activeForm: "PATCHing downstream content to DB"},
  {content: "Epic write-back (if applicable)", status: "pending", activeForm: "Checking epic write-back"},
  {content: "Ship review (Gate Keeper)", status: "pending", activeForm: "Running ship review (Gate Keeper)"},
  {content: "Record session recap", status: "pending", activeForm: "Recording session recap"}
]
```

For BUG stories **only**, add before "PATCH downstream content" — do NOT add for non-BUG stories (feature, refactor, SDLC, data, maintenance, investigation):
```
  {content: "BUG runtime verification", status: "pending", activeForm: "Running BUG runtime verification"}
```

### 4a: Test Suites (Final Run)

> Invoke `/run-all-tests` — rebases from origin/main first, then runs all 3 suites sequentially. This ensures `SUITES-GREEN` reflects the latest main state. See `.claude/skills/run-all-tests/SKILL.md`.

- **Story/BUG/Refactor:** Run all suites via `/run-all-tests`. STOP if any fail.
- **SDLC/Data:** Skip if no code changes; run applicable suites if code exists.
- `test-emitter.sh` (PostToolUse) auto-emits `SUITES-GREEN @<origin/main SHA>` when all 3 pass via `POST /api/v1/stories/{uuid}/test-results`. **SUITES-GREEN verification (WARN tier):** After all suites pass, query the API to confirm the stamp was emitted: `hub_get "/api/v1/stories/$STORY_UUID"` and check for `suites_green` in `gate_stamps`. If not present after 5 seconds: output `⚠️ WARNING: SUITES-GREEN stamp not emitted by test-emitter.sh — commit-gate will block — recovery: hub_record_test_results "$STORY_UUID" "[suites_json]" "[origin_sha]"`. Manual persist:
  ```bash
  source scripts/hub-client.sh
  hub_record_test_results "$STORY_UUID" '["backend","api","frontend"]' "$(git rev-parse origin/main)"
  ```
- **TodoWrite:** Mark "Run all test suites" as `completed`

### 4a2: Runtime AC Verification

> Automated tests verify correctness; runtime verification verifies the user experience. Agent MUST verify each AC is met from the user's perspective before calling ship-review.

**Verification by story type:**
- **UI stories:** Use preview tools (`preview_screenshot`, `preview_snapshot`, `preview_inspect`) to verify visual changes match AC expectations
- **API/backend stories:** `curl` endpoints and verify response shapes match AC expectations
- **Domain stories:** Run verification commands or read test output to confirm behavior
- **Directive-only stories (SDLC):** Read the changed files and verify text matches AC requirements

**Procedure:**
1. For each AC, verify it is met from the user's perspective (not just "tests pass")
2. Document verification results in the story's execution log
3. If an AC cannot be runtime-verified (pure refactor, no observable behavior), note justification

This runs in addition to (not replacing) automated tests in 4a.

### 4b: Gate Stamp Verification

> Verify per CLAUDE.md §Policy 9. STOP if any required stamp missing.

| Phase | Required Stamps | Applies To |
|-------|----------------|------------|
| Upstream | GATE-SPEC, GATE-PLAN, APPROVED-SPEC, PLAN | ALL types |
| Upstream (UI) | WIREFRAME | UI stories only |
| Downstream | GATE-CODE | Story/BUG/Refactor only (SDLC/Data exempt) |
| Ship | SUITES-GREEN (emitted in 4a) | ALL types with code changes |

- **TodoWrite:** Mark "Verify gate stamps" as `completed`

### 4c: Documentation

> Update per CLAUDE.md §Rule 5. Agent prepares documentation updates — Gate Keeper ship-review (4h) independently verifies and emits `DOCS: [files]`.

- **TodoWrite:** Mark "Update documentation" as `completed`

### 4d: Compliance Checklist

> **Canonical keys (MANDATORY):** Fetch the story type's canonical items via `GET /api/v1/compliance/template?type={story_type}`. Each item has a stable `key`, `label`, `description`, and `gate`. The `key` field is **required** when submitting compliance items — unknown keys cause `422 UNKNOWN_COMPLIANCE_KEYS`. See `.claude/skills/hub-api-helpers.md` §Execution & Compliance Endpoints for full schema documentation.
>
> **Fallback:** If template endpoint unavailable, reference `docs/templates/compliance-checklist.md` for canonical key reference.

```bash
source scripts/hub-client.sh
# 1. Fetch canonical template
TEMPLATE=$(hub_get "/api/v1/compliance/template?type=$STORY_TYPE")
# 2. Iterate canonical items, assess each as checked: true/false with optional na_reason
# 3. Submit with canonical keys:
hub_post "/api/v1/stories/$STORY_UUID/compliance" '{
  "items": [
    {"key": "<canonical_key>", "label": "<label>", "checked": true},
    {"key": "<canonical_key>", "label": "<label>", "checked": false, "na_reason": "<justification>"}
  ]
}'
```

**Error handling:** If `POST /compliance` returns `422 UNKNOWN_COMPLIANCE_KEYS`, re-fetch the template and use only keys from the `items[].key` values in the response. Do NOT construct keys manually.

- **TodoWrite:** Mark "Fill compliance checklist" as `completed`

### 4e: Drift Review (Automated Classification)

> `drift_type` is **auto-computed from evidence** at DONE transition — agents do NOT classify drift. Agent writes a qualitative narrative only. Gate Keeper ship-review (4h) independently verifies and emits `DRIFT: [none/detected]`.

**Agent writes:** Narrative drift_review text describing any process friction, plan deviations, or observations. No classification line needed.

**Agent PATCHes drift_type only if:** The agent knowingly deviated from the approved plan. In that case, PATCH `drift_type: "plan_drift"` to the story. All other drift_type values are auto-computed:
- `friction` — auto-detected from gate FAIL verdicts in gate_verdicts history
- `bug` / `regression` — auto-escalated when BUG stories are created with source_story_id
- `none` — default when no evidence of drift

```bash
# Only if plan deviation occurred:
source scripts/hub-client.sh
hub_patch "/api/v1/stories/$STORY_UUID" '{"drift_type": "plan_drift"}'
```

- **TodoWrite:** Mark "Fill drift review" as `completed`

### 4f: BUG Runtime Verification Gate (BUG Stories Only)

If story type is BUG, STOP and verify before proceeding:
1. **Verification Criteria section** exists in story file (not empty/placeholder)
2. **"How to Reproduce"** subsection has numbered steps filled (not template placeholders)
3. **"Runtime Verification"** checklist items are all completed: `[x]` or `[N/A] — reason`
4. Any unchecked `[ ]` item = **BLOCKING** — agent must complete verification before shipping

If not a BUG story: skip this gate.

- **TodoWrite:** Mark "BUG runtime verification" as `completed` (BUG stories only)

### 4g: PATCH Downstream Content to DB

> **Why before ship-review:** Content must be in DB for Gate Keeper to verify independently.

Persist downstream content using structured endpoints and PATCH. Each field uses its optimal path:

**1. Compliance checklist** — use structured endpoint with canonical keys (do NOT include in PATCH body):
```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/compliance" '{
  "items": [
    {"key": "spec_complete", "label": "Spec complete (Context, Goal, ACs G/W/T, User Journey, Edge Cases 3+, Risks)", "checked": true},
    {"key": "tdd_followed", "label": "TDD: RED->GREEN->REFACTOR documented per AC", "checked": true},
    {"key": "wireframes", "label": "Wireframes present or N/A justified (Policy 14)", "checked": false, "na_reason": "backend-only story"}
  ]
}'
```
Each item has `key` (canonical key from registry — required for new stories), `label` (string), `checked` (boolean), and optional `na_reason` (string). Backend validates keys against the story type's canonical registry (422 for unknown keys, warnings for missing keys). Query `GET /api/v1/compliance/template?type={type}` for the canonical item set.

**2. Execution log** — use structured endpoint (do NOT include in PATCH body):
```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/execution-log" '{
  "entries": [
    "AC1: Description of what was done",
    "AC2: Description of what was done"
  ]
}'
```
Each entry is a plain string. Backend creates `LogEntry` VOs with server-side UTC timestamps — no bullet format needed.

**3. Drift review + acceptance criteria** — use PATCH for remaining text fields:
```bash
source scripts/hub-client.sh
hub_patch "/api/v1/stories/$STORY_UUID" '{
  "drift_review": "<drift review content>",
  "acceptance_criteria": "<acceptance criteria content>"
}'
```

Only include fields that have content.

**IMPORTANT — acceptance_criteria format:** The `acceptance_criteria` text MUST use checkbox format to preserve AC met state through `hydrate_vos_from_raw()` rehydration. Before constructing the text, read the current story from `GET /api/v1/stories/{id}` and check each AC's `met` field in the `acceptance_criteria` array. Format each AC as:
- `- [x] ACN: Name` — if `acceptance_criteria[N-1].met == true`
- `- [ ] ACN: Name` — if `acceptance_criteria[N-1].met == false`

Using `### ACN:` header format (without checkboxes) will reset all ACs to `met=false`.

**IMPORTANT:** Do NOT include `gate_stamps` in this PATCH — the PATCH path is destructive (calls `vo_list.clear()`). Gate stamps are persisted as side effects of `POST /api/v1/stories/{id}/gate-review` and `POST /api/v1/stories/{id}/test-results` throughout the lifecycle. Direct stamp emission via `POST /gate-stamps` returns 410 Gone.

**Per-call error handling (WARN tier):** Each of the three calls is independent. If any fails:
- Compliance POST fails: `⚠️ WARNING: compliance POST failed ([detail]) — ship-review may flag incomplete compliance — recovery: hub_post "/api/v1/stories/$STORY_UUID/compliance" '{...}'`
- Execution-log POST fails: `⚠️ WARNING: execution-log POST failed ([detail]) — ship-review may flag empty log — recovery: hub_post "/api/v1/stories/$STORY_UUID/execution-log" '{...}'`
- Drift/AC PATCH fails: `⚠️ WARNING: downstream PATCH failed ([detail]) — DB content stale — recovery: hub_patch "/api/v1/stories/$STORY_UUID" '{...}'`
Continue to the next call regardless — do NOT stop on any individual failure.

**Retry:** All three calls (compliance, execution-log, PATCH) are **idempotent** — safe to retry directly (same payload produces same result).

- **TodoWrite:** Mark "PATCH downstream content to DB" as `completed`

### 4g2: Stage Files for Ship Review

> **Why before ship-review:** Gate Keeper uses `git diff --cached` to inspect changes during ship-review. Files must be staged (`git add`) so they appear in the cached diff. Without staging, Gate Keeper sees an empty diff and cannot verify code changes.

1. Run `git status --porcelain` to check for unstaged changes
2. If output is empty: log "No unstaged changes — skipping pre-review staging" and skip to 4h
3. If non-empty: stage modified and new files using explicit paths from `git status --porcelain` output
   - **Exclude `temp/` directory** — scratch files must not be staged
   - Use `git add <file1> <file2> ...` with specific paths (NOT `git add -A` or `git add .`)
4. Verify staging: run `git diff --cached --stat` to confirm files are staged

**On ship-review FAIL:** After fixing issues flagged by Gate Keeper, re-stage changed files before re-running ship-review (staging is not preserved across edits).

- **TodoWrite:** `{content: "Stage files for ship-review", status: "pending"}`

### 4g3: Epic Write-Back (conditional — only for epic stories)

> Feeds execution discoveries back to the parent epic so subsequent stories benefit from accumulated context.

**If story has null `epic_id`:** Skip this step entirely. Log nothing.

**If story has non-null `epic_id`:** Evaluate whether execution revealed significant deviations:
- **(a) AC deviations from plan** — implementation required changes not anticipated in the approved plan
- **(b) New risks discovered** — risks that materialized or were identified during execution
- **(c) New edge cases discovered** — edge cases found during TDD or runtime verification
- **(d) Dependency changes** — story required changes to the dependency graph (added/removed dependencies)

**If no deviations found:** Log "No epic write-back needed — execution matched plan." Skip PATCH.

**If deviations found:**

1. Fetch current epic state:
   ```bash
   source scripts/hub-client.sh
   hub_get "/api/v1/epics/$EPIC_ID"
   ```

2. For each affected field, construct the updated value by appending a discovery section:
   ```
   [existing field content]

   ## Discovered During [STORYID]

   [description of what was discovered and why it matters for remaining epic stories]
   ```
   - If the existing field is null/empty, set the field to just the `## Discovered During` section (no append)
   - **Only include fields that have actual discoveries** — do not PATCH unchanged fields

3. PATCH the epic with updated fields:
   ```bash
   source scripts/hub-client.sh
   hub_patch "/api/v1/epics/$EPIC_ID" '{
     "risks": "<updated risks with discovery appended>",
     "edge_cases": "<updated edge cases with discovery appended>",
     "dependency_graph": "<updated dependency graph if changed>"
   }'
   ```
   Only include fields that were actually updated. Omit unchanged fields.

4. Log result: `"Epic write-back: updated [field names] for epic [EPIC_NAME]"`

**Fail-open:** If the GET or PATCH fails (API unreachable, 404, 422), log warning "Epic write-back failed (non-blocking) — [error]" and continue to ship-review. **Never block story shipping due to epic write-back failure.**

**Over-enrichment guard:** Only append content that represents a *significant* deviation — not routine implementation details. If the agent is uncertain whether a discovery is significant, skip the write-back. Conservative is better than noisy.

- **TodoWrite:** Mark "Epic write-back (if applicable)" as `completed`

### 4g4: Epic Review (Capstone Stories Only)

> **Gate:** MODE 5 (epic-review) is the cross-story integration gate for capstone stories. Ensures all epic acceptance criteria (EACs) are verified across the full story set before the epic can complete. On FAIL, Gate Keeper auto-creates BUG story skeletons (see `.claude/agents/gate-keeper.md` §On VERDICT: FAIL — Auto-Create Follow-up BUG Stories).

**Detection:** Check if the story title matches the capstone pattern `^S\d+ .+ \| Story \| Capstone$` (regex-based detection via `is_capstone_title()` in `epic_validation.py`).

**If NOT a capstone story:** Skip this step entirely. Proceed to 4h.

**If capstone story:**

1. Invoke Gate Keeper MODE 5 (epic-review):
   ```
   Agent tool:
     subagent_type: gate-keeper
     model: "opus"
     prompt: "epic-review for story [STORYID]. Story UUID: $STORY_UUID.
              Epic: [EPICNAME]. Read capstone spec for EACs.
              Query all sibling story UUIDs from epic_id."
   ```

2. **On VERDICT: PASS:**
   - Gate Keeper persists `GATE-EPIC` stamp via `POST /api/v1/stories/{UUID}/gate-review`
   - Log: `✅ Epic review PASS — proceeding to ship-review`
   - Proceed to Step 4h (Ship Review)

3. **On VERDICT: FAIL:**
   - Gate Keeper auto-creates BUG story skeletons per `.claude/agents/gate-keeper.md` MODE 5 §Auto-Create Follow-up BUG Stories
   - **STOP execution.** Output:
     ```
     ❌ STOP: Epic review FAIL — [count] CRITICAL finding(s).
     Auto-created BUG stories: [list of story IDs and titles]
     Fix BUGs via /spec + /pull for each, then resume: /pull STORYID --resume
     ```
   - Do NOT proceed to ship-review

4. **On subagent failure:** Retry once. If still fails, perform manual review using MODE 5 checklist from `.claude/agents/gate-keeper.md`. Gate Keeper persists `GATE-EPIC` stamp via `POST /gate-review` on PASS. For manual review, use:
   ```bash
   source scripts/hub-client.sh
   hub_post "/api/v1/stories/$STORY_UUID/gate-review" '{"gate_type": "epic", "result": "pass", "stamp_values": {"gate_epic": "pass (manual)"}}'
   ```

- **TodoWrite:** `{content: "Epic review (capstone only)", status: "pending"}` — only add for capstone stories (title detection at Step 4 entry). Mark as `completed` or `not applicable` based on capstone detection.

**Gate friction summary:** Recorded structurally — Gate Keeper includes `friction_summary` + `session_id` in the `POST /gate-review` payload. The backend auto-creates the `ChatHistoryEntry`. No separate `hub_record_chat_history` call needed.

### 4g5: Pre-Flight DB Field Check (before Ship Review)

> **Why:** Gate Keeper ship-review (MODE 4, Opus) checks DOD fields — execution_log, compliance, drift_review, ACs met — and FAILs at CRITICAL level if any are empty. This lightweight pre-flight check catches missing fields before invoking an expensive Opus call. Mirrors Step 10b in `/spec` skill (upstream pre-flight).

After all PATCH operations in Steps 4g–4g4, fetch the story from the DB and verify required downstream fields are populated:

```bash
source scripts/hub-client.sh
STORY_JSON=$(hub_get "/api/v1/stories/$STORY_UUID")
MISSING=""
# Check execution_log non-empty
EL=$(echo "$STORY_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print('empty' if not d.get('execution_log') else 'ok')")
[ "$EL" = "empty" ] && MISSING="$MISSING execution_log"
# Check compliance non-empty
CL=$(echo "$STORY_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print('empty' if not d.get('compliance') else 'ok')")
[ "$CL" = "empty" ] && MISSING="$MISSING compliance"
# Check drift_review non-null
DR=$(echo "$STORY_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print('null' if not d.get('drift_review') else 'ok')")
[ "$DR" = "null" ] && MISSING="$MISSING drift_review"
# Check all ACs met
AC=$(echo "$STORY_JSON" | python3 -c "import sys,json; acs=json.load(sys.stdin)['data'].get('acceptance_criteria',[]); print('unmet' if any(not a.get('met') for a in acs) else 'ok')")
[ "$AC" = "unmet" ] && MISSING="$MISSING acceptance_criteria(unmet)"

if [ -n "$MISSING" ]; then
  echo "❌ STOP: Missing DOD fields before ship-review:$MISSING"
  echo "Fix missing fields and re-run Step 4g5 before invoking Gate Keeper."
  # Do NOT proceed to Step 4h
fi
```

**On failure:** STOP. List missing fields with actionable guidance (which Step to re-run). Do NOT invoke Gate Keeper (Step 4h) with empty DOD fields.
**On success:** Proceed to Step 4h (Ship Review).

### 4h: Ship Review (Gate Keeper)

> **Gate:** Ship-review is the final quality gate before code leaves the local machine. Structurally enforced by `push-gate.sh` (blocks push without `gate-ship` marker).

Invoke the Gate Keeper subagent (`.claude/agents/gate-keeper.md`, MODE 4: ship-review):

```
Agent tool:
  subagent_type: gate-keeper
  model: "opus"
  prompt: "ship-review for story [STORYID]. Story UUID: [UUID].
           Read story from API: GET $EUPRAXIS_HUB_URL/api/v1/stories/{UUID}
           Review ship readiness per MODE 4 checklist."
```

Gate Keeper independently verifies:
- DOD (all ACs met, all tests passing, execution log complete)
- Documentation updated and matches code
- Compliance checklist fully filled
- Prior gate stamps present (GATE-SPEC, APPROVED-SPEC, GATE-PLAN, GATE-CODE for code types)
- Independent drift review (4 dimensions: directive, architecture, process, rationalization)

**Gate Keeper emits:** `DOCS: [files]`, `COMPLIANCE: complete ([N]/[M])`, `DRIFT: [none/detected]`, `GATE-SHIP: [result]`

**On VERDICT: PASS:** Gate Keeper calls `POST /api/v1/stories/{UUID}/gate-review` to persist `review_ship` stamp (plus DOCS, COMPLIANCE, DRIFT stamps as side effects) → push unblocked. Proceed to Step 5.
**On VERDICT: FAIL:** Fix critical issues, then re-run ship-review in **Retry Mode** — capture the `gate-keeper-summary` JSON block from the FAIL report and include it in the retry prompt:
```
Agent tool:
  subagent_type: gate-keeper
  model: "opus"
  prompt: "ship-review for story [STORYID]. Story UUID: [UUID].
           Read story from API: GET $EUPRAXIS_HUB_URL/api/v1/stories/{UUID}
           Review ship readiness per MODE 4 checklist.

PRIOR_REVIEW
[paste the full gate-keeper-summary JSON from the FAIL verdict, verbatim]
END_PRIOR_REVIEW"
```
Gate Keeper re-evaluates only categories with CRITICAL findings, carrying forward clean categories. See `.claude/agents/gate-keeper.md` §Retry Mode. STOP if critical issues unresolved after retry.
**On subagent failure:** Retry once. If still fails, perform manual review using MODE 4 checklist. Use gate-review for manual stamp:
```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/gate-review" '{"gate_type": "ship", "result": "pass", "stamp_values": {"docs": "[files]", "compliance": "complete ([N]/[M])", "drift": "[none/detected]", "review_ship": "pass (manual)"}}'
```

> **Note:** All stamps (DOCS, COMPLIANCE, DRIFT, GATE-SHIP) are emitted as side effects of the gate-review call. `POST /api/v1/stories/{id}/gate-stamps` returns 410 Gone.

- **TodoWrite:** Mark "Ship review (Gate Keeper)" as `completed`

**Gate friction summary:** Recorded structurally — Gate Keeper includes `friction_summary` + `session_id` in the `POST /gate-review` payload. The backend auto-creates the `ChatHistoryEntry`. No separate `hub_record_chat_history` call needed.

### 4i: Session Capture (Best-Effort)

Record a structured recap of the pull phase to the story's chat history. Fail-open — capture failure MUST NOT block shipping.

```bash
source scripts/hub-client.sh
source .claude/hooks/lib/hub-query.sh
MARKER_ID=$(resolve_marker_id)
hub_record_chat_history "$STORY_UUID" "pull" "<recap_content>" "$MARKER_ID"
```

The `<recap_content>` is a markdown recap following the 6-section format defined in `/session-log` Step 3:
1. **Session Summary** — what the downstream execution accomplished
2. **Key Decisions** — implementation approach choices, trade-offs made during TDD
3. **Friction Points** — test failures, code-review rejections, ship-review rejections, API errors
4. **Problems Encountered** — design challenges, unexpected complexity, constraint conflicts
5. **User Interactions** — questions asked, feedback received, corrections applied
6. **Outcomes** — ACs met (N/N), tests passing (count), stamps emitted, files created/modified

Keep under 500 words. Be specific (file names, test counts, actual errors). On API failure: log "Failed to record session recap (non-blocking)" and continue to Step 5.

- **TodoWrite:** Mark "Record session recap" as `completed`

---

## Step 5: Ship

Invoke `/ship STORYID`.

`/ship` handles git plumbing and state transition only (all quality work completed in Step 4):
- Pre-flight validation (verify gate-ship marker, story in_progress)
- `echo SHIP_COMPLETE` + commit
- Pull-rebase + push
- Transition to `done` (AFTER push succeeds)
- SHIPPED stamp + commit hash
- Context reset + `/next`

---

## Failure Handling

| Failure | Action |
|---------|--------|
| Hub API unreachable | Report with URL. STOP |
| 409 on claim (race condition) | "Story already claimed by another agent." STOP |
| Null spec (old flow) | "Run `/spec` first." STOP |
| Test failure | Analyze root cause, fix, re-run ALL suites |
| Code-review FAIL | Fix code, re-run code-review |
| Ship-review FAIL (Step 4h) | Fix critical issues, re-run ship-review |
| Git conflict on push | Handled by `/ship` — STOP on code conflicts |
| Story state changed externally (409/422 on PATCH/transition) | "Story state changed externally — re-check via API." STOP |

---

## Gate Stamps

> See CLAUDE.md §Policy 9 for the full gate stamp taxonomy (3-class: User, Agent Evidence, Gate Keeper).

During `/pull`, the agent emits:
- **Class 2 (Agent Evidence):** `RED`, `GREEN` (Step 3 TDD), `SUITES-GREEN` (Step 4a)
- **Class 3 (Gate Keeper):** `GATE-CODE` (Step 3 code-review), `DOCS`, `COMPLIANCE`, `DRIFT`, `GATE-SHIP` (Step 4h ship-review)

Upstream stamps (`PLAN`, `GATE-SPEC`, `GATE-PLAN`, `APPROVED-SPEC`) are emitted by `/spec`. Ship-finalization stamp (`SHIPPED`) is emitted by `/ship` (Step 5).
