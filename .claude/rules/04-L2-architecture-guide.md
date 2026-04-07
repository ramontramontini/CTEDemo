# L2 Architecture Guide — CTEDemo-Specific (Auto-Loaded)

> Per-project architecture patterns, test organization, cross-layer analysis, and migration conventions.
> L0+L1 rules are identical across projects. L2+L3 are project-specific.

---

## Test Organization

**Tests mirror the domain aggregate structure.** Group by domain concept, not by technical layer.

| Type | Location | Technology | Run |
|------|----------|------------|-----|
| Pure logic | `tests/frontend/{Domain}/` | Vitest (no JSX) | `cd frontend && npx vitest run` |
| Component | `frontend/src/__tests__/{Domain}/` | Vitest + RTL | `cd frontend && npx vitest run` |
| Backend | `tests/backend/{Domain}/` | pytest | `cd backend && python -m pytest ../tests/backend -v --no-cov` |
| API | `tests/api/{Domain}/` | pytest + httpx | `cd backend && python -m pytest ../tests/api -v --no-cov` |
| E2E | `tests/integration/{Domain}/` | Playwright | `npm run e2e` |

**`{Domain}` must match the aggregate name.** All tests for an aggregate live under the same folder — not scattered by technical type.

> **Test commands:** See `.claude/rules/03-L2-project-stack.md` §Test Commands for the canonical run commands per suite.

---

## Architecture & Code Patterns

**Clean Architecture:** Domain services > Application services > API endpoints. No business logic in frontend.

> **OO, SOLID, Design Patterns, Clean Code (L1):** `.claude/rules/02-L1-code-quality.md` (auto-loaded)

**CTEDemo aggregates:** `story/`, `epic/`, `agent/`, `project/`, `conversation/` + `shared/` (cross-aggregate types) + `services/` (cross-aggregate orchestration). Dependencies: `docs/domain/overview.md`

**TypeScript:** No `any`. Interfaces for all props. Max 200 lines per component, 50 lines per function.

> Deep-dive: `docs/architecture/code-quality.md` (SOLID, OOP, patterns, frontend, clean code)
> Backend patterns: `docs/architecture/backend-guide.md` (DB architecture, persistence, migrations)
> API patterns: `docs/architecture/api-guide.md`
> Frontend patterns: `docs/architecture/frontend-guide.md`
> UI standards: `docs/architecture/ui-standards.md`

---

<!-- EUPRAXIS:MANAGED:START -->
## Cross-Layer Impact Analysis (MANDATORY)

When a story modifies any production layer (`backend/src/`, `frontend/src/`), agents MUST trace cross-cutting dependencies **before** making changes. A single modification (e.g., adding a status, changing a field, modifying a filter) can ripple across multiple layers that must be updated together.

**Upstream (spec/plan):** The execution plan MUST identify all dependent layers that need coordinated changes. List specific files per layer. If no cross-cutting impact exists, state "single-layer change — no cross-cutting dependencies" with justification.

**Downstream (code):** All identified layers MUST be updated in the same commit. Partial updates (e.g., backend changed but frontend types not updated) are not acceptable.

**Layer checklist (bottom-up):**
| Layer | What to check |
|-------|--------------|
| Backend domain | Entity, Home, enums, VOs, repository |
| API | Endpoints, serializers, Pydantic schemas |
| Frontend data | `apiService.ts`, `types/index.ts`, React Query hooks |
| Frontend UI | Components, pages, utils that consume the data |
| Infrastructure | Migrations, config, seed data |
| Tests | All layers — backend, API, frontend, E2E (when applicable) |

**Enforcement:** Gate Keeper code-review (MODE 3) verifies cross-layer completeness by comparing the plan's declared layer list against the actual diff.

**Exemption:** SDLC/Data stories that don't touch production code (`backend/src/`, `frontend/src/`).

**Common cross-cutting dependency chains:**

1. **Board column/status changes** — frontend board utils (e.g., `boardUtils.ts` column maps) → frontend board components (e.g., `BoardLayout.tsx`, `BoardPage.tsx`, `StatusActions.tsx`) → backend board serializer + schemas (e.g., `board_serializer.py`, `board_schemas.py`) → backend story aggregate state machine (e.g., `entity.py`) → backend services (e.g., `dependency_resolver.py`, `queue_service.py`)

2. **Entity field addition** — backend aggregate (entity, home, enums, VOs) → persistence (repository, migration) → API layer (schemas, endpoint) → frontend data layer (`apiService.ts`, `types/index.ts`) → frontend consumers (components that render the field) → tests at each layer
<!-- EUPRAXIS:MANAGED:END -->

---

<!-- EUPRAXIS:MANAGED:START -->
## Alembic Migration Conventions
- **Naming:** `YYYYMMDD_HHMM_<revision>_<slug>.py` (timestamp-based, UTC)
- **Revision IDs (post-`000056`):** Hash-based, 12-char hex. Generate via `python3 -c "import secrets; print(secrets.token_hex(6))"`. Grandfathered: `001`–`039` (3-digit), `000040`–`000056` (6-digit), `e73e3dd8fef3` (hash) — do NOT extend the sequential numbering
- **`down_revision` lookup:** Find current head from the latest file: `ls -1 backend/alembic/versions/*.py | tail -1`, then extract the `revision = ` value. Never compute sequentially
- **Concurrent migrations:** Multiple agents get unique hash IDs but share the same `down_revision`, creating multiple heads. Resolve with `alembic merge heads` on main before `alembic upgrade head`
- **Mandatory:** Every story that changes a domain entity or SQLAlchemy model MUST include a migration in the same commit
- **Agent worktrees:** Never execute migrations in agent worktrees (`DATA_MODE=memory`). Main worktree runs migrations via `alembic upgrade head`. Files are committed in agent worktrees but not run until merged to main
- **Deep-dive:** `docs/architecture/backend-guide.md` §Database & Persistence Architecture
<!-- EUPRAXIS:MANAGED:END -->
