from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DAG = BACKEND_ROOT / "rewrite" / "owner-dag.json"
CANONICAL_PRODUCT_MANIFEST = BACKEND_ROOT / "rewrite" / "product-contracts.json"
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "check_owner_contracts.py"
SPEC = importlib.util.spec_from_file_location("check_owner_contracts", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
contracts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contracts)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _built_manifest(tmp_path: Path) -> Path:
    manifest_path = tmp_path / "owner-contracts.json"
    dag_path = tmp_path / "owner-dag.json"
    dag_path.write_text(CANONICAL_DAG.read_text(encoding="utf-8"), encoding="utf-8")
    contracts.build_manifest(manifest_path, dag_path)
    return manifest_path


def _approved_auth_product(tmp_path: Path) -> tuple[Path, Path]:
    product_manifest = _read(CANONICAL_PRODUCT_MANIFEST)
    artifact = tmp_path / ".omx" / "specs" / "backend-products" / "auth.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Approved Auth contract\n", encoding="utf-8")
    evidence = tmp_path / "auth-product-review.txt"
    evidence.write_text("product contract approved\n", encoding="utf-8")
    product_manifest["modules"][0].update(
        {
            "state": "contract_approved",
            "contract_artifact": str(artifact),
            "contract_hash": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "evidence": [{"path": str(evidence), "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()}],
            "actors": ["tenant member"],
            "product_workflow": ["sign in"],
            "persistence": ["account and membership"],
            "api_events": ["POST /auth/login"],
            "authorization": ["public login then tenant principal"],
            "failure_behavior": ["invalid credentials fail closed"],
            "consumers": ["web application"],
            "endpoint_mapping": ["http.auth.login"],
            "acceptance_tests": ["tests/modules/auth/test_login.py"],
            "explicit_deletions": ["none"],
        }
    )
    product_manifest_path = tmp_path / "product-contracts.json"
    product_manifest_path.write_text(json.dumps(product_manifest), encoding="utf-8")
    return artifact, evidence


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


def test_sso_dependency_and_ledger_order_are_canonical(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)
    dag_rows = _read(tmp_path / "owner-dag.json")["owners"]
    owner_rows = _read(manifest_path)["owners"]
    sso = next(row for row in dag_rows if row["owner_id"] == "sso")

    assert "credential" in sso["depends_on"]
    assert [row["owner_id"] for row in owner_rows] == [row["owner_id"] for row in dag_rows]
    assert next(index for index, row in enumerate(dag_rows) if row["owner_id"] == "credential") < next(
        index for index, row in enumerate(dag_rows) if row["owner_id"] == "sso"
    )


def test_dag_rejects_missing_or_late_sso_credential_dependency(tmp_path: Path) -> None:
    dag = _read(CANONICAL_DAG)
    sso = next(row for row in dag["owners"] if row["owner_id"] == "sso")
    sso["depends_on"].remove("credential")
    missing_dag = tmp_path / "missing-credential.json"
    missing_dag.write_text(json.dumps(dag), encoding="utf-8")
    with pytest.raises(contracts.ContractError, match="missing required dependencies for sso: credential"):
        contracts.build_manifest(tmp_path / "manifest.json", missing_dag)

    dag = _read(CANONICAL_DAG)
    rows = dag["owners"]
    credential_index = next(index for index, row in enumerate(rows) if row["owner_id"] == "credential")
    sso_index = next(index for index, row in enumerate(rows) if row["owner_id"] == "sso")
    sso_row = rows.pop(sso_index)
    rows.insert(credential_index, sso_row)
    late_dag = tmp_path / "late-credential.json"
    late_dag.write_text(json.dumps(dag), encoding="utf-8")
    with pytest.raises(contracts.ContractError, match=r"dependencies must appear before sso: .*credential"):
        contracts.build_manifest(tmp_path / "manifest.json", late_dag)


def test_sso_approval_requires_credential_approval(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)
    artifact = tmp_path / "sso-contract.md"
    evidence = tmp_path / "sso-review.txt"
    artifact.write_text("approved SSO contract\n", encoding="utf-8")
    evidence.write_text("SSO review passed\n", encoding="utf-8")

    with pytest.raises(contracts.ContractError, match="not approved for sso: credential"):
        contracts.approve_owner(manifest_path, "sso", str(artifact), [str(evidence)])


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


def test_s3_owner_approval_requires_the_matching_approved_product_contract(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)
    product_manifest_path = tmp_path / "product-contracts.json"
    product_manifest_path.write_text(CANONICAL_PRODUCT_MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")
    arbitrary_artifact = tmp_path / "arbitrary.md"
    arbitrary_evidence = tmp_path / "arbitrary-review.txt"
    arbitrary_artifact.write_text("not the product contract\n", encoding="utf-8")
    arbitrary_evidence.write_text("not the product approval\n", encoding="utf-8")

    with pytest.raises(contracts.ContractError, match="product contract is not approved"):
        contracts.approve_owner(
            manifest_path,
            "auth",
            str(arbitrary_artifact),
            [str(arbitrary_evidence)],
        )
    auth_row = next(row for row in _read(manifest_path)["owners"] if row["owner_id"] == "auth")
    assert auth_row["state"] == "unreviewed"


def test_s3_owner_approval_rejects_product_artifact_or_evidence_mismatch(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)
    product_artifact, product_evidence = _approved_auth_product(tmp_path)
    arbitrary_artifact = tmp_path / "arbitrary.md"
    arbitrary_evidence = tmp_path / "arbitrary-review.txt"
    arbitrary_artifact.write_text("not the product contract\n", encoding="utf-8")
    arbitrary_evidence.write_text("not the product approval\n", encoding="utf-8")

    with pytest.raises(contracts.ContractError, match="artifact does not match product contract"):
        contracts.approve_owner(manifest_path, "auth", str(arbitrary_artifact), [str(product_evidence)])
    with pytest.raises(contracts.ContractError, match="evidence does not match product contract"):
        contracts.approve_owner(manifest_path, "auth", str(product_artifact), [str(arbitrary_evidence)])


def test_s3_owner_check_remains_linked_to_product_contract_state(tmp_path: Path) -> None:
    manifest_path = _built_manifest(tmp_path)
    product_artifact, product_evidence = _approved_auth_product(tmp_path)

    contracts.approve_owner(manifest_path, "auth", str(product_artifact), [str(product_evidence)])
    contracts.check_manifest(manifest_path, ["auth"], [])

    product_manifest_path = tmp_path / "product-contracts.json"
    product_manifest = _read(product_manifest_path)
    canonical_auth = _read(CANONICAL_PRODUCT_MANIFEST)["modules"][0]
    product_manifest["modules"][0] = canonical_auth
    product_manifest_path.write_text(json.dumps(product_manifest), encoding="utf-8")

    with pytest.raises(contracts.ContractError, match="product contract is not approved"):
        contracts.check_manifest(manifest_path, ["auth"], [])
