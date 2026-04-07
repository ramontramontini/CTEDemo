# API Guide — CTEDemo

> REST API patterns, error handling, and conventions for the CTEDemo backend.

---

## API Structure

```
/api/v1/
├── stories/          # Story CRUD + state transitions
├── epics/            # Epic CRUD + story listing
├── agents/           # Agent registration + status
├── queue/            # Queue orchestration (claim/release/complete)
├── board/            # Board aggregate (cross-aggregate read)
├── ws/events         # WebSocket event stream (real-time)
├── projects/         # Project configuration
├── conversations/    # Agent conversation management
├── metrics/          # KPI computation + daily snapshots
├── tests/            # Test runner (execute suites, SSE stream, status)
├── dev/              # Development utilities (memory mode)
└── health            # Health check (no versioning)
```

---

## Authentication

**Middleware:** `TokenAuthMiddleware` in `backend/src/infrastructure/middleware/auth.py`.

**Modes:**
- `DATA_MODE=memory` — all auth bypassed (agent worktrees, local dev frictionless)
- `DATA_MODE=db` — Bearer token required on all `/api/v1/` endpoints (main worktree, production)

**Token configuration:** `EUPRAXIS_AUTH_TOKENS` env var with `machine_id:token` pairs (comma-separated). Parsed by `parse_auth_tokens()` into `{token → machine_id}` map.

**HTTP requests:** `Authorization: Bearer <token>` header. Middleware resolves machine_id onto `request.state.machine_id`.

**WebSocket:** Token via `?token=<token>` query parameter (WS doesn't support custom headers). Validated directly in `ws_events()` endpoint — `BaseHTTPMiddleware` does not intercept WebSocket connections.

**Exempt endpoints:** `/health`, `/docs`, `/redoc`, `/openapi.json`, `/`, `OPTIONS` preflight.

**Frontend:** Axios request interceptor adds `Authorization: Bearer <token>` when `VITE_API_TOKEN` env var is set.

---

## Conventions

### URL Patterns
- **Collection:** `GET /api/v1/stories` — list with pagination
- **Resource:** `GET /api/v1/stories/{id}` — single item
- **Create:** `POST /api/v1/stories` — create new
- **Update:** `PUT /api/v1/stories/{id}` — full update
- **Partial:** `PATCH /api/v1/stories/{id}` — partial update
- **Delete:** `DELETE /api/v1/stories/{id}` — soft delete
- **Action:** `POST /api/v1/stories/{id}/transition` — state change

### Response Format
```json
{
  "data": { ... },
  "meta": {
    "total": 42,
    "page": 1,
    "per_page": 20
  }
}
```

### Error Format
```json
{
  "error": {
    "code": "STORY_BLOCKED",
    "message": "Story cannot transition to doing: unmet dependencies",
    "details": {
      "blocked_by": ["story-id-1", "story-id-2"]
    }
  }
}
```

---

## HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success (GET, PUT, PATCH) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request (validation failure) |
| 404 | Not Found |
| 409 | Conflict (lock contention, invalid state transition) |
| 422 | Unprocessable Entity (business rule violation) |
| 500 | Internal Server Error |

---

## Pagination

```
GET /api/v1/stories?page=1&per_page=20&sort=created_at&order=desc
```

Default: `page=1`, `per_page=20`, `sort=created_at`, `order=desc`

---

## Filtering

```
GET /api/v1/stories?status=todo&epic=CTEDemo_Boot
GET /api/v1/agents?available=true
```

---

## API Contract Changes

When modifying API responses:
1. Update Pydantic response model
2. Update frontend TypeScript interface
3. Update serializer if applicable
4. Update tests (backend + API + frontend)
5. All in the same commit

---

## Dependency Injection

All aggregate routers use `Depends()` to inject repositories from `backend/src/api/dependencies.py`:

```python
from backend.src.api.dependencies import get_story_repository
from backend.src.domain.story.repository import StoryRepository

@router.get("")
async def list_stories(
    repo: StoryRepository = Depends(get_story_repository),
):
    ...
```

Provider creates repos based on `settings.data_mode` (memory vs db). One function per aggregate: `get_story_repository()`, `get_epic_repository()`, etc.

---

## Error Handling

### Centralized Domain Error Handlers

Domain exceptions are mapped to HTTP responses via `register_domain_error_handlers(app)` in `backend/src/api/error_handlers.py`, registered in `main.py`:

| Domain Exception | HTTP Status | Error Code |
|-----------------|-------------|------------|
| `InvalidTransitionError` | 409 | `INVALID_TRANSITION` |
| `StoryNotAvailableError` | 409 | `STORY_NOT_AVAILABLE` |
| `SelfDependencyError` | 422 | `SELF_DEPENDENCY` |
| `InvalidEpicStateError` | 409 | `INVALID_EPIC_STATE` |
| `DuplicateStoryError` | 409 | `DUPLICATE_STORY` |
| `StoryNotFoundError` (epic) | 404 | `STORY_NOT_IN_EPIC` |
| `DuplicateEpicNameError` | 409 | `DUPLICATE_EPIC_NAME` |
| `InvalidAgentStateError` | 409 | `INVALID_AGENT_STATE` |
| `AlreadyClaimedError` | 409 | `ALREADY_CLAIMED` |
| `AgentBusyError` | 409 | `AGENT_BUSY` |
| `WipLimitExceededError` | 429 | `WIP_LIMIT_EXCEEDED` |
| `NotClaimedError` | 409 | `NOT_CLAIMED` |

Routers let domain errors propagate — no inline try/except. Pydantic `field_validator` handles input validation (422) at the schema boundary.

### Exception Class Hierarchy

Standard exception pattern for all API errors:

```python
class APIException(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class NotFoundError(APIException):
    """Resource not found (404)."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} with identifier '{identifier}' not found", 404)

class ConflictError(APIException):
    """Resource conflict (409)."""
    def __init__(self, message: str):
        super().__init__(message, 409)

class BusinessRuleViolation(APIException):
    """Business rule violation (422)."""
    def __init__(self, message: str):
        super().__init__(message, 422)
```

Domain-specific exceptions (e.g., `InvalidTransitionError`, `StoryNotAvailableError`) are mapped to HTTP codes via the centralized handler table above. `APIException` subclasses are for infrastructure-level errors that don't originate from domain logic.

### Structured 500 Responses

Unhandled exceptions return structured JSON with traceability information:

```json
{
  "error": "Internal server error",
  "detail": "ExceptionType: error message",
  "errorId": "req-a1b2c3d4",
  "errorType": "ExceptionType",
  "context": "POST /api/v1/stories"
}
```

**Global catch-all handler:**
- Generates unique `errorId` (`req-{uuid4().hex[:8]}`) for each unhandled exception
- Logs with structlog: error message, type, ID, method, path, full traceback
- Returns structured JSON — never exposes stack traces to the client
- `errorId` enables log correlation for support/debugging

### Pattern: No Try/Except in Routers

```python
# GOOD — domain errors propagate to centralized handlers
story.transition_to(target)

# BAD — catching domain errors inline
try:
    story.transition_to(target)
except InvalidTransitionError as e:
    return JSONResponse(status_code=409, ...)
```

---

## Serialization

Entity-to-dict mapping via explicit serializer functions in `backend/src/api/v1/serializers/`:

- `story_serializer.py` — `story_to_response(story: Story) -> dict`
- `epic_serializer.py` — `epic_to_response()` (list) and `epic_to_detail_response()` (detail with story summaries)
- `agent_serializer.py` — `agent_to_response(agent: Agent) -> dict`
- `board_serializer.py` — `assemble_board(stories, epics, agents) -> dict` (pure function, cross-aggregate)

Serializers handle: UUIDs → strings, datetimes → ISO 8601, enums → `.value`, nested VOs → dicts, derived properties (e.g., `phase`).

---

## Pydantic DTOs

Request validation schemas in `backend/src/api/v1/schemas/`:

- `story_schemas.py` — `CreateStoryRequest`, `UpdateStoryRequest`, `TransitionRequest`, `ClaimRequest`, `ShelveRequest`
- `epic_schemas.py` — `CreateEpicRequest`, `UpdateEpicRequest`, `AddStoryRequest`
- `agent_schemas.py` — `RegisterAgentRequest`, `StartWorkingRequest`
- `queue_schemas.py` — `QueueAgentRequest` (shared by claim/release/start/complete), `RunStoryResponse`, `BoardSummaryResponse`, `BoardSummaryStoryItem`
- `board_schemas.py` — `BoardResponse`, `BoardEpicResponse`, `StatusGroupedStories`, `BoardStorySummary`, `BoardAgentResponse`, `QueueStatsResponse`
- `event_schemas.py` — `BaseEvent`, `WelcomeEvent`, `StoryTransitionEvent`, `AgentStatusEvent`, `AgentOutputEvent`, `QueueUpdateEvent` (WebSocket event DTOs) + `build_story_event()`, `build_agent_event()` helpers

Use `field_validator` for business-level input validation (enum values, UUID format, non-empty strings).

---

## Implemented Endpoints

### Story Aggregate (`/api/v1/stories`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/stories` | 200 | List with ?status, ?type, ?epic_id, ?page, ?per_page |
| GET | `/api/v1/stories/{id}` | 200, 404 | Get single story |
| POST | `/api/v1/stories` | 201, 422 | Create via StoryHome.create() |
| PATCH | `/api/v1/stories/{id}` | 200, 404 | Update content fields only |
| POST | `/api/v1/stories/{id}/transition` | 200, 404, 409 | State machine transition |
| POST | `/api/v1/stories/{id}/claim` | 200, 404, 409 | Claim for agent |
| POST | `/api/v1/stories/{id}/release` | 200, 404, 409 | Release back to READY_TO_PULL |
| POST | `/api/v1/stories/{id}/shelve` | 200, 404, 409 | Shelve to SPEC_COMPLETE |
| POST | `/api/v1/stories/{id}/cancel` | 200, 404, 409 | Cancel from non-terminal |
| POST | `/api/v1/stories/{id}/replan` | 200, 404, 409 | Mark for replan (sets needs_replan flag) |
| POST | `/api/v1/stories/{id}/gate-stamps` | **410 Gone** | **REMOVED** — use gate-review or test-results |
| POST | `/api/v1/stories/{id}/gate-review` | 200, 404, 422 | Composite gate verdict + stamp emission |
| POST | `/api/v1/stories/{id}/test-results` | 200, 404, 422 | Record test results (entity emits SUITES-GREEN) |
| POST | `/api/v1/stories/{id}/gate-verdicts` | 200, 404, 422 | Record a gate verdict |
| POST | `/api/v1/stories/{id}/mark-ac-met` | 200, 404, 422 | Mark an AC as met |
| POST | `/api/v1/stories/{id}/compliance` | 200, 404, 422 | Submit compliance checklist (replace semantics) |
| POST | `/api/v1/stories/{id}/execution-log` | 200, 404, 422 | Submit execution log entries (replace semantics) |
| POST | `/api/v1/stories/{id}/assign-upstream` | 200, 404 | Assign agent for upstream work |
| POST | `/api/v1/stories/{id}/ship-finalize` | 200, 400, 404, 409, 422 | Atomic ship + done transition |

#### Gate Stamps

> **DEPRECATED:** `POST /api/v1/stories/{id}/gate-stamps` returns **410 Gone**. All stamp emission now goes through `POST /api/v1/stories/{id}/gate-review` (Gate Keeper stamps) or `POST /api/v1/stories/{id}/test-results` (SUITES-GREEN stamp). The schema below is retained for reference only.

**Endpoint:** `POST /api/v1/stories/{id}/gate-stamps` **(410 Gone)**

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token_type` | string | Yes | Must be a valid key in `GATE_STAMP_TYPE_MAP` (see table below) |
| `value` | string | Yes | Stamp message/content (e.g., `"pass"`, `"12 tests passing"`) |
| `emitted_at` | ISO 8601 datetime | No | Override timestamp. Defaults to server `utcnow()` if omitted |

**Response:** Full story serialization (same shape as `GET /api/v1/stories/{id}`).

**Valid `token_type` Values:**

> Authoritative source: `GateStampType` enum in `backend/src/domain/story/enums.py`. The map is generated dynamically via `GATE_STAMP_TYPE_MAP`.

| token_type | Enum Value | Class | Phase | Description |
|------------|-----------|-------|-------|-------------|
| `APPROVED-SPEC` | `approved_spec` | User | Upstream | User approved spec in ExitPlanMode |
| `PLAN` | `plan` | Agent | Upstream | Agent wrote execution plan |
| `WIREFRAME` | `wireframe` | Agent | Upstream | Agent drew wireframes |
| `RED` | `red` | Agent | Downstream | Failing test written (TDD) |
| `GREEN` | `green` | Agent | Downstream | Tests passing (TDD) |
| `SUITES-GREEN` | `suites_green` | Agent | Downstream | All suites pass (pre-commit) |
| `DOCS` | `docs` | Gate Keeper | Downstream | Documentation verified |
| `COMPLIANCE` | `compliance` | Gate Keeper | Downstream | Compliance checklist verified |
| `SHIPPED` | `shipped` | Gate Keeper | Downstream | Post-push verification |
| `DRIFT` | `drift` | Gate Keeper | Downstream | Drift review result |
| `REVIEW-SPEC` | `review_spec` | Gate Keeper | Upstream | Combined upstream spec review |
| `REVIEW-PLAN` | `review_plan` | Gate Keeper | Upstream | Combined upstream plan review |
| `REVIEW-CODE` | `review_code` | Gate Keeper | Downstream | Code review |
| `REVIEW-SHIP` | `review_ship` | Gate Keeper | Downstream | Ship review |

**Convenience Aliases** (map to the same enum member):

| Alias | Maps To |
|-------|---------|
| `GATE-SPEC` | `REVIEW-SPEC` |
| `GATE-PLAN` | `REVIEW-PLAN` |
| `GATE-CODE` | `REVIEW-CODE` |
| `GATE-SHIP` | `REVIEW-SHIP` |

**Behavioral Rules:**

1. **Idempotency:** Emitting a stamp with an existing `token_type` updates the existing stamp (value + emitted_at) rather than creating a duplicate. Safe to retry.
2. **Ordering Prerequisites:** `REVIEW-*` stamps require prior stamps:
   - `REVIEW-PLAN` requires `REVIEW-SPEC`
   - `REVIEW-CODE` requires `REVIEW-SPEC` + `REVIEW-PLAN`
   - `REVIEW-SHIP` requires `REVIEW-SPEC` + `REVIEW-PLAN` (all types) + `REVIEW-CODE` (code types only)
   - Re-emission (updating an existing stamp) skips prerequisite checks
3. **Status-Phase Validation:** Stamps are rejected on closed statuses (`done`, `canceled`). Exception: `SHIPPED` is in `POST_DONE_STAMPS` and is accepted on `done` stories. Downstream stamps (RED, GREEN, etc.) require `in_progress` status.
4. **Auto-Advance:** When DOR-required stamps (`REVIEW-SPEC` + `APPROVED-SPEC`) are all present, the story auto-advances from `spec_complete` to `ready_to_pull`.

**Error Responses:**

| HTTP Status | When |
|-------------|------|
| 200 | Stamp emitted (or updated) |
| 404 | Story not found |
| 409 | Status-phase conflict (e.g., stamp on done story, downstream stamp on non-in_progress) or stamp ordering violation |
| 422 | Invalid `token_type` (not in `GATE_STAMP_TYPE_MAP`) |

#### Compliance & Execution Log

**`POST /api/v1/stories/{id}/compliance`** — Submit compliance checklist items. **Replace semantics** — overwrites the entire compliance list, does not append.

**Request schema** (`SubmitComplianceRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `items` | array | Yes | Non-empty array of `ComplianceItemRequest` objects |
| `items[].label` | string | Yes | Checklist item description |
| `items[].checked` | boolean | Yes | Whether the item is checked/complete |
| `items[].na_reason` | string | No | Justification when item is not applicable |

**Example:**
```bash
curl -4 -X POST "$HUB_URL/api/v1/stories/$UUID/compliance" \
  -H "Content-Type: application/json" \
  -d '{"items": [
    {"label": "TDD: N/A — SDLC type", "checked": true},
    {"label": "API contract: N/A", "checked": true, "na_reason": "No production API changes"}
  ]}'
```

> **⚠️ PATCH `compliance_checklist` vs POST `/compliance`:** The PATCH endpoint accepts a `compliance_checklist` string field — this is a **different field** from the `compliance` array. The ship-readiness check (`check-ship-readiness.sh`) validates `.data.compliance` (the array). Always use `POST /compliance` to populate the ship-readiness field.

**`POST /api/v1/stories/{id}/execution-log`** — Submit structured execution log entries. **Replace semantics** — overwrites the entire log. All entries receive a uniform server-side timestamp.

**Request schema** (`SubmitExecutionLogRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entries` | array of strings | Yes | Non-empty array of log messages. Whitespace-only entries are filtered out |

**Example:**
```bash
curl -4 -X POST "$HUB_URL/api/v1/stories/$UUID/execution-log" \
  -H "Content-Type: application/json" \
  -d '{"entries": ["Task 1: Implemented feature X", "Task 2: Updated docs"]}'
```

**Response:** Both endpoints return the full story serialization (`StoryResponse`). Status codes: 200 (success), 404 (story not found), 422 (empty items/entries array).

### Epic Aggregate (`/api/v1/epics`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/epics` | 200 | List with ?status, ?page, ?per_page + progress |
| GET | `/api/v1/epics/{id}` | 200, 404 | Get with story summaries + progress |
| POST | `/api/v1/epics` | 201, 409, 422 | Create via EpicHome.create() |
| PATCH | `/api/v1/epics/{id}` | 200, 404 | Update title/goal (name immutable) |
| POST | `/api/v1/epics/{id}/complete` | 200, 404, 409 | Mark COMPLETE |
| POST | `/api/v1/epics/{id}/shelve` | 200, 404, 409 | Mark SHELVED |
| POST | `/api/v1/epics/{id}/stories` | 200, 404, 409 | Add story to epic |
| DELETE | `/api/v1/epics/{id}/stories/{story_id}` | 200, 404 | Remove story from epic |

### Agent Aggregate (`/api/v1/agents`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/agents` | 200 | List with ?status, ?available, ?page, ?per_page |
| GET | `/api/v1/agents/{id}` | 200, 404 | Get single agent |
| POST | `/api/v1/agents` | 201, 409, 422 | Register via AgentHome.register() |
| POST | `/api/v1/agents/{id}/heartbeat` | 200, 404 | Update heartbeat timestamp |
| POST | `/api/v1/agents/{id}/start-working` | 200, 404, 409 | Start working on story |
| POST | `/api/v1/agents/{id}/activate` | 200, 404, 409 | Activate (IDLE→WORKING) |
| POST | `/api/v1/agents/{id}/deactivate` | 200, 404, 409 | Deactivate (WORKING→IDLE) |
| POST | `/api/v1/agents/{id}/finish-working` | 200, 404, 409 | Deprecated — delegates to deactivate |
| POST | `/api/v1/agents/{id}/pause` | 200, 404, 409 | Pause work |
| POST | `/api/v1/agents/{id}/resume` | 200, 404, 409 | Resume work |
| POST | `/api/v1/agents/{id}/mark-stale` | 200, 404, 409 | Mark stale (admin) |
| POST | `/api/v1/agents/{id}/clear-signal` | 200, 404 | Clear stale remote_status, reset heartbeat. Status re-derives from scratch |
| POST | `/api/v1/agents/load` | 200, 400 | Scan worktrees at source path/URL. Validates explicit paths are bare repos or projects folders (400 `NOT_A_BARE_REPO` if not). Defaults to `.` |
| DELETE | `/api/v1/agents/{id}` | 204, 404, 409 | Deregister (idle/stale only) |

**Background Task:** `stale_detection_loop` runs on app startup, checks all agents every 60s. Agents with expired heartbeats (>5min) and dirty worktrees are marked STALE. Clean worktree + expired heartbeat transitions to IDLE (session ended normally). Heartbeat from IDLE agent auto-activates to WORKING. Cancelled on shutdown.

### Queue Orchestration (`/api/v1/queue`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/queue/board-summary` | 200 | Lightweight board summary: status counts + in_progress/available story lists |
| GET | `/api/v1/queue/ready_to_pull` | 200 | List READY_TO_PULL stories in FIFO order |
| POST | `/api/v1/queue/claim/{story_id}` | 200, 404, 409, 429 | Atomic claim (story→CLAIMED, agent→WORKING) |
| POST | `/api/v1/queue/release/{story_id}` | 200, 404, 409 | Atomic release (story→READY_TO_PULL, agent→IDLE) |
| POST | `/api/v1/queue/start/{story_id}` | 200, 404, 409 | Start execution (story→IN_PROGRESS) |
| POST | `/api/v1/queue/complete/{story_id}` | 200, 404, 409 | Complete with dependency cascade |
| POST | `/api/v1/queue/run-story/{story_id}` | 200, 400, 404, 422 | Launch agent session — phase-detected: specifying→`/spec`, ready_to_pull→claim+`/pull`. Returns `RunStoryResponse` (agent_id, conversation_id, prompt). Starts background monitor to auto-kill terminal tabs on story completion |

**Cross-aggregate:** Wraps `QueueService` domain service. Claim/release/complete modify both Story and Agent entities. Complete returns `newly_available` UUIDs from dependency cascade (SPEC_COMPLETE→READY_TO_PULL). Optional `?wip_limit=N` on claim (default 0 = unlimited).

### Board Aggregate (`/api/v1/board`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/board` | 200 | Complete board state — epics, stories, agents, queue stats |

**Cross-aggregate read:** Fetches all stories, epics, and agents in one call. Assembly via pure function `assemble_board()` in `board_serializer.py`. Response shape:
- `epics[]` — each with `stories` grouped by status (6 buckets), `progress` ({done, total, percentage})
- `unassigned_stories` — stories without epic_id, same status grouping
- `agents[]` — sorted by name, each with `current_story` ({id, title} or null)
- `queue_stats` — available_count, wip_count (CLAIMED + IN_PROGRESS), done_today_count

**`BoardStorySummary` fields:** `id`, `story_id`, `title`, `type`, `status`, `class_of_service`, `agent_name`, `agent_status` (resolved from agent entity), `summary` (first 120 chars of goal, word-boundary truncated), `elapsed_seconds` (contextual: age for queue statuses, processing time for in_progress, lead time for done), `dependency_count`, `dependencies_met`, `ac_met` (count of acceptance criteria marked met), `ac_total` (total acceptance criteria count).

Terminal stories (ARCHIVED/CANCELED) excluded from display and queue stats but included in epic progress computation and dependency resolution. Stories sorted by `created_at` ascending (FIFO) within each status bucket.

### Metrics (`/api/v1/metrics`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/metrics/summary` | 200 | All dashboard KPIs in one call |
| GET | `/api/v1/metrics/lead-time` | 200 | Lead time with ?days (default 30), by_type breakdown |
| GET | `/api/v1/metrics/cycle-time` | 200 | Cycle time with ?days (default 30), by_type breakdown |
| GET | `/api/v1/metrics/drift-rate` | 200 | Drift rate with ?days (default 30), daily trend array |
| POST | `/api/v1/metrics/snapshot` | 201 | Compute and store daily snapshot (upsert by date) |

**Cross-aggregate read:** All GET endpoints inject `StoryRepository` and compute metrics live from Story data. POST /snapshot also injects `MetricSnapshotRepository` to persist the computed snapshot. No Pydantic request schemas needed — GET endpoints use query params, POST has no body.

**Response shapes:**
- `summary` — `{wip_count, shipped_today, avg_lead_time, drift_rate, throughput_per_week, throughput_trend}`
- `lead-time` / `cycle-time` — `{average_hours, story_count, by_type: {type: {average_hours, count}}}`
- `drift-rate` — `{rate, process_count, defect_count, trend: [{date, rate}]}`
- `snapshot` — `{id, date, wip_count, shipped_count, lead_time_avg_hours, cycle_time_avg_hours, drift_rate, process_drift_count, defect_drift_count, throughput_weekly, created_at}`

### Monitor (`/api/v1/monitor`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/monitor/worktrees` | 200, 500 | Worktree monitor dashboard (KPIs, worktree table, recent commits) |

**Query params:** `?project_id=UUID` — optional. Filters worktrees to agents belonging to the specified project. Omit for all worktrees.

**Cross-aggregate read:** Injects `AgentRepository`, `StoryRepository`, `ProjectRepository`, and `MonitorInspector` (worktree manager). Builds a reverse map from `project.agent_ids` to resolve `project_id` per worktree. When `project_id` is provided, filters to agents belonging to that project before inspecting worktrees.

**Response shape:** `{worktrees: [{name, branch, is_dirty, is_missing, behind_count, agent_status, current_story, last_commit_message, last_commit_at, project_id}], summary: {total, clean_count, dirty_count, behind_total, active_count}, recent_commits: [{hash, message, committed_at}]}`

**Error:** Returns 500 with `MONITOR_ERROR` code if worktree inspection fails.

### Intelligence (`/api/v1/intelligence`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/intelligence/drift-report` | 200, 422 | Aggregated drift report with classification, weighted rate, trend, bug tracing |
| GET | `/api/v1/intelligence/audit` | 200, 422 | Project-level compliance audit across completed stories |
| GET | `/api/v1/intelligence/audit/{story_id}` | 200, 404, 422 | Per-story compliance audit |
| POST | `/api/v1/intelligence/retrospective` | 200, 422 | Trigger retrospective analysis |
| GET | `/api/v1/intelligence/retrospective` | 200 | List all past retrospectives |
| GET | `/api/v1/intelligence/retrospective/{retro_id}` | 200, 404 | Get specific retrospective |
| PATCH | `/api/v1/intelligence/proposals/{proposal_id}` | 200, 404, 422 | Accept or reject a proposal |

**Query params:** `?days=N` (1-365, default 30 for drift/audit, 14 for retrospective). `?project_id=UUID` — optional on drift-report, audit, and retrospective POST. Filters to stories belonging to the specified project. Omit for all stories.

**Cross-aggregate read:** Drift report and audit inject `StoryRepository`, filter by `project_id` at endpoint level, then pass to domain services (`compute_drift_report`, `audit_project`). Retrospective additionally injects `RetrospectiveRepository` and `RetroAnalyzerPort`.

### Test Runner (`/api/v1/tests`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| POST | `/api/v1/tests/run` | 202, 400, 409, 422 | Start test run for selected suites |
| GET | `/api/v1/tests/run/{run_id}/stream` | 200, 404 | SSE stream of test execution events |
| GET | `/api/v1/tests/status` | 200 | Current run status (idle/running) + last run summary |

**Request (POST /tests/run):** `{"suites": ["frontend", "backend", "api", "e2e"]}` — `suites` optional, defaults to all four.

**SSE event types:** `run_started`, `suite_started`, `output_line`, `suite_completed`, `suite_error`, `run_completed`. Each event has `data` as JSON with `timestamp` field.

**Concurrency:** One test run at a time. `asyncio.Lock` + `_running` flag. Returns 409 if a run is already in progress. Lock is ephemeral (no stale locks after server restart).

**Subprocess execution:** Each suite runs sequentially via `asyncio.create_subprocess_exec` with 300s timeout. JSON output parsed from vitest (`--reporter=json`) and pytest (`--json-report`). Falls back to raw output on parse failure.

**Error codes:** `RUN_IN_PROGRESS` (409), `PREREQUISITES_MISSING` (422), invalid suite name (400).

### Development (`/api/v1/dev`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| POST | `/api/v1/dev/reset-data` | 200 | Reset memory state to initial seed |

### Filesystem (`/api/v1/filesystem`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| GET | `/api/v1/filesystem/browse` | 200, 400, 403 | Browse directories for worktree selection. Query param: `?path=~`. Returns `DirectoryEntry[]` with `is_bare_repo` indicator. Restricted to user's home directory |

**`DirectoryEntry` fields:** `name`, `path`, `is_dir`, `is_bare_repo` (true when directory contains `HEAD` or `.bare/HEAD`).

### WebSocket Events (`/api/v1/ws/events`)

| Method | Path | Status Codes | Description |
|--------|------|-------------|-------------|
| WS | `/api/v1/ws/events` | 101 (Upgrade) | Real-time event stream |

**Connection lifecycle:**
1. Client connects via WebSocket upgrade
2. Server sends `WelcomeEvent` with `message: "Connected to CTEDemo event stream"`
3. Client can send `{"type": "ping"}` → receives `{"type": "pong"}` (keepalive)
4. Server broadcasts domain events as they occur
5. On disconnect, connection is removed from active set

**Delivery model:** Fire-and-forget. No acknowledgment, no replay, no persistence. Clients must re-fetch board state via `GET /api/v1/board` on reconnect.

**Event types:**

| Event Type | Emitted By | Payload Fields |
|------------|-----------|----------------|
| `welcome` | WS connect | `type`, `message`, `timestamp` |
| `story_transition` | stories.py, queue.py | `type`, `story_id`, `title`, `from_status`, `to_status`, `agent_id?`, `epic_id?`, `timestamp` |
| `agent_status` | agents.py, queue.py | `type`, `agent_id`, `agent_name`, `from_status`, `to_status`, `story_id?`, `timestamp` |
| `agent_output` | (infrastructure only) | `type`, `agent_id`, `story_id?`, `lines`, `timestamp` |
| `queue_update` | queue.py | `type`, `available_count`, `wip_count`, `done_today_count`, `timestamp` |

**Emission points:** Events are broadcast AFTER successful entity save. Story/agent state changes in `stories.py` (5 endpoints), `agents.py` (6 endpoints), and `queue.py` (4 endpoints) all emit events via `ConnectionManager.broadcast()`.

**Infrastructure:** `ConnectionManager` singleton in `backend/src/api/v1/events/manager.py`. Event DTOs in `backend/src/api/v1/schemas/event_schemas.py`. WS endpoint in `backend/src/api/v1/ws.py`. DRY helpers: `build_story_event()`, `build_agent_event()` in event_schemas.py.
