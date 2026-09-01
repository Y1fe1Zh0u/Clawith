from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DAG = BACKEND_ROOT / "rewrite" / "owner-dag.json"
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "check_owner_contracts.py"
SPEC = importlib.util.spec_from_file_location("check_owner_contracts", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
contracts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contracts)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _built_manifest(tmp_path: Path) -> Path:
    manifest_path = tmp_path / "owner-contracts.json"
    contracts.build_manifest(manifest_path, CANONICAL_DAG)
    return manifest_path


def test_build_creates_the_exact_approved_owner_roster(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)
    manifest = _read(manifest_path)

    assert [row["owner_id"] for row in manifest["owners"]] == [
        row["owner_id"] for row in _read(CANONICAL_DAG)["owners"]
    ]
    assert len(manifest["owners"]) == 34
    assert {row["schema_wave"] for row in manifest["owners"]} == {"S0", "S1", "S2", "S3"}
    assert all(row["state"] == "unreviewed" for row in manifest["owners"])
    contracts.check_manifest(manifest_path, [], [])


def test_approve_records_current_hashes_and_rejects_duplicate_approval(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)
    artifact = tmp_path / "identity-contract.md"
    evidence = tmp_path / "identity-review.txt"
    artifact.write_text("approved identity contract\n", encoding="utf-8")
    evidence.write_text("review passed\n", encoding="utf-8")

    contracts.approve_owner(manifest_path, "identity_tenant", str(artifact), [str(evidence)])
    contracts.check_manifest(manifest_path, ["identity_tenant"], ["S0"])

    row = _read(manifest_path)["owners"][0]
    assert row["contract_hash"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert row["evidence"] == [{"path": str(evidence), "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()}]
    with pytest.raises(contracts.ContractError, match="already approved"):
        contracts.approve_owner(manifest_path, "identity_tenant", str(artifact), [str(evidence)])


def test_check_rejects_tampered_approval_artifacts(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)
    artifact = tmp_path / "identity-contract.md"
    evidence = tmp_path / "identity-review.txt"
    artifact.write_text("approved\n", encoding="utf-8")
    evidence.write_text("review passed\n", encoding="utf-8")
    contracts.approve_owner(manifest_path, "identity_tenant", str(artifact), [str(evidence)])

    artifact.write_text("changed after approval\n", encoding="utf-8")

    with pytest.raises(contracts.ContractError, match="artifact hash mismatch"):
        contracts.check_manifest(manifest_path, [], [])


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda rows: rows.pop(), "missing owners"),
        (lambda rows: rows.append(copy.deepcopy(rows[0])), "duplicate owner"),
        (
            lambda rows: rows.append(
                {
                    **copy.deepcopy(rows[0]),
                    "owner_id": "runtime",
                }
            ),
            "extra owner",
        ),
        (lambda rows: rows[0].update(schema_wave="S1"), "wave mismatch"),
        (lambda rows: rows[0].update(implementation_phase=4), "phase mismatch"),
    ],
)
def test_check_rejects_roster_and_wave_drift(tmp_path: Path, mutation, message: str) -> None:
    manifest_path = _built_manifest(tmp_path)
    manifest = _read(manifest_path)
    mutation(manifest["owners"])
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(contracts.ContractError, match=message):
        contracts.check_manifest(manifest_path, [], [])


def test_check_rejects_unapproved_required_owner_and_wave(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)

    with pytest.raises(contracts.ContractError, match="required owner is not approved"):
        contracts.check_manifest(manifest_path, ["run"], [])
    with pytest.raises(contracts.ContractError, match="S1 has unapproved owners"):
        contracts.check_manifest(manifest_path, [], ["S1"])


def test_build_rejects_duplicate_or_cyclic_dag(tmp_path: Path) -> None:
    dag = _read(CANONICAL_DAG)
    dag["owners"].append(copy.deepcopy(dag["owners"][0]))
    duplicate_dag = tmp_path / "duplicate-dag.json"
    duplicate_dag.write_text(json.dumps(dag), encoding="utf-8")
    with pytest.raises(contracts.ContractError, match="duplicate owner"):
        contracts.build_manifest(tmp_path / "manifest.json", duplicate_dag)

    dag = _read(CANONICAL_DAG)
    dag["owners"][0]["depends_on"] = ["auth"]
    cyclic_dag = tmp_path / "cyclic-dag.json"
    cyclic_dag.write_text(json.dumps(dag), encoding="utf-8")
    with pytest.raises(contracts.ContractError, match="dependency cycle"):
        contracts.build_manifest(tmp_path / "manifest.json", cyclic_dag)


def test_build_does_not_replace_an_invalid_existing_ledger(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)
    manifest = _read(manifest_path)
    manifest["owners"].pop()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(contracts.ContractError, match="missing owners"):
        contracts.build_manifest(manifest_path, CANONICAL_DAG)
    assert _read(manifest_path) == manifest
