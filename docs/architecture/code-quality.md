# Code Quality Standards — EuPraxis

> L1 deep-dive for SOLID, OOP, design patterns, frontend patterns, and clean code.
> L1 portable rules: `.claude/rules/02-L1-code-quality.md`

---

## SOLID in Practice

### Single Responsibility
- **Entity:** owns its state + behavior (e.g., `Story.can_transition_to(state)`)
- **Home:** manages lifecycle (create, lookup, scoped queries)
- **Service:** orchestrates cross-aggregate workflows
- **Repository:** persistence only — no business logic

### Open/Closed
- New story types, agent capabilities, or project configurations = new strategy class + registry entry
- Never modify existing strategy code to add a new variant

### Dependency Inversion
- Domain layer depends on abstractions (repository interfaces)
- Infrastructure layer implements those interfaces
- API layer depends on domain, never the reverse

---

## OOP Patterns for EuPraxis

### Entity Pattern
```python
class Story(BaseEntity):
    """Story aggregate root — owns state machine and transition logic."""

    @property
    def is_blocked(self) -> bool:
        """Check if dependencies prevent transition to doing."""
        return any(dep.status != StoryStatus.DONE for dep in self.dependencies)

    def transition_to(self, target_status: StoryStatus) -> None:
        """Validate and execute state transition."""
        if not self.can_transition_to(target_status):
            raise InvalidTransitionError(self.status, target_status)
        self._status = target_status
```

### Home Pattern
```python
class StoryHome:
    """Factory + lifecycle manager for Story aggregate."""

    @classmethod
    def create(cls, data: StoryCreateDTO) -> Story:
        """Create a new story with validation."""
        return Story(id=uuid4(), **data.model_dump())

    @classmethod
    def for_epic(cls, epic: Epic, repository: StoryRepository) -> list[Story]:
        """All stories belonging to an epic."""
        return repository.find_by_epic_id(epic.id)
```

### Factory + Strategy for Agent Types
```python
class AgentStrategyFactory:
    _strategies: dict[AgentType, type[AgentStrategy]] = {}

    @classmethod
    def register(cls, agent_type: AgentType, strategy: type[AgentStrategy]):
        cls._strategies[agent_type] = strategy

    @classmethod
    def get_strategy(cls, agent_type: AgentType) -> AgentStrategy:
        return cls._strategies[agent_type]()
```

### Encapsulation Pattern
```python
class StoryProgress:
    """Tracks story completion state — private state + property accessors."""

    def __init__(self, total_acs: int):
        self._total_acs = total_acs
        self._completed = 0

    @property
    def percentage(self) -> Decimal:
        if self._total_acs == 0:
            return Decimal("0")
        return Decimal(self._completed) / Decimal(self._total_acs) * 100

    @property
    def is_complete(self) -> bool:
        return self._completed == self._total_acs

    def mark_ac_done(self) -> None:
        if self._completed >= self._total_acs:
            raise AllACsAlreadyCompleteError()
        self._completed += 1
```

**Rule:** Never access `_private` attributes from outside the class. Use `@property` for reads, methods for mutations.

### Enum Polymorphism Pattern
```python
class StoryType(str, Enum):
    STORY = "story"
    BUG = "bug"
    REFACTOR = "refactor"
    SDLC = "sdlc"
    DATA = "data"

    def requires_tdd(self) -> bool:
        """SDLC and Data types are TDD-exempt."""
        return self not in (StoryType.SDLC, StoryType.DATA)

    def requires_source_story(self) -> bool:
        """Only BUG type requires source story traceability."""
        return self == StoryType.BUG
```

**Rule:** Use enum methods when type-discriminated logic is simple. Entity delegates: `story.requires_tdd() → self.story_type.requires_tdd()`. Use Strategy pattern when behavior needs external dependencies or complex multi-method contracts.

### Entity Delegation Pattern
```python
class Story(BaseEntity):
    """Entity delegates to enum/strategy — callers ask the entity, not its internals."""

    def requires_tdd(self) -> bool:
        return self.story_type.requires_tdd()

    def requires_source_story(self) -> bool:
        return self.story_type.requires_source_story()
```

**Rule:** Callers should ask the entity, not reach through to its enum/strategy. Keeps the entity as the primary API surface (Rich Domain Model).

### Value Object Operator Overloading
```python
from pydantic import BaseModel

class Duration(BaseModel):
    """Immutable value object with arithmetic operators."""
    model_config = ConfigDict(frozen=True)

    hours: Decimal

    def __add__(self, other: "Duration") -> "Duration":
        return Duration(hours=self.hours + other.hours)

    def __sub__(self, other: "Duration") -> "Duration":
        return Duration(hours=self.hours - other.hours)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented
        return self.hours == other.hours
```

**Rule:** VOs that represent domain quantities (Duration, Money) MUST support arithmetic via operator overloading. Use `frozen=True` for immutability.

---

## Domain Polymorphism Patterns

Three patterns for type-discriminated behavior, in order of preference:

| Pattern | When | Example |
|---------|------|---------|
| **Strategy + Factory** | Behavior varies by type, multiple methods, needs extensibility | `AgentStrategyFactory.get_strategy(agent_type)` |
| **Entity Delegation** | Entity wraps strategy/enum call as its own API | `story.requires_tdd()` → `self.story_type.requires_tdd()` |
| **Enum Methods** | Simple, self-contained type property queries | `story_type.requires_tdd()` |

### Anti-Pattern: Unnecessary Inheritance Hierarchies

**BANNED:** Creating deep class hierarchies or Pydantic discriminated unions when Strategy+Factory suffices. If subtypes share the same fields and only behavior differs → Strategy pattern. If the discriminator is an enum already on the entity → delegate to enum methods.

---

## Service Composition Pattern

Application services compose domain services via constructor injection:

```python
class BoardAssemblyService:
    """Application service — composes domain services for board view."""

    def __init__(
        self,
        story_service: StoryQueryService,
        epic_service: EpicQueryService,
        agent_service: AgentQueryService,
    ):
        self._story_service = story_service
        self._epic_service = epic_service
        self._agent_service = agent_service

    def assemble_board(self) -> dict:
        stories = self._story_service.get_all()
        epics = self._epic_service.get_with_progress()
        agents = self._agent_service.get_active()
        return {"stories": stories, "epics": epics, "agents": agents}
```

**Rules:**
- Domain services are reusable building blocks (one responsibility each)
- Application services wire domain services together (orchestration, no business logic)
- Inject dependencies via constructor — never import concrete classes in services

---

## Anti-Patterns (BANNED)

| Anti-Pattern | Why It's Banned | Correct Approach |
|-------------|-----------------|------------------|
| `if story_type == "BUG": ...` chain | Violates OCP, forces modification for new types | ABC + subclasses + factory |
| Public mutable attributes on entities | Breaks encapsulation, no invariant protection | `_private` + `@property` + mutation methods |
| God functions with 200+ lines | Violates SRP, untestable | Decompose into collaborating classes |
| Importing concrete classes in services | Violates DIP, hard to test | Depend on ABC, inject via constructor |
| `isinstance()` checks in business logic | Procedural polymorphism | Use method dispatch on the object itself |

---

## Frontend Patterns

### Component Structure
- Max 200 lines per component, 50 lines per function
- Props defined as TypeScript interfaces — no `any`
- State management via React hooks (useState, useReducer, useContext)
- Data fetching via custom hooks wrapping API service calls

### Component Organization
```
frontend/src/
├── components/          # Reusable UI components
│   ├── common/         # Shared across pages (Button, Modal, etc.)
│   └── {aggregate}/    # Aggregate-specific components
├── pages/              # Page-level components (route targets)
├── hooks/              # Custom React hooks
├── services/           # API service layer
└── types/              # TypeScript interfaces
```

### No Business Logic in Frontend
- Frontend renders state received from API
- All calculations, validations, state transitions happen in backend
- Frontend may have UI-only logic (form validation, display formatting)

---

## Clean Code Rules

- **Naming:** `calculateStoryLeadTime()` not `calc()`. `isBlocked` not `flag`
- **Functions:** single purpose, ≤50 lines, max 3 parameters
- **DRY:** 3+ lines duplicated → extract to shared utility
- **Dead code:** delete immediately. No commented-out code
- **Comments:** explain WHY, not WHAT. Code should be self-documenting

---

## Backend Service Patterns

### Domain Service (cross-aggregate)
```python
class StoryOrchestrationService:
    """Coordinates story lifecycle across aggregates."""

    def assign_to_agent(self, story: Story, agent: Agent) -> None:
        """Assign a story to an agent, checking availability."""
        if not agent.is_available:
            raise AgentUnavailableError(agent.id)
        story.lock(agent)
```

### Application Service (use case)
```python
class MoveStoryToDoingUseCase:
    """Application service — orchestrates a single use case."""

    def execute(self, story_id: UUID) -> Story:
        story = self.story_repo.get(story_id)
        story.transition_to(StoryStatus.DOING)
        self.story_repo.save(story)
        return story
```

---

*DRAFT — will be refined as EuPraxis_Domain epic implements domain entities.*
