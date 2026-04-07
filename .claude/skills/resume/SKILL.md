---
name: resume
description: >
  Session resume for in_progress stories. Detects active work via board-check,
  reads execution plan/log from API, reports resume state, updates lock.
  Handles stale locks (>4h auto-takeover) and active lock conflicts.
---

# /resume — Session Resume

**Usage:** `/resume` (no arguments — auto-detects in_progress story from board state)

> **Sources:** CLAUDE.md §Story Locking, §Session Resume (incoming/outgoing)
>
> **Hub API:** Source `scripts/hub-client.sh` for all API operations. Provides `hub_get()`, `hub_post()`, `hub_patch()`, `hub_claim()` with 3-retry exponential backoff. See `.claude/skills/hub-api-helpers.md` for idempotency notes.
>
> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT).

---

## Step 1: Detect In-Progress Story

Query the hub API for stories in `in_progress` status:

```bash
source scripts/hub-client.sh
hub_get "/api/v1/stories?status=in_progress"
```

**If no in_progress stories found:** Report "No in_progress stories found. Use `/pull STORYID` to start a story." STOP.

**If multiple in_progress stories found:** List all with STORYID + Title. Use AskUserQuestion with each story as a structured option (format: "[STORYID] — [Title]"). STOP until user selects.

**If exactly one found:** Extract UUID (`id`), STORYID (`story_id`), Title, Type, ACs, Execution Plan, Execution Log, Lock metadata. Proceed to Step 2.

---

## Step 2: Evaluate Lock State

Read the story's lock metadata from the API response.

### Lock Decision Table

| Lock State | Condition | Action |
|------------|-----------|--------|
| No lock | `lock` is null | Proceed freely — claim and update lock (Step 3) |
| Stale lock | Lock timestamp is >4 hours old | Auto-takeover — claim and update lock (Step 3). Report: "Stale lock (>4h) from [session]. Auto-takeover." |
| Active lock (same agent) | Lock held by current agent, <4h old | Proceed — refresh lock timestamp (Step 3) |
| Active lock (different agent) | Lock held by different agent, <4h old | STOP. Report lock details. Use AskUserQuestion with options: "Release lock and resume" / "Wait for [agent] to finish" / "Cancel resume". |

**Stale threshold:** 4 hours from lock timestamp to current time.

---

## Step 3: Claim and Update Lock

Update the lock by re-claiming the story:

```bash
source scripts/hub-client.sh
hub_claim "$STORY_UUID" "$EUPRAXIS_AGENT_NAME"
```

**409 conflict (exit 1, already claimed by another agent — STOP tier):** Re-evaluate lock staleness from Step 2 data. If lock timestamp is >4h old (stale): report `❌ STOP: 409 on claim despite stale lock (>4h) — API may have race condition. Lock holder: [agent] since [timestamp].` Use AskUserQuestion with options: "Force release lock via hub_patch" / "Abort resume". If lock is <4h old (active): report `❌ STOP: Story locked by [agent] since [timestamp] (active lock, <4h). Cannot auto-takeover.` In both cases STOP.

**Retry:** Non-idempotent — check if already claimed by this agent before retry.

---

## Step 4: Read Execution State

From the story data retrieved in Step 1, extract:

1. **Execution Plan** — the task list for this story
2. **Execution Log** — what has been completed so far
3. **ACs** — acceptance criteria and their met/unmet status
4. **Gate Stamps** — which gates have been passed

---

## Step 5: Report Resume State

Report to user:

```
Resuming [title] (STORYID). Last action: [from execution log]. Next task: [from execution plan].
ACs: [met]/[total] | Gate Stamps: [list of emitted stamps]
```

If execution log is empty: "Resuming [title] (STORYID). No execution log — starting from execution plan Step 1."

If execution plan is empty: "Resuming [title] (STORYID). No execution plan found — write plan before proceeding."

---

## Step 6: Continue Execution

Determine resume point from execution log and skip completed steps:

1. Match execution log entries against execution plan tasks
2. Identify the first incomplete task
3. Continue from that task using the appropriate skill (`/pull STORYID --resume` for code types, or direct execution for SDLC/Data types)

---

## Outgoing Resume Procedure

When ending a session with an in_progress story (not invoked as `/resume` — this is guidance for session exit):

1. **Update execution log** — PATCH the story with current progress:
   ```bash
   source scripts/hub-client.sh
   hub_patch "/api/v1/stories/$STORY_UUID" '{"execution_log": "<updated log>"}'
   ```
2. **Commit all modified tracked files** — `stop-clean-worktree.sh` Stop hook blocks session exit with a dirty worktree
3. **Push WIP to main** — ensures next session can pull-rebase and continue
4. Story files in `stories/` are gitignored and do not need committing

---

## Failure Handling

| Failure | Action |
|---------|--------|
| Hub API unreachable | Report with URL. STOP |
| No in_progress stories | Report: "No in_progress stories found." STOP |
| Multiple in_progress stories | List all, use AskUserQuestion with each story as an option |
| Active lock by another agent | Report lock holder and timestamp. STOP |
| 409 on claim | Report conflict details. STOP |
| Empty execution plan | Report and advise writing plan before proceeding |
| Story state changed externally | "Story state changed externally — re-check via API." STOP |

---

## Notes

- `/resume` is invoked during incoming session resume (after bootstrap). It is not part of the normal story execution flow
- The outgoing resume procedure is enforced by `stop-clean-worktree.sh` — not by this skill
- Lock format in DB: `Lock: YYYY-MM-DDTHH:MM:SSZ by Session #XX`
- No gate stamps are emitted by this skill — it resumes execution context only
