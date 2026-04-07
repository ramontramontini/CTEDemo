# Governance Override Log

> Tier 2 overrides only. Tier 3 refusals are not logged here (the refusal itself is the record).
> Format: one row per override. **Append-only** — never edit or delete existing rows.
> See CLAUDE.md §Communication Style for tier definitions.

| Date | Session | Story ID | Override # | Agent Recommendation | User Direction | Risk Level |
|------|---------|----------|------------|---------------------|----------------|------------|
| 2026-03-27 | agent99 | 2026-03-27.16-38-25 | 1 | Classify as Refactor (primary deliverable is production code) and create companion SDLC story for hook changes per Policy 2 | Override — keep bundled. Hook changes are mechanically coupled to backend signal endpoint; splitting creates artificial dependency | Low — hook changes are dual-write additions, not behavioral modifications. Logged in spec Risks section |
