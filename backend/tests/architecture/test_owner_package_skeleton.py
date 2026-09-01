from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODULES_ROOT = BACKEND_ROOT / "app" / "modules"
OWNER_CONTRACTS = BACKEND_ROOT / "rewrite" / "owner-contracts.json"
EXPECTED_OWNER_COUNT = 34

OwnerContract = tuple[str, str, int]


class SkeletonError(AssertionError):
    pass


def _canonical_owner_contracts() -> list[OwnerContract]:
    manifest = json.loads(OWNER_CONTRACTS.read_text(encoding="utf-8"))
    return [
        (row["owner_id"], row["schema_wave"], row["implementation_phase"])
        for row in manifest["owners"]
    ]


def _owner_contract_map(owner_contracts: Iterable[OwnerContract]) -> dict[str, tuple[str, int]]:
    rows = list(owner_contracts)
    owner_ids = [owner_id for owner_id, _, _ in rows]
    duplicate_owner_ids = sorted(
        owner_id for owner_id in set(owner_ids) if owner_ids.count(owner_id) > 1
    )
    if duplicate_owner_ids:
        raise SkeletonError(f"duplicate owners: {duplicate_owner_ids}")
    if len(rows) != EXPECTED_OWNER_COUNT:
        raise SkeletonError(f"expected {EXPECTED_OWNER_COUNT} owners, found {len(rows)}")
    return {
        owner_id: (schema_wave, implementation_phase)
        for owner_id, schema_wave, implementation_phase in rows
    }


def _validate_owner_package_skeleton(
    modules_root: Path,
    owner_contracts: Iterable[OwnerContract],
) -> dict[str, tuple[str, int]]:
    expected_contracts = _owner_contract_map(owner_contracts)
    expected_owner_ids = set(expected_contracts)
    actual_owner_ids = {path.name for path in modules_root.iterdir() if path.is_dir()}

    missing_owner_ids = sorted(expected_owner_ids - actual_owner_ids)
    if missing_owner_ids:
        raise SkeletonError(f"missing owner packages: {missing_owner_ids}")
    extra_owner_ids = sorted(actual_owner_ids - expected_owner_ids)
    if extra_owner_ids:
        raise SkeletonError(f"extra owner packages: {extra_owner_ids}")

    root_files = sorted(path.name for path in modules_root.iterdir() if path.is_file())
    if root_files != ["__init__.py"]:
        raise SkeletonError(f"unexpected modules root files: {root_files}")
    if (modules_root / "__init__.py").read_bytes():
        raise SkeletonError("modules package marker must be empty")

    for owner_id, (schema_wave, implementation_phase) in expected_contracts.items():
        package_root = modules_root / owner_id
        entries = sorted(path.name for path in package_root.iterdir())
        if entries != ["__init__.py"]:
            raise SkeletonError(
                f"{owner_id} ({schema_wave}/phase-{implementation_phase}) has unexpected implementation: {entries}"
            )
        if (package_root / "__init__.py").read_bytes():
            raise SkeletonError(f"{owner_id} package marker must be empty")

    return expected_contracts


def _write_skeleton(root: Path, owner_ids: Iterable[str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "__init__.py").touch()
    for owner_id in owner_ids:
        owner_root = root / owner_id
        owner_root.mkdir()
        (owner_root / "__init__.py").touch()


def test_owner_package_skeleton_matches_the_canonical_contract_ledger() -> None:
    owner_contracts = _canonical_owner_contracts()

    actual_contracts = _validate_owner_package_skeleton(MODULES_ROOT, owner_contracts)

    assert len(owner_contracts) == EXPECTED_OWNER_COUNT
    assert len(actual_contracts) == EXPECTED_OWNER_COUNT
    assert actual_contracts == {
        owner_id: (schema_wave, implementation_phase)
        for owner_id, schema_wave, implementation_phase in owner_contracts
    }


def test_owner_package_skeleton_rejects_a_missing_owner(tmp_path: Path) -> None:
    owner_contracts = _canonical_owner_contracts()
    _write_skeleton(tmp_path, (owner_id for owner_id, _, _ in owner_contracts[1:]))

    with pytest.raises(SkeletonError, match="missing owner packages"):
        _validate_owner_package_skeleton(tmp_path, owner_contracts)


def test_owner_package_skeleton_rejects_an_extra_owner(tmp_path: Path) -> None:
    owner_contracts = _canonical_owner_contracts()
    _write_skeleton(tmp_path, (owner_id for owner_id, _, _ in owner_contracts))
    extra_owner = tmp_path / "unexpected_owner"
    extra_owner.mkdir()
    (extra_owner / "__init__.py").touch()

    with pytest.raises(SkeletonError, match="extra owner packages"):
        _validate_owner_package_skeleton(tmp_path, owner_contracts)


def test_owner_package_skeleton_rejects_duplicate_ledger_owners(tmp_path: Path) -> None:
    owner_contracts = _canonical_owner_contracts()
    _write_skeleton(tmp_path, (owner_id for owner_id, _, _ in owner_contracts))

    with pytest.raises(SkeletonError, match="duplicate owners"):
        _validate_owner_package_skeleton(tmp_path, [*owner_contracts, owner_contracts[0]])
