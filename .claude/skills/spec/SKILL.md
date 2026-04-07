---
name: spec
description: >
  Run the full Upstream requirements ceremony for a story. See CLAUDE.md §Lifecycle Upstream.
---

# /spec — Upstream Requirements Ceremony

**Usage:** `/spec` | `/spec STORYID` | `/spec Story Title`

> Follow CLAUDE.md §Lifecycle Upstream for the full ceremony. This skill outlines the steps and API integration.
>
> **Argument resolution:** The argument can be a **UUID**, **STORYID** (timestamp `YYYY-MM-DD.HH-MM-SS`), or a **story title** (any other string). Pass the argument directly as a path parameter — the API resolves it server-side (UUID → timestamp → title, case-insensitive with substring fallback). Single match → resolved. Zero matches → 404. Multiple title matches → 409 `AMBIGUOUS_MATCH` with `matches` array — present candidates via AskUserQuestion. URL-encode titles containing `/`, `?`, or `#`.
>
> **Hub API:** Source `scripts/hub-client.sh` for all API operations. Provides `hub_get()`, `hub_post()`, `hub_patch()`, `hub_create_story()` with 3-retry exponential backoff. See `.claude/skills/hub-api-helpers.md` for idempotency notes. Gate stamps are emitted as side effects of `gate-review` and `test-results` endpoints — no direct stamp emission needed.
>
> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT). Each operation below is classified per-tier.

---

## Steps 1–12: Ceremony (per CLAUDE.md §Lifecycle Upstream)

1. **Setup + Early Story Creation:**

   > **IMMEDIATE ACTION: Create the specifying skeleton as your FIRST Bash commands — before exploration, before EnterPlanMode.** Infer type from title/context using the fast-path table below. Do not delay creation for detailed analysis. Type can be corrected via PATCH at Step 10a if classification changes during exploration.

   **Step 1a: Skeleton detection** (only when argument provided)

   If argument provided, look up via path-based resolution:
   ```bash
   source scripts/hub-client.sh
   hub_get "/api/v1/stories/$ARGUMENT"
   ```
   - **200** → story found. If `status == "specifying"` and `spec` is null/empty: this is an **existing skeleton** (auto-created by epic ceremony or prior `/spec` invocation). Extract UUID, title, type, epic_id. Skip STORYID generation and early creation (use existing). Log: "Detected skeleton story [STORYID] — running upstream in update mode." Proceed to Step 1d.
   - **200** with non-specifying status → story exists but is not a skeleton. Report status and STOP.
   - **404** → no existing story. Proceed to Step 1b (create new).
   - **409** → ambiguous title match. Parse `error.matches` array, present candidates via AskUserQuestion.

   **Step 1b: Fast-path type inference**

   Infer type from the title/context using keyword matching. Do NOT spend time on detailed analysis — create first, refine later.

   | Title/context keywords | Type (API value) |
   |----------------------|-----------------|
   | "fix", "bug", "broken", "defect" | `bug` |
   | governance files (CLAUDE.md, .claude/rules, skills, hooks, agents, docs/templates, docs/architecture, scripts/) | `sdlc` |
   | "refactor", "cleanup", "restructure", "rename" | `refactoring` |
   | "investigate", "spike", "research", "explore" | `investigation` |
   | "deps", "config", "routine", "update", "upgrade" | `maintenance` |
   | "data", "migration", "seed", "import", "export" | `data` |
   | **Default** (anything else) | `feature` |

   **Step 1c: Create specifying skeleton immediately**

   Execute these Bash commands as your first actions:
   1. Generate STORYID via `date -u +'%Y-%m-%d.%H-%M-%S'`
   2. Create story via API with minimal payload (spec omitted — stays in `specifying` status):
      ```bash
      source scripts/hub-client.sh
      hub_create_story '{
        "title": "<story title>",
        "type": "<feature|bug|sdlc|...>",
        "project_id": "<project UUID>",
        "epic_id": "<UUID or null>",
        "goal": "<story goal>"
      }'
      ```
      The `goal` field is **mandatory** — infer from the story title or user context if not explicitly provided. Do NOT leave goal as null. Optional: include `"context"` if available from `/discuss` context. All other fields null. **Do NOT include `spec`** — null spec keeps the story in `specifying` status.
   3. Capture `data.id` (UUID) and `data.story_id` (STORYID) from response for later PATCH in Step 10a
   4. **If API unreachable or transient error (5xx/network):** Log `⚠️ WARNING: hub_create_story failed ([detail]) — story not in DB yet — recovery: will create at Step 13 (deferred fallback)`. Set `DEFERRED_CREATION=true`. Continue ceremony
   5. **If permanent error (4xx, e.g., 422 validation):** Output `❌ STOP: hub_create_story failed ([HTTP status]: [error message]) — cannot create story`. Do NOT proceed. Fix the payload issue (missing project_id, invalid type, etc.) before retrying
   6. **Retry idempotency:** If POST fails and is retried, query `GET /api/v1/stories?status=specifying` and match by title. If found, reuse existing UUID and skip creation

   **Step 1d: Post-creation housekeeping**

   - **Assign agent upstream:** After creating or detecting the story:
     ```bash
     source scripts/hub-client.sh
     hub_assign_upstream "$STORY_UUID"
     ```
     This sets `agent_id` and `lock` on the story, providing visibility into who is spec'ing it. The agent is auto-released when the story transitions to `ready_to_pull` (Step 12c gate-review approval). **Fail-open:** if hub is unreachable, log warning and continue — no behavioral change from current flow.
   - **Clear discuss-mode marker:** Run `rm -f /tmp/claude-discuss-mode-{SESSION_ID}` via Bash. This ensures spec-review becomes mandatory for ExitPlanMode. No-op if not invoked from `/discuss`

   **Step 1e: Epic Context Loading** (conditional — only for epic stories)

   If the story has a non-null `epic_id` (from skeleton detection in Step 1a or from creation in Step 1c):

   ```bash
   source scripts/hub-client.sh
   hub_get "/api/v1/epics/$EPIC_ID"
   ```

   - **200** → Extract and cache the epic's key fields for use during spec writing:
     - `goal` — the epic-level objective
     - `acceptance_criteria` — epic-level ACs (EACs) that this story contributes to
     - `dependency_graph` — where this story fits in the epic's execution order
     - `risks` — known epic-level risks (including any `## Discovered During` sections from prior stories)
     - `edge_cases` — known epic-level edge cases (including discoveries from prior stories)
     - `spec` — full epic macro-requirements markdown
   - Display a summary to the agent (not user-facing — internal ceremony context):
     ```
     Epic Context: [epic title]
     Goal: [epic goal]
     EACs: [count] acceptance criteria
     This story's position in dependency graph: [position]
     Known risks: [count] | Known edge cases: [count]
     ```
   - **404 / API unreachable** → Log warning "Epic context unavailable — proceeding without parent context." Continue ceremony without epic context. **Fail-open** — epic context enriches the ceremony but is not required to proceed.
   - **If `epic_id` is null:** Skip this step entirely.

   **Step 1f: Sibling Story Context** (conditional — skeleton stories with epic_id only)

   > Prevents scope overlap and enables coherent cross-story design when spec'ing skeleton stories from an epic. Shows what sibling stories already cover so the agent can write a spec that complements rather than duplicates.

   **Condition:** Story was detected as a skeleton in Step 1a (existing `specifying` story with null spec) AND `epic_id` is non-null. Skip if either condition is false.

   ```bash
   source scripts/hub-client.sh
   hub_get "/api/v1/stories?epic_id=$EPIC_ID"
   ```

   - **200** → For each sibling story (excluding the current story) with a non-null `spec` field, extract: title, goal (truncated to first line/sentence), and AC names (from `acceptance_criteria` array).
   - Render a summary table:
     ```
     === SIBLING STORY CONTEXT ===
     | # | Title | Goal | ACs |
     |---|-------|------|-----|
     | 1 | [title] | [goal, 1 line] | AC1: [name], AC2: [name] |
     | 2 | ... | ... | ... |
     === END SIBLING CONTEXT ===
     ```
   - If no siblings have non-null specs: Log "No sibling stories with specs found — this is the first story being spec'd in this epic." Continue.
   - **API failure / 404** → Log warning: `⚠️ WARNING: Sibling story fetch failed — proceeding without sibling context.` Continue ceremony. **Fail-open.**

   ---

   <details>
   <summary><strong>Story Type Classification Reference (expand for detailed rules)</strong></summary>

   | Type | When to use | TDD | Code-Review |
   |------|------------|-----|-------------|
   | **Story** (feature) | New user-facing or architectural functionality. Primary deliverable is production code (`backend/src/`, `frontend/src/`) | Yes | Yes |
   | **BUG** (bug) | Fixes a defect in existing functionality. Requires `source_story_id`. Behavior was working and broke | Yes | Yes |
   | **Refactor** (refactoring) | Restructures existing production code without changing external behavior. Same inputs → same outputs. Includes dead code cleanup | Yes | Yes |
   | **SDLC** (sdlc) | Primary deliverable modifies governance directives: `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`, `.claude/agents/`, `.claude/hooks/`, `docs/templates/`, `docs/architecture/`, governance `scripts/`. Requires PHD Research AC | Exempt | Exempt |
   | **Data** (data) | Data migrations, seed data, data operations. Primary deliverable is data transformation | Exempt | Exempt |
   | **Maintenance** (maintenance) | Routine upkeep: dependency updates, config changes. No behavior change, no structural improvement | Exempt | Exempt |
   | **Investigation** (investigation) | Time-boxed research spike. Primary deliverable is a recommendation document, not shipped code. Spike code in `spike/[story-title]/` | Exempt | Exempt |

   **Disambiguation rules:**
   - The **primary deliverable** determines the type — not side-effects
   - Production code changes (`backend/src/`, `frontend/src/`) that don't touch directives → **never SDLC**
   - **Directive side-effect rule:** If a non-SDLC story also needs directive changes, create a companion SDLC story (linked via `dependencies`). Do not bundle directive changes into production stories
   - Fixes broken behavior → **BUG**, not Refactor
   - Restructures without behavior change → **Refactor**, not Story
   - Dead code cleanup → **Refactor**, not Maintenance

   **Directive side-effect detection (during Step 4 — Write Spec):**
   If during spec writing you realize the story needs changes to governance directives (`CLAUDE.md`, `.claude/rules/`, `.claude/skills/`, etc.) but the primary deliverable is production code:
   1. Do NOT include directive changes in the current story's scope
   2. Note in the Risks section: "Directive side-effect detected — companion SDLC story required"
   3. After the current story's upstream ceremony completes, run `/spec` for a companion SDLC story covering the directive changes, with `dependencies` linking to the parent story UUID

   </details>
2. **EnterPlanMode** — begin requirements ceremony. If invoked from `/discuss` (plan mode already active), skip this step and proceed directly to Explore
3. **Explore** (optional) — read source files, clarify via AskUserQuestion. **If invoked from `/discuss`:** exploration was already performed during the discussion phase. Skip this step unless new areas need investigation that were not covered during discussion. Do not re-explore files already reviewed. **If epic context was loaded in Step 1e:** review the parent epic's EACs and dependency graph as part of exploration. The story's spec MUST be coherent with the epic's macro-requirements — identify which EACs this story contributes to and how it relates to sibling stories in the dependency graph
4. **Write Spec** — write the spec using the mandatory section structure below. Type-specific rules per CLAUDE.md §Lifecycle Upstream.

   **Mandatory Spec Sections (do NOT rely on reading `docs/templates/story-template.md` — use this inline guide):**

   | # | Section | Requirement | Minimum Bar |
   |---|---------|-------------|-------------|
   | 1 | `## Context` | MANDATORY | Why this work is needed. Background, motivation, triggering problem |
   | 2 | `## Goal` | MANDATORY | 1-2 sentences. What is true when done. Specific and measurable |
   | 3 | `## Acceptance Criteria` | MANDATORY | GWT format: `### ACN: [Name]` with GIVEN/WHEN/THEN per AC |
   | 4 | `## User Journey` | **CRITICAL** | Step-by-step flow for ALL story types. UI: screens/clicks/responses. Backend/SDLC: developer/operator journey. Include alternate + error paths. "N/A" is NOT acceptable |
   | 5 | `## Wireframes` | **CRITICAL** (UI) | UI stories: ASCII wireframes per modified screen. Non-UI: `N/A — [justification per Policy 14 criteria]`. Never omit section |
   | 6 | `## Edge Cases` | **CRITICAL** — min 3 | `- [scenario] — [expected behavior]`. Cover: boundary/null/zero, error, concurrency |
   | 7 | `## Risks` | MANDATORY | `- **[Risk]:** [description + mitigation]`. Include open questions |
   | 8 | `## OO Design Decision` | MANDATORY | Present 2+ OO approaches with pros/cons, recommend one. Non-code stories: `N/A — [justification]` via AskUserQuestion. User must approve selection |
   | 9 | `## Data Model Changes` | If applicable | Entity changes in TypeScript interface format. `N/A` if none |
   | 10 | `## API Contract Changes` | If applicable | Endpoints, request/response shapes, error table. `N/A` if none |
   | 11 | `## Business Rules` | If applicable | Domain logic, calculations, validations. Omit if none |
   | 12 | `## Verification Criteria` | BUG only | Reproduction steps + runtime verification checklist |

   > **CRITICAL items block Gate Keeper spec-review (MODE 1).** Missing User Journey, fewer than 3 Edge Cases, or missing Wireframes on a UI story = automatic gate FAIL.
   >
   > `docs/templates/story-template.md` remains canonical for rendered story format. If template sections change, update BOTH the template AND this inline guide.

   **If invoked from `/discuss`:** formalize the discussion context into spec format — transform emerging concepts into GWT ACs, extract identified risks, codify scope boundaries discussed. Build on what was explored during discussion rather than starting from a blank template. **If epic context was loaded in Step 1e:** the Context section MUST reference the parent epic's goal and the specific EACs this story contributes to. Cross-reference the epic dependency graph to show where this story fits in the execution order. Incorporate known epic-level risks and edge cases relevant to this story's scope
5. **INVEST Validation** — verify story meets all 6 criteria before proceeding:
   - **I**ndependent — deliverable on its own, minimal inter-story deps
   - **N**egotiable — details refined during ceremony, not locked prematurely
   - **V**aluable — delivers measurable value (user-facing or architectural)
   - **E**stimable — clear scope enables complexity/time classification
   - **S**mall — completable in a single session (≤3h target)
   - **T**estable — ACs verifiable via Given/When/Then
   If any criterion fails: decompose into smaller stories or adjust scope. Use AskUserQuestion to confirm with user if decomposition is needed
6. **Wireframes** — per CLAUDE.md §Policy 14. UI stories: ASCII wireframes. Non-UI: N/A with justification
7. **OO Design Decision** — analyze OO implications and present structured design options for user approval:
   - **Code stories (feature, bug, refactoring) that add/modify domain entities:** Present 2+ OO approaches via AskUserQuestion. Each approach must include: description (entities, aggregates, patterns, VOs), pros, and cons. Agent marks one "(Recommended)" with reasoning. User selects an approach. Record selection in the `## OO Design Decision` section of the spec
   - **Code stories with no OO implications** (e.g., pure CSS, config changes): Present N/A justification via AskUserQuestion: "No domain entity changes — [reason]. OO Design Decision: N/A. Approve?" User must explicitly approve before proceeding
   - **Non-code stories (sdlc, data, maintenance, investigation):** Present N/A justification via AskUserQuestion: "This is a [type] story with no production code changes. OO Design Decision: N/A. Approve?" User must confirm before proceeding
   - **Single viable approach:** Agent must still present a second approach (even if inferior) to demonstrate deliberation. The second can be "Status quo / no change" if applicable
   - **User selects "Other":** Record custom direction verbatim and adapt execution plan accordingly
   - **No silent skips:** ALL story types pass through this step. The N/A path is lightweight (one AskUserQuestion) but mandatory
8. **Write Execution Plan** — write the execution plan for how the story will be implemented:
   - **Code types (feature, bug, refactoring):** Group tasks under `### AC[N]: [name]` headers with numbered RED/GREEN/REFACTOR steps beneath each AC
   - **Non-code types (SDLC, Data, etc.):** Use `### Task [N]: [description]` headers (no TDD steps)
   - Include: Goal, files to modify, scope boundaries
   - The execution plan is written in the plan file alongside the spec (see Step 9)
9. **Plan File** — write to `temp/plan-[STORYID].md` for ExitPlanMode pop-up. Header: `# Spec: [title] (STORYID)`. Include:
   - **Spec summary:** Goal, ACs, User Journey, Edge Cases, Risks, Wireframes
   - **Execution Plan:** The full execution plan from Step 8 (Goal, tasks, files to modify, scope boundaries)
   The user sees both spec AND plan before approving in ExitPlanMode
10. **PATCH Spec to Backend + Pre-Flight Check** — PATCH structured fields to DB, then verify before Gate Keeper. See Step 10a and Step 10b below.
11. **Combined Upstream Review** — invoke Gate Keeper subagent (`.claude/agents/gate-keeper.md`, MODE 1: spec-review). The combined review evaluates both spec quality AND execution plan quality in a single invocation. Fix criticals in plan mode. Structurally enforced by `spec-review-gate.sh` (blocks ExitPlanMode without `gate-spec` marker). Gate Keeper calls `POST /api/v1/stories/{UUID}/gate-review` to persist `review_spec` + `review_plan` stamps on PASS.
   ```
   Agent tool:
     subagent_type: gate-keeper
     model: "opus"
     prompt: "spec-review for story [STORYID]. Story UUID: $STORY_UUID. [Spec content + execution plan content]"
   ```
   **On VERDICT: FAIL:** Fix critical issues (spec or plan) while still in plan mode, re-PATCH (Step 10a — idempotent), then re-run spec-review in **Retry Mode** — capture the `gate-keeper-summary` JSON block from the FAIL report and include it in the retry prompt:
   ```
   Agent tool:
     subagent_type: gate-keeper
     model: "opus"
     prompt: "spec-review for story [STORYID]. Story UUID: $STORY_UUID. [Spec content + execution plan content]

   PRIOR_REVIEW
   [paste the full gate-keeper-summary JSON from the FAIL verdict, verbatim]
   END_PRIOR_REVIEW"
   ```
   Gate Keeper re-evaluates only categories with CRITICAL findings, carrying forward clean categories. See `.claude/agents/gate-keeper.md` §Retry Mode.
   **On subagent failure:** Retry once. If still fails, perform manual review using MODE 1 checklist, emit `GATE-SPEC: pass (manual)`.
   **Gate friction summary:** Recorded structurally — Gate Keeper includes `friction_summary` + `session_id` in the `POST /gate-review` payload. The backend auto-creates the `ChatHistoryEntry`. No separate `hub_record_chat_history` call needed.
12. **Approval & Routing** — dual-write, ExitPlanMode, then approve via API. **When invoked from `/batch`:** skip directly to Step 12b (batch controls its own flow).

   ### Step 10a: PATCH Spec to Backend (MANDATORY — before Gate Keeper and ExitPlanMode)

   > **Why before Gate Keeper:** Gate Keeper queries the DB to evaluate story fields. If structured fields are not PATCHed before Gate Keeper runs, it finds empty fields and FAILs. PATCH first, then Gate Keeper.
   > **Why before ExitPlanMode:** The agent has full state (UUID, plan content, extracted fields) while in plan mode. After ExitPlanMode, context may compress and local state may be lost. Persist spec content NOW while it's available.

   Extract content from the plan file (`temp/plan-[STORYID].md`) and PATCH the story:

   ```bash
   source scripts/hub-client.sh
   hub_patch "/api/v1/stories/$STORY_UUID" '{
     "spec": "<FULL plan .md file content>",
     "context": "<Context section>",
     "goal": "<Goal section>",
     "acceptance_criteria": "<GWT format — use ### ACN: headers with GIVEN/WHEN/THEN>",
     "user_journey": "<User Journey section>",
     "wireframes": "<Wireframes section content OR N/A justification — NEVER null>",
     "edge_cases": "<Edge Cases section>",
     "risks": "<Risks section>",
     "data_model_changes": "<or null>",
     "api_contract_changes": "<or null>",
     "business_rules": "<or null>",
     "verification_criteria": "<Runtime verification steps — required for BUG type, null otherwise>",
     "dependencies": ["<UUID>", ...],
     "source_story_id": "<UUID or null for BUG traceability>"
   }'
   ```

   **Field extraction rules:**
   1. **`spec` field:** The **full plan .md file content** — not a summary. DB column is `Text` (unlimited). The API validates `## Context` and `## Goal` markdown headers.
   2. **`wireframes` field (MANDATORY — never null):**
      - **UI stories:** Extract the **entire Wireframes section** including sub-headers, ASCII art, descriptions.
      - **Non-UI stories:** Set to `"N/A — [justification]"`. **Never `null`.**
   3. **All other fields:** Extract each section from the plan file content.

   **Verify response:** Check for 200 status. The PATCH transitions the story from `specifying` to `spec_complete` (spec is now non-null).

   **If PATCH fails (any error):** Output `⚠️ WARNING: spec PATCH failed ([HTTP status]: [detail]) — story DB content may be stale — recovery: hub_patch "/api/v1/stories/$STORY_UUID" '{...}'`. Set `DEFERRED_PATCH=true`. Continue to ExitPlanMode — spec content will be persisted via POST fallback in Step 13.

   **Retry:** PATCH is **idempotent** — safe to retry directly.

   ### Step 10b: Pre-Flight DB Field Check (before Gate Keeper)

   > **Why:** Gate Keeper (Opus) queries the DB to evaluate story fields. If required fields are null, Gate Keeper FAILs at CRITICAL level — wasting an expensive Opus invocation. This lightweight check catches missing fields before Gate Keeper runs.

   After the PATCH in Step 10a, fetch the story from the DB and verify required upstream fields are populated:

   ```bash
   source scripts/hub-client.sh
   STORY_JSON=$(hub_get "/api/v1/stories/$STORY_UUID")
   # Check always-required upstream fields
   for field in context goal acceptance_criteria user_journey edge_cases risks wireframes; do
     value=$(echo "$STORY_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; v=d.get('$field'); print('null' if v is None or v == '' or v == [] else 'ok')")
     if [ "$value" = "null" ]; then
       echo "❌ STOP: Field '$field' is null/empty in DB after PATCH. Fix PATCH payload and retry Step 10a before invoking Gate Keeper."
       # Do NOT proceed to Step 11
     fi
   done
   ```

   **Always-required upstream fields:** `context`, `goal`, `acceptance_criteria`, `user_journey`, `edge_cases`, `risks`, `wireframes`
   **Type-conditional fields (do NOT check):** `verification_criteria` (BUG only), `data_model_changes`, `api_contract_changes`, `business_rules` (only when applicable)

   **On failure:** STOP. List the missing fields. Re-run Step 10a with corrected payload. Do NOT invoke Gate Keeper (Step 11) with empty fields.
   **On success:** Proceed to Step 11 (Gate Keeper spec-review).

   ### Step 12b: Dual-write + ExitPlanMode

   **Dual-write (MANDATORY — before ExitPlanMode):** Write the plan to BOTH `temp/plan-[STORYID].md` (already done in Step 9) AND the **system-specified plan file** (path shown in the EnterPlanMode system message, e.g., `~/.claude/plans/<name>.md`). ExitPlanMode reads from the system-specified file — if you only write to `temp/`, the pop-up will be empty.

   **Call ExitPlanMode** — the user sees the full spec+plan in the pop-up and approves or rejects.

   **If ExitPlanMode is rejected** by the user: remain in plan mode. Use AskUserQuestion with options: "Revise spec" / "Revise plan" / "Revise both" / "Abandon story" to determine what to change. After changes are made, if spec/plan content was modified, re-PATCH the story (Step 10a — idempotent), re-run pre-flight check (Step 10b), re-run Gate Keeper spec-review (Step 11), dual-write the updated plan, then retry ExitPlanMode.

   **If ExitPlanMode is blocked** by spec-review-gate (gate-spec marker missing): run Gate Keeper spec-review first (Step 11), then retry ExitPlanMode.

   ### Step 12c: Approve Spec via API (after ExitPlanMode succeeds)

   After ExitPlanMode approval, transition the story to `ready_to_pull` and emit APPROVED-SPEC stamp via gate-review:

   ```bash
   source scripts/hub-client.sh
   hub_post "/api/v1/stories/$STORY_UUID/gate-review" '{
     "gate_type": "approval",
     "result": "pass",
     "stamp_values": {"approved_spec": "<1-2 sentence summary of what was approved>"}
   }'
   ```

   The backend validates preconditions (REVIEW_SPEC stamp, correct status), emits APPROVED_SPEC stamp, and auto-advances to `ready_to_pull`. **One API call — stamps are emitted as a side effect.**

   **If gate-review fails:** Retry once (idempotent). If persistent failure, output `⚠️ WARNING: gate-review approval failed ([detail]) — story not advanced to ready_to_pull`. STOP — do not attempt direct stamp emission (POST /gate-stamps returns 410 Gone).

   ### Post-Approval Routing

   **Present AskUserQuestion** with two structured options:
   1. **"Spec Approved + Pull"** — start downstream execution immediately
   2. **"Spec Approved + Stand By"** — user will invoke `/pull` later

   Store the routing choice (Pull or Stand By) for Step 14

---

## Step 13: Deferred Creation Fallback

> **Normal flow:** Spec content was already PATCHed to the backend in Step 10a (before Gate Keeper and ExitPlanMode) and approved via gate-review (approval) in Step 12c. **This step only executes when `DEFERRED_CREATION=true` or `DEFERRED_PATCH=true`** (API was unreachable at Step 1 or Step 10a).

**If `DEFERRED_CREATION=true`** (API was unreachable at Step 1 — no story exists yet):

Use `hub_create_story` with the full spec content:

```bash
source scripts/hub-client.sh
hub_create_story '{
  "title": "<story title>",
  "type": "<feature|bug|sdlc|maintenance|data|refactoring|investigation>",
  "project_id": "<project UUID>",
  "epic_id": "<UUID or null>",
  "spec": "<FULL plan .md file content>",
  "context": "<Context section>",
  "goal": "<Goal section>",
  "acceptance_criteria": "<GWT format>",
  "user_journey": "<User Journey section>",
  "wireframes": "<Wireframes section content OR N/A justification — NEVER null>",
  "edge_cases": "<Edge Cases section>",
  "risks": "<Risks section>",
  "dependencies": ["<UUID>", ...],
  "source_story_id": "<UUID or null>"
}'
```

Capture `data.id` (UUID) and `data.story_id` from response. **If creation fails:** Output `❌ STOP: Deferred story creation failed ([detail]) — story cannot be persisted`. Do NOT proceed to Step 14. Then call `hub_post "/api/v1/stories/$UUID/gate-review" '{\gate_type\: pproval\, 
esult\: \pass\, \stamp_values\: {pproved_spec\: \summary\}}'` to emit APPROVED_SPEC and advance.

**Retry:** POST create is **non-idempotent** — before retry, check if story was already created (match by title). If exists, skip create and use existing UUID.

**If `DEFERRED_PATCH=true`** (story exists but Step 10a PATCH failed):

Re-read `temp/plan-[STORYID].md` and PATCH using the same payload as Step 10a. **If PATCH fails:** Output `⚠️ WARNING: Deferred spec PATCH failed ([detail]) — story DB content stale — recovery: re-run hub_patch manually`. Then call `hub_post "/api/v1/stories/$STORY_UUID/gate-review" '{\gate_type\: pproval\, 
esult\: \pass\, \stamp_values\: {pproved_spec\: \summary\}}'`.

---

## Step 14: Commit + Stamps + Routing

Commit per CLAUDE.md §Git Workflow: `sdlc: create story — [title] (STORYID)`.

**UUID validation (MANDATORY before stamps):** Verify `$STORY_UUID` is non-empty. If empty: output `❌ STOP: STORY_UUID is empty — cannot emit stamps. Check Step 1/Step 13 for creation failures`. Do NOT emit stamps with an empty UUID.

**Stamp status:** All stamps for the upstream ceremony are now emitted as side effects of the `gate-review` endpoint:
- **GATE-SPEC + GATE-PLAN:** Emitted by Gate Keeper's `POST /gate-review` in Step 11
- **APPROVED-SPEC:** Emitted by `POST /gate-review` with `gate_type: approval` in Step 12c
- **PLAN, WIREFRAME:** Evidence stamps — no longer emitted via separate API calls. These are recorded as part of gate-review stamp_values.

> **Note:** `POST /api/v1/stories/{id}/gate-stamps` returns 410 Gone. All stamp emission goes through `POST /gate-review`.

**No manual stamp emission calls needed in this step.**

**Session capture (best-effort):** Record a structured recap of the spec phase to the story's chat history. Fail-open — capture failure MUST NOT block the ceremony or routing.

```bash
source scripts/hub-client.sh
source .claude/hooks/lib/hub-query.sh
MARKER_ID=$(resolve_marker_id)
hub_record_chat_history "$STORY_UUID" "spec" "<recap_content>" "$MARKER_ID"
```

The `<recap_content>` is a markdown recap following the 6-section format defined in `/session-log` Step 3:
1. **Session Summary** — what the upstream ceremony accomplished
2. **Key Decisions** — type classification, scope choices, AC formulation decisions
3. **Friction Points** — operational issues (API errors, stamp failures, gate rejections)
4. **Problems Encountered** — requirement ambiguity, constraint conflicts, decomposition needs
5. **User Interactions** — questions asked via AskUserQuestion, user routing choice
6. **Outcomes** — story created, spec PATCHed, stamps emitted, approval status

Keep under 500 words. Be specific (file names, counts, actual errors). On API failure: log "Failed to record session recap (non-blocking)" and continue to routing.

**Post-commit routing** (based on routing choice stored in Step 12):
- **"Spec Approved + Pull":** Invoke `/pull` with the story title: `Skill tool: skill: "pull", args: "[Story Title]"`
- **"Spec Approved + Stand By":** Emit completion summary and stop: `✅ [title] upstream complete (STORYID). Commit: [sha]. Status: available. Stamps: GATE-SPEC, APPROVED-SPEC, PLAN`
- **No routing stored** (legacy flow or `/batch` invocation): no post-commit action
