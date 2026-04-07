# /session-log — Session Chat History Capture

**Usage:** `/session-log <phase>`

> Captures an agent-curated markdown recap of the current session phase and POSTs it to the story's chat history. Primarily used for the `discuss` phase or as a manual backup — lifecycle skills (`/spec`, `/pull`, `/ship`) handle automatic capture at phase boundaries.
>
> **Phases:** `discuss`, `spec`, `pull`, `ship`
>
> **Hub API:** Source `scripts/hub-client.sh` for `hub_record_chat_history()`.
> **Error Handling:** SILENT tier — best-effort capture. API failures logged but never block workflows. See `.claude/skills/error-handling-convention.md`.

---

## Step 1: Validate Phase Argument

1. Phase argument is **mandatory**. If missing: report usage hint and stop
2. Validate phase is one of: `discuss`, `spec`, `pull`, `ship`. If invalid: report and stop

---

## Step 2: Resolve Active Story

1. Resolve marker ID:
   ```bash
   source .claude/hooks/lib/hub-query.sh
   MARKER_ID=$(resolve_marker_id)
   ```
2. Read story UUID from tracking file:
   ```bash
   STORY_UUID=$(cat "/tmp/claude-active-story-uuid-${MARKER_ID}" 2>/dev/null)
   ```
3. **No active story:** Log warning "No active story found — skipping session capture." and STOP. This is expected (fail-open) — capture is best-effort, not a governance gate

---

## Step 3: Write Structured Recap

Write a markdown recap of the current session phase. The recap MUST include all 6 sections below. Each section should be concise but substantive — capture what actually happened, not boilerplate.

### Required Sections

```markdown
## Session Summary
Brief narrative of what happened during this phase. What was the goal and what was accomplished.

## Key Decisions
Bullet list of significant decisions made during this phase and their rationale.

## Friction Points
Operational problems encountered: invalid parameters, parse failures, API errors,
stamp rejections, hook denials, validation failures, retry loops. Include the specific
error and how it was resolved. If none: "None encountered."

## Problems Encountered
Technical or domain problems beyond operational friction: design challenges, constraint
conflicts, ambiguous requirements, unexpected complexity. If none: "None encountered."

## User Interactions
Summarize meaningful user interactions: questions asked, choices made, feedback given,
corrections applied. If the phase had no user interaction: "No user interactions."

## Outcomes
What was produced: artifacts created, stamps emitted, tests written/passing, story
state changes. Concrete deliverables, not process descriptions.
```

### Writing Guidelines

- **Be specific.** "Fixed AC validation" → "AC text required explicit GIVEN/WHEN/THEN keywords; markdown bold syntax (`**Given**`) was rejected by backend validator"
- **Capture friction honestly.** The purpose is retrospective analysis — sanitizing problems defeats the purpose
- **Include counts.** "15 tests passing" not "tests pass". "3 ACs met" not "ACs complete"
- **Reference files.** Name the files that were created or modified
- **Keep it under 500 words.** Concise recaps are more useful than verbose ones

---

## Step 4: POST to Story

```bash
source scripts/hub-client.sh
source .claude/hooks/lib/hub-query.sh
MARKER_ID=$(resolve_marker_id)
hub_record_chat_history "$STORY_UUID" "<phase>" "<recap_content>" "$MARKER_ID"
```

- **On success:** Log "Session recap recorded for phase: <phase>"
- **On failure:** Log warning "Failed to record session recap (non-blocking)" — do NOT fail the session. Capture is best-effort

---

## When to Invoke

Session capture is now **automatic** — lifecycle skills handle phase-boundary capture directly:

| Lifecycle Skill | Phase Captured | Trigger Point |
|----------------|---------------|---------------|
| `/spec` Step 12 | `spec` | After commit + stamps, before routing |
| `/pull` Step 4i | `pull` | After ship-review PASS, before `/ship` |
| `/ship` Step 4.5 | `ship` | After transition to done, before cleanup |

**Manual invocation** of `/session-log <phase>` remains available as a backup for:
- The `discuss` phase (no automatic trigger — discuss has no Gate Keeper review)
- Re-capturing a phase if the automatic capture failed or produced incomplete content
- Ad-hoc session documentation outside the standard lifecycle
