from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).parents[2] / "scripts/rewrite_inventory.py"
_SPEC = importlib.util.spec_from_file_location("rewrite_inventory", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
rewrite_inventory = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = rewrite_inventory
_SPEC.loader.exec_module(rewrite_inventory)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _fixture_source(tmp_path: Path) -> Path:
    _write(
        tmp_path / "app/config.py",
        'class Settings:\n    API_PREFIX: str = "/api"\n',
    )
    _write(
        tmp_path / "app/api/items.py",
        '''from fastapi import APIRouter

CALLBACK = "/callback"
router = APIRouter(prefix="/items")

@router.get("")
async def list_items(): ...

@router.get("/")
async def list_items_with_slash(): ...

@router.post("/{item_id}")
async def create_item(): ...

@router.get(CALLBACK)
async def callback(): ...

@router.websocket("/{item_id}/events")
async def events(): ...
''',
    )
    _write(
        tmp_path / "app/main.py",
        '''from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.items import router as items_router

settings = object()

@asynccontextmanager
async def lifespan(app):
    await seed_builtin_tools()
    task_specs = [("trigger", start_trigger_daemon()), ("feishu", feishu_ws_manager.start_all())]
    try:
        yield
    finally:
        await realtime_router.stop()
        await close_redis()

app = FastAPI(lifespan=lifespan)
app.include_router(items_router, prefix=settings.API_PREFIX)

@app.get("/health")
async def health(): ...
''',
    )
    return tmp_path


def _artifact(path: Path) -> dict[str, str]:
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _complete_row(row: dict[str, object], artifact: dict[str, str], *, disposition: str) -> None:
    row["disposition"] = disposition
    row["behavior_evidence"] = [artifact]
    row["consumer_evidence"] = [artifact]
    row["planned_gate"] = "tests/acceptance/test_owner.py"
    row["target_owner_id"] = None if disposition == "delete" else "agent"


def test_discover_finds_only_mounted_routes_and_lifespan_operations(tmp_path: Path) -> None:
    source = _fixture_source(tmp_path)

    entries = rewrite_inventory.discover(source)
    by_id = {entry.id: entry for entry in entries}

    assert "GET:/api/items" in by_id
    assert "GET:/api/items/" in by_id
    assert "POST:/api/items/{item_id}" in by_id
    assert "GET:/api/items/callback" in by_id
    assert by_id["WEBSOCKET:/api/items/{item_id}/events"].kind == "websocket"
    assert "GET:/health" in by_id
    assert "LIFECYCLE:application:lifespan" in by_id
    assert "LIFECYCLE:bootstrap:seed_builtin_tools" in by_id
    assert "LIFECYCLE:trigger:start_trigger_daemon" in by_id
    assert "LIFECYCLE:channel:feishu_ws_manager_start_all" in by_id
    assert "LIFECYCLE:realtime:realtime_router_stop" in by_id
    assert "LIFECYCLE:infrastructure:close_redis" in by_id


def test_discover_rejects_missing_mounted_source(tmp_path: Path) -> None:
    source = _fixture_source(tmp_path)
    (source / "app/api/items.py").unlink()

    with pytest.raises(rewrite_inventory.InventoryError, match="mounted module is missing"):
        rewrite_inventory.discover(source)


def test_discover_rejects_duplicate_stable_ids(tmp_path: Path) -> None:
    source = _fixture_source(tmp_path)
    items = source / "app/api/items.py"
    items.write_text(
        items.read_text(encoding="utf-8")
        + '\n@router.get("")\nasync def duplicate_list(): ...\n',
        encoding="utf-8",
    )

    with pytest.raises(rewrite_inventory.InventoryError, match="duplicate stable IDs"):
        rewrite_inventory.discover(source)


def test_build_is_deterministic_and_preserves_review_fields(tmp_path: Path) -> None:
    source = _fixture_source(tmp_path / "source")
    manifest_path = tmp_path / "rewrite/coverage.json"
    first = rewrite_inventory.build_manifest(manifest_path, source)
    first["entries"][0]["planned_gate"] = "kept"
    manifest_path.write_text(json.dumps(first), encoding="utf-8")

    second = rewrite_inventory.build_manifest(manifest_path, source)
    rendered = manifest_path.read_text(encoding="utf-8")
    third = rewrite_inventory.build_manifest(manifest_path, source)

    assert second == third
    assert rendered == manifest_path.read_text(encoding="utf-8")
    assert second["entries"][0]["planned_gate"] == "kept"


def test_build_refuses_to_prune_a_reviewed_frozen_inventory(tmp_path: Path) -> None:
    source = _fixture_source(tmp_path / "source")
    manifest_path = tmp_path / "rewrite/coverage.json"
    manifest = rewrite_inventory.build_manifest(manifest_path, source)
    removed = next(row for row in manifest["entries"] if row["id"] == "GET:/api/items")
    removed["state"] = "disposition_approved"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    items = source / "app/api/items.py"
    items.write_text(
        items.read_text(encoding="utf-8").replace(
            '@router.get("")\nasync def list_items(): ...\n\n', ""
        ),
        encoding="utf-8",
    )

    with pytest.raises(rewrite_inventory.InventoryError, match="disappeared from discovery"):
        rewrite_inventory.build_manifest(manifest_path, source)


def test_check_reports_and_enforces_manifest_counts(tmp_path: Path) -> None:
    source = _fixture_source(tmp_path / "source")
    manifest_path = tmp_path / "rewrite/coverage.json"
    manifest = rewrite_inventory.build_manifest(manifest_path, source)

    assert rewrite_inventory.check_manifest(
        manifest_path,
        require_zero_unreviewed=False,
        require_zero_disposition_missing=False,
        require_all_terminal=False,
    ) == (len(manifest["entries"]), len(manifest["entries"]), len(manifest["entries"]))
    with pytest.raises(rewrite_inventory.InventoryError, match="unreviewed="):
        rewrite_inventory.check_manifest(
            manifest_path,
            require_zero_unreviewed=True,
            require_zero_disposition_missing=False,
            require_all_terminal=False,
        )


def test_evidence_hash_change_invalidates_manifest(tmp_path: Path) -> None:
    source = _fixture_source(tmp_path / "source")
    manifest_path = tmp_path / "rewrite/coverage.json"
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("approved", encoding="utf-8")
    manifest = rewrite_inventory.build_manifest(manifest_path, source)
    _complete_row(manifest["entries"][0], _artifact(evidence), disposition="delete")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    evidence.write_text("changed", encoding="utf-8")

    with pytest.raises(rewrite_inventory.InventoryError, match="evidence hash changed"):
        rewrite_inventory.check_manifest(
            manifest_path,
            require_zero_unreviewed=False,
            require_zero_disposition_missing=False,
            require_all_terminal=False,
        )


def test_transition_enforces_predecessor_disposition_and_evidence(tmp_path: Path) -> None:
    source = _fixture_source(tmp_path / "source")
    manifest_path = tmp_path / "rewrite/coverage.json"
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("approved", encoding="utf-8")
    manifest = rewrite_inventory.build_manifest(manifest_path, source)
    row = manifest["entries"][0]
    _complete_row(row, _artifact(evidence), disposition="delete")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rewrite_inventory.transition(manifest_path, row["id"], "disposition_approved", evidence)
    rewrite_inventory.transition(manifest_path, row["id"], "deletion_approved", evidence)
    transitioned = json.loads(manifest_path.read_text(encoding="utf-8"))["entries"][0]

    assert transitioned["state"] == "deletion_approved"
    assert transitioned["removal_evidence"] == [
        {"path": "evidence.txt", "sha256": _artifact(evidence)["sha256"]}
    ]
    with pytest.raises(rewrite_inventory.InventoryError, match="illegal transition"):
        rewrite_inventory.transition(manifest_path, row["id"], "contract_approved", evidence)


def test_contract_transition_requires_approved_matching_owner_hash(tmp_path: Path) -> None:
    source = _fixture_source(tmp_path / "source")
    manifest_path = tmp_path / "rewrite/coverage.json"
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("approved", encoding="utf-8")
    manifest = rewrite_inventory.build_manifest(manifest_path, source)
    row = manifest["entries"][0]
    _complete_row(row, _artifact(evidence), disposition="rewrite")
    row["owner_contract_id"] = "agent"
    row["owner_contract_hash"] = "contract-hash"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (manifest_path.parent / "owner-contracts.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "owner_id": "agent",
                        "state": "contract_approved",
                        "contract_hash": "contract-hash",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    rewrite_inventory.transition(manifest_path, row["id"], "disposition_approved", evidence)
    rewrite_inventory.transition(manifest_path, row["id"], "contract_approved", evidence)

    assert json.loads(manifest_path.read_text(encoding="utf-8"))["entries"][0]["state"] == "contract_approved"


def _init_reference(tmp_path: Path) -> tuple[Path, str, str]:
    worktree = tmp_path / "reference"
    worktree.mkdir()
    subprocess.run(["git", "init"], cwd=worktree, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=worktree, check=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=worktree, check=True)
    _write(worktree / "backend/app/main.py", "app = object()\n")
    subprocess.run(["git", "add", "."], cwd=worktree, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=worktree, check=True, capture_output=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=worktree, check=True, capture_output=True, text=True
    ).stdout.strip()
    return worktree, head, rewrite_inventory._tracked_content_hash(worktree)


def test_reference_integrity_detects_head_content_and_dirty_changes(tmp_path: Path) -> None:
    worktree, head, content_hash = _init_reference(tmp_path)
    manifest = {
        "reference": {"expected_head": head, "tracked_content_hash": content_hash},
    }

    rewrite_inventory._verify_reference(manifest, worktree, head, require_clean=True)
    (worktree / "backend/app/main.py").write_text("app = None\n", encoding="utf-8")

    with pytest.raises(rewrite_inventory.InventoryError, match="not clean"):
        rewrite_inventory._verify_reference(manifest, worktree, head, require_clean=True)
    with pytest.raises(rewrite_inventory.InventoryError, match="tracked content changed"):
        rewrite_inventory._verify_reference(manifest, worktree, head, require_clean=False)


def test_bind_reference_records_the_clean_checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _fixture_source(tmp_path / "source")
    manifest_path = tmp_path / "rewrite/coverage.json"
    worktree, head, content_hash = _init_reference(tmp_path)
    rewrite_inventory.build_manifest(manifest_path, source)
    monkeypatch.setattr(rewrite_inventory, "_backend_root", lambda: tmp_path / "target/backend")

    rewrite_inventory.bind_reference(manifest_path, worktree, head[:8])

    reference = json.loads(manifest_path.read_text(encoding="utf-8"))["reference"]
    assert reference == {
        "expected_head": head[:8],
        "persistence_namespace": "clawith_legacy_reference",
        "tracked_content_hash": content_hash,
        "worktree": str(worktree),
    }


def test_reference_environment_requires_distinct_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = {
        "reference": {"persistence_namespace": "legacy"},
        "target": {"persistence_namespace": "target"},
    }
    black_box = {
        "persistence_namespace": "legacy",
        "environment_from": {"DATABASE_URL": "LEGACY_DATABASE_URL"},
        "target_environment_from": {"DATABASE_URL": "TARGET_DATABASE_URL"},
    }
    monkeypatch.setenv("LEGACY_DATABASE_URL", "postgresql://legacy")
    monkeypatch.setenv("TARGET_DATABASE_URL", "postgresql://target")

    environment = rewrite_inventory._isolated_environment(manifest, black_box)

    assert environment["DATABASE_URL"] == "postgresql://legacy"
    monkeypatch.setenv("TARGET_DATABASE_URL", "postgresql://legacy")
    with pytest.raises(rewrite_inventory.InventoryError, match="share persistence resource"):
        rewrite_inventory._isolated_environment(manifest, black_box)


def test_release_preflight_requires_all_terminal_and_never_removes_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _fixture_source(tmp_path / "source")
    manifest_path = tmp_path / "rewrite/coverage.json"
    worktree, head, content_hash = _init_reference(tmp_path)
    manifest = rewrite_inventory.build_manifest(manifest_path, source)
    manifest["reference"] = {
        "expected_head": head,
        "persistence_namespace": "legacy",
        "tracked_content_hash": content_hash,
        "worktree": str(worktree),
    }
    manifest["target"] = {"persistence_namespace": "target"}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(rewrite_inventory.InventoryError, match="nonterminal="):
        rewrite_inventory.release_reference_preflight(manifest_path, worktree)

    for row in manifest["entries"]:
        evidence = tmp_path / f"{hashlib.sha256(row['id'].encode()).hexdigest()}.txt"
        evidence.write_text("approved", encoding="utf-8")
        record = _artifact(evidence)
        _complete_row(row, record, disposition="delete")
        row["state"] = "deletion_approved"
        row["removal_evidence"] = [record]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(
        rewrite_inventory,
        "_git",
        lambda _path, *args: (
            f"worktree {worktree}\nHEAD {head}" if args == ("worktree", "list", "--porcelain") else head
        ),
    )
    monkeypatch.setattr(rewrite_inventory, "_verify_reference", lambda *args, **kwargs: None)

    assert rewrite_inventory.release_reference_preflight(manifest_path, worktree) == worktree
    rewrite_inventory.release_reference(manifest_path, worktree, preflight_only=True)
    assert worktree.exists()
