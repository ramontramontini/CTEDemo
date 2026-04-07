# L3 Domain — CTEDemo-Specific (Auto-Loaded)

<!-- EUPRAXIS:MANAGED:START -->
> Per-project domain rules: business rules, aggregates, domain-specific gotchas.
> Full domain rules live in `docs/domain/`. Read on-demand.
> L0+L1 rules are identical across projects. L2+L3 are project-specific.
<!-- EUPRAXIS:MANAGED:END -->

---

## Domain Overview

**CTEDemo** (Autonomous Development Through Practical Wisdom) manages:
- **Stories** — work items with state machines, pull model, dependency resolution
- **Epics** — groups of related stories with dependency graphs
- **Agents** — Claude Code sessions with capabilities and governance
- **Projects** — repositories with directive architectures
- **Conversations** — agent interactions and coordination

---

## Key Business Rules
- Story state machine: drafting → req_ready → available → claimed → in_progress → done (with canceled, archived paths). API is source of truth
- Pull model: agents query available stories via API (`GET /api/v1/queue/available`) based on Kanban priority
- Dependency resolution: stories cannot start until dependencies are in done status (resolved by QueueService)
- Lock protection: active locks prevent concurrent modification (managed in DB)

> Domain specs: `docs/domain/overview.md`

---

## CTEDemo Aggregates
`story/`, `epic/`, `agent/`, `project/`, `conversation/` + `shared/` (cross-aggregate types) + `services/` (cross-aggregate orchestration)

Dependencies: `docs/domain/overview.md`

---

## CTEDemo-Specific Gotchas

- **Agent orchestration data** — from API hooks, never compute in frontend
- **WebSocket connections** — managed by backend, frontend subscribes to events only
- **Story state transitions** — domain logic in backend via API (`POST /api/v1/stories/{id}/transition`), frontend renders current state. Local story files exported on-demand (gitignored cache)
