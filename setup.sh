#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT/backend"
BACKEND_ENV="$BACKEND_DIR/.env"
BACKEND_ENV_EXAMPLE="$BACKEND_DIR/.env.example"
TARGET_DATABASE="clawith_target"
TARGET_ROLE="clawith"
PG_HOST="${CLAWITH_PG_HOST:-localhost}"
PG_PORT="${CLAWITH_PG_PORT:-5432}"
PG_ADMIN_USER="${CLAWITH_PG_ADMIN_USER:-${USER:-postgres}}"
INSTALL_DEV=false

for argument in "$@"; do
    case "$argument" in
        --dev) INSTALL_DEV=true ;;
        *) echo "Unsupported setup option: $argument" >&2; exit 2 ;;
    esac
done

for command in uv psql createuser createdb; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Required command is unavailable: $command" >&2
        exit 1
    fi
done

if [ ! -f "$BACKEND_ENV_EXAMPLE" ]; then
    echo "Missing target environment template: $BACKEND_ENV_EXAMPLE" >&2
    exit 1
fi

TARGET_DATABASE_URL="postgresql+asyncpg://${TARGET_ROLE}:${TARGET_ROLE}@${PG_HOST}:${PG_PORT}/${TARGET_DATABASE}?ssl=disable"
TEMP_ENV="$(mktemp "$BACKEND_DIR/.env.tmp.XXXXXX")"
trap 'rm -f "$TEMP_ENV"' EXIT

while IFS= read -r line || [ -n "$line" ]; do
    if [[ "$line" =~ ^([A-Z][A-Z0-9_]*)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        if [ "$key" = "DATABASE_URL" ]; then
            value="$TARGET_DATABASE_URL"
        elif [ -f "$BACKEND_ENV" ]; then
            existing="$(grep -m 1 "^${key}=" "$BACKEND_ENV" || true)"
            if [ -n "$existing" ]; then
                value="${existing#*=}"
            fi
        fi
        printf '%s=%s\n' "$key" "$value" >> "$TEMP_ENV"
    else
        printf '%s\n' "$line" >> "$TEMP_ENV"
    fi
done < "$BACKEND_ENV_EXAMPLE"

mv "$TEMP_ENV" "$BACKEND_ENV"
trap - EXIT
chmod 600 "$BACKEND_ENV"
echo "Prepared backend/.env from backend/.env.example"

PSQL_ADMIN=(psql --host "$PG_HOST" --port "$PG_PORT" --username "$PG_ADMIN_USER" --dbname postgres --set ON_ERROR_STOP=1)
if ! "${PSQL_ADMIN[@]}" --tuples-only --no-align --command "SELECT 1 FROM pg_roles WHERE rolname='${TARGET_ROLE}'" | grep -q '^1$'; then
    createuser --host "$PG_HOST" --port "$PG_PORT" --username "$PG_ADMIN_USER" --login "$TARGET_ROLE"
fi
"${PSQL_ADMIN[@]}" --command "ALTER ROLE ${TARGET_ROLE} WITH PASSWORD '${TARGET_ROLE}'"

if ! "${PSQL_ADMIN[@]}" --tuples-only --no-align --command "SELECT 1 FROM pg_database WHERE datname='${TARGET_DATABASE}'" | grep -q '^1$'; then
    createdb --host "$PG_HOST" --port "$PG_PORT" --username "$PG_ADMIN_USER" --owner "$TARGET_ROLE" "$TARGET_DATABASE"
fi
echo "Prepared PostgreSQL database: $TARGET_DATABASE"

cd "$BACKEND_DIR"
if [ "$INSTALL_DEV" = true ]; then
    uv sync --extra dev
else
    uv sync
fi

echo "G002 setup complete. No schema migration or product bootstrap was run."
echo "Start the health-only target with: bash restart.sh"
