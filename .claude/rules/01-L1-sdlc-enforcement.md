# L1 SDLC Enforcement Rules (Auto-Loaded)

> Enforcement supplements to CLAUDE.md.

---

## Enforcement Rules

- **Done Means Done:** Shipped = git log shows commit + git status clean + all tests pass
- **Sequential Tasks:** MUST NOT start second task while first has uncommitted work
- **Anti-Rationalization:** ALL changes go through the full workflow. Change size is IRRELEVANT

---

## TDD Standards

**Cycle:** RED > GREEN > REFACTOR.
**Per-AC GREEN:** Run only the TDD test file(s) for the current AC.
**Pre-commit:** Run all suites before commit. Fix any failures.
**Naming:** Backend: `test_<what>_<condition>_<expected>()` | Frontend: `test('should <expected> when <condition>')`
