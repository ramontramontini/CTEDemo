#!/usr/bin/env bash

# =========================================
# start.sh — CTEDemo Service Launcher
# =========================================
# Single entry point for all CTEDemo services.
# Reads ALL configuration from .env — no hardcoded ports.
#
# Usage:
#   ./start.sh              → start in mode from .env (default: memory)
#   ./start.sh memory       → in-memory mode (no Docker, no DB)
#   ./start.sh db           → PostgreSQL mode (Docker PG + Alembic)
#   ./start.sh db --seed    → PostgreSQL + seed DB from story files
#   ./start.sh stop         → stop all services (backend, frontend, Docker PG)
#   ./start.sh status       → show running services + config
#
# Configuration (.env):
#   DATA_MODE           memory | db
#   VITE_API_BASE_URL   http://localhost:PORT (backend URL, port extracted)
#   CORS_ORIGINS        http://localhost:PORT (allowed frontend origin)
#   FRONTEND_PORT       frontend dev server port (default: 5174)
#   DATABASE_URL        PostgreSQL connection string (db mode)
#   DB_NAME             database name (default: ctedemo)
# =========================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Detect project root (script may be in root or scripts/)
if [ -f "$SCRIPT_DIR/CLAUDE.md" ]; then
    PROJECT_ROOT="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/../CLAUDE.md" ]; then
    PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
else
    PROJECT_ROOT="$SCRIPT_DIR"
fi

PROJECT_NAME="$(basename "$PROJECT_ROOT")"
PROJECT_LOWER="$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]')"
LOGS_DIR="$PROJECT_ROOT/logs"
DBDEV_COMPOSE="docker-compose.dbdev.yml"
DBDEV_PROJECT="${PROJECT_LOWER}-dbdev"

mkdir -p "$LOGS_DIR"

# Cross-platform helpers (colors, port_in_use, find_pid_by_pattern, etc.)
source "$PROJECT_ROOT/scripts/lib/portable.sh"

# Colors (from portable.sh — respects NO_COLOR and terminal detection)
GREEN="$PORTABLE_GREEN"
BLUE="$PORTABLE_BLUE"
YELLOW="$PORTABLE_YELLOW"
RED="$PORTABLE_RED"
NC="$PORTABLE_NC"

# =========================================
# Load .env ONCE — all config comes from here
# =========================================
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a; source "$PROJECT_ROOT/.env"; set +a
fi

# Extract backend port from VITE_API_BASE_URL
BACKEND_PORT=$(echo "${VITE_API_BASE_URL:-http://localhost:9000}" | sed 's|.*://[^:]*:\([0-9]*\).*|\1|')
BACKEND_PORT="${BACKEND_PORT:-9000}"
FRONTEND_PORT="${FRONTEND_PORT:-5174}"
DB_NAME="${DB_NAME:-$PROJECT_LOWER}"

# Parse arguments
SEED=false
MODE=""
for arg in "$@"; do
    case "$arg" in
        --seed) SEED=true ;;
        memory|db|stop|status) [ -z "$MODE" ] && MODE="$arg" ;;
    esac
done

# Default mode from .env, fallback to memory
if [ -z "$MODE" ]; then
    MODE="${DATA_MODE:-memory}"
fi

# Normalize: dbdev → db (legacy compat)
if [ "$MODE" = "dbdev" ]; then
    MODE="db"
fi

# =========================================
# Helpers
# =========================================

check_docker() {
    if ! command -v docker &>/dev/null; then
        echo -e "${RED}Docker not found. Install Docker Desktop.${NC}"
        exit 1
    fi
    if ! docker info &>/dev/null 2>&1; then
        echo -e "${RED}Docker daemon not running. Start Docker Desktop.${NC}"
        exit 1
    fi
}

check_prereqs() {
    local missing=0
    for cmd in node python3 npm; do
        if ! command -v "$cmd" &>/dev/null; then
            echo -e "${RED}Missing: $cmd${NC}"
            missing=1
        fi
    done
    if [ $missing -eq 1 ]; then exit 1; fi
}

check_port() {
    local port=$1
    local name=$2
    if port_in_use "$port"; then
        local proc=$(find_pid_on_port "$port")
        local cmd=$(ps -p "$proc" -o args= 2>/dev/null || echo "unknown")
        echo -e "${RED}Port $port ($name) in use — PID: $proc  CMD: $cmd${NC}"
        return 1
    fi
    return 0
}

install_deps() {
    if [ ! -d "$PROJECT_ROOT/backend/.venv" ]; then
        echo -e "${BLUE}Installing backend deps...${NC}"
        (cd "$PROJECT_ROOT/backend" && poetry install --no-root)
    fi
    if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
        echo -e "${BLUE}Installing frontend deps...${NC}"
        (cd "$PROJECT_ROOT/frontend" && npm install --legacy-peer-deps)
    fi
}

stop_services() {
    local stopped=0

    # Stop by PID files
    for svc in backend frontend; do
        local pidfile="$LOGS_DIR/${svc}.pid"
        if [ -f "$pidfile" ]; then
            local pid
            pid=$(cat "$pidfile")
            if ps -p "$pid" &>/dev/null; then
                echo -e "${YELLOW}Stopping $svc (PID: $pid)...${NC}"
                kill "$pid" 2>/dev/null || true
                sleep 1
                ps -p "$pid" &>/dev/null && kill -9 "$pid" 2>/dev/null || true
                stopped=1
            fi
            rm -f "$pidfile"
        fi
    done

    # Cleanup orphan uvicorn
    local uvicorn_pids
    uvicorn_pids=$(find_pid_by_pattern "uvicorn src.main:app")
    if [ -n "$uvicorn_pids" ]; then
        echo -e "${YELLOW}Cleaning orphan uvicorn...${NC}"
        echo "$uvicorn_pids" | xargs kill 2>/dev/null || true
        sleep 1
        echo "$uvicorn_pids" | xargs kill -9 2>/dev/null || true
        stopped=1
    fi

    # Cleanup orphan vite (match any vite process in this project)
    local vite_pids
    vite_pids=$(find_pid_by_pattern "node.*vite.*${PROJECT_ROOT}")
    if [ -z "$vite_pids" ]; then
        vite_pids=$(find_pid_by_pattern "vite.*--port")
    fi
    if [ -n "$vite_pids" ]; then
        echo -e "${YELLOW}Cleaning orphan vite...${NC}"
        echo "$vite_pids" | xargs kill 2>/dev/null || true
        sleep 1
        echo "$vite_pids" | xargs kill -9 2>/dev/null || true
        stopped=1
    fi

    # Final fallback: kill anything on our ports
    if port_in_use "$BACKEND_PORT"; then
        echo -e "${YELLOW}Killing process on port $BACKEND_PORT...${NC}"
        kill_on_port "$BACKEND_PORT"
        stopped=1
    fi
    if port_in_use "$FRONTEND_PORT"; then
        echo -e "${YELLOW}Killing process on port $FRONTEND_PORT...${NC}"
        kill_on_port "$FRONTEND_PORT"
        stopped=1
    fi

    # Stop Docker PostgreSQL (data volumes preserved)
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        if docker compose -f "$PROJECT_ROOT/$DBDEV_COMPOSE" -p "$DBDEV_PROJECT" ps --quiet 2>/dev/null | grep -q .; then
            echo -e "${YELLOW}Stopping Docker PostgreSQL (data preserved)...${NC}"
            docker compose -f "$PROJECT_ROOT/$DBDEV_COMPOSE" -p "$DBDEV_PROJECT" down
            stopped=1
        fi
    fi

    if [ $stopped -eq 1 ]; then
        echo -e "${GREEN}All services stopped. DB volumes preserved.${NC}"
    else
        echo -e "${BLUE}No services were running${NC}"
    fi
}

show_status() {
    echo -e "${BLUE}=== ${PROJECT_NAME} Status ===${NC}"
    echo ""

    # Backend
    if [ -f "$LOGS_DIR/backend.pid" ] && ps -p "$(cat "$LOGS_DIR/backend.pid" 2>/dev/null)" &>/dev/null 2>&1; then
        local pid
        pid=$(cat "$LOGS_DIR/backend.pid")
        local health
        health=$(curl -s "http://localhost:$BACKEND_PORT/api/v1/health" 2>/dev/null)
        if [ -n "$health" ]; then
            echo -e "Backend:  ${GREEN}Running${NC} (PID $pid) → :$BACKEND_PORT"
        else
            echo -e "Backend:  ${YELLOW}Running but unhealthy${NC} (PID $pid) → :$BACKEND_PORT"
        fi
    else
        echo -e "Backend:  ${RED}Not running${NC}"
    fi

    # Frontend
    if [ -f "$LOGS_DIR/frontend.pid" ] && ps -p "$(cat "$LOGS_DIR/frontend.pid" 2>/dev/null)" &>/dev/null 2>&1; then
        echo -e "Frontend: ${GREEN}Running${NC} (PID $(cat "$LOGS_DIR/frontend.pid")) → :$FRONTEND_PORT"
    else
        echo -e "Frontend: ${RED}Not running${NC}"
    fi

    # Docker PG
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        if docker compose -f "$PROJECT_ROOT/$DBDEV_COMPOSE" -p "$DBDEV_PROJECT" ps --quiet 2>/dev/null | grep -q .; then
            echo -e "Postgres: ${GREEN}Running${NC} (Docker) → :5432"
        else
            echo -e "Postgres: ${RED}Not running${NC}"
        fi
    fi

    # Config
    echo ""
    echo -e "Config (.env):"
    echo -e "  DATA_MODE:         ${YELLOW}${DATA_MODE:-not set}${NC}"
    echo -e "  Backend port:      ${YELLOW}$BACKEND_PORT${NC}"
    echo -e "  Frontend port:     ${YELLOW}$FRONTEND_PORT${NC}"
    echo -e "  CORS_ORIGINS:      ${YELLOW}${CORS_ORIGINS:-not set}${NC}"
    echo -e "  EUPRAXIS_HUB_URL:  ${YELLOW}${EUPRAXIS_HUB_URL:-not set}${NC}"
    echo ""
}

wait_for_backend() {
    local pid=$1
    local expected_mode=$2

    echo -e "${BLUE}Waiting for backend...${NC}"
    for i in $(seq 1 30); do
        if ! ps -p "$pid" &>/dev/null; then
            echo -e "${RED}Backend crashed. Last 20 lines:${NC}"
            tail -20 "$LOGS_DIR/backend.log"
            exit 1
        fi
        if curl -s "http://localhost:$BACKEND_PORT/api/v1/health" &>/dev/null; then
            echo -e "${GREEN}Backend ready → :$BACKEND_PORT (data_mode=$expected_mode)${NC}"
            return 0
        fi
        sleep 1
    done
    echo -e "${RED}Backend timed out after 30s. Check logs/backend.log${NC}"
    exit 1
}

start_backend() {
    local data_mode=$1

    # Set environment for backend process
    export DATA_MODE="$data_mode"
    export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:$FRONTEND_PORT}"
    export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

    if [ "$data_mode" = "db" ]; then
        export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-ctedemo_dev_2026}@${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-$DB_NAME}}"
    fi

    echo -e "${BLUE}Starting backend (DATA_MODE=${YELLOW}$data_mode${BLUE}) → :$BACKEND_PORT${NC}"

    cd "$PROJECT_ROOT/backend"
    if [ -f ".venv/bin/uvicorn" ]; then
        nohup .venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" \
            > "$LOGS_DIR/backend.log" 2>&1 &
    elif command -v poetry &>/dev/null; then
        nohup poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" \
            > "$LOGS_DIR/backend.log" 2>&1 &
    else
        echo -e "${RED}No uvicorn found. Run 'cd backend && poetry install' first.${NC}"
        exit 1
    fi
    local pid=$!
    echo "$pid" > "$LOGS_DIR/backend.pid"
    cd "$PROJECT_ROOT"

    wait_for_backend "$pid" "$data_mode"
}

start_frontend() {
    local data_mode=${1:-memory}

    export VITE_DATA_MODE="$data_mode"
    export VITE_API_BASE_URL="http://localhost:$BACKEND_PORT/api/v1"

    echo -e "${BLUE}Starting frontend → :$FRONTEND_PORT${NC}"

    cd "$PROJECT_ROOT/frontend"
    nohup npx vite --port "$FRONTEND_PORT" > "$LOGS_DIR/frontend.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$LOGS_DIR/frontend.pid"
    cd "$PROJECT_ROOT"

    sleep 3
    if ps -p "$pid" &>/dev/null; then
        echo -e "${GREEN}Frontend ready → :$FRONTEND_PORT${NC}"
    else
        echo -e "${RED}Frontend failed. Check logs/frontend.log${NC}"
        exit 1
    fi
}

print_summary() {
    local mode=$1
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ${PROJECT_NAME} — ${mode} mode               ${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Frontend:  ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "  Backend:   ${GREEN}http://localhost:$BACKEND_PORT${NC}"
    if [ "$mode" = "db" ]; then
        echo -e "  Postgres:  ${GREEN}localhost:5432${NC} (Docker — data preserved on stop)"
    fi
    echo -e "  API Docs:  ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
    echo -e "  Hub:       ${YELLOW}${EUPRAXIS_HUB_URL:-http://localhost:$BACKEND_PORT}${NC}"
    echo ""
    echo -e "  Logs:  ${YELLOW}tail -f logs/backend.log${NC}"
    echo -e "         ${YELLOW}tail -f logs/frontend.log${NC}"
    echo -e "  Stop:  ${YELLOW}./start.sh stop${NC}"
    echo ""
}

# =========================================
# Main
# =========================================

case "$MODE" in

    stop)
        stop_services
        ;;

    status)
        show_status
        ;;

    memory)
        echo -e "${BLUE}=== ${PROJECT_NAME} — memory mode ===${NC}"
        echo ""
        stop_services 2>/dev/null || true
        check_prereqs
        install_deps
        check_port "$BACKEND_PORT" "backend" || exit 1
        check_port "$FRONTEND_PORT" "frontend" || exit 1

        start_backend "memory"
        start_frontend "memory"
        print_summary "memory"
        ;;

    db)
        echo -e "${BLUE}=== ${PROJECT_NAME} — db mode ===${NC}"
        echo ""
        check_docker
        check_prereqs
        stop_services 2>/dev/null || true
        install_deps

        # Port checks (skip 5432 if our container already runs)
        if port_in_use 5432; then
            if ! docker compose -f "$PROJECT_ROOT/$DBDEV_COMPOSE" -p "$DBDEV_PROJECT" ps --quiet 2>/dev/null | grep -q .; then
                echo -e "${RED}Port 5432 in use by another process. Stop it first.${NC}"
                exit 1
            fi
        fi
        check_port "$BACKEND_PORT" "backend" || exit 1
        check_port "$FRONTEND_PORT" "frontend" || exit 1

        # --- Docker PostgreSQL ---
        if docker compose -f "$PROJECT_ROOT/$DBDEV_COMPOSE" -p "$DBDEV_PROJECT" ps --quiet 2>/dev/null | grep -q .; then
            echo -e "${GREEN}PostgreSQL already running (reusing)${NC}"
        else
            echo -e "${BLUE}Starting PostgreSQL (Docker)...${NC}"
            docker compose -f "$PROJECT_ROOT/$DBDEV_COMPOSE" -p "$DBDEV_PROJECT" up -d
        fi

        # Wait for PG
        echo -e "${BLUE}Waiting for PostgreSQL...${NC}"
        for i in $(seq 1 30); do
            if docker exec "${DBDEV_PROJECT}-db" pg_isready -U postgres &>/dev/null 2>&1; then
                echo -e "${GREEN}PostgreSQL ready${NC}"
                break
            fi
            if command -v pg_isready &>/dev/null && pg_isready -h localhost -p 5432 &>/dev/null 2>&1; then
                echo -e "${GREEN}PostgreSQL ready${NC}"
                break
            fi
            if [ "$i" -eq 30 ]; then
                echo -e "${RED}PostgreSQL timed out after 30s${NC}"
                exit 1
            fi
            sleep 1
        done

        # --- Alembic migrations ---
        echo -e "${BLUE}Running Alembic migrations...${NC}"
        export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-ctedemo_dev_2026}@${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-$DB_NAME}}"
        export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"
        (cd "$PROJECT_ROOT/backend" && poetry run alembic upgrade head)
        echo -e "${GREEN}Migrations applied${NC}"

        # --- Backend + Frontend ---
        start_backend "db"
        start_frontend "db"

        # --- Optional seed ---
        if $SEED; then
            echo -e "${BLUE}Seeding from story files...${NC}"
            seed_response=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$BACKEND_PORT/api/v1/dev/seed-from-files" 2>/dev/null)
            seed_status=$(echo "$seed_response" | tail -1)
            if [ "$seed_status" = "200" ]; then
                echo -e "${GREEN}Seed complete${NC}"
            else
                echo -e "${YELLOW}Seed warning (HTTP $seed_status) — continuing without seed${NC}"
            fi
        fi

        print_summary "db"
        ;;

    *)
        echo "Usage: ./start.sh [memory|db] [--seed] | stop | status"
        echo ""
        echo "  memory    In-memory mode, no Docker needed (default)"
        echo "  db        PostgreSQL mode: Docker PG + Alembic"
        echo "  --seed    Seed DB from story files via API (db mode only)"
        echo "  stop      Stop all services (backend, frontend, Docker PG)"
        echo "  status    Show running services and configuration"
        echo ""
        echo "Reads all config from .env — ports, CORS, hub URL."
        echo "Main worktree: ./start.sh db --seed"
        echo "Default:       ./start.sh memory"
        echo ""
        exit 1
        ;;
esac
