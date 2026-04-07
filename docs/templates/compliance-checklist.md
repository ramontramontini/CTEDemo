# Compliance Review & Plan Validation

---

## Canonical Compliance Registry

> **Source of truth:** `backend/src/domain/story/compliance_registry.py` — 21 unique canonical items composed per StoryType.
> **Programmatic access:** `GET /api/v1/compliance/template?type={type}` returns the canonical item set for any story type.
> **Submission:** `POST /api/v1/stories/{id}/compliance` with `key` field per item. Backend validates keys against registry (422 for unknown keys, warnings for missing keys).

**BLOCKING:** Agent MUST NOT transition story to done via API or commit until every applicable canonical item is checked or N/A justified.

### All 21 Canonical Items

| Key | Label | Description | Gate |
|-----|-------|-------------|------|
| `spec_complete` | Spec complete (Context, Goal, ACs G/W/T, User Journey, Edge Cases 3+, Risks) | Requirements are testable and complete | upstream |
| `execution_plan` | Execution plan with ordered tasks per AC | Code types: TDD-ordered. Non-code: task headers with deliverables | upstream |
| `upstream_approved` | Upstream review passed + user approved (GATE-SPEC, APPROVED-SPEC) | Independent spec quality gate + explicit user consent | upstream |
| `wireframes` | Wireframes present or N/A justified (Policy 14) | Visual design verified before code | upstream |
| `oo_design_planned` | OO Design Decision section complete (2+ approaches with pros/cons, user-selected approach, or N/A with user approval) | Structured OO deliberation before code — aggregate boundaries, entity behavior, Home patterns | upstream |
| `research_log_planned` | Research log file planned (docs/research/logs/) | PHD research delivery planned | upstream |
| `tdd_followed` | TDD: RED->GREEN->REFACTOR documented per AC | Test-first discipline executed | ship |
| `oo_design_verified` | OO design implementation matches selected approach from spec's OO Design Decision section | Verified: entities, Home, VOs, aggregate structure match user-approved design choice | ship |
| `clean_code` | Clean code: DRY, clear names, no debug artifacts, API contracts match | SOLID principles applied, maintainable and professional | ship |
| `code_review` | Code-review passed (GATE-CODE) | Independent quality gate on implementation | ship |
| `all_suites_passing` | All test suites passing (zero failures/errors/skipped) | No regressions introduced | ship |
| `docs_verified` | Documentation updated, verified against code | Domain/arch/API docs match actual implementation | ship |
| `commit_format` | Conventional commit with story ID + Co-Authored-By | Git history traceable | ship |
| `execution_log` | Execution log has timestamped entries | Traceable work record | ship |
| `completion_verified` | All ACs met + all gate stamps emitted per Policy 9 | Acceptance criteria fulfilled, complete governance trail | ship |
| `drift_review` | Drift review completed | Process compliance verified | ship |
| `regression_test` | Regression test (test_regression_STORYID) | Defect prevented from recurring | ship |
| `verification_criteria` | Verification Criteria + Source Story filled | Fix verified against reproduction, drift chain maintained | ship |
| `old_tests_cleaned` | Old tests deleted for moved code | No stale tests after restructure | ship |
| `research_log_created` | Research log created in docs/research/logs/ | PHD research findings persisted | ship |
| `governance_clean` | Overrides logged, no Tier 3 violations. Count: [N] | Governance transparency maintained | governance |

### Items Per Story Type

| Type | Upstream | Ship | Gov | Total | Keys |
|------|----------|------|-----|-------|------|
| **feature** | 5 | 10 | 1 | **16** | spec_complete, execution_plan, upstream_approved, wireframes, oo_design_planned, tdd_followed, oo_design_verified, clean_code, code_review, all_suites_passing, docs_verified, commit_format, execution_log, completion_verified, drift_review, governance_clean |
| **bug** | 5 | 12 | 1 | **18** | feature keys + regression_test, verification_criteria |
| **refactoring** | 5 | 11 | 1 | **17** | feature keys + old_tests_cleaned |
| **sdlc** | 4 | 7 | 1 | **12** | spec_complete, execution_plan, upstream_approved, research_log_planned, all_suites_passing, docs_verified, commit_format, research_log_created, execution_log, completion_verified, drift_review, governance_clean |
| **data** | 3 | 6 | 1 | **10** | spec_complete, execution_plan, upstream_approved, all_suites_passing, docs_verified, commit_format, execution_log, completion_verified, drift_review, governance_clean |
| **maintenance** | 3 | 6 | 1 | **10** | Same as data |
| **investigation** | 3 | 3 | 1 | **7** | spec_complete, execution_plan, upstream_approved, execution_log, completion_verified, drift_review, governance_clean |

### Type-Specific Item Notes

- **Code types** (feature, bug, refactoring): Include `wireframes`, `oo_design_planned` (upstream) + `tdd_followed`, `oo_design_verified`, `clean_code`, `code_review` (ship)
- **BUG adds:** `regression_test`, `verification_criteria`
- **Refactoring adds:** `old_tests_cleaned`
- **SDLC adds:** `research_log_planned` (upstream), `research_log_created` (ship)
- **Investigation:** Minimal ship items — only `execution_log`, `completion_verified`, `drift_review`

---

## Evidence → Verification → Certification Chain

Each governance item maps to a 3-stage chain: agent produces evidence, Gate Keeper verifies, entity emits stamp.

| Phase | Evidence (Agent) | Verification (Gate Keeper) | Certification (Entity Stamp) |
|-------|-----------------|---------------------------|------------------------------|
| Upstream Ceremony | Spec + ACs + plan written | GK MODE 1 (spec-review) | PLAN, REVIEW_SPEC, REVIEW_PLAN, APPROVED_SPEC |
| OO Design | Execution plan specifies OO patterns | GK MODE 1 verifies OO design in plan | Covered by REVIEW_PLAN |
| TDD Cycle | Test-before-code workflow | tdd-gate.sh structural + GK MODE 3 | Structural (no stamp) + REVIEW_CODE |
| OO Implementation | Code uses encapsulation, polymorphism, SOLID | GK MODE 3 verifies OO in code | Covered by REVIEW_CODE |
| Test Coverage | All 3 suites pass | test-emitter.sh → POST /test-results | SUITES_GREEN |
| Ship Readiness | Docs, compliance, drift, DOD | GK MODE 4 reads artifacts | DOCS, COMPLIANCE, DRIFT, REVIEW_SHIP |
| Post-Ship | Push verified | GK post-push | SHIPPED |

## User Review (from Done)

**User-driven:** Agent transitions story to done via API. User reviews at their own pace.

- User tests the feature manually
- Accept → no action needed (already in done status)
- Reject (minor) → user creates inline fix request
- Reject (major) → user creates new BUG story via API

---

**If ANY unchecked → FIX before plan-review (Plan gate) or ExitPlanMode (Upstream gate) or commit (Ship gate).**
