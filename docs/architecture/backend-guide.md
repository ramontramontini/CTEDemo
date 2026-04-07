# Backend Architecture Guide — EuPraxis

> FastAPI backend patterns, domain architecture, and infrastructure conventions.

---

## Architecture Layers

```
backend/src/
├── api/                  # HTTP layer (FastAPI routers)
│   ├── v1/              # Versioned API endpoints
│   └── exceptions.py    # API exception handlers
├── application/          # Use cases (orchestration)
├── domain/              # Business logic (entities, homes, VOs)
│   ├── story/           # Story aggregate
│   ├── epic/            # Epic aggregate
│   ├── agent/           # Agent aggregate
│   ├── project/         # Project aggregate
│   ├── conversation/    # Conversation aggregate
│   ├── shared/          # Cross-aggregate types
│   └── services/        # Cross-aggregate orchestration
├── infrastructure/       # External concerns
│   ├── database/        # SQLAlchemy models, repositories
│   ├── memory/          # In-memory repositories (DATA_MODE=memory)
│   └── external/        # External API clients
└── config/              # Settings, startup configuration
```

---

## Domain Layer Rules

1. **Package by aggregate** — each aggregate is self-contained
2. **Entity owns behavior** — computed properties, state transitions, invariants
3. **Home manages lifecycle** — factory, lookup, scoped queries
4. **No infrastructure dependencies** — entities never import DB, HTTP, or framework code
5. **Acyclic imports** — if A imports B, B must NOT import A

---

## Repository Pattern

```python
# domain/story/repository.py (interface)
class StoryRepository(ABC):
    @abstractmethod
    def get(self, id: UUID) -> Story: ...

    @abstractmethod
    def save(self, story: Story) -> None: ...

    @abstractmethod
    def find_by_status(self, status: StoryStatus) -> list[Story]: ...

# infrastructure/memory/story_repository.py (implementation)
class MemoryStoryRepository(StoryRepository):
    def __init__(self):
        self._store: dict[UUID, Story] = {}

    def get(self, id: UUID) -> Story:
        if id not in self._store:
            raise StoryNotFoundError(id)
        return self._store[id]
```

---

## DATA_MODE Architecture

| Mode | Repository | When |
|------|-----------|------|
| `memory` | `MemoryXxxRepository` | Agent worktrees, testing |
| `db` | `DatabaseXxxRepository` | Main worktree (production-like), production |

Repository selection happens at startup via dependency injection. The domain layer never knows which repository implementation is active.

---

## Dependency Injection

```python
# config/dependencies.py
def get_story_repository() -> StoryRepository:
    if settings.data_mode == "memory":
        return MemoryStoryRepository()
    return DatabaseStoryRepository(session)
```

---

## Database & Persistence Architecture

### ISP-Split Repository Interfaces

Repository interfaces follow Interface Segregation — three focused ABCs instead of one monolithic interface:

```python
class ReadRepository(ABC, Generic[EntityType]):
    """Read-only operations: query and existence checks."""
    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[EntityType]: ...
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[EntityType]: ...
    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool: ...

class WriteRepository(ABC, Generic[EntityType]):
    """Write operations: create, update, delete."""
    @abstractmethod
    async def add(self, entity: EntityType) -> EntityType: ...
    @abstractmethod
    async def update(self, entity: EntityType) -> EntityType: ...
    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool: ...

class MappingRepository(ABC, Generic[EntityType, ModelType]):
    """DB-only: domain entity ↔ SQLAlchemy model conversion."""
    @abstractmethod
    def _to_domain(self, model: ModelType) -> EntityType: ...
    @abstractmethod
    def _to_model(self, entity: EntityType) -> ModelType: ...
```

**Composition:**
- Memory repos inherit `ReadRepository` + `WriteRepository` only (no model mapping needed)
- DB repos inherit all three (need domain ↔ model conversion)
- Aggregate-specific repos extend with custom queries (e.g., `find_by_status()`)

### RepositoryFactory

Centralized factory selects the correct implementation based on `DATA_MODE`:

```python
class RepositoryFactory:
    """Mode-aware factory — returns memory or DB repos."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self._cache: dict[str, Any] = {}

    def _get_repo(self, key: str) -> Any:
        if settings.data_mode == "memory":
            if key not in self._cache:
                self._cache[key] = _resolve(mem_path)()
            return self._cache[key]
        return _resolve(db_path)(self.session)
```

**Key behaviors:**
- Memory mode: returns cached singleton (same instance for lifecycle)
- DB mode: returns new instance per session (session-scoped)
- Application code is mode-agnostic — same API regardless of mode
- Registry maps entity keys to (memory_path, db_path) tuples

### File-Backed Memory Persistence

Memory repositories persist state to `temp/memory-state.json` so data survives backend restarts during development:

**Architecture:**
- `MemoryStateManager` singleton manages all repository persistence
- Each memory repo registers with the state manager on `__init__`
- On every write (`add`/`update`/`delete`): state manager persists all repos to JSON atomically (write to `.tmp`, rename)
- On startup with file: load from JSON, skip mock data
- On startup without file: load mock data (fresh start)
- Corrupt file: rename to `.corrupt`, fall back to mock data
- Dev endpoints: `POST /api/v1/dev/reset-data` deletes persistence file and reloads mock data

### Database Mode Architecture

| Mode | Value | Storage | Use Case |
|------|-------|---------|----------|
| **Memory** | `memory` | In-memory + file persistence | Agent worktrees, testing (instant start) |
| **Database** | `db` | PostgreSQL + async SQLAlchemy | Main worktree, production, staging |

**How it works:**
1. `DATA_MODE` env var read by `config/settings.py`
2. `RepositoryFactory` checks `settings.data_mode`
3. Returns memory repositories (mock data) OR DB repositories (SQLAlchemy)
4. Application code is mode-agnostic — same API, same behavior

### Credential Management

Database credentials are centralized in `.env` using component variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `eupraxis_dev_2026` | Database password (change for shared/production) |
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_DB` | `eupraxis` | Database name |
| `DATABASE_URL` | _(assembled)_ | Direct override — takes precedence if set |

**Assembly chain:** `settings.py` → `effective_database_url` property assembles from components if `DATABASE_URL` is not set directly. Scripts (`start.sh`, `prod-local.sh`, `dev.sh`) use `${VAR:-default}` shell interpolation. Docker Compose files use the same pattern.

**Never hardcode credentials** in scripts, compose files, or Python code. Always reference env vars.

### Connection Pooling

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| Pool size | `DB_POOL_SIZE` | 10 | Persistent connections in pool |
| Max overflow | `DB_POOL_MAX_OVERFLOW` | 20 | Additional connections above pool_size |
| Pre-ping | `DB_POOL_PRE_PING` | True | Validate connections before reuse |

**Production recommendation:** `DB_POOL_SIZE=20`, `DB_POOL_MAX_OVERFLOW=40`

### Alembic Migration Conventions

- **Naming format:** `YYYYMMDD_HHMM_<revision>_<slug>.py` (timestamp-based, UTC). Example: `20260406_1300_a3f8b2c1d4e5_add_foo_column.py`
- **Revision ID format (post-`000056`):** Hash-based, 12-char hex (e.g., `a3f8b2c1d4e5`). Agents generate via `python3 -c "import secrets; print(secrets.token_hex(6))"` — `alembic revision` is blocked in agent worktrees by `forbidden-command-blocker.sh`
- **`down_revision` lookup:** Find current head from the latest file: `ls -1 backend/alembic/versions/*.py | tail -1`, then extract the `revision = ` value. Never compute sequentially — the previous head may be a hash
- **Mandatory rule:** Every story that changes a domain entity or SQLAlchemy model MUST include a migration
- **Never execute** migrations in agent worktrees (`DATA_MODE=memory`). Main worktree runs migrations via `alembic upgrade head`
- Migration files are committed but not run until deployment
- **Concurrent migrations:** When multiple agents create migrations concurrently, each gets a unique hash ID but they share the same `down_revision`, creating multiple heads. Resolve with `alembic merge heads -m "merge concurrent migrations"` before running `alembic upgrade head`
- **Grandfathered sequential IDs:** `001`–`039` (3-digit), `000040`–`000056` (6-digit zero-padded), and `e73e3dd8fef3` (hash) are historical. All coexist via Alembic's `down_revision` chain. Do NOT extend the sequential numbering

**Common commands:**
```bash
cd backend && alembic upgrade head          # Apply all pending
cd backend && alembic downgrade -1          # Roll back one
cd backend && alembic revision --autogenerate -m "description"  # Create new
cd backend && alembic current               # Show current revision
cd backend && alembic history               # Show history
cd backend && alembic heads                 # Check for multiple heads
cd backend && alembic merge heads -m "merge concurrent migrations"  # Merge multiple heads
```

### Migration Smoke Test

Validates the full Alembic migration chain against a real temporary PostgreSQL — catches SQL errors before they reach the dev server.

**Usage:**
```bash
bash scripts/migration-smoke-test.sh
```

**What it validates:**
- `alembic upgrade head` — full forward migration chain
- `alembic downgrade base` — full rollback chain (skipped if upgrade fails)

**Exit codes:** `0` = all pass, `1` = upgrade fail, `2` = downgrade fail

**Configuration:** Set `SMOKE_PG_PORT` env var to change the temporary PostgreSQL port (default: `5433`). Uses container `eupraxis-smoke-db` and volume `eupraxis-smoke-pgdata` — isolated from the dev database.

**When to run:** Before committing/pushing any migration changes. The script spins up a temporary PostgreSQL container, runs the migration chain, reports results, and cleans up automatically.

**Automatic integration with `prod-local.sh`:** The smoke test runs automatically as a preflight step when `./scripts/prod-local.sh` starts — after PostgreSQL is ready but before `alembic upgrade head` touches the dev database. If the smoke test fails, startup aborts. Use `./scripts/prod-local.sh --skip-smoke` to bypass the check (e.g., when you've already run it manually).

---

*DRAFT — architecture will evolve as EuPraxis_Domain entities are implemented.*
