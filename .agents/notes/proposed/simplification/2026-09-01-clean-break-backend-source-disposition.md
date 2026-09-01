# Agent Note: Clean-Break Backend Source Disposition

Status: proposed — the capability disposition is agreed; target application composition and database infrastructure are implemented, and the legacy Agent execution, old Context, structured Experience, old Model/LLM, Persistent Task, old Tool, old Skill, dedicated OpenClaw/Gateway, and old Agent Credential authorities are removed, while owner rewrites and the remaining category deletions remain incomplete

## Problem

The current Backend contains the product capabilities that the target must account for, but its implementation joins Agent identity, LangGraph execution, checkpoints, Commands, Tool execution ledgers, product reconciliation, relationship Workspaces, quotas, approvals, compatibility paths, and channel delivery across the same models and services. The `backend/app/services/agent_runtime/` package alone contains about sixty Python files and thirty-four thousand lines. Incrementally reshaping those authorities would preserve the exact lifecycle and compatibility structures the target architecture removes.

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

`backend/tests/architecture/test_deleted_authorities.py` makes every removed Python import identity absent as both a module file and a same-named package directory. Its negative fixtures prove that recreating either form fails the target guard. The generated Skill creator-files directory is independently guarded as a forbidden path. Surviving legacy callers remain staged evidence for their own deletion category; they do not justify compatibility modules, fallback Context assembly, Experience projections, an old Model execution facade, Persistent Task persistence, OpenClaw/Gateway authority, or the old Agent Credential authority.

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
| Relationship labels, creator-management semantics, relationship Memory/access metadata, relationship Workspace, and legacy relationship compatibility API | `AgentRelationship`, `AgentAgentRelationship`, obsolete portions of `app/api/relationships.py`, `access_relationships.py`, relationship Workspace behavior; explicit Membership/Agent visibility assignment is rewritten under Permission rather than removed |
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
- Tenant EnterpriseInfo, Tenant Knowledge Base files, administrator mutation, Agent read-only Tenant knowledge Context, and current synchronization. This remains a supported product capability but is not a fourth Workspace by default; its Product Context or Tenant Knowledge owner must be decided before the old routes and storage are removed.
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
- OpenClaw, LangGraph Checkpoint, Command, Runtime Event, Tool Ledger, persistent Task, Approval, fallback Model, quota enforcement, relationship Workspace, Experience RAG, Session Context State, legacy Schedule, startup repair, and old migration behavior have no target execution path.
- Explicit Membership/Agent visibility assignment is rewritten as the producer of `agent_visibility_grants`; deleting legacy relationship semantics does not remove this required Permission surface.
- Tenant EnterpriseInfo and Knowledge Base remain explicitly deferred until a Product Context or Tenant Knowledge owner is approved; they are not silently deleted or placed into Agent Workspace.
- Agent handover through mutable creator identity is removed; creation identity remains immutable audit and Tenant administrator retains management authority.
- The foundational rewrite starts from new module owners and one new schema baseline rather than modifying old Runtime authority in place.
- Sandbox, storage, conversion, Provider, MCP, external Tool, Channel, realtime, and infrastructure code is reusable only after removing imports and assumptions owned by deleted contracts.
- Every currently mounted product capability is either included in a rewrite slice or explicitly deferred; deferred does not mean silently removed.
- Old APIs, models, tests, configuration, and dependencies are deleted together when their replacement or removal becomes authoritative.
- No compatibility adapter, dual write, fallback read, startup repair, or legacy data migration connects the current Backend to the target.
- Implementation planning sequences owner prerequisites before consumers and verifies each cutover through the target contract rather than old test expectations.

## Risks and open questions

This source map is grounded in current route registration, models, services, migrations, tests, and startup composition, but dynamic external consumers and Frontend calls still require a separate cross-layer inventory before each API removal. A route with no Backend registration is not treated as supported solely because a file exists. Tenant Knowledge remains an explicit unresolved product owner rather than an omitted capability.

The exact package tree, implementation slices, retained third-party dependencies, and temporary development branch cutover order remain implementation-planning decisions. No old persistence contract may leak into those decisions merely to reduce short-term code movement.
