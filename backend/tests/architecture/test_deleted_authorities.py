from __future__ import annotations

import ast
import symtable
from pathlib import Path

import pytest
import yaml

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
LEGACY_AGENT_RUN_EVENT_DAO_IMPORT_IDENTITY = Path("app/dao/agent_run_event_dao")
LEGACY_AGENT_RUN_EVENT_DAO_REINTRODUCTIONS = [
    (LEGACY_AGENT_RUN_EVENT_DAO_IMPORT_IDENTITY, representation)
    for representation in ("module", "package")
]
LEGACY_AGENT_RUN_EVENT_DAO_DOTTED_IMPORT_IDENTITY = (
    LEGACY_AGENT_RUN_EVENT_DAO_IMPORT_IDENTITY.as_posix().replace("/", ".")
)
LEGACY_OKR_AGENT_HOOK_IMPORT_IDENTITY = Path("app/services/okr_agent_hook")
LEGACY_OKR_AGENT_HOOK_REINTRODUCTIONS = [
    (LEGACY_OKR_AGENT_HOOK_IMPORT_IDENTITY, representation)
    for representation in ("module", "package")
]
LEGACY_OKR_AGENT_HOOK_DOTTED_IMPORT_IDENTITY = (
    LEGACY_OKR_AGENT_HOOK_IMPORT_IDENTITY.as_posix().replace("/", ".")
)
LEGACY_TOKEN_TRACKER_IMPORT_IDENTITY = Path("app/services/token_tracker")
LEGACY_TOKEN_TRACKER_REINTRODUCTIONS = [
    (LEGACY_TOKEN_TRACKER_IMPORT_IDENTITY, representation)
    for representation in ("module", "package")
]
LEGACY_TOKEN_TRACKER_DOTTED_IMPORT_IDENTITY = (
    LEGACY_TOKEN_TRACKER_IMPORT_IDENTITY.as_posix().replace("/", ".")
)
LEGACY_WECOM_SERVICE_IMPORT_IDENTITY = Path("app/services/wecom_service")
LEGACY_WECOM_SERVICE_REINTRODUCTIONS = [
    (LEGACY_WECOM_SERVICE_IMPORT_IDENTITY, representation)
    for representation in ("module", "package")
]
LEGACY_WECOM_SERVICE_DOTTED_IMPORT_IDENTITY = (
    LEGACY_WECOM_SERVICE_IMPORT_IDENTITY.as_posix().replace("/", ".")
)
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
LEGACY_ORGANIZATION_RELATIONSHIP_IMPORT_IDENTITIES = (
    Path("app/models/org"),
    Path("app/api/organization"),
    Path("app/api/relationships"),
    Path("app/dao/org_member_dao"),
    Path("app/services/org_sync_adapter"),
    Path("app/services/org_sync_service"),
    Path("app/services/access_relationships"),
)
LEGACY_ORGANIZATION_RELATIONSHIP_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_ORGANIZATION_RELATIONSHIP_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_ORGANIZATION_RELATIONSHIP_DAO_EXPORT = "org_member_dao"
LEGACY_ORGANIZATION_RELATIONSHIP_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_ORGANIZATION_RELATIONSHIP_IMPORT_IDENTITIES
)
LEGACY_INVITATION_IMPORT_IDENTITIES = (
    Path("app/models/invitation_code"),
    Path("app/dao/invitation_code_dao"),
)
LEGACY_INVITATION_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_INVITATION_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_INVITATION_DAO_EXPORT = "invitation_code_dao"
LEGACY_INVITATION_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_INVITATION_IMPORT_IDENTITIES
)
LEGACY_ONBOARDING_IMPORT_IDENTITIES = (
    Path("app/models/onboarding"),
    Path("app/api/onboarding"),
    Path("app/services/onboarding"),
)
LEGACY_ONBOARDING_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_ONBOARDING_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_ONBOARDING_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_ONBOARDING_IMPORT_IDENTITIES
)
LEGACY_DIRECTORY_IMPORT_IDENTITIES = (
    Path("app/api/directory"),
    Path("app/services/agent_directory"),
)
LEGACY_DIRECTORY_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_DIRECTORY_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_DIRECTORY_PACKAGE_EXPORTS = {
    Path("app/api/__init__.py"): ("directory",),
    Path("app/services/__init__.py"): ("agent_directory",),
}
LEGACY_DIRECTORY_DOTTED_IMPORT_IDENTITIES = tuple(
    dict.fromkeys(
        [
            identity.as_posix().replace("/", ".")
            for identity in LEGACY_DIRECTORY_IMPORT_IDENTITIES
        ]
        + [
            f"{relative_path.parent.as_posix().replace('/', '.')}.{export}"
            for relative_path, exports in LEGACY_DIRECTORY_PACKAGE_EXPORTS.items()
            for export in exports
        ]
    )
)
LEGACY_FOCUS_IMPORT_IDENTITIES = (
    Path("app/models/focus"),
    Path("app/dao/focus_dao"),
    Path("app/api/focus"),
    Path("app/services/focus_service"),
)
LEGACY_FOCUS_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_FOCUS_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_FOCUS_DAO_EXPORT = "focus_dao"
LEGACY_FOCUS_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_FOCUS_IMPORT_IDENTITIES
)
LEGACY_NOTIFICATION_IMPORT_IDENTITIES = (
    Path("app/models/notification"),
    Path("app/api/notification"),
    Path("app/services/notification_service"),
)
LEGACY_NOTIFICATION_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_NOTIFICATION_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_NOTIFICATION_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_NOTIFICATION_IMPORT_IDENTITIES
)
LEGACY_PUBLISHED_PAGE_IMPORT_IDENTITIES = (
    Path("app/models/published_page"),
    Path("app/api/pages"),
)
LEGACY_PUBLISHED_PAGE_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_PUBLISHED_PAGE_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_PUBLISHED_PAGE_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_PUBLISHED_PAGE_IMPORT_IDENTITIES
)
LEGACY_PLAZA_IMPORT_IDENTITIES = (
    Path("app/models/plaza"),
    Path("app/api/plaza"),
)
LEGACY_PLAZA_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_PLAZA_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_PLAZA_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_PLAZA_IMPORT_IDENTITIES
)
LEGACY_AGENT_TEMPLATE_IMPORT_IDENTITIES = (
    Path("app/dao/agent_template_dao"),
    Path("app/services/template_seeder"),
)
LEGACY_AGENT_TEMPLATE_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_AGENT_TEMPLATE_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_AGENT_TEMPLATE_DAO_EXPORT = "agent_template_dao"
LEGACY_AGENT_TEMPLATE_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_AGENT_TEMPLATE_IMPORT_IDENTITIES
)
LEGACY_AGENTBAY_IMPORT_IDENTITIES = (
    Path("app/api/agentbay_control"),
    Path("app/services/agentbay_client"),
    Path("app/services/agentbay_live"),
)
LEGACY_AGENTBAY_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_AGENTBAY_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_AGENTBAY_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_AGENTBAY_IMPORT_IDENTITIES
)
LEGACY_TENANT_KNOWLEDGE_PUBLICATION_IMPORT_IDENTITIES = (
    Path("app/services/enterprise_sync"),
)
LEGACY_TENANT_KNOWLEDGE_PUBLICATION_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_TENANT_KNOWLEDGE_PUBLICATION_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_SESSION_SUBSTRATE_IMPORT_IDENTITIES = (
    Path("app/models/chat_session"),
    Path("app/dao/chat_session_dao"),
    Path("app/dao/chat_message_dao"),
    Path("app/services/chat_session_service"),
    Path("app/services/channel_session"),
    Path("app/api/chat_sessions"),
    Path("app/api/websocket"),
)
LEGACY_SESSION_SUBSTRATE_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_SESSION_SUBSTRATE_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_SESSION_SUBSTRATE_DAO_EXPORTS = (
    "chat_session_dao",
    "chat_message_dao",
)
LEGACY_SESSION_SUBSTRATE_FORBIDDEN_FACTS = {
    Path("app/models/audit.py"): frozenset(
        {
            "class:ChatMessage",
            "table:chat_messages",
            "enum:chat_role_enum",
        }
    ),
    Path("app/schemas/schemas.py"): frozenset(
        {
            "class:ChatMessageOut",
            "class:ChatSend",
        }
    ),
}
LEGACY_AUTONOMY_APPROVAL_IMPORT_IDENTITIES = (
    Path("app/services/autonomy_service"),
)
LEGACY_AUTONOMY_APPROVAL_REINTRODUCTIONS = [
    (identity, representation)
    for identity in LEGACY_AUTONOMY_APPROVAL_IMPORT_IDENTITIES
    for representation in ("module", "package")
]
LEGACY_AUTONOMY_APPROVAL_DOTTED_IMPORT_IDENTITIES = tuple(
    identity.as_posix().replace("/", ".")
    for identity in LEGACY_AUTONOMY_APPROVAL_IMPORT_IDENTITIES
)
LEGACY_AUTONOMY_APPROVAL_FORBIDDEN_FACTS = {
    Path("app/models/audit.py"): frozenset(
        {
            "class:ApprovalRequest",
            "table:approval_requests",
            "enum:approval_status_enum",
        }
    ),
    Path("app/api/enterprise.py"): frozenset(
        {
            "import:ApprovalRequest",
            "import:ApprovalRequestOut",
            "import:ApprovalAction",
            "import:autonomy_service",
            "reference:ApprovalRequest",
            "reference:ApprovalRequestOut",
            "reference:ApprovalAction",
            "reference:autonomy_service",
            "function:list_approvals",
            "function:resolve_approval",
            "route:GET:/approvals",
            "route:POST:/approvals/{approval_id}/resolve",
            "assigned:pending_approvals",
            "key:pending_approvals",
        }
    ),
    Path("app/api/advanced.py"): frozenset(
        {
            "class-field:TemplateCreate:default_autonomy_policy",
            "class-field:TemplateOut:default_autonomy_policy",
            "field:default_autonomy_policy",
            "key:default_autonomy_policy",
            "key:total_approvals",
            "key:pending_approvals",
        }
    ),
    Path("app/dao/agent_metrics_dao.py"): frozenset(
        {
            "import:ApprovalRequest",
            "reference:ApprovalRequest",
            "assigned:total_approvals",
            "assigned:pending_approvals",
            "key:total_approvals",
            "key:pending_approvals",
        }
    ),
    Path("app/schemas/schemas.py"): frozenset(
        {
            "class:ApprovalRequestOut",
            "class:ApprovalAction",
            "class-field:AgentCreate:autonomy_policy",
            "class-field:AgentOut:autonomy_policy",
            "class-field:AgentUpdate:autonomy_policy",
        }
    ),
    Path("app/services/feishu_service.py"): frozenset(
        {"function:send_approval_card"}
    ),
}
AGENT_TEMPLATE_METADATA_ROOT = Path("agent_templates")
LEGACY_TEMPLATE_AUTONOMY_FIELD = "default_autonomy_policy"
DELETED_AUTHORITY_GUARD_TEST = Path("tests/architecture/test_deleted_authorities.py")
DYNAMIC_MODULE_EXPORT_HOOK = "__getattr__"
DAO_PACKAGE_INIT = Path("app/dao/__init__.py")


class DeletedAuthorityViolation(RuntimeError):
    """A deleted Backend authority is present in the target tree."""


def _is_globals_call(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "globals"
        and not node.args
        and not node.keywords
    )


def _is_dynamic_export_hook_name(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value == DYNAMIC_MODULE_EXPORT_HOOK


def _is_globals_hook_target(node: ast.expr) -> bool:
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(_is_globals_hook_target(element) for element in node.elts)
    if isinstance(node, ast.Starred):
        return _is_globals_hook_target(node.value)
    return (
        isinstance(node, ast.Subscript)
        and _is_globals_call(node.value)
        and _is_dynamic_export_hook_name(node.slice)
    )


class _ModuleScopeDynamicExportHookVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.installs_hook = False

    def _visit_function_signature(
        self,
        *,
        decorators: list[ast.expr],
        arguments: ast.arguments,
    ) -> None:
        for decorator in decorators:
            self.visit(decorator)
        for default in (*arguments.defaults, *arguments.kw_defaults):
            if default is not None:
                self.visit(default)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_signature(
            decorators=node.decorator_list,
            arguments=node.args,
        )

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_signature(
            decorators=node.decorator_list,
            arguments=node.args,
        )

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_function_signature(decorators=[], arguments=node.args)

    def visit_Assign(self, node: ast.Assign) -> None:
        if any(_is_globals_hook_target(target) for target in node.targets):
            self.installs_hook = True
            return
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if _is_globals_hook_target(node.target):
            self.installs_hook = True
            return
        if node.value is not None:
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if _is_globals_hook_target(node.target):
            self.installs_hook = True
            return
        self.visit(node.value)

    def visit_Call(self, node: ast.Call) -> None:
        calls_globals_setitem = (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "__setitem__"
            and _is_globals_call(node.func.value)
            and bool(node.args)
            and _is_dynamic_export_hook_name(node.args[0])
        )
        calls_setattr = (
            isinstance(node.func, ast.Name)
            and node.func.id == "setattr"
            and len(node.args) >= 2
            and _is_dynamic_export_hook_name(node.args[1])
        )
        if calls_globals_setitem or calls_setattr:
            self.installs_hook = True
            return
        self.generic_visit(node)


def _assert_dao_package_exports_are_static(backend_root: Path) -> None:
    package_init = backend_root / DAO_PACKAGE_INIT
    if not package_init.is_file():
        return

    source = package_init.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(package_init))
    symbols = symtable.symtable(source, str(package_init), "exec")
    try:
        dynamic_hook = symbols.lookup(DYNAMIC_MODULE_EXPORT_HOOK)
    except KeyError:
        binds_dynamic_hook = False
    else:
        binds_dynamic_hook = (
            dynamic_hook.is_assigned()
            or dynamic_hook.is_imported()
            or dynamic_hook.is_namespace()
        )

    dynamic_installer = _ModuleScopeDynamicExportHookVisitor()
    dynamic_installer.visit(tree)
    if binds_dynamic_hook or dynamic_installer.installs_hook:
        raise DeletedAuthorityViolation(
            "app.dao package exports must be static; module-level __getattr__ is "
            "forbidden"
        )


def _assert_deleted_dao_package_exports(
    backend_root: Path,
    *,
    authority: str,
    exports: tuple[str, ...],
) -> None:
    package_init = backend_root / DAO_PACKAGE_INIT
    if not package_init.is_file():
        return

    tree = ast.parse(package_init.read_text(encoding="utf-8"), filename=str(package_init))
    for node in ast.walk(tree):
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
                    f"deleted legacy {authority} DAO package export was "
                    f"reintroduced: {export}"
                )


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
    _assert_deleted_dao_package_exports(
        backend_root,
        authority="Credential",
        exports=(LEGACY_CREDENTIAL_DAO_EXPORT,),
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
    _assert_deleted_dao_package_exports(
        backend_root,
        authority="Agent",
        exports=LEGACY_AGENT_DAO_EXPORTS,
    )


def _assert_deleted_legacy_agent_run_event_dao_authority(
    backend_root: Path,
) -> None:
    identity = LEGACY_AGENT_RUN_EVENT_DAO_IMPORT_IDENTITY
    module = (backend_root / identity).with_suffix(".py")
    package = backend_root / identity
    if module.is_file():
        raise DeletedAuthorityViolation(
            "deleted legacy Agent Run Event DAO compatibility module was "
            f"reintroduced: {identity}"
        )
    if package.is_dir():
        raise DeletedAuthorityViolation(
            "deleted legacy Agent Run Event DAO compatibility package was "
            f"reintroduced: {identity}"
        )


def _assert_tests_do_not_reference_deleted_agent_run_event_dao(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="Agent Run Event DAO compatibility",
        deleted_identities=(LEGACY_AGENT_RUN_EVENT_DAO_DOTTED_IMPORT_IDENTITY,),
    )


def _assert_deleted_legacy_okr_agent_hook_authority(backend_root: Path) -> None:
    identity = LEGACY_OKR_AGENT_HOOK_IMPORT_IDENTITY
    module = (backend_root / identity).with_suffix(".py")
    package = backend_root / identity
    if module.is_file():
        raise DeletedAuthorityViolation(
            f"deleted legacy OKR Agent Hook module was reintroduced: {identity}"
        )
    if package.is_dir():
        raise DeletedAuthorityViolation(
            f"deleted legacy OKR Agent Hook package was reintroduced: {identity}"
        )


def _assert_tests_do_not_reference_deleted_okr_agent_hook(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="OKR Agent Hook",
        deleted_identities=(LEGACY_OKR_AGENT_HOOK_DOTTED_IMPORT_IDENTITY,),
    )


def _assert_deleted_legacy_token_tracker_authority(backend_root: Path) -> None:
    identity = LEGACY_TOKEN_TRACKER_IMPORT_IDENTITY
    module = (backend_root / identity).with_suffix(".py")
    package = backend_root / identity
    if module.is_file():
        raise DeletedAuthorityViolation(
            f"deleted legacy Token Tracker module was reintroduced: {identity}"
        )
    if package.is_dir():
        raise DeletedAuthorityViolation(
            f"deleted legacy Token Tracker package was reintroduced: {identity}"
        )


def _assert_tests_do_not_reference_deleted_token_tracker(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="Token Tracker",
        deleted_identities=(LEGACY_TOKEN_TRACKER_DOTTED_IMPORT_IDENTITY,),
    )


def _assert_deleted_legacy_wecom_service_authority(backend_root: Path) -> None:
    identity = LEGACY_WECOM_SERVICE_IMPORT_IDENTITY
    module = (backend_root / identity).with_suffix(".py")
    package = backend_root / identity
    if module.is_file():
        raise DeletedAuthorityViolation(
            f"deleted legacy WeCom service module was reintroduced: {identity}"
        )
    if package.is_dir():
        raise DeletedAuthorityViolation(
            f"deleted legacy WeCom service package was reintroduced: {identity}"
        )


def _assert_tests_do_not_reference_deleted_wecom_service(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="WeCom service",
        deleted_identities=(LEGACY_WECOM_SERVICE_DOTTED_IMPORT_IDENTITY,),
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
    _assert_deleted_dao_package_exports(
        backend_root,
        authority="Identity/Tenant",
        exports=LEGACY_IDENTITY_TENANT_DAO_EXPORTS,
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
    _assert_deleted_dao_package_exports(
        backend_root,
        authority="SSO",
        exports=(LEGACY_SSO_DAO_EXPORT,),
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


def _assert_deleted_legacy_organization_relationship_authorities(
    backend_root: Path,
) -> None:
    for identity in LEGACY_ORGANIZATION_RELATIONSHIP_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Organization/Relationship authority module was "
                f"reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Organization/Relationship authority package was "
                f"reintroduced: {identity}"
            )


def _assert_deleted_legacy_organization_relationship_dao_export(
    backend_root: Path,
) -> None:
    _assert_deleted_dao_package_exports(
        backend_root,
        authority="Organization/Relationship",
        exports=(LEGACY_ORGANIZATION_RELATIONSHIP_DAO_EXPORT,),
    )


def _assert_tests_do_not_import_deleted_organization_relationship_authorities(
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
            for deleted_identity in (
                LEGACY_ORGANIZATION_RELATIONSHIP_DOTTED_IMPORT_IDENTITIES
            ):
                if imported_identity == deleted_identity or imported_identity.startswith(
                    f"{deleted_identity}."
                ):
                    raise DeletedAuthorityViolation(
                        "test imports deleted legacy Organization/Relationship authority: "
                        f"{relative_path} -> {deleted_identity}"
                    )


def _assert_deleted_legacy_invitation_authorities(backend_root: Path) -> None:
    for identity in LEGACY_INVITATION_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Invitation authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Invitation authority package was reintroduced: "
                f"{identity}"
            )


def _assert_deleted_legacy_invitation_dao_export(backend_root: Path) -> None:
    _assert_deleted_dao_package_exports(
        backend_root,
        authority="Invitation",
        exports=(LEGACY_INVITATION_DAO_EXPORT,),
    )


def _assert_tests_do_not_import_deleted_invitation_authorities(
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
            for deleted_identity in LEGACY_INVITATION_DOTTED_IMPORT_IDENTITIES:
                if imported_identity == deleted_identity or imported_identity.startswith(
                    f"{deleted_identity}."
                ):
                    raise DeletedAuthorityViolation(
                        "test imports deleted legacy Invitation authority: "
                        f"{relative_path} -> {deleted_identity}"
                    )


def _assert_deleted_legacy_onboarding_authorities(backend_root: Path) -> None:
    for identity in LEGACY_ONBOARDING_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Onboarding authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Onboarding authority package was reintroduced: "
                f"{identity}"
            )


def _assert_tests_do_not_import_deleted_onboarding_authorities(
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
            for deleted_identity in LEGACY_ONBOARDING_DOTTED_IMPORT_IDENTITIES:
                if imported_identity == deleted_identity or imported_identity.startswith(
                    f"{deleted_identity}."
                ):
                    raise DeletedAuthorityViolation(
                        "test imports deleted legacy Onboarding authority: "
                        f"{relative_path} -> {deleted_identity}"
                    )


def _assert_deleted_legacy_directory_authorities(backend_root: Path) -> None:
    for identity in LEGACY_DIRECTORY_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Directory authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Directory authority package was reintroduced: "
                f"{identity}"
            )


def _assert_deleted_legacy_directory_package_exports(backend_root: Path) -> None:
    for relative_path, exports in LEGACY_DIRECTORY_PACKAGE_EXPORTS.items():
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
                    "deleted legacy Directory package exports can be restored by "
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
                    "deleted legacy Directory package exports can be restored by "
                    f"a module-level __getattr__ hook in {relative_path}"
                )

            for export in exports:
                imports_export_module = (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    == f"{relative_path.parent.as_posix().replace('/', '.')}.{export}"
                )
                references_export = (
                    imports_export_module
                    or (isinstance(node, ast.Name) and node.id == export)
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
                        "deleted legacy Directory package export was reintroduced in "
                        f"{relative_path}: {export}"
                    )


def _assert_tests_do_not_import_deleted_directory_authorities(
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
            for deleted_identity in LEGACY_DIRECTORY_DOTTED_IMPORT_IDENTITIES:
                if imported_identity == deleted_identity or imported_identity.startswith(
                    f"{deleted_identity}."
                ):
                    raise DeletedAuthorityViolation(
                        "test imports deleted legacy Directory authority: "
                        f"{relative_path} -> {deleted_identity}"
                    )


def _assert_deleted_legacy_focus_authorities(backend_root: Path) -> None:
    for identity in LEGACY_FOCUS_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                f"deleted legacy Focus authority module was reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                f"deleted legacy Focus authority package was reintroduced: {identity}"
            )


def _assert_deleted_legacy_focus_dao_export(backend_root: Path) -> None:
    _assert_deleted_dao_package_exports(
        backend_root,
        authority="Focus",
        exports=(LEGACY_FOCUS_DAO_EXPORT,),
    )


def _assert_tests_do_not_import_deleted_focus_authorities(
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
            for deleted_identity in LEGACY_FOCUS_DOTTED_IMPORT_IDENTITIES:
                if imported_identity == deleted_identity or imported_identity.startswith(
                    f"{deleted_identity}."
                ):
                    raise DeletedAuthorityViolation(
                        "test imports deleted legacy Focus authority: "
                        f"{relative_path} -> {deleted_identity}"
                    )


def _assert_deleted_legacy_notification_authorities(backend_root: Path) -> None:
    for identity in LEGACY_NOTIFICATION_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Notification authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Notification authority package was reintroduced: "
                f"{identity}"
            )


def _assert_tests_do_not_reference_deleted_notification_authorities(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="Notification",
        deleted_identities=LEGACY_NOTIFICATION_DOTTED_IMPORT_IDENTITIES,
    )


def _assert_tests_do_not_reference_deleted_authorities(
    backend_root: Path,
    *,
    authority: str,
    deleted_identities: tuple[str, ...],
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
        referenced_identities: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                referenced_identities.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                referenced_identities.append(node.module)
                referenced_identities.extend(
                    f"{node.module}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                referenced_identities.append(node.value)

        for referenced_identity in referenced_identities:
            for deleted_identity in deleted_identities:
                if referenced_identity == deleted_identity or referenced_identity.startswith(
                    f"{deleted_identity}."
                ):
                    raise DeletedAuthorityViolation(
                        f"test references deleted legacy {authority} authority: "
                        f"{relative_path} -> {deleted_identity}"
                    )


def _assert_deleted_legacy_published_page_authorities(backend_root: Path) -> None:
    for identity in LEGACY_PUBLISHED_PAGE_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Published Page authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Published Page authority package was reintroduced: "
                f"{identity}"
            )


def _assert_tests_do_not_reference_deleted_published_page_authorities(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="Published Page",
        deleted_identities=LEGACY_PUBLISHED_PAGE_DOTTED_IMPORT_IDENTITIES,
    )


def _assert_deleted_legacy_plaza_authorities(backend_root: Path) -> None:
    for identity in LEGACY_PLAZA_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Plaza authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Plaza authority package was reintroduced: "
                f"{identity}"
            )


def _assert_tests_do_not_reference_deleted_plaza_authorities(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="Plaza",
        deleted_identities=LEGACY_PLAZA_DOTTED_IMPORT_IDENTITIES,
    )


def _assert_deleted_legacy_agent_template_authorities(backend_root: Path) -> None:
    for identity in LEGACY_AGENT_TEMPLATE_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Agent Template authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Agent Template authority package was reintroduced: "
                f"{identity}"
            )


def _assert_deleted_legacy_agent_template_dao_export(backend_root: Path) -> None:
    _assert_deleted_dao_package_exports(
        backend_root,
        authority="Agent Template",
        exports=(LEGACY_AGENT_TEMPLATE_DAO_EXPORT,),
    )


def _assert_tests_do_not_reference_deleted_agent_template_authorities(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="Agent Template",
        deleted_identities=LEGACY_AGENT_TEMPLATE_DOTTED_IMPORT_IDENTITIES,
    )


def _assert_deleted_legacy_agentbay_authorities(backend_root: Path) -> None:
    for identity in LEGACY_AGENTBAY_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy AgentBay authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy AgentBay authority package was reintroduced: "
                f"{identity}"
            )


def _assert_tests_do_not_reference_deleted_agentbay_authorities(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="AgentBay",
        deleted_identities=LEGACY_AGENTBAY_DOTTED_IMPORT_IDENTITIES,
    )


def _assert_deleted_legacy_tenant_knowledge_publication_authority(
    backend_root: Path,
) -> None:
    for identity in LEGACY_TENANT_KNOWLEDGE_PUBLICATION_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Tenant Knowledge publication authority module was "
                f"reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Tenant Knowledge publication authority package was "
                f"reintroduced: {identity}"
            )


def _assert_deleted_legacy_session_substrate_authorities(
    backend_root: Path,
) -> None:
    for identity in LEGACY_SESSION_SUBSTRATE_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Session substrate authority module was "
                f"reintroduced: {identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Session substrate authority package was "
                f"reintroduced: {identity}"
            )


def _assert_deleted_legacy_session_substrate_dao_exports(
    backend_root: Path,
) -> None:
    _assert_deleted_dao_package_exports(
        backend_root,
        authority="Session substrate",
        exports=LEGACY_SESSION_SUBSTRATE_DAO_EXPORTS,
    )


def _assert_mixed_owners_do_not_restore_session_substrate_facts(
    backend_root: Path,
) -> None:
    for relative_path, forbidden_facts in (
        LEGACY_SESSION_SUBSTRATE_FORBIDDEN_FACTS.items()
    ):
        source_path = backend_root / relative_path
        if not source_path.is_file():
            continue
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )
        restored_facts = sorted(forbidden_facts & _source_contract_facts(tree))
        if restored_facts:
            raise DeletedAuthorityViolation(
                "mixed retained owner restores legacy Session substrate facts: "
                f"{relative_path} -> {', '.join(restored_facts)}"
            )


def _assert_deleted_legacy_autonomy_approval_authority(
    backend_root: Path,
) -> None:
    for identity in LEGACY_AUTONOMY_APPROVAL_IMPORT_IDENTITIES:
        module = (backend_root / identity).with_suffix(".py")
        package = backend_root / identity
        if module.is_file():
            raise DeletedAuthorityViolation(
                "deleted legacy Autonomy/Approval authority module was reintroduced: "
                f"{identity}"
            )
        if package.is_dir():
            raise DeletedAuthorityViolation(
                "deleted legacy Autonomy/Approval authority package was reintroduced: "
                f"{identity}"
            )


def _assert_tests_do_not_reference_deleted_autonomy_approval_authority(
    backend_root: Path,
) -> None:
    _assert_tests_do_not_reference_deleted_authorities(
        backend_root,
        authority="Autonomy/Approval",
        deleted_identities=LEGACY_AUTONOMY_APPROVAL_DOTTED_IMPORT_IDENTITIES,
    )


def _assignment_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Attribute):
        return {target.attr}
    if isinstance(target, (ast.Tuple, ast.List)):
        return {
            name
            for element in target.elts
            for name in _assignment_names(element)
        }
    return set()


def _string_value(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _source_contract_facts(tree: ast.Module) -> set[str]:
    facts: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                facts.add(f"import:{alias.asname or alias.name.split('.')[-1]}")
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                facts.add(f"import:{alias.asname or alias.name}")
        elif isinstance(node, ast.ClassDef):
            facts.add(f"class:{node.name}")
            for statement in node.body:
                targets: list[ast.expr] = []
                value: ast.expr | None = None
                if isinstance(statement, ast.Assign):
                    targets.extend(statement.targets)
                    value = statement.value
                elif isinstance(statement, ast.AnnAssign):
                    targets.append(statement.target)
                    value = statement.value
                for target in targets:
                    for name in _assignment_names(target):
                        facts.add(f"class-field:{node.name}:{name}")
                        if name == "__tablename__":
                            table_name = _string_value(value)
                            if table_name:
                                facts.add(f"table:{table_name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            facts.add(f"function:{node.name}")
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not decorator.args:
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue
                if not (
                    isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "router"
                ):
                    continue
                route = _string_value(decorator.args[0])
                if route and decorator.func.attr in {"get", "post"}:
                    facts.add(f"route:{decorator.func.attr.upper()}:{route}")
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                for name in _assignment_names(target):
                    facts.add(f"assigned:{name}")
        elif isinstance(node, ast.AnnAssign):
            for name in _assignment_names(node.target):
                facts.add(f"assigned:{name}")
        elif isinstance(node, ast.Attribute):
            facts.add(f"field:{node.attr}")
            facts.add(f"reference:{node.attr}")
        elif isinstance(node, ast.Name):
            facts.add(f"reference:{node.id}")
        elif isinstance(node, ast.Dict):
            for key in node.keys:
                key_name = _string_value(key)
                if key_name:
                    facts.add(f"key:{key_name}")
        elif isinstance(node, ast.Subscript):
            key_name = _string_value(node.slice)
            if key_name:
                facts.add(f"key:{key_name}")
        elif isinstance(node, ast.Call):
            function_name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else None
            )
            if function_name == "Enum":
                for keyword in node.keywords:
                    if keyword.arg == "name":
                        enum_name = _string_value(keyword.value)
                        if enum_name:
                            facts.add(f"enum:{enum_name}")
    return facts


def _assert_mixed_owners_do_not_restore_autonomy_approval_facts(
    backend_root: Path,
) -> None:
    for relative_path, forbidden_facts in (
        LEGACY_AUTONOMY_APPROVAL_FORBIDDEN_FACTS.items()
    ):
        source_path = backend_root / relative_path
        if not source_path.is_file():
            continue
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )
        restored_facts = sorted(forbidden_facts & _source_contract_facts(tree))
        if restored_facts:
            raise DeletedAuthorityViolation(
                "mixed retained owner restores legacy Autonomy/Approval facts: "
                f"{relative_path} -> {', '.join(restored_facts)}"
            )


def _assert_agent_templates_do_not_restore_autonomy_policy(
    backend_root: Path,
) -> None:
    metadata_root = backend_root / AGENT_TEMPLATE_METADATA_ROOT
    if not metadata_root.is_dir():
        return
    for metadata_path in sorted(metadata_root.rglob("meta.yaml")):
        relative_path = metadata_path.relative_to(backend_root)
        try:
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise DeletedAuthorityViolation(
                f"Agent Template metadata is invalid YAML: {relative_path}"
            ) from exc
        if not isinstance(metadata, dict):
            raise DeletedAuthorityViolation(
                f"Agent Template metadata must be a top-level mapping: {relative_path}"
            )
        if LEGACY_TEMPLATE_AUTONOMY_FIELD in metadata:
            raise DeletedAuthorityViolation(
                "Agent Template restores legacy Autonomy policy field: "
                f"{relative_path}"
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


def test_dao_package_exports_are_static() -> None:
    _assert_dao_package_exports_are_static(BACKEND_ROOT)


@pytest.mark.parametrize(
    "package_source",
    [
        "def __getattr__(name):\n    return object()\n",
        "async def __getattr__(name):\n    return object()\n",
        "__getattr__ = lambda name: object()\n",
        "if True:\n    __getattr__: object = object()\n",
        "from app.hooks import resolve as __getattr__\n",
        'globals()["__getattr__"] = lambda name: object()\n',
        'globals()["__getattr__"], marker = object(), object()\n',
        'globals()["__getattr__"]: object = object()\n',
        'globals().__setitem__("__getattr__", lambda name: object())\n',
        'setattr(module, "__getattr__", lambda name: object())\n',
    ],
    ids=[
        "function-hook",
        "async-function-hook",
        "assigned-hook",
        "annotated-assigned-hook",
        "imported-hook",
        "globals-subscript-hook",
        "globals-unpacked-subscript-hook",
        "globals-annotated-subscript-hook",
        "globals-setitem-hook",
        "setattr-hook",
    ],
)
def test_dynamic_dao_package_export_hook_fails_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="app.dao package exports must be static",
    ):
        _assert_dao_package_exports_are_static(tmp_path)


@pytest.mark.parametrize(
    "package_source",
    [
        'hook_name = "__getattr__"\n',
        "def helper():\n    def __getattr__(name):\n        return object()\n",
        "def helper():\n    __getattr__ = object()\n    return __getattr__\n",
        "def helper(module):\n    return module.__getattr__\n",
        "class Helper:\n    def __getattr__(self, name):\n        return object()\n",
        "helper.__getattr__ = object()\n",
    ],
    ids=[
        "inert-string",
        "nested-function",
        "local-binding",
        "attribute-reference",
        "class-hook",
        "unrelated-attribute-assignment",
    ],
)
def test_non_package_hook_reference_passes_static_dao_export_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    _assert_dao_package_exports_are_static(tmp_path)


def test_legacy_credential_dao_package_export_is_absent_from_target_tree() -> None:
    _assert_deleted_legacy_credential_dao_export(BACKEND_ROOT)


def test_legacy_agent_authorities_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_agent_authorities(BACKEND_ROOT)


def test_legacy_agent_dao_package_exports_are_absent_from_target_tree() -> None:
    _assert_deleted_legacy_agent_dao_exports(BACKEND_ROOT)


def test_legacy_agent_run_event_dao_compatibility_authority_is_absent() -> None:
    _assert_deleted_legacy_agent_run_event_dao_authority(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_agent_run_event_dao() -> None:
    _assert_tests_do_not_reference_deleted_agent_run_event_dao(BACKEND_ROOT)


def test_legacy_okr_agent_hook_authority_is_absent() -> None:
    _assert_deleted_legacy_okr_agent_hook_authority(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_okr_agent_hook() -> None:
    _assert_tests_do_not_reference_deleted_okr_agent_hook(BACKEND_ROOT)


def test_legacy_token_tracker_authority_is_absent() -> None:
    _assert_deleted_legacy_token_tracker_authority(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_token_tracker() -> None:
    _assert_tests_do_not_reference_deleted_token_tracker(BACKEND_ROOT)


def test_legacy_wecom_service_authority_is_absent() -> None:
    _assert_deleted_legacy_wecom_service_authority(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_wecom_service() -> None:
    _assert_tests_do_not_reference_deleted_wecom_service(BACKEND_ROOT)


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
        'globals()["agent_credential_dao"] = object()\n',
    ],
    ids=[
        "direct-import",
        "aliased-import",
        "assignment-reexport",
        "all-exposure",
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
        'globals()["agent_dao"] = object()\n',
    ],
    ids=[
        "direct-import",
        "aliased-import",
        "assignment-reexport",
        "all-exposure",
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
    LEGACY_AGENT_RUN_EVENT_DAO_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_AGENT_RUN_EVENT_DAO_REINTRODUCTIONS
    ],
)
def test_reintroduced_agent_run_event_dao_compatibility_identity_fails_guard(
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
            "deleted legacy Agent Run Event DAO compatibility "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_agent_run_event_dao_authority(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.dao.agent_run_event_dao\n",
        "from app.dao import agent_run_event_dao\n",
        "from app.dao.agent_run_event_dao import agent_run_dao\n",
    ],
    ids=["module-import", "package-import", "symbol-import"],
)
def test_backend_test_static_reference_to_agent_run_event_dao_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_agent_run_event_dao.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Agent Run Event DAO compatibility",
    ):
        _assert_tests_do_not_reference_deleted_agent_run_event_dao(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        'module = importlib.import_module("app.dao.agent_run_event_dao")\n',
        'dao_path = "app.dao.agent_run_event_dao.agent_run_dao"\n',
    ],
    ids=["dynamic-module-import", "dotted-symbol-reference"],
)
def test_backend_test_dynamic_reference_to_agent_run_event_dao_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_agent_run_event_dao_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Agent Run Event DAO compatibility",
    ):
        _assert_tests_do_not_reference_deleted_agent_run_event_dao(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "from app.dao.agent_run_dao import agent_run_dao\n",
        'dao_path = "app.dao.agent_run_dao.agent_run_dao"\n',
    ],
    ids=["run-dao-static-import", "run-dao-dotted-reference"],
)
def test_agent_run_dao_reference_passes_agent_run_event_dao_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_agent_run_dao_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    _assert_tests_do_not_reference_deleted_agent_run_event_dao(tmp_path)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_OKR_AGENT_HOOK_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_OKR_AGENT_HOOK_REINTRODUCTIONS
    ],
)
def test_reintroduced_okr_agent_hook_identity_fails_guard(
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
        match=f"deleted legacy OKR Agent Hook {representation} was reintroduced",
    ):
        _assert_deleted_legacy_okr_agent_hook_authority(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.services.okr_agent_hook\n",
        "from app.services import okr_agent_hook\n",
        "from app.services.okr_agent_hook import hook_new_agent\n",
    ],
    ids=["module-import", "package-import", "symbol-import"],
)
def test_backend_test_static_reference_to_okr_agent_hook_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_okr_agent_hook.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy OKR Agent Hook authority",
    ):
        _assert_tests_do_not_reference_deleted_okr_agent_hook(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        'module = importlib.import_module("app.services.okr_agent_hook")\n',
        'hook_path = "app.services.okr_agent_hook.hook_new_org_member"\n',
    ],
    ids=["dynamic-module-import", "dotted-hook-reference"],
)
def test_backend_test_dynamic_reference_to_okr_agent_hook_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_okr_agent_hook_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy OKR Agent Hook authority",
    ):
        _assert_tests_do_not_reference_deleted_okr_agent_hook(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "from app.services.okr_reporting import generate_company_daily_report\n",
        'service_path = "app.services.okr_daily_collection.trigger_daily_collection_for_tenant"\n',
    ],
    ids=["okr-reporting-static-import", "okr-collection-dotted-reference"],
)
def test_retained_okr_service_reference_passes_okr_agent_hook_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_retained_okr_service_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    _assert_tests_do_not_reference_deleted_okr_agent_hook(tmp_path)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_TOKEN_TRACKER_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_TOKEN_TRACKER_REINTRODUCTIONS
    ],
)
def test_reintroduced_token_tracker_identity_fails_guard(
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
        match=f"deleted legacy Token Tracker {representation} was reintroduced",
    ):
        _assert_deleted_legacy_token_tracker_authority(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.services.token_tracker\n",
        "from app.services import token_tracker\n",
        "from app.services.token_tracker import record_token_usage\n",
    ],
    ids=["module-import", "package-import", "symbol-import"],
)
def test_backend_test_static_reference_to_token_tracker_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_token_tracker.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Token Tracker authority",
    ):
        _assert_tests_do_not_reference_deleted_token_tracker(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        'module = importlib.import_module("app.services.token_tracker")\n',
        'tracker_path = "app.services.token_tracker.TokenUsage"\n',
    ],
    ids=["dynamic-module-import", "dotted-type-reference"],
)
def test_backend_test_dynamic_reference_to_token_tracker_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_token_tracker_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Token Tracker authority",
    ):
        _assert_tests_do_not_reference_deleted_token_tracker(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "from app.models.activity_log import DailyTokenUsage\n",
        'report_path = "app.api.admin.get_platform_timeseries"\n',
    ],
    ids=["daily-usage-static-import", "admin-report-dotted-reference"],
)
def test_retained_token_reporting_reference_passes_token_tracker_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_retained_token_reporting_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    _assert_tests_do_not_reference_deleted_token_tracker(tmp_path)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_WECOM_SERVICE_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_WECOM_SERVICE_REINTRODUCTIONS
    ],
)
def test_reintroduced_wecom_service_identity_fails_guard(
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
        match=f"deleted legacy WeCom service {representation} was reintroduced",
    ):
        _assert_deleted_legacy_wecom_service_authority(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.services.wecom_service\n",
        "from app.services import wecom_service\n",
        "from app.services.wecom_service import send_wecom_message\n",
    ],
    ids=["module-import", "package-import", "symbol-import"],
)
def test_backend_test_static_reference_to_wecom_service_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_wecom_service.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy WeCom service authority",
    ):
        _assert_tests_do_not_reference_deleted_wecom_service(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        'module = importlib.import_module("app.services.wecom_service")\n',
        'sender_path = "app.services.wecom_service.send_wecom_message"\n',
    ],
    ids=["dynamic-module-import", "dotted-sender-reference"],
)
def test_backend_test_dynamic_reference_to_wecom_service_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_wecom_service_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy WeCom service authority",
    ):
        _assert_tests_do_not_reference_deleted_wecom_service(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "from app.api.wecom import wecom_callback\n",
        'stream_path = "app.services.wecom_stream.wecom_stream_manager"\n',
    ],
    ids=["wecom-api-static-import", "wecom-stream-dotted-reference"],
)
def test_active_wecom_reference_passes_deleted_wecom_service_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_active_wecom_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    _assert_tests_do_not_reference_deleted_wecom_service(tmp_path)


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
        'globals()["user_dao"] = object()\n',
    ],
    ids=[
        "direct-import",
        "aliased-import",
        "assignment-reexport",
        "all-exposure",
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
        'globals()["identity_provider_dao"] = object()\n',
    ],
    ids=[
        "direct-import",
        "assignment-reexport",
        "all-exposure",
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


def test_legacy_organization_relationship_import_identities_are_absent() -> None:
    _assert_deleted_legacy_organization_relationship_authorities(BACKEND_ROOT)


def test_legacy_organization_relationship_dao_export_is_absent() -> None:
    _assert_deleted_legacy_organization_relationship_dao_export(BACKEND_ROOT)


def test_backend_tests_do_not_import_deleted_organization_relationship_authorities() -> None:
    _assert_tests_do_not_import_deleted_organization_relationship_authorities(
        BACKEND_ROOT
    )


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_ORGANIZATION_RELATIONSHIP_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in (
            LEGACY_ORGANIZATION_RELATIONSHIP_REINTRODUCTIONS
        )
    ],
)
def test_reintroduced_legacy_organization_relationship_identity_fails_guard(
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
            "deleted legacy Organization/Relationship authority "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_organization_relationship_authorities(tmp_path)


@pytest.mark.parametrize(
    "package_source",
    [
        "from app.dao.org_member_dao import org_member_dao\n",
        "org_member_dao = object()\n",
        '__all__ = ["org_member_dao"]\n',
        'globals()["org_member_dao"] = object()\n',
    ],
    ids=[
        "direct-import",
        "assignment-reexport",
        "all-exposure",
        "globals-restoration",
    ],
)
def test_reintroduced_legacy_organization_relationship_dao_export_fails_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Organization/Relationship DAO package export",
    ):
        _assert_deleted_legacy_organization_relationship_dao_export(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.models.org\n",
        "from app.api import organization\n",
        "from app.api.relationships import router\n",
        "from app.dao import org_member_dao\n",
        "from app.services.org_sync_adapter import BaseOrgSyncAdapter\n",
        "from app.services import org_sync_service\n",
        "from app.services.access_relationships import ensure_access_granted_platform_relationships\n",
    ],
    ids=[
        "model-import",
        "api-package-import",
        "api-symbol-import",
        "dao-package-import",
        "sync-adapter-import",
        "sync-service-package-import",
        "access-relationships-import",
    ],
)
def test_backend_test_import_of_deleted_organization_relationship_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_organization_relationship.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test imports deleted legacy Organization/Relationship authority",
    ):
        _assert_tests_do_not_import_deleted_organization_relationship_authorities(
            tmp_path
        )


def test_legacy_invitation_import_identities_are_absent() -> None:
    _assert_deleted_legacy_invitation_authorities(BACKEND_ROOT)


def test_legacy_invitation_dao_export_is_absent() -> None:
    _assert_deleted_legacy_invitation_dao_export(BACKEND_ROOT)


def test_backend_tests_do_not_import_deleted_invitation_authorities() -> None:
    _assert_tests_do_not_import_deleted_invitation_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_INVITATION_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_INVITATION_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_invitation_identity_fails_guard(
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
            "deleted legacy Invitation authority "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_invitation_authorities(tmp_path)


@pytest.mark.parametrize(
    "package_source",
    [
        "from app.dao.invitation_code_dao import invitation_code_dao\n",
        "invitation_code_dao = object()\n",
        '__all__ = ["invitation_code_dao"]\n',
        'globals()["invitation_code_dao"] = object()\n',
    ],
    ids=[
        "direct-import",
        "assignment-reexport",
        "all-exposure",
        "globals-restoration",
    ],
)
def test_reintroduced_legacy_invitation_dao_export_fails_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Invitation DAO package export",
    ):
        _assert_deleted_legacy_invitation_dao_export(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.models.invitation_code\n",
        "from app.models.invitation_code import InvitationCode\n",
        "from app.dao import invitation_code_dao\n",
        "from app.dao.invitation_code_dao import InvitationCodeDAO\n",
    ],
    ids=[
        "model-import",
        "model-symbol-import",
        "dao-package-import",
        "dao-symbol-import",
    ],
)
def test_backend_test_import_of_deleted_invitation_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_invitation.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test imports deleted legacy Invitation authority",
    ):
        _assert_tests_do_not_import_deleted_invitation_authorities(tmp_path)


def test_legacy_onboarding_import_identities_are_absent() -> None:
    _assert_deleted_legacy_onboarding_authorities(BACKEND_ROOT)


def test_backend_tests_do_not_import_deleted_onboarding_authorities() -> None:
    _assert_tests_do_not_import_deleted_onboarding_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_ONBOARDING_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_ONBOARDING_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_onboarding_identity_fails_guard(
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
            "deleted legacy Onboarding authority "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_onboarding_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.models.onboarding\n",
        "from app.models.onboarding import UserTenantOnboarding\n",
        "from app.api import onboarding\n",
        "from app.api.onboarding import router\n",
        "from app.services import onboarding\n",
        "from app.services.onboarding import resolve_onboarding_prompt\n",
    ],
    ids=[
        "model-import",
        "model-symbol-import",
        "api-package-import",
        "api-symbol-import",
        "service-package-import",
        "service-symbol-import",
    ],
)
def test_backend_test_import_of_deleted_onboarding_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_onboarding.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test imports deleted legacy Onboarding authority",
    ):
        _assert_tests_do_not_import_deleted_onboarding_authorities(tmp_path)


def test_legacy_directory_import_identities_are_absent() -> None:
    _assert_deleted_legacy_directory_authorities(BACKEND_ROOT)


def test_legacy_directory_package_exports_are_absent() -> None:
    _assert_deleted_legacy_directory_package_exports(BACKEND_ROOT)


def test_backend_tests_do_not_import_deleted_directory_authorities() -> None:
    _assert_tests_do_not_import_deleted_directory_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_DIRECTORY_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_DIRECTORY_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_directory_identity_fails_guard(
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
            "deleted legacy Directory authority "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_directory_authorities(tmp_path)


@pytest.mark.parametrize(
    ("relative_path", "package_source"),
    [
        (
            Path("app/api/__init__.py"),
            "from app.api.directory import router\n",
        ),
        (
            Path("app/services/__init__.py"),
            "agent_directory = object()\n",
        ),
        (
            Path("app/api/__init__.py"),
            '__all__ = ["directory"]\n',
        ),
        (
            Path("app/services/__init__.py"),
            "def __getattr__(name):\n    return object()\n",
        ),
    ],
    ids=[
        "api-direct-import",
        "service-assignment-reexport",
        "api-all-exposure",
        "service-module-getattr",
    ],
)
def test_reintroduced_legacy_directory_package_export_fails_guard(
    tmp_path: Path,
    relative_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / relative_path
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Directory package export",
    ):
        _assert_deleted_legacy_directory_package_exports(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.api.directory\n",
        "from app.api import directory\n",
        "from app.api.directory import router\n",
        "import app.services.agent_directory\n",
        "from app.services import agent_directory\n",
        "from app.services.agent_directory import query_agent_directory\n",
    ],
    ids=[
        "api-import",
        "api-package-import",
        "api-symbol-import",
        "service-import",
        "service-package-import",
        "service-symbol-import",
    ],
)
def test_backend_test_import_of_deleted_directory_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_directory.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test imports deleted legacy Directory authority",
    ):
        _assert_tests_do_not_import_deleted_directory_authorities(tmp_path)


def test_legacy_focus_import_identities_are_absent() -> None:
    _assert_deleted_legacy_focus_authorities(BACKEND_ROOT)


def test_legacy_focus_dao_export_is_absent() -> None:
    _assert_deleted_legacy_focus_dao_export(BACKEND_ROOT)


def test_backend_tests_do_not_import_deleted_focus_authorities() -> None:
    _assert_tests_do_not_import_deleted_focus_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_FOCUS_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_FOCUS_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_focus_identity_fails_guard(
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
        match=f"deleted legacy Focus authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_focus_authorities(tmp_path)


@pytest.mark.parametrize(
    "package_source",
    [
        "from app.dao.focus_dao import focus_dao\n",
        "focus_dao = object()\n",
        '__all__ = ["focus_dao"]\n',
    ],
    ids=[
        "direct-import",
        "assignment-reexport",
        "all-exposure",
    ],
)
def test_reintroduced_legacy_focus_dao_export_fails_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Focus DAO package export",
    ):
        _assert_deleted_legacy_focus_dao_export(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.models.focus\n",
        "from app.models import focus\n",
        "from app.models.focus import AgentFocusItem\n",
        "import app.dao.focus_dao\n",
        "from app.dao import focus_dao\n",
        "from app.dao.focus_dao import FocusDAO\n",
        "import app.api.focus\n",
        "from app.api import focus\n",
        "from app.api.focus import router\n",
        "import app.services.focus_service\n",
        "from app.services import focus_service\n",
        "from app.services.focus_service import list_focus_items\n",
    ],
    ids=[
        "model-import",
        "model-package-import",
        "model-symbol-import",
        "dao-import",
        "dao-package-import",
        "dao-symbol-import",
        "api-import",
        "api-package-import",
        "api-symbol-import",
        "service-import",
        "service-package-import",
        "service-symbol-import",
    ],
)
def test_backend_test_import_of_deleted_focus_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_focus.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test imports deleted legacy Focus authority",
    ):
        _assert_tests_do_not_import_deleted_focus_authorities(tmp_path)


def test_legacy_notification_import_identities_are_absent() -> None:
    _assert_deleted_legacy_notification_authorities(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_notification_authorities() -> None:
    _assert_tests_do_not_reference_deleted_notification_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_NOTIFICATION_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_NOTIFICATION_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_notification_identity_fails_guard(
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
        match=f"deleted legacy Notification authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_notification_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.models.notification\n",
        "from app.models import notification\n",
        "from app.models.notification import Notification\n",
        "import app.api.notification\n",
        "from app.api import notification\n",
        "from app.api.notification import router\n",
        "import app.services.notification_service\n",
        "from app.services import notification_service\n",
        "from app.services.notification_service import send_notification\n",
    ],
    ids=[
        "model-import",
        "model-package-import",
        "model-symbol-import",
        "api-import",
        "api-package-import",
        "api-symbol-import",
        "service-import",
        "service-package-import",
        "service-symbol-import",
    ],
)
def test_backend_test_import_of_deleted_notification_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_notification.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Notification authority",
    ):
        _assert_tests_do_not_reference_deleted_notification_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        (
            'monkeypatch.setattr('
            '"app.services.notification_service.send_notification", object())\n'
        ),
        'module = importlib.import_module("app.api.notification")\n',
        'model_path = "app.models.notification.Notification"\n',
    ],
    ids=[
        "monkeypatch-dotted-reference",
        "dynamic-import-reference",
        "model-dotted-reference",
    ],
)
def test_backend_test_dynamic_reference_of_deleted_notification_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_notification_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Notification authority",
    ):
        _assert_tests_do_not_reference_deleted_notification_authorities(tmp_path)


def test_unrelated_dynamic_test_reference_passes_notification_guard(
    tmp_path: Path,
) -> None:
    test_path = tmp_path / "tests/test_system_email_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(
        (
            'monkeypatch.setattr('
            '"app.services.system_email_service.send_system_email", object())\n'
        ),
        encoding="utf-8",
    )

    _assert_tests_do_not_reference_deleted_notification_authorities(tmp_path)


def test_legacy_published_page_import_identities_are_absent() -> None:
    _assert_deleted_legacy_published_page_authorities(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_published_page_authorities() -> None:
    _assert_tests_do_not_reference_deleted_published_page_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_PUBLISHED_PAGE_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_PUBLISHED_PAGE_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_published_page_identity_fails_guard(
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
            "deleted legacy Published Page authority "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_published_page_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.models.published_page\n",
        "from app.models import published_page\n",
        "from app.models.published_page import PublishedPage\n",
        "import app.api.pages\n",
        "from app.api import pages\n",
        "from app.api.pages import router\n",
    ],
    ids=[
        "model-import",
        "model-package-import",
        "model-symbol-import",
        "api-import",
        "api-package-import",
        "api-symbol-import",
    ],
)
def test_backend_test_import_of_deleted_published_page_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_published_page.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Published Page authority",
    ):
        _assert_tests_do_not_reference_deleted_published_page_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        'module = importlib.import_module("app.api.pages")\n',
        'model_path = "app.models.published_page.PublishedPage"\n',
    ],
    ids=["dynamic-api-import-reference", "model-dotted-reference"],
)
def test_backend_test_dynamic_reference_of_deleted_published_page_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_published_page_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Published Page authority",
    ):
        _assert_tests_do_not_reference_deleted_published_page_authorities(tmp_path)


def test_unrelated_dynamic_test_reference_passes_published_page_guard(
    tmp_path: Path,
) -> None:
    test_path = tmp_path / "tests/test_unrelated_page_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(
        'module = importlib.import_module("app.services.text_extractor")\n',
        encoding="utf-8",
    )

    _assert_tests_do_not_reference_deleted_published_page_authorities(tmp_path)


def test_legacy_plaza_import_identities_are_absent() -> None:
    _assert_deleted_legacy_plaza_authorities(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_plaza_authorities() -> None:
    _assert_tests_do_not_reference_deleted_plaza_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_PLAZA_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_PLAZA_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_plaza_identity_fails_guard(
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
        match=f"deleted legacy Plaza authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_plaza_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.models.plaza\n",
        "from app.models import plaza\n",
        "from app.models.plaza import PlazaPost\n",
        "import app.api.plaza\n",
        "from app.api import plaza\n",
        "from app.api.plaza import router\n",
    ],
    ids=[
        "model-import",
        "model-package-import",
        "model-symbol-import",
        "api-import",
        "api-package-import",
        "api-symbol-import",
    ],
)
def test_backend_test_import_of_deleted_plaza_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_plaza.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Plaza authority",
    ):
        _assert_tests_do_not_reference_deleted_plaza_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        'module = importlib.import_module("app.api.plaza")\n',
        'model_path = "app.models.plaza.PlazaPost"\n',
    ],
    ids=["dynamic-api-import-reference", "model-dotted-reference"],
)
def test_backend_test_dynamic_reference_of_deleted_plaza_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_plaza_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Plaza authority",
    ):
        _assert_tests_do_not_reference_deleted_plaza_authorities(tmp_path)


def test_unrelated_dynamic_test_reference_passes_plaza_guard(tmp_path: Path) -> None:
    test_path = tmp_path / "tests/test_unrelated_social_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(
        'module = importlib.import_module("app.services.heartbeat")\n',
        encoding="utf-8",
    )

    _assert_tests_do_not_reference_deleted_plaza_authorities(tmp_path)


def test_legacy_agent_template_import_identities_are_absent() -> None:
    _assert_deleted_legacy_agent_template_authorities(BACKEND_ROOT)


def test_legacy_agent_template_dao_export_is_absent() -> None:
    _assert_deleted_legacy_agent_template_dao_export(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_agent_template_authorities() -> None:
    _assert_tests_do_not_reference_deleted_agent_template_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_AGENT_TEMPLATE_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_AGENT_TEMPLATE_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_agent_template_identity_fails_guard(
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
        match=f"deleted legacy Agent Template authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_agent_template_authorities(tmp_path)


@pytest.mark.parametrize(
    "package_source",
    [
        "from app.dao.agent_template_dao import agent_template_dao\n",
        "agent_template_dao = object()\n",
        '__all__ = ["agent_template_dao"]\n',
    ],
    ids=[
        "direct-import",
        "assignment-reexport",
        "all-exposure",
    ],
)
def test_reintroduced_legacy_agent_template_dao_export_fails_guard(
    tmp_path: Path,
    package_source: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(package_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Agent Template DAO package export",
    ):
        _assert_deleted_legacy_agent_template_dao_export(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.dao.agent_template_dao\n",
        "from app.dao import agent_template_dao\n",
        "from app.dao.agent_template_dao import AgentTemplateDAO\n",
        "import app.services.template_seeder\n",
        "from app.services import template_seeder\n",
        "from app.services.template_seeder import seed_agent_templates\n",
    ],
    ids=[
        "dao-import",
        "dao-package-import",
        "dao-symbol-import",
        "service-import",
        "service-package-import",
        "service-symbol-import",
    ],
)
def test_backend_test_import_of_deleted_agent_template_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_agent_template.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Agent Template authority",
    ):
        _assert_tests_do_not_reference_deleted_agent_template_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        'module = importlib.import_module("app.services.template_seeder")\n',
        'dao_path = "app.dao.agent_template_dao.AgentTemplateDAO"\n',
    ],
    ids=["dynamic-service-import-reference", "dao-dotted-reference"],
)
def test_backend_test_dynamic_reference_of_deleted_agent_template_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_agent_template_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Agent Template authority",
    ):
        _assert_tests_do_not_reference_deleted_agent_template_authorities(tmp_path)


def test_unrelated_dynamic_test_reference_passes_agent_template_guard(
    tmp_path: Path,
) -> None:
    test_path = tmp_path / "tests/test_unrelated_template_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(
        'module = importlib.import_module("app.services.text_extractor")\n',
        encoding="utf-8",
    )

    _assert_tests_do_not_reference_deleted_agent_template_authorities(tmp_path)


def test_legacy_agentbay_import_identities_are_absent() -> None:
    _assert_deleted_legacy_agentbay_authorities(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_agentbay_authorities() -> None:
    _assert_tests_do_not_reference_deleted_agentbay_authorities(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_AGENTBAY_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_AGENTBAY_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_agentbay_identity_fails_guard(
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
        match=f"deleted legacy AgentBay authority {representation} was reintroduced",
    ):
        _assert_deleted_legacy_agentbay_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.api.agentbay_control\n",
        "from app.api.agentbay_control import control_lock\n",
        "import app.services.agentbay_client\n",
        "from app.services.agentbay_client import AgentBayClient\n",
        "import app.services.agentbay_live\n",
        "from app.services.agentbay_live import detect_agentbay_env\n",
    ],
    ids=[
        "control-import",
        "control-symbol-import",
        "client-import",
        "client-symbol-import",
        "live-import",
        "live-symbol-import",
    ],
)
def test_backend_test_import_of_deleted_agentbay_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_agentbay.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy AgentBay authority",
    ):
        _assert_tests_do_not_reference_deleted_agentbay_authorities(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        'module = importlib.import_module("app.api.agentbay_control")\n',
        'client_path = "app.services.agentbay_client.AgentBayClient"\n',
        'monkeypatch.setattr("app.services.agentbay_live.detect_agentbay_env", fake)\n',
    ],
    ids=[
        "dynamic-control-import-reference",
        "client-dotted-reference",
        "live-monkeypatch-reference",
    ],
)
def test_backend_test_dynamic_reference_of_deleted_agentbay_authority_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_agentbay_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy AgentBay authority",
    ):
        _assert_tests_do_not_reference_deleted_agentbay_authorities(tmp_path)


def test_unrelated_dynamic_test_reference_passes_agentbay_guard(tmp_path: Path) -> None:
    test_path = tmp_path / "tests/test_unrelated_agentbay_reference.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(
        'module = importlib.import_module("app.services.vision_inject")\n',
        encoding="utf-8",
    )

    _assert_tests_do_not_reference_deleted_agentbay_authorities(tmp_path)


def test_legacy_tenant_knowledge_publication_import_identity_is_absent() -> None:
    _assert_deleted_legacy_tenant_knowledge_publication_authority(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_TENANT_KNOWLEDGE_PUBLICATION_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in (
            LEGACY_TENANT_KNOWLEDGE_PUBLICATION_REINTRODUCTIONS
        )
    ],
)
def test_reintroduced_legacy_tenant_knowledge_publication_identity_fails_guard(
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
            "deleted legacy Tenant Knowledge publication authority "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_tenant_knowledge_publication_authority(tmp_path)


def test_legacy_session_substrate_authorities_are_absent() -> None:
    _assert_deleted_legacy_session_substrate_authorities(BACKEND_ROOT)


def test_legacy_session_substrate_dao_exports_are_absent() -> None:
    _assert_deleted_legacy_session_substrate_dao_exports(BACKEND_ROOT)


def test_mixed_owners_do_not_restore_session_substrate_facts() -> None:
    _assert_mixed_owners_do_not_restore_session_substrate_facts(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_SESSION_SUBSTRATE_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_SESSION_SUBSTRATE_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_session_substrate_identity_fails_guard(
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
            "deleted legacy Session substrate authority "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_session_substrate_authorities(tmp_path)


@pytest.mark.parametrize("export", LEGACY_SESSION_SUBSTRATE_DAO_EXPORTS)
def test_reintroduced_legacy_session_substrate_dao_export_fails_guard(
    tmp_path: Path,
    export: str,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(f"__all__ = [{export!r}]\n", encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="deleted legacy Session substrate DAO package export was reintroduced",
    ):
        _assert_deleted_legacy_session_substrate_dao_exports(tmp_path)


def test_dynamic_session_substrate_dao_export_hook_fails_guard(
    tmp_path: Path,
) -> None:
    package_init = tmp_path / DAO_PACKAGE_INIT
    package_init.parent.mkdir(parents=True)
    package_init.write_text(
        "def __getattr__(name):\n    return object()\n",
        encoding="utf-8",
    )

    with pytest.raises(
        DeletedAuthorityViolation,
        match="app.dao package exports must be static",
    ):
        _assert_dao_package_exports_are_static(tmp_path)


@pytest.mark.parametrize(
    ("relative_path", "source"),
    [
        (Path("app/models/audit.py"), "class ChatMessage: ...\n"),
        (
            Path("app/models/audit.py"),
            'class Legacy:\n    __tablename__ = "chat_messages"\n',
        ),
        (
            Path("app/models/audit.py"),
            'role = Enum("user", name="chat_role_enum")\n',
        ),
        (Path("app/schemas/schemas.py"), "class ChatMessageOut: ...\n"),
        (Path("app/schemas/schemas.py"), "class ChatSend: ...\n"),
    ],
    ids=[
        "chat-message-model",
        "chat-messages-table",
        "chat-role-enum",
        "chat-message-out-schema",
        "chat-send-schema",
    ],
)
def test_restored_session_substrate_fact_fails_guard(
    tmp_path: Path,
    relative_path: Path,
    source: str,
) -> None:
    source_path = tmp_path / relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="mixed retained owner restores legacy Session substrate facts",
    ):
        _assert_mixed_owners_do_not_restore_session_substrate_facts(tmp_path)


def test_unrelated_audit_and_schema_facts_pass_session_substrate_guard(
    tmp_path: Path,
) -> None:
    safe_sources = {
        Path("app/models/audit.py"): "class AuditLog: ...\nclass EnterpriseInfo: ...\n",
        Path("app/schemas/schemas.py"): "class AuditLogOut: ...\n",
    }
    for relative_path, source in safe_sources.items():
        source_path = tmp_path / relative_path
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source, encoding="utf-8")

    _assert_mixed_owners_do_not_restore_session_substrate_facts(tmp_path)


def test_legacy_autonomy_approval_authority_is_absent() -> None:
    _assert_deleted_legacy_autonomy_approval_authority(BACKEND_ROOT)


def test_backend_tests_do_not_reference_deleted_autonomy_approval_authority() -> None:
    _assert_tests_do_not_reference_deleted_autonomy_approval_authority(BACKEND_ROOT)


def test_mixed_owners_do_not_restore_autonomy_approval_symbols() -> None:
    _assert_mixed_owners_do_not_restore_autonomy_approval_facts(BACKEND_ROOT)


def test_agent_templates_do_not_restore_autonomy_policy() -> None:
    _assert_agent_templates_do_not_restore_autonomy_policy(BACKEND_ROOT)


@pytest.mark.parametrize(
    ("identity", "representation"),
    LEGACY_AUTONOMY_APPROVAL_REINTRODUCTIONS,
    ids=[
        f"{identity.as_posix()}-{representation}"
        for identity, representation in LEGACY_AUTONOMY_APPROVAL_REINTRODUCTIONS
    ],
)
def test_reintroduced_legacy_autonomy_approval_identity_fails_guard(
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
            "deleted legacy Autonomy/Approval authority "
            f"{representation} was reintroduced"
        ),
    ):
        _assert_deleted_legacy_autonomy_approval_authority(tmp_path)


@pytest.mark.parametrize(
    "test_source",
    [
        "import app.services.autonomy_service\n",
        "from app.services import autonomy_service\n",
        "from app.services.autonomy_service import AutonomyService\n",
        'module = importlib.import_module("app.services.autonomy_service")\n',
        (
            'monkeypatch.setattr("app.services.autonomy_service.autonomy_service", '
            "object())\n"
        ),
    ],
    ids=[
        "service-import",
        "service-package-import",
        "service-symbol-import",
        "dynamic-service-import",
        "monkeypatch-dotted-reference",
    ],
)
def test_backend_test_reference_of_deleted_autonomy_approval_fails_guard(
    tmp_path: Path,
    test_source: str,
) -> None:
    test_path = tmp_path / "tests/test_restored_autonomy_approval.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="test references deleted legacy Autonomy/Approval authority",
    ):
        _assert_tests_do_not_reference_deleted_autonomy_approval_authority(tmp_path)


def test_unrelated_feishu_approval_reference_passes_autonomy_guard(
    tmp_path: Path,
) -> None:
    test_path = tmp_path / "tests/test_feishu_approval_transport.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(
        "from app.services.feishu_service import feishu_service\n",
        encoding="utf-8",
    )

    _assert_tests_do_not_reference_deleted_autonomy_approval_authority(tmp_path)


@pytest.mark.parametrize(
    ("relative_path", "test_source"),
    [
        (Path("app/models/audit.py"), "class ApprovalRequest: ...\n"),
        (
            Path("app/models/audit.py"),
            'class Legacy:\n    __tablename__ = "approval_requests"\n',
        ),
        (
            Path("app/models/audit.py"),
            'status = Enum("pending", name="approval_status_enum")\n',
        ),
        (
            Path("app/api/enterprise.py"),
            (
                '@router.get("/approvals", response_model=ApprovalRequestOut)\n'
                "async def list_approvals(): ...\n"
            ),
        ),
        (
            Path("app/api/enterprise.py"),
            (
                '@router.post("/approvals/{approval_id}/resolve")\n'
                "async def resolve_approval(): ...\n"
            ),
        ),
        (
            Path("app/api/advanced.py"),
            "class TemplateCreate:\n    default_autonomy_policy: dict = {}\n",
        ),
        (
            Path("app/api/advanced.py"),
            'payload = {"total_approvals": 1, "pending_approvals": 1}\n',
        ),
        (
            Path("app/dao/agent_metrics_dao.py"),
            "from app.models.audit import ApprovalRequest\n",
        ),
        (
            Path("app/dao/agent_metrics_dao.py"),
            "total_approvals, pending_approvals = (1, 1)\n",
        ),
        (Path("app/schemas/schemas.py"), "class ApprovalRequestOut: ...\n"),
        (Path("app/schemas/schemas.py"), "class ApprovalAction: ...\n"),
        (
            Path("app/schemas/schemas.py"),
            "class AgentCreate:\n    autonomy_policy: dict | None = None\n",
        ),
        (
            Path("app/services/feishu_service.py"),
            "class FeishuService:\n    async def send_approval_card(self): ...\n",
        ),
    ],
    ids=[
        "model-class",
        "model-table",
        "model-enum",
        "enterprise-list-route-response",
        "enterprise-resolve-route",
        "advanced-template-field",
        "advanced-metric-keys",
        "metrics-model-import",
        "metrics-assignments",
        "approval-response-schema",
        "approval-action-schema",
        "agent-autonomy-field",
        "feishu-runtime-card-method",
    ],
)
def test_restored_mixed_owner_autonomy_approval_fact_fails_guard(
    tmp_path: Path,
    relative_path: Path,
    test_source: str,
) -> None:
    source_path = tmp_path / relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(test_source, encoding="utf-8")

    with pytest.raises(
        DeletedAuthorityViolation,
        match="mixed retained owner restores legacy Autonomy/Approval facts",
    ):
        _assert_mixed_owners_do_not_restore_autonomy_approval_facts(tmp_path)


def test_unrelated_mixed_owner_symbols_pass_autonomy_approval_guard(
    tmp_path: Path,
) -> None:
    safe_sources = {
        Path("app/models/audit.py"): (
            'class AuditLog: ...\nnote = "ApprovalRequest is retired"\n'
        ),
        Path("app/api/enterprise.py"): (
            'approvals = []\ntext = "/approvals is unavailable"\n'
        ),
        Path("app/api/advanced.py"): (
            'approvals = []\npayload = {"approvals": "unavailable"}\n'
        ),
        Path("app/dao/agent_metrics_dao.py"): 'result = {"recent_actions": 0}\n',
        Path("app/schemas/schemas.py"): "class AuditLogOut: ...\n",
        Path("app/services/feishu_service.py"): (
            "class FeishuService:\n"
            "    async def create_approval_instance(self): ...\n"
            "    async def query_approval_instances(self): ...\n"
            "    async def get_approval_instance(self): ...\n"
        ),
    }
    for relative_path, source in safe_sources.items():
        source_path = tmp_path / relative_path
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source, encoding="utf-8")

    _assert_mixed_owners_do_not_restore_autonomy_approval_facts(tmp_path)


def test_native_feishu_approval_instance_methods_pass_autonomy_guard(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "app/services/feishu_service.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        (
            "class FeishuService:\n"
            "    async def create_approval_instance(self): ...\n"
            "    async def query_approval_instances(self): ...\n"
            "    async def get_approval_instance(self): ...\n"
        ),
        encoding="utf-8",
    )

    _assert_mixed_owners_do_not_restore_autonomy_approval_facts(tmp_path)


@pytest.mark.parametrize(
    "policy_key",
    [
        "default_autonomy_policy",
        "'default_autonomy_policy'",
        '"default_autonomy_policy"',
    ],
    ids=["plain-key", "single-quoted-key", "double-quoted-key"],
)
def test_restored_agent_template_autonomy_policy_fails_guard(
    tmp_path: Path,
    policy_key: str,
) -> None:
    metadata_path = tmp_path / "agent_templates/restored/meta.yaml"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(
        f'name: restored\n{policy_key}:\n  read_files: "L1"\n',
        encoding="utf-8",
    )

    with pytest.raises(
        DeletedAuthorityViolation,
        match="Agent Template restores legacy Autonomy policy field",
    ):
        _assert_agent_templates_do_not_restore_autonomy_policy(tmp_path)


def test_agent_template_without_autonomy_policy_passes_guard(
    tmp_path: Path,
) -> None:
    metadata_path = tmp_path / "agent_templates/safe/meta.yaml"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(
        (
            "name: safe\n"
            "description: default_autonomy_policy is retired\n"
            "default_skills: []\n"
        ),
        encoding="utf-8",
    )

    _assert_agent_templates_do_not_restore_autonomy_policy(tmp_path)


@pytest.mark.parametrize(
    ("metadata_source", "expected_error"),
    [
        ("name: [unterminated\n", "Agent Template metadata is invalid YAML"),
        ("- name: list-entry\n", "Agent Template metadata must be a top-level mapping"),
    ],
    ids=["invalid-yaml", "non-mapping-yaml"],
)
def test_invalid_agent_template_metadata_fails_closed(
    tmp_path: Path,
    metadata_source: str,
    expected_error: str,
) -> None:
    metadata_path = tmp_path / "agent_templates/invalid/meta.yaml"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(metadata_source, encoding="utf-8")

    with pytest.raises(DeletedAuthorityViolation, match=expected_error):
        _assert_agent_templates_do_not_restore_autonomy_policy(tmp_path)
