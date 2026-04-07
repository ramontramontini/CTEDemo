# Scoring Rubrics — sdlc-audit

> Reference file for `/sdlc-audit` skill. Read on-demand during Steps 3, 3.5, 4, and 5.

---

## Per-Area Scoring Rubric (0-5)

| Score | Meaning | Criteria |
|-------|---------|----------|
| 0 | Non-existent | No artifact exists for this area |
| 1 | Rudimentary | Exists but mostly broken, incomplete, or contradictory |
| 2 | Partial | Significant gaps, contradictions, or unresolved ambiguity |
| 3 | Functional | Works but has notable issues in 2+ dimensions |
| 4 | Strong | Minor issues only, at most 1 dimension with room for improvement |
| 5 | State of the art | Exemplary across all dimensions, no meaningful issues |

**Composite score per area** = mean of the 4 dimension scores (each scored 0-5 using the same rubric).

---

## Weighted Overall Score

| Area | Weight | Rationale |
|------|--------|-----------|
| Directives | 35% | Foundation — all other artifacts derive from these |
| Enforcement | 30% | Mechanical enforcement is the primary governance guarantee |
| Automation | 25% | Agent/skill quality determines execution reliability |
| Hygiene | 10% | Templates are consumed less frequently than other artifacts |

**Formula:** `Overall = SUM(area_composite * area_weight)`

---

## Determinism Rubric (Enforcement Dimension)

Used when evaluating the Enforcement dimension of any area.

| Score | Level | Criteria |
|-------|-------|----------|
| 5 | Fully deterministic | Hook deny — agent physically blocked |
| 4 | Mostly deterministic | Hook deny + behavioral supplement |
| 3 | Partially deterministic | Hook advisory + behavioral rules |
| 2 | Behavioral with backstop | No hook, but Gate Keeper catches violations |
| 1 | Purely behavioral | Rule only, no enforcement mechanism |
| 0 | No enforcement | No rule, no hook, no Gate Keeper coverage |

---

## Enforcement Coverage Classification

Used in Step 3.5 when mapping rules/policies to enforcement mechanisms.

| Classification | Definition | Example |
|---------------|------------|---------|
| **Mechanical** | Hook HARD DENY — agent physically blocked | `pre-commit-test-gate.sh` blocks commit without tests |
| **Behavioral+Backstop** | No blocking hook, but Gate Keeper subagent catches violations during review | Code-review checks SOLID principles |
| **Behavioral Only** | Rule in CLAUDE.md, agent compliance is voluntary. No hook, no Gate Keeper check | Anti-rationalization (Policy 10) |
| **Ungoverned** | No rule, no hook, no Gate Keeper coverage | Not documented |

When a rule has **multiple mechanisms**, classify by the strongest: Mechanical > Behavioral+Backstop > Behavioral Only.

---

## Improvement Impact Levels

Used in Step 5 when ranking improvements.

| Level | Criteria | Score Impact |
|-------|----------|-------------|
| Critical | Contradictions or broken enforcement | >0.5 overall |
| High | Significant duplicity or ambiguity | 0.3-0.5 |
| Medium-High | Notable conciseness or effectiveness gaps | 0.2-0.3 |
| Medium | Moderate issues | 0.1-0.2 |
| Low-Medium | Minor issues with some benefit | 0.05-0.1 |
| Low | Polish items | <0.05 |

**Ranking:** Impact descending, then Token Savings descending for same-impact items.

---

## Skill Quality Rubric (Automation — Structure Dimension)

Used when evaluating the Structure dimension of skills in the Automation area. Based on Claude SDK skill-creator best practices.

| Score | Level | Criteria |
|-------|-------|----------|
| 5 | Full SDK compliance | Progressive disclosure (SKILL.md ≤500 lines, references/ for detail), trigger-optimized description (50-500 chars, third person, WHAT+WHEN), complete frontmatter (allowed-tools, version), imperative writing style, bundled resources (references/, scripts/, assets/) |
| 4 | Strong | Progressive disclosure implemented, good description with trigger phrases, minor gaps (e.g., missing allowed-tools or one resource not bundled) |
| 3 | Functional | Proper frontmatter and step-based procedure, but missing progressive disclosure when needed (>500 lines without references/) or weak description |
| 2 | Partial | Basic frontmatter + body present, no progressive disclosure, description lacks trigger phrases or is too short/long, missing allowed-tools |
| 1 | Rudimentary | SKILL.md exists but missing frontmatter fields or has empty/minimal body |
| 0 | Non-existent | No SKILL.md found for the skill |

**Progressive disclosure threshold:** Skills >200 lines benefit from splitting; >500 lines strongly recommend references/ subdirectory.

**Description quality checks:** Contains specific user trigger phrases, 50-500 characters, third person, describes WHAT the skill does and WHEN to use it.

**Frontmatter completeness:** `name`, `description`, `version` required. `allowed-tools` required when the skill uses tools beyond Read/Glob/Grep.

---

## Hook Quality Rubric (Enforcement — Structure Dimension)

Used when evaluating the Structure dimension of hooks in the Enforcement area. Based on Claude SDK hook patterns.

| Score | Level | Criteria |
|-------|-------|----------|
| 5 | Full compliance | Fast-path exits (≤5 lines to bail), fail-closed/open explicitly declared, throttled state with TTL markers, shared library usage (`hub-query.sh`, `session-error-capture.sh`), <150 lines per hook |
| 4 | Strong | Fast-path exits, fail-closed/open declared, shared library usage, minor gaps (e.g., no throttling or slightly over 150 lines) |
| 3 | Functional | Fast-path exits and fail-closed/open declared, but no shared library usage or no throttling when needed |
| 2 | Partial | Some fast-path exits but inconsistent error handling, no fail-closed/open declaration, duplicates shared library patterns |
| 1 | Rudimentary | Hooks exist but no fast-path exits, no error handling strategy, no shared libraries |
| 0 | Non-existent | No hooks found |

**Fast-path exit check:** Hook exits within first 5 lines when tool/file doesn't match. Matchers declare applicable tool types.

**Error handling declaration:** PreToolUse hooks must declare fail-closed or fail-open. PostToolUse hooks must fail silently (exit 0 on errors).

**Performance checks:** API calls use shared cache (5-second TTL via `hub-query.sh`). PostToolUse hooks use throttle markers (30s+ intervals).

---

## Agent Quality Rubric (Automation — Structure Dimension)

Used when evaluating the Structure dimension of agents in the Automation area. Based on Claude SDK agent patterns.

| Score | Level | Criteria |
|-------|-------|----------|
| 5 | Full compliance | Mode-based operation with trigger detection, shared definitions reused across modes, critical/warning/suggestion severity classification, structured verdict format (VERDICT: PASS/FAIL), gate stamp authority respected |
| 4 | Strong | Mode-based operation, checklist architecture with severity classification, minor gaps (e.g., no shared definitions or missing drift signal) |
| 3 | Functional | Checklists present with clear items, but no mode detection, no severity classification, or no structured verdict format |
| 2 | Partial | Basic agent definition with some checklist items, but unstructured output, no severity levels, no verdict format |
| 1 | Rudimentary | Agent file exists but minimal content, no checklists, no structured output |
| 0 | Non-existent | No agent definition file found |

**Mode detection check:** Multi-purpose agents detect mode from prompt trigger phrases. Single-mode agents are assessed on other criteria.

**Checklist architecture:** Items classified as CRITICAL (blocking), WARNING (logged), or Suggestion (optional). Mechanical verification instructions where possible.

**Verdict format:** Structured `VERDICT: PASS/FAIL` with issue counts and summary. Gate stamp authority: only Gate Keeper emits Class 3 governance stamps.

---

## Directive Quality Rubric (Directives — Structure Dimension)

Used when evaluating the Structure dimension of CLAUDE.md and rules in the Directives area. Based on Claude SDK prompt architecture patterns.

| Score | Level | Criteria |
|-------|-------|----------|
| 5 | Full compliance | Three-level architecture (L0/L1/L2), progressive disclosure (CLAUDE.md summarizes, rules detail, docs deep-dive), no verbatim duplication, token-efficient (<35K est. total), directory structure documented |
| 4 | Strong | Three-level architecture, good progressive disclosure, minor duplication or economy gaps |
| 3 | Functional | Three-level architecture present, some cross-referencing, but notable economy gaps (>20-word duplication without cross-reference) or missing level |
| 2 | Partial | Basic structure but monolithic sections, heavy duplication across CLAUDE.md and rules, no progressive disclosure |
| 1 | Rudimentary | CLAUDE.md exists but no structure, no rules files, no cross-referencing |
| 0 | Non-existent | No CLAUDE.md found |

**Three-level check:** L0 (portable SDLC) in CLAUDE.md + rules, L1 (project-specific) in rules + architecture docs, L2 (domain) in domain docs. Each level has clear scope.

**Progressive disclosure check:** CLAUDE.md contains summaries with explicit references to detailed rules. Full duplication without cross-reference is a finding.

**Token efficiency check:** Total directive footprint estimated as characters/4. Flag areas consuming >25% of total. Flag total >35K estimated tokens.

---

## Agent Friction Rubric (Cross-Cutting)

Evaluates governance artifacts for patterns that cause agent failures, retries, or wasted time. Applies across all areas. Score per artifact, report alongside per-area assessment.

| Score | Level | Criteria |
|-------|-------|----------|
| 5 | No friction | All machine-consumed outputs structured (JSON), no eval/string-concat payloads, repeatable shell logic consolidated to backend endpoints |
| 4 | Minimal | Structured output enforced, jq/library-based construction, minor shell→backend gaps remaining |
| 3 | Moderate | Structured output standard with exceptions, safe payload construction in most cases, backend consolidation identified but not acted on |
| 2 | Notable | Majority structured output but notable gaps (free-text verdicts, string-concat payloads), some shell→backend opportunities |
| 1 | High | Some structured output but inconsistent, eval-based construction, shell duplicates backend logic |
| 0 | Severe | No structured output patterns — all free-text, string-concat payloads, no backend consolidation |

### Sub-Checks

**Backend consolidation:** Flag shell scripts that perform: API queries with response parsing, state management across invocations, JSON construction >5 lines, business logic (validation, classification). These are backend endpoint candidates. Exception: one-off bootstrap tasks (git rebase, file discovery) are not consolidation candidates — score based on invocation frequency.

**Output format:** Machine-consumed outputs MUST use structured format (JSON). Human-facing reports (audit output, research logs) are exempt. Check: `hookSpecificOutput` usage, verdict format, stamp values, script outputs consumed by other scripts.

**Parsing safety:** Flag: `eval` in JSON construction, string concatenation for API payloads, `grep`/`sed`/`awk` parsing of JSON responses (use `jq`), unquoted variable expansion in payloads. Partial credit: correct format (e.g., `hookSpecificOutput`) but fragile construction (string-concat).
