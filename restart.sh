#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT/backend"
BACKEND_ENV="$BACKEND_DIR/.env"
STATE_DIR="$ROOT/.data"
PROCESS_FILE="$STATE_DIR/backend.process"
LOG_FILE="$STATE_DIR/backend.log"
BACKEND_HOST="${CLAWITH_BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${CLAWITH_BACKEND_PORT:-8008}"
HEALTH_ATTEMPTS="${CLAWITH_HEALTH_ATTEMPTS:-50}"
STOP_ATTEMPTS="${CLAWITH_STOP_ATTEMPTS:-50}"
UVICORN_BIN="$BACKEND_DIR/.venv/bin/uvicorn"
PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
PROCESS_MARKER="$UVICORN_BIN app.main:app"
cleanup_armed=false
pending_pid=""
pending_start=""

read_evidence() {
    evidence_pid="$(sed -n 's/^pid=//p' "$PROCESS_FILE")"
    evidence_start="$(sed -n 's/^start=//p' "$PROCESS_FILE")"
    [ -n "$evidence_pid" ] && [[ "$evidence_pid" =~ ^[0-9]+$ ]] && [ -n "$evidence_start" ]
}

process_start_identity() {
    ps -p "$1" -o lstart= 2>/dev/null | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || true
}

process_command() {
    ps -p "$1" -o command= 2>/dev/null || true
}

process_matches_identity() {
    owned_pid="$1"
    owned_start="$2"
    [ "$(process_start_identity "$owned_pid")" = "$owned_start" ] || return 1
    command_line="$(process_command "$owned_pid")"
    case "$command_line" in
        *"$PROCESS_MARKER"*"--workers 1"*) ;;
        *) return 1 ;;
    esac
}

terminate_owned_process() {
    owned_pid="$1"
    owned_start="$2"
    kill -0 "$owned_pid" 2>/dev/null || return 0
    process_matches_identity "$owned_pid" "$owned_start" || return 1
    kill -TERM "$owned_pid"
    for _ in $(seq 1 "$STOP_ATTEMPTS"); do
        if ! kill -0 "$owned_pid" 2>/dev/null; then
            return 0
        fi
        sleep 0.1
    done
    return 1
}

terminate_pending_process() {
    kill -0 "$pending_pid" 2>/dev/null || return 0
    command_line="$(process_command "$pending_pid")"
    case "$command_line" in
        *"$PROCESS_MARKER"*"--workers 1"*) ;;
        *) return 1 ;;
    esac
    kill -TERM "$pending_pid"
    for _ in $(seq 1 "$STOP_ATTEMPTS"); do
        if ! kill -0 "$pending_pid" 2>/dev/null; then
            return 0
        fi
        sleep 0.1
    done
    return 1
}

stop_owned_process() {
    [ -f "$PROCESS_FILE" ] || return 0
    if ! read_evidence; then
        echo "Refusing to signal process with malformed ownership evidence: $PROCESS_FILE" >&2
        return 1
    fi
    if ! kill -0 "$evidence_pid" 2>/dev/null; then
        rm -f "$PROCESS_FILE"
        return 0
    fi
    if ! process_matches_identity "$evidence_pid" "$evidence_start"; then
        echo "Refusing to signal process without matching ownership evidence: $evidence_pid" >&2
        return 1
    fi
    if ! terminate_owned_process "$evidence_pid" "$evidence_start"; then
        echo "Owned target backend did not stop; ownership evidence retained: $PROCESS_FILE" >&2
        return 1
    fi
    rm -f "$PROCESS_FILE"
}

cleanup_after_launch() {
    status=$?
    trap - EXIT
    if [ "$cleanup_armed" = true ]; then
        if [ -f "$PROCESS_FILE" ]; then
            stop_owned_process || status=1
        elif [ -n "$pending_pid" ]; then
            if [ -n "$pending_start" ]; then
                terminate_owned_process "$pending_pid" "$pending_start" || status=1
            elif ! terminate_pending_process; then
                printf 'pid=%s\nstart=unverified\n' "$pending_pid" > "$PROCESS_FILE"
                status=1
            fi
        fi
    fi
    exit "$status"
}

trap cleanup_after_launch EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if [ ! -f "$BACKEND_ENV" ]; then
    echo "Missing backend/.env. Run bash setup.sh first." >&2
    exit 1
fi
for command in curl ps; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Required command is unavailable: $command" >&2
        exit 1
    fi
done
for executable in "$UVICORN_BIN" "$PYTHON_BIN"; do
    if [ ! -x "$executable" ]; then
        echo "Required Backend executable is unavailable: $executable" >&2
        exit 1
    fi
done

mkdir -p "$STATE_DIR"
stop_owned_process

cd "$BACKEND_DIR"
startup_id="$($PYTHON_BIN -c 'import secrets; print(secrets.token_hex(16))')"
nohup bash -c 'trap - INT TERM; exec "$@"' g002-backend \
    env STARTUP_INSTANCE_ID="$startup_id" \
    "$UVICORN_BIN" app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --workers 1 \
    > "$LOG_FILE" 2>&1 &
backend_pid=$!
pending_pid="$backend_pid"
cleanup_armed=true
backend_start="$(process_start_identity "$backend_pid")"
if [ -z "$backend_start" ]; then
    echo "Could not capture target backend start identity: pid=$backend_pid" >&2
    exit 1
fi
pending_start="$backend_start"
TEMP_PROCESS_FILE="$(mktemp "$STATE_DIR/backend.process.tmp.XXXXXX")"
printf 'pid=%s\nstart=%s\nstartup_id=%s\n' \
    "$backend_pid" "$backend_start" "$startup_id" > "$TEMP_PROCESS_FILE"
mv "$TEMP_PROCESS_FILE" "$PROCESS_FILE"

for _ in $(seq 1 "$HEALTH_ATTEMPTS"); do
    health_response="$(curl --fail --silent --max-time 1 "http://${BACKEND_HOST}:${BACKEND_PORT}/api/health" || true)"
    if printf '%s' "$health_response" | grep -q '"status":"ok"' \
        && printf '%s' "$health_response" | grep -q "\"process_pid\":${backend_pid}" \
        && printf '%s' "$health_response" | grep -q "\"startup_id\":\"${startup_id}\""; then
        cleanup_armed=false
        trap - EXIT INT TERM
        echo "G002 target backend health check passed: http://${BACKEND_HOST}:${BACKEND_PORT}/api/health"
        echo "Backend log: $LOG_FILE"
        exit 0
    fi
    if ! kill -0 "$backend_pid" 2>/dev/null; then
        echo "Target backend exited before becoming healthy. See $LOG_FILE" >&2
        exit 1
    fi
    sleep 0.2
done

echo "Target backend health check timed out. See $LOG_FILE" >&2
exit 1
