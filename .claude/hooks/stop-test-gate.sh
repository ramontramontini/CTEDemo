#!/usr/bin/env bash
# Stop hook: Test enforcement gate (000376, 001047 AC4, 2026-03-25.00-04-05)
# Runs all test suites before Claude finishes a session — conditional on uncommitted code changes.
# Includes E2E tests when integration test files exist (AC4).
# Exit 1 = tests failed (blocks session completion)
# Exit 0 = tests passed (session can complete)

ROOT_DIR="${CLAUDE_PROJECT_DIR:-.}"
TEST_RUNNER="$ROOT_DIR/run-tests.sh"

# Graceful fallback if run-tests.sh doesn't exist
if [ ! -f "$TEST_RUNNER" ]; then
  echo "⚠️  run-tests.sh not found at $TEST_RUNNER — skipping test gate"
  exit 0
fi

# Skip tests if no uncommitted code changes on code paths (2026-03-25.00-04-05)
# Checks both staged and unstaged changes (unlike pre-commit-test-gate.sh which checks staged-only)
CODE_CHANGES=$(git -C "$ROOT_DIR" status --porcelain backend/src/ frontend/src/ tests/ 2>/dev/null)
if [ -z "$CODE_CHANGES" ]; then
  echo "✅ No uncommitted code changes — skipping test gate."
  exit 0
fi

# Determine if E2E tests should be included
# Include --with-e2e if integration test files exist
E2E_FLAG=""
if ls "$ROOT_DIR/tests/integration/"*.spec.* 1>/dev/null 2>&1 || \
   ls "$ROOT_DIR/tests/integration/"*/*.spec.* 1>/dev/null 2>&1; then
  E2E_FLAG="--with-e2e"
fi

# Run all test suites (frontend, backend, API, + E2E if applicable)
if bash "$TEST_RUNNER" $E2E_FLAG 2>&1; then
  echo ""
  echo "✅ Test gate passed — all suites green."
  exit 0
else
  echo ""
  echo "❌ Test gate FAILED — fix failing tests before finishing."
  exit 1
fi
