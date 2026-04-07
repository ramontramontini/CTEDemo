#!/usr/bin/env bash
# Aggregate token usage from Claude Code JSONL conversation files.
#
# Outputs JSON to stdout: {input_tokens, output_tokens, cache_read_tokens, cache_write_tokens}
# Outputs nothing (empty stdout) and exits 0 if no data found.
#
# Environment:
#   CLAUDE_HOME     — override ~/.claude (for testing)
#   MOCK_PPID       — override $PPID (for testing)
#   MOCK_CWD        — override working directory (for testing)

set -euo pipefail

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
PARENT_PID="${MOCK_PPID:-$PPID}"
CWD="${MOCK_CWD:-$(pwd)}"

# 1. Resolve session ID from session file
SESSION_FILE="$CLAUDE_HOME/sessions/${PARENT_PID}.json"
if [ ! -f "$SESSION_FILE" ]; then
  # Fallback: scan session files for matching CWD
  SESSION_ID=""
  if [ -d "$CLAUDE_HOME/sessions" ]; then
    for f in "$CLAUDE_HOME/sessions"/*.json; do
      [ -f "$f" ] || continue
      file_cwd=$(jq -r '.cwd // empty' "$f" 2>/dev/null)
      if [ "$file_cwd" = "$CWD" ]; then
        SESSION_ID=$(jq -r '.sessionId // empty' "$f" 2>/dev/null)
        break
      fi
    done
  fi
  if [ -z "$SESSION_ID" ]; then
    exit 0
  fi
else
  SESSION_ID=$(jq -r '.sessionId // empty' "$SESSION_FILE" 2>/dev/null)
  if [ -z "$SESSION_ID" ]; then
    exit 0
  fi
fi

# 2. Derive project path hash from CWD
PROJECT_HASH=$(echo "$CWD" | tr '/' '-')

# 3. Locate JSONL files
PROJECT_DIR="$CLAUDE_HOME/projects/$PROJECT_HASH"
MAIN_JSONL="$PROJECT_DIR/$SESSION_ID.jsonl"
SUBAGENT_DIR="$PROJECT_DIR/$SESSION_ID/subagents"

if [ ! -f "$MAIN_JSONL" ]; then
  exit 0
fi

# 4. Collect all JSONL files (main + subagents)
JSONL_FILES=("$MAIN_JSONL")
if [ -d "$SUBAGENT_DIR" ]; then
  for f in "$SUBAGENT_DIR"/agent-*.jsonl; do
    [ -f "$f" ] && JSONL_FILES+=("$f")
  done
fi

# 5. Aggregate usage from all assistant messages across all files
# Uses grep to filter assistant messages, then jq to extract and sum usage fields.
# Malformed lines are silently skipped (grep only matches valid JSON patterns,
# jq's -R + fromjson? handles parse errors).
{
  for f in "${JSONL_FILES[@]}"; do
    grep '"type"[[:space:]]*:[[:space:]]*"assistant"' "$f" 2>/dev/null || true
  done
} | jq -s '
  map(
    .message.usage // empty
    | {
        input_tokens: (.input_tokens // 0),
        output_tokens: (.output_tokens // 0),
        cache_read_tokens: (.cache_read_input_tokens // 0),
        cache_write_tokens: (.cache_creation_input_tokens // 0)
      }
  )
  | if length == 0 then empty
    else {
      input_tokens: (map(.input_tokens) | add),
      output_tokens: (map(.output_tokens) | add),
      cache_read_tokens: (map(.cache_read_tokens) | add),
      cache_write_tokens: (map(.cache_write_tokens) | add)
    }
    end
' 2>/dev/null || true
