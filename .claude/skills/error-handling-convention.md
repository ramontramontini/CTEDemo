# Skill Error Handling Convention

> **Referenced by:** All 14 skills in `.claude/skills/*/SKILL.md`
> **Purpose:** Ensure no skill fails silently. Every failure must be visible to the user or explicitly classified as best-effort.

---

## 3-Tier Error Classification

Every operation in every skill MUST be classified into one of these tiers:

### STOP (Fatal)
Operation cannot continue — the skill halts immediately.

**Agent behavior:**
1. Output the error: `❌ STOP: [operation] failed ([detail]) — [impact]`
2. Do NOT proceed to subsequent steps
3. Include recovery action if applicable: `Recovery: [specific command or action]`

**When to classify as STOP:**
- Story creation/transition fails permanently (4xx)
- Git rebase conflict during commit/push
- Required env var missing (e.g., `EUPRAXIS_PROJECT_ID` empty before `hub_create_story`)
- Gate stamp verification fails (e.g., `review_ship` missing before push)
- UUID is empty/null when needed for API calls

---

### WARN (Degraded)
Operation failed but the skill can continue safely — user must see the impact.

**Agent behavior:**
1. Output: `⚠️ WARNING: [operation] failed ([detail]) — [impact] — [recovery: command or action]`
2. Continue to next step
3. Increment warning counter for completion summary

**Format:** `⚠️ WARNING: [what failed] ([HTTP status or error]) — [user-visible impact] — [recovery: exact command]`

**Examples:**
- `⚠️ WARNING: mark-ac-met failed for AC1 (API 500) — progress bar won't update — recovery: hub_post mark-ac-met $UUID AC1`
- `⚠️ WARNING: validate-agent-env.sh failed — missing EUPRAXIS_HUB_URL, VITE_DATA_MODE — recovery: check .env file`
- `⚠️ WARNING: EUPRAXIS_HUB_URL resolved from fallback (localhost:8000) — may be hitting wrong server — recovery: set EUPRAXIS_HUB_URL in .env`
- `⚠️ WARNING: hub_post render failed (API 500) — story file not rendered in hub — recovery: hub_post /api/v1/stories/$UUID/render`

**When to classify as WARN:**
- mark-ac-met fails (progress tracking is best-effort but user should know)
- Spec PATCH fails (ceremony continues but DB state incomplete)
- Compliance/execution-log POST fails (ship readiness affected)
- Env validation fails but session can continue (e.g., missing optional vars)
- SUITES-GREEN stamp not emitted after test pass (commit-gate will catch it, but user should know why)
- Multi-step finalization where one step fails but others succeed

---

### SILENT (Best-Effort)
Failure is expected or acceptable — no user-visible output needed.

**Agent behavior:**
1. Log internally only (no output to user)
2. Continue normally

**When to classify as SILENT:**
- Session capture (`hub_record_chat_history`) — best-effort by design
- `/tmp` file cleanup (`rm -f`) — idempotent, failure is harmless
- Gate Keeper ledger buffer discard — cleanup only
- Session heartbeat — background operation

---

## Completion Summary Rule

Every skill completion message MUST include warning count if any warnings were emitted during the run:

- **Zero warnings:** Normal completion message (no mention of warnings)
- **1+ warnings:** Append `| Warnings: [N]` to the completion summary

Example: `✅ [title] complete (STORYID). Commit: abc123f. AC: 3/3 | Tests: 15/15 | Warnings: 2`

---

## Env/Config Validation Patterns

Skills that depend on environment variables MUST validate them before use:

| Variable | Required By | If Missing |
|----------|------------|------------|
| `EUPRAXIS_PROJECT_ID` | `hub_create_story` | **STOP** — "EUPRAXIS_PROJECT_ID not set — check .env" |
| `EUPRAXIS_AGENT_NAME` | `hub_claim`, `hub_assign_upstream` | **WARN** — "Agent identity unknown — hub tracking disabled" |
| `EUPRAXIS_HUB_URL` | All hub API calls | **WARN** if resolved from fallback (not .env or env var) |
| `VITE_DATA_MODE` | Frontend operation | **WARN** — "VITE_DATA_MODE not set — frontend may fail" |
| `VITE_API_BASE_URL` | Frontend operation | **WARN** — "VITE_API_BASE_URL not set — frontend cannot reach API" |

**Resolution chain:** env var → `.env` file → hardcoded fallback (if any). If resolved from fallback, emit WARN so user knows the source.

---

## How to Add Error Handling to a Skill Operation

For each operation (API call, script, git command), add one of these patterns:

**STOP pattern:**
```
Execute [operation]. **If fails (non-transient):** output `❌ STOP: [operation] failed — [impact]` and halt. Do NOT proceed to Step N+1.
```

**WARN pattern:**
```
Execute [operation]. **If fails:** output `⚠️ WARNING: [operation] failed ([detail]) — [impact] — [recovery: command]` and continue to Step N+1.
```

**SILENT pattern:**
```
Execute [operation]. **If fails:** continue (best-effort, non-blocking).
```
