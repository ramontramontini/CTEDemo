# Epic: EPICNAME

> **Status:** Active | Complete | Shelved
> **Created:** YYYY-MM-DDTHH:MM:SSZ
> **Started:** YYYY-MM-DDTHH:MM:SSZ or — (first story transitioned to in_progress via API)
> **Completed:** YYYY-MM-DDTHH:MM:SSZ or — (last story transitioned to done or canceled via API)
> **Lead Time:** [calculated: Completed − Started] or —

> **Section requirements:**
> - **Always mandatory:** Goal, EACs (Given/When/Then), Stories table (with INVEST column)
> - **Mandatory for all epics:** Dependency Graph, Complexity Assessment, Risks, Edge Cases (min 3)
> - **Optional:** Key Files, Developer Journey, Cross-Epic Dependencies, Notes

---

## Goal *(mandatory)*

[1-3 sentences: what business problem this epic solves and what success looks like.]

---

## Acceptance Criteria (Epic-Level) *(mandatory — Given/When/Then)*

- [ ] EAC1: **Given** [precondition], **When** [action], **Then** [expected outcome]
- [ ] EAC2: **Given** [precondition], **When** [action], **Then** [expected outcome]

---

## Stories *(mandatory — INVEST validated per row)*

| Order | Story | Type | Title | Status | Dependencies | INVEST |
|-------|-------|------|-------|--------|--------------|--------|
| S1 | STORYID - EPICNAME \| Type \| Title | Type | Title | Todo/Doing/Done | — | I: [1 sentence]. N: [1 sentence]. V: [1 sentence]. E: [1 sentence]. S: [1 sentence]. T: [1 sentence]. |
| S2 | STORYID - EPICNAME \| Type \| Title | Type | Title | Todo | S1 | I: ... N: ... V: ... E: ... S: ... T: ... |
| S{N} | *(auto-created by backend)* | Story | Capstone | Todo | S1, S2, ..., S{N-1} | I: Fan-in verification, no inter-story deps. N: ACs derived from EACs. V: Proves epic works as a whole. E: Scope = EAC count. S: Verification + fixes. T: Each EAC is a test. |

> **S-prefix convention:** Stories receive auto-assigned `S{N}` prefixes on creation via `POST /api/v1/stories` when `epic_id` is set. Creation order = dependency order (topological). Already-prefixed titles are not double-prefixed.
>
> **Capstone story (all epics, including 0-story):** The last row is auto-created by the backend when ceremony fields are populated via PATCH. Title: `S{N} EPICNAME | Story | Capstone`. Depends on ALL other stories (fan-in, empty for 0-story epics). ACs derived from the epic's EACs. See CLAUDE.md §Policy 7.

---

## Dependency Graph *(mandatory)*

```
STORYID - EPICNAME | Type | Title (foundation)
    |--- STORYID - EPICNAME | Type | Title ---> STORYID - EPICNAME | Type | Title
    |--- STORYID - EPICNAME | Type | Title
```

---

## Complexity Assessment *(mandatory)*

| Story | Complexity | Time | Rationale |
|-------|-----------|------|-----------|
| STORYID — Title | Simple / Medium / Complex | Small (<1h) / Medium (1-3h) / Large (3h+) | [Why this complexity/time rating] |

---

## Key Files *(optional)*

[List key source files and directories relevant to this epic.]

| Area | Path | Purpose |
|------|------|---------|
| [Domain/Frontend/Infra] | `path/to/file` | [What this file does in the context of this epic] |

---

## Risks *(mandatory)*

[Document risks with impact and mitigation.]

| Risk | Impact | Mitigation |
|------|--------|------------|
| [What could go wrong] | [Low/Medium/High — consequence] | [How we prevent or handle it] |

---

## OO Design Decision *(mandatory)*

> **Macro-level OO design decisions for the epic.** Covers aggregate boundaries, cross-aggregate patterns, shared types strategy. Individual stories reference and refine the epic decision without contradicting it.

| Decision Area | Approach | Rationale |
|---------------|----------|-----------|
| **Aggregate Boundaries** | [Which aggregates are involved, how they're scoped] | [Why these boundaries] |
| **Cross-Aggregate Patterns** | [Service composition, event-driven, direct calls] | [Trade-offs considered] |
| **Shared Types Strategy** | [What goes in `domain/shared/`, immutability rules] | [Why shared vs aggregate-local] |
| **Entity Behavior Model** | [Key entity methods, Home factory patterns, VOs] | [Design rationale] |

**N/A Path:** If no OO implications (e.g., pure SDLC/infrastructure epic): "N/A — [justification]. User approved."

---

## Developer Journey *(optional)*

[Include when the epic changes a developer or operator workflow. Describe the end-to-end flow from the developer/operator perspective after all stories are complete.]

1. Developer/Operator does X
2. System responds with Y
3. ...

---

## Edge Cases *(mandatory — min 3)*

[Structural edge cases the epic as a whole must address.]

- **[Edge case name]** — [description and how it's handled]

---

## Cross-Epic Dependencies *(optional)*

[Document when this epic depends on or is depended upon by other epics.]

**Incoming (this epic depends on):**
- [EPICNAME — what this epic needs from it, or "None"]

**Outgoing (other epics depend on this):**
- [EPICNAME — what other epics need from this, or "None"]

---

## Notes *(optional)*

[Architectural decisions, constraints, open questions for the epic.]

---

## Completion Log

### YYYY-MM-DDTHH:MM:SSZ - Epic Created
- Stories decomposed from: "[original feature request]"
- N stories created in dependency order

### YYYY-MM-DDTHH:MM:SSZ - Epic Started
- First story STORYID - EPICNAME | Type | Title transitioned to in_progress via API
- Updated Started timestamp

### YYYY-MM-DDTHH:MM:SSZ - Epic Complete
- Last story STORYID - EPICNAME | Type | Title transitioned to done via API
- All epic-level AC met
- Updated Completed timestamp and Lead Time

---

**Timestamp Rules:**
- **Started** = timestamp when the first story in this epic transitions to `in_progress` via API
- **Completed** = timestamp when the last story transitions to `done` or `canceled` via API
- **Lead Time** = Completed − Started (measures total epic execution duration)
- Agent updates these timestamps as stories progress

---

*Template Version: 2.2 (Added mandatory OO Design Decision section between Risks and Developer Journey.)*
*Last Updated: 2026-04-04*
