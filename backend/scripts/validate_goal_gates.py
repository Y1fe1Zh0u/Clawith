"""Validate the cumulative clean-rewrite Goal checkpoint contract.

Run from ``backend/``::

    uv run python scripts/validate_goal_gates.py \
        --manifest rewrite/goal-gates.json

The manifest declares gates and future evidence paths. It does not execute a gate,
record runtime state, or replay mutating commands.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_GOALS = tuple(f"G{number:03d}" for number in range(10))
EXPECTED_PHASES = {
    "G000": [0],
    "G001": [0],
    "G002": [1],
    "G003": [2],
    "G004": [3],
    "G005": [4],
    "G006": [5],
    "G007": [6],
    "G008": [7, 8],
    "G009": [8],
}
EXPECTED_E2E_LEVELS = {
    "G000": "unavailable",
    "G001": "unavailable",
    "G002": "unavailable",
    "G003": "unavailable",
    "G004": "unavailable",
    "G005": "core_runtime",
    "G006": "product_input",
    "G007": "module_cumulative",
    "G008": "complete_backend",
    "G009": "complete_backend",
}
EXPECTED_APPROVALS = {
    "G003": ["run", "context"],
    "G004": ["session", "a2a", "group", "trigger", "heartbeat", "channel"],
}
EXPECTED_IMPLEMENTATION_OWNERS = {
    "G000": [],
    "G001": [],
    "G002": [],
    "G003": ["identity_tenant", "credential", "model", "agent", "permission", "audit"],
    "G004": ["workspace", "tool", "capability_market", "model"],
    "G005": ["run", "context"],
    "G006": ["session", "a2a", "group", "trigger", "heartbeat", "channel"],
    "G007": ["S3-approved-owner"],
    "G008": [],
    "G009": [],
}
EXPECTED_MUTATIONS = {
    "G000": [],
    "G001": [],
    "G002": [],
    "G003": ["approve-run-contract-only", "approve-context-contract-only"],
    "G004": ["approve-product-input-contracts-only"],
    "G005": [],
    "G006": [],
    "G007": ["approve-s3-owner-contract", "transition-coverage-row"],
    "G008": ["release-legacy-reference"],
    "G009": [],
}
EXPECTED_VALIDATION_ARTIFACTS = {
    "G000": ["backend/rewrite/goal-gates.json"],
    "G001": [
        "backend/artifacts/rewrite/G001/phase-0-ledgers.txt",
        "backend/artifacts/rewrite/G001/legacy-reference.json",
    ],
    "G002": [
        "backend/artifacts/rewrite/G002/architecture-static.txt",
        "backend/artifacts/rewrite/G002/pytest-collection.txt",
    ],
    "G003": [
        "backend/artifacts/rewrite/G003/owner-contract-check.txt",
        "backend/artifacts/rewrite/G003/foundation-tests.txt",
    ],
    "G004": [
        "backend/artifacts/rewrite/G004/owner-contract-check.txt",
        "backend/artifacts/rewrite/G004/execution-dependency-tests.txt",
    ],
    "G005": [
        "backend/artifacts/rewrite/G005/core-runtime-e2e.txt",
        "backend/artifacts/performance/core.json",
    ],
    "G006": [
        "backend/artifacts/rewrite/G006/product-input-e2e.txt",
        "backend/artifacts/performance/mixed.json",
    ],
    "G007": [
        "backend/artifacts/rewrite/G007/cumulative-module-e2e.txt",
        "backend/artifacts/rewrite/G007/coverage-progress.json",
    ],
    "G008": [
        "backend/artifacts/rewrite/G008/fresh-e2e-before-reference-removal.txt",
        "backend/artifacts/rewrite/G008/terminal-coverage.json",
        "backend/artifacts/rewrite/G008/fresh-e2e-after-reference-removal.txt",
    ],
    "G009": [
        "backend/artifacts/rewrite/G009/complete-backend.txt",
        "backend/artifacts/rewrite/G009/deployment-recovery.txt",
        "backend/artifacts/performance/final.json",
    ],
}
EXPECTED_REQUIRED_PATHS = {
    "G000": [
        ".omx/plans/prd-clean-break-backend-rewrite.md",
        ".omx/plans/test-spec-clean-break-backend-rewrite.md",
        ".omx/plans/phase-verification-clean-break-backend.md",
        "backend/rewrite/goal-gates.json",
    ],
    "G001": [
        "backend/rewrite/coverage.json",
        "backend/rewrite/owner-contracts.json",
        "backend/rewrite/product-contracts.json",
        "backend/rewrite/owner-dag.json",
        "backend/rewrite/legacy-black-box.json",
        "backend/tests/performance/profiles/backend_50.json",
    ],
    "G002": [
        "backend/app/application.py",
        "backend/app/infrastructure/database.py",
        "backend/tests/architecture/test_application_composition.py",
        "backend/tests/architecture/test_import_boundaries.py",
        "backend/tests/architecture/test_module_boundaries.py",
    ],
    "G003": [
        "backend/rewrite/owner-contracts.json",
        "backend/tests/database/test_schema_wave_S0.py",
        "backend/tests/database/test_schema_wave_S1.py",
        "backend/tests/compose.postgres.yml",
    ],
    "G004": [
        "backend/rewrite/owner-contracts.json",
        "backend/tests/database/test_schema_wave_S2.py",
        "backend/tests/modules/workspace",
        "backend/tests/modules/tool",
        "backend/tests/modules/capability_market",
    ],
    "G005": [
        "backend/tests/e2e/test_runtime_product_owner_fixture.py",
        "backend/tests/performance/profiles/backend_50.json",
        "backend/tests/performance/test_execution_scheduler_fairness.py",
    ],
    "G006": [
        "backend/tests/e2e/test_direct_session.py",
        "backend/tests/e2e/test_product_inputs.py",
        "backend/tests/performance/profiles/backend_50.json",
    ],
    "G007": [
        "backend/rewrite/coverage.json",
        "backend/rewrite/owner-contracts.json",
        "backend/rewrite/product-contracts.json",
        "backend/tests/e2e",
    ],
    "G008": [
        "backend/tests/e2e",
        "backend/tests/database/test_fresh_baseline.py",
        "backend/rewrite/coverage.json",
        "backend/rewrite/legacy-black-box.json",
    ],
    "G009": [
        "backend/tests/e2e",
        "backend/tests/deployment/test_single_runner_topology.py",
        "backend/tests/deployment/test_readiness.py",
        "backend/tests/recovery/test_target_snapshot_restore.py",
        "backend/tests/recovery/test_fix_forward.py",
        "backend/tests/performance/profiles/backend_50.json",
    ],
}
EXPECTED_HOSTILE_FAIRNESS = {
    "scheduler": "in_memory_tenant_then_agent_execution_scheduler",
    "boundary": "after_each_bounded_model_step_or_tool_batch",
    "initial_tenant_a_runs": 50,
    "tenant_a_runs": "continuously_runnable_nonterminating",
    "tenant_b_expectation": "next_model_step_within_scheduler_bound",
    "max_consecutive_eligible_tenant_skips": 1,
    "fifo_scope": "per_agent",
    "terminal_cleanup": ["cancellation_removes_run", "failure_removes_run", "execution_slot_released"],
    "excluded_authorities": [
        "initial_admission_queue",
        "persisted_queue",
        "checkpoint",
        "durable_scheduler_state",
        "whole_run_limit",
    ],
}
MUTATING_TOKENS = (" build ", " approve ", " transition ", " release-reference ")
REPLAY_POLICY = "verify_receipt_before_execute"


class GateContractError(ValueError):
    """A deterministic Goal-gate contract validation failure."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GateContractError(f"manifest does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GateContractError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateContractError("goal-gate manifest must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GateContractError(f"{label} must be a list")
    return value


def _is_mutating(command: str) -> bool:
    normalized = f" {command.strip()} "
    return any(token in normalized for token in MUTATING_TOKENS)


def _validate_policy(manifest: dict[str, Any]) -> list[str]:
    policy = manifest.get("policy")
    if not isinstance(policy, dict):
        raise GateContractError("policy must be an object")
    expected = {
        "cumulative": True,
        "validation_commands_are_repeatable": True,
        "mutations_require_receipts": True,
        "mutation_replay_policy": REPLAY_POLICY,
        "e2e_levels": [
            "unavailable",
            "core_runtime",
            "product_input",
            "module_cumulative",
            "complete_backend",
        ],
    }
    if policy != expected:
        raise GateContractError("goal-gate policy differs from the canonical cumulative contract")
    return expected["e2e_levels"]


def _validate_goal(goal: dict[str, Any], index: int, levels: list[str]) -> None:
    goal_id = EXPECTED_GOALS[index]
    if goal.get("phase_crosswalk") != EXPECTED_PHASES[goal_id]:
        raise GateContractError(f"phase crosswalk mismatch for {goal_id}")
    if goal.get("carries_forward") != list(EXPECTED_GOALS[:index]):
        raise GateContractError(f"cumulative carry-forward mismatch for {goal_id}")
    if goal.get("e2e_level") != EXPECTED_E2E_LEVELS[goal_id]:
        current_level = goal.get("e2e_level")
        expected_level = EXPECTED_E2E_LEVELS[goal_id]
        if current_level in levels and levels.index(current_level) < levels.index(expected_level):
            raise GateContractError(f"E2E level regresses at {goal_id}")
        raise GateContractError(f"E2E level mismatch for {goal_id}")
    if goal.get("required_paths") != EXPECTED_REQUIRED_PATHS[goal_id]:
        raise GateContractError(f"required paths mismatch for {goal_id}")
    expected_approvals = EXPECTED_APPROVALS.get(goal_id, [])
    if goal.get("contract_approval_owners") != expected_approvals:
        raise GateContractError(f"contract approvals mismatch for {goal_id}")
    if goal.get("implementation_owners") != EXPECTED_IMPLEMENTATION_OWNERS[goal_id]:
        raise GateContractError(f"implementation owners mismatch for {goal_id}")
    if goal_id == "G005" and goal.get("hostile_fairness_test") != EXPECTED_HOSTILE_FAIRNESS:
        raise GateContractError("hostile fairness contract mismatch for G005")

    validations = _list(goal.get("validations"), f"validations for {goal_id}")
    if not validations:
        raise GateContractError(f"at least one validation is required for {goal_id}")
    validation_ids: set[str] = set()
    for validation in validations:
        if not isinstance(validation, dict):
            raise GateContractError(f"validation entry must be an object for {goal_id}")
        validation_id = validation.get("id")
        command = validation.get("command")
        artifacts = validation.get("artifacts")
        if not isinstance(validation_id, str) or not validation_id or validation_id in validation_ids:
            raise GateContractError(f"validation ids must be unique non-empty strings for {goal_id}")
        validation_ids.add(validation_id)
        if not isinstance(command, str) or not command:
            raise GateContractError(f"validation command is required for {goal_id}")
        if _is_mutating(command):
            raise GateContractError(f"mutating command in validations for {goal_id}: {validation_id}")
        if not isinstance(artifacts, list) or not artifacts or not all(isinstance(path, str) and path for path in artifacts):
            raise GateContractError(f"validation artifacts are required for {goal_id}: {validation_id}")
    artifact_paths = [path for validation in validations for path in validation["artifacts"]]
    if artifact_paths != EXPECTED_VALIDATION_ARTIFACTS[goal_id]:
        raise GateContractError(f"validation artifact paths mismatch for {goal_id}")

    mutations = _list(goal.get("mutations"), f"mutations for {goal_id}")
    mutation_id_roster = [mutation.get("id") if isinstance(mutation, dict) else None for mutation in mutations]
    if mutation_id_roster != EXPECTED_MUTATIONS[goal_id]:
        raise GateContractError(f"mutations mismatch for {goal_id}")
    mutation_ids: set[str] = set()
    for mutation in mutations:
        if not isinstance(mutation, dict):
            raise GateContractError(f"mutation entry must be an object for {goal_id}")
        mutation_id = mutation.get("id")
        command = mutation.get("command")
        if not isinstance(mutation_id, str) or not mutation_id or mutation_id in mutation_ids:
            raise GateContractError(f"mutation ids must be unique non-empty strings for {goal_id}")
        mutation_ids.add(mutation_id)
        if not isinstance(command, str) or not _is_mutating(command):
            raise GateContractError(f"mutation command is required for {goal_id}: {mutation_id}")
        if not isinstance(mutation.get("receipt"), str) or not mutation["receipt"]:
            raise GateContractError(f"mutation receipt is required for {goal_id}: {mutation_id}")
        if mutation.get("replay_policy") != REPLAY_POLICY:
            raise GateContractError(f"mutation receipt guard mismatch for {goal_id}: {mutation_id}")


def validate_manifest(path: Path) -> None:
    manifest = _load_json(path)
    if manifest.get("version") != 1:
        raise GateContractError("goal-gate manifest version must be 1")
    levels = _validate_policy(manifest)
    goals = _list(manifest.get("goals"), "goals")
    goal_ids = [goal.get("id") if isinstance(goal, dict) else None for goal in goals]
    if goal_ids != list(EXPECTED_GOALS):
        raise GateContractError("goals must be exactly G000 through G009 in order")
    for index, goal in enumerate(goals):
        assert isinstance(goal, dict)
        _validate_goal(goal, index, levels)
    level_indexes = [levels.index(EXPECTED_E2E_LEVELS[goal_id]) for goal_id in EXPECTED_GOALS]
    if level_indexes != sorted(level_indexes):
        raise GateContractError("E2E levels must be monotonic")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("rewrite/goal-gates.json"))
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        validate_manifest(args.manifest)
    except GateContractError as exc:
        print(f"goal-gate validation failed: {exc}")
        return 1
    print("goal-gate validation passed: G000-G009 cumulative contract is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
