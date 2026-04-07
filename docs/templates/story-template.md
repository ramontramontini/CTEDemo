> **Reference Format** — Stories are created via API (`POST /api/v1/stories`). This template documents the standard markdown format that the Session Story Renderer produces in agent worktrees. Do not manually create story files from this template.

# STORYID - Type | [Title]

> **Status:** Todo | Doing | Done
> **Type:** Story | BUG | Refactor | SDLC | Data
> **Priority:** High | Medium | Low
> **Epic:** EPICNAME or — (optional, must match stories/epics/EPICNAME.md)
> **Dependencies:** STORYID, STORYID or — (optional)
> **Source Story:** STORYID, STORYID or — (REQUIRED for BUG type: links to story that introduced the defect. Use `unknown — [justification]` if source cannot be identified)
> **Created:** YYYY-MM-DDTHH:MM:SSZ
> **Started:** YYYY-MM-DDTHH:MM:SSZ or —
> **Completed:** YYYY-MM-DDTHH:MM:SSZ or —
> **Lead Time:** [calculated: Completed − Created] or —
> **Gate Keys:** [number] or —
> **Upstream Token Cost:** [number] or —
> **Plan Token Cost:** [number] or —
> **Execution Token Cost:** [number] or —
> **Token Cost Total:** [computed: sum of non-None costs] or —
> **Lock:** YYYY-MM-DDTHH:MM:SSZ by Session #XX or —

> **Filename Format:** `STORYID - EPIC | Type | Short Title.md` (with epic) or `STORYID - Type | Short Title.md` (without epic). STORYID = `YYYY-MM-DD.HH-MM-SS` from `date -u`

---

## Upstream: Requirements

> Written during upstream plan mode (EnterPlanMode). Committed after ExitPlanMode approval (APPROVED-SPEC).

---

## Context

[Why are we doing this? What problem, gap, or user need triggered this story? Include background and motivation.]

---

## Goal

[1-2 sentences: What does success look like? What will be true when this story is done?]

---

## Acceptance Criteria

> Use Given/When/Then format for testable criteria.

### AC1: [Short Name]
GIVEN [initial state]
WHEN [action]
THEN [expected outcome]

### AC2: [Short Name]
GIVEN [state]
WHEN [action]
THEN [outcome]

### AC3: [Short Name]
GIVEN [state]
WHEN [action]
THEN [outcome]

---

## User Journey

> **MANDATORY for ALL stories.** Step-by-step flow showing how the user/developer/operator interacts with the feature.
> UI stories: include screens, clicks, system responses. Backend/SDLC/Data: developer or operator journey.

1. User navigates to [page] / Developer runs [command]
2. User sees [initial state] / Developer observes [behavior]
3. User clicks [element] / Developer executes [action]
4. System responds with [behavior]
5. User sees [result] / Developer verifies [outcome]

**Alternate paths:**
- If [condition] → [different behavior]

**Error paths:**
- If [error condition] → [error message shown to user]

---

## Wireframes

> **MANDATORY for UI stories.** ASCII wireframes for each screen added or modified.
> Non-UI stories: Write "N/A — [justification]" (e.g., "N/A — no UI changes. Backend domain model.")

```
+-----------------------------------------------+
|  Header                              [Action]  |
+-----------------------------------------------+
|  [ Sidebar ]  |  Main Content Area             |
|               |  +---------------------------+ |
|               |  | Component Name            | |
|               |  | [field] [field] [button]   | |
|               |  +---------------------------+ |
+-----------------------------------------------+
```

---

## Edge Cases

> **MANDATORY — minimum 3 edge cases with expected behavior.**

- [Boundary condition or unusual scenario] — [expected behavior]
- [Error scenario] — [expected behavior]
- [Empty/null/zero case] — [expected behavior]
- [Concurrent access scenario] — [expected behavior]

---

## Risks

- **[Risk 1]:** [Description and mitigation strategy]
- **[Risk 2]:** [Description and mitigation strategy]
- **Open question:** [Question] → **Decision:** [Answer or "TBD"]

---

## OO Design Decision

> **MANDATORY for ALL story types.** The agent must analyze OO implications and present structured design options for user approval during upstream `/spec` ceremony.
>
> **Code stories (feature, bug, refactoring):** Present 2+ OO approaches with pros/cons. Agent recommends one. User selects.
> **Non-code stories (sdlc, data, maintenance, investigation) or no OO implications:** Present N/A justification via AskUserQuestion. User must explicitly approve the N/A classification.

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **A: [Name]** | [Description of OO design: entities, aggregates, patterns, value objects] | [Advantages] | [Disadvantages] |
| **B: [Name]** | [Description of alternative OO design] | [Advantages] | [Disadvantages] |

**Agent Recommendation:** [A or B] — [Reasoning why this approach is preferred]

**Selected Approach:** [User's selection recorded here after AskUserQuestion approval]

**N/A Path:** If no OO implications: "N/A — [justification, e.g., 'No domain entity changes — pure CSS update']. User approved via AskUserQuestion."

---

## Data Model Changes (Include if applicable)

> Write "N/A" if no data model changes.

**New/Modified Entities:**
```typescript
interface EntityName {
  id: string;
  field: type;  // NEW or MODIFIED — describe change
}
```

---

## API Contract Changes (Include if applicable)

> Write "N/A" if no API changes.

**Endpoints:**
- `[METHOD] /api/v1/[path]` — [description]

**Request/Response shapes:**
```json
{ "field": "value" }
```

**Error Responses:**

| Error Condition | HTTP Status | User Message |
|----------------|-------------|--------------|
| [Error 1] | [Code] | [Message] |

---

## Business Rules (Include if applicable)

- [Rule 1: domain logic, calculation, or validation]
- [Rule 2]

---

## Execution Plan

> Written during upstream plan mode alongside spec. Included in combined upstream review (Gate Keeper spec-review).

### Goal
[1-2 sentences: What are we trying to achieve?]

### AC1: [AC name]
1. RED — [failing test description]
2. GREEN — [implementation to pass test]
3. REFACTOR — [cleanup if needed]

### AC2: [AC name]
1. RED — [failing test description]
2. GREEN — [implementation to pass test]

> **Code types (feature, bug, refactoring):** Group tasks under AC headers with RED/GREEN/REFACTOR steps.
> **Non-code types (SDLC, Data, etc.):** Use task headers instead (no TDD steps). Example: `### Task 1: [description]`

---

## Verification Criteria (Include for BUG type — required)

> For BUG stories only. Defines how to reproduce the bug and verify the fix.

### How to Reproduce (Before Fix)
1. [Step 1]
2. [Step 2]
3. [Observe incorrect behavior]

### Runtime Verification (After Fix)
- [ ] Backend restarted (if needed)
- [ ] API called with curl/httpx — specific values verified
- [ ] Frontend tested (if UI change)
- [ ] No regression in related functionality

---

## Downstream: Execute

> Execute the plan approved upstream. TDD per AC (RED > GREEN > REFACTOR). Code-review after all ACs green. Structural hooks enforce combined upstream review before code changes.

---

## Execution Log

- [timestamp] [task] — [outcome]

---

## Compliance Checklist

> Fill per `docs/templates/compliance-checklist.md`

---

## Drift Review

[Qualitative narrative only — no classification needed. drift_type is auto-computed from evidence at DONE transition: friction from gate FAILs, bug/regression from auto-escalation. Only flag plan_drift if you knowingly deviated from the approved plan.]

[If friction occurred: what caused gate FAILs, lessons learned. If plan deviation: why, what changed, impact.]

---

## Approval

**Commit SHA:** [SHA]

---

*Template Version: 16.0 (Added mandatory OO Design Decision section between Risks and Data Model Changes.)*
*Last Updated: 2026-04-04*
