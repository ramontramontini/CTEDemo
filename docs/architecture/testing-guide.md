# Testing Guide — EuPraxis

> Test organization, naming conventions, and aggregate-aligned test structure.

---

## Test Organization

Tests mirror the domain aggregate structure. Group by domain concept, not by technical layer.

| Type | Location | Technology | Command |
|------|----------|------------|---------|
| Pure logic | `tests/frontend/{Domain}/` | Vitest (no JSX) | `cd frontend && npx vitest run` |
| Component | `frontend/src/__tests__/{Domain}/` | Vitest + RTL | `cd frontend && npx vitest run` |
| Backend | `tests/backend/{Domain}/` | pytest | `cd backend && DATA_MODE=memory poetry run python -m pytest ../tests/backend -v --no-cov` |
| API | `tests/api/{Domain}/` | pytest + httpx | `cd backend && DATA_MODE=memory poetry run python -m pytest ../tests/api -v --no-cov` |
| E2E | `tests/integration/{Domain}/` | Playwright | `npm run e2e` |

**`{Domain}` must match the aggregate name:** `Story/`, `Epic/`, `Agent/`, `Project/`, `Conversation/`

---

## Test Directory Structure

```
tests/
├── backend/
│   ├── conftest.py          # Memory mode guard
│   ├── pytest.ini
│   ├── Story/               # Story aggregate tests
│   │   ├── test_entity.py
│   │   ├── test_home.py
│   │   └── test_repository.py
│   ├── Epic/
│   └── Agent/
├── api/
│   ├── conftest.py
│   ├── pytest.ini
│   ├── Story/               # Story API tests
│   │   └── test_story_endpoints.py
│   └── Agent/
├── frontend/
│   └── Story/               # Pure logic tests
│       └── story-utils.test.ts
└── integration/
    └── Story/               # E2E Story tests
        └── story-lifecycle.spec.ts
```

---

## Naming Conventions

### Backend (pytest)
```python
def test_story_transition_to_doing_when_dependencies_met_succeeds():
    """test_<what>_<condition>_<expected>"""
    pass

def test_story_transition_to_doing_when_blocked_raises_error():
    pass
```

### Frontend (Vitest)
```typescript
test('should display story title when story is loaded', () => {
  // test('should <expected> when <condition>')
});

test('should show blocked indicator when story has unmet dependencies', () => {
});
```

---

## TDD Workflow

1. **RED:** Write a failing test that describes the expected behavior
2. **GREEN:** Write the minimum code to make the test pass
3. **REFACTOR:** Clean up while keeping tests green

### Exemptions
- **SDLC stories:** No TDD required (directive/process changes)
- **Data stories:** No TDD required (mock data, seed data)

---

## Memory Mode Testing

All tests run with `DATA_MODE=memory` regardless of the worktree type (main or agent). Tests never connect to PostgreSQL. The `conftest.py` enforces this:

```python
# tests/backend/conftest.py
import os
os.environ["DATA_MODE"] = "memory"

@pytest.fixture(scope="session", autouse=True)
def memory_mode_guard():
    assert os.environ.get("DATA_MODE") == "memory", \
        "Tests MUST run in memory mode"
```

---

## Pre-Commit Test Checklist

Before every commit, ALL suites must pass:
1. `cd backend && DATA_MODE=memory poetry run python -m pytest ../tests/backend -v --no-cov`
2. `cd backend && DATA_MODE=memory poetry run python -m pytest ../tests/api -v --no-cov`
3. `cd frontend && npx vitest run`
4. Zero failures, zero errors, zero skipped

---

*DRAFT — test patterns will be refined as domain entities are implemented.*
