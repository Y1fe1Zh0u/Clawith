# Agent Note: Target Agent Execution Architecture

Status: proposed — the complete clean-break target architecture is agreed as the source for implementation planning but is not implemented

## Problem

Clawith needs a simpler execution architecture that keeps human conversation responsive, delegates planned work to isolated Subagent Runs, supports User, Agent, and Group Workspaces, progressively assembles Context, normalizes Model and Tool execution, and lets product capabilities start independent Main Runs without preserving the current Runtime topology or compatibility protocols.

The target is a clean break. It does not preserve existing Run checkpoints, Tool Ledger and Lease semantics, legacy execution variants, nested Workspace roots, relationship-specific Memory, or unused product paths merely because code exists.

## Proposal

### System map

```text
Human / Session Goal / Group / Heartbeat / Trigger / A2A / Approval
                         |
                         v
                Product capability owner
                 - records Product Input
                 - selects target Agent
                 - initiates start or resume
                         |
                         v
                    Agent Runner
                 - creates Run identity
                 - owns Status and History
                 - parent-child cancellation
                         |
                         v
                      Main Run
                         |
                         v
                     Agent Loop
              +----------+-----------+
              |                      |
              v                      v
           Context               Tool System
              |                      |
              v                      +---- Task Tool ----> Subagent Run
         Model System                +---- ordinary Tools
              |                                      |
              v                                      v
      normalized Model Step                     Tool Results
              |                                      |
              +-------------------> Run History <-----+
                                      |
                                      v
                                  Run Output
                                      |
                                      v
                           initiating product capability
```

### Main Agent and Subagent

Main Agent owns human or product interaction, intent understanding, direct execution, delegation, result synthesis, requests for human input, and completion judgment. It may perform work directly or delegate through Task Tool. How it interprets a requested work method or judges unspecified work complexity belongs to Main Prompt and Tool Description rather than Agent Loop or lifecycle architecture.

Task Tool is optional and directly exposed only to Main Runs. One call accepts one or more delegated Task work descriptions and starts one Subagent Run for each accepted description. Task is a Run-scoped model working view derived from Task Tool Calls, Child Run facts, and Child Results, not a table, ID, persistent record, status, result object, planner, Workspace, execution engine, lifecycle controller, or state machine.

Subagent is a leaf executor. It inherits the parent Main Run's complete resolved Tenant, RBAC, Workspace, and ordinary Tool authorization without inheriting parent or sibling Run History. It receives Task description as Run Input, uses Todo Tool for current-Run planning, performs and verifies the work, and returns Run Result. Subagent cannot invoke Task Tool recursively.

A Subagent missing required human or product input remains Waiting and emits a correlated Child Need Input event to Main. Main Agent may answer from its Context or request human input and enter Waiting. Task Tool then resumes the exact Child Run, preserving its original input and accumulated Run History.

Main and Subagent Runs use the same Agent Runner, Agent Loop, Model System, Tool System, Status, and Run History contracts. Their role, input, Context, and Tool exposure differ.

### Agent Runner and Run lifecycle

Product capabilities initiate Main Runs using stable source identity, so retry returns the existing Run reference. Related input submission is likewise idempotent per target Run and source identity. One Main Task Tool Call submits one or more work descriptions, starts one idempotent Child Run per accepted assignment using existing Parent Run and Tool Call correlation, and returns acceptance immediately. Later calls append new delegated work rather than updating a persistent Task. Agent Runner is the only Run creator and the only Run Status and Run History writer.

Run Status is limited to Running, Waiting, Completed, Failed, Cancelled, and Interrupted. Agent Runner atomically appends explicitly related input to any non-terminal Run: Waiting becomes Running, while Running retains status and consumes the input in a later Model Step. Concurrent inputs retain commit order in Run History. Completed cannot commit over already-recorded input absent from its producing Model Step, and terminal Runs cannot be revived. Every terminal Parent Main Run outcome, including Completed, cancels active Child Runs; premature Main completion is accepted without adding a completion gate.

Agent Runner does not provide cross-Worker takeover, arbitrary execution-point recovery, generic side-effect reconciliation, or automatic replay. Lost execution ends as Interrupted; later work starts a new Run from committed facts.

### Session and product inputs

Direct Session is a human-facing conversation. Only authenticated human input creates Session Input. An explicit reply resumes its exact Waiting Main Run; every other input starts a new Main Run. Each new Main Run receives a fixed Session-history cutoff, and concurrent replies commit when ready while retaining their originating Input relation.

Group, Heartbeat, Trigger, A2A, and Approval remain independent product capabilities. Each records its own input, initiates or resumes Main Run through Agent Runner, consumes Run Output, and owns product projection and delivery. There is no global Product Event bus and no routing of non-human events through direct Session.

Heartbeat is independent from Trigger. A2A creates the receiver's independent Main Run and transfers only explicit input, never sender authorization or implicit Context. A2A Tool Calls settle with immediate acceptance; `consult` and `task_delegate` later submit correlated A2A Result Input to the exact non-terminal source Main Run, while `notify` remains one-way.

Goal mode is lightweight direct Session configuration and continuation policy. One Session stores at most one active objective, committed progress, wait condition, and relation to the existing `/goal` Session Input without a Goal table or ID. Each iteration starts a new ordinary Main Run related to that input and cutoff with bounded committed facts rather than inheriting an earlier Run History or restoring a terminal Run. `continue` completes the current iteration and starts the next immediately; Goal `wait` completes it and delays the next Run until a future condition is satisfied. Goal has no `require_user` disposition; missing human information uses ordinary Need Input, Run Status Waiting, and Resume of the same Run. `achieved` and final stopped failure use ordinary Agent Reply without new Goal-specific output types.

### Context

Context is a per-model-call sourced view with eight owner categories: Platform Instructions, Agent Identity, Product Input, Run Context, Workspace Discovery, Tool Exposure, Retrieved Content, and Model Context Profile.

Platform Instructions and executing Agent Soul are mandatory fixed instruction sources. Product owners supply bounded Product Input. Agent Runner supplies isolated Run History. Authorized Workspaces supply labeled Memory entry sections and Skill Indexes. Tool System supplies only directly exposed Tool Definitions. Retrieved content enters only through Tool Results. Model System supplies an immutable secret-free Model Context Profile; credentials and secret-bearing Provider configuration never enter Context.

Context uses a Run-scoped immutable source snapshot, current Compaction Base, and incremental event Delta. Logical segments remain Provider-neutral; Model System chooses physical order and cache controls. Compaction first removes stale high-volume Tool Results, then uses a structured derived summary, recent complete interaction tail, and coverage cursor without deleting source facts.

### Workspaces

Every User, Agent, and Group has exactly one Workspace:

```text
memory/MEMORY.md
skills/
files/
```

`MEMORY.md` begins with a compact Guide and Index entry section injected into Context; remaining content is searched and read by line range. Skill Indexes are injected and full Skill packages load on demand. `files/` has no automatic directory summary and is inspected through Workspace Tools when current work requires it.

Humans may inspect and preview authorized Workspace content but cannot mutate it directly. Authorized Agent Runs perform every Workspace create, edit, delete, move, rename, import, and cross-Workspace publication through Workspace Tools. Mutations are current-revision checked and atomic. A write lock is resource-scoped and held only for storage commit, never across model, Run, or surrounding Tool latency. Agent-Agent conflicts use semantic merge and bounded retry. Current revision is a concurrency token rather than Git history or a recovery guarantee; version retention and accidental-deletion recovery are deferred.

Soul, Heartbeat policy, Group Announcement, Session and its Goal-mode configuration, Run, Task Tool Calls, Child Run facts, Focus, Trigger, messages, credentials, permissions, Model configuration, Runtime state, revisions, locks, and audit metadata remain outside Workspace.

### Tool System

Every Builtin, MCP, product, and external Tool enters one Registry through one Definition and Executor registration. Authorization, Run-role eligibility, direct exposure, searchable exposure, scheduling, execution, and presentation remain separate concerns.

The model receives a small directly exposed Tool set plus authorized search, not the complete Registry. Main Runs directly receive Task Tool and not Todo Tool; Subagent Runs directly receive Todo Tool and cannot discover or invoke Task Tool. A2A preserves `notify`, `consult`, and `task_delegate` product intent over two technical execution semantics: one-way send and asynchronous request-result. Exact model-facing Tool shape remains implementation design.

Tool Calls and Tool Results enter Run History. Ordinary Tool failure returns a model-visible Tool Result rather than failing the Run. The target has no generic Tool Ledger, Lease, takeover, replay, reconciliation, or Progress state machine.

### Model System

Every Run fixes one Model Policy. Model System supplies Context Profile and Provider capabilities; Context owns budgeting and compression. Provider Adapter maps logical Context segments to physical requests, caching, streaming, and continuation mechanisms.

Agent Loop consumes one normalized Model Step Result. Streaming, Usage, Error, and opaque Provider Execution Metadata use separate narrow contracts. Optional Provider conversation state and caches are disposable optimizations. Required continuation metadata is persisted by Model System before Model Step settlement, replayed exactly through Waiting and resume, and removed when no longer needed or the Run becomes terminal; it never becomes Context, product truth, or Run History authority.

### Minimal Tenant and RBAC

The initial architecture retains only Tenant isolation and minimal product relationships:

```text
cross-Tenant access --> denied
User Workspace ------> human owner previews; authorized User Runs mutate
Agent Workspace -----> same-Tenant humans preview; authorized Agent Runs mutate
Group Workspace -----> active members preview; authorized Group Runs mutate
Soul / Agent config -> Tenant administrator
```

Subagent inherits Parent Main Run authorization exactly. A2A resolves receiver authorization independently. The initial implementation has no company/private/custom Agent modes, per-file ACL, directory ACL, ABAC, policy engine, relationship Workspace, or capability-token hierarchy.

Every protected operation still enforces current Tenant and basic RBAC at execution even when the model received a fixed authorization snapshot earlier. Permission grants affect only new Runs. Revocation cancels affected Running and Waiting Runs and their Child Runs before another Model Step; it does not attempt to erase already-observed Context or rewrite Run History.

### Capacity and responsiveness

The platform capacity floor is 50 simultaneously active Main and Subagent executions without control-plane or Frontend lag. API, Session intake, Context, Workspace, Streaming, browser interaction, rendering, bounded execution, backpressure, and performance evidence follow [Capacity, Performance, and Responsiveness](2026-08-28-capacity-performance-and-responsiveness.md).

### Owner documents

| Owner | Contract |
|---|---|
| Direct Session | [Direct Session Input, History, and Concurrency](2026-08-27-direct-session-input-history-and-concurrency.md) |
| Main Agent, Task, Subagent, Goal mode | [Session, Main Agent, Task, and Agent Loop Model](2026-08-27-session-main-agent-parallel-task-model.md) |
| Run lifecycle and history | [Agent Runner Lifecycle and Run History](2026-08-27-agent-runner-lifecycle-and-history.md) |
| Tool, Task Tool, Todo, A2A Tool | [Tool Registry, Execution, and Exposure](2026-08-27-tool-registry-execution-and-exposure.md) |
| User, Agent, Group Workspace | [User, Agent, and Group Workspaces](2026-08-27-user-agent-group-workspaces.md) |
| Context | [Context Source and Assembly Model](2026-08-28-context-source-and-assembly-model.md) |
| Model and Provider | [Model System and Provider Boundary](2026-08-28-model-system-provider-boundary.md) |
| Product input and output | [Product Input, Main Run, and Output Boundaries](2026-08-28-product-input-main-run-and-output-boundaries.md) |
| Capacity and Frontend responsiveness | [Capacity, Performance, and Responsiveness](2026-08-28-capacity-performance-and-responsiveness.md) |

## Alternatives considered

### Preserve the current Runtime and migrate incrementally

The accepted target removes ownership and protocol layers rather than maintaining compatibility between old and new authorities. Current checkpoint and execution compatibility is not a requirement.

### Add one global lifecycle or event bus

Session, Group, Trigger, Tool, Run, Workspace, and Model facts have independent owners. One shared bus would recreate optional-field protocols and duplicate authority.

### Make Main Agent execute every request

Long multi-step work can block or flood the human-facing context. Task Tool provides isolated leaf Subagents and bounded Results, but architecture does not force Main Agent to use it for a particular Prompt.

### Give Subagents recursive delegation

Recursive Task trees add coordination, cancellation, and Context complexity. Subagents remain leaf executors; Main Agent owns decomposition and may submit additional delegated work through later Task Tool Calls.

### Add Task or Goal state machines

Task and Todo are Run-scoped model working views. Goal mode is configuration embedded in Session plus a continuation policy. None requires an independent domain object, status state machine, lifecycle controller, or execution engine.

### Put all durable state in Workspace

Workspace stores subject-owned Memory, Skills, and Files. Product, security, execution, and operational facts remain with their owning modules.

## Acceptance criteria

- The complete target uses one Agent Runner, one Agent Loop, one Tool Registry, one Context contract, and one Model System boundary.
- Product capabilities initiate only Main Runs; one Main Task Tool Call submits one or more work descriptions, starts one Child Run per accepted description, and returns acceptance immediately.
- Child Results and Need Input signals become ordered correlated Child Inputs; Waiting Main resumes and Running Main consumes them in later Model Steps.
- A2A Tool Calls settle immediately; `notify` is one-way, while `consult` and `task_delegate` submit correlated A2A Result Input to the exact non-terminal source Main Run.
- A2A target Runs remain independent from source lifecycle, and late results cannot revive terminal source Runs.
- Main Agent may perform work directly or delegate to leaf Subagents; Prompt interpretation and complexity judgment are model behavior rather than a lifecycle rule.
- Task and Todo add no independent table, ID, persistent record, result object, state machine, Workspace, Agent role, Run type, or execution engine; Goal mode adds only lightweight Session configuration and no separate table, ID, domain object, status state machine, Reply type, projection type, or history.
- Run Status and History have one owner and no automatic replay, takeover, or arbitrary recovery.
- Run start and related-input submission are idempotent by owner-issued source identity; Task and A2A reuse existing correlation rather than adding domain IDs.
- Direct Session accepts only human input and supports concurrent Main Runs with fixed history cutoffs.
- Product capabilities retain independent input, result, projection, and delivery ownership without a shared event bus.
- Context retains source ownership, builds incrementally, preserves stable cacheable segments, and never deletes source facts during Compaction.
- User, Agent, and Group each own one Workspace with `memory/MEMORY.md`, `skills/`, and `files/`.
- Humans receive Workspace preview but no direct mutation surface; authorized Agent Runs mutate through revision-checked atomic Workspace Tools and automatically resolve Agent-Agent conflicts.
- Tool System separates registration, authorization, role eligibility, exposure, scheduling, execution, and presentation.
- Main has Task Tool, Subagent has Todo Tool, and Subagent cannot recursively delegate.
- Subagent missing input remains Waiting and notifies Main through a correlated event; Main or human supplies input and Task Tool resumes the exact Child.
- Every Run fixes one Model Policy and Agent Loop consumes only normalized Model output.
- Model System distinguishes disposable Provider optimizations from required continuation metadata and persists the required form before Model Step settlement without creating generic recovery.
- Tenant isolation and minimal owner/member RBAC are enforced at real execution boundaries.
- Permission grants affect only new Runs, while revocation cancels affected non-terminal Runs and their Child Runs without dynamic Context rewriting.
- At least 50 Agent executions remain active without control-plane, Streaming, or Frontend responsiveness falling below the linked performance contract.
- Existing checkpoints, legacy Runtime variants, compatibility protocols, and unused paths are not preserved by default.
- Each detailed contract has one linked owner document rather than copied implementations across notes.

## Risks and open questions

Implementation planning must still map current source consumers, decide exact data shapes, choose deletion and cutover order, define focused tests, research stable-source fingerprinting and Provider cache controls, and select metrics before optimization. These are implementation decisions under this target, not reasons to retain the old architecture.
