# Step 4: Quality & Ship Readiness — Detailed Sub-Steps

> This file contains the full sub-step procedures for `/pull` Step 4.
> **Context:** Story UUID, STORYID, Type, and Epic ID are established in the main `/pull` SKILL.md (Steps 1-3) before this reference is read. TodoWrite quality items are appended at Step 4 entry (see main file).

---

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
> **Fallback:** If template endpoint unavailable, reference `backend/src/domain/story/compliance_registry.py` for canonical key reference.

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

After all PATCH operations in Steps 4g-4g4, fetch the story from the DB and verify required downstream fields are populated:

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

**On VERDICT: PASS:** Gate Keeper calls `POST /api/v1/stories/{UUID}/gate-review` to persist `review_ship` stamp (plus DOCS, COMPLIANCE, DRIFT stamps as side effects) -> push unblocked. Proceed to Step 5.
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
AGENT_ID=$(resolve_agent_id)
hub_record_chat_history "$STORY_UUID" "pull" "<recap_content>" "$AGENT_ID"
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
