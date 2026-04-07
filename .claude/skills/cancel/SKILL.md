---
name: cancel
description: >
  Cancel a story via API. Handles uncommitted code revert if needed.
  Covers stories in todo/doing status — rejects done/archived/canceled.
---

# /cancel — Story Cancellation

**Usage:** `/cancel STORYID` or `/cancel Story Title`

> **Argument resolution:** The argument can be a **UUID**, **STORYID** (timestamp `YYYY-MM-DD.HH-MM-SS`), or a **story title** (any other string). Pass the argument directly as a path parameter — the API resolves it server-side (UUID → timestamp → title, case-insensitive with substring fallback). Single match → resolved. Zero matches → 404. Multiple title matches → 409 `AMBIGUOUS_MATCH` with `matches` array — present candidates via AskUserQuestion. URL-encode titles containing `/`, `?`, or `#`.

> **Sources:** CLAUDE.md §Abandonment & Rejection, §Git Workflow
>
> **Hub API:** Source `scripts/hub-client.sh` for all API operations. Provides `hub_get()`, `hub_post()` with 3-retry exponential backoff. See `.claude/skills/hub-api-helpers.md` for idempotency notes.
>
> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT).

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

**Reject if:** Story is already in done/archived/canceled status.

---

## Step 2: Handle Uncommitted Code (if doing)

If story is in `in_progress` or `claimed` status with uncommitted code changes:

1. Check `git status` for modified files in `backend/src/`, `frontend/src/`, `tests/`
2. If changes found: `git checkout -- backend/src/ frontend/src/ tests/ 2>&1` (preserves doc/story edits). **Capture stderr** for error reporting.
3. **If revert fails (STOP tier):** Output `❌ STOP: git checkout revert failed — [stderr output]. Files that failed to revert: [list].` Use AskUserQuestion with options: "Retry revert" / "Manual revert (I will fix)" / "Abort cancel". Do NOT proceed to Step 3.

If no uncommitted changes or story is in specifying/spec_complete/ready_to_pull: skip this step.

---

## Step 3: Cancel via API

```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/cancel" '{}'
```

**Retry:** Cancel is **non-idempotent** — before retry, `hub_get "/api/v1/stories/$STORY_UUID"` to check current status. If already `canceled`, skip.

**Errors:** 404/409 = permanent failure (exit 1, display API error). 5xx/network = transient (exit 2, retried by hub-client.sh).

---

## Step 4: Commit + Push + Reload

> Follow CLAUDE.md §Git Workflow

1. Commit: `sdlc: cancel story — [title] (STORYID)` + `Co-Authored-By: Claude <noreply@anthropic.com>`
2. Pull-rebase → Push → Reload
3. Report: "[title] canceled (STORYID)."

---

## Notes

- No drift review or compliance needed for cancellations
- Canceled stories can be reactivated via `POST /api/v1/stories/{id}/transition` with `{"target_status": "specifying"}`
