---
name: gate-keeper-bench
description: >
  Benchmark Gate Keeper detection rates against curated test fixtures.
  Runs known-good and known-bad specs/code through Gate Keeper, measures
  detection rate, false positive rate, and variance across 3 runs per fixture.
version: 1.0.0
---

# /gate-keeper-bench — Gate Keeper Benchmarking

**Usage:**
- `/gate-keeper-bench` — benchmark all modes (spec-review + code-review)
- `/gate-keeper-bench --mode spec-review` — benchmark spec-review fixtures only
- `/gate-keeper-bench --mode code-review` — benchmark code-review fixtures only

---

## Step 1: Parse Arguments

1. If `--mode` is provided, validate against `[spec-review, code-review]`. If invalid: output `"Invalid mode '[value]'. Valid modes: spec-review, code-review"` and STOP
2. If `--runs` is provided: output `"Only 3 runs supported (per EAC3). --runs is not accepted."` and STOP
3. Set `MODE_FILTER` to the provided mode, or `null` for all modes

---

## Step 2: Load Fixtures

1. Read `docs/governance/bench-fixtures/manifest.json`
2. Validate manifest has `version` and `fixtures` array. If malformed: STOP with error
3. If `MODE_FILTER` is set: filter fixtures to only those matching the mode
4. For each fixture entry, verify the file exists using Glob: `docs/governance/bench-fixtures/{file}`
   - If missing: log warning `"Fixture [file] not found — skipping"`, remove from list
5. **If zero valid fixtures remain after filtering (WARN + STOP):** Output `⚠️ WARNING: No valid fixtures found after filtering — benchmark cannot proceed. Check manifest.json and fixture files.` STOP. Do NOT enter the invocation loop with an empty fixture set.
6. Report: `"Loaded N fixtures (M spec-review, K code-review)"`

> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT).

---

## Step 3: Gate Keeper Invocation Loop

For each fixture in the filtered list, execute 3 runs:

### 3.1 Per-Run Execution

For run `R` (1, 2, 3) of fixture `F`:

1. **Read** the fixture file content using the Read tool
2. **Determine Gate Keeper mode:**
   - `spec-review` fixtures → invoke as `spec-review`
   - `code-review` fixtures → invoke as `code-review`
3. **Invoke Gate Keeper** via Agent tool:
   ```
   Agent tool:
     subagent_type: gate-keeper
     model: "opus"
     prompt: "[mode] for benchmark fixture [F.file]. Story ID: BENCH-[F.file].
              This is a benchmark evaluation — review the content below as if it were a real [mode] submission.
              [fixture file content]"
   ```
4. **Parse response:**
   - Extract `VERDICT: PASS` or `VERDICT: FAIL` line (regex: `VERDICT:\s*(PASS|FAIL)`)
   - Extract `gate-keeper-summary` fenced JSON block (between `` ```gate-keeper-summary `` and `` ``` ``)
   - If no verdict found: mark run as `inconclusive`
   - If no structured summary: set `summary_available: false`, use verdict-only comparison
5. **Store run result:**
   ```
   {
     fixture: F.file,
     run: R,
     verdict: "PASS"|"FAIL"|"inconclusive",
     expected_verdict: F.expected_verdict,
     match: (verdict == expected_verdict),
     critical_count: (from summary or null),
     warning_count: (from summary or null),
     issues: (from summary or []),
     summary_available: true|false
   }
   ```

### 3.2 Error Handling

- **Gate Keeper subagent fails to launch:** Mark run as `inconclusive`, log warning, continue to next run
- **Gate Keeper produces no VERDICT line:** Mark as `inconclusive`
- **Timeout or context overflow:** Mark as `inconclusive`, note in report

### 3.3 Progress Reporting

After each fixture completes all 3 runs, report:
```
Fixture [N/total]: [file] — [R1 verdict] / [R2 verdict] / [R3 verdict] (expected: [expected])
```

---

## Step 4: Metrics Aggregation and Report

### 4.1 Per-Mode Metrics

For each mode (spec-review, code-review), calculate:

**Detection Rate** (true positives):
- For each known-bad fixture (expected_verdict = FAIL): determine majority verdict across 3 runs
- Detection rate = (known-bad fixtures where majority verdict = FAIL) / (total known-bad fixtures)
- Advisory baseline: >= 66%

**False Positive Rate:**
- For each known-good fixture (expected_verdict = PASS): determine majority verdict across 3 runs
- False positive rate = (known-good fixtures where majority verdict = FAIL) / (total known-good fixtures)
- Target: 0%

**Consistency Score:**
- For each fixture: check if all 3 runs agree on verdict
- Consistency = (fixtures where all 3 runs agree) / (total fixtures)

### 4.2 Per-Fixture Breakdown

For each fixture, produce a row with:
- Fixture name, mode, expected verdict
- Run 1/2/3 verdicts
- Majority verdict, match (correct/incorrect)
- Critical counts per run
- Unexpected findings (issues not in expected_categories)

### 4.3 Category Detection Table

For known-bad fixtures only:
- List each expected category from manifest
- For each run, check if the category appears in the `issues` array (by `category` field)
- Report detection rate per expected category across all runs

### 4.4 Write Report

Write the full report to `temp/bench-report-TIMESTAMP.md` (where TIMESTAMP = `date -u +'%Y%m%d-%H%M%S'`).

**Report format:**

```markdown
# Gate Keeper Benchmarking Report

**Date:** [ISO timestamp]
**Manifest version:** [version]
**Taxonomy version:** [taxonomy_version]
**Fixtures:** [N] ([M] spec-review, [K] code-review)
**Runs per fixture:** 3

---

## Summary Metrics

| Mode | Detection Rate | False Positive Rate | Consistency |
|------|---------------|--------------------:|------------:|
| spec-review | [X]/[Y] ([P]%) | [A]/[B] ([Q]%) | [C]/[D] ([R]%) |
| code-review | [X]/[Y] ([P]%) | [A]/[B] ([Q]%) | [C]/[D] ([R]%) |
| **Overall** | [X]/[Y] ([P]%) | [A]/[B] ([Q]%) | [C]/[D] ([R]%) |

Detection baseline: >= 66% (advisory)

---

## Fixture Results

| # | Fixture | Mode | Expected | Run 1 | Run 2 | Run 3 | Majority | Match | Criticals |
|---|---------|------|----------|-------|-------|-------|----------|-------|-----------|
| 1 | [file] | [mode] | [PASS/FAIL] | [v] | [v] | [v] | [v] | [Y/N] | [c1/c2/c3] |

---

## Category Detection (Known-Bad Fixtures)

| Fixture | Category | Run 1 | Run 2 | Run 3 | Detection |
|---------|----------|-------|-------|-------|-----------|
| [file] | [category] | [Y/N] | [Y/N] | [Y/N] | [X/3] |

---

## Unexpected Findings

[List any issues found that were NOT in expected_categories]

---

## Inconclusive Runs

[List any runs that produced no verdict or failed to execute]
```

### 4.5 Output Summary

After writing the report file, output a concise summary to the user:
```
Gate Keeper Benchmarking Complete
  Detection: [X]% | False Positives: [Y]% | Consistency: [Z]%
  Report: temp/bench-report-[TIMESTAMP].md
  Fixtures: [N] | Runs: [N*3] | Inconclusive: [I]
```

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| All runs inconclusive for a fixture | Report fixture as "inconclusive", exclude from rate calculations |
| No fixtures match mode filter | Report: "No fixtures found for mode [mode]" and STOP |
| Manifest file missing | STOP with error: "Manifest not found at docs/governance/bench-fixtures/manifest.json" |
| Gate Keeper catches unexpected issues on known-good | Report in "Unexpected Findings" section, do NOT count as false positive unless verdict is FAIL |
| Tied verdict (e.g., 1 PASS, 1 FAIL, 1 inconclusive) | Use non-inconclusive majority. If tied 1-1: report as "split" |

---

## Failure Handling

| Step | Failure | Action |
|------|---------|--------|
| Step 2 | Manifest missing or malformed | STOP with error message |
| Step 2 | Fixture file missing | Skip fixture with warning, continue |
| Step 3 | Gate Keeper subagent fails | Mark run as inconclusive, continue |
| Step 3 | No VERDICT in response | Mark run as inconclusive, continue |
| Step 4 | All fixtures inconclusive | Report "No valid results" — metrics all N/A |
| Step 4 | Write to temp/ fails | Output report to conversation instead |

---

## Notes

- This skill does NOT modify Gate Keeper or any governance artifacts — it is read-only except for the report file in `temp/`
- Benchmark runs produce real Gate Keeper invocations that generate ledger entries in `docs/governance/gate-keeper-ledger.jsonl`. These are identifiable by their `story_id` field matching fixture names (e.g., `BENCH-good-spec.md`)
- The 3-run count is fixed per EAC3 of the SDLC_SHARPENING epic
- Re-run after Gate Keeper checklist changes to measure detection rate trends
