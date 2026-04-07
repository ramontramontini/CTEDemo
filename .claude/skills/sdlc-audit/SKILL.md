---
name: sdlc-audit
description: >
  Perform a comprehensive health assessment of SDLC governance artifacts.
  This skill should be used when the user asks about governance health,
  directive quality, hook coverage, SDLC compliance, or wants to audit
  governance artifacts. Triggers on: "audit governance", "check directive
  quality", "governance health", "hook coverage", "SDLC compliance",
  "review governance", "assess directives".
version: 2.4.1
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
  - TodoWrite
---

# /sdlc-audit — Governance Health Assessment

**Usage:** `/sdlc-audit` (full) | `/sdlc-audit --area AREA` (single area: directives | enforcement | automation | hygiene)

> **Directive sources:** CLAUDE.md, .claude/rules/, .claude/agents/, .claude/hooks/, .claude/skills/, docs/templates/
> **Error Handling:** SILENT tier — read-only audit. Glob/file failures noted as issues in the report but never block the assessment. See `.claude/skills/error-handling-convention.md`.

**Invalid `--area` values:** Output "Invalid area '[name]'. Valid areas: directives, automation, enforcement, hygiene" and stop. This includes old 7-area names (`claude-md`, `rules`, `agents`, `hooks`, `skills`, `templates`, `token-budget`).

---

## Step 1: Artifact Discovery

Discover governance artifacts dynamically via glob patterns. Do NOT hardcode filenames.

| Area | Artifacts |
|------|-----------|
| **Directives** | `CLAUDE.md` (project root) + `.claude/rules/*.md` |
| **Enforcement** | `.claude/hooks/*.sh` + `.claude/hooks/*.json` + `.claude/settings.json` |
| **Automation** | `.claude/agents/*.md` + `.claude/skills/*/SKILL.md` |
| **Hygiene** | `docs/templates/*.md` |

For each file: record filename, character count (`wc -c`), line count (`wc -l`). Use parallel reads for independent areas. For `--area` mode, read only the target area plus CLAUDE.md (needed for cross-referencing).

If a directory is empty or missing: note "0 artifacts" — it will score 0.

---

## Step 2: Token Budget Assessment

Compute token consumption per area. Sum character counts, estimate tokens as `characters / 4`. Compute percentage of total per area. Flag areas consuming >25% as "token-heavy." Token Budget is cross-cutting — reported separately, not in the weighted overall score.

Read `references/output-templates.md` § "Token Budget" for the output format.

---

## Step 3: Per-Area Assessment

For each of the 4 areas, evaluate all 4 dimensions. The 4 dimensions consolidate the original 7 into complementary pairs:

### Assessment Areas

| # | Area | Key Questions |
|---|------|---------------|
| 1 | **Directives** | Three-level architecture clear? Progressive disclosure (summaries + cross-refs)? Directive economy? Policies consistent? Rules add value beyond CLAUDE.md? **Friction:** References to shell patterns that should be backend endpoints current? |
| 2 | **Enforcement** | Mechanisms correct? Edge cases handled? Fast-path exits? Fail-closed/open declared? Shared library usage? Performance throttling? Session state? **Friction:** Output format consistent (JSON `hookSpecificOutput`)? Payload construction safe (no eval/string-concat)? Shell logic that should be endpoints? |
| 3 | **Automation** | Agent definitions complete? Checklists actionable? Mode-based operation? Verdict format? Skill procedures complete? Progressive disclosure? Description trigger-optimized? Frontmatter complete (allowed-tools)? **Friction:** Structured completion signals? Machine-readable verdicts? Safe payload construction? |
| 4 | **Hygiene** | Templates current? Match actual usage? Governance footprint sustainable? **Friction:** Templates reference current endpoint patterns (not stale shell patterns)? |

### Evaluation Dimensions

**Clarity** (consolidates: Contradictions + Ambiguity)
- Cross-reference instructions against ALL other areas
- Check: conflicting directives, stale cross-references, inconsistent terminology, ambiguous instructions, undefined terms, missing scoping, conflicting defaults

**Economy** (consolidates: Duplicity + Conciseness)
- Identify content repeated verbatim or near-verbatim (>20 words) across files
- Intentional CLAUDE.md summaries referencing detailed rules ARE acceptable
- Full duplication without cross-reference is NOT acceptable
- Estimate achievable token savings; flag areas where >10% reduction seems feasible

**Enforcement** (consolidates: Effectiveness + Determinism)
- Does the directive achieve its stated goal?
- Is there an enforcement mechanism (hook, review gate, skill step)?
- Identify "dead directives" — rules with no enforcement, routinely ignored
- Check for redundant enforcement mechanisms
- Score determinism per rubric in `references/scoring-rubrics.md` § "Determinism Rubric"

**Structure** (consolidates: Best Practices)
- Directive architecture: three-level (L0/L1/L2), progressive disclosure (CLAUDE.md summarizes, rules detail, docs deep-dive), directive economy (no verbatim duplication without cross-ref), token efficiency. Score per `references/scoring-rubrics.md` § "Directive Quality Rubric"
- Hook design: fast-path exits (≤5 lines to bail), fail-closed/open declared, throttled state with TTL markers, shared library usage (`hub-query.sh`), <150 lines. Score per `references/scoring-rubrics.md` § "Hook Quality Rubric"
- Skill structure: progressive disclosure (SKILL.md ≤500 lines, references/ for detail), description quality (trigger phrases, 50-500 chars, third person), frontmatter (allowed-tools, version), imperative style, bundled resources. Score per `references/scoring-rubrics.md` § "Skill Quality Rubric"
- Agent definitions: mode-based operation, checklist architecture (critical/warning/suggestion), structured verdict format, gate stamp authority. Score per `references/scoring-rubrics.md` § "Agent Quality Rubric"
- Agent friction (cross-cutting): backend consolidation (shell→endpoint candidates), output format enforcement (structured JSON for machine consumers, free-text for humans), parsing safety (jq over eval/string-concat). Score per `references/scoring-rubrics.md` § "Agent Friction Rubric"

Read `references/output-templates.md` § "Per-Area Assessment" for the output format.

---

## Step 3.5: Enforcement Coverage

After per-area assessment, map every Core Rule (R0-R9) and Policy (P1-P20) to enforcement mechanisms.

1. Read CLAUDE.md §Core Rules and §SDLC Policies
2. For each: identify all enforcement mechanisms (PreToolUse hooks, PostToolUse trackers, Gate Keeper checklist items, skill steps)
3. Classify by strongest mechanism per rubric in `references/scoring-rubrics.md` § "Enforcement Coverage Classification"
4. Produce coverage matrix and summary

Enforcement Coverage is cross-cutting — reported separately, not in the weighted overall score. Read `references/output-templates.md` § "Enforcement Coverage" for the output format.

---

## Step 4: Scoring

Score each dimension 0-5 per rubric in `references/scoring-rubrics.md` § "Per-Area Scoring Rubric". Composite score per area = mean of 4 dimension scores. Weighted overall = SUM(composite * weight). Weights: Directives 35%, Enforcement 30%, Automation 25%, Hygiene 10%.

Read `references/output-templates.md` § "Scorecard" for the output format.

---

## Step 5: Improvement Table

Collect all issues from Step 3. For each, create an improvement entry ranked by impact per `references/scoring-rubrics.md` § "Improvement Impact Levels". Include projected score gain and token savings where applicable.

Read `references/output-templates.md` § "Improvements Table" for the output format.

---

## Step 6: Story Generation

User-guided process for generating SDLC/Refactor story proposals from approved improvements. Read `references/output-templates.md` § "Story Generation" for the full procedure and output format.

This skill does **not auto-create** stories — explicit user approval is required.

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Empty area directory | Score area 0, note "No artifacts found for [area]" |
| Single file in area | Normal assessment, note "Limited sample (1 file)" |
| Context window pressure | Prioritize by area weight: Directives first, Hygiene last |
| Self-assessment | This skill is included in Automation area — no self-exclusion |
| Stale cross-references | Flagged under Clarity dimension |
| Token budget > 35K est. | Flag as "elevated governance footprint" in Token Budget section |
| `--area` mode | Skip non-target areas. Still read CLAUDE.md for cross-referencing. Enforcement Coverage runs for all modes |
| Rule with multiple mechanisms | List all, classify by strongest (Mechanical > Behavioral+Backstop > Behavioral) |

---

## Failure Handling

| Step | Failure | Action |
|------|---------|--------|
| Step 1 | Glob returns no files for an area | Score area 0, continue to next area |
| Step 1 | File unreadable (permissions, encoding) | Note in issues, score dimension as N/A |
| Step 2 | `wc -c` fails | Estimate from line count * 80 chars/line |
| Step 3 | Finding is ambiguous (uncertain if issue) | Log as "uncertain — [reasoning]", do not score as issue |
| Step 3.5 | Rule/policy not clearly documented | Note as "unclear scope" in coverage matrix |
| Step 4 | Dimension not applicable to area | Exclude from composite mean, note "N/A" in scorecard |
| Step 6 | User selects no improvements | End audit with scorecard only |

---

## Notes

- Steps 1-5 are **read-only** — no files are modified
- Re-run after governance changes to track score trends
- The `version` field tracks rubric changes — bump on scoring methodology updates
- For partial audits, use `--area` to reduce context pressure
- The audit report is output as conversation text — not persisted to a file unless requested
- **Migration from v1 (7x7):** D1+D3→Clarity, D2+D4→Economy, D5+D7→Enforcement, D6→Structure. Old areas: CLAUDE.md+Rules→Directives, Hooks→Enforcement, Agents+Skills→Automation, Templates+TokenBudget→Hygiene
