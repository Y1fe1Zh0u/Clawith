from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = BACKEND_ROOT / "rewrite" / "goal-gates.json"
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "validate_goal_gates.py"
SPEC = importlib.util.spec_from_file_location("validate_goal_gates", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
goal_gates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(goal_gates)

EXPECTED_GOALS = [f"G{number:03d}" for number in range(10)]


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _write_manifest(tmp_path: Path, manifest: dict) -> Path:
    path = tmp_path / "goal-gates.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_canonical_manifest_passes_validation() -> None:
    goal_gates.validate_manifest(MANIFEST_PATH)


def test_validator_rejects_goal_roster_or_order_drift(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][3], manifest["goals"][4] = manifest["goals"][4], manifest["goals"][3]

    with pytest.raises(goal_gates.GateContractError, match="exactly G000 through G009 in order"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_rejects_missing_cumulative_carry_forward(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][6]["carries_forward"].remove("G003")

    with pytest.raises(goal_gates.GateContractError, match="cumulative carry-forward mismatch for G006"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_rejects_mutation_in_validation_commands(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][3]["validations"].append(
        {
            "id": "approve-run-contract",
            "command": "uv run python scripts/check_owner_contracts.py approve --owner run",
            "artifacts": ["backend/rewrite/owner-contracts.json"],
        }
    )

    with pytest.raises(goal_gates.GateContractError, match="mutating command in validations for G003"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_rejects_mutation_without_receipt_guard(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][3]["mutations"][0]["receipt"] = None

    with pytest.raises(goal_gates.GateContractError, match="mutation receipt is required for G003"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_rejects_e2e_regression(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][7]["e2e_level"] = "core_runtime"

    with pytest.raises(goal_gates.GateContractError, match="E2E level regresses at G007"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_rejects_missing_required_fixture_path(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][5]["required_paths"].remove("backend/tests/performance/profiles/backend_50.json")

    with pytest.raises(goal_gates.GateContractError, match="required paths mismatch for G005"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_rejects_ignored_omx_as_canonical_evidence(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][0]["required_paths"][0] = ".omx/plans/prd-clean-break-backend-rewrite.md"

    with pytest.raises(goal_gates.GateContractError, match="ignored .omx path cannot be canonical evidence"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_rejects_required_artifact_path_drift(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][8]["validations"][0]["artifacts"] = ["backend/artifacts/rewrite/G008/unspecified.txt"]

    with pytest.raises(goal_gates.GateContractError, match="validation artifact paths mismatch for G008"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_rejects_goal_phase_crosswalk_drift(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][8]["phase_crosswalk"] = [7]

    with pytest.raises(goal_gates.GateContractError, match="phase crosswalk mismatch for G008"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_requires_contract_only_approvals_before_g003_and_g004(tmp_path: Path) -> None:
    manifest = _manifest()
    broken_g003 = copy.deepcopy(manifest)
    broken_g003["goals"][3]["contract_approval_owners"].remove("context")
    with pytest.raises(goal_gates.GateContractError, match="contract approvals mismatch for G003"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, broken_g003))

    manifest["goals"][4]["contract_approval_owners"].remove("heartbeat")
    with pytest.raises(goal_gates.GateContractError, match="contract approvals mismatch for G004"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_keeps_early_contract_approvals_out_of_implementation_rosters(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][3]["implementation_owners"].append("run")

    with pytest.raises(goal_gates.GateContractError, match="implementation owners mismatch for G003"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_keeps_g001_validation_only(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][1]["mutations"].append(copy.deepcopy(manifest["goals"][3]["mutations"][0]))

    with pytest.raises(goal_gates.GateContractError, match="mutations mismatch for G001"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))


def test_validator_requires_the_g005_hostile_scheduler_fixture(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["goals"][5]["hostile_fairness_test"]["initial_tenant_a_runs"] = 49

    with pytest.raises(goal_gates.GateContractError, match="hostile fairness contract mismatch for G005"):
        goal_gates.validate_manifest(_write_manifest(tmp_path, manifest))
