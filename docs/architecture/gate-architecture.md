# Gate Architecture Reference — DOR/DOD Analysis

> Maps all SDLC structural gates to lifecycle stages with Definition of Ready (DOR) and Definition of Done (DOD) conditions, enforcement strength, and gap analysis.
>
> **Last verified:** 2026-03-08
> **Source story:** 2026-02-24.21-56-05 (SDLC | Gate Architecture DOR/DOD Analysis)
> **Review trigger:** Update this document when hooks in `.claude/hooks/` change

---

## Lifecycle Overview

4 lifecycle steps, 17 logical gates (G0-G15a), 12 hook scripts. Stories flow: todo → doing → done (lifecycle shorthand — DB statuses are source of truth; hooks query the hub API, not the filesystem. See CLAUDE.md §Story Structure).

**Four enforcement layers** compose as defense-in-depth:

| Layer | Type | Always Active? | Bypassable? | Strength Alone |
|-------|------|---------------|-------------|---------------|
| **Rules** (4 auto-loaded `.claude/rules/`) | Behavioral — always in agent context | Yes | Yes — agent can ignore | Low |
| **Skills** (`/ship`, `/spec`, `/batch`, `/next`) | Codified workflow — directed by rules | No — must be invoked | Yes — agent can skip | Medium |
| **Hooks** (7 scripts, PreToolUse/PostToolUse/Stop) | Mechanical — deny/allow | Yes — fires on every tool use | No — physical block | High |
| **Gate Keeper** (4 modes: spec/plan/code/ship) | Subagent — deep semantic analysis | No — must be invoked | Depends on hook backing | High (when hook-backed) |

---

## Gate Matrix (15 Gates)

### G0: Session Bootstrap

| Aspect | Detail |
|--------|--------|
| **Stage** | Pre-work — every session start and post-push |
| **DOR** | Worktree synced, directives loaded, board state known |
| **Gate** | 3-step sequence: (1) git pull/rebase, (2) ls .claude/rules/, (3) board state via API (`board-check.sh`) |
| **Enforcement** | `unified-reload-gate.sh` (Mode A) — **Advisory** (additionalContext, not deny) |
| **Marker** | `/tmp/claude-session-init-{SID}` |
| **Strength** | WEAK — advisory only, agent can ignore and proceed |

### G1: Upstream Entry (Requirements Start)

| Aspect | Detail |
|--------|--------|
| **Stage** | Upstream — entering requirements ceremony |
| **DOR** | EPIC approved (if part of EPIC). No conflicting story in doing/ |
| **Gate** | EnterPlanMode called. Plan mode enforced by Claude Code runtime |
| **Enforcement** | **Claude Code runtime** — plan mode prevents Write/Edit to non-plan files |
| **Marker** | Claude Code plan mode state (internal) |
| **Strength** | STRONG — structural, agent physically cannot edit production files in plan mode |

### G2: Spec-Review (Upstream Exit)

| Aspect | Detail |
|--------|--------|
| **Stage** | Upstream — after spec written, before ExitPlanMode |
| **DOR** | ACs in G/W/T, User Journey, Edge Cases (min 3), Wireframes (UI), Risks |
| **Gate** | spec-review passed with no critical issues |
| **Enforcement** | `spec-review-gate.sh` — **HARD DENY** on ExitPlanMode unless `gate-spec` marker exists. Escape hatch after 3 denials (advisory warning) |
| **Marker** | `/tmp/claude-gate-spec-{SID}` + `/tmp/claude-spec-gate-attempts-{SID}` (counter) |
| **Strength** | STRONG — mechanical, agent physically cannot ExitPlanMode without spec-review pass (escape hatch at 3 attempts for deadlock prevention) |

### G3: User Approval (Upstream → todo/)

| Aspect | Detail |
|--------|--------|
| **Stage** | Upstream exit — user approves spec in pop-up |
| **DOR** | Spec summary in plan file. Wireframes status line present |
| **Gate** | User clicks approve in ExitPlanMode pop-up |
| **Enforcement** | **Claude Code runtime** — ExitPlanMode requires user interaction |
| **Marker** | Gate stamp `APPROVED-SPEC` |
| **Strength** | STRONG — structural, user physically must approve |

### G4: Story Lock (todo/ → doing/)

| Aspect | Detail |
|--------|--------|
| **Stage** | Downstream entry — story picked up for execution |
| **DOR** | Story in available status (upstream complete). Dependencies in done status (via API). No active lock (or stale >4h) |
| **Gate** | No story currently in doing/ with active lock. Dependencies met |
| **Enforcement** | `story-gate.sh` — detects story transition via API story_id comparison; clears governance markers (gate-plan, approved-spec, gate-spec, spec-gate-attempts) when in_progress story changes. Code edits always clear tests-passed + gate-code. **Behavioral** for dependency check |
| **Marker** | On story transition (API story_id change): clears gate-plan, approved-spec, gate-spec, spec-gate-attempts. On code edit: clears tests-passed, gate-code. Preserves gate-plan, gate-spec on code edits |
| **Strength** | MEDIUM — story-gate enforces "no code without story in doing/" (strong), but dependency verification is behavioral |

### G5: Plan-Review (Plan → Execution)

| Aspect | Detail |
|--------|--------|
| **Stage** | Downstream — after execution plan written, before any code |
| **DOR** | Execution plan in story file with TDD-ordered tasks |
| **Gate** | Two-gate check: (1) plan-review passed → marker, (2) approved-spec → marker or cross-session fallback |
| **Enforcement** | `plan-review-gate.sh` — **HARD DENY** on Write/Edit to `backend/src/`, `frontend/src/`, `tests/`. Gate 1: gate-plan marker. Gate 2: approved-spec marker OR story file has `## Goal` + `## Acceptance Criteria` headers (cross-session fallback with advisory) |
| **Marker** | `/tmp/claude-gate-plan-{SID}` + `/tmp/claude-approved-spec-{SID}` |
| **Strength** | STRONG (same-session: both markers) / MEDIUM (cross-session: structural fallback with advisory) |

### G6: No-Story Guard (Continuous)

| Aspect | Detail |
|--------|--------|
| **Stage** | Continuous — always active during execution |
| **Gate** | At least one story in_progress (hub API query) |
| **Enforcement** | `story-gate.sh` — **HARD DENY** on Write/Edit to production paths when no story in_progress (hub API) |
| **Marker** | File existence check (no marker file) |
| **Strength** | STRONG — mechanical, no code without an active story |

### G7: DB Command Guard (Continuous — Agent Worktrees)

| Aspect | Detail |
|--------|--------|
| **Stage** | Continuous — always active in agent worktrees |
| **Gate** | Bash command does not contain forbidden DB commands (alembic, docker-compose, psql, etc.) |
| **Enforcement** | `forbidden-command-blocker.sh` — **HARD DENY** |
| **Marker** | None (stateless) |
| **Strength** | STRONG — mechanical, DB commands physically blocked in agent context |

### G8: Stale Marker Invalidation (Continuous)

| Aspect | Detail |
|--------|--------|
| **Stage** | Continuous — every code edit during execution |
| **Gate** | Any Write/Edit to production code |
| **Enforcement** | `story-gate.sh` — automatically clears `tests-passed` and `gate-code` markers on every code edit |
| **Marker** | Clears `/tmp/claude-tests-passed-{SID}` and `/tmp/claude-gate-code-{SID}` |
| **Strength** | STRONG — mechanical, ensures every code change requires fresh test run and code-review |

### G9: Code-Review (Execution → Commit)

| Aspect | Detail |
|--------|--------|
| **Stage** | Downstream — after all ACs GREEN, before commit |
| **DOD** | All ACs met, all tests passing, code-review passed (Story/BUG/Refactor only) |
| **Gate** | gate-code marker exists (OR story type is SDLC/Data = exempt) |
| **Enforcement** | `pre-commit-test-gate.sh` Gate 2 — **HARD DENY** on `git commit` |
| **Marker** | `/tmp/claude-gate-code-{SID}` |
| **Strength** | STRONG — mechanical, agent physically cannot commit without code-review (non-exempt types) |

### G10: Test Suite (Execution → Commit)

| Aspect | Detail |
|--------|--------|
| **Stage** | Downstream — before every commit |
| **DOD** | ALL test suites passing, zero failures/errors/skipped |
| **Gate** | tests-passed marker exists |
| **Enforcement** | `pre-commit-test-gate.sh` Gate 1 — **HARD DENY** on `git commit` |
| **Marker** | `/tmp/claude-tests-passed-{SID}` |
| **Strength** | STRONG — mechanical, agent physically cannot commit without green tests |

### G11: Directive Freshness (Before Push)

| Aspect | Detail |
|--------|--------|
| **Stage** | Downstream — before push |
| **DOD** | Local directives match origin/main |
| **Gate** | Git object hashes for CLAUDE.md and .claude/rules/ match origin |
| **Enforcement** | `directive-freshness-check.sh` — **Blocking** (permissionDecision: deny) |
| **Marker** | None (stateless git comparison) |
| **Strength** | STRONG — blocking (permissionDecision: deny when stale, fail-open when origin unreachable) |

### G12: Post-Push Reload (After Push)

| Aspect | Detail |
|--------|--------|
| **Stage** | After every push — re-sync |
| **DOD** | Directives reloaded, board state refreshed |
| **Gate** | 3-step reload: pull, directives, board check (same as G0) |
| **Enforcement** | `unified-reload-gate.sh` (Mode B) — **Advisory** |
| **Marker** | `/tmp/claude-post-push-pending-{SID}` |
| **Strength** | WEAK — advisory only, same weakness as G0 |

### G13: Session Stop (Session End)

| Aspect | Detail |
|--------|--------|
| **Stage** | Session termination |
| **DOD** | All test suites green |
| **Gate** | `run-tests.sh` exits 0 |
| **Enforcement** | `stop-test-gate.sh` — **HARD DENY** on Stop event |
| **Marker** | None (runs tests live) |
| **Strength** | STRONG (when run-tests.sh exists) / WEAK (graceful fallback if missing) |

### G14: Governance Pushback (Continuous)

| Aspect | Detail |
|--------|--------|
| **Stage** | Continuous — every design decision |
| **DOD** | No BANNED pattern violations. Overrides logged |
| **Gate** | Three tiers: T1 (advisory), T2 (AskUserQuestion + log), T3 (refuse) |
| **Enforcement** | **Behavioral** (T1/T2) + **Gate Keeper backstop** (T3 caught by code-review) |
| **Marker** | Override log entry in `docs/governance/override-log.md` (T2). Session counter (T2) |
| **Strength** | T1: WEAK. T2: MEDIUM (logged but compliant). T3: MEDIUM (behavioral refuse + Gate Keeper backstop) |

### G15: Ship DOD (Ship-Review → Push)

| Aspect | Detail |
|--------|--------|
| **Stage** | Downstream — verified by Gate Keeper ship-review, enforced at push |
| **DOD** | Story in done status (API), drift review filled, compliance checklist has checked items, docs updated, prior gate stamps present |
| **Gate** | Gate Keeper ship-review (MODE 4) independently verifies all DOD conditions. `push-gate.sh` consumes `gate-ship` marker |
| **Enforcement** | Gate Keeper ship-review + `push-gate.sh` — **HARD DENY** on `git push` when hub API reports in_progress story and `gate-ship` marker absent. Fail-open if API unreachable |
| **Marker** | `review_ship` stamp in DB (set by Gate Keeper's direct `POST /gate-review` call on ship-review PASS) |
| **Strength** | STRONG — mechanical (push-gate hook) + independent semantic verification (Gate Keeper). Replaced pre-commit G3 (2026-03-07.18-50-16) |

### G15a: Ship-Review (Pre-Push Gate Keeper Verification)

| Aspect | Detail |
|--------|--------|
| **Stage** | Downstream — after commit, before push. Independent verification of ship readiness |
| **DOD** | DOD verified, docs verified, compliance complete, prior gate stamps present, drift review passed (4 dimensions) |
| **Gate** | Gate Keeper ship-review mode (MODE 4). Checklist: DOD Verification, Documentation Verification, Compliance Verification, Prior Gate Stamp Verification, Independent Drift Review |
| **Enforcement** | Gate Keeper subagent (invoked by `/ship` skill). Gate Keeper calls `POST /gate-review` to persist `review_ship` stamp on ship-review PASS. `push-gate.sh` **HARD DENY** on push without `review_ship` stamp when in_progress story exists (API-based detection) |
| **Marker** | `review_ship` stamp in DB — set by Gate Keeper's direct `POST /gate-review` call on ship-review PASS |
| **Strength** | STRONG — Hook deny (`push-gate.sh`) + Gate Keeper deep semantic verification. Push physically blocked without ship-review PASS |

---

## Strength Assessment Summary

| Strength | Count | Gates |
|----------|-------|-------|
| STRONG (Mechanical deny) | 12 | G1, G2, G3, G5, G6, G7, G8, G9, G10, G11, G15, G15a |
| MEDIUM (Behavioral + structural backstop) | 2 | G4, G14 |
| WEAK (Advisory only) | 3 | G0, G12, G13 (fallback) |

---

## API-Backed Governance State

> **Migration (2026-03-26.23-12-00):** Governance state moved from filesystem markers (`/tmp/claude-*`) to gate stamps stored in the database. Hooks query the hub API via `hub-query.sh` (5-second cache TTL). See CLAUDE.md §Policy 9 for the full stamp taxonomy.

**Stamp producers:**

| Hook | Stamps Produced | Trigger |
|------|----------------|---------|
| Gate Keeper direct `POST /gate-review` | `review_spec`, `review_plan`, `review_code`, `review_ship` | Gate Keeper VERDICT: PASS |
| `test-emitter.sh` (PostToolUse Bash) | `suites_green` | All 3 test suites pass (per-suite tracking in `/tmp`) |

**Stamp consumers (PreToolUse gates):**

| Hook | Stamps Checked | Effect |
|------|---------------|--------|
| `spec-review-gate.sh` (ExitPlanMode) | `review_spec` | HARD DENY ExitPlanMode without spec-review pass |
| `spec-ceremony-gate.sh` (Bash POST) | `review_spec` | HARD DENY story creation without spec ceremony |
| `commit-gate.sh` (Bash git commit) | `suites_green`, `review_code` | G1: suites_green + staleness check. G2: review_code (SDLC/Data exempt) |
| `push-gate.sh` (Bash git push) | `review_ship` | HARD DENY push without ship-review when in_progress story exists |

**Remaining `/tmp` files (session-local ephemeral state — NOT governance):**

| File | Purpose | Producer | Consumer |
|------|---------|----------|----------|
| `claude-active-story-uuid-{SID}` | Track current story UUID | `todo-capture.sh` | `session-heartbeat.sh` |
| `claude-last-signal-{SID}` | Carry-forward signal for heartbeat | `session-heartbeat.sh` | `session-heartbeat.sh`, `agent-keepalive.sh` |
| `claude-last-phase-{SID}` | Carry-forward phase for heartbeat | `session-heartbeat.sh` | `session-heartbeat.sh`, `agent-keepalive.sh` |
| `claude-todo-progress-{SID}` | Todo completed/total counts | `todo-capture.sh` | `session-heartbeat.sh` |
| `claude-test-suites-{SID}/` | Per-suite pass tracking | `test-emitter.sh` | `test-emitter.sh` (all-3 detection) |
| `claude-heartbeat-last-{SID}` | 30-second throttle | `session-heartbeat.sh` | `session-heartbeat.sh` |

These files are cleaned up by `/ship` Step 5 (post-ship cleanup) and `stop-keepalive-cleanup.sh` (session exit)

---

## DOR/DOD Per Lifecycle Step

### Step 0: Session Bootstrap

| | Condition | Enforced? | How |
|--|-----------|-----------|-----|
| **DOR** | New session started | STRONG | Claude Code runtime |
| **DOD-1** | git pull/rebase executed | BEHAVIORAL | `unified-reload-gate.sh` (Mode A) — advisory only |
| **DOD-2** | `.claude/rules/*.md` loaded | BEHAVIORAL | `unified-reload-gate.sh` (Mode A) — advisory only |
| **DOD-3** | Board state checked via API (`board-check.sh`) | BEHAVIORAL | `unified-reload-gate.sh` (Mode A) — advisory only |

**Honest assessment:** WEAK. All 3 DOD conditions are advisory. Agent can skip bootstrap entirely.

### Step 1: Upstream (Requirements)

| | Condition | Enforced? | How |
|--|-----------|-----------|-----|
| **DOR-1** | Session bootstrap complete | BEHAVIORAL | Advisory (G0 is weak) |
| **DOR-2** | EPIC approved (if part of EPIC) | STRONG (API) + Gate Keeper | Gate Keeper epic-specific spec-review checklist validates epic completeness (S7). API endpoint `POST /api/v1/stories` returns 422 when epic has ≥2 stories and no `acceptance_criteria` (S9). `epic-ceremony-gate.sh` provides advisory defense-in-depth |
| **DOR-3** | EnterPlanMode called | STRONG | Claude Code runtime |
| **DOD-1** | Spec follows story template | BEHAVIORAL | No hook validates story content |
| **DOD-2** | spec-review passed (no criticals) | STRONG | Gate Keeper calls `POST /gate-review` to persist `review_spec` stamp on pass. `spec-review-gate.sh` denies ExitPlanMode without stamp (escape hatch at 3 attempts) |
| **DOD-3** | Spec summary written to plan file | BEHAVIORAL | No hook checks plan file content |
| **DOD-4** | User approves in ExitPlanMode pop-up | STRONG | Claude Code runtime |
| **DOD-5** | APPROVED-SPEC stamp emitted | BEHAVIORAL + Marker | `approved-spec-tracker.sh` sets `/tmp/claude-approved-spec-{SID}` on spec commit. Consumer: S5 |
| **DOD-6** | Story created via API (`POST /api/v1/stories`) | BEHAVIORAL | Commit hook only checks tests, not spec presence |

**Honest assessment:** STRONG. Plan mode (DOR-3), user approval (DOD-4), and spec-review (DOD-2) are all mechanically enforced. `spec-review-gate.sh` blocks ExitPlanMode without `gate-spec` marker (escape hatch at 3 attempts for deadlock prevention).

### Step 2: Downstream — Execution Plan

| | Condition | Enforced? | How |
|--|-----------|-----------|-----|
| **DOR-1** | Story in_progress (API) | STRONG | `story-gate.sh` — hard deny without story |
| **DOR-2** | Upstream complete (APPROVED-SPEC) | STRONG / MEDIUM | `plan-review-gate.sh` Gate 2: checks `approved-spec` marker (STRONG same-session). Cross-session fallback: greps story file for `## Goal` + `## Acceptance Criteria` headers (MEDIUM — structural, not semantic) |
| **DOR-3** | Dependencies satisfied | BEHAVIORAL | No hook checks dependency metadata |
| **DOR-4** | Lock set, no conflicting session | BEHAVIORAL | No hook validates lock metadata |
| **DOR-5** | Markers cleared (fresh cycle) | STRONG | `story-gate.sh` on story transition: clears gate-plan, approved-spec, gate-spec, spec-gate-attempts. Code edits: clear tests-passed, gate-code |
| **DOD-1** | Execution plan written | BEHAVIORAL | No hook inspects story for plan content |
| **DOD-2** | Plan follows TDD order | BEHAVIORAL | Gate Keeper checks this |
| **DOD-3** | plan-review passed (no criticals) | STRONG | `plan-review-gate.sh` gates on marker |

**Honest assessment:** STRONG EXIT, STRONG ENTRY (same-session) / MEDIUM ENTRY (cross-session). plan-review-gate.sh blocks code until Gate Keeper approves (Gate 1) AND upstream is verified (Gate 2: approved-spec marker or structural fallback).

### Step 3: Downstream — Code (TDD per AC)

| | Condition | Enforced? | How |
|--|-----------|-----------|-----|
| **DOR-1** | plan-review marker exists | STRONG | `plan-review-gate.sh` — hard deny |
| **DOR-2** | Story in_progress (API) | STRONG | `story-gate.sh` — hard deny |
| **DOR-3** | Memory mode active | STRONG | `forbidden-command-blocker.sh` — hard deny |
| **Continuous** | Every code edit clears test+code-review markers | STRONG | `story-gate.sh` auto-clears |
| **DOD-1** | All ACs implemented | BEHAVIORAL | No hook verifies AC coverage |
| **DOD-2** | code-review passed (Story/BUG/Refactor) | STRONG | `pre-commit-test-gate.sh` gates on marker |
| **DOD-3** | All test suites green | STRONG | `pre-commit-test-gate.sh` gates on marker |

**Honest assessment:** STRONG. Both DOR and DOD mechanically enforced. Strongest step in lifecycle.

### Step 4: Downstream — Ship (Compliance + Commit + Push)

| | Condition | Enforced? | How |
|--|-----------|-----------|-----|
| **DOR-1** | Tests + code-review passed | STRONG | `pre-commit-test-gate.sh` markers |
| **DOR-2** | All ACs met | BEHAVIORAL | `/ship` skill verifies but no hook |
| **DOD-1** | Compliance checklist filled | STRONG | Gate Keeper ship-review verifies, `push-gate.sh` blocks push without `gate-ship` marker |
| **DOD-2** | Drift review filled | STRONG | Gate Keeper ship-review verifies (independent 4-dimension review), `push-gate.sh` blocks push |
| **DOD-3** | Documentation updated | STRONG | Gate Keeper ship-review verifies docs, `push-gate.sh` blocks push without ship-review PASS |
| **DOD-4** | Story transitioned to done via API | BEHAVIORAL | `/ship` skill transitions before commit. No hook enforces ordering |
| **DOD-5** | All gate stamps emitted | STRONG | Gate Keeper ship-review verifies prior gate stamps, `push-gate.sh` blocks push |
| **DOD-6** | Commit format correct | BEHAVIORAL | No hook validates commit message format |
| **DOD-7** | Post-push reload complete | BEHAVIORAL | Advisory — `unified-reload-gate.sh` (Mode B) |
| **DOD-8** | Ship-review passed | STRONG | `push-gate.sh` — HARD DENY push without `gate-ship` marker during ship workflow |

**Honest assessment:** STRONG. 5 of 8 DOD conditions (compliance, drift, docs, tokens, ship-review) are mechanically enforced by Gate Keeper ship-review + `push-gate.sh` (gate-ship marker at push). Replaced pre-commit G3 with deeper independent verification at push time (2026-03-07.18-50-16).

---

## Lifecycle Flow Diagram

```
SESSION START
    |
    v
+-----------------------------+
| G0: Session Bootstrap       | Advisory -- pull, directives, board
| DOR: Worktree synced        |
+---------+-------------------+
          |
          v
+-----------------------------+
| G1: Upstream Entry           | STRONG -- EnterPlanMode (runtime)
| DOR: EPIC approved (if any)  | STRONG (API) + GK epic checklist (S7+S9)
| G2: Spec-Review             | MEDIUM -- behavioral, Gate Keeper catches
| DOR: ACs+Journey+Edge+Wire  |
| G3: User Approval           | STRONG -- ExitPlanMode pop-up
| DOD: APPROVED-SPEC emitted  |
+---------+-------------------+
          |  commit spec -> todo/
          v
+-----------------------------+
| G4: Story Lock               | MEDIUM -- move to doing/
| DOR: Deps satisfied, no lock|
| G6: No-Story Guard          | STRONG -- story-gate.sh (deny)
+---------+-------------------+
          |
          v
+-----------------------------+
| G5: Plan-Review              | STRONG -- plan-review-gate.sh (deny)
| DOR: Plan written, TDD order|
| DOD: GATE-PLAN pass       |
+---------+-------------------+
          |  marker set -> code allowed
          v
+-----------------------------+
| EXECUTION (TDD per AC)       |
| G7: DB Command Guard        | STRONG -- forbidden-command-blocker (deny, agent worktrees)
| G8: Stale Invalidation      | STRONG -- auto-clears markers on edit
| G14: Governance Pushback    | MEDIUM -- T1/T2/T3 behavioral tiers
| Per-AC: RED -> GREEN        |
+---------+-------------------+
          |  all ACs done
          v
+-----------------------------+
| G9: Code-Review              | STRONG -- pre-commit-test-gate (deny)
| G10: Test Suite              | STRONG -- pre-commit-test-gate (deny)
| DOD: Tests green, review pass|
+---------+-------------------+
          |  move to done/, commit
          v
+-----------------------------+
| G15a: Ship-Review            | STRONG -- Gate Keeper MODE 4 + push-gate (deny)
| G11: Directive Freshness     | STRONG -- blocking before push (deny)
| DOD: Ship-review pass,       |
|      directives fresh        |
+---------+-------------------+
          |  push
          v
+-----------------------------+
| G12: Post-Push Reload        | WEAK -- advisory after push
| G13: Session Stop            | STRONG -- stop-test-gate (deny)
| DOD: Shipped, reloaded       |
+-----------------------------+
```

---

## Gates x Steps Cross-Reference Matrix

| Gate | Type | Enforcement | Step 0 | Step 1 | Step 2 | Step 3 | Step 4 |
|------|------|------------|--------|--------|--------|--------|--------|
| **G0** | Hook (advisory) | `unified-reload-gate` (Mode A) | **DOD** | --- | --- | --- | --- |
| **G1** | Runtime (deny) | Claude Code plan mode | --- | **DOR** STRONG | --- | --- | --- |
| **G2** | Hook (deny)+Gate Keeper | `spec-review-gate` + Gate Keeper | --- | **DOD** STRONG | --- | --- | --- |
| **G3** | Runtime (deny) | Claude Code ExitPlanMode | --- | **DOD** STRONG | --- | --- | --- |
| **G4** | Behavioral+Hook(clear) | `story-gate` marker clear | --- | --- | **DOR** MEDIUM | --- | --- |
| **G5** | Hook (deny) | `plan-review-gate` | --- | --- | **DOD** STRONG | **DOR** STRONG | --- |
| **G6** | Hook (deny) | `story-gate` | --- | --- | **C** STRONG | **C** STRONG | **C** STRONG |
| **G7** | Hook (deny) | `forbidden-command` | --- | --- | --- | **C** STRONG | **C** STRONG |
| **G8** | Hook (auto-clear) | `story-gate` | --- | --- | --- | **C** STRONG | --- |
| **G9** | Hook (deny) | `pre-commit-test` + Gate Keeper | --- | --- | --- | **DOD** STRONG | **DOR** STRONG |
| **G10** | Hook (deny) | `pre-commit-test` + `stop-test` | --- | --- | --- | **DOD** STRONG | **DOR** STRONG |
| **G11** | Hook (deny) | `directive-freshness` | --- | --- | --- | --- | **DOD** STRONG |
| **G12** | Hook (advisory) | `unified-reload-gate` (Mode B) + `post-push-reload` | --- | --- | --- | --- | **DOD** WEAK |
| **G13** | Hook (deny) | `stop-test-gate` | **DOD*** | --- | --- | --- | **DOD*** |
| **G14** | Behavioral+Gate Keeper | 3-tier protocol | --- | --- | --- | **C** MED-HIGH | **C** MED-HIGH |
| **G15** | Hook (deny)+Gate Keeper | `push-gate` + Gate Keeper ship-review | --- | --- | --- | --- | **DOD** STRONG |
| **G15a** | Hook (deny)+Gate Keeper | `push-gate` + Gate Keeper ship-review | --- | --- | --- | --- | **DOD** STRONG |

*G13 fires at session end (not story-scoped).

---

## Compositional Enforcement Model

### Composition Strength Scale

| Rating | Definition | Failure Mode |
|--------|-----------|-------------|
| STRONG | Hook deny (mechanical gate) | Agent physically blocked |
| STRONG- | Hook deny + Gate Keeper | Agent physically blocked + deep quality check |
| MED-HIGH | Rule + Skill + Gate Keeper (no hook) | All three must fail simultaneously |
| MEDIUM | Rule + Skill (no hook, no Gate Keeper) | Agent ignores rule AND skips skill |
| MED-LOW | Rule + Hook(advisory) | Agent ignores rule and dismisses advisory |
| WEAK | Rule only | Agent ignores directive |

### Compositional Heat Map

```
             Step 0    Step 1    Step 2    Step 3    Step 4
           Bootstrap  Upstream  Exec Plan   Code    Ship/Done
          +----------+---------+---------+---------+---------+
DOR       |          | STRONG  | STRONG  | STRONG  | STRONG  |
          |  N/A     | (G1)    | (G4+G5) | (G5)    | (G9+10) |
          +----------+---------+---------+---------+---------+
Work      | 3-step   | Spec    | Exec    | TDD     | Comply  |
          | init     | write   | plan    | per AC  | + ship  |
          +----------+---------+---------+---------+---------+
DOD       | MED-LOW  | STRONG  | STRONG  | STRONG  | STRONG  |
          | (adv)    | (G2+G3) | (G5)    | (G9+10) | (G15+GK)|
          +----------+---------+---------+---------+---------+
Continuous| ---      | ---     | G6 STR  | G6,7,8  | G6,7    |
gates     |          |         |         | G14 M-H | G14 M-H |
          +----------+---------+---------+---------+---------+

Legend: STRONG = Hook deny   MED-HI = Rule+Skill+Gate Keeper
        MEDIUM = Rule+Skill  MED-LOW = Rule+Advisory  WEAK = Rule only
```

### Consolidated Strength Matrix (Compositional)

| Step | DOR Strength | DOD Strength | Key Composition |
|------|-------------|-------------|-----------------|
| 0: Bootstrap | N/A | MED-LOW | Rule + advisory hook |
| 1: Upstream | STRONG | STRONG | Hook (`spec-review-gate`) + runtime (`ExitPlanMode`) + Gate Keeper |
| 2: Exec Plan | STRONG | STRONG- | Hook (`plan-review-gate` Gate 2: approved-spec) + Gate Keeper for deps; plan-review hook |
| 3: Code (TDD) | STRONG | STRONG- | Hook + Gate Keeper + skill + rule (deepest coverage) |
| 4: Ship/Done | STRONG | STRONG | Rule + `/ship` skill + Gate Keeper ship-review + `push-gate.sh` (gate-ship marker at push) |

---

## Gap Analysis

| Gap | Where | Impact | Fix Difficulty |
|-----|-------|--------|---------------|
| Bootstrap/Reload are advisory | G0/G12 | Agent could work with stale directives | Medium (blocked by done/ contract for now) |
| ~~Spec-review not mechanically enforced~~ | ~~G2 upstream exit~~ | ~~Agent could ExitPlanMode without spec-review~~ | **RESOLVED** (S4: `spec-review-gate.sh` blocks ExitPlanMode, escape hatch at 3 attempts) |
| ~~Directive freshness is advisory~~ | ~~G11 before push~~ | ~~Agent could push with stale rules~~ | **RESOLVED** (S1: advisory → deny) |
| BANNED patterns have no hook | G14 T3 | Relies on behavioral refuse + code-review backstop | Hard (code scanning is fragile) |
| Dependency check is behavioral | G4 story lock | Agent could start story with unmet deps | Medium (cross-file metadata parsing) |
| ~~Compliance/Drift are behavioral~~ | ~~Step 4 before done/~~ | ~~Agent could skip compliance checklist~~ | **RESOLVED** (S2: G15 ship gate checks done/, drift, compliance) |

### True Gaps (After Compositional Analysis)

Reduced from 5 "complete gaps" (hook-only) to 1 true gap (compositional):

1. ~~**Spec-review before ExitPlanMode**~~ — **RESOLVED** (S4: ExitPlanMode hookable, `spec-review-gate.sh` deployed)
2. **`/ship` invocation is not mandatory** — no hook can enforce "use this skill"

Other "gaps" are MEDIUM (Rule + Skill) — not ideal but not unenforceable.

---

## Consistency Review Findings

### Finding 1: Session-Init Deny — BLOCKED

Story `2026-02-23.19-39-44a` (SDLC_HOOKS) AC4 explicitly mandates: "unified-reload-gate.sh (Mode A) uses `additionalContext` (advisory) — NOT converted to blocking." Two passing tests enforce this contract. Upgrading bootstrap to deny would break this contract. (Note: originally `session-init-gate.sh`, consolidated into `unified-reload-gate.sh` by story 2026-03-05.01-40-18.)

**Self-interference risk:** The bootstrap sequence itself IS bash commands. Deny logic must whitelist the bootstrap steps — but those steps are detected by the same pattern matching. Advisory model avoids this circularity.

### Finding 2: APPROVED-SPEC in Plan-Review Gate — BLOCKED

Gate stamps are NOT stored in story files. APPROVED-SPEC is emitted in chat context, not written to `.md` files. Grepping the story file for `APPROVED-SPEC` would find nothing in ANY existing story — immediately breaking all stories in `todo/`.

**Resolution:** Establish a convention where agent writes `APPROVED-SPEC: [timestamp]` to story file at upstream commit time (prerequisite infrastructure).

### Finding 3: Spec-Review Gate on ExitPlanMode — CONFIRMED HOOKABLE

ExitPlanMode as a hook target is confirmed by S4 spike (2026-02-24.23-16-02d). PreToolUse hooks fire for any tool name matcher, including ExitPlanMode. `spec-review-gate.sh` registered with matcher "ExitPlanMode" and deployed.

**Atomic dependency resolved:** Gate Keeper calls `POST /gate-review` to persist `review_spec` stamp on spec-review pass. `spec-review-gate.sh` (S4) consumes it via API query. Escape hatch at 3 attempts prevents permanent deadlock.

### Finding 4: Ship Compliance Gate — CIRCULAR DEPENDENCY

Checklist items reference the commit itself (e.g., "Conventional commit with story ID + Co-Authored-By"). Cannot check this BEFORE the commit happens. If gate denies on any unchecked `- [ ]` item, this creates deadlock.

**Resolution:** Scope gate to check ONLY: (a) story in done/ (not doing/), (b) DRIFT line is not placeholder, (c) compliance section exists with >0 checked items. Skip per-item validation.

### Root Cause: Gate Stamp Ephemerality

Gate stamps exist only in conversation context — emitted as chat messages, not persisted to files. No hook can verify them.

**Resolution options:**
1. **Convention change:** Agent writes stamps to story file in structured section. Requires template update + migration
2. **Marker files as proxies:** Use `/tmp/claude-*` markers (already done for plan/code-review). Session-scoped limitation
3. **Accept behavioral:** Stamps remain conversational. `/ship` skill verifies. Current state

Option 2 is the pragmatic middle ground for same-session enforcement.

---

## Implementation Roadmap (6 Stories)

### Proposed Stories

| # | Story | Type | Priority | Depends On | Scope | Estimated |
|---|-------|------|----------|-----------|-------|-----------|
| 0 | Gate Stamp Markers | Story | Medium | — | Extend hook infra for spec-review + APPROVED-SPEC markers | Medium (1-3h) |
| 1 | Gate Architecture Document | SDLC | High | — | This story — reference doc | Small (<1h) |
| 2 | Harden Push Gate | Story | High | — | **DONE** — `directive-freshness` upgraded to deny (S1: 2026-02-24.23-16-02a) | Small (<1h) |
| 3 | Spec-Review Enforcement | Story | Medium | Story 0 | **DONE** — `spec-review-gate.sh` blocks ExitPlanMode (S4: 2026-02-24.23-16-02d) | Medium (1-3h) |
| 4 | Ship Gate | Story | High | — | **DONE** — G15 ship DOD gate added (S2: 2026-02-24.23-16-02b) | Medium (1-3h) |
| 5 | Upstream Token Gate | Story | Low | Story 0 | **DONE** — `plan-review-gate.sh` Gate 2 checks approved-spec marker + cross-session fallback (S5: 2026-02-24.23-16-02e) | Small-Medium (1-2h) |

### Execution Order

```
Stories 0, 1, 2 — no dependencies, execute first in any order
Story 4 — independent, can execute alongside 0/1/2
Stories 3, 5 — depend on Story 0 (marker infrastructure)
```

### Expected Strength Improvement

| Step | DOR Before → After | DOD Before → After |
|------|--------------------|--------------------|
| 0: Bootstrap | N/A | MED-LOW → MED-LOW (unchanged, contract-blocked) |
| 1: Upstream | STRONG | MED-HIGH → **STRONG** (S4: ExitPlanMode hookable, `spec-review-gate.sh` deployed) |
| 2: Exec Plan | MEDIUM → **STRONG** (S5: approved-spec marker + fallback in plan-review-gate) | STRONG (no change) |
| 3: Code (TDD) | STRONG | STRONG (no change) |
| 4: Ship/Done | STRONG | MEDIUM → STRONG (done/ + drift + compliance hooks) |

### Hardening Tiers

**Tier 1 — Clean conversions (zero-to-low risk):**
- Directive freshness: advisory → deny (zero risk, flip flag)
- Story in done/ before commit (low risk, `pre-commit-test-gate.sh`)
- Drift review filled (low risk, grep check)
- Compliance ≥1 checked (low risk, grep check)

**Tier 2 — Requires infrastructure:**
- ~~Spec-review before ExitPlanMode~~ **DONE** (S4: ExitPlanMode confirmed hookable, `spec-review-gate.sh` deployed)
- ~~APPROVED-SPEC marker~~ **DONE** (S5: `plan-review-gate.sh` Gate 2 checks approved-spec marker)
- ~~Upstream complete at doing/ DOR~~ **DONE** (S5: Gate 2 + cross-session fallback)

**Tier 3 — Impractical for hooks (ceiling is MED-HIGH):**
- Docs updated (aggregate-to-doc mapping too fragile for shell)
- Gate stamps all emitted (variable per type, semantic)
- Bootstrap/reload (contract-blocked + self-interference)

---

## Token Burden Analysis

| Metric | Value |
|--------|-------|
| Typical story total tokens | 50,000–200,000 |
| Current hook overhead | ~3,000–11,500 (~5% of story) |
| Tier 1 addition | ~150–300 (<0.2%) |
| Tier 2 addition | ~220–550 (<0.3%) |
| **Full hardening total** | **~370–850 tokens (<0.5% increase)** |

All new checks fire at low-frequency events (commit, push, story transitions) — not on every tool call. Negligible impact on latency and cost.

---

## What Stays Behavioral (Honest List)

| Condition | Why | Acceptable? |
|-----------|-----|-------------|
| Session bootstrap (Step 0) | Existing contract prevents hardening | Temporary — revisit when scope allows |
| ~~EPIC approval~~ | ~~Gate Keeper epic-specific checklist validates completeness (S7). Hook enforcement deferred to S9~~ | **RESOLVED** (S9: API endpoint returns 422 when epic ≥2 stories without `acceptance_criteria`. `epic-ceremony-gate.sh` advisory hook + API-layer primary enforcement) |
| Dependencies satisfied | Cross-file metadata parsing | Yes — `/next` skill + plan-review catches |
| Per-item compliance validation | Circular dependency with commit items | Yes — existence check is sufficient |
| Docs updated | Git diff analysis needed | Yes — code-review catches |
| All gate stamps emitted | Conversational context only | Yes — `/ship` skill verifies |
| AC coverage complete | Semantic verification | Yes — code-review catches |

---

*Document Version: 1.0*
*Created: 2026-02-24 by story 2026-02-24.21-56-05*
