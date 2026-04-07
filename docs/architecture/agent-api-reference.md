# Agent API Contract Reference

> Explicit contracts for every hub API endpoint invoked by hooks, skills, scripts, and Gate Keeper.
> **Last verified:** 2026-03-28 | **Stories:** 2026-03-28.22-45-31, 2026-03-28.23-40-33

---

## Purpose

Agents (hooks, skills, scripts, Gate Keeper) invoke hub API endpoints via two wrapper libraries:
- **`scripts/hub-client.sh`** — used by skills and scripts (3x retry, 10s timeout)
- **`.claude/hooks/lib/hub-query.sh`** — used by hooks (no retry, 5s timeout, 5s cache)

This document is the single source of truth for what each endpoint expects and returns. When writing a new caller, reference this document — do not reverse-engineer from existing callers.

**Base URL:** `$EUPRAXIS_HUB_URL` (default: `http://localhost:8000`)

---

## 1. Caller-to-Endpoint Cross-Reference

### Hooks (`.claude/hooks/`)

| Hook | Endpoint | Method | Via |
|------|----------|--------|----|
| `session-heartbeat.sh` | `/api/v1/agents/{id}/status` | POST | Direct curl (by UUID) |
| `intervention-poll-hook.sh` | `/api/v1/agents/{id}/interventions` | GET | Direct curl (by UUID) |
| `test-emitter.sh` | `/api/v1/stories/{uuid}/test-results` | POST | `hub_record_test_results()` |
| `test-emitter.sh` | `/api/v1/stories/{uuid}/signals` | POST | `hub_emit_signal()` |
| `commit-gate.sh` | `/api/v1/stories/{uuid}/gates/{name}` | GET | `hub_check_gate()` |
| `commit-gate.sh` | `/api/v1/stories?status=in_progress` | GET | `hub_query_stories()` |
| `push-gate.sh` | `/api/v1/stories/{uuid}/gates/push` | GET | `hub_check_gate()` |
| `spec-ceremony-gate.sh` | `/api/v1/agents/by-name/{name}/checks/spec-ceremony` | GET | Direct curl |
| `spec-review-gate.sh` | `/api/v1/stories/{uuid}/gates/spec` | GET | `hub_check_gate()` |
| `spec-review-gate.sh` | `/api/v1/stories?status={status}` | GET | `hub_query_stories()` |
| `directive-protection.sh` | `/api/v1/agents/by-name/{name}/checks/directive-write` | GET | Direct curl |
| `story-gate.sh` | `/api/v1/stories/{uuid}/gates/code_write` | GET | `hub_check_gate()` |
| `plan-gate.sh` | `/api/v1/stories/{uuid}/gates/plan` | GET | `hub_check_gate()` |
| `epic-ceremony-gate.sh` | *(pattern detection only — no API call)* | — | grep on Bash command |
| `unified-reload-gate.sh` | `/health` | GET | Direct curl |
| `todo-capture.sh` | `/api/v1/stories?status=in_progress` | GET | `hub_query_stories()` |
| `todo-capture.sh` | `/api/v1/stories/{uuid}` | PATCH | `hub_patch()` (via hub-client.sh) |
| `awaiting-input-signal.sh` | `/api/v1/agents/by-name/{name}/status` | POST | Direct curl |
| `stop-keepalive-cleanup.sh` | `/api/v1/agents/by-name/{name}/status` | POST | Direct curl |

### Skills (`.claude/skills/`)

| Skill | Endpoint | Method | Via |
|-------|----------|--------|----|
| `/spec` | `/api/v1/stories` | POST | `hub_create_story()` |
| `/spec` | `/api/v1/stories/{uuid}/assign-upstream` | POST | `hub_assign_upstream()` |
| `/spec` | `/api/v1/stories/{uuid}` | PATCH | `hub_patch()` |
| `/spec` | `/api/v1/stories/{uuid}/gate-review` | POST | `hub_post()` (stamps as side effect) |
| `/spec` | `/api/v1/stories?status=specifying` | GET | `hub_get()` |
| `/pull` | `/api/v1/stories?status={status}` | GET | `hub_get()` |
| `/pull` | `/api/v1/stories/{uuid}/claim` | POST | `hub_claim()` |
| `/pull` | `/api/v1/stories/{uuid}/transition` | POST | `hub_transition()` |
| `/pull` | `/api/v1/stories/{uuid}` | PATCH | `hub_patch()` |
| `/pull` | `/api/v1/stories/{uuid}/mark-ac-met` | POST | `hub_post()` |
| `/pull` | `/api/v1/stories/{uuid}/gate-review` | POST | `hub_post()` (stamps as side effect) |
| `/ship` | `/api/v1/stories?status=in_progress` | GET | `hub_get()` |
| `/ship` | `/api/v1/stories/{uuid}/transition` | POST | `hub_transition()` |
| `/ship` | `/api/v1/stories/{uuid}/render` | POST | `hub_post()` |
| `/ship` | `/api/v1/stories/{uuid}` | PATCH | `hub_patch()` |
| `/ship` | `/api/v1/stories/{uuid}/gate-review` | POST | `hub_post()` (stamps as side effect) |
| `/batch` | `/api/v1/epics` | GET | `hub_get()` |
| `/batch` | `/api/v1/stories?epic_id={uuid}` | GET | `hub_get()` |
| `/batch` | `/api/v1/stories/{uuid}/claim` | POST | `hub_claim()` |
| `/batch` | `/api/v1/stories/{uuid}/transition` | POST | `hub_transition()` |
| `/resume` | `/api/v1/stories?status=in_progress` | GET | `hub_get()` |
| `/resume` | `/api/v1/stories/{uuid}/claim` | POST | `hub_claim()` |
| `/resume` | `/api/v1/stories/{uuid}` | PATCH | `hub_patch()` |
| `/cancel` | `/api/v1/stories` | GET | `hub_get()` |
| `/cancel` | `/api/v1/stories/{uuid}/cancel` | POST | `hub_post()` |
| `/shelve` | `/api/v1/stories` | GET | `hub_get()` |
| `/shelve` | `/api/v1/stories/{uuid}` | PATCH | `hub_patch()` |
| `/shelve` | `/api/v1/stories/{uuid}/transition` | POST | `hub_transition()` |
| `/next` | `/api/v1/stories?status=in_progress` | GET | `hub_get()` |
| `/next` | `/api/v1/queue/ready_to_pull` | GET | `hub_get()` |
| `/init` | `/api/v1/queue/ready_to_pull` | GET | via `board-check.sh` |

### Scripts (`scripts/`)

| Script | Endpoint | Method | Via |
|--------|----------|--------|----|
| `board-check.sh` | `/api/v1/queue/board-summary` | GET | Direct curl |
| `check-ship-readiness.sh` | `/api/v1/stories/{uuid}` | GET | `hub_get()` |
| `hub-client.sh` | *(wrapper — all endpoints)* | — | Provides `hub_get/post/patch` |
| `agent-keepalive.sh` | `/api/v1/agents/by-name/{name}/status` | POST | `hub_push_status()` |
| `sync-agent-status.sh` | `/api/v1/agents/by-name/{name}/status` | POST | `hub_push_status()` |
| `emit-gate-stamp.sh` | **REMOVED** (stub with migration error) | — | — |
| `backfill-gate-stamps.sh` | `/api/v1/stories?status=done` | GET | `hub_get()` |
| `backfill-gate-stamps.sh` | `/api/v1/stories/{uuid}/gate-review` | POST | `hub_post()` |
| `backfill-story-data.sh` | `/api/v1/stories?status=done` | GET | `hub_get()` |
| `backfill-story-data.sh` | `/api/v1/stories/{uuid}` | PATCH | `hub_patch()` |
| `backfill-todo-counts.sh` | `/api/v1/stories?status=done` | GET | `hub_get()` |
| `backfill-todo-counts.sh` | `/api/v1/stories/{uuid}` | PATCH | `hub_patch()` |
| `rename-agents.sh` | `/api/v1/agents?name={name}` | GET | Direct curl (**endpoint not implemented**) |
| `rename-agents.sh` | `/api/v1/agents/{uuid}` | PATCH | Direct curl (**endpoint not implemented**) |

> **Note:** `backfill-*.sh` and `rename-agents.sh` are admin/one-time scripts, not part of regular agent workflow. `rename-agents.sh` calls two endpoints that do not exist in the backend — tracked as a separate feature story.

### Gate Keeper (`.claude/agents/gate-keeper.md`)

| Caller | Endpoint | Method | Via |
|--------|----------|--------|----|
| Gate Keeper | `/api/v1/stories/{uuid}/gate-review` | POST | Direct API call |
| Gate Keeper | `/api/v1/stories/{uuid}` | GET | Direct API call |

---

## 2. Endpoint Contract Definitions

### 2.1 Story Endpoints

#### `GET /api/v1/stories`

List stories with optional filters.

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `status` | string | No | — | Filter by status (e.g., `in_progress`, `ready_to_pull`, `specifying`) |
| `type` | string | No | — | Filter by type (e.g., `feature`, `bug`, `sdlc`) |
| `epic_id` | UUID | No | — | Filter by epic |
| `title` | string | No | — | Search by title (case-insensitive) |
| `agent_name` | string | No | — | Filter by assigned agent |
| `page` | int | No | 1 | Page number |
| `per_page` | int | No | 20 | Items per page |

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "story_id": "YYYY-MM-DD.HH-MM-SS",
      "title": "string",
      "type": "string",
      "status": "string",
      "agent_id": "uuid | null",
      "epic_id": "uuid | null",
      "spec": "string | null",
      "acceptance_criteria": [{"name": "string", "given": "string", "when": "string", "then": "string", "met": false}],
      "gate_stamps": [{"token_type": "string", "value": "string", "emitted_at": "ISO8601"}],
      "lock": {"agent_id": "uuid", "locked_at": "ISO8601"} | null
    }
  ],
  "total": 0,
  "page": 1,
  "per_page": 20
}
```

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_get "/api/v1/stories?status=in_progress&agent_name=agent86"
```

---

#### `POST /api/v1/stories`

Create a new story.

**Request Body (`CreateStoryRequest`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Story title |
| `type` | string | Yes | `feature`, `bug`, `sdlc`, `data`, `refactoring`, `maintenance`, `investigation` |
| `project_id` | UUID | Yes | Project UUID (not nullable) |
| `epic_id` | UUID | No | Epic UUID |
| `goal` | string | Yes | Story goal (mandatory) |
| `spec` | string | No | Full spec markdown. If null → status stays `specifying`. If non-null → auto-transitions to `spec_complete` → `ready_to_pull` |
| `context` | string | No | Context section |
| `acceptance_criteria` | string | No | GWT format text |
| `user_journey` | string | No | User journey text |
| `wireframes` | string | No | Wireframe text or N/A justification |
| `edge_cases` | string | No | Edge cases text |
| `risks` | string | No | Risks text |
| `dependencies` | UUID[] | No | Dependency story UUIDs |
| `source_story_id` | UUID | No | Source story for BUG traceability |

**Response:** `201 Created`
```json
{
  "data": {
    "id": "uuid",
    "story_id": "YYYY-MM-DD.HH-MM-SS",
    "title": "string",
    "type": "string",
    "status": "specifying"
  }
}
```

**Error:** `422` — Pydantic validation (missing required fields, invalid type)

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_create_story '{
  "title": "My Story",
  "type": "feature",
  "project_id": "ad8a709f-e2bd-4975-8d99-f283c4165ddf",
  "goal": "What success looks like"
}'
```

**Idempotency:** Non-idempotent. Before retry, query `GET /api/v1/stories?status=specifying` and match by title.

---

#### `GET /api/v1/stories/{uuid}`

Get a single story by UUID.

**Response:** `200 OK` — full story object (same shape as list item, all fields)

**Error:** `404` — story not found

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_get "/api/v1/stories/$STORY_UUID"
```

---

#### `PATCH /api/v1/stories/{uuid}`

Update story fields. Idempotent — safe to retry.

**Request Body (`UpdateStoryRequest`):** All fields optional. Only include fields being updated.

| Field | Type | Description |
|-------|------|-------------|
| `spec` | string | Full spec markdown. Triggers `_auto_extract_upstream_fields()` to fill null structured fields from markdown headers |
| `context` | string | Context section |
| `goal` | string | Goal section |
| `acceptance_criteria` | string | **Use checkbox format** (`- [x] AC1: Name`) to preserve met state. Header format (`### AC1:`) resets all to `met=false` |
| `wireframes` | string | Wireframe text |
| `edge_cases` | string | Edge cases text |
| `risks` | string | Risks text |
| `drift_review` | string | Drift review narrative |
| `execution_log` | string | Execution log content |
| `compliance_checklist` | string | Filled compliance checklist |
| `commit_sha` | string | Git commit hash |
| `drift_type` | string | Only PATCH if agent knowingly deviated from plan (`plan_drift`) |
| `lock` | null | Set to null to release lock |
| `revision_required` | string | Revision notes (for shelving) |
| `dependencies` | UUID[] | Dependency story UUIDs |

**IMPORTANT:** Do NOT include `gate_stamps` in PATCH — the PATCH path calls `vo_list.clear()`, destroying all existing stamps. Gate stamps are persisted as side effects of `POST /api/v1/stories/{uuid}/gate-review` and `POST /api/v1/stories/{uuid}/test-results`.

**Response:** `200 OK` — updated story object

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_patch "/api/v1/stories/$STORY_UUID" '{"drift_review": "No drift detected."}'
```

---

#### `POST /api/v1/stories/{uuid}/transition`

Transition story status.

**Request Body (`TransitionRequest`):**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `target_status` | string | Yes | Cannot be `claimed` (use `/claim` instead). Valid: `specifying`, `spec_complete`, `ready_to_pull`, `in_progress`, `done`, `canceled`, `archived` |

**Response:** `200 OK` — updated story object

**Error:** `422` — invalid target status or invalid transition from current status

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_transition "$STORY_UUID" "in_progress"
```

**Idempotency:** Non-idempotent. Check current status before retry.

---

#### `POST /api/v1/stories/{uuid}/claim`

Claim a story (assigns agent + sets lock).

**Request Body (`ClaimRequest`):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `agent_name` | string | Yes | — | Agent name (cannot be empty) |
| `machine_id` | string | No | `"local"` | Machine identifier |

**Response:** `200 OK` — updated story object

**Error:** `409` — already claimed by a different agent

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_claim "$STORY_UUID" "agent86"
```

**Idempotency:** Non-idempotent. Check if already claimed before retry.

---

#### `POST /api/v1/stories/{uuid}/claim-and-transition`

Claim + transition in one atomic call.

**Request Body (`ClaimAndTransitionRequest`):**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `agent_name` | string | Yes | — |
| `machine_id` | string | No | `"local"` |
| `target_status` | string | Yes | — |

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_claim_and_transition "$STORY_UUID" "agent86"
# Always transitions to in_progress
```

---

#### `POST /api/v1/stories/{uuid}/assign-upstream`

Assign agent for upstream ceremony (sets agent_id + lock without claiming).

**Request Body (`ClaimRequest`):**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `agent_name` | string | Yes | — |
| `machine_id` | string | No | `"local"` |

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_assign_upstream "$STORY_UUID" "agent86"
```

---

#### `POST /api/v1/stories/{uuid}/cancel`

Cancel a story. No request body.

**Response:** `200 OK` — updated story object

**Error:** `409/422` — story in terminal state

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/cancel" '{}'
```

---

#### `POST /api/v1/stories/{uuid}/shelve`

Shelve a story.

**Request Body (`ShelveRequest`):**

| Field | Type | Required |
|-------|------|----------|
| `reason` | string | No |

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/shelve" '{"reason": "Blocked by dependency"}'
```

---

#### `POST /api/v1/stories/{uuid}/mark-ac-met`

Mark a single AC as met. Triggers WebSocket broadcast for real-time progress.

**Request Body (`MarkAcMetRequest`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ac_number` | int | Yes | 1-based AC position |

**Response:** `200 OK`

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/mark-ac-met" '{"ac_number": 1}'
```

---

#### `POST /api/v1/stories/{uuid}/gate-stamps`

> **REMOVED (410 Gone).** This endpoint returns 410 Gone. All stamp emission now goes through `POST /gate-review` (Gate Keeper stamps) or `POST /test-results` (SUITES-GREEN).

---

#### `POST /api/v1/stories/{uuid}/test-results`

Record test results. Entity internally emits SUITES-GREEN stamp.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `suites_passed` | string[] | Yes | Array of passed suite names (e.g., `["backend", "api", "frontend"]`) |
| `origin_sha` | string | Yes | origin/main SHA for audit trail |

**Response:** `200 OK` — updated story object (with SUITES-GREEN stamp)

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_record_test_results "$STORY_UUID" '["backend","api","frontend"]' "$(git rev-parse origin/main)"
```

**Note:** `hub_emit_stamp` (hub-client.sh) is deprecated — the underlying endpoint returns 410 Gone.

---

#### `POST /api/v1/stories/{uuid}/signals`

Record a signal.

**Request Body (`RecordSignalRequest`):**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `signal_type` | string | Yes | Same validator as gate stamps (`GATE_STAMP_TYPE_MAP`) — see Known Inconsistency #5 |
| `value` | string | Yes | Signal value |

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_emit_signal "$STORY_UUID" "phase" "tdd-red"
```

---

#### `POST /api/v1/stories/{uuid}/gate-verdicts`

Record a gate verdict (pass/fail).

**Request Body (`RecordGateVerdictRequest`):**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `gate_type` | string | Yes | No enum validation (unlike gate-review) |
| `result` | string | Yes | `pass` or `fail` |

**Canonical curl:**
```bash
# Used by hub-query.sh hub_post_gate_verdict()
hub_post_gate_verdict "$STORY_UUID" "spec" "pass"
```

---

#### `POST /api/v1/stories/{uuid}/gate-review`

Submit a gate review (used by Gate Keeper). Persists stamps atomically.

**Request Body (`SubmitGateReviewRequest`):**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `gate_type` | string | Yes | `spec`, `code`, or `ship` |
| `result` | string | Yes | `pass` or `fail` |

**Side effects on PASS:**
- `spec` → persists `review_spec` + `review_plan` stamps
- `code` → persists `review_code` stamp
- `ship` → persists `review_ship` stamp

**Canonical curl:**
```bash
# Called directly by Gate Keeper subagent
curl -sf -X POST -H "Content-Type: application/json" \
  -d '{"gate_type": "spec", "result": "pass"}' \
  "$EUPRAXIS_HUB_URL/api/v1/stories/$STORY_UUID/gate-review"
```

---

#### `POST /api/v1/stories/{uuid}/render`

Render story file to worktree.

**Request Body (`RenderStoryRequest`):**

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `worktree_path` | string | Yes | — | Agent worktree path |
| `target_dir` | string | No | `"done"` | `doing` or `done` |

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/render" "{\"worktree_path\": \"$(pwd)\", \"target_dir\": \"done\"}"
```

---

#### `POST /api/v1/stories/{uuid}/retype`

Change a story's type with full ceremony reset to `specifying`. Clears spec, ACs, gate stamps, and resets status.

**Request Body (`RetypeRequest`):**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `type` | string | Yes | Must be a valid `StoryType` value: `feature`, `bug`, `sdlc`, `data`, `refactoring`, `maintenance`, `investigation` |

**Response:** `200 OK` — updated story object (status reset to `specifying`)

**Error:** `422` — invalid type value

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/retype" '{"type": "sdlc"}'
```

**Side effects:** Clears `spec`, `acceptance_criteria`, `gate_stamps`, releases agent linkage. Story must go through full upstream ceremony again.

---

#### `GET /api/v1/stories/{uuid}/gates/{gate_name}`

Evaluate a single gate.

**Path Parameters:** `gate_name` — e.g., `spec`, `plan`, `code_write`, `push`

**Response (`GateResultResponse`):** `200 OK`
```json
{
  "gate_name": "string",
  "allowed": true,
  "reason": "string",
  "missing_stamps": [],
  "missing_fields": [],
  "advisory": "string | null"
}
```

**Canonical curl (via hub-query.sh):**
```bash
source .claude/hooks/lib/hub-query.sh
hub_check_gate "$STORY_UUID" "push"
# Returns: exit 0 + JSON body (allowed), exit 1 (denied), exit 2 (gate engine disabled)
```

---

#### `GET /api/v1/stories/{uuid}/gates`

Evaluate all gates at once.

**Response (`AllGatesResponse`):** `200 OK`
```json
{
  "gates": {
    "spec": {"gate_name": "spec", "allowed": true, "reason": "...", ...},
    "plan": {"gate_name": "plan", "allowed": true, "reason": "...", ...},
    "code_write": {"gate_name": "code_write", "allowed": false, "reason": "...", ...}
  }
}
```

---

### 2.2 Agent Endpoints

#### `POST /api/v1/agents/{id}/status`

Push agent session status (by UUID).

**Request Body (`RemoteStatusPayload`):**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `story_id` | UUID string | No | — |
| `tdd_phase` | string | No | — |
| `gate_stamps` | string[] | No | — |
| `current_action` | string | No | — |
| `progress` | string | No | — |
| `todo_completed` | int | No | — |
| `todo_total` | int | No | — |
| `phase` | string | No | — |
| `signal` | string | No | — |
| `gate` | string | No | — |
| `clear_story` | bool | No | `false` |

**Canonical curl:**
```bash
# session-heartbeat.sh uses this path (by UUID):
curl -sf -X POST -H "Content-Type: application/json" \
  -d '{"current_action": "implementing", "story_id": "'$UUID'"}' \
  "$EUPRAXIS_HUB_URL/api/v1/agents/$EUPRAXIS_AGENT_ID/status"
```

---

#### `POST /api/v1/agents/by-name/{name}/status`

Push agent session status (by name). Same `RemoteStatusPayload`.

**Canonical curl:**
```bash
# hub-client.sh hub_push_status() uses this path (by name):
source scripts/hub-client.sh
hub_push_status "agent86" '{"current_action": "implementing"}'
```

**Note:** See Known Inconsistency #4 — hooks use by-UUID, skills use by-name.

---

#### `GET /api/v1/agents/{id}/interventions`

Poll for pending interventions (by UUID).

**Response:** `200 OK`
```json
{
  "interventions": [
    {"type": "message", "message": "string", "queued_at": "ISO8601"}
  ]
}
```

**Canonical curl:**
```bash
# intervention-poll-hook.sh uses by-UUID:
curl -sf --connect-timeout 3 --max-time 5 \
  "$EUPRAXIS_HUB_URL/api/v1/agents/$EUPRAXIS_AGENT_ID/interventions"
```

---

#### `GET /api/v1/agents/by-name/{name}/interventions`

Poll for pending interventions (by name).

**Canonical curl:**
```bash
# hub-client.sh hub_poll_interventions() uses by-name:
source scripts/hub-client.sh
hub_poll_interventions "agent86"
```

---

#### `POST /api/v1/agents/by-name/{name}/session-errors`

Record a session error for drift tracking (L1).

**Request Body (`RecordSessionErrorRequest`):**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `error_type` | string | Yes | `hook-deny`, `api-failure`, `script-error`, `gate-fail`, `test-fail`, `env-error` |
| `severity` | string | Yes | `critical`, `warning`, `info` |
| `source` | string | Yes | Cannot be empty |
| `message` | string | Yes | Cannot be empty |
| `story_id` | string | No | — |
| `context` | string | No | — |

**Response:** `201 Created`

**Canonical curl:**
```bash
curl -sf -X POST -H "Content-Type: application/json" \
  -d '{"error_type": "hook-deny", "severity": "warning", "source": "commit-gate.sh", "message": "Missing suites_green stamp"}' \
  "$EUPRAXIS_HUB_URL/api/v1/agents/by-name/agent86/session-errors"
```

---

#### `GET /api/v1/agents/by-name/{name}/checks/spec-ceremony`

Check if agent has completed spec ceremony (for `spec-ceremony-gate.sh`).

**Response:** `200 OK` — **No `data` wrapper**
```json
{
  "allowed": true,
  "reason": "spec ceremony complete"
}
```

---

#### `GET /api/v1/agents/by-name/{name}/checks/directive-write`

Check if agent can write to protected directive files.

**Response:** `200 OK` — **No `data` wrapper**
```json
{
  "allowed": true,
  "reason": "sdlc story in_progress",
  "story_title": "Agent API Contract Reference"
}
```

---

### 2.3 Epic Endpoints

#### `GET /api/v1/epics`

List all epics.

**Query Parameters:**

| Param | Type | Required |
|-------|------|----------|
| `status` | string | No |

**Response:** `200 OK`
```json
{
  "data": [
    {"id": "uuid", "name": "EPIC_NAME", "status": "string", ...}
  ]
}
```

---

#### `GET /api/v1/epics/{id}/checks/ceremony-ready`

Check if epic ceremony is complete (for `epic-ceremony-gate.sh`).

**Response:** `200 OK` — **No `data` wrapper**
```json
{
  "allowed": true,
  "reason": "ceremony complete",
  "missing_fields": [],
  "story_count": 5
}
```

---

### 2.4 Queue Endpoints

#### `GET /api/v1/queue/board-summary`

Board summary for init/board-check.

**Response:** `200 OK` (`BoardSummaryResponse`)
```json
{
  "available_count": 3,
  "wip_count": 2,
  "done_today_count": 1,
  "in_progress": [
    {"story_id": "YYYY-MM-DD.HH-MM-SS", "type": "feature", "title": "string"}
  ],
  "available": [
    {"story_id": "YYYY-MM-DD.HH-MM-SS", "type": "feature", "title": "string"}
  ]
}
```

**Canonical curl:**
```bash
curl -sf --connect-timeout 3 --max-time 5 \
  "$EUPRAXIS_HUB_URL/api/v1/queue/board-summary"
```

---

#### `GET /api/v1/queue/ready_to_pull`

Get available stories with dependency resolution applied.

**Query Parameters:**

| Param | Type | Required |
|-------|------|----------|
| `project_id` | string | No |

**Response:** `200 OK` — ordered list of stories ready for execution

**Canonical curl:**
```bash
source scripts/hub-client.sh
hub_get "/api/v1/queue/ready_to_pull"
```

---

### 2.5 Health

#### `GET /health`

Health check (no API version prefix).

**Response:** `200 OK`
```json
{
  "status": "ok",
  "environment": "development",
  "version": "0.1.0",
  "data_mode": "db"
}
```

---

### 2.6 Dev Endpoints

#### `POST /api/v1/dev/seed-from-files`

> **Dev/admin only.** Not part of regular agent workflow. Used to import story/epic markdown files into the database.

Import story and epic markdown files from the `stories/` directory into active repositories. Deduplicates by `story_id` and by `title+type+epic_id`.

**Request Body:** None (reads from filesystem)

**Response:** `200 OK`
```json
{
  "status": "seeded",
  "stories": 15,
  "epics": 3,
  "skipped": 2,
  "ready_to_pull": 8,
  "new_stories": 5,
  "new_epics": 1,
  "skipped_dedup": 0
}
```

**Error:** `500` — `{"error": "Seed failed: <message>"}`

**Canonical curl:**
```bash
curl -sf -X POST "$EUPRAXIS_HUB_URL/api/v1/dev/seed-from-files"
```

---

## 3. Known Inconsistencies

> These are documented friction points. Fixes should be tracked as separate stories.

### #1: Two Wrapper Libraries with Different Contracts

| Aspect | `hub-client.sh` (skills) | `hub-query.sh` (hooks) |
|--------|--------------------------|------------------------|
| Retry | 3x exponential backoff (1s, 2s, 4s) | None |
| Timeout | 3s connect, **10s** max | 3s connect, **5s** max |
| Auth | Resolved once, passed down | Resolved per-call, conditional |
| Response | HTTP code classification (200-299/400-499/5xx) | Exit code only (`-sf` flag) |
| Caching | None | 5s TTL for story queries |

**Impact:** Same endpoint has different reliability guarantees depending on caller type. A stamp emitted from a hook (no retry) is less reliable than one from a skill (3x retry).

**Canonical pattern:** Use `hub-client.sh` wrappers for all new callers. Hook callers should migrate to `hub-client.sh` when feasible.

### #2: Duplicate Functions with Different Implementations

| Function | `hub-client.sh` | `hub-query.sh` |
|----------|-----------------|----------------|
| Gate stamp emission | `hub_emit_stamp()` — **DEPRECATED** (POST /gate-stamps returns 410 Gone) | `hub_emit_gate_stamp()` — **DEPRECATED** |
| Test result recording | `hub_record_test_results()` — replaces SUITES-GREEN stamp emission | N/A |
| Signal emission | `hub_emit_signal()` — uses `jq -Rs` | `hub_emit_signal()` — string interpolation |
| Gate verdict | N/A | `hub_post_gate_verdict()` — string interpolation |

**Impact:** Gate stamp emission functions are deprecated. Stamps are now emitted as side effects of `POST /gate-review` (Gate Keeper) and `POST /test-results` (test-emitter.sh).

**Canonical pattern:** Use `hub_record_test_results` for SUITES-GREEN. All other stamps are side effects of `gate-review`.

### #3: Naming Inconsistencies (Resolved)

| Caller context | Old function | New pattern |
|----------------|-------------|-------------|
| Skills | `hub_emit_stamp()` (deprecated) | Stamps are side effects of `gate-review` / `test-results` |
| Hooks | `hub_emit_gate_stamp()` (deprecated) | `hub_record_test_results()` for SUITES-GREEN |

**Resolution:** Direct stamp emission is deprecated. All stamps are now emitted as side effects of `POST /gate-review` or `POST /test-results`.

### #4: Path Pattern Mismatch (by-UUID vs by-name)

| Caller | Endpoint path | Identity |
|--------|--------------|----------|
| `session-heartbeat.sh` | `/api/v1/agents/{EUPRAXIS_AGENT_ID}/status` | By UUID |
| `hub_push_status()` | `/api/v1/agents/by-name/{name}/status` | By name |
| `intervention-poll-hook.sh` | `/api/v1/agents/{EUPRAXIS_AGENT_ID}/interventions` | By UUID |
| `hub_poll_interventions()` | `/api/v1/agents/by-name/{name}/interventions` | By name |

**Impact:** Same `RemoteStatusPayload`, but hooks resolve agent identity differently than skills. If agent UUID or name changes, different callers break in different ways.

**Canonical pattern:** Use by-name paths (`/agents/by-name/{name}/...`) — agent name is more stable and readable than UUID.

### #5: Signal Schema Reuses Gate Stamp Validator

`RecordSignalRequest.signal_type` validates against `GATE_STAMP_TYPE_MAP` — the same enum used for gate stamps. This means signals are constrained to the same set of `token_type` values as gate stamps.

**Location:** `backend/src/api/v1/schemas/story_schemas.py` — `RecordSignalRequest`

**Impact:** Signals cannot use domain-specific signal types (e.g., `phase`, `tdd-red`) without those types existing in the gate stamp enum. Likely a copy-paste from `EmitGateStampRequest`.

**Canonical pattern:** Signals should have their own validator or accept arbitrary types.

### #6: Response Shape Assumptions (data wrapper vs flat)

| Endpoint | Response shape |
|----------|---------------|
| `/api/v1/stories`, `/api/v1/stories/{uuid}`, `/api/v1/epics` | `{"data": ...}` (wrapped) |
| `/api/v1/agents/by-name/{name}/checks/spec-ceremony` | `{"allowed": ..., "reason": ...}` (flat) |
| `/api/v1/agents/by-name/{name}/checks/directive-write` | `{"allowed": ..., "reason": ..., "story_title": ...}` (flat) |
| `/api/v1/epics/{id}/checks/ceremony-ready` | `{"allowed": ..., "reason": ..., "missing_fields": ..., "story_count": ...}` (flat) |
| `/api/v1/queue/board-summary` | `{"in_progress": [...], "available": [...]}` (flat) |

**Impact:** Callers must know which shape to expect — `jq '.data[0]'` works for story endpoints but fails on check endpoints.

**Canonical pattern:** New callers should consult this document for the exact shape. Check endpoints use flat responses; CRUD endpoints use `data` wrapper.

### #7: Fire-and-Forget vs Acknowledged

| Library | Stamp/signal emission | Error visibility |
|---------|----------------------|------------------|
| `hub-client.sh` | Returns exit code; caller can check | Visible |
| `hub-query.sh` | `>/dev/null 2>&1` — completely silent | **Invisible** |

**Impact:** A failed gate stamp emitted from a hook vanishes silently — the stamp never lands in the DB, no error surfaces, and the agent proceeds as if it succeeded. Governance stamps can be lost without trace.

**Canonical pattern:** All stamp emissions should check exit codes. Hook callers should log failures via `session-error-capture.sh`.

### #8: Missing Error Context (422 Bodies Discarded)

When `hub-client.sh` gets a 4xx response, it returns exit code 1 but discards the response body. Pydantic validation errors (422) contain field-level error detail that callers never see.

**Impact:** Callers only know "permanent failure" — not which field was wrong or why.

**Canonical pattern:** `hub-client.sh` should preserve and expose the response body on 4xx errors (at minimum via stderr).

---

## 4. Maintenance Notes

- **When adding a new endpoint:** Add it to Section 2 with full contract, and to Section 1 cross-reference for each caller
- **When modifying a schema:** Update the corresponding contract definition in Section 2
- **When adding a new hook/skill:** Add it to the cross-reference in Section 1
- **Staleness detection:** If a caller passes params not listed here, or gets an unexpected response shape, update this document and file a companion SDLC story if the contract changed
- **Relationship to `api-guide.md`:** That document covers general REST patterns and conventions. This document covers agent-specific endpoint contracts. No overlap
