# Development System Prompt

> Four-level directive architecture: L0 (bare model), L1 (SDLC), L2 (project stack), L3 (domain).
> Enforcement rules auto-load from `.claude/rules/`. Deep-dive references in `docs/`.

---

## Session Initialization (MANDATORY)

```bash
git fetch origin && git rebase origin/main   # worktree (or: git pull --rebase origin main)
ls .claude/rules/*.md
bash scripts/board-check.sh                  # query hub API for board state
```

> **DB-first model:** The database is the source of truth for story state. Hooks query the hub API (`$HUB_URL` — see L2 project stack for project-specific variable) for story status via gate stamps on stories. The `stories/` directories contain on-demand exported files (gitignored) via Export button or `POST /api/v1/sync/db-to-file`. All state transitions and queries go through the API.
> **API-backed governance:** All governance hooks query gate stamps on stories via the hub API — no filesystem markers. Gate stamps are the single source of truth for governance state (2026-03-26.23-12-00).

> **Auto-init enforcement:** `prompt-init-gate.sh` (UserPromptSubmit hook) runs all init steps automatically on the first user prompt — no manual `/init` required. Subsequent prompts pass through instantly via session marker. See `.claude/rules/01-L1-sdlc-enforcement.md` §UserPromptSubmit Gates.

**Procedure:** Invoke `/init` skill (`.claude/skills/init/SKILL.md`) for the full bootstrap/reload procedure including response template and session conflict resolution. Also available as manual re-init when needed.

---

# LEVEL 0: Bare Model

> Identity, values, communication — identical across all projects. Details: `.claude/rules/00-L0-bare-model.md`

## Identity & Communication

> Identity, core traits, values, communication style, pushback protocol, banned phrases, progress/completion formats — all canonical in `.claude/rules/00-L0-bare-model.md` (auto-loaded). Not duplicated here.

---

# LEVEL 1: SDLC

> Portable lifecycle, policies, and governance — identical across all projects.

## Core Rules

| Rule | Summary |
|------|---------|
| **0** | **Environment:** Main=`DATA_MODE=db` (PostgreSQL mandatory). Agents=`DATA_MODE=memory` (default) or DB+`DATABASE_SCHEMA`. Story operations via hub API. See `.claude/rules/03-L2-project-stack.md` |
| **1** | **Story + Plan Required:** EVERY change needs story + approved plan. No code without approved story |
| **2** | **TDD:** RED > GREEN > REFACTOR. Exemption: Data/SDLC/Maintenance/Investigation types **that do not modify production source code files** (`backend/src/`, `frontend/src/`). If any production source code file is modified, TDD is required regardless of story type |
| **3** | **Story-Driven Workflow:** All work flows through stories (API source of truth, worktree has rendered files). See lifecycle below |
| **4** | **Git Discipline:** Direct-to-main. Pull-rebase before work + before push. Conventional commit with story ID. Reload after push |
| **5** | **Documentation Currency:** Update domain/architecture/API docs in same commit as code changes. Domain docs follow aggregate structure: `backend/src/domain/{agg}/` → `docs/domain/{agg}-domain.md` (underscores→hyphens). Must create/update when aggregate logic changes. Exempt: `services/`, `shared/`, `constants.py`, `__init__.py`. Documentation is part of "done" |
| **6** | **Clean Architecture:** No business logic in frontend. Factory pattern for entity branching. OOP + SOLID in backend (downstream). DRY (3+ lines -> extract) |
| **9** | **Rich Domain Model (Golden Rule):** Domain objects MUST co-locate data + behavior + types. Package by aggregate, not by technical layer. No anemic entities. See `.claude/rules/02-L1-code-quality.md` |
| **7** | **Directive Protection:** Protected files require user approval before modification (see below) |
| **8** | **Enforcement:** Zero-skip policy. No console.log. No `any`. API contract changes: serializer > Pydantic > frontend interface > tests (same commit) |
| **10** | **Model Tiering:** 200K context default (all sessions). Agent tool: `model: "opus"` for Gate Keeper, `model: "sonnet"` for Explore/research/read-only subagents. See `.claude/rules/03-L2-project-stack.md` §Model Tiering |

**Protected files (Rule 7):**
- Approval required: `CLAUDE.md`, `.claude/rules/*`, `docs/architecture/*`
- No approval needed: `docs/domain/*`, `docs/research/*`, story files

---

## Story-Driven Workflow

### Definition of Ready (DOR)
A story can transition to `available` status when: INVEST criteria met (Policy 6), specification complete (ACs in Given/When/Then, User Journey, Edge Cases — min 3, Wireframes for UI), dependencies identified, no blockers. Story created via `POST /api/v1/stories`.

### Definition of Done (DOD)
A story can transition to `done` status when: All ACs met, TDD followed, ALL test suites passing (zero failures/errors/skipped), compliance review passed, drift review performed, docs updated, committed + pushed + reloaded. Transition via `POST /api/v1/stories/{id}/transition`. User reviews completed stories at their own pace. Rejection creates BUG stories via API.

### Story Structure

> **DB-first:** Story state lives in the database, accessed via API. Hooks query the hub API for story status. The `stories/` directories below are gitignored local cache (on-demand export via Export button or `POST /api/v1/sync/db-to-file`).
> **API-only story manipulation:** Direct writes to `stories/(doing|done|todo|canceled|archive)/` are BLOCKED by `story-gate.sh` (Write/Edit) and `story-bash-guard.sh` (Bash). All story content changes must go through `curl -X PATCH/POST` to the hub API.

```
stories/
├── epics/      # Epic definitions (gitignored, DB is source of truth)
├── doing/      # Local cache: rendered file for story in progress (gitignored)
├── done/       # Local cache: rendered file after completion (gitignored)
└── (DB statuses: drafting → req_ready → available → claimed → in_progress → done | canceled | archived)
```

**Boundaries:** `available` = upstream complete | `done` = downstream complete (user reviews at own pace)

### Lifecycle

**Upstream — Requirements + Plan:** Invoke `/spec` skill (`.claude/skills/spec/SKILL.md`).
EnterPlanMode → spec (Context, Goal, ACs, User Journey, Edge Cases min 3, Risks; wireframes per Policy 14) → INVEST validation (Policy 6) → execution plan → combined upstream review (Gate Keeper) → **ExitPlanMode user approval** (hard gate: `spec-review-gate.sh` + `spec-ceremony-gate.sh`). Emit `APPROVED-SPEC`. Create story via API, commit, push

**Downstream — Execute:**
- Pull-rebase. Transition story to `in_progress` via `POST /api/v1/stories/{id}/transition`. **Dependency check:** no cycles (A→B→A)
- Execute: TDD per AC (RED > GREEN > REFACTOR) following the approved plan (in spec). After all ACs: **code-review** (skip for Data/SDLC)
- **Quality & Ship Readiness** (`/pull` Step 4): Final test run, **runtime AC verification** (agent verifies each AC against the running application — automated tests verify correctness, runtime verification verifies user experience), gate stamp verification, documentation, compliance + drift review, PATCH downstream content to DB, **ship-review** (Gate Keeper MODE 4). All quality work completes BEFORE commit

**Complete Story:** Invoke `/ship` skill for git plumbing + transition.
- Commit, pull-rebase, push. `push-gate.sh` verifies `review_ship` stamp via hub API before allowing push
- Transition to `done` via `POST /api/v1/stories/{id}/transition` AFTER push succeeds. Clean up stale `/tmp` session state (signal, phase, story-uuid)
- Suggest next work (Policy 4)

### Story Locking
- **Lock format:** `Lock: YYYY-MM-DDTHH:MM:SSZ by Session #XX` (stored in DB, reflected in rendered worktree file)
- No lock -> start freely. Stale (>4h) -> auto-takeover. Active -> ask user
- **Session Resume:** Invoke `/resume` skill (`.claude/skills/resume/SKILL.md`) for incoming/outgoing resume procedures. Covers: read plan/log from API, report resume state, update lock, handle stale locks.

### Shelving & Rejection
Invoke `/shelve STORYID` skill (`.claude/skills/shelve/SKILL.md`) for the full 2-path procedure:
- **Uncommitted:** reverts code, logs, releases lock, transitions to available
- **Committed:** preserves code, logs, releases lock, transitions to available with Revision Required
- **Reject:** log feedback, transition to available, release lock, add Revision Required

---

## SDLC Policies

### Policy 2: Story Filename Format
**Format:** `STORYID - [EPIC |] Type | Short Title.md`
- STORYID = UTC timestamp in `YYYY-MM-DD.HH-MM-SS` format (e.g., `2026-02-22.14-37-50`)
- Story ID format preserved; stories created via `POST /api/v1/stories` (not from template files). Session Story Renderer produces the worktree file in this format
- EPIC = uppercase, matching epic name in DB (also in `stories/epics/EPIC.md`)
- Type = `Story` | `BUG` | `Refactor` | `SDLC` | `Data` | `Maintenance` | `Investigation`
- SDLC, Data, Maintenance, and Investigation types are exempt from TDD. SDLC requires PHD Research AC
- **Type classification:** Primary deliverable determines type. SDLC = governance directive changes only (`CLAUDE.md`, `.claude/rules/`, `.claude/skills/`, `.claude/agents/`, `.claude/hooks/`, `docs/architecture/`, governance `scripts/`). Production code changes = Story/BUG/Refactor. If a non-SDLC story needs directive changes, create a companion SDLC story linked via dependencies
- Investigation spike code goes in `spike/[story-title]/` (gitignored)
- **Created timestamp:** MUST use actual system clock: `date -u +'%Y-%m-%dT%H:%M:%SZ'`. Never manually construct with `:00` seconds
- **Collision fallback:** If two stories share the same second, append suffix: `a`, `b`, `c` (e.g., `2026-02-22.14-37-50a`). Real seconds make this extremely rare

### Policy 4: Kanban Prioritization
**Stop Starting, Start Finishing.** Priority: (1) Review done stories -> (2) Finish in-progress stories -> (3) FIFO from available. Query via API (`GET /api/v1/stories?status=...`).

### Policy 5: Story Suggestion Format
After completing a story, query available stories via `GET /api/v1/queue/available` and present:
```
| Number | Epic | Name | Type | Dependencies | Complexity | Time | Ready |
```
Queue endpoint applies dependency resolution. Blocked if dependencies unmet.
Complexity = Simple/Medium/Complex. Time = Small (<1h) / Medium (1-3h) / Large (3h+).

### Policy 6: INVEST Story Decomposition
Stories and epics follow INVEST criteria:
- **I**ndependent — minimize inter-story dependencies; each story is deliverable on its own
- **N**egotiable — details refined during upstream ceremony, not locked prematurely
- **V**aluable — each story delivers measurable value (user-facing or architectural)
- **E**stimable — clear scope enables complexity/time classification (Simple/Medium/Complex)
- **S**mall — completable in a single agent session (≤3h target)
- **T**estable — ACs are verifiable via Given/When/Then

Large features → decompose into INVEST-compliant stories. Core logic first, UI last. Map dependencies.

### Policy 7: Epic Management
**When:** Related stories that benefit from coordinated planning. **File:** `stories/epics/EPICNAME.md` (short uppercase). Epics also tracked in DB (`GET /api/v1/epics`). Track Started/Completed/Lead Time timestamps.

**Epic Mandatory Sections:**
- **Always mandatory:** Goal, EACs (Given/When/Then), Stories table (with INVEST validation per row), Dependency Graph, Complexity Assessment, Risks, Edge Cases (min 3)
- **Optional:** Key Files, Developer Journey, Cross-Epic Dependencies, Notes

**EPIC Macro-Requirements Ceremony (MANDATORY before individual stories):**
EnterPlanMode → write macro-requirements (Goal, EACs, stories table with INVEST per row, dependency graph, complexity, risks, edge cases) → combined upstream review (Gate Keeper) → ExitPlanMode user approval → emit `EPIC_APPROVED: [epic-name]` → **auto-create skeleton stories** (topologically sorted by dependency, idempotency-checked, `drafting` status). Procedural details: `/spec` skill Step 11, `/batch` skill (`.claude/skills/batch/SKILL.md`). Each skeleton enters upstream via `/spec STORYID`

**Epic Story Numbering (S-Prefix Convention):**
Stories in an epic receive auto-assigned sequence prefixes on creation via `POST /api/v1/stories`. The backend assigns `S{N}` where N = count of existing non-capstone stories + 1. Creation order = dependency order (agents create skeletons in topological order during ceremony). Already-prefixed titles (matching `^S\d+\s`) are not double-prefixed (idempotent retry).

**Capstone Story (MANDATORY for all epics):**
When the epic's macro-requirements ceremony completes (all ceremony fields populated via `PATCH /api/v1/epics/{id}`), the **backend auto-creates a capstone story** as the final node in the dependency graph. No agent action required — the backend detects ceremony completion and creates the capstone automatically. Created for all epics including 0-story epics.
- **Title:** `S{N} EPICNAME | Story | Capstone` (N = non-capstone count + 1; S1 for 0-story epics)
- **Type:** `feature`
- **Dependencies:** Fan-in on ALL other stories in the epic (empty list for 0-story epics)
- **ACs:** Derived from epic EACs (each EAC becomes a verification criterion)
- **Purpose:** Cross-story integration verification via Gate Keeper MODE 5 (epic-review) before epic can be marked complete
- **Execution:** During capstone downstream, agent runs E2E tests, runtime-verifies each EAC, and invokes Gate Keeper MODE 5. On PASS, capstone ships and batch auto-completes the epic
- **Detection:** Title matches regex `^S\d+ .+ \| Story \| Capstone$` (pattern-based, not substring). `/pull` Step 4g4 and `/batch` per-story loop invoke MODE 5 for capstone stories. Structurally enforced — not behavioral-only
- **On MODE 5 FAIL — Auto-BUG creation:** Gate Keeper auto-creates BUG story skeletons per CRITICAL finding (coalesced by root cause), linked via `source_story_id` to the capstone, in the same epic. Capstone stays blocked until BUGs are fixed via `/spec` + `/pull`, then MODE 5 re-runs on retry. See `.claude/agents/gate-keeper.md` §On VERDICT: FAIL — Auto-Create Follow-up BUG Stories

### Policy 8: ISO 8601 Timestamps
All story/epic metadata: `YYYY-MM-DDTHH:MM:SSZ`. Never date-only or midnight placeholders.

### Policy 9: Gate Stamps (3-Class Taxonomy)

**Stamp authority model:** Stamps are keys to gates. Gate Keeper is the sole locksmith. Only Gate Keeper stamps unlock governance gates — agent-emitted stamps are evidence of work, not governance keys.

**Class 1 — User Stamps** (consent authority, emitted after explicit user approval):
| Stamp | When |
|-------|------|
| `APPROVED-SPEC: [summary]` | After user approves spec + plan in plan pop-up (Upstream ExitPlanMode) |
| `EPIC_APPROVED: [epic-name]` | After user approves epic macro-requirements in ExitPlanMode |

**Class 2 — Agent Evidence Stamps** (operational progress, not governance keys):
| Stamp | When |
|-------|------|
| `PLAN: [title]` | After writing plan section in spec (Upstream — before combined review) |
| `WIREFRAME: [N] screens` | After drawing wireframes |
| `RED: [path]` | After writing failing test |
| `GREEN: [count] tests passing` | After tests pass |
| `SUITES-GREEN: [count] ([breakdown])` | After ALL suites pass before commit (distinct from per-AC GREEN) |

**Class 3 — Gate Keeper Stamps** (governance keys that unlock gates, emitted only by Gate Keeper):
| Stamp | When | Gate |
|-------|------|------|
| `GATE-SPEC: [result]` | After combined upstream review (spec + plan) | Unlocks ExitPlanMode |
| `GATE-PLAN: [result]` | After combined upstream review (spec + plan) — same review sets both | Unlocks code-write |
| `GATE-CODE: [result]` | After code-review | Unlocks commit |
| `DOCS: [files]` | After Gate Keeper verifies documentation | Ship readiness |
| `COMPLIANCE: complete ([N]/[M])` | After Gate Keeper verifies compliance checklist | Ship readiness |
| `DRIFT: [detected/none]` | After Gate Keeper performs independent drift review | Ship readiness |
| `GATE-SHIP: [result]` | After ship-review (pre-push approval) | Unlocks push |
| `GATE-EPIC: [result]` | After epic-review (MODE 5 — capstone story) | Unlocks capstone ship |
| `SHIPPED: [hash]` | After Gate Keeper post-push verification | Confirms clean landing |

**Drift Signal on FAIL (informational, not a stamp):** When Gate Keeper produces VERDICT: FAIL at upstream/code gates, the report includes `DRIFT-SIGNAL: [friction|plan_drift|none] — [reason]`. This is metadata in the Gate Keeper report, not a governance key. Recorded via `POST /api/v1/stories/{id}/gate-review` (result=fail). Ship-review (MODE 4) excluded — has full 4-dimension drift review instead.

### Policy 14: Wireframes (MANDATORY)
Every plan for a story that adds or modifies UI MUST include ASCII wireframes. Show layout structure, key elements, interactive states. Non-UI stories: "N/A — no UI changes" with justification.

**UI story definition (verifiable criteria):**
- **UI story:** Adds or modifies production files in `frontend/src/` (excluding `__tests__/`), adds/modifies page routes, or adds/modifies user-facing visual components
- **Non-UI story:** Does NOT touch production files in `frontend/src/` (backend-only, SDLC, Data, infrastructure)
- N/A justification MUST reference which criterion makes the story non-UI
- At upstream (spec time), classification is based on scope from ACs — if ACs mention UI elements (pages, components, modals, buttons), it's a UI story

### Policy 15: Drift Review (4-Level System)

| Level | Trigger | Mechanism | Detail |
|-------|---------|-----------|--------|
| **L0** | Gate rejection (VERDICT: FAIL at spec/plan/code) | `DRIFT-SIGNAL` in Gate Keeper report, recorded via `POST /gate-review` | Lightweight classification: `friction`, `plan_drift`, or `none` |
| **L1** | Operational friction (hook HARD DENY, API failure, script error) | `session-error-capture.sh` → `POST /api/v1/agents/by-name/{name}/session-errors` | Error taxonomy: `hook-deny`, `api-failure`, `script-error`, `gate-fail`, `test-fail`, `env-error`. Severity: `critical`/`warning`/`info`. Fire-and-forget, fail-open |
| **L2** | Ship review (before push) | Full 4-dimension adversarial drift review in Gate Keeper MODE 4 | Directive compliance, architecture, process, rationalization detection |
| **L3** | BUG story creation | BUG Drift Classification in spec-review (MODE 1) | Source story drift type: auto-escalated to `bug` or `regression` via DriftEscalationService |

After every story, before transitioning to done: Reflect on directive deviations, document in story, suggest SDLC improvement if gap found.

### Policy 16: Directive Maintenance
Factual corrections (stale refs, typos) may use `maint:` commit prefix without a story.
**Procedure:** (1) Agent identifies correction and states the exact change to user. (2) User approves via chat. (3) Agent makes change, commits with `maint: <description>` + Co-Authored-By. (4) Agent logs the change in the commit message body (what was wrong, what was fixed).
**Scope:** Typos, dead links, stale file paths, outdated counts. NOT policy changes, NOT new rules, NOT behavior changes — those require a story.

### Policy 18: Research Log (SDLC Only)
Every SDLC story MUST produce a standalone research log file:
- **Filename:** `RESEARCH-LOG-STORYID-TITLE.md` (story ID + UPPER-KEBAB-CASE title)
- **Location:** `docs/research/logs/`
- This is in addition to appending findings to `PHD-RESEARCH-TRAJECTORY.md`
- No new gate stamp — covered by existing `DOCS:` stamp
- Does NOT apply to Data type stories

**Required sections (inline guide — backward compatible with existing logs):**

```
## 1. What Was Done
### 1.1 Problem Statement — what gap/failure motivated this change
### 1.2 Intervention Design — what was changed and why this approach
### 1.3 Implementation Details — files modified, patterns applied

## 2. Why This Matters for the Research
### 2.1 Connection to Phase 2 Findings — what prior findings informed this
### 2.2 Connection to Research Questions — which RQs does this address
### 2.3 Connection to Phase 3 — how this advances experimental analysis

## 3. What We Expect to Improve
### 3.1 Measurable Hypotheses — labeled H-XX1, H-XX2, etc.
### 3.2 Expected Impact on Evaluation Dimensions — D[N] Before/After/Expected Change table
### 3.3 Risks and Open Questions

## 4. Artifacts Produced — table of files created/modified

## 5. Relationship to Research Documents — table mapping to PHD-RESEARCH-TRAJECTORY.md, PHD-PAPER, DIRECTIVE-ARCHITECTURE-REFERENCE.md
```

**RQ reference (compact):** RQ1: portability | RQ2: ontology matching | RQ3: quality | RQ4: governance protection | RQ5: minimal ontology | RQ6: drift prevention | RQ7: parallel coordination

### Policy 19: Batch Execution Mode
**Activation:** `/batch EPICNAME`. **Skill:** `.claude/skills/batch/SKILL.md`.
**Prerequisite:** Stories in `available` or `drafting` (skeleton — `/spec` runs inline). All gates preserved (TDD, code-review, compliance, drift, gate stamps). Dependency order from epic. Per-story commits. Stop-on-failure mandatory. Resumption: `--resume STORYID`.

> Policies 10-13 (Anti-Rationalization, Done Means Done, Session Fatigue, Sequential Tasks) enforced via `.claude/rules/01-L1-sdlc-enforcement.md`

### Policy 20: Regression Coverage
Three distinct rules with explicit applicability:

1. **Boundary tests:** Required when a story modifies functions that perform arithmetic on business values (cost, duration, allocation, FTE). Must cover min, max, zero, negative, off-by-one
2. **Contract shape tests:** Required when a story adds or modifies API response fields. Must assert exact response shape (field names, types, nesting)
3. **Regression test naming:** Required for BUG stories only. Test named `test_regression_STORYID_<description>` (backend) or `test('regression STORYID: <description>')` (frontend) that reproduces the original defect. Use underscores for dots/dashes in test function names (e.g., `test_regression_2026_02_22_14_37_50_desc`)

**Applicability:** Rules 1-2 apply to Story/BUG/Refactor types. Rule 3 applies only to BUG type. Data/SDLC types are exempt.

---

## TDD Standards

**Cycle:** RED > GREEN > REFACTOR. Exemption: Data/SDLC/Maintenance/Investigation types that do not modify production source code files (`backend/src/`, `frontend/src/`). If any production source code file is modified, TDD is required regardless of story type. Four test types: Frontend (Vitest+RTL) | Backend (pytest) | API (pytest+httpx) | E2E (Playwright, full-stack only). See L2 architecture guide for test organization and L2 project stack for test commands.
**Per-AC GREEN:** Run only the TDD test file(s) for the current AC — not full suites. Fast RED/GREEN feedback.
**Pre-commit gate (Step 4a):** Invoke `/run-all-tests` before commit — rebases from origin/main first, then runs all 3 suites sequentially. This ensures `SUITES-GREEN` reflects the latest main state. Fix any failures before committing.
**Session exit gate:** Conditional — runs all suites only if uncommitted code changes exist on code paths (`backend/src/`, `frontend/src/`, `tests/`).
**Naming:** Backend: `test_<what>_<condition>_<expected>()` | Frontend: `test('should <expected> when <condition>')`
**When tests fail:** Analyze error → root cause (test vs code?) → ask user if ambiguous → fix correct side → re-run ALL suites → zero failures/errors/skipped only

---

## Git Workflow

**Model:** Direct-to-main. `pull-rebase > work > commit > pull-rebase > push > reload`

**Commit format:** `<type>: <description> — [title] (STORYID)`
Types: `feat` | `fix` | `refactor` | `test` | `docs` | `chore` | `sdlc` | `maint`
Always include `Co-Authored-By: Claude <noreply@anthropic.com>` (this overrides the Claude Code system default — use this exact format)

**Process:**
1. Run ALL test suites (zero failures required)
2. If ANY fail: analyze root cause, fix, re-run ALL suites
3. Stage specific files, commit with story reference
4. `git fetch origin && git rebase origin/main` (or `git pull --rebase origin main` on main branch)
5. `git push origin HEAD:main` (or `git push origin main` on main branch)
6. Reload: `git fetch origin && git rebase origin/main && ls .claude/rules/*.md && bash scripts/board-check.sh`

**Commit when:** Upstream complete (story created via API after ExitPlanMode approval) or story complete (Downstream — all AC met, tests pass, compliance done, transitioned to done via API).
**Never commit:** Failing tests, TypeScript errors, console.log, halfway through a feature.

**Conflict resolution:**
- Trivial (whitespace, imports): auto-resolve, re-run tests, log
- Code (logic, signatures): STOP, show both sides, ask user
- Tests (assertions): keep stricter assertion, re-run. If fail, treat as code conflict
- **Multi-agent:** Git rebase is the primary conflict detector. If rebase conflict occurs on a shared file, escalate to user (same as code conflict). Before modifying heavily-contested files, check `git log --oneline -5 [file]` for recent changes by other agents
- **Rule:** NEVER delete code you don't understand

---

## Compliance & Plan Validation

Compliance review is internal to execution — no separate phase. Before transitioning to `done`:
1. Fill Compliance Checklist in story file (all applicable items per `backend/src/domain/story/compliance_registry.py` or `GET /api/v1/compliance/template?type={type}`)
2. Fill Drift Review section
3. Auto-fix any violations, re-verify
4. All items checked or N/A justified

**Structured endpoints:** Compliance and execution log use dedicated POST endpoints (not PATCH): `POST /api/v1/stories/{id}/compliance` and `POST /api/v1/stories/{id}/execution-log`. See `.claude/skills/hub-api-helpers.md` for schemas.

**Full checklists:** See `backend/src/domain/story/compliance_registry.py` or `GET /api/v1/compliance/template?type={type}`
**Plan validation:** See Planning section in compliance registry (`backend/src/domain/story/compliance_registry.py`)

---

## Gate Keeper Subagent (Policy 17)

> **Model:** Opus (mandatory). All Gate Keeper invocations MUST specify `model: "opus"`. See Rule 10.

| Gate | Mode | When | Applies To |
|------|------|------|-----------|
| Upstream Review | `spec-review` | Upstream — inside plan mode, before ExitPlanMode. Evaluates spec + plan together | ALL types |
| Code Review | `code-review` | Downstream (after GREEN) | Story/BUG/Refactor only |
| Ship Review | `ship-review` | Downstream — after commit, before push (independent DOD/drift verification) | ALL types |
| Epic Review | `epic-review` | Downstream — capstone story, cross-story integration verification (5 dimensions) | Capstone stories (all epics) |

- Combined upstream review sets BOTH `gate-spec` and `gate-plan` markers in one invocation
- Critical issues are **blocking** at each gate
- E2E happy-day required for full-stack stories
- DB schema verification when entities change
- **Code-review (MODE 3) hardened:** BANNED patterns have concrete FAIL/PASS code examples, SOLID principles have severity + verification heuristics, clean code items have mechanical verification instructions. All items classified as CRITICAL (blocks) or WARNING (logged). Progressive DOD check warns on empty execution_log/compliance
- **Ship-review (MODE 4) hardened:** DOD fields (execution_log, compliance, drift_review, ACs met) are all CRITICAL — blocks ship if empty/incomplete
- Ship-review includes independent drift review (4 dimensions: directive compliance, architecture patterns, process compliance, agent rationalization detection)
- If subagent fails: retry once, then manual review. **Manual review procedure:** Agent performs self-review using the gate's checklist from `.claude/agents/gate-keeper.md` (combined upstream review checklist at upstream gate, code-review at code gate, ship-review at ship gate). Document each item as pass/fail/N/A in the story's Execution Log. Append `(manual)` to the GATE gate stamp (e.g., `GATE-PLAN: pass (manual)`). Never skip a gate entirely

> Gate Keeper definition: `.claude/agents/gate-keeper.md`

---

## Documentation Requirements

**Three tiers of documentation:**

| Tier | Location | Approval | Update When |
|------|----------|----------|-------------|
| L3 Domain | `docs/domain/` | Not needed | Business rules, entity relationships, validation logic changes |
| L2 Architecture | `docs/architecture/` | Required | New patterns, tech decisions, API changes |
| L0+L1 Process | `CLAUDE.md`, `.claude/rules/` | Required | Workflow or policy changes |

**Update documentation in the same commit as code changes.** "I'll update docs later" = never happens.

---

# Quick Reference

## Gotchas & Patterns

- **Write tool requires fresh Read** — must read a file before writing to it
- **`temp/` for agent scratch files** — never use `/tmp`. The `temp/` dir is gitignored. (Hook infrastructure uses `/tmp` for ephemeral session state — this prohibition applies to agent-created files only)

## Directory Structure

```
CLAUDE.md                    # This file (L0+L1 portable)
.claude/rules/               # Auto-loaded: 00-L0, 01-L1, 02-L1, 03-L2, 04-L2, 05-L3
.claude/hooks/               # PreToolUse, PostToolUse, Stop hooks
.claude/skills/batch/        # /batch — epic batch execution
.claude/agents/gate-keeper.md   # Opus Gate Keeper (4 gates)
docs/architecture/           # L2: code-quality, guides, ui-standards, gate-architecture
docs/domain/                 # L3: overview, story, epic, agent, etc.
docs/research/               # Research logs
scripts/board-check.sh       # API-based board state check (bootstrap/reload)
stories/epics/               # Epic definitions (git-tracked, also in DB)
stories/{doing,done,todo}/   # Local cache — gitignored (DB is source of truth)
spike/                       # Investigation spike code — spike/[story-title]/ (.gitignored)
temp/                        # Scratch files (.gitignored)
```
