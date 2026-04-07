#!/usr/bin/env bash
# portable.sh — Cross-platform helper functions for Linux, macOS, and Windows (Git Bash/WSL)
#
# Usage: source scripts/lib/portable.sh
#
# Provides:
#   sed_inplace     — portable sed -i (GNU vs BSD)
#   port_in_use     — check if a TCP port is in use (lsof > ss > nc fallback)
#   find_pid_by_pattern — find PIDs matching a pattern (pgrep > ps fallback)
#   kill_by_pattern — kill processes matching a pattern
#   PORTABLE_GREEN, PORTABLE_RED, PORTABLE_YELLOW, PORTABLE_BLUE, PORTABLE_NC — color vars
#
# NOT wrapped (available on all targets including Git Bash/MSYS2):
#   nohup — ships with Git Bash; no fallback needed
#   ps -o args= — works on BSD (macOS) and GNU (Linux); Git Bash has /usr/bin/ps

# =============================================================================
# sed_inplace — portable in-place sed edit
# Usage: sed_inplace "s/old/new/" file
# =============================================================================
sed_inplace() {
    if sed --version 2>/dev/null | grep -q GNU; then
        sed -i "$@"
    else
        sed -i '' "$@"
    fi
}

# =============================================================================
# Color variables — respect NO_COLOR (https://no-color.org/) and terminal detection
# NO_COLOR: any non-empty value disables color. Empty string = color enabled.
# FORCE_COLOR: any non-empty value forces color on (overrides terminal check, not NO_COLOR).
# Prefixed with PORTABLE_ to avoid clashing with scripts that define their own.
# =============================================================================
if [ -n "${NO_COLOR:-}" ]; then
    # NO_COLOR is set and non-empty — disable all colors
    PORTABLE_GREEN=''
    PORTABLE_RED=''
    PORTABLE_YELLOW=''
    PORTABLE_BLUE=''
    PORTABLE_CYAN=''
    PORTABLE_NC=''
elif [ -t 1 ] || [ -n "${FORCE_COLOR:-}" ]; then
    # Terminal detected or FORCE_COLOR set — enable colors
    PORTABLE_GREEN='\033[0;32m'
    PORTABLE_RED='\033[0;31m'
    PORTABLE_YELLOW='\033[1;33m'
    PORTABLE_BLUE='\033[0;34m'
    PORTABLE_CYAN='\033[0;36m'
    PORTABLE_NC='\033[0m'
else
    # Not a terminal and no FORCE_COLOR — disable colors
    PORTABLE_GREEN=''
    PORTABLE_RED=''
    PORTABLE_YELLOW=''
    PORTABLE_BLUE=''
    PORTABLE_CYAN=''
    PORTABLE_NC=''
fi

# =============================================================================
# port_in_use — check if a TCP port is occupied
# Usage: port_in_use PORT
# Returns: 0 if port is in use, 1 if free (or cannot check)
# =============================================================================
port_in_use() {
    local port="$1"

    # Try lsof (macOS, most Linux)
    # -sTCP:LISTEN filters to LISTEN sockets only — excludes ESTABLISHED client
    # connections (e.g., macOS WebKit processes connecting TO a port)
    if command -v lsof &>/dev/null; then
        lsof -i :"$port" -sTCP:LISTEN &>/dev/null && return 0 || return 1
    fi

    # Try ss (Linux, some minimal containers)
    # -l flag already filters to LISTEN sockets
    if command -v ss &>/dev/null; then
        ss -tlnp 2>/dev/null | grep -qE ":${port}[[:space:]]" && return 0 || return 1
    fi

    # Try nc (netcat — widely available)
    if command -v nc &>/dev/null; then
        nc -z localhost "$port" 2>/dev/null && return 0 || return 1
    fi

    # No tool available — warn and assume free
    echo "portable.sh: no port-check tool found (lsof, ss, nc). Assuming port $port is free." >&2
    return 1
}

# =============================================================================
# find_pid_on_port — find the PID of a process listening on a TCP port
# Usage: find_pid_on_port PORT
# Output: single PID (first match) or empty string
# =============================================================================
find_pid_on_port() {
    local port="$1"

    # Try lsof (macOS, most Linux)
    # -sTCP:LISTEN filters to the actual listener, not client connections
    if command -v lsof &>/dev/null; then
        lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null | head -1
        return
    fi

    # Try ss (Linux)
    if command -v ss &>/dev/null; then
        ss -tlnp 2>/dev/null | grep -E ":${port}[[:space:]]" | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -1
        return
    fi

    # No tool available — return empty
    echo ""
}

# =============================================================================
# kill_on_port — kill the process listening on a TCP port
# Usage: kill_on_port PORT
# =============================================================================
kill_on_port() {
    local port="$1"

    # Try lsof — only kill the LISTEN process, not client connections
    if command -v lsof &>/dev/null; then
        lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null | xargs kill 2>/dev/null || true
        return
    fi

    # Fallback: find PID and kill
    local pid
    pid=$(find_pid_on_port "$port")
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null || true
    fi
}

# =============================================================================
# find_pid_by_pattern — find process IDs matching a pattern
# Usage: find_pid_by_pattern "pattern"
# Output: space-separated PIDs (may be empty)
# =============================================================================
find_pid_by_pattern() {
    local pattern="$1"

    # Try pgrep (macOS, most Linux)
    if command -v pgrep &>/dev/null; then
        pgrep -f "$pattern" 2>/dev/null || true
        return
    fi

    # Fallback: ps + grep (Git Bash, minimal containers)
    ps aux 2>/dev/null | grep -v grep | grep "$pattern" | awk '{print $2}' || true
}

# =============================================================================
# kill_by_pattern — kill processes matching a pattern
# Usage: kill_by_pattern "pattern" [SIGNAL]
# =============================================================================
kill_by_pattern() {
    local pattern="$1"
    local signal="${2:-TERM}"
    local pids

    pids=$(find_pid_by_pattern "$pattern")
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -"$signal" 2>/dev/null || true
    fi
}
