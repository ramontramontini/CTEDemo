---
name: discuss
description: >
  Upstream start mode for exploratory discussions. Enters plan mode for
  ungated exploration — reading files, searching code, brainstorming.
  Three exit paths: knowledge gained (exit), actionable work (→ /spec),
  or large scope (→ epic ceremony).
---

# /discuss — Upstream Start Mode (Exploratory Discussion)

**Usage:** `/discuss`

> **Sources:** CLAUDE.md §Plan Mode Decision (upstream split), EAC8
>
> `/discuss` is the **entry point** for all upstream work. It enters plan mode
> for free exploration without gates. When actionable work is identified,
> transition to `/spec` for the structured specification ceremony.

---

## Step 1: Enter Discuss Mode

1. Call **EnterPlanMode** — begin exploratory plan mode session
2. Set discuss-mode marker: run `touch /tmp/claude-discuss-mode-{SESSION_ID}` via Bash
   - This marker exempts ExitPlanMode from spec-review (`spec-review-gate.sh` allows exit when marker present)
   - Same pattern as `echo SHIP_COMPLETE` in /ship skill — no hook needed, agent sets marker directly
   - **Verify marker exists (WARN tier):** After `touch`, check `[ -f /tmp/claude-discuss-mode-{SESSION_ID} ]`. If not: output `⚠️ WARNING: Discuss marker not set — ExitPlanMode may require spec-review gate. Recovery: touch /tmp/claude-discuss-mode-{SESSION_ID} manually or use /spec directly`

> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT).

---

## Step 2: Free Exploration

Explore freely with the user — no gates, no story creation, no code changes:

- Read source files, search code, explore architecture
- Discuss trade-offs, investigate questions, brainstorm approaches
- Use AskUserQuestion for clarifications
- Launch Explore agents for codebase investigation

**No governance tokens are emitted.** /discuss is purely conversational.

### Inflection-Point Detection

Monitor for signals that the discussion has evolved into spec-worthy work:

| Signal | Example |
|--------|---------|
| Concrete ACs emerging | User describes specific expected behaviors in Given/When/Then-like terms |
| Specific files identified | Discussion narrows to "we need to change X in file Y" |
| Scope crystallizing | Discussion converges on a single deliverable with clear boundaries |
| Language shift | User moves from "what if" / "could we" to "let's do" / "we should" |
| Implementation direction chosen | Trade-off analysis concludes with a chosen approach |

**When 2+ signals are present:** Proactively suggest transitioning to `/spec` via Path B. Example: "This has crystallized into actionable work. Transitioning to /spec to formalize."

> **Anti-pattern: do NOT exit plan mode (Path A) and then invoke `/spec`.** This creates redundant ceremony — the agent re-enters plan mode, re-explores the codebase, and re-asks about scope. Path B keeps plan mode active and carries forward all discussion context.

---

## Step 3: Exit — Three Paths

At the natural conclusion of discussion, take one of three paths:

### Path A: Knowledge Gained (Exit)

> Discussion concludes with knowledge gained but no actionable work identified.

1. Call **ExitPlanMode** — `spec-review-gate.sh` sees discuss-mode marker → allows exit without gate-spec
2. No artifact produced. No story created. No tokens emitted

### Path B: Transition to /spec (Actionable Work)

> Discussion identifies actionable work that should become a story. This is the **preferred path** when inflection-point signals are detected — do not exit via Path A and re-invoke `/spec` separately.

1. Invoke `/spec` or `/spec STORYID`
2. `/spec` Step 1 clears the discuss-mode marker (`rm -f /tmp/claude-discuss-mode-{SESSION_ID}`)
3. Plan mode is **continuous** — `/spec` skips EnterPlanMode (no exit/re-enter cycle)
4. Spec-review becomes mandatory for ExitPlanMode (discuss-mode marker cleared)
5. **Context carries forward:** `/spec` builds on exploration and conclusions from the discussion. It formalizes discussed concepts into GWT ACs, extracts risks, and codifies scope — rather than starting from a blank template. See `/spec` Step 3-4 discuss-handoff notes

### Path C: Transition to Epic Macro-Requirements (Large Scope)

> Discussion identifies large scope requiring 3+ stories — needs an epic.

1. Clear discuss-mode marker: run `rm -f /tmp/claude-discuss-mode-{SESSION_ID}` via Bash
2. Begin epic macro-requirements ceremony per CLAUDE.md §Policy 7
3. Spec-review becomes mandatory for ExitPlanMode (discuss-mode marker cleared)
4. Full epic ceremony proceeds: write macro-requirements, spec-review, ExitPlanMode approval

---

## Discuss-Mode Marker

| Aspect | Detail |
|--------|--------|
| **Marker** | `/tmp/claude-discuss-mode-{SESSION_ID}` |
| **Set by** | This skill (Step 1) via Bash `touch` |
| **Cleared by** | `/spec` Step 1, Path C instruction, `story-gate.sh` (story transition), `/ship` Step 5 (post-ship `/tmp` cleanup) |
| **Consumed by** | `spec-review-gate.sh` — allows ExitPlanMode without gate-spec when present |
| **Scope** | Session-scoped (new session = new SESSION_ID = no stale marker) |

---

## When to Use /discuss vs /spec

| Signal | Use |
|--------|-----|
| User asks a question, wants exploration | `/discuss` |
| User says "let's build X" or "create a story for X" | `/spec` directly (no /discuss needed) |
| User proposes investigation or trade-off analysis | `/discuss` |
| User provides clear requirements ready for specification | `/spec` directly |
| Uncertain whether work is needed | `/discuss` → may transition to `/spec` |
