# Hub API Helpers — Shared Retry & Fallback Procedures

> **Purpose:** Reference document for hub API retry/fallback procedures and idempotency notes. The executable implementation is `scripts/hub-client.sh` — all skills source that library for API operations.
> **Not user-invokable.** This is an internal reference document, not a slash command.
> **Research basis:** Story A extraction matrix candidates #7, #8, #9 (RESEARCH-LOG-2026-03-07.02-56-21-SKILLS-EXTRACTION-ANALYSIS.md §1.3).
> **Implementation:** `scripts/hub-client.sh` provides `hub_get()`, `hub_post()`, `hub_patch()` + convenience wrappers (`hub_transition()`, `hub_claim()`, `hub_create_story()`, `hub_record_test_results()`) with 3-retry exponential backoff (1s, 2s, 4s). Exit codes: 0=success, 1=permanent (4xx), 2=transient exhausted. Gate stamps are emitted as side effects of `gate-review` and `test-results` endpoints — `hub_emit_stamp()` is deprecated (POST /gate-stamps returns 410 Gone).

---

## Hub URL Resolution

```
$EUPRAXIS_HUB_URL (from .env, default http://localhost:8000)
```

Auth: `-H "Authorization: Bearer $EUPRAXIS_HUB_TOKEN"` (from `.env`, omit if empty/unset).

---

## Procedure: API Call with Retry

**Executable implementation:** `scripts/hub-client.sh` — source this library and use `hub_get()`, `hub_post()`, `hub_patch()`, or convenience wrappers.

```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$UUID/transition" '{"target_status": "done"}'
```

The library implements the retry/backoff logic described below. Callers handle exit codes:
- **Exit 0:** Success — response body on stdout
- **Exit 1:** Permanent failure (4xx) — do NOT retry. Error message on stderr
- **Exit 2:** All retries exhausted (transient) — caller uses AskUserQuestion:
  ```
  AskUserQuestion:
    question: "Hub API unreachable after 3 retries ([endpoint]). How should we proceed?"
    options:
      - "Retry" — re-execute the call
      - "Abort operation" — stop the current skill
  ```

### Retry Behavior (implemented in hub-client.sh)

| Response | Classification | Action |
|----------|---------------|--------|
| 2xx success | **Success** | Return 0, response body on stdout |
| 4xx client error | **Permanent failure** | Return 1 immediately (no retry) |
| 5xx server error | **Transient failure** | Retry with exponential backoff |
| Network error | **Transient failure** | Retry with exponential backoff |

**Backoff schedule:** 1s, 2s, 4s (3 retries total, 7s worst-case delay).

---

## Idempotency Notes

Not all API calls are safe to blindly retry. Use this guidance:

| Operation | Idempotent? | Retry Safety |
|-----------|-------------|-------------|
| `GET` (query) | Yes | Always safe |
| `PATCH` (update fields) | Yes | Safe — same payload produces same result |
| `POST /stories` (create) | **No** | Check if story was created before retrying (GET by title/timestamp). If already exists, skip create |
| `POST /stories/{id}/transition` | **No** | Check current status before retrying. If already in target status, skip transition |
| `POST /stories/{id}/render` | Yes | Safe — re-renders same content |
| `POST /stories/{id}/claim` | **No** | Check if already claimed by this agent before retrying |
| `POST /stories/{id}/cancel` | **No** | Check current status before retrying |
| `POST /stories/{id}/gate-stamps` | — | **REMOVED (410 Gone)** — use `POST /gate-review` or `POST /test-results` instead |
| `POST /stories/{id}/gate-review` | Yes | Safe — re-submitting same gate_type+result updates existing stamps |
| `POST /stories/{id}/test-results` | Yes | Safe — re-submitting same suites updates existing SUITES-GREEN stamp |
| `POST /stories/{id}/compliance` | Yes | Safe — replace semantics (overwrites entire checklist). See §Execution & Compliance Endpoints |
| `POST /stories/{id}/execution-log` | Yes | Safe — replace semantics (overwrites entire log). See §Execution & Compliance Endpoints |
| `POST /stories/{id}/mark-ac-met` | Yes | Safe — re-marking already-met AC is a no-op. See §Execution & Compliance Endpoints |

**For non-idempotent calls:** Before retry, query current state (`GET /stories/{id}`) to verify the operation hasn't already succeeded. If it has, skip the retry and proceed.

---

## Gate Stamp Emission

> **IMPORTANT:** `POST /api/v1/stories/{id}/gate-stamps` returns **410 Gone**. All stamp emission now goes through two internalized endpoints:

### Via Gate Review (Gate Keeper stamps)

**Endpoint:** `POST /api/v1/stories/{uuid}/gate-review`

Gate Keeper calls this directly after reaching a verdict. Stamps are emitted as side effects based on `gate_type`:
- `spec` → `review_spec` + `review_plan`
- `code` → `review_code`
- `ship` → `review_ship` + `docs` + `compliance` + `drift`
- `epic` → `gate_epic`
- `approval` → `approved_spec`

```bash
# Called by Gate Keeper subagent — not by agent skills directly
curl -sf -X POST -H "Content-Type: application/json" \
  -d '{"gate_type": "spec", "result": "pass", "stamp_values": {"review_spec": "pass"}}' \
  "$EUPRAXIS_HUB_URL/api/v1/stories/$STORY_UUID/gate-review"
```

### Via Test Results (SUITES-GREEN stamp)

**Function:** `hub_record_test_results`

```bash
source scripts/hub-client.sh
hub_record_test_results "$STORY_UUID" '["backend","api","frontend"]' "$(git rev-parse origin/main)"
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `$STORY_UUID` | Yes | Story UUID (not story_id) |
| `$SUITES_JSON` | Yes | JSON array of passed suite names |
| `$ORIGIN_SHA` | Yes | origin/main SHA for audit trail |

The entity internally emits `SUITES-GREEN` stamp with `@<sha>` audit trail.

### Deprecated: `hub_emit_stamp`

The `hub_emit_stamp` function in `hub-client.sh` is **deprecated** — the underlying endpoint returns 410 Gone. Existing callers must migrate to `gate-review` or `test-results`.

---

## Execution & Compliance Endpoints

> **Authoritative source:** `backend/src/api/v1/schemas/story_schemas.py` for Pydantic request schemas. `backend/src/domain/story/compliance_registry.py` for canonical compliance keys.

### Mark AC Met

**Endpoint:** `POST /api/v1/stories/{uuid}/mark-ac-met`

Marks a single acceptance criterion as met by AC number (1-indexed).

```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/mark-ac-met" '{"ac_number": 1}'
```

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `ac_number` | `int` | Yes | Must be >= 1. Must not exceed total AC count |

**Errors:**
- `422` — AC number out of range or AC already marked met
- `404` — Story not found

### Execution Log

**Endpoint:** `POST /api/v1/stories/{uuid}/execution-log`

Replaces the story's execution log with the provided entries. Replace semantics — each call overwrites the entire log.

```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/execution-log" '{
  "entries": [
    "Task 1: Reordered /spec skill steps (AC1)",
    "Task 2: Documented API schemas (AC2)",
    "Task 3: Added pre-flight checks (AC3)"
  ]
}'
```

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `entries` | `list[str]` | Yes | At least 1 entry. Empty strings and whitespace-only entries are stripped and rejected |

**Errors:**
- `422` — Entries array empty, or all entries are whitespace-only

### Compliance

**Endpoint:** `POST /api/v1/stories/{uuid}/compliance`

Replaces the story's compliance checklist. Replace semantics — each call overwrites all items. Items MUST use canonical `key` values from the compliance template.

```bash
source scripts/hub-client.sh
hub_post "/api/v1/stories/$STORY_UUID/compliance" '{
  "items": [
    {"key": "tests_passing", "label": "All tests passing", "checked": true},
    {"key": "docs_updated", "label": "Docs updated", "checked": true},
    {"key": "no_console_log", "label": "No console.log", "checked": true, "na_reason": null}
  ]
}'
```

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `items` | `list[ComplianceItem]` | Yes | At least 1 item |

Each `ComplianceItem`:

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `key` | `str` or `null` | No | Must match a canonical key for the story's type (from `GET /compliance/template`). Unknown keys → 422 |
| `label` | `str` | Yes | Display label for the item |
| `checked` | `bool` | Yes | Whether the item passes |
| `na_reason` | `str` or `null` | No | Justification when item is not applicable |

**Errors:**
- `422 UNKNOWN_COMPLIANCE_KEYS` — One or more `key` values not in the canonical set for this story type. Fetch canonical keys via `GET /api/v1/compliance/template?type={story_type}` first

### Compliance Template

**Endpoint:** `GET /api/v1/compliance/template?type={story_type}`

Returns the canonical compliance checklist template for a given story type. Use this to populate the `key` field when submitting compliance items.

```bash
source scripts/hub-client.sh
hub_get "/api/v1/compliance/template?type=feature"
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | query param | Yes | Story type: `feature`, `bug`, `sdlc`, `maintenance`, `data`, `refactoring`, `investigation` |

**Response:**
```json
{
  "data": {
    "type": "feature",
    "item_count": 12,
    "items": [
      {"key": "tests_passing", "label": "All tests passing", "description": "...", "gate": "commit"},
      {"key": "docs_updated", "label": "Documentation updated", "description": "...", "gate": "ship"}
    ]
  }
}
```

**Usage pattern:** Fetch template once at the start of the quality phase (`/pull` Step 4d). Iterate over `items`, assess each as `checked: true/false` with optional `na_reason`. Submit via `POST /compliance` with the canonical `key` values.

---

## Error Message Format

When reporting errors to the user:

- **Permanent failure:** `"Hub API error: [HTTP status] [error code] — [message from API response]"`
- **Transient failure (retrying):** Silent — log only, don't surface to user until all retries exhausted
- **All retries exhausted:** `"Hub API unreachable after 3 retries ([endpoint]). How should we proceed?"` via AskUserQuestion
- **Abort:** `"Operation aborted by user — [endpoint]. [N] total attempts failed."`
