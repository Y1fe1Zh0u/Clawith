"""Contract tests for the canonical Backend 50-Agent load profile."""

from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "validate_load_profile.py"
PROFILE_PATH = Path(__file__).parent / "profiles" / "backend_50.json"


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_load_profile", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _profile() -> dict[str, object]:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def _nested_mapping(profile: dict[str, object], *path: str) -> dict[str, object]:
    current: object = profile
    for part in path:
        assert isinstance(current, dict)
        current = current[part]
    assert isinstance(current, dict)
    return current


def test_canonical_backend_50_profile_is_valid() -> None:
    validator = _load_validator()

    assert validator.validate_profile(_profile()) == ()


@pytest.mark.parametrize(
    "path",
    [
        ("environment", "cpu_vcpus"),
        ("duration", "measurement_seconds"),
        ("provider", "first_delta_ms"),
        ("capacity", "run_pool"),
        ("thresholds", "p95_ms"),
        ("fairness", "tenant_agent_admission"),
    ],
)
def test_missing_critical_field_is_rejected(path: tuple[str, ...]) -> None:
    validator = _load_validator()
    profile = deepcopy(_profile())
    parent = _nested_mapping(profile, *path[:-1])
    del parent[path[-1]]

    issues = validator.validate_profile(profile)

    assert any(issue.path == ".".join(path) and issue.code == "missing" for issue in issues)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("environment", "cpu_vcpus"), 16),
        (("duration", "warmup_seconds"), 0),
        (("provider", "completion_ms"), 499),
        (("tools", "slow_latency_ms"), "2000"),
        (("capacity", "database_pools", "control"), 40),
        (("workload_mix", "direct_session"), 19),
        (("thresholds", "platform_error_rate_max_exclusive"), 1),
        (("fairness", "max_consecutive_skips_per_eligible_tenant"), 2),
    ],
)
def test_invalid_critical_field_is_rejected(path: tuple[str, ...], value: object) -> None:
    validator = _load_validator()
    profile = deepcopy(_profile())
    parent = _nested_mapping(profile, *path[:-1])
    parent[path[-1]] = value

    issues = validator.validate_profile(profile)

    assert any(issue.path == ".".join(path) and issue.code == "invalid" for issue in issues)


@pytest.mark.parametrize(
    "path",
    [
        (),
        ("capacity",),
        ("thresholds", "p95_ms"),
    ],
)
def test_unknown_critical_field_is_rejected(path: tuple[str, ...]) -> None:
    validator = _load_validator()
    profile = deepcopy(_profile())
    parent = _nested_mapping(profile, *path)
    parent["unspecified_override"] = 1

    issues = validator.validate_profile(profile)
    issue_path = ".".join((*path, "unspecified_override"))

    assert any(issue.path == issue_path and issue.code == "unknown" for issue in issues)


def test_cli_returns_success_for_canonical_profile() -> None:
    validator = _load_validator()

    assert validator.main([str(PROFILE_PATH)]) == 0


def test_cli_returns_failure_for_invalid_profile(tmp_path: Path) -> None:
    validator = _load_validator()
    profile = _profile()
    profile["unspecified_override"] = 1
    profile_path = tmp_path / "invalid.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    assert validator.main([str(profile_path)]) == 1
