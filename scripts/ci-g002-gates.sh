#!/bin/bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backend_root="$repository_root/backend"
ci_temp_root="$(mktemp -d)"
reference_worktree="$ci_temp_root/legacy-reference"

cleanup() {
    status=$?
    trap - EXIT INT TERM
    git -C "$repository_root" worktree remove --force "$reference_worktree" >/dev/null 2>&1 || true
    git -C "$repository_root" worktree prune
    rm -rf "$ci_temp_root"
    exit "$status"
}
trap cleanup EXIT INT TERM

git -C "$repository_root" cat-file -e '8ed4ae2f^{commit}'
git -C "$repository_root" worktree add --detach "$reference_worktree" 8ed4ae2f
uv sync --project "$reference_worktree/backend" --extra dev
reference_python="$reference_worktree/backend/.venv/bin/python"

export CLAWITH_LEGACY_REFERENCE_AGENT_DATA_DIR="$ci_temp_root/persistence/legacy/agents"
export CLAWITH_LEGACY_REFERENCE_DATABASE_URL="postgresql+asyncpg://legacy:legacy@127.0.0.1:5432/clawith_legacy_reference"
export CLAWITH_LEGACY_REFERENCE_REDIS_URL="redis://127.0.0.1:6379/14"
export CLAWITH_LEGACY_REFERENCE_S3_PREFIX="clawith-legacy-reference/"
export CLAWITH_LEGACY_REFERENCE_STORAGE_LOCAL_ROOT="$ci_temp_root/persistence/legacy/storage"
export CLAWITH_TARGET_AGENT_DATA_DIR="$ci_temp_root/persistence/target/agents"
export CLAWITH_TARGET_DATABASE_URL="postgresql+asyncpg://target:target@127.0.0.1:5432/clawith_target"
export CLAWITH_TARGET_REDIS_URL="redis://127.0.0.1:6379/15"
export CLAWITH_TARGET_S3_PREFIX="clawith-target/"
export CLAWITH_TARGET_STORAGE_LOCAL_ROOT="$ci_temp_root/persistence/target/storage"

cd "$backend_root"
uv sync --extra dev
uv run python scripts/validate_goal_gates.py --manifest rewrite/goal-gates.json
uv run python scripts/rewrite_inventory.py check --manifest rewrite/coverage.json --require-zero-unreviewed --require-zero-disposition-missing
uv run --extra dev pytest tests/architecture/test_governance.py tests/architecture/test_module_boundaries.py
uv run python scripts/check_owner_contracts.py check --manifest rewrite/owner-contracts.json
uv run python scripts/validate_goal_gates.py --manifest rewrite/goal-gates.json --check-product-roster-and-linkage
uv run python scripts/validate_load_profile.py tests/performance/profiles/backend_50.json
uv run python scripts/rewrite_inventory.py check-reference --manifest rewrite/coverage.json --expected-head 8ed4ae2f --require-clean --boot-smoke --black-box-manifest rewrite/legacy-black-box.json --worktree "$reference_worktree" --python "$reference_python"
uv run --extra dev pytest tests/architecture
uv run --extra dev pytest
uv run --extra dev pytest --collect-only
uv run --extra dev ruff check app tests
uv run --extra dev pyright app
