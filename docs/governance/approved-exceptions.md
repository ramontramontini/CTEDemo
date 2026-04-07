# Approved Exceptions to BANNED Patterns

> Each exception MUST be approved via an SDLC story. The story goes through full upstream (spec-review + ExitPlanMode approval).
> When an approved exception exists, the agent treats that specific pattern+context as Tier 2 (logged override) instead of Tier 3 (refuse).
> See `.claude/rules/02-L1-code-quality.md` §STRICTLY BANNED for the authoritative BANNED list.

| Story ID | Pattern Exception | Context | Rationale | Approved Date |
|----------|------------------|---------|-----------|---------------|

---

## Bootstrap Exceptions

> These are one-time exceptions for changes required to make the SDLC itself operational.
> They exist outside the normal story workflow because the workflow depends on them.

| Date | Change | Justification |
|------|--------|---------------|
| 2026-03-05 | Created `start.sh` (unified service launcher) | Cannot create stories without a running API. `dev.sh` and `prod-local.sh` had `.env` sourcing bugs that prevented starting the hub correctly. `start.sh` replaces both with correct config handling. Bootstrap circularity: fixing the SDLC requires the SDLC to be working. |
| 2026-03-05 | Fixed main `.env` for hub operation | Main's `.env` had agent-worktree values (port 8001, wrong CORS, no EUPRAXIS_HUB_URL). Skills default to port 8000 and need hub URL. Without this fix, no skill can reach the API. |
| 2026-03-05 | Updated `.env.example` with EUPRAXIS_HUB_URL, CORS_ORIGINS, FRONTEND_PORT | Aligning the example with actual required configuration for dogfooding. |
