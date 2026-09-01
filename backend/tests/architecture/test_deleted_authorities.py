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
LEGACY_AGENT_IMPORT_IDENTITIES = (
    Path("app/models/agent"),
    Path("app/api/agents"),
    Path("app/dao/agent_dao"),
    Path("app/dao/agent_access_dao"),
    Path("app/services/agent_seeder"),
)
LEGACY_AGENT_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_AGENT_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_AGENT_DAO_EXPORTS = ("agent_dao", "agent_access_dao")
LEGACY_IDENTITY_TENANT_IMPORT_IDENTITIES = (
    Path("app/models/user"),
    Path("app/models/tenant"),
    Path("app/models/tenant_setting"),
    Path("app/api/users"),
    Path("app/api/tenants"),
    Path("app/dao/identity_dao"),
    Path("app/dao/user_dao"),
    Path("app/dao/tenant_dao"),
)
LEGACY_IDENTITY_TENANT_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_IDENTITY_TENANT_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_IDENTITY_TENANT_DAO_EXPORTS = (
    "identity_dao",
    "user_dao",
    "tenant_dao",
)
LEGACY_AUTH_IMPORT_IDENTITIES = (
    Path("app/api/auth"),
    Path("app/services/auth_provider"),
    Path("app/services/auth_registry"),
    Path("app/services/registration_service"),
    Path("app/services/password_reset_service"),
    Path("app/services/email_verification_service"),
)
LEGACY_AUTH_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_AUTH_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_AUTH_PACKAGE_EXPORTS = {
    Path("app/api/__init__.py"): ("auth",),
    Path("app/services/__init__.py"): (
        "auth_provider",
        "auth_registry",
        "auth_provider_registry",
        "registration_service",
        "password_reset_service",
        "email_verification_service",
    ),
}
LEGACY_AUTH_DOTTED_IMPORT_IDENTITIES = tuple(
    dict.fromkeys(
        [
            identity.as_posix().replace("/", ".")
            for identity in LEGACY_AUTH_IMPORT_IDENTITIES
        ]
        + [
            f"{relative_path.parent.as_posix().replace('/', '.')}.{export}"
            for relative_path, exports in LEGACY_AUTH_PACKAGE_EXPORTS.items()
            for export in exports
        ]
    )
)
LEGACY_SSO_IMPORT_IDENTITIES = (
    Path("app/api/sso"),
    Path("app/api/google_workspace"),
    Path("app/models/identity"),
    Path("app/dao/identity_provider_dao"),
    Path("app/services/sso_service"),
    Path("app/services/sso_session_security"),
    Path("app/services/identity_provider_lookup"),
    Path("app/services/google_workspace_oauth"),
)
LEGACY_SSO_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_SSO_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_SSO_DAO_EXPORT = "identity_provider_dao"
LEGACY_SSO_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_SSO_IMPORT_IDENTITIES
)
DELETED_AUTHORITY_GUARD_TEST = Path("tests/architecture/test_deleted_authorities.py")
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


def _assert_deleted_legacy_agent_authorities(backend_root: Path) -> None:
    for identity in LEGACY_AGENT_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted legacy Agent authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted legacy Agent authority package was reintroduced: {identity}"
            )


def _assert_deleted_legacy_agent_dao_exports(backend_root: Path) -> None:
    package_init = backend_root / DAO_PACKAGE_INIT
    if not package_init.is_file():
        return

    tree = ast.parse(package_init.read_text(encoding="utf-8"), filename=str(package_init))
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            statement.name == DYNAMIC_MODULE_EXPORT_HOOK
        ):
            raise DeletedAuthorityViolation(
                "deleted legacy Agent DAO package exports can be restored by "
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
                "deleted legacy Agent DAO package exports can be restored by "
                "a module-level __getattr__ hook"
            )

        for export in LEGACY_AGENT_DAO_EXPORTS:
            references_export = (
                isinstance(node, ast.Name) and node.id == export
            ) or (
                isinstance(node, ast.Attribute) and node.attr == export
            ) or (
                isinstance(node, ast.Constant) and node.value == export
            ) or (
                isinstance(node, ast.keyword) and node.arg == export
            ) or (
                isinstance(node, ast.alias)
                and (
                    node.name.split(".")[-1] == export
                    or node.asname == export
                )
            )
            if references_export:
                raise DeletedAuthorityViolation(
                    "deleted legacy Agent DAO package export was reintroduced: "
                    f"{export}"
                )


def _assert_deleted_legacy_identity_tenant_authorities(backend_root: Path) -> None:
    for identity in LEGACY_IDENTITY_TENANT_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Identity/Tenant authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Identity/Tenant authority package was reintroduced: "
                f"{identity}"
            )


def _assert_deleted_legacy_identity_tenant_dao_exports(
    backend_root: Path,
) -> None:
    package_init = backend_root / DAO_PACKAGE_INIT
    if not package_init.is_file():
        return

    tree = ast.parse(package_init.read_text(encoding="utf-8"), filename=str(package_init))
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            statement.name == DYNAMIC_MODULE_EXPORT_HOOK
        ):
            raise DeletedAuthorityViolation(
                "deleted legacy Identity/Tenant DAO package exports can be restored by "
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
                "deleted legacy Identity/Tenant DAO package exports can be restored by "
                "a module-level __getattr__ hook"
            )

        for export in LEGACY_IDENTITY_TENANT_DAO_EXPORTS:
            references_export = (
                isinstance(node, ast.Name) and node.id == export
            ) or (
                isinstance(node, ast.Attribute) and node.attr == export
            ) or (
                isinstance(node, ast.Constant) and node.value == export
            ) or (
                isinstance(node, ast.keyword) and node.arg == export
            ) or (
                isinstance(node, ast.alias)
                and (
                    node.name.split(".")[-1] == export
                    or node.asname == export
                )
            )
            if references_export:
                raise DeletedAuthorityViolation(
                    "deleted legacy Identity/Tenant DAO package export was "
                    f"reintroduced: {export}"
                )


def _assert_deleted_legacy_auth_authorities(backend_root: Path) -> None:
    for identity in LEGACY_AUTH_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted legacy Auth authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted legacy Auth authority package was reintroduced: {identity}"
            )


def _assert_deleted_legacy_auth_package_exports(backend_root: Path) -> None:
    for relative_path, exports in LEGACY_AUTH_PACKAGE_EXPORTS.items():
        package_init = backend_root / relative_path
        if not package_init.is_file():
            continue

        tree = ast.parse(
            package_init.read_text(encoding="utf-8"),
            filename=str(package_init),
        )
        for statement in tree.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                statement.name == DYNAMIC_MODULE_EXPORT_HOOK
            ):
                raise DeletedAuthorityViolation(
                    "deleted legacy Auth package exports can be restored by "
                    f"a module-level __getattr__ hook in {relative_path}"
                )

        for node in ast.walk(tree):
            references_dynamic_hook = (
                isinstance(node, ast.Name) and node.id == DYNAMIC_MODULE_EXPORT_HOOK
            ) or (
                isinstance(node, ast.Attribute)
                and node.attr == DYNAMIC_MODULE_EXPORT_HOOK
            ) or (
                isinstance(node, ast.Constant)
                and node.value == DYNAMIC_MODULE_EXPORT_HOOK
            ) or (
                isinstance(node, ast.keyword)
                and node.arg == DYNAMIC_MODULE_EXPORT_HOOK
            ) or (
                isinstance(node, ast.alias)
                and (
                    node.name.split(".")[-1] == DYNAMIC_MODULE_EXPORT_HOOK
                    or node.asname == DYNAMIC_MODULE_EXPORT_HOOK
                )
            )
            if references_dynamic_hook:
                raise DeletedAuthorityViolation(
                    "deleted legacy Auth package exports can be restored by "
                    f"a module-level __getattr__ hook in {relative_path}"
                )

            for export in exports:
                references_export = (
                    isinstance(node, ast.Name) and node.id == export
                ) or (
                    isinstance(node, ast.Attribute) and node.attr == export
                ) or (
                    isinstance(node, ast.Constant) and node.value == export
                ) or (
                    isinstance(node, ast.keyword) and node.arg == export
                ) or (
                    isinstance(node, ast.alias)
                    and (
                        node.name.split(".")[-1] == export
                        or node.asname == export
                    )
                )
                if references_export:
                    raise DeletedAuthorityViolation(
                        "deleted legacy Auth package export was reintroduced in "
                        f"{relative_path}: {export}"
                    )


def _assert_tests_do_not_import_deleted_auth_authorities(
    backend_root: Path,
) -> None:
    tests_root = backend_root / "tests"
    if not tests_root.is_dir():
        return

    for source_path in sorted(tests_root.rglob("*.py")):
        relative_path = source_path.relative_to(backend_root)
        if relative_path == DELETED_AUTHORITY_GUARD_TEST:
            continue

        tree = ast.parse(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )
        imported_identities: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_identities.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_identities.append(node.module)
                imported_identities.extend(
                    f"{node.module}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )

        for imported_identity in imported_identities:
            for deleted_identity in LEGACY_AUTH_DOTTED_IMPORT_IDENTITIES:
                if imported_identity == deleted_identity or imported_identity.startswith(
                    f"{deleted_identity}."
                ):
                    raise DeletedAuthorityViolation(
                        "test imports deleted legacy Auth authority: "
                        f"{relative_path} -> {deleted_identity}"
                    )


def _assert_deleted_legacy_sso_authorities(backend_root: Path) -> None:
    for identity in LEGACY_SSO_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted legacy SSO authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted legacy SSO authority package was reintroduced: {identity}"
            )


def _assert_deleted_legacy_sso_dao_export(backend_root: Path) -> None:
    package_init = backend_root / DAO_PACKAGE_INIT
    if not package_init.is_file():
        return

    tree = ast.parse(package_init.read_text(encoding="utf-8"), filename=str(package_init))
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            statement.name == DYNAMIC_MODULE_EXPORT_HOOK
        ):
            raise DeletedAuthorityViolation(
                "deleted legacy SSO DAO package export can be restored by "
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
                "deleted legacy SSO DAO package export can be restored by "
                "a module-level __getattr__ hook"
            )

        references_export = (
            isinstance(node, ast.Name) and node.id == LEGACY_SSO_DAO_EXPORT
        ) or (
            isinstance(node, ast.Attribute) and node.attr == LEGACY_SSO_DAO_EXPORT
        ) or (
            isinstance(node, ast.Constant) and node.value == LEGACY_SSO_DAO_EXPORT
        ) or (
            isinstance(node, ast.keyword) and node.arg == LEGACY_SSO_DAO_EXPORT
        ) or (
            isinstance(node, ast.alias)
            and (
                node.name.split(".")[-1] == LEGACY_SSO_DAO_EXPORT
                or node.asname == LEGACY_SSO_DAO_EXPORT
            )
        )
        if references_export:
            raise DeletedAuthorityViolation(
                "deleted legacy SSO DAO package export was reintroduced: "
                f"{LEGACY_SSO_DAO_EXPORT}"
            )


def _assert_tests_do_not_import_deleted_sso_authorities(
    backend_root: Path,
) -> None:
    tests_root = backend_root / "tests"
    if not tests_root.is_dir():
        return

    for source_path in sorted(tests_root.rglob("*.py")):
        relative_path = source_path.relative_to(backend_root)
        if relative_path == DELETED_AUTHORITY_GUARD_TEST:
            continue

        tree = ast.parse(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )
        imported_identities: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_identities.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_identities.append(node.module)
                imported_identities.extend(
                    f"{node.module}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )

        for imported_identity in imported_identities:
            for deleted_identity in LEGACY_SSO_DOTTED_IMPORT_IDENTITIES:
                if imported_identity == deleted_identity or imported_identity.startswith(
                    f"{deleted_identity}."
                ):
                    raise DeletedAuthorityViolation(
                        "test imports deleted legacy SSO authority: "
                        f"{relative_path} -> {deleted_identity}"
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


def test_legacy_agent_authorities_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_agent_authorities(BACKEND_ROOT)


def test_legacy_agent_dao_package_exports_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_agent_dao_exports(BACKEND_ROOT)


def test_legacy_identity_tenant_authorities_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_identity_tenant_authorities(BACKEND_ROOT)


def test_legacy_identity_tenant_dao_exports_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_identity_tenant_dao_exports(BACKEND_ROOT)


def test_legacy_auth_authorities_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_auth_authorities(BACKEND_ROOT)


def test_legacy_auth_package_exports_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_auth_package_exports(BACKEND_ROOT)


def test_backend_tests_do_not_import_deleted_auth_authorities() -> None:
    _assert_tests_do_not_import_deleted_auth_authorities(BACKEND_ROOT)


def test_legacy_sso_authorities_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_sso_authorities(BACKEND_ROOT)


def test_legacy_sso_dao_package_export_is_absent_from_target_tree() -> None:
    _assert_deleted_legacy_sso_dao_export(BACKEND_ROOT)


def test_backend_tests_do_not_import_deleted_sso_authorities() -> None:
    _assert_tests_do_not_import_deleted_sso_authorities(BACKEND_ROOT)


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


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_AGENT_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_AGENT_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_agent_import_identity_fails_the_guard(
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
        match=f"deleted legacy Agent authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_agent_authorities(tmp_path)


@pytest.mark.parametrize(
    "package_source",
    [
        "from app.dao.agent_dao import agent_dao\n",
        "from app.dao.agent_access_dao import agent_access_dao as restored\n",
        "agent_dao = object()\n",
        '__all__ = ["agent_access_dao"]\n',
        "def __getattr__(name):\n    return object()\n",
        "__getattr__ = lambda name: object()\n",
        'globals()["agent_dao"] = object()\n',
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
def test_reintroduced_legacy_agent_dao_package_export_fails_the_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Agent DAO package export",
    ):
        _assert_deleted_legacy_agent_dao_exports(tmp_path)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_IDENTITY_TENANT_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_IDENTITY_TENANT_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_identity_tenant_import_identity_fails_the_guard(
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
        match=(
            "deleted legacy Identity/Tenant authority "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_identity_tenant_authorities(tmp_path)


@pytest.mark.parametrize(
    "package_source",
    [
        "from app.dao.identity_dao import identity_dao\n",
        "from app.dao.user_dao import user_dao as restored\n",
        "tenant_dao = object()\n",
        '__all__ = ["identity_dao"]\n',
        "def __getattr__(name):\n    return object()\n",
        "__getattr__ = lambda name: object()\n",
        'globals()["user_dao"] = object()\n',
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
def test_reintroduced_legacy_identity_tenant_dao_export_fails_the_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Identity/Tenant DAO package export",
    ):
        _assert_deleted_legacy_identity_tenant_dao_exports(tmp_path)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_AUTH_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_AUTH_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_auth_import_identity_fails_the_guard(
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
        match=f"deleted legacy Auth authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_auth_authorities(tmp_path)


@pytest.mark.parametrize(
    ("relative_path", "package_source"),
    [
        (Path("app/api/__init__.py"), "from app.api import auth\n"),
        (Path("app/api/__init__.py"), '__all__ = ["auth"]\n'),
        (Path("app/services/__init__.py"), "auth_provider = object()\n"),
        (
            Path("app/services/__init__.py"),
            "from app.services.auth_registry import auth_provider_registry\n",
        ),
        (Path("app/services/__init__.py"), "def __getattr__(name):\n    return object()\n"),
        (
            Path("app/services/__init__.py"),
            'globals()["registration_service"] = object()\n',
        ),
    ],
    ids=[
        "api-direct-import",
        "api-all-exposure",
        "services-assignment",
        "services-direct-import",
        "services-module-getattr",
        "services-globals-restoration",
    ],
)
def test_reintroduced_legacy_auth_package_export_fails_the_guard(
    tmp_path: Path,
    relative_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / relative_path
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Auth package export",
    ):
        _assert_deleted_legacy_auth_package_exports(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.api.auth\n",
        "from app.api import auth\n",
        "from app.services.auth_registry import auth_provider_registry\n",
        "from app.services import registration_service\n",
        "from app.services import auth_provider_registry as registry\n",
    ],
    ids=[
        "direct-module-import",
        "package-submodule-import",
        "service-symbol-import",
        "services-package-import",
        "aliased-package-export-import",
    ],
)
def test_backend_test_import_of_deleted_auth_authority_fails_the_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_auth_dependency.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test imports deleted legacy Auth authority",
    ):
        _assert_tests_do_not_import_deleted_auth_authorities(tmp_path)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_SSO_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_SSO_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_sso_import_identity_fails_the_guard(
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
        match=f"deleted legacy SSO authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_sso_authorities(tmp_path)


@pytest.mark.parametrize(
    "package_source",
    [
        "from app.dao.identity_provider_dao import identity_provider_dao\n",
        "identity_provider_dao = object()\n",
        '__all__ = ["identity_provider_dao"]\n',
        "def __getattr__(name):\n    return object()\n",
        "__getattr__ = lambda name: object()\n",
        'globals()["identity_provider_dao"] = object()\n',
    ],
    ids=[
        "direct-import",
        "assignment-reexport",
        "all-exposure",
        "module-getattr",
        "assigned-module-getattr",
        "globals-restoration",
    ],
)
def test_reintroduced_legacy_sso_dao_package_export_fails_the_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy SSO DAO package export",
    ):
        _assert_deleted_legacy_sso_dao_export(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.api.sso\n",
        "from app.api import google_workspace\n",
        "from app.models.identity import IdentityProvider\n",
        "from app.dao import identity_provider_dao\n",
        "from app.services.sso_service import sso_service\n",
        "from app.services import google_workspace_oauth\n",
    ],
    ids=[
        "direct-api-import",
        "api-package-import",
        "model-import",
        "dao-package-import",
        "service-symbol-import",
        "services-package-import",
    ],
)
def test_backend_test_import_of_deleted_sso_authority_fails_the_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_sso_dependency.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test imports deleted legacy SSO authority",
    ):
        _assert_tests_do_not_import_deleted_sso_authorities(tmp_path)
