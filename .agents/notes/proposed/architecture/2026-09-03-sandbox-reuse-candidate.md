# Agent Note: Sandbox Reuse Candidate

Status: proposed — mature Sandbox mechanics are retained without claiming a current product entry or approving their future owner contract.

## Problem

The clean-break target has removed the old Tool and Runtime entry paths that composed Sandbox configuration, leases, workspaces, and result formatting. The remaining Sandbox package still contains mature local and remote execution mechanics, but source presence and focused tests do not make it an active target capability. Deleting the package would discard useful isolation and provider behavior; promoting it unchanged would preserve hidden dependencies and imply ownership that the target contracts have not approved.

## Proposal

Retain Sandbox as a reuse candidate with these fixed behavioral invariants:

- one requested execution resolves one backend and never switches venue or repeats code after dispatch;
- subprocess execution preserves its configured bwrap requirement and explicit unsafe-fallback policy;
- local execution keeps bounded timeout, output capture, sanitization, protected-file handling, process termination, and cleanup;
- Run-scoped bwrap processes and materialized workspaces keep one stable identity and explicit close paths;
- `merge` and `isolated_output` keep their existing publication paths, conflict modes, gateway callbacks, and publication-ownership checks;
- execution leases keep the exact Tenant/Agent/Session key, NX acquisition, TTL, owner-checked renewal and release, heartbeat, publication window, and ownership-loss behavior;
- remote provider errors keep their existing timeout, known failure, and unknown-outcome distinctions.

There is no current product, Tool, API, Runner, or application-composition entry that constructs these objects. Tests prove only the retained mechanics. A future owning contract must identify the product caller and lifecycle owner, provide decoded secrets and an owned Redis client explicitly, supply approved Workspace materialization and publication callbacks, define authorization and Tenant inputs, and verify the assembled entry path. It must not add a settings singleton, hidden `SECRET_KEY`, alternate execution path, or compatibility import.

The legacy implemented venue-ownership Note is archived because its `agent_tools` workspace entry, configuration store, and result formatter no longer exist. This proposed Note is the current decision boundary for evaluating reuse; it does not authorize activation.

## Alternatives considered

**Delete every Sandbox backend now.** Rejected because the isolation, lifecycle, provider normalization, and output-safety mechanics remain bounded and behaviorally tested.

**Treat the retained package as an active target subsystem.** Rejected because no current product entry or approved owner contract constructs or governs it.

**Redesign Sandbox during G002 source disposition.** Rejected because the current task is dependency cleanup and static correctness, not a change to venue, fallback, session, lease, isolation, or publication semantics.

## Acceptance criteria

- Sandbox imports no deleted Auth, DAO, global Redis-events, Workspace facade, or target Settings authority.
- The retained package and its tests pass Ruff and Pyright without file-level ignores.
- Focused tests preserve the listed invariants and full Backend collection remains clean.
- Future activation begins with an approved owner and assembled-path tests rather than restoring deleted entrypoints.

## Risks and open questions

The future owner, product entry, secret-decoder implementation, Redis lifecycle, Workspace contract, and supported venue set remain unapproved. Provider health checks and remote execution have not been validated against live external services in this source-disposition change.
