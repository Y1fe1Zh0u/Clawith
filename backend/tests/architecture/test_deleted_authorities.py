from __future__ import annotations

from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_MODULE = Path("app/services/agent_context.py")
CONTEXT_PACKAGE = Path("app/services/agent_context")
EXPERIENCE_IMPORT_IDENTITIES = (
    Path("app/api/experience"),
    Path("app/models/experience"),
    Path("app/models/experience_reference"),
    Path("app/services/experience_retrieval"),
)
EXPERIENCE_REINTRODUCTIONS = [
    (identity, representation)
    for identity in EXPERIENCE_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
MODEL_LLM_IMPORT_IDENTITIES = (
    Path("app/models/llm"),
    Path("app/services/llm"),
)
MODEL_LLM_REINTRODUCTIONS = [
    (identity, representation)
    for identity in MODEL_LLM_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
PERSISTENT_TASK_IMPORT_IDENTITIES = (
    Path("app/models/task"),
    Path("app/api/tasks"),
    Path("app/services/task_executor"),
)
PERSISTENT_TASK_REINTRODUCTIONS = [
    (identity, representation)
    for identity in PERSISTENT_TASK_IMPORT_IDENTITIES
    for representation in ("module", "package")
]


class DeletedAuthorityViolation(RuntimeError):
    """A deleted Backend authority is present in the target tree."""


def _assert_deleted_context_authority(backend_root: Path) -> None:
    module = backend_root / CONTEXT_MODULE
    package = backend_root / CONTEXT_PACKAGE
    if module.is_file():
        raise DeletedAuthorityViolation(
            f"deleted Context authority module was reintroduced: {CONTEXT_MODULE}"
        )
    if package.is_dir():
        raise DeletedAuthorityViolation(
            f"deleted Context authority package was reintroduced: {CONTEXT_PACKAGE}"
        )


def _assert_deleted_experience_authorities(backend_root: Path) -> None:
    for identity in EXPERIENCE_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted Experience authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted Experience authority package was reintroduced: {identity}"
            )


def _assert_deleted_model_llm_authorities(backend_root: Path) -> None:
    for identity in MODEL_LLM_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted Model/LLM authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted Model/LLM authority package was reintroduced: {identity}"
            )


def _assert_deleted_persistent_task_authorities(backend_root: Path) -> None:
    for identity in PERSISTENT_TASK_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted Persistent Task authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted Persistent Task authority package was reintroduced: {identity}"
            )


def test_legacy_context_import_identity_is_absent_from_target_tree() -> None:
    _assert_deleted_context_authority(BACKEND_ROOT)


def test_reintroduced_context_module_fails_the_guard(tmp_path: Path) -> None:
    module = tmp_path / CONTEXT_MODULE
    module.parent.mkdir(parents=True)
    module.write_text("async def build_agent_context(): ...\n", encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted Context authority module was reintroduced",
    ):
        _assert_deleted_context_authority(tmp_path)


def test_reintroduced_context_package_fails_the_guard(tmp_path: Path) -> None:
    package = tmp_path / CONTEXT_PACKAGE
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted Context authority package was reintroduced",
    ):
        _assert_deleted_context_authority(tmp_path)


def test_legacy_experience_import_identities_are_absent_from_target_tree() -> None:
    _assert_deleted_experience_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    EXPERIENCE_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in EXPERIENCE_REINTRODUCTIONS
    ],
)
def test_reintroduced_experience_import_identity_fails_the_guard(
    tmp_path: Path,
    identity: Path,
    representation: str,
) -> None:
    authority = tmp_path / identity
    if representation == "module":
        authority.parent.mkdir(parents=True, exist_ok=True)
        authority.with_suffix(".py").write_text("", encoding="utf-8")
    else:
        authority.mkdir(parents=True, exist_ok=True)
        (authority / "__init__.py").write_text("", encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match=f"deleted Experience authority {representation} was reintroduced",
    ):
        _assert_deleted_experience_authorities(tmp_path)


def test_legacy_model_llm_import_identities_are_absent_from_target_tree() -> None:
    _assert_deleted_model_llm_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    MODEL_LLM_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in MODEL_LLM_REINTRODUCTIONS
    ],
)
def test_reintroduced_model_llm_import_identity_fails_the_guard(
    tmp_path: Path,
    identity: Path,
    representation: str,
) -> None:
    authority = tmp_path / identity
    if representation == "module":
        authority.parent.mkdir(parents=True, exist_ok=True)
        authority.with_suffix(".py").write_text("", encoding="utf-8")
    else:
        authority.mkdir(parents=True, exist_ok=True)
        (authority / "__init__.py").write_text("", encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match=f"deleted Model/LLM authority {representation} was reintroduced",
    ):
        _assert_deleted_model_llm_authorities(tmp_path)


def test_legacy_persistent_task_import_identities_are_absent_from_target_tree() -> None:
    _assert_deleted_persistent_task_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    PERSISTENT_TASK_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in PERSISTENT_TASK_REINTRODUCTIONS
    ],
)
def test_reintroduced_persistent_task_import_identity_fails_the_guard(
    tmp_path: Path,
    identity: Path,
    representation: str,
) -> None:
    authority = tmp_path / identity
    if representation == "module":
        authority.parent.mkdir(parents=True, exist_ok=True)
        authority.with_suffix(".py").write_text("", encoding="utf-8")
    else:
        authority.mkdir(parents=True, exist_ok=True)
        (authority / "__init__.py").write_text("", encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match=f"deleted Persistent Task authority {representation} was reintroduced",
    ):
        _assert_deleted_persistent_task_authorities(tmp_path)
