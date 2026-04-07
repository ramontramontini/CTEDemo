# L1 Code Quality — OO, SOLID, Design Patterns, Clean Code (Auto-Loaded)

---

## OO Domain Architecture (Rich Domain Model)

**Data + behavior together.** Entities encapsulate state, behavior, and invariants.

**Package by aggregate:**
```
domain/{aggregate}/
    entity.py          # Identity + state + behavior
    home.py            # Factory + lifecycle + scoped queries
    value_objects.py   # Immutable domain concepts
    enums.py           # Aggregate-specific enumerations
    repository.py      # Repository interface (port)
```

### Mandatory Rules
- Creation through Home only. `Entity(**data)` in endpoints is BANNED
- Acyclic dependencies
- Infrastructure independence (no DB/HTTP/file I/O in entities)
- Encapsulation via _private + @property + mutation methods

---

## SOLID Principles

- **S** — Single Responsibility
- **O** — Open/Closed: extend via Strategy, not modification
- **L** — Liskov Substitution
- **I** — Interface Segregation
- **D** — Dependency Inversion

---

## Clean Code

- Naming reveals intent. No abbreviations
- Functions: <=50 lines, max 3 parameters
- DRY: 3+ lines duplicated -> extract
- Dead code: delete it. No commented-out code

---

## STRICTLY BANNED

- Anemic Domain Model
- Layer-first packaging (`entities/`, `services/`, `repositories/`)
- Cyclical dependencies
- Direct entity construction (use Home.create())
- If/else chains on entity type (use Factory + Strategy)
- `isinstance()` checks in business logic
