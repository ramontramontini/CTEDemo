# L1 SDLC Enforcement Rules (Auto-Loaded)

> Enforcement supplements to CLAUDE.md. Full SDLC rules: CLAUDE.md §Core Rules, §Lifecycle, §TDD Standards, §Git Workflow, §Policies.
> L0+L1 rules are portable across projects. L2+L3 are project-specific.

---

## Enforcement-Only Rules

These rules add enforcement constraints beyond CLAUDE.md definitions:

- **BUG traceability:** BUG stories MUST populate `Source Story` metadata (drift traceability). Use `unknown — [justification]` if source cannot be identified. Bugs in completed stories = governance drift evidence. Log and trace
- **Done Means Done (Policy 11):** "Shipped" = `git log` shows commit + `git status` clean + story transitioned to `done` in DB (via API) + all gate stamps emitted. User can say "Prove it." — agent must run `git log -1` and `git status` to verify
- **Sequential Tasks (Policy 13):** MUST NOT start second task while first has uncommitted work
- **Research Log (Policy 18):** SDLC stories: standalone `RESEARCH-LOG-STORYID-TITLE.md` MUST exist in `docs/research/logs/` before transitioning to done
- **Init Confirmation (Visual):** The agent's FIRST response in every session MUST render the init status summary (rules loaded, board state, mode) to the user. Hook stdout (`prompt-init-gate.sh`) goes into `<system-reminder>` tags — invisible to the user. The agent MUST relay it. Applies to both auto-init (hook) and manual `/init`

---

## Structural Hook Enforcement

> **API-backed governance:** All governance hooks query gate stamps on stories via the hub API (`$HUB_URL` — see L2 project stack for project-specific variable name) through `hub-query.sh` shared helper (5-second cache). No filesystem markers — gate stamps in the database are the single source of truth for governance state.
> **API-only story manipulation:** Direct Write/Edit/Bash writes to `stories/(doing|done|todo|canceled|archive)/` are BLOCKED by `story-gate.sh` and `story-bash-guard.sh`. All story content changes must go through `curl -X PATCH/POST` to the hub API.

### UserPromptSubmit Gates

- `prompt-init-gate.sh` (all prompts): Self-executing session init. First prompt: runs full bootstrap (git rebase, board-check, sync-agent-status, generate-launch-json), sets `/tmp` marker, injects context via stdout. Subsequent prompts: marker check only (fast no-op). **Fail-closed** on rebase conflict or unresolvable agent identity (exit 2). Whitelist: `/init`, `/resume`, `/help`

### PreToolUse Gates (HARD DENY)

- `forbidden-command-blocker.sh` (Bash): Blocks DB commands (alembic, psql, etc.) in agent worktrees
- `story-bash-guard.sh` (Bash): **HARD DENY** for Bash writes (>, cp, mv, sed -i, etc.) targeting `stories/(doing|done|todo|canceled|archive)/`
- `spec-content-guard.sh` (Bash): **HARD DENY** for `curl` POST/PATCH to `/api/v1/stories` when `spec` field contains a plan-file reference (≤200 chars + matches "See plan file" or "temp/plan-", case-insensitive). Defense-in-depth alongside Pydantic validators in `story_schemas.py`
- `spec-ceremony-gate.sh` (Bash `curl POST /api/v1/stories`): **HARD DENY** on `POST /api/v1/stories` (story creation) without `review_spec` stamp. Calls `GET /api/v1/agents/by-name/{name}/checks/spec-ceremony` (single API call). Allows PATCH (updates) and sub-path POSTs (transition, claim, gate-review, test-results, mark-ac-met)
- `commit-gate.sh` (Bash `git commit`): Two gates — (G1) `suites_green` stamp required + staleness detection (stamp emitted_at vs git commit timestamps of staged files), (G2) `review_code` stamp required (SDLC/Data/Maintenance exempt). Docs-only bypass when no code paths staged. Fail-closed when API unreachable
- `freshness-gate.sh` (Bash `git push`): Blocks push when local directives diverge from origin/main
- `push-gate.sh` (Bash `git push`): **HARD DENY** on push without `review_ship` stamp when hub API reports in_progress story. Non-story pushes pass through. Fail-closed when Gate Engine unreachable (legacy fallback removed)
- `epic-ceremony-gate.sh` (Bash `curl POST /api/v1/stories`): **HARD DENY** when epic ceremony incomplete. Calls `GET /api/v1/epics/{epic_id}/checks/ceremony-ready` (single API call). Fail-open if hub API unreachable. Defense-in-depth — primary enforcement is in the API endpoint (`POST /api/v1/stories` returns 422 `EPIC_CEREMONY_REQUIRED`)
- `directive-protection.sh` (Write/Edit): Blocks Write/Edit to protected directive files (CLAUDE.md, `.claude/rules/`, `docs/templates/`, `docs/architecture/`). Calls `GET /api/v1/agents/by-name/{name}/checks/directive-write` (single API call). **HARD DENY** when no sdlc/maintenance/refactoring story in_progress. Advisory (allow with warning) when qualifying story is active. Fail-closed on API errors
- `story-gate.sh` (Write/Edit): Blocks production code without in_progress story. **Blocks all writes to story cache directories** (API-only). Queries hub API for active story status. Fail-open when Gate Engine unreachable (legacy fallback removed)
- `plan-gate.sh` (Write/Edit): Queries API for `review_plan` stamp on active story. Cross-session fallback: checks spec + ACs + status >= in_progress. Gate 2: mandatory structured fields check (context, goal)
- `spec-review-gate.sh` (ExitPlanMode): Blocks ExitPlanMode without `review_spec` stamp on specifying/spec_complete story. Queries Gate Engine via `hub_check_gate()`. **No escape hatch** — spec-review is mandatory. Discuss-mode (no specifying story) exempted. Fail-closed when Gate Engine unreachable (legacy fallback removed)

### PostToolUse Emitters & Trackers

- `test-emitter.sh` (Bash): Detects test suite pass (pytest/vitest), tracks per-suite state in `/tmp`. When all 3 suites pass → resolves `origin/main` SHA → POSTs test results with `@<sha>` audit trail to API via `POST /api/v1/stories/{uuid}/test-results` (entity internally emits SUITES-GREEN stamp). Use `/run-all-tests` skill to guarantee rebase-before-suites freshness
- **Gate Keeper direct API call** (Agent): Gate Keeper calls `POST /api/v1/stories/{id}/gate-review` directly after reaching a verdict. spec-review PASS → `review_spec` + `review_plan` stamps. code-review PASS → `review_code`. ship-review PASS → `review_ship`. Verdict recorded atomically with stamps. JSONL ledger buffered by Gate Keeper agent
- `session-heartbeat.sh` (Bash/Write/Edit/Agent/ExitPlanMode/TodoWrite/AskUserQuestion): Clears stale awaiting_input signals. Prevents "stuck awaiting input" status
- `intervention-poll-hook.sh` (Bash/Write/Edit/Agent/ExitPlanMode): Consistency with PostToolUse entries
- `todo-capture.sh` (TodoWrite): Captures TodoWrite progress for story tracking

### Stop Gates

- `stop-keepalive-cleanup.sh`: Session exit cleanup — kills keepalive process, removes PID/heartbeat files, clears test suite tracking, clears agent signal via API. Fail-open (always exits 0)
- `stop-clean-worktree.sh`: Blocks session exit if worktree has uncommitted tracked files or untracked `docs/`/`.claude/` files
- `stop-test-gate.sh`: Runs `run-tests.sh` (all 3 suites) **only if uncommitted code changes exist on code paths** (`backend/src/`, `frontend/src/`, `tests/`) — blocks session exit on test failure. Skips tests when worktree is clean on code paths

---

## Policy 10: Anti-Rationalization
ALL changes go through the full workflow. The agent's assessment of change size is IRRELEVANT to workflow requirements. Banned rationalization phrases consolidated in CLAUDE.md §Identity & Communication.

If user says "just quickly do X" — respond: "This requires a story and plan. Should I create one?"

---

## Policy 12: Session Fatigue & Override Tracking
- **1-3 stories:** Normal workflow.
- **4-6 stories:** Re-read CLAUDE.md before each new plan.
- **7+ stories:** Warn user: "Extended session — drift risk elevated. Consider new session."

**Governance Override Counter (Tier 2 only):**
- Tier 1 and 1.5 disagreements are professional discourse, not overrides — they are NOT counted
- Track Tier 2 override count per session (resets on new session, NOT on new story)
- **3+ overrides:** Warn: "3 governance overrides this session. Consider reviewing design direction."
- **5+ overrides:** Escalate: "Override threshold exceeded. Recommend new session with fresh context." — prepend to every subsequent response
- Report override count in story completion summary (see `/ship` Step 9)

---

## Gate Stamps
> Full table: CLAUDE.md §Policy 9 (3-class taxonomy). User: APPROVED-SPEC, EPIC_APPROVED. Agent evidence: PLAN, WIREFRAME, RED, GREEN, SUITES-GREEN. Gate Keeper: GATE-SPEC, GATE-PLAN, GATE-CODE, DOCS, COMPLIANCE, DRIFT, GATE-SHIP, SHIPPED
