# Agent Note: Minimal RBAC and Agent Visibility

Status: proposed — the first-release Permission owner and Agent visibility contract is agreed but not implemented

## Problem

Agent discovery, Session creation, A2A targeting, Agent Workspace preview, Capability installation, protected execution, and authorization revocation all require one current permission decision. Deferring the entire Permission domain would force each caller to invent its own Tenant and visibility checks and could allow a known Agent or Workspace identity to bypass discovery restrictions.

The first release needs only basic Tenant roles, Agent visibility, explicit Agent audience relations, one resolver, and an index from authorization dependencies to non-terminal Runs. It does not need custom roles, Department ACL, ABAC, Approval, per-file policy, or a generic policy engine.

## Proposal

### Roles

Account may hold platform administration. Membership role is the closed set `tenant_admin` or `member` defined by [Account, Membership, Tenant, and Principal](2026-08-31-account-membership-tenant-principal.md).

Platform administrator performs explicit audited platform operations against a target Tenant and does not automatically receive that Tenant's ordinary Agent Context. Its audit actor is the global Account and does not require a fabricated target-Tenant Membership. Tenant administrator manages Tenant Memberships, Agents, Soul, Model, Tool and MCP grants, Market, Credential, Channel, Agent visibility, and Agent Workspace preview. Member may use and preview only visible Agents and its own Membership Workspace. The first release allows only Tenant administrator to create and manage Agent; Agent creator identity remains audit only.

### Agent visibility

Agent visibility is `tenant` or `restricted`. An enabled `tenant` Agent is visible and usable to active Memberships and Agents in the same Tenant. A `restricted` Agent is visible and usable only to explicitly granted same-Tenant Memberships or source Agents. Tenant administrator always receives management access.

`agent_visibility_grants` contains Tenant, target Agent, exactly one subject Membership or source Agent, granting Membership, revocation timestamp, and timestamps. A `num_nonnulls(subject_membership_id, subject_agent_id) = 1` check enforces exactly one subject. Separate partial unique indexes for Membership and Agent subjects enforce one effective target-subject relation without nullable uniqueness gaps. Composite foreign keys enforce that target, subject, and granting Membership belong to the recorded Tenant. A private product preset may create a restricted Agent plus one explicit Membership grant; it does not add another persistence mode.

### Permission Resolver

One Permission Resolver returns `none`, `use`, or `manage` for a current Tenant Principal or Agent subject and target Agent. Platform Principal cannot enter this ordinary Agent authorization path. Cross-Tenant, disabled subject, disabled target, missing restricted grant, and revoked relation return `none`. Tenant administrator returns `manage`; the first release has no Agent-specific manage grant. Visible active Membership or Agent returns `use`.

Agent list and search, Session creation, A2A target discovery, Agent Workspace preview, Run start, and Capability installation consume the same result and recheck it at the protected operation. Frontend hiding, Tool omission, known identifiers, Prompt text, and ordinary call ordering never authorize access. Workspace does not store another visibility ACL.

### Capability installation

Agent may install a Market item only when its immutable Available Tool Set contains the explicitly granted `install_capability` Builtin. Installation may create or reuse Tenant Catalog data and may create only the executing Agent's connection and grants. It cannot grant another Agent, expose another Agent's Credential, disable shared Tenant items, or perform Tenant-admin mutations. Approval remains deferred; the first release evaluates basic allow or deny only.

### Revocation and Run dependencies

Every revocable authorization dependency exposes a positive monotonic `authorization_generation`. Run Snapshot records each complete resolved dependency identity and generation plus their count and digest. `run_authorization_dependencies` is its indexed projection from active Run to the Membership, Agent visibility grant, Agent Tool Grant, Credential, Group membership, Workspace, and other revocable facts on which that Run depends. Run, Snapshot, and every dependency row commit in the same start transaction; an incomplete projection rejects Run creation and never reaches admission. The projection grants no permission and cannot expand Snapshot.

When a dependency is revoked, disabled, deleted, transferred, or narrowed, its owner commits that authoritative fact and increments `authorization_generation` in one short transaction. Re-enablement or a later grant never restores or reuses an earlier generation. Credential Secret rotation that preserves the same authorization does not increment generation; revocation or owner/scope change does. Every protected operation and Agent Runner's pre-Model-Step dependency check requires the owner to remain active and its current generation to equal the Run Snapshot generation. A mismatch fails closed permanently for that Run, so cancellation cleanup latency or rapid re-enablement cannot authorize more execution. Newly granted permission affects only new Runs. Historical Context and Run History are not rewritten.

After an invalidating generation change commits, Permission finds dependent Running and Waiting Runs whose projected generation differs from the current dependency generation, or whose dependency no longer exists or is inactive, in bounded stable-order batches and requests idempotent cancellation from Agent Runner, which propagates to Child Runs. Each batch uses its own transaction and never locks all Tenant Runs at once. No durable cancellation job or generic queue is required: a restart repeats the mismatch query, and already terminal Runs fall out of it. Cleanup completes when no mismatched non-terminal Run remains, even if the owner has since been re-enabled.

The projection is rebuildable from non-Secret Run Snapshot facts but is operationally required for every non-terminal Run. It is never deleted or partially rebuilt while those Runs continue. Startup first applies the normal interruption sweep to inherited Running Runs, then validates every preserved Waiting Run and rebuilds missing projection rows before Runner readiness; a coverage cursor plus count and digest verification proves completion. Rebuild failure keeps Runner unready. If incomplete coverage is detected online, Runner stops admission and further Model Steps while revocation may still commit; execution resumes only after rebuild and required cancellations complete.

## Alternatives considered

### Defer all Permission work

The first release already exposes Agent, A2A, Workspace, Tool, Credential, and Market operations. Without one resolver those consumers would implement divergent security rules.

### Add generic Role and Permission tables

Two Tenant roles and one Agent visibility relation satisfy current consumers. Generic role assignment, permission catalogs, inheritance, and policy evaluation add unused choices and are deferred.

### Put use and manage levels on every Agent grant

The first release derives manage only from Tenant administrator and use from visibility. A per-Agent manage grant would create another role system without a current need.

### Treat Tenant equality as Agent visibility

Some Agents must be restricted within a Tenant. Tenant equality is necessary but does not authorize discovery, use, A2A, or Workspace preview by itself.

## Acceptance criteria

- The first-release Membership roles are only `tenant_admin` and `member`; platform role belongs to Account.
- Agent visibility is only `tenant` or `restricted`, with same-Tenant Membership or Agent grants for restricted visibility.
- Permission Resolver returns `none`, `use`, or `manage` and is the common decision for discovery, Session, A2A, Workspace preview, Run start, and Capability installation.
- Tenant administrator is the only Agent manager in the first release; Agent creator is audit only and no Agent manage grant exists.
- A known Agent or Workspace identity cannot bypass visibility, and every protected operation rechecks current Tenant and authorization.
- `install_capability` permits one Agent to install only for itself and never grants Tenant administration or another Agent's Credential.
- Run authorization dependency projection grants no access and supports complete cancellation after revocation without scanning arbitrary Snapshot JSON.
- Run start atomically commits the complete dependency projection; Runner readiness, revocation, and every next Model Step fail closed when its Snapshot count or digest does not match.
- Revocation commits before cancellation fan-out and is immediately authoritative; dependent Runs are cancelled in bounded idempotent batches that can resume after process loss without a generic job table.
- Every revocable dependency uses a monotonic authorization generation; invalidation increments it, later re-enablement never revives an old generation, and old Runs remain permanently ineligible.
- Approval, custom roles, Department ACL, ABAC, per-file ACL, policy engine, and complex permission inheritance remain deferred.

## Risks and open questions

Exact Permission Resolver API, dependency types and indexing, visibility grant foreign keys, list-query pagination, disabled-state cancellation transaction, permission-cache invalidation, and later migration to richer Permission policy remain implementation decisions under this minimal contract.
