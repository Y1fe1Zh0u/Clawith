from __future__ import annotations

import ast
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
LEGACY_TOOL_IMPORT_IDENTITIES = (
    Path("app/api/tools"),
    Path("app/models/tool"),
    Path("app/services/agent_tools"),
    Path("app/services/builtin_tool_definitions"),
    Path("app/services/tool_config"),
    Path("app/services/tool_exchange"),
    Path("app/services/tool_seeder"),
)
LEGACY_TOOL_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_TOOL_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_SKILL_IMPORT_IDENTITIES = (
    Path("app/api/skills"),
    Path("app/models/skill"),
    Path("app/services/skill_creator_content"),
    Path("app/services/skill_seeder"),
)
LEGACY_SKILL_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_SKILL_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_SKILL_CREATOR_FILES = Path("app/services/skill_creator_files")
OPENCLAW_GATEWAY_IMPORT_IDENTITIES = (
    Path("app/api/gateway"),
    Path("app/models/gateway_message"),
    Path("app/services/agent_manager"),
)
OPENCLAW_GATEWAY_REINTRODUCTIONS = [
    (identity, representation)
    for identity in OPENCLAW_GATEWAY_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_CREDENTIAL_IMPORT_IDENTITIES = (
    Path("app/api/agent_credentials"),
    Path("app/dao/agent_credential_dao"),
    Path("app/models/agent_credential"),
    Path("app/schemas/agent_credential"),
)
LEGACY_CREDENTIAL_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_CREDENTIAL_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_CREDENTIAL_DAO_EXPORT = "agent_credential_dao"
DYNAMIC_MODULE_EXPORT_HOOK = "__getattr__"
DAO_PACKAGE_INIT = Path("app/dao/__init__.py")


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


def _assert_deleted_legacy_tool_authorities(backend_root: Path) -> None:
    for identity in LEGACY_TOOL_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted legacy Tool authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted legacy Tool authority package was reintroduced: {identity}"
            )


def _assert_deleted_legacy_skill_authorities(backend_root: Path) -> None:
    for identity in LEGACY_SKILL_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted legacy Skill authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted legacy Skill authority package was reintroduced: {identity}"
            )

    creator_files = backend_root / LEGACY_SKILL_CREATOR_FILES
    if creator_files.exists():
        raise DeletedAuthorityViolation(
            "deleted legacy Skill creator-files path was reintroduced: "
            f"{LEGACY_SKILL_CREATOR_FILES}"
        )


def _assert_deleted_openclaw_gateway_authorities(backend_root: Path) -> None:
    for identity in OPENCLAW_GATEWAY_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted OpenClaw/Gateway authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted OpenClaw/Gateway authority package was reintroduced: {identity}"
            )


def _assert_deleted_legacy_credential_authorities(backend_root: Path) -> None:
    for identity in LEGACY_CREDENTIAL_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted legacy Credential authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted legacy Credential authority package was reintroduced: {identity}"
            )


def _assert_deleted_legacy_credential_dao_export(backend_root: Path) -> None:
    package_init = backend_root / DAO_PACKAGE_INIT
    if not package_init.is_file():
        return

    tree = ast.parse(package_init.read_text(encoding="utf-8"), filename=str(package_init))
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            statement.name == DYNAMIC_MODULE_EXPORT_HOOK
        ):
            raise DeletedAuthorityViolation(
                "deleted legacy Credential DAO package export can be restored by "
                "a module-level __getattr__ hook"
            )

    for node in ast.walk(tree):
        references_dynamic_hook = (
            isinstance(node, ast.Name) and node.id == DYNAMIC_MODULE_EXPORT_HOOK
        ) or (
            isinstance(node, ast.Attribute) and node.attr == DYNAMIC_MODULE_EXPORT_HOOK
        ) or (
            isinstance(node, ast.Constant) and node.value == DYNAMIC_MODULE_EXPORT_HOOK
        ) or (
            isinstance(node, ast.keyword) and node.arg == DYNAMIC_MODULE_EXPORT_HOOK
        ) or (
            isinstance(node, ast.alias)
            and (
                node.name.split(".")[-1] == DYNAMIC_MODULE_EXPORT_HOOK
                or node.asname == DYNAMIC_MODULE_EXPORT_HOOK
            )
        )
        if references_dynamic_hook:
            raise DeletedAuthorityViolation(
                "deleted legacy Credential DAO package export can be restored by "
                "a module-level __getattr__ hook"
            )

        references_export = (
            isinstance(node, ast.Name) and node.id == LEGACY_CREDENTIAL_DAO_EXPORT
        ) or (
            isinstance(node, ast.Attribute)
            and node.attr == LEGACY_CREDENTIAL_DAO_EXPORT
        ) or (
            isinstance(node, ast.Constant)
            and node.value == LEGACY_CREDENTIAL_DAO_EXPORT
        ) or (
            isinstance(node, ast.keyword)
            and node.arg == LEGACY_CREDENTIAL_DAO_EXPORT
        ) or (
            isinstance(node, ast.alias)
            and (
                node.name.split(".")[-1] == LEGACY_CREDENTIAL_DAO_EXPORT
                or node.asname == LEGACY_CREDENTIAL_DAO_EXPORT
            )
        )
        if references_export:
            raise DeletedAuthorityViolation(
                "deleted legacy Credential DAO package export was reintroduced: "
                f"{LEGACY_CREDENTIAL_DAO_EXPORT}"
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


def test_legacy_tool_import_identities_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_tool_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_TOOL_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_TOOL_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_tool_import_identity_fails_the_guard(
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
        match=f"deleted legacy Tool authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_tool_authorities(tmp_path)


def test_legacy_skill_authorities_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_skill_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_SKILL_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_SKILL_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_skill_import_identity_fails_the_guard(
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
        match=f"deleted legacy Skill authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_skill_authorities(tmp_path)


def test_reintroduced_legacy_skill_creator_files_path_fails_the_guard(
    tmp_path: Path,
) -> None:
    creator_files = tmp_path / LEGACY_SKILL_CREATOR_FILES
    creator_files.mkdir(parents=True)
    (creator_files / "generated.py").write_text("", encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Skill creator-files path was reintroduced",
    ):
        _assert_deleted_legacy_skill_authorities(tmp_path)


def test_openclaw_gateway_authorities_are_absent_from_target_tree() -> None:
    _assert_deleted_openclaw_gateway_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    OPENCLAW_GATEWAY_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in OPENCLAW_GATEWAY_REINTRODUCTIONS
    ],
)
def test_reintroduced_openclaw_gateway_import_identity_fails_the_guard(
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
        match=f"deleted OpenClaw/Gateway authority {representation} was reintroduced",
    ):
        _assert_deleted_openclaw_gateway_authorities(tmp_path)


def test_legacy_credential_authorities_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_credential_authorities(BACKEND_ROOT)


def test_legacy_credential_dao_package_export_is_absent_from_target_tree() -> None:
    _assert_deleted_legacy_credential_dao_export(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_CREDENTIAL_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_CREDENTIAL_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_credential_import_identity_fails_the_guard(
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
        match=f"deleted legacy Credential authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_credential_authorities(tmp_path)


@pytest.mark.parametrize(
    "package_source",
    [
        "from app.dao.agent_credential_dao import agent_credential_dao\n",
        "from app.dao.agent_credential_dao import agent_credential_dao as restored\n",
        "agent_credential_dao = object()\n",
        '__all__ = ["agent_credential_dao"]\n',
        "def __getattr__(name):\n    return object()\n",
        "__getattr__ = lambda name: object()\n",
        'globals()["agent_credential_dao"] = object()\n',
    ],
    ids=[
        "direct-import",
        "aliased-import",
        "assignment-reexport",
        "all-exposure",
        "module-getattr",
        "assigned-module-getattr",
        "globals-restoration",
    ],
)
def test_reintroduced_legacy_credential_dao_package_export_fails_the_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Credential DAO package export",
    ):
        _assert_deleted_legacy_credential_dao_export(tmp_path)
