#!/usr/bin/env bash
# start.sh — starts FilmTracker backend (uvicorn) and frontend (vite) in the background
# Usage:  ./start.sh          — start both services
#         ./start.sh stop      — stop both services using saved PIDs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/.pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
BACKEND_LOG="$SCRIPT_DIR/.pids/backend.log"
FRONTEND_LOG="$SCRIPT_DIR/.pids/frontend.log"

VENV="$SCRIPT_DIR/backend/venv/bin"

# ── Stop ─────────────────────────────────────────────────────────────────────
stop_services() {
  local stopped=0
  if [[ -f "$BACKEND_PID_FILE" ]]; then
    local pid
    pid=$(cat "$BACKEND_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && echo "Stopped backend  (PID $pid)"
      stopped=1
    fi
    rm -f "$BACKEND_PID_FILE"
  fi
  if [[ -f "$FRONTEND_PID_FILE" ]]; then
    local pid
    pid=$(cat "$FRONTEND_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && echo "Stopped frontend (PID $pid)"
      stopped=1
    fi
    rm -f "$FRONTEND_PID_FILE"
  fi
  [[ $stopped -eq 0 ]] && echo "No running services found."
}

if [[ "${1:-}" == "stop" ]]; then
  stop_services
  exit 0
fi

# ── Start ─────────────────────────────────────────────────────────────────────
mkdir -p "$PID_DIR"

# Stop any previously running instances first
stop_services 2>/dev/null || true

echo ""
echo "Starting FilmTracker..."
echo ""

# Backend
(
  cd "$SCRIPT_DIR/backend"
  "$VENV/uvicorn" app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    > "$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID_FILE"
)
echo "Backend  started — http://localhost:8000  (log: .pids/backend.log,  PID: $(cat "$BACKEND_PID_FILE"))"

# Frontend
(
  cd "$SCRIPT_DIR/frontend"
  npm run dev -- --host \
    > "$FRONTEND_LOG" 2>&1 &
  echo $! > "$FRONTEND_PID_FILE"
)
echo "Frontend started — http://localhost:5173  (log: .pids/frontend.log, PID: $(cat "$FRONTEND_PID_FILE"))"

echo ""
echo "Run './start.sh stop' to stop both services."
