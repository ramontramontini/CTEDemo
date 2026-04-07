# L1 Code Quality — OO, SOLID, Design Patterns, Clean Code (Auto-Loaded)

> Portable to any project. Tech-stack examples: `docs/architecture/code-quality.md`
> L0+L1 rules are portable across projects. L2+L3 are project-specific.

---

## OO Domain Architecture (Rich Domain Model — Rule 9)

**Data + behavior together (MANDATORY).** Entities encapsulate state, behavior, and invariants. Domain logic lives inside the entity — computed properties and behavior methods, never external services or passive getters.

**Package by aggregate (MANDATORY).** Each domain concept is self-contained in its own module:
```
domain/{aggregate}/
    entity.py          # Identity + state + behavior
    home.py            # Factory + lifecycle + scoped queries
    value_objects.py   # Immutable domain concepts
    enums.py           # Aggregate-specific enumerations
    repository.py      # Repository interface (port)
```
Entity, Home, VOs, enums, and repository interface MUST be co-located. Never scatter across layer-based folders.

### Two OO Patterns — Each With ONE Job

| Pattern | Job | Examples |
|---------|-----|----------|
| **Entity** | Single-instance behavior owner (identity, state, invariants) | `order.total_amount`, `order.cancel()` |
| **Home** | Aggregate lifecycle manager (factory, lookup, scoped queries) | `OrderHome.create(data)`, `LineItemHome.for_order(order)` |

**Independent aggregate Home:** creation + lookup — `OrderHome.create(data)`, `OrderHome.get(id)`
**Dependent aggregate Home:** creation + scoped ops receiving independent entities — `LineItemHome.create(order, product, ...)`, `LineItemHome.for_order(order)`

### Mandatory Rules
- **Creation through Home only.** `Entity(**data)` in endpoints/services is BANNED — use `Home.create()`
- **Acyclic dependencies.** If A imports B, B MUST NOT import A. Independent aggregates MUST NOT import dependent ones. Dependent Homes receive independent entities as parameters
- **No inverted navigation.** BANNED: `order.get_line_items()` — use `LineItemHome.for_order(order)`
- **Infrastructure independence.** Entities MUST NOT perform: DB access, HTTP calls, file I/O, or framework access. Persistence is handled by Homes and repositories
- **Encapsulation.** Protect internal state with `_private` attributes + `@property` accessors + mutation methods. Never access `_private` attributes from outside the class
- **Abstraction extraction.** If 2+ implementations share the same concept, extract an ABC. Every strategy family MUST define an abstract contract
- **Entity delegation.** Entities expose type-discriminated behavior as their own API, delegating to enum methods or strategies internally. Callers ask the entity, not reach through to its internals
- **Value object immutability.** VOs use `frozen=True` (Pydantic `model_config`) or `@dataclass(frozen=True)`. Operator overloading (`__add__`, `__sub__`, `__eq__`) for domain arithmetic (Money, Duration)

### Shared Types
Cross-aggregate types go in `domain/shared/` (e.g., Money, Currency). MUST be immutable and dependency-free. Only types used by 2+ aggregates belong here.

### Cross-Aggregate Orchestration
Cross-aggregate workflows live in `domain/services/`. Services orchestrate aggregates but MUST NOT contain entity logic.

### Where Does Behavior Belong?

| Behavior | Owner | Example |
|----------|-------|---------|
| Single-entity logic | Entity | `order.total_amount` |
| Creation / lifecycle | Home | `OrderHome.create(data)` |
| Scoped collection query | Dependent Home | `LineItemHome.for_order(order)` |
| Cross-aggregate workflow | Domain Service | `FulfillmentService.process(order, warehouse)` |
| Shared immutable concept | `domain/shared/` | `Money`, `Currency` |

### Aggregate Testability
Each aggregate MUST be independently testable. Tests mirror aggregate structure: `tests/{Aggregate}/`. Entity, enum, VO, Home, and repository tests all live under the same aggregate folder.

---

## SOLID Principles (Downstream — Code Development)

- **S** — Single Responsibility: one reason to change per class
- **O** — Open/Closed: extend via Strategy pattern, not modification
- **L** — Liskov Substitution: subtypes must be substitutable for their base type
- **I** — Interface Segregation: small, focused interfaces over fat ones
- **D** — Dependency Inversion: depend on abstractions (inject repositories, not implementations)

---

## Design Patterns

**Factory + Strategy (MANDATORY for entity-type branching):**
- One strategy class per type. Factory selects strategy at runtime
- Adding a new type = one strategy class + registry entry. No if/else chains

**Enum Polymorphism (for type-discriminated properties):**
- Enums MAY define behavior methods when type-discriminated logic is simple and self-contained
- Entity delegates to enum methods: `entity.is_x() → self.type_enum.is_x()`
- Use Strategy pattern when behavior requires external dependencies or complex multi-method contracts

**Service Composition (for cross-aggregate orchestration):**
- Application services compose domain services via constructor injection
- Domain services are reusable building blocks; application services wire them together
- Each service has one responsibility — decompose God services into collaborators

---

## Clean Code Essentials

- **Naming:** names reveal intent. No abbreviations, no generic names
- **Functions:** ≤50 lines, max 3 parameters. Do one thing
- **DRY:** 3+ lines duplicated → extract immediately
- **Dead code:** delete it. No commented-out code, no unused imports
- **Comments:** explain WHY, not WHAT. Self-documenting code first

---

## Test Performance

**Performance Budget (per suite):**
- Backend (`pytest ../tests/backend`): **<30s**
- Frontend (`npx vitest run`): **<30s**
- API (`pytest ../tests/api`): **<30s**
- E2E (Playwright): exempt — inherently slow, full-stack
- Budget assumes `--no-cov`. If a suite exceeds its budget, a Refactor story is required before new feature work. Run `--durations=10` periodically to catch regressions

**Mock Time-Dependent Behavior:**
- Tests MUST NOT wait on real `sleep()`, `asyncio.sleep()`, polling loops, or network timeouts
- Patch at module level (where used, not where defined): `monkeypatch.setattr("module.asyncio.sleep", no_op)`
- Any test taking >1s is suspect — likely has an unmocked wait

**Fixture Scope for Expensive Setup:**
- Subprocess calls, file I/O scaffolds, network connections → `session` or `module` scope when assertions are read-only
- `function` scope reserved for tests that mutate the fixture output
- Document the read-only invariant in the fixture docstring (e.g., "Do NOT mutate — use your own fixture for write tests")

---

## STRICTLY BANNED

> **Enforcement: Tier 3 (Hard Refuse).** These patterns are non-negotiable. The agent MUST NOT implement them even if instructed. Override path: SDLC story to add a contextual exception to `docs/governance/approved-exceptions.md`. See CLAUDE.md §Communication Style.

- Anemic Domain Model (entities as passive data containers with external services)
- Layer-first packaging (`entities/`, `services/`, `repositories/`, `enums/`)
- Cyclical dependencies (if A imports B, B must NOT import A)
- Inverted navigation (`order.get_line_items()` — use Home instead)
- Direct entity construction (`Entity(**data)` — use Home.create())
- Infrastructure logic inside entities (DB, HTTP, File I/O, framework access)
- If/else chains on entity type (use Factory + Strategy pattern)
- `isinstance()` checks in business logic (use method dispatch on the object itself)
- Unnecessary inheritance hierarchies when Strategy+Factory suffices (subtypes with same fields but different behavior = Strategy, not subclass)
