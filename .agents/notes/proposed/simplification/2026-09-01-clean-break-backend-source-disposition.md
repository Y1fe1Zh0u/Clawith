# Agent Note: Clean-Break Backend Source Disposition

Status: proposed — the capability disposition is agreed; target application composition and database infrastructure are implemented, and the legacy Agent execution, old Context, structured Experience, old Model/LLM, Persistent Task, old Tool, old Skill, dedicated OpenClaw/Gateway, old Agent Credential, overloaded old Agent aggregate, old Identity/Tenant aggregate, old Auth, old SSO, overloaded old Organization/Relationship, legacy Invitation, and legacy Tenant Knowledge publication authorities are removed, while owner rewrites and the remaining category deletions remain incomplete

## Problem

The current Backend contains the product capabilities that the target must account for, but its implementation joins Agent identity, LangGraph execution, checkpoints, Commands, Tool execution ledgers, product reconciliation, relationship labels and access metadata, quotas, approvals, compatibility paths, and channel delivery across the same models and services. The `backend/app/services/agent_runtime/` package alone contains about sixty Python files and thirty-four thousand lines. Incrementally reshaping those authorities would preserve the exact lifecycle and compatibility structures the target architecture removes.

The rewrite must not lose supported product capabilities merely because their current owner is wrong. It also must not retain an obsolete model, route, test, dependency, migration, or adapter merely because some useful behavior currently passes through it. This Note classifies current source by capability and disposition; the target architecture Notes remain the authority for replacement behavior.

## Proposal

### Classification

Each current source area receives one disposition:

- `delete`: the capability or compatibility behavior is absent from the accepted target and is not ported.
- `rewrite`: the product capability remains, but its current authority, persistence, API, or lifecycle is replaced.
- `reuse`: a bounded provider, transport, conversion, storage, or pure helper implementation may move behind a new owner after its imports and behavior are verified.
- `defer`: the product capability remains in scope for the complete Backend rewrite but does not block the foundational Agent Runtime slice. It receives its own contract and rewrite before the old Backend is removed.

No current ORM model, API response, internal service contract, migration, or test is automatically compatible with the target. Reuse is code-level implementation reuse, never authority reuse.

### Current target cutover state

The target branch no longer contains the legacy Agent execution authority. The removed source manifest is:

- `backend/app/services/agent_runtime/**`
- `backend/app/models/agent_run.py`
- `backend/app/models/agent_run_command.py`
- `backend/app/models/agent_run_event.py`
- `backend/app/models/agent_tool_execution.py`
- `backend/app/models/session_context_state.py`
- `backend/app/scripts/setup_langgraph_checkpoints.py`
- `backend/tests/test_agent_runtime_*.py`
- `backend/tests/test_setup_langgraph_checkpoints.py`
- the dedicated old-authority tests `test_runtime_schema.py`, `test_session_context_service.py`, `test_tool_exchange.py`, `test_tool_execution.py`, `test_model_capabilities.py`, `test_runtime_model_settings_resolution.py`, `test_chat_session_runtime_state.py`, `test_unified_runtime_group_migration.py`, and `test_websocket_runtime_chat.py`

`backend/app/runtime/` remains the target Runner/Loop implementation boundary. Product APIs, services, models, migrations, and tests that still import the removed authority remain only as staged deletion evidence for their own later owner or deletion-category commits; they do not restore or replace the removed authority. The separate deletion categories below, including Approval, quota, relationship, Schedule, startup repair, storage compatibility, the monolithic Tool facade, product adapters, migrations, and dependencies, remain pending.

The target branch also no longer contains the old Context authority:

- `backend/app/services/agent_context.py`
- `backend/tests/test_agent_context.py`

The structured Experience authority is also removed:

- `backend/app/api/experience.py`
- `backend/app/models/experience.py`
- `backend/app/models/experience_reference.py`
- `backend/app/services/experience_retrieval.py`
- the dedicated Experience API, citation/RAG, and revision-migration tests

The old Model and LLM execution authority is removed as a separate category:

- `backend/app/models/llm.py`
- the entire `backend/app/services/llm/` package, including Model resolution,
  fallback, the monolithic caller, finish protocol, single-step execution,
  Provider clients, and multimodal request assembly
- the dedicated Model persistence and tenant-scope, runtime Model settings,
  resolution, fallback, finish, single-step, Provider request-shape, capability
  probe, and multimodal tests

The Persistent Task authority is also removed as a separate category:

- `backend/app/models/task.py`
- `backend/app/api/tasks.py`
- `backend/app/services/task_executor.py`
- the dedicated Task CRUD/intake and execution tests

This removal does not remove or implement the target Task Tool. In the accepted target, delegated work is represented by the parent Tool Call, Child Run Input, and Child Run outcome rather than a separate Task or TaskLog lifecycle object.

The old Tool authority is also removed as a separate category:

- `backend/app/models/tool.py`
- `backend/app/api/tools.py`
- `backend/app/services/agent_tools.py`
- `backend/app/services/builtin_tool_definitions.py`
- `backend/app/services/tool_config.py`
- the already-absent `backend/app/services/tool_exchange.py` import identity
- `backend/app/services/tool_seeder.py`
- every `backend/tests/test_agent_tools_*.py` file present at cutover: `agentbay_a0`, `deadlines`, `deploy_contracts`, `email_contracts`, `feishu_f0_contracts`, `legacy_contract_compatibility`, `okr_contracts`, `remaining_typed_outcomes`, `storage_workspace`, `tool_config_logging`, `typed_agentbay_reads`, `typed_bitable`, `typed_content_outcomes`, `typed_deploy_reads`, `typed_deploy_simple_writes`, `typed_dynamic_mcp`, `typed_e2b_outcome`, `typed_email_read`, `typed_email_write`, `typed_feishu_approval`, `typed_feishu_calendar`, `typed_feishu_doc_drive`, `typed_feishu_remaining`, `typed_feishu_wiki`, `typed_image_outcomes_v2`, `typed_okr_jobs`, `typed_okr_transactions`, `typed_search_outcomes`, and `typed_vercel_deploy`
- the dedicated old Tool contract files `test_builtin_tool_contracts.py`, `test_custom_image_tool.py`, `test_deploy_tools.py`, `test_human_send_tools.py`, `test_query_directory_tool.py`, `test_roster_human_resolver.py`, `test_tool_tenant_scope.py`, and `test_tools_category_config.py`
- the mixed legacy files `test_feishu_channel_runtime.py`, `test_mcp_oauth_authorization.py`, `test_sandbox_execution_policy.py`, `test_trigger_config_updates.py`, and `test_workspace_reconciliation.py`
- `test_smithery_recovery_does_not_store_auth_required_connection` from `test_mcp_recovery.py`

These deleted tests instantiated `Tool`/`AgentTool`, called the old Tool management API, asserted the monolithic builtin definition and seeding catalogs, or executed and patched the `agent_tools` exposure/dispatch/configuration facade. The user explicitly approved deleting all legacy `agent_tools`-era tests, including mixed files and assertions that directly exercised retained MCP, Feishu, Sandbox, AgentBay, Trigger, or Workspace helpers through the old authority. No old test is extracted, moved, or adapted during this deletion. Each retained owner must receive new target-contract tests when it is implemented. The independent MCP transport error test remains in `test_mcp_recovery.py` because it imports and exercises only `MCPClient`.

This removal does not implement the target `modules/tool` owner or Capability Market. `mcp_client.py`, MCP OAuth helpers, `resource_discovery.py`, provider- and Channel-specific adapters, Atlassian-specific services, collaboration/A2A sources, migrations, and dependency declarations remain staged candidates. Their surviving imports of the deleted identities are intentional dangling evidence for later minimum owner or deletion-category commits, not compatibility authority. `tool_exchange.py` had already left the target tree with the old Agent Runtime cutover and is not recreated.

The old Skill authority is also removed as a separate category:

- `backend/app/models/skill.py`
- `backend/app/api/skills.py`
- `backend/app/services/skill_seeder.py`
- `backend/app/services/skill_creator_content.py`
- the complete generated and evaluation asset directory `backend/app/services/skill_creator_files/`
- `backend/tests/test_skill_seeder_sync.py`
- `backend/tests/test_skills_api.py`

The deleted tests asserted the old global/tenant Skill ORM, CRUD and direct file mutation API, default-Skill database seeding and repair, and import compatibility. They are not moved or adapted during deletion. The future Workspace and Capability Market owners must write fresh tests from their approved target contracts, including controlled Market/Admin installation and Workspace Skill package behavior.

This removal does not implement Capability Market or remove independently owned capability/resource discovery, MCP transport, Workspace/file/storage behavior, target Tool modules, provider/Channel adapters, templates, migrations, or dependencies. The mixed `files.py` Skill routes, Agent bootstrap repair path, model import lists, and database bootstrap imports remain staged dangling consumers for their own minimum owner/category deletions; none authorizes recreating the old Skill identities. Agent-authored creation, evaluation assets, direct database-backed file mutation, and the old Skill import/install facade are gone.

The dedicated OpenClaw/Gateway authority is also removed as a separate category:

- `backend/app/api/gateway.py`
- `backend/app/models/gateway_message.py`
- `backend/app/services/agent_manager.py`
- `backend/tests/test_gateway_runtime_a2a.py`
- `backend/tests/test_agent_manager_soul.py`

The Gateway API, queued remote-message model, API-key polling/report/heartbeat/send-message protocol, OpenClaw container lifecycle, and the combined legacy Agent file-initialization manager no longer exist as importable target authorities. The two deleted tests asserted the retired Gateway protocol and behavior embedded in that combined manager; they are not moved or adapted during deletion. The target Agent, Workspace, Session, A2A, and Channel owners must write fresh tests from their approved contracts.

This minimum deletion deliberately leaves mixed residual branches for their own owner/category commits: OpenClaw fields and API-key/container routes in `models/agent.py` and `api/agents.py`; Gateway queueing in `api/websocket.py`; legacy Gateway schemas in `schemas/schemas.py`; file initialization calls in `api/onboarding.py` and `services/agent_seeder.py`; container status in `api/advanced.py`; Gateway model imports in bootstrap and cleanup/backfill scripts; and mixed storage/API tests that still import `app.services.agent_manager`. Those dangling consumers do not authorize restoring `app.api.gateway`, `app.models.gateway_message`, or `app.services.agent_manager`. Discord's independently owned connection mode and generic Sandbox publication-owner terminology are not classified as OpenClaw authority by this removal.

The old Agent Credential authority is also removed as a separate category:

- `backend/app/models/agent_credential.py`
- `backend/app/dao/agent_credential_dao.py`
- `backend/app/api/agent_credentials.py`
- `backend/app/schemas/agent_credential.py`
- the `agent_credential_dao` compatibility export from `backend/app/dao/__init__.py`

These modules owned the Agent-scoped cookie record, direct DAO, CRUD transport, encryption-on-write behavior, and legacy request/response shapes. They are deleted rather than migrated. No dedicated legacy Credential tests remain in the target tree, and no legacy test is extracted or adapted during this deletion. The target Credential owner must write fresh model, persistence, authorization, Secret-handling, and transport tests from its approved contract.

This minimum deletion deliberately preserves mixed consumers for their own owner/category commits: AgentBay control and cookie injection still import the removed model; Tenant cleanup still names the old table; legacy Alembic revisions still create and alter the table until the target baseline replaces the full chain; and independently owned Channel configuration, identity-provider, Agent, Tool/MCP, Atlassian, and Provider Secret paths remain untouched. Those residuals do not authorize recreating `app.api.agent_credentials`, `app.dao.agent_credential_dao`, `app.models.agent_credential`, or `app.schemas.agent_credential`.

The overloaded old Agent aggregate authority is also removed as a separate category:

- `backend/app/models/agent.py`
- `backend/app/api/agents.py`
- `backend/app/dao/agent_dao.py`
- `backend/app/dao/agent_access_dao.py`
- `backend/app/services/agent_seeder.py`
- the `agent_dao` and `agent_access_dao` compatibility exports from `backend/app/dao/__init__.py`
- `backend/tests/test_agent_delete_api.py`
- `backend/tests/test_agent_permission_candidates.py`
- `backend/tests/test_agent_seeder_storage_repair.py`
- `backend/tests/test_agent_visibility.py`

These sources combined Agent identity and CRUD with creator ownership, access modes, visibility and management grants, permission candidates, soft deletion, execution/container status, start/stop and API-key operations, OpenClaw fields, runtime and quota counters, template bootstrap, default-Agent seeding and storage repair, and relationships to Runtime, Task, Channel, Model, and User state. The deleted tests asserted only those retired aggregate contracts. They are not moved or adapted; the target Agent and Permission owners must write fresh contract tests when implemented.

`AgentPermission`, `AgentTemplate`, and `AgentUserOnboarding` were physically declared in the removed `models/agent.py`, but they are not accepted as facts owned by the target Agent aggregate. Permission grants, Agent Template, and Onboarding must be reimplemented by their separate target owners only after those owner contracts are reviewed and approved, with new persistence and service tests. The retained `agent_template_dao.py`, `advanced.py`, Directory, Metrics, Focus, Onboarding, Identity, Organization, Workspace, storage `agent_files`, mixed `schemas.py`, migrations, dependency declarations, Frontend, and target module packages remain staged for their own minimum commits. Their dangling imports and relationships are evidence of incomplete source disposition, not authorization to recreate the removed aggregate or add a compatibility shim.

The old Identity/Tenant aggregate authority is also removed as a separate category:

- `backend/app/models/user.py`
- `backend/app/models/tenant.py`
- `backend/app/models/tenant_setting.py`
- `backend/app/api/users.py`
- `backend/app/api/tenants.py`
- `backend/app/dao/identity_dao.py`
- `backend/app/dao/user_dao.py`
- `backend/app/dao/tenant_dao.py`
- the `identity_dao`, `user_dao`, and `tenant_dao` compatibility exports from `backend/app/dao/__init__.py`
- the old Tenant model/API validation assertions removed from the mixed `backend/tests/test_timezone_validation.py`

These sources combined a global login Identity, tenant-scoped User membership, Tenant configuration and sparse Tenant settings with CRUD, tenant switching and assignment, self-create and join, quota counters and limits, logo storage, registration configuration, SSO-domain lookup, Tenant deletion, and compatibility association proxies. The removed tests asserted only retired Tenant persistence or API schemas. They are not adapted; the target `identity_tenant` owner must write fresh Account, Membership, Tenant, Tenant Principal, and Platform Principal tests from its approved contract.

The Identity/Tenant deletion deliberately preserved the then-staged Auth routes and services together with SSO and identity-provider models and services, Organization, Invitation, Onboarding, Permission core, AgentBay, Channel, Enterprise and Platform Administration, mixed `schemas.py`, migrations, dependency declarations, Frontend, and target module packages. The old Auth authority is removed in the following category; the other retained consumers still import deleted model or DAO identities and remain staged for their own owner/category commits. Their dangling imports are evidence of incomplete source disposition, not authorization to recreate an old aggregate, package export, or compatibility shim.

The old Auth authority is also removed as a separate category:

- `backend/app/api/auth.py`
- `backend/app/services/auth_provider.py`
- `backend/app/services/auth_registry.py`
- `backend/app/services/registration_service.py`
- `backend/app/services/password_reset_service.py`
- `backend/app/services/email_verification_service.py`
- `backend/tests/test_auth.py`
- the old Auth Provider assertions removed from `backend/tests/test_auth_provider.py`
- the password reset and Auth API assertions removed from `backend/tests/test_password_reset_and_notifications.py`

These sources combined password login and registration, Account binding, tenant switching, JWT issuance, password change and reset, email verification, SSO callback/session orchestration, Provider construction, and cross-owner Identity/Tenant, Organization, Invitation, Onboarding, and notification mutations. Their tests asserted that retired orchestration and are deleted rather than adapted. The target Auth owner must receive fresh password, login, token, bind, reset, and verification tests after its approved contract is implemented.

Generic system-email transport tests remained after the Auth deletion and now live independently in `backend/tests/test_system_email.py`; the later Notification deletion removed only broadcast-notification assertions. The Auth deletion preserved the then-independent SSO and IdentityProvider authority so it could be removed in its own minimum commit. `core/security.py` remains because retained API, WebSocket, encryption, Sandbox, and provider boundaries still consume its bearer, JWT, authorization-dependency, and data-encryption helpers; it is not solely the old Auth or SSO authority.

Retained Google Workspace Organization sync, Feishu, WeCom, DingTalk, Organization, relationship, Plaza, Trigger, OKR, and cleanup-script sources still import one or more deleted Auth identities. They remain staged for their own owner/category commits. Those dangling imports do not authorize recreating the old Auth API, Provider registry, registration orchestrator, password-reset lifecycle, email-verification lifecycle, or package exports.

The old SSO authority and its mixed identity-provider entry surfaces are also removed as a separate category:

- `backend/app/api/sso.py`
- `backend/app/api/google_workspace.py`
- `backend/app/models/identity.py`
- `backend/app/dao/identity_provider_dao.py`
- `backend/app/services/sso_service.py`
- `backend/app/services/sso_session_security.py`
- `backend/app/services/identity_provider_lookup.py`
- `backend/app/services/google_workspace_oauth.py`
- the `identity_provider_dao` compatibility export from `backend/app/dao/__init__.py`
- `backend/tests/test_identity_provider_and_google_workspace_oauth.py`
- `backend/tests/test_sso_session_browser_binding.py`
- `backend/tests/test_identity_id_mapping.py`
- `backend/tests/test_sso_toggle.py`

These sources combined SSO login and browser-session binding with IdentityProvider persistence and selection, Channel identity mapping, Tenant-domain resolution, platform SSO settings, and Google Workspace Organization administration and directory synchronization. `backend/app/api/google_workspace.py`, `backend/app/services/google_workspace_oauth.py`, and their deleted tests were mixed legacy entry surfaces: they joined Google Workspace administrator authorize URLs, OAuth state and callbacks, directory probe/proxy/sync behavior, and SSO browser-session completion. Their presence in this deletion does not assign those Organization capabilities to the target SSO owner. All listed legacy tests are deleted rather than adapted.

Fresh tests follow the target owner contracts: SSO owns login, session, provider selection, and binding-policy tests; Organization owns Google Workspace administrator authorize URL, OAuth state and callback, directory probe, proxy, and synchronization tests; Channel owns external identity mapping tests; `identity_tenant` owns Tenant-domain resolution tests; and `platform_administration` owns platform SSO settings and toggle tests. Each owner writes those tests only after its approved contract is implemented.

This minimum deletion preserves Organization sync adapters and services, provider-specific Channel APIs, mixed IdentityProvider administration and SSO policy routes in `enterprise.py`, Invitation, Onboarding, generic email, `core/security.py`, mixed schemas, migrations, dependencies, Frontend, and the empty target `modules/sso` package. Those retained sources may still import the deleted IdentityProvider model or SSO services, and the Organization adapter may still import the deleted Google Workspace OAuth proxy constant. These dangling consumers are staged evidence for their own owner/category commits; they do not authorize restoring the old SSO API, model, DAO, services, Google Workspace OAuth entrypoint, or compatibility export.

`backend/tests/architecture/test_deleted_authorities.py` makes every removed Python import identity absent as both a module file and a same-named package directory. Its negative fixtures prove that recreating either form fails the target guard. The generated Skill creator-files directory is independently guarded as a forbidden path; deleted DAO, Auth, SSO, Organization/Relationship, or Invitation exports cannot return through static or dynamic re-exports; and ordinary Backend tests cannot import a deleted Auth, SSO, Organization/Relationship, or Invitation identity. Surviving legacy callers remain staged evidence for their own deletion category; they do not justify compatibility modules, fallback Context assembly, Experience projections, an old Model execution facade, Persistent Task persistence, OpenClaw/Gateway authority, old Agent Credential authority, the overloaded old Agent aggregate, the old Identity/Tenant aggregate, old Auth orchestration, old SSO authority, the overloaded old Organization/Relationship aggregate, old Invitation persistence, or the legacy Tenant Knowledge publication adapter.

The overloaded legacy Organization/Relationship aggregate is removed as its own minimum category:

- `backend/app/models/org.py`
- `backend/app/api/organization.py`
- `backend/app/api/relationships.py`
- `backend/app/dao/org_member_dao.py`
- `backend/app/services/org_sync_adapter.py`
- `backend/app/services/org_sync_service.py`
- `backend/app/services/access_relationships.py`
- the `org_member_dao` compatibility export from `backend/app/dao/__init__.py`
- `backend/tests/test_org_sync_adapter.py`
- `backend/tests/test_organization_tenant_scope.py`

These sources made `OrgDepartment`, `OrgMember`, `AgentRelationship`, and `AgentAgentRelationship` one shared authority for provider directory synchronization, Tenant membership administration, relationship labels and creator-management rules, and access metadata. The relationship Workspace regeneration hook was already a no-op compatibility concept; this deletion removes that compatibility surface and does not remove a live Workspace projection. These legacy facts do not remain as a compatibility aggregate, and their dedicated tests are deleted rather than adapted.

The Phase 0 disposition is approved for deleting this legacy aggregate. The target owner assignments are disposition-approved, but their owner contracts remain unreviewed; this deletion does not authorize implementation. After those contracts are reviewed and approved, `identity_tenant` rewrites Tenant membership facts and membership tests, while Auth/Account owns global login fields and their mutation tests. Organization owns departments, external-directory facts, provider synchronization orchestration, and their tests. Permission owns explicit Membership/Agent visibility grants, access resolution, and denial-path tests without relationship labels or creator-management metadata. Directory composes those owners only through their public services and tests that composition. Workspace tests only its own mutation boundary and does not receive a relationship projection. No target owner may restore `OrgDepartment`, `OrgMember`, `AgentRelationship`, `AgentAgentRelationship`, or `org_member_dao` as a shared legacy persistence contract.

The Organization/Relationship category deliberately excludes Enterprise Info persistence and API ownership, Invitation codes, mixed routes in `enterprise.py`, the Directory API and service, Participant and Group, OKR, Onboarding, Channel, templates, migrations, dependency declarations, Frontend, and the empty target `modules/organization`, `modules/permission`, and `modules/directory` packages. Retained Enterprise, Directory, OKR, Onboarding, Permission-core, Channel, script, seed, and bootstrap sources still import one or more deleted Organization/Relationship identities. Those dangling imports are staged evidence for later owner/category commits and are not repaired here; they do not authorize a compatibility module, DAO export, implicit relationship lookup, or relationship Workspace regeneration.

The deleted-authority guard now covers every removed Organization/Relationship module and same-named package representation, static or dynamic restoration of the `org_member_dao` package export, and ordinary Backend test imports of any deleted identity. After contract review and approval, `identity_tenant`, Auth/Account, Organization, Permission, Directory, and Workspace must write their own boundary tests rather than importing or renaming these legacy tests.

The legacy Invitation persistence authority is removed as its own minimum category:

- `backend/app/models/invitation_code.py`
- `backend/app/dao/invitation_code_dao.py`
- the `invitation_code_dao` compatibility export from `backend/app/dao/__init__.py`

These sources made `InvitationCode` and its active-code lookup the shared persistence contract for registration gating, Tenant invitation-code administration, platform company creation, batch user invitation, listing, CSV export, and deactivation. The Phase 0 disposition preserves Invitation as a product capability but assigns its replacement to the separate target `invitation` owner; that owner contract remains unreviewed, so this deletion does not authorize implementation or preservation of the old table contract.

No dedicated Backend test currently protects the old InvitationCode persistence, invitation-code CRUD/export, or invite-user persistence flow. `backend/tests/test_enterprise_invites.py` remains because it tests only the generic System Email enabled/disabled preflight and does not import or instantiate the deleted model or DAO. After contract review and approval, the target Invitation owner must receive fresh persistence, lifecycle, Tenant-scope, limit, registration-consumption, and delivery-boundary tests; generic email configuration remains owned and tested separately.

This minimum deletion preserves the mixed Invitation routes in `backend/app/api/enterprise.py` and `backend/app/api/admin.py`, `backend/seed.py`, `backend/app/scripts/bootstrap_db.py`, Onboarding, generic and System Email, mixed schemas, migrations, dependency declarations, Frontend, and the empty target `modules/invitation` package. Their surviving imports of `app.models.invitation_code` are deliberate staged evidence for later owner/category commits and are not repaired here. They do not authorize restoring the old model, DAO, DAO export, table contract, or compatibility shim.

The deleted-authority guard covers both removed Invitation import identities as module and same-named package forms, static or dynamic restoration of the `invitation_code_dao` package export, and ordinary Backend test imports. Fresh target Invitation tests must exercise the new owner contract rather than rename the retained System Email preflight test or restore an old fixture.

The legacy Onboarding authority is removed as its own minimum category:

- `backend/app/models/onboarding.py`
- `backend/app/api/onboarding.py`
- `backend/app/services/onboarding.py`
- `backend/tests/test_onboarding.py`

These sources combined two obsolete facts: `UserTenantOnboarding` tracked company-entry progress and personal-assistant creation, while the service tracked per-user Agent greeting and calibration phases through the already deleted `AgentUserOnboarding` fact. The API also coupled Onboarding completion to old Agent creation, relationship projection, Agent-file initialization, and container startup. The dedicated test file protected only those old prompts, phase transitions, bootstrap-field absence, and file/focus finalization instructions, so it is deleted instead of carried into the target.

Onboarding remains an S3 product capability, but its owner contract remains unreviewed and this deletion does not authorize target implementation or preservation of either old state machine. After contract review and approval, the target `onboarding` owner receives fresh Tenant-scoped lifecycle, idempotency, completion, and Agent-creation orchestration tests. The later S3-wave Agent and Workspace owners receive their own fresh boundary tests; Onboarding tests must consume those public boundaries rather than restore direct Agent-file or container control.

Agent Template sources and `template_seeder.py` remain because template inventory and seeding are independently owned by `agent_template`, not by the deleted Onboarding phases. Generic Auth and Email, Enterprise, Directory, Channel, Workspace, mixed schemas, migrations, dependencies, and Frontend remain staged. Their surviving imports or references are deliberate source-disposition evidence for later minimum owner/category commits and are not repaired here; they do not authorize restoring `app.models.onboarding`, `app.api.onboarding`, `app.services.onboarding`, or the deleted tests.

The deleted-authority guard makes all three old Onboarding import identities absent as modules and same-named packages, with negative fixtures for both representations and ordinary Backend-test imports. Fresh target tests must use the approved S3 owner contracts rather than rename the old prompt, phase, bootstrap, or file-initialization fixtures.

The legacy Directory authority is removed as its own minimum category:

- `backend/app/api/directory.py`
- `backend/app/services/agent_directory.py`
- `backend/tests/test_agent_directory_api.py`

These sources joined a read-only human/Agent roster query with Custom Directory maintenance. The API directly queried and mutated the deleted Organization/Relationship aggregate and old Agent Permission persistence, while the service directly combined Agent, Permission, Organization, IdentityProvider, ChatSession, and Channel-contact readiness facts. Its sole dedicated test imported the deleted API directly and protected only old route shapes, Organization-backed candidate SQL, roster filtering, and error translation, so it is deleted instead of carried into the target.

Directory remains an S3 composition owner, but its owner contract remains unreviewed and this deletion does not authorize a replacement implementation or preservation of the old route and payload contracts. After contract review and approval, the target `directory` owner receives fresh composition tests over public Identity/Tenant, Organization, Permission, Agent, Group/Participant, and Channel contracts. Those tests must cover bounded search, Tenant isolation, visibility, contactability, and unavailable-target behavior without restoring direct imports of private persistence models.

There was no separate Directory DAO, helper module, package export, or production router registration to delete. The empty `backend/app/modules/directory` target-owner package remains. Group/Participant, Channel identity mapping and delivery, Permission core, `participant_identity.py`, `channel_user_service.py`, mixed query DAOs, Enterprise and administration surfaces, schemas, migrations, dependencies, and Frontend remain staged. Their surviving Directory wording or dangling imports are evidence for later owner/category commits and do not authorize restoring `app.api.directory`, `app.services.agent_directory`, or the deleted tests.

The deleted-authority guard makes both old Directory import identities absent as modules and same-named packages, prevents static or dynamic API/service package re-exports, and rejects ordinary Backend-test imports. Fresh S3 tests must exercise the approved Directory public composition rather than rename the old API fixture or couple to Group, Channel, Permission, Organization, or Agent persistence.

The legacy Focus authority is removed as its own minimum category:

- `backend/app/models/focus.py`
- `backend/app/dao/focus_dao.py` and its `app.dao` package export
- `backend/app/api/focus.py`
- `backend/app/services/focus_service.py`
- `backend/tests/test_focus_service.py`

These sources made database-backed `AgentFocusItem` rows, legacy `focus.md` migration, item upsert/completion, model-context rendering, and the Agent-scoped Focus HTTP routes one coupled authority. The sole dedicated test imported the deleted service and protected only its legacy migration and DAO orchestration, so it is deleted instead of adapted.

Focus remains a later S3 product owner, but its owner and product contracts remain unreviewed. After both contracts are reviewed and approved, the target `focus` owner must receive fresh persistence, Tenant and Agent scope, bounded list, upsert, completion, authorization, migration-disposition, API, and model-context tests. The old service test is not renamed or used to infer the target contract.

This minimum deletion preserves OKR and its Focus wording, activity and observability, schedules and Triggers, retained file APIs and storage tests that mention `focus.md`, mixed schemas, migrations, dependencies, Frontend, and the empty target `modules/focus` package. Their surviving imports of the deleted Focus service or model are deliberate staged evidence for later owner/category commits and are not repaired here; they do not authorize restoring the old model, DAO, DAO export, API, service, file-migration path, or compatibility shim.

The deleted-authority guard makes all four old Focus import identities absent as modules and same-named packages, prevents static or dynamic restoration of the `focus_dao` package export, and rejects ordinary Backend-test imports. Fresh S3 Focus tests must exercise the approved target owner rather than preserve the legacy database/file hybrid.

The legacy Notification authority is removed as its own minimum category:

- `backend/app/models/notification.py`
- `backend/app/api/notification.py`
- `backend/app/services/notification_service.py`
- the Notification broadcast assertions removed from the former mixed `backend/tests/test_system_email_and_notifications.py`

These sources made one `Notification` table and service the shared authority for human and Agent inbox persistence, unread counts, read state, Tenant broadcast fan-out, approval/autonomy notices, Plaza mentions and comments, Heartbeat draining, and OKR oneshot-failure reporting. The HTTP layer also coupled in-app broadcast persistence to generic System Email delivery. Those legacy persistence and delivery contracts are deleted rather than adapted.

Notification remains an S3 product owner, but its owner and product contracts remain unreviewed. After both contracts are reviewed and approved, the target `notification` owner must receive fresh persistence, Tenant and recipient scope, unread/read lifecycle, bounded listing, authorization, post-commit publication, and delivery-outcome tests. Approval-driven behavior is not restored through Notification: the clean-break target removes the old Approval Request and L1/L2/L3 autonomy contract.

Generic System Email transport remains independently owned in `backend/app/services/system_email_service.py`, with its SMTP timeout and per-recipient failure-containment tests preserved in `backend/tests/test_system_email.py`. Chat messages and Channel delivery, group realtime publication, activity and observability, enterprise notification-bar settings, mixed Platform/Enterprise routes, schemas, migrations, dependencies, Frontend, and the empty target `modules/notification` package also remain staged.

Heartbeat, Plaza, OKR, Autonomy, bootstrap, cleanup-script, and other retained consumers still import the deleted Notification model or service. Those dangling imports are deliberate source-disposition evidence for their later owner/category commits and are not repaired here; they do not authorize restoring the table, API, service, inbox, broadcast, approval-notice path, or a compatibility shim.

The deleted-authority guard makes all three legacy Notification import identities absent as modules and same-named packages and rejects ordinary Backend-test imports. Fresh S3 tests must exercise the approved Notification owner and its explicit consumers rather than rename the removed broadcast assertions or preserve old approval persistence.

The legacy Tenant Knowledge publication adapter is removed as a separate minimum category:

- `backend/app/services/enterprise_sync.py`
- `backend/tests/test_enterprise_info_tenant_isolation.py`

`enterprise_sync.py` combined `EnterpriseInfo` creation and update, Redis publication, Agent selection, role filtering, and JSON writes under each Agent's `enterprise_info/` directory. Its test mixed Enterprise Info CRUD and Tenant isolation with publication into the deleted Agent aggregate and old Agent-file layout. The adapter and mixed test are deleted rather than carried into the target.

The target owner is definitively `tenant_knowledge`, but its owner contract remains unreviewed and this deletion does not authorize implementation. Enterprise Info persistence and its mixed API routes remain staged source evidence. After contract review and approval, `tenant_knowledge` owns CRUD, Tenant isolation, source facts, and their tests. Agent and Context test consumption and source attribution through the public Product Context consumer boundary; Product Context is never an alternate owner. Workspace owns and tests only its own mutation boundary and does not own Tenant Knowledge or publish it into Agent files.

The deleted-authority guard makes `app.services.enterprise_sync` absent as both a module and a same-named package, with negative fixtures for both restoration forms. Mixed `enterprise.py` routes retain a dangling import until their later source-disposition category; that staged failure does not authorize restoring the publication adapter.

### Delete without porting

The following behavior and its dedicated source, schema, tests, configuration, and dependencies are removed:

| Removed behavior | Current source evidence |
|---|---|
| OpenClaw Agent type, API key, Gateway polling/report/send-message, remote online status, and Native/OpenClaw branching | `app/models/agent.py`, `app/models/gateway_message.py`, `app/api/gateway.py`, OpenClaw branches in `app/api/websocket.py`, Gateway and OpenClaw tests |
| Agent execution status, container identity, start/stop lifecycle, Agent expiry, `agent_type`, system-Agent runtime variants, and Agent-owned Runtime counters | current `Agent` fields and `app/api/agents.py` start/stop/API-key routes |
| LangGraph graph, PostgreSQL Checkpoint, Thread state, Checkpoint compatibility decoding, Command worker, execution takeover/replay, scheduling lanes, and checkpoint-side-effect reconciliation | `app/services/agent_runtime/graph.py`, `state.py`, `checkpointer.py`, `langgraph_driver.py`, `command_worker.py`, `checkpoint_side_effects.py`, `worker_service.py`, `scheduling_lane.py`; `agent_run_commands`; LangGraph dependencies |
| Generic Runtime Event, Tool execution Ledger, async Tool polling, Tool repair budget, and product reconciler | `agent_run_events`, `agent_tool_executions`, `event_stream.py`, `tool_result_store.py`, `async_tool_poll.py`, `tool_repair_budget.py`, `product_reconciler.py` |
| Old Prompt and Context authority, implicit relationship/setting queries, and fallback Context assembly | `app/services/agent_context.py`, its direct consumers and tests; replacement comes only from the target Context source contract |
| Persistent Task and Task Log lifecycle, Task CRUD/intake, Task completion projection, and Task execution service | `app/models/task.py`, `app/api/tasks.py`, `app/services/task_executor.py`, `task_completion.py`, related tests |
| Approval Request, L1/L2/L3 autonomy policy, approval-driven Waiting/Resume, and approval APIs | `ApprovalRequest`, Agent `autonomy_policy`, `autonomy_service.py`, approval routes in `agents.py` and `enterprise.py`, Runtime approval authorization |
| Model fallback, cross-Model failover, Model-step/Tool-round cap, Run duration cap, and Token/message/call quota enforcement | `fallback_model_id`, `app/services/llm/failover.py`, `quota_guard.py`, Agent and User quota fields, quota APIs and tests |
| Relationship labels, creator-management semantics, relationship Memory/access metadata, no-op `relationships.md` compatibility regeneration, and the legacy relationship API | `AgentRelationship`, `AgentAgentRelationship`, `app/api/relationships.py`, and `access_relationships.py`; the file-regeneration hook no longer projected live Workspace state, while explicit Membership/Agent visibility assignment is rewritten under Permission rather than removed |
| Structured Experience library, revision drafts, citation projection, and retrieval/RAG path | `ExperienceEntry`, `ExperienceReference`, `app/api/experience.py`, `experience_retrieval.py`, Runtime experience citation paths |
| Agent-authored Skill creation, evaluation loop, generated Skill assets, and direct Skill file mutation | `skill_creator_content.py`, `skill_creator_files/`, Agent-facing Skill write/browse routes; first release permits only controlled Market/Admin installation |
| Agent handover by changing creator identity | `app/api/advanced.py` handover route; target creation audit is immutable and Agent management belongs to Tenant administrator |
| Session Context State, background Session compaction authority, and checkpoint-derived Context state | `session_context_states`, `session_context_*` services and their tests |
| Legacy schedule object separate from Trigger | `AgentSchedule`, `app/api/schedules.py`, `scheduler.py`; schedule behavior is re-expressed by Trigger ownership |
| Startup schema repair, default-Tenant repair, inline data migration, backfill scripts, old bootstrap patches, and the existing Alembic chain | migration and repair blocks in `app/main.py`, `app/scripts/migrate_*`, `backfill_*`, `setup_langgraph_checkpoints.py`, every current `alembic/versions/*` migration |
| Storage compatibility fallback and old key/path fallback | `app/services/storage_runtime/fallback.py` and compatibility reads of legacy Workspace or storage layouts |
| Monolithic Model/Tool authority facades | `app/services/llm/caller.py` and `app/services/agent_tools.py`, which combine old ORM, Prompt, permission, fallback, Tool exposure/dispatch, approval, Ledger, plaintext-Secret compatibility, and loop behavior |
| Unmounted or unconsumed transport code with no current application route or runtime consumer | presently unregistered modules such as `app/api/whatsapp.py`, unless a later Channel inventory establishes a real consumer before removal |

Tests whose only purpose is to preserve one of these deleted contracts are deleted with it. A useful scenario is rewritten against the new owner rather than retaining an old fixture or compatibility adapter.

### Rewrite as foundational modules

These capabilities are required by the first implementation slices and receive new modules, tables, services, APIs, and tests:

| Target module | Current capability to inventory, not preserve | Replacement owner |
|---|---|---|
| Identity and Tenant | `Identity`, `User`, `Tenant`, auth middleware, tenant switching | Account, Membership, Tenant, Tenant Principal, Platform Principal |
| Minimal Permission | Agent access modes, `AgentPermission`, current relationship assignment APIs, scattered route checks | one Permission Resolver, explicit Membership/Agent visibility-grant mutation surface, authorization generation, Run dependency projection |
| Credential and Audit | Agent credential table, Secret-bearing Channel/Tool/LLM JSON, audit logger | one Credential store with binding-specific owner matrix; closed Audit actor union |
| Agent | overloaded `Agent` row, templates and bootstrap fields | narrow Tenant Agent identity, Soul, greeting, model relation, enabled/archive controls |
| Model System | LLM rows, caller/client, runtime settings, capability probing, failover | fixed per-Run Model Policy, Provider adapters, normalized result, required continuation state |
| Tool and Capability | `Tool`, `AgentTool`, builtin definitions, MCP discovery, Skill database and ClawHub paths | Registry, Tenant Tool Definitions and Grants, Capability Market, per-Agent MCP connections, Workspace Skill packages |
| Workspace | Agent files, group files, Skill browse/write, Experience Memory, revision and edit-lock tables | Membership, Agent, and Group Workspaces with `memory/`, `skills/`, `files/`, CAS mutation and one-way publication |
| Agent Runner and Loop | the entire `app/services/agent_runtime/` execution authority | Run, immutable Snapshot, append-only History, Context Projection, one lightweight Runner and Loop |
| Context | `agent_context.py`, Runtime context builders, Session Context State, implicit relationship/settings lookup, and old Base Prompt | explicit Platform Instructions, Agent Identity/Soul, Product Input, Run Context, Workspace Discovery, Tool Exposure, Retrieved Content, and Model Context Profile sources |
| Direct Session | `ChatSession`, `ChatMessage`, WebSocket chat intake and delivery | immutable human Session Input, cutoff, Main Run initiation/resume, atomic Session Reply |
| Task, Todo, A2A, Goal | current Task tables, planning services, A2A Runtime and Gateway correlations | model-facing Tools and Session Goal configuration without Task/Todo/Goal lifecycle objects |
| Product handoff | checkpoint completion handlers and generic reconciler | owner-specific atomic result records and A2A pending delivery |

The old `app/services/agent_runtime/` package is not incrementally converted. New Runtime modules are built from the accepted contracts; only independently pure helpers may be copied after review. Once the new composition owns a path, the corresponding old Runtime files and tests are deleted rather than kept behind a compatibility switch.

### Reuse behind new owners

The following implementations carry useful bounded behavior and should be evaluated for extraction instead of rewritten automatically:

| Reusable capability | Candidate source | Required adaptation |
|---|---|---|
| Sandbox providers and isolation | `app/services/sandbox/` including local Docker/subprocess and remote providers | keep Sandbox as a separate execution venue; remove Runtime-specific leases or identity assumptions that do not match new Run scope |
| Local and S3 object operations | `app/services/storage_runtime/local.py`, `s3.py`, atomic storage tests | expose only through the new Workspace owner; remove compatibility fallback and legacy paths |
| Document and text conversion | `document_conversion/`, `text_extractor.py`, `vision_inject.py` | register as ordinary Tools with bounded results |
| Provider HTTP and multimodal encoding | individually named functions recovered from Git history for the former `app/services/llm/client.py`, `multimodal_content.py`, and narrow utilities | review and test each recovered function behind the target Provider Adapter; the old package and `llm/caller.py` are never restored |
| MCP transport and OAuth mechanics | `mcp_client.py` and current OAuth helpers | place behind Tenant Catalog materialization, Agent connection, Credential, and new Tool executor |
| External Tool protocol operations | capability-specific Atlassian, Feishu, Google Workspace, email, deployment, search, and document helpers | preserve supported operations but regenerate Definition/Grant registration and normalized Tool Result boundaries; `agent_tools.py` and `builtin_tool_definitions.py` remain inventory inputs and are not reusable facades |
| Channel protocol adapters | Feishu, DingTalk, WeCom, WeChat, Slack, Discord, Teams and Atlassian service modules | retain SDK/webhook/stream protocol code only; rewrite authentication, Product Input, Session/Group ownership, Run start, and delivery |
| Realtime transport | Redis pub/sub and WebSocket connection mechanics | publish only committed owner events; replace Runtime event/checkpoint payloads |
| Cross-cutting infrastructure | database engine/session, logging, error mapping, time-zone and business-calendar helpers | retain only generic behavior; rewrite Tenant middleware and security around Principal union |

Reuse requires direct source and behavior review. Deleted Provider candidates may be recovered only from Git history; the immutable legacy checkout remains black-box behavior evidence and is never imported, copied from, or treated as a source tree. A candidate that imports deleted ORM models, Runtime contracts, checkpoint data, legacy permission, plaintext Secret fields, or fallback behavior is split or rewritten before use. Code formerly in `llm/caller.py`, `agent_tools.py`, or another authority aggregator may move only as an individually named and tested pure function or single-capability protocol operation; the original module, facade, initialization, fallback, discovery, and dispatch paths are always deleted.

### Preserve product capability but rewrite later

These currently exposed features are not prerequisites for the foundational Runner, but they are not silently deleted. Each becomes a later module slice with its own owner decision and target tests:

- SSO, OAuth identity binding, Google Workspace directory sync, invitations, registration, password recovery, and organization synchronization.
- Group administration, membership, announcement, Group Session, Group Workspace, group realtime transport, and external-group channel mapping.
- Tenant EnterpriseInfo, Tenant Knowledge Base files, administrator mutation, Agent read-only Tenant Knowledge Context, and replacement consumption. The definitive owner is `tenant_knowledge`, whose contract remains unreviewed; Product Context is only the public consumer boundary for Agent and Context, and Workspace is not an alternate owner.
- Heartbeat, schedules-as-Triggers, webhook and polling Triggers, Trigger execution results, and Focus.
- Feishu, DingTalk, WeCom, WeChat, Slack, Discord, Microsoft Teams, Atlassian, and other mounted Channel configuration, inbound message, outbound delivery, and connection health.
- OKR objectives, key results, alignment, progress, daily collection, member/company reports, and the OKR Agent product integration.
- Agent templates, onboarding, directory presentation, activity/usage observability, notifications, public pages, Plaza, enterprise settings, platform administration, email configuration, and AgentBay control.

`defer` means the old implementation remains only until its replacement slice is ready. It does not authorize old tables or APIs in the final clean-break Backend, and it does not create a compatibility layer between old and new identities.

### Migration, composition, and dependency disposition

The target starts with one new Alembic baseline. `alembic/env.py` and the migration template may be reused as infrastructure, but the current version chain and model-import list are replaced. Before that work begins, `backend/alembic/AGENTS.md` is rewritten to record the approved one-time clean-break exception to its current append-only head rule; after the new baseline, it again requires one head, retained forward migrations, and normal verification. The initial target composition performs no schema mutation or product bootstrap. Later owner integration may add schema verification and explicit idempotent product bootstrap, but startup never calls `create_all`, migrates files, patches existing records, or swallows bootstrap ownership failures.

The G002 startup boundary launches only `app.main:app` in one Uvicorn worker and no longer runs Alembic, LangGraph checkpoint installation, schema repair, or process-role branches. `alembic/env.py` now reads metadata only from the target infrastructure registry. The existing legacy revision chain and head remain temporarily present for topology evidence until G008; they are not the target baseline or a supported target upgrade path, and this change does not generate or apply a new baseline.

FastAPI composition has one factory and one application lifespan. The lifespan owns separate control and execution SQLAlchemy engines against the validated target PostgreSQL database, creates isolated pools of twenty connections with zero overflow by default, and awaits disposal of both pools at shutdown. Target configuration loads dotenv values only from `backend/.env`, rejects unknown dotenv settings, requires a complete `postgresql+asyncpg` URL, and fails when neither an explicit application version nor the non-empty `backend/VERSION` artifact is available. Each module later registers its own transport adapters and bounded lifecycle resources; current process-role branches, connector managers, schedulers, Runtime worker startup, and seeding blocks are not copied wholesale. The first release enforces one non-overlapping Runner deployment while connector and product background services retain their own bounded lifecycle owners.

`langgraph`, `langgraph-checkpoint-postgres`, and checkpoint-only `psycopg` usage are removed when no surviving consumer remains. Other dependencies remain only when a retained provider, Channel, conversion, Sandbox, storage, authentication, or product module imports and tests them. Dependency removal follows source removal rather than preceding it.

### Test disposition

New tests are organized by target owner and contract. Runtime tests cover Run start/resume/cancel, Status and History atomicity, Child and product handoffs, Waiting, interruption, Context source reconstruction, Tool exposure/dispatch identity, Provider continuation, and concurrency. Database tests cover fresh baseline creation, composite Tenant foreign keys, partial uniqueness, owner checks, idempotency, authorization generation, and concurrent duplicate submission.

Existing pure tests for provider encoding, Sandbox isolation, S3/local storage atomicity, document conversion, Channel protocol parsing, and external Tool behavior may be retained after their imports are moved to the new boundary. Tests for deleted models, routes, fields, compatibility reads, fallback, quotas, approvals, Checkpoints, Commands, Ledger, Task persistence, relationship Memory, or OpenClaw are removed.

## Alternatives considered

### Incrementally refactor the current Agent Runtime

The current package makes Checkpoint, Command, Tool Ledger, scheduling lane, product reconciliation, and LangGraph Thread state central to execution. Preserving it while introducing Run History and the new owner boundaries would create two authorities and prolong compatibility work the clean break explicitly rejects.

### Delete every Backend file and recreate all provider code

Provider adapters, Channel protocol handling, Sandbox isolation, storage operations, document conversion, and external Tool implementations contain useful bounded behavior. Rewriting all of them simultaneously adds risk without changing their responsibility. They are reused only after separation from old authority.

### Keep every current product table until its frontend is rewritten

This would force new core modules to reference old User, Agent, permission, Task, Credential, and Workspace identities. Deferred product modules may remain temporarily during staged development, but the final Backend has one target schema and no cross-schema compatibility contract.

## Acceptance criteria

- Every current Backend capability is classified as delete, rewrite, reuse, or defer; omission does not decide product behavior.
- OpenClaw, LangGraph Checkpoint, Command, Runtime Event, Tool Ledger, persistent Task, Approval, fallback Model, quota enforcement, relationship labels/access metadata and no-op compatibility regeneration, Experience RAG, Session Context State, legacy Schedule, startup repair, and old migration behavior have no target execution path.
- Explicit Membership/Agent visibility assignment is rewritten as the producer of `agent_visibility_grants`; deleting legacy relationship semantics does not remove this required Permission surface.
- Tenant EnterpriseInfo and Knowledge Base remain explicitly deferred under `tenant_knowledge` until its owner contract is reviewed and approved; Product Context remains a consumer boundary, and Tenant Knowledge is neither silently deleted nor placed under Workspace ownership.
- Agent handover through mutable creator identity is removed; creation identity remains immutable audit and Tenant administrator retains management authority.
- The foundational rewrite starts from new module owners and one new schema baseline rather than modifying old Runtime authority in place.
- Sandbox, storage, conversion, Provider, MCP, external Tool, Channel, realtime, and infrastructure code is reusable only after removing imports and assumptions owned by deleted contracts.
- Every currently mounted product capability is either included in a rewrite slice or explicitly deferred; deferred does not mean silently removed.
- Old APIs, models, tests, configuration, and dependencies are deleted together when their replacement or removal becomes authoritative.
- No compatibility adapter, dual write, fallback read, startup repair, or legacy data migration connects the current Backend to the target.
- Implementation planning sequences owner prerequisites before consumers and verifies each cutover through the target contract rather than old test expectations.

## Risks and open questions

This source map is grounded in current route registration, models, services, migrations, tests, and startup composition, but dynamic external consumers and Frontend calls still require a separate cross-layer inventory before each API removal. A route with no Backend registration is not treated as supported solely because a file exists. `tenant_knowledge` is the definitive owner, but its unreviewed contract, persistence, API, source-attribution, and Product Context consumption boundaries remain unresolved implementation work.

The exact package tree, implementation slices, retained third-party dependencies, and temporary development branch cutover order remain implementation-planning decisions. No old persistence contract may leak into those decisions merely to reduce short-term code movement.

The final handoff for this deletion is to `identity_tenant` for Membership, Auth/Account for global login fields, Organization for departments and external-directory synchronization, Invitation for invitation lifecycle and consumption, Permission for visibility grants and authorization, Directory for public-service composition, and Workspace only for its independent mutation boundary after each owner contract is reviewed and approved.

The Tenant Knowledge publication handoff is to `tenant_knowledge` for CRUD, isolation, and source facts, Agent and Context for Product Context consumption and source-attribution tests, and Workspace only for its independent mutation boundary after the `tenant_knowledge` owner contract is reviewed and approved.
