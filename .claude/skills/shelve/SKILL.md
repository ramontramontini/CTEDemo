---
name: shelve
description: >
  Shelve an in_progress story and return it to ready_to_pull with a Revision Required
  section. Detects uncommitted vs committed state and applies the correct path:
  revert code (uncommitted) or preserve commits (committed-but-incomplete).
---

# /shelve -- Story Shelving

**Usage:** `/shelve STORYID` or `/shelve Story Title`

> **Argument resolution:** The argument can be a **UUID**, **STORYID** (timestamp `YYYY-MM-DD.HH-MM-SS`), or a **story title** (any other string). Pass the argument directly as a path parameter — the API resolves it server-side (UUID → timestamp → title, case-insensitive with substring fallback). Single match → resolved. Zero matches → 404. Multiple title matches → 409 `AMBIGUOUS_MATCH` with `matches` array — present candidates via AskUserQuestion. URL-encode titles containing `/`, `?`, or `#`.

> **Sources:** CLAUDE.md §Shelving & Rejection, §Git Workflow
>
> **Hub API:** Source `scripts/hub-client.sh` for all API operations. Provides `hub_get()`, `hub_post()`, `hub_patch()`, `hub_transition()` with 3-retry exponential backoff. See `.claude/skills/hub-api-helpers.md` for idempotency notes.
>
> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT).

> **Distinction from /cancel:** `/cancel` transitions a story to `canceled` status (terminal -- story will not be worked on). `/shelve` transitions a story back to `ready_to_pull` status with a Revision Required section so another session can pick it up and continue the work. Use `/cancel` when the story itself is no longer needed; use `/shelve` when the current session cannot finish but the work should continue.

---

## Step 1: Look Up Story

Look up story using path-based resolution:
```bash
source scripts/hub-client.sh
hub_get "/api/v1/stories/$ARGUMENT"
```
- **200** → story found. Extract UUID (`data.id`), status, title from response.
- **404** → report not found. STOP.
- **409** → ambiguous title match. Parse `error.matches` array, present candidates via AskUserQuestion.

**Reject if:**
- Story not found (404)
- Story is NOT in `in_progress` or `claimed` status -- shelving only applies to active work. Report: "Story STORYID is in [status] -- only in_progress or claimed stories can be shelved."

---

## Step 2: Detect Shelvement Path

Check for uncommitted code changes:
```bash
git status --porcelain -- backend/src/ frontend/src/ tests/
```

### Decision Table

| Uncommitted changes in `backend/src/`, `frontend/src/`, `tests/`? | Path |
|-------------------------------------------------------------------|------|
| Yes -- modified/added/deleted files detected | **Path 1: Uncommitted** (Step 3a) |
| No -- working tree clean for those paths | **Path 2: Committed-but-incomplete** (Step 3b) |

---

## Step 3a: Shelve -- Uncommitted Changes

> Code has NOT been committed to main. Safe to revert.

1. **Revert code changes:**
   ```bash
   git checkout -- backend/src/ frontend/src/ tests/ 2>&1
   ```
   This preserves documentation and story edits (docs/, .claude/, stories/). **Capture stderr** for error reporting.

   **If revert fails (STOP tier):** Output `❌ STOP: git checkout revert failed — [stderr output]. Files that failed to revert: [list from git status].` Use AskUserQuestion with options: "Retry revert" / "Manual revert (I will fix)" / "Abort shelve". Do NOT proceed to Step 3a.2.

2. **Verify revert succeeded:**
   ```bash
   git status --porcelain -- backend/src/ frontend/src/ tests/
   ```
   If any changes remain, STOP and report.

3. **Log shelving in story's Execution Log** via PATCH:
   ```bash
   source scripts/hub-client.sh
   hub_patch "/api/v1/stories/$STORY_UUID" '{"execution_log": "<existing log + shelving details>"}'
   ```

4. **Proceed to Step 4** (Release Lock + Transition).

---

## Step 3b: Shelve -- Committed-but-Incomplete

> Code is already committed to main. Do NOT revert-commit. Next session continues from committed state.

1. **Log status in story's Execution Log** via PATCH:
   ```bash
   source scripts/hub-client.sh
   hub_patch "/api/v1/stories/$STORY_UUID" '{"execution_log": "<existing log + shelving details>"}'
   ```

2. **Proceed to Step 4** (Release Lock + Transition).

---

## Step 4: Release Lock + Transition

0. **Discard Gate Keeper ledger buffer** (prevent stale entries leaking into future sessions):
   ```bash
   source .claude/hooks/lib/hub-query.sh
   rm -f "/tmp/claude-gate-keeper-buffer-$(resolve_marker_id).jsonl" 2>/dev/null
   ```

1. **Release lock** (clear lock metadata):
   ```bash
   source scripts/hub-client.sh
   hub_patch "/api/v1/stories/$STORY_UUID" '{"lock": null}'
   ```
   **Retry:** PATCH is **idempotent** -- safe to retry directly.

2. **Add Revision Required section** describing what was done and what remains:
   ```bash
   hub_patch "/api/v1/stories/$STORY_UUID" '{"revision_required": "<revision required content>"}'
   ```

3. **Transition story back to ready_to_pull:**
   ```bash
   hub_transition "$STORY_UUID" "ready_to_pull"
   ```
   **Retry:** Non-idempotent -- check current status before retry. If already `ready_to_pull`, skip.

4. **Report:**
   ```
   [title] shelved (STORYID). Path: [uncommitted/committed-but-incomplete].
   Story returned to ready_to_pull with Revision Required.
   ```

---

## Failure Handling

| Failure | Action |
|---------|--------|
| Hub API unreachable | Report with URL. STOP |
| Story not in `in_progress` or `claimed` | Report current status. STOP |
| `git checkout` revert fails | STOP. Report failed files. Use AskUserQuestion with options: "Retry revert" / "Manual revert" / "Abort shelve" |
| 409/422 on transition (state changed externally) | "Story state changed externally -- re-check via API." STOP |
| Lock release fails (4xx) | Log warning, continue with transition (lock is secondary) |

---

## Notes

- No gate stamps emitted by this skill (shelving is not a governance gate)
- No compliance review or drift review required for shelving
- No commit is made by this skill -- it only reverts or preserves existing state
- The Revision Required section is critical for the next session: it tells the incoming agent exactly where to resume
- If the user provides a reason for shelving, include it in the execution log. If not, use AskUserQuestion with options: "Provide shelving reason" / "No reason — proceed with shelve"
