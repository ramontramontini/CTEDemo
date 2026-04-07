---
name: next
description: >
  Suggest next work following Kanban priority (Policy 4). Queries API for available
  stories with dependency resolution. Use after completing a story or when starting a session.
---

# /next — Next Work Suggestion

**Usage:** `/next`

> **Sources:** CLAUDE.md §Policy 4 (Kanban Prioritization), §Policy 5 (Story Suggestion Format)
>
> **Hub URL:** All story API calls target `$EUPRAXIS_HUB_URL` (from `.env`, default `http://localhost:8000`).
>
> **Error handling:** See `.claude/skills/error-handling-convention.md` for the 3-tier convention (STOP/WARN/SILENT).
> - **API unreachable (WARN):** Output `⚠️ WARNING: Hub API unreachable at $EUPRAXIS_HUB_URL — cannot query available work — recovery: check if main backend is running`. STOP.
> - **API returns empty results (informational):** Output "No stories available." — this is NOT an error, just an empty queue.
> - Distinguish API failure (connection error, 5xx) from empty results (200 with empty data) — different messages for each.

---

## Step 1: Kanban Priority Check

> "Stop Starting, Start Finishing" — CLAUDE.md §Policy 4

Check for active work:
```
GET $EUPRAXIS_HUB_URL/api/v1/stories?status=in_progress
GET $EUPRAXIS_HUB_URL/api/v1/stories?status=claimed
```

If stories found in progress: warn per Kanban priority, use AskUserQuestion (Continue / Cancel / Show available anyway).

---

## Step 2: Get Available Stories

```
GET $EUPRAXIS_HUB_URL/api/v1/queue/ready_to_pull
```

Returns ordered available stories with dependency resolution already applied by QueueService.

**Fallback** (if queue endpoint unavailable):
```
GET $EUPRAXIS_HUB_URL/api/v1/stories?status=ready_to_pull
```
**Note:** This fallback does NOT apply dependency resolution — results may include stories with unmet dependencies. Warn the user.

If empty result: "No stories available."

---

## Step 3: Build Policy 5 Table

Present ALL stories from response as:

| # | Epic | Name | Type | Dependencies | Complexity | Time | Ready |
|---|------|------|------|-------------|------------|------|-------|

- **Complexity:** Simple (1-2 ACs) / Medium (3-4 ACs) / Complex (5+ ACs)
- **Time:** Small (<1h) / Medium (1-3h) / Large (3h+)
- **Ready:** Yes (from queue/ready_to_pull) / Blocked (from fallback if deps unmet)

---

## Step 4: Present to User

Use AskUserQuestion with top candidates as options. Order by: Priority → Type (BUG first) → FIFO.

**This skill is read-only** — no state modifications. AskUserQuestion is mandatory.
