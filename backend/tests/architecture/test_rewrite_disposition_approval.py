from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = BACKEND_ROOT / "scripts/approve_rewrite_dispositions.py"
SPEC = importlib.util.spec_from_file_location("approve_rewrite_dispositions", SCRIPT_PATH)
assert SPEC and SPEC.loader
approval = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = approval
SPEC.loader.exec_module(approval)


def _manifest() -> dict:
    return json.loads((BACKEND_ROOT / "rewrite/coverage.json").read_text(encoding="utf-8"))


def test_classifier_is_total_and_uses_exact_owner_roster() -> None:
    manifest = _manifest()
    owner_contracts = json.loads((BACKEND_ROOT / "rewrite/owner-contracts.json").read_text(encoding="utf-8"))
    owners = {row["owner_id"] for row in owner_contracts["owners"]}

    decisions = [approval.classify(row) for row in manifest["entries"]]

    assert len(decisions) == 401
    assert all(
        decision.disposition in {"delete", "defer_rewrite", "reuse_rewrite", "rewrite"} for decision in decisions
    )
    assert {decision.owner for decision in decisions if decision.owner} <= owners


def test_removed_authorities_do_not_receive_target_owners() -> None:
    rows = {row["id"]: row for row in _manifest()["entries"]}

    for row_id in (
        "GET:/api/agents/{agent_id}/approvals",
        "POST:/api/agents/{agent_id}/start",
        "GET:/api/experience/entries",
        "POST:/api/gateway/heartbeat",
        "GET:/api/agents/{agent_id}/tasks/",
        "LIFECYCLE:bootstrap:Base_metadata_create_all",
        "LIFECYCLE:run:running_runtime_worker_context",
    ):
        decision = approval.classify(rows[row_id])
        assert decision.disposition == "delete"
        assert decision.owner is None


def test_split_surfaces_resolve_to_one_owner_each() -> None:
    rows = {row["id"]: row for row in _manifest()["entries"]}

    assert approval.classify(rows["PUT:/api/agents/{agent_id}/permissions"]).owner == "permission"
    assert approval.classify(rows["POST:/api/agents/{agent_id}/collaborate/message"]).owner == "a2a"
    assert approval.classify(rows["GET:/api/enterprise/audit-logs"]).owner == "audit"
    assert approval.classify(rows["GET:/api/enterprise/llm-models"]).owner == "model"
    assert approval.classify(rows["GET:/api/enterprise/info"]).owner == "tenant_knowledge"
    assert approval.classify(rows["GET:/api/agents/{agent_id}/files/content"]).owner == "workspace"
    assert approval.classify(rows["POST:/api/agents/{agent_id}/files/import-from-clawhub"]).owner == "capability_market"
