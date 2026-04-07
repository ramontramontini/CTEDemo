# /run-all-tests — Rebase + Full Suite Run

**Usage:** `/run-all-tests`

> Canonical pre-commit test command. Rebases from origin/main first, then runs all 3 test suites sequentially. Ensures `SUITES-GREEN` stamp always reflects the latest main state.
>
> **When to use:** Before committing — replaces the manual 3-command suite sequence. The `/ship` and `/pull` skills reference this in Step 4 (pre-commit suite run).
>
> **What it does NOT do:** Per-AC TDD test runs. Use direct pytest/vitest commands for RED/GREEN/REFACTOR cycles during development.

---

## Step 1: Rebase from origin/main (Stash-Aware)

Fetch and rebase to integrate any commits pushed by other agents since the last rebase. Uses `safe_rebase` for dirty-worktree safety:

```bash
source .claude/hooks/lib/safe-rebase.sh
git fetch origin && safe_rebase . origin/main
```

If the worktree has uncommitted changes, `safe_rebase` stashes them, rebases, and restores automatically.

**On success (exit 0):** Report result to agent:
- If new commits pulled: `"Rebased: [N] commits from origin/main integrated."`
- If no-op: `"Already up to date with origin/main."`
- If rebase conflict (graceful): `"Rebase conflict — aborted, stash restored, running on stale code."` Proceed to test suites (tests should still pass against current code).

**On pop conflict (exit 1):** `"Stash pop conflict — uncommitted changes in git stash. Resolve conflicts before running suites."` Do NOT proceed to test suites.

**On fetch failure (network):** Report error and stop. Do NOT run suites against potentially stale code: `"git fetch failed — cannot verify origin/main freshness. Check network and retry."`

---

## Step 2: Run backend suite

```bash
cd backend && DATA_MODE=memory poetry run python -m pytest ../tests/backend -q --no-header --no-cov --tb=short -n auto --dist=loadscope
```

> **Quiet mode:** Suite-level runs use `-q --no-header --tb=short` to minimize context consumption (~50 lines vs ~7K with `-v`). Per-AC TDD runs retain `-v` for debugging feedback.
> **Parallel mode:** Suite-level runs use `-n auto --dist=loadscope` (pytest-xdist) to distribute test modules across CPU workers. `loadscope` preserves `asyncio_mode = auto` event loop isolation per module. Per-AC TDD runs remain sequential (no `-n` flag in pytest.ini addopts).

**On failure:** Report which tests failed and STOP. Do not proceed to API suite.

**On success:** Report pass count. `test-emitter.sh` (PostToolUse hook) automatically marks backend as passed.

---

## Step 3: Run API suite

```bash
cd backend && DATA_MODE=memory poetry run python -m pytest ../tests/api -q --no-header --no-cov --tb=short -n auto --dist=loadscope
```

**On failure:** Report which tests failed and STOP. Do not proceed to frontend suite.

**On success:** Report pass count. `test-emitter.sh` marks API as passed.

---

## Step 4: Run frontend suite

```bash
cd frontend && npx vitest run --reporter=dot
```

**On failure:** Report which tests failed and STOP.

**On success:** Report pass count. `test-emitter.sh` detects all 3 suites passed → emits `SUITES-GREEN @<origin/main SHA>` stamp to API.

---

## Step 5: Report

After all 4 steps complete:

**All GREEN:**
```
✅ All suites GREEN (backend: [N] | api: [N] | frontend: [N]).
SUITES-GREEN stamp emitted by test-emitter. Ready to commit.
```

**Any FAILED:**
```
❌ Suite [name] FAILED ([N] failures). Fix and re-invoke /run-all-tests.
```

---

## Step 5.5: SUITES-GREEN Stamp Verification (WARN tier)

> `test-emitter.sh` (PostToolUse hook) auto-emits `SUITES-GREEN` after all 3 suites pass. This step verifies the stamp was actually emitted — catches silent hook failures.

After Step 5 reports all GREEN, query the API to verify the SUITES-GREEN stamp was emitted:

```bash
source scripts/hub-client.sh
source .claude/hooks/lib/hub-query.sh
STORY_UUID=$(cat "/tmp/claude-active-story-uuid-$(resolve_marker_id)" 2>/dev/null)
if [ -n "$STORY_UUID" ]; then
  hub_get "/api/v1/stories/$STORY_UUID" | grep -q "suites_green"
fi
```

**If stamp NOT found (after ~5 seconds):** Output `⚠️ WARNING: Tests passed but SUITES-GREEN stamp not emitted — check test-emitter.sh hook. Manual: hub_record_test_results "$STORY_UUID" '["backend","api","frontend"]' "$(git rev-parse origin/main)"`. The commit-gate will block without this stamp.

**If no active story UUID (non-story test run):** Skip verification silently — stamp emission only applies to in_progress stories.

---

## Notes

> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT).

- **Stop on first failure:** No point running remaining suites if one fails. Agent fixes, then re-invokes `/run-all-tests` (which rebases again — ensuring freshness).
- **test-emitter.sh handles stamp emission:** This skill does NOT emit stamps directly. It runs the test commands; `test-emitter.sh` (PostToolUse hook) detects passes and emits `SUITES-GREEN` when all 3 are done. Step 5.5 verifies the stamp was actually emitted.
- **Manual runs still work:** Agents can still run suites manually. `test-emitter.sh` records `@sha` audit trail regardless. The skill is the recommended path for the rebase-first guarantee.
