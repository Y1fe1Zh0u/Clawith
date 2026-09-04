#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT/backend"
BACKEND_ENV="$BACKEND_DIR/.env"
STATE_DIR="$ROOT/.data"
PID_FILE="$STATE_DIR/backend.pid"
LOG_FILE="$STATE_DIR/backend.log"
BACKEND_HOST="${CLAWITH_BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${CLAWITH_BACKEND_PORT:-8008}"

if [ ! -f "$BACKEND_ENV" ]; then
    echo "Missing backend/.env. Run bash setup.sh first." >&2
    exit 1
fi
for command in uv curl; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Required command is unavailable: $command" >&2
        exit 1
    fi
done

mkdir -p "$STATE_DIR"
if [ -f "$PID_FILE" ]; then
    existing_pid="$(cat "$PID_FILE")"
    if [[ "$existing_pid" =~ ^[0-9]+$ ]] && kill -0 "$existing_pid" 2>/dev/null; then
        kill "$existing_pid"
        for _ in $(seq 1 50); do
            if ! kill -0 "$existing_pid" 2>/dev/null; then
                break
            fi
            sleep 0.1
        done
        if kill -0 "$existing_pid" 2>/dev/null; then
            echo "Existing target backend did not stop: $existing_pid" >&2
            exit 1
        fi
    fi
    rm -f "$PID_FILE"
fi

cd "$BACKEND_DIR"
nohup uv run uvicorn app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --workers 1 > "$LOG_FILE" 2>&1 &
backend_pid=$!
printf '%s\n' "$backend_pid" > "$PID_FILE"

for _ in $(seq 1 50); do
    if curl --fail --silent --max-time 1 "http://${BACKEND_HOST}:${BACKEND_PORT}/api/health" | grep -q '"status":"ok"'; then
        echo "G002 target backend health check passed: http://${BACKEND_HOST}:${BACKEND_PORT}/api/health"
        echo "Backend log: $LOG_FILE"
        exit 0
    fi
    if ! kill -0 "$backend_pid" 2>/dev/null; then
        echo "Target backend exited before becoming healthy. See $LOG_FILE" >&2
        rm -f "$PID_FILE"
        exit 1
    fi
    sleep 0.2
done

kill "$backend_pid" 2>/dev/null || true
rm -f "$PID_FILE"
echo "Target backend health check timed out. See $LOG_FILE" >&2
exit 1
