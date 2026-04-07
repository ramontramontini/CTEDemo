# Output Templates — sdlc-audit

> Reference file for `/sdlc-audit` skill. Read on-demand when generating output for each step.

---

## Token Budget (Step 2)

```
## Token Budget

| Area | Files | Characters | Est. Tokens | % of Total |
|------|-------|------------|-------------|------------|
| Directives | [N] | [chars] | [tokens] | [pct]% |
| Enforcement | [N] | [chars] | [tokens] | [pct]% |
| Automation | [N] | [chars] | [tokens] | [pct]% |
| Hygiene | [N] | [chars] | [tokens] | [pct]% |
| **Total** | **[N]** | **[chars]** | **[tokens]** | **100%** |

Token-heavy (>25%): [list areas or "none"]
```

Token estimation heuristic: `characters / 4`.

---

## Per-Area Assessment (Step 3)

```
### [Area Name] — [Composite Score]/5

**Strengths:**
- [Key strength 1]
- [Key strength 2]

**Issues:**

| # | Issue | Dimension | Severity |
|---|-------|-----------|----------|
| 1 | [description] | [Dimension name] | Critical/Warning/Suggestion |
| 2 | [description] | [Dimension name] | Critical/Warning/Suggestion |
```

---

## Enforcement Coverage (Step 3.5)

```
## Enforcement Coverage

| # | Rule/Policy | Description | Mechanism(s) | Classification |
|---|-------------|-------------|--------------|----------------|
| R0 | Rule 0: Environment | DATA_MODE bifurcation | forbidden-command-blocker.sh | Mechanical |
| R1 | Rule 1: Story + Plan | Every change needs story + plan | spec-ceremony-gate + story-gate + plan-review-gate | Mechanical |
| ... | ... | ... | ... | ... |
| P2 | Policy 2: Filename Format | Story filename format | API schema validation | Mechanical |
| ... | ... | ... | ... | ... |
| P20 | Policy 20: Regression | Regression coverage rules | Gate Keeper code-review | Behavioral+Backstop |

### Summary
Mechanical: [N]/[total] | Behavioral+Backstop: [N]/[total] | Behavioral Only: [N]/[total] | Ungoverned: [N]/[total]
```

---

## Scorecard (Step 4)

```
## Scorecard

| Area | Clarity | Economy | Enforcement | Structure | Composite | Weight | Weighted |
|------|---------|---------|-------------|-----------|-----------|--------|----------|
| Directives | [0-5] | [0-5] | [0-5] | [0-5] | [X.X] | 35% | [X.XX] |
| Enforcement | [0-5] | [0-5] | [0-5] | [0-5] | [X.X] | 30% | [X.XX] |
| Automation | [0-5] | [0-5] | [0-5] | [0-5] | [X.X] | 25% | [X.XX] |
| Hygiene | [0-5] | [0-5] | [0-5] | [0-5] | [X.X] | 10% | [X.XX] |
| **Overall** | | | | | | | **[X.XX]/5** |

Token Budget: [X.X]/5 (cross-cutting, not in weighted total)
Enforcement Coverage: Mechanical [N]/[T] | Behavioral+Backstop [N]/[T] | Behavioral Only [N]/[T] | Ungoverned [N]/[T]
```

---

## Improvements Table (Step 5)

```
## Improvements (Ranked by Impact)

| # | Improvement | Impact | Token Savings | Areas | Projected Gain |
|---|------------|--------|---------------|-------|----------------|
| 1 | [description] | Critical | ~[N] tokens | [areas] | +[X.XX] |
| 2 | [description] | High | — | [areas] | +[X.XX] |
| ... | ... | ... | ... | ... | ... |

Projected overall after all improvements: [X.XX]/5 (current: [X.XX]/5)
```

---

## Story Generation (Step 6)

### 6.1 Select Improvements

Present via AskUserQuestion:
```
"Which improvements should I generate story proposals for?"
Options: "All", "High-impact only (Critical + High)", "Custom selection"
```

### 6.2 Proposal Table

```
| # | Type | Title | Scope | Grouping |
|---|------|-------|-------|----------|
| I[N] | SDLC/Refactor | [Short title] | [1-3 sentence scope] | Standalone / Epic: [name] |
```

**Type guidance:**
- **SDLC** — directive changes, policy updates, documentation restructuring
- **Refactor** — hook code changes, structural reorganization of existing artifacts

**Grouping:** 3+ related improvements → suggest epic. Isolated → standalone.

### 6.3 Approval

Present via AskUserQuestion:
```
"Approve these story proposals? I will NOT auto-create them."
Options: "Approve all — create stories", "Approve selection", "Skip — no stories"
```

If approved: create stories via standard upstream workflow. If skipped: end audit.
