# Agent Note: User, Agent, and Group Workspaces

Status: proposed — the Workspace ownership, contents, progressive-loading, and minimal Tenant/RBAC model is agreed as the basis for implementation planning but is not implemented

## Problem

The target architecture needs durable files for Users, Agents, and Groups without creating a separate Workspace for every relationship or mixing product state, Runtime internals, and subject-owned content in one file tree. Memory, Skills, and ordinary work files need one consistent file capability while retaining different model-loading semantics.

The current Agent file root and its nested `workspace/` use Workspace to mean two different things. The target model needs one top-level Workspace per subject and no second nested Workspace boundary.

## Proposal

### One Workspace per subject

Every User, Agent, and Group has exactly one persistent Workspace. All three use the same fixed top-level areas:

```text
User Workspace
  ├── memory/
  ├── skills/
  └── files/

Agent Workspace
  ├── memory/
  ├── skills/
  └── files/

Group Workspace
  ├── memory/
  ├── skills/
  └── files/
```

Workspace identity is keyed only by its owning User, Agent, or Group. The architecture does not create a Workspace for each `(User, Agent)`, `(User, Group)`, Task, or other relationship. Conversation, Task Tool Call, Child Run, and other execution facts remain with Session and Run History unless an explicit operation writes selected content into a Workspace.

The same Workspace capability provides scoped list, search, read, preview, write, move, delete, current-revision conflict, and audit behavior for all three subject types. Humans receive only authorized list, search, read, and preview surfaces. Workspace mutation is available only to authorized Agent Runs through Workspace Tools. Subject type changes authorization and available content, not the basic file protocol.

### Visibility and isolation

A User Workspace is the User's one private persistent Workspace across every Agent the User authorizes. Its owner may inspect and preview it, while authorized Runs acting for that User may read and mutate it. Different Users' Workspaces are isolated.

An Agent Workspace is the Agent's shared persistent Workspace across its authorized Users and Runs. Same-Tenant authorized Users may inspect and preview the same Agent Memory, Skills, and Files rather than receiving private copies; only authorized Agent Runs mutate them.

A Group Workspace is shared within the Group. Active members may inspect and preview it, and authorized Group Runs may read and mutate it. Individual members' User Workspaces remain private and are not imported automatically.

```text
Direct Run for User U by Agent A
  ├── User U Workspace
  └── Agent A Workspace

Group Run for Group G by Agent A
  ├── Group G Workspace
  └── Agent A Workspace

Heartbeat for Agent A
  └── Agent A Workspace

A2A Main Run received by Agent B
  └── Agent B Workspace

Subagent Run created by Main Run A
  └── exactly the Workspaces authorized for Main Run A
```

Subagent Run inherits the complete resolved Workspace access of its parent Main Run. A delegated Task work description has no Workspace or persistence of its own. A2A is different: its receiving Main Run uses the receiver's own Workspace and only explicit A2A Input, never the sender's Workspaces.

### Memory

Memory initially consists of one authoritative `memory/MEMORY.md` file per Workspace. The architecture has no required structured Memory database, vector store, embedding index, relationship-specific Memory, or automatically synchronized copy.

The beginning of `MEMORY.md` contains a standard compact Guide and Index. When a Run is authorized to use that Workspace, Context injects only this entry section with an explicit User, Agent, or Group source label. The remaining content is searched and read by line range on demand.

Multiple authorized Memory Indexes remain separate. Context does not merge them into one Memory source, and search is always scoped to an explicitly authorized Workspace.

Every Memory creation, edit, deletion, Index update, and cross-Workspace copy is explicit. Agent Final Output, Run completion, delegated-work judgment, Context compaction, search, and reads do not mutate Memory implicitly.

### Skills

Skills are authoritative file packages under `skills/`. A Skill may contain instructions, workflows, scripts, templates, examples, references, and static resources. Skills describe how an Agent should perform work; they do not grant permissions, own product state, create another Agent role, or replace executable Tools.

Each Workspace exposes a compact Skill Index to authorized Runs. Complete `SKILL.md` instructions and auxiliary files are read on demand through the same Workspace file capability. A Skill activation is a current-Run fact, not another persistent copy of the Skill.

User Skills provide methods reusable across the User's authorized Agents. Agent Skills provide methods shared across that Agent's authorized Users and Runs. Group Skills provide flexible collaboration methods and shared working conventions without creating a Group Soul, hidden Group prompt, or collaboration state machine.

When a Run receives more than one Workspace, each Skill Index retains its User, Agent, or Group source. Same-named Skills from different Workspaces do not silently overwrite or merge. Context selection and precedence are defined later.

Installed Workspace Skill files are the only authority for that subject's Skill package. An Agent may use an authorized catalog, marketplace, installer, or loader Tool to discover, validate, and copy Skills into a Workspace, but that external source does not become a second store for the installed content.

### Files

`files/` contains ordinary durable work material and outputs. Its subtree is managed through Agent Workspace Tools and has no required category layout.

```text
files/
  └── arbitrary folders and files
```

Directories such as `projects/`, `reports/`, `source-code/`, `datasets/`, and `images/` are examples only. The platform does not pre-create them, treat them as product objects, or move files automatically based on type.

Generation, authorized import, and delivery are ways a file enters or leaves a Workspace, not separate persistent namespaces. Human-uploaded or externally received content remains Product Input or temporary content until an Agent explicitly writes or copies it into an authorized Workspace. User-private files belong to a User Workspace, Group-shared files belong to a Group Workspace, and Agent-shared files belong to an Agent Workspace. Cross-Workspace copy or movement is an explicit Agent publication across ownership boundaries.

Run Output and Child Result content may reference Workspace files without creating a separate Artifact store. Runtime temporary files, sandbox copies, caches, and uncommitted candidates are not Workspace content; they become durable only through an explicit write to an authorized Workspace.

### Agent-only mutation and concurrency

Workspace Tools are the only mutation boundary for `memory/`, `skills/`, and `files/`; Agent Runs do not bypass them to modify underlying storage, and human product surfaces expose no direct mutation operation. Every readable mutable resource has a logical current revision. An Agent mutation supplies the revision it was based on, and Workspace commits only when that revision is still current.

```text
read content + revision
        |
        v
Agent prepares mutation without holding a lock
        |
        v
atomic commit if revision still matches
        |
        +---- success ----> new revision
        |
        `---- conflict ---> latest revision ---> Agent rereads, merges, and retries
```

Workspace uses only a short resource-scoped write lock while validating and atomically committing one mutation. No lock extends beyond that storage commit into model execution, the surrounding Tool operation, a Run, or another external operation. Readers observe either the complete earlier revision or the complete committed revision and never a partial write.

A revision conflict means another Agent committed first. It is a model-visible Workspace Tool Result, not human Need Input. The executing Agent reads the latest content, semantically combines the concurrent Agent change with its intended change, and retries against the new revision. Workspace does not apply silent last-write-wins, discard either accepted change, or guess a generic text merge. The Agent must not persist unresolved conflict markers as a successful merge.

Automatic resolution is bounded so sustained contention cannot create an infinite retry loop. If repeated conflicts prevent convergence, the Agent chooses a non-destructive resolution that preserves the competing content, such as producing a separate candidate for a non-mergeable resource, and reports the resulting file relation in its normal Run Result. Conflict handling never pauses for a human merge decision and never overwrites a newer revision silently.

Create, delete, move, and rename operations apply equivalent revision checks to the affected resource and namespace. A multi-file Skill installation or update is staged and published atomically as one package so another Run cannot observe a partially updated Skill. Current revision is a compare-and-swap concurrency token, not a Git commit, retained version history, branch, snapshot, recycle bin, or recovery guarantee. The concrete revision representation, storage lock, retry bound, and merge prompt remain implementation decisions; version retention, backup, and accidental-deletion recovery are deferred product decisions.

### Product configuration stays outside Workspace

Workspace is not a file serialization of every subject or Runtime fact. Product configuration and lifecycle state remain with their owning modules.

```text
User product object  ----> Profile and identity
Agent product object ----> Soul
Group product object ----> Announcement and Group settings
Heartbeat module --------> Heartbeat policy and scheduling
```

Soul is mandatory Agent identity and behavior configuration. It is loaded by Context for every Agent model call, cannot be modified by the Agent, and is edited only through an authorized Agent-management operation. It may use Markdown internally but is not exposed through Workspace file operations.

Group Announcement is public Group product content, not Group Soul, Memory, or Skill. Long-term Group knowledge belongs in Group Memory, and flexible collaboration behavior belongs in Group Skills.

Session and its Goal-mode configuration, Task Tool Calls, Child Run facts, Run History, Focus, Trigger, Schedule, messages, credentials, permissions, model configuration, checkpoints, Runtime state, file revisions, locks, audit metadata, and reconciliation data remain outside Workspace even when their implementations use persistence.

### Minimal Tenant and RBAC boundary

Workspace authorization uses only the existing product relationships needed for the first implementation:

```text
Tenant boundary
  - cross-Tenant access is denied

User Workspace
  - owned by that User
  - human owner may list, search, read, and preview
  - authorized Runs acting for that User may read and mutate

Agent Workspace
  - same-Tenant authorized humans may list, search, read, and preview
  - authorized Agent Runs may read and mutate
  - Soul and Agent product configuration remain Tenant-admin operations

Group Workspace
  - active members may list, search, read, and preview
  - authorized Group Runs may read and mutate
```

Subagent Runs inherit the parent Main Run's resolved Workspace access exactly. A2A resolves the receiver's own Tenant and Workspace access and never inherits the sender's. The initial architecture has no company/private/custom Agent modes, per-file ACL, directory ACL, ABAC, policy engine, or capability-token hierarchy. More granular policy requires a later product decision.

Newly granted Workspace authorization affects only new Runs. When User, Agent, Group, or Tenant authorization required by a Running or Waiting Run is revoked, the permission owner cancels that Run through Agent Runner, which also cancels its active Child Runs. Workspace does not attempt to remove already-observed Index content from model Context or rewrite Run History.

The initial product exposes no human Workspace create, edit, delete, move, or rename operation. A human changes Workspace content by instructing an Agent, which performs the authorized mutation through Workspace Tools. Concurrent Agent mutation uses revision checks and Agent-managed merge without introducing another permission layer.

## Alternatives considered

### Create a Workspace for every User-Agent relationship

This multiplies state with every relationship, fragments one User's continuity across Agents, and requires ambiguous merge and precedence rules. One Workspace per subject preserves continuity without combinatorial storage.

### Keep a subject root plus a nested workspace directory

Two Workspace meanings make path ownership and Tool behavior unclear. The subject Workspace is the only root; ordinary files live under `files/`.

### Store Memory, Skills, and Files in separate persistence systems

All three are subject-owned files and benefit from one file capability. Their different Context and behavior semantics are expressed by their fixed top-level areas rather than duplicate storage and mutation protocols.

### Put Soul, Heartbeat, Announcement, and product state in Workspace

These facts drive identity, product behavior, scheduling, or lifecycle and have independent owners. File placement for convenient editing would create competing authorities and allow general Workspace mutation to change protected product behavior.

### Write Memory automatically when work ends

Automatic summarization can persist incorrect conclusions or move private information into shared Workspaces. Memory changes remain explicit Tool or product actions.

## Acceptance criteria

- Every User, Agent, and Group has exactly one persistent Workspace.
- No Workspace is created for a User-Agent or other relationship pair.
- Every Workspace has fixed `memory/`, `skills/`, and `files/` areas and no nested second Workspace boundary.
- User Workspaces are isolated from other Users and remain continuous across authorized Agents.
- Agent Workspaces are shared across the Agent's authorized Users and Runs.
- Group Workspaces are shared within the Group without importing members' User Workspaces.
- Memory initially consists of one `memory/MEMORY.md` per Workspace; only its labeled Guide and Index entry section is injected automatically and all other content requires scoped search and read.
- Skills are authoritative Workspace file packages; only their labeled Index is injected automatically and full instructions and resources are read on demand.
- User, Agent, and Group Memory and Skill Indexes remain separate and retain source identity.
- `files/` is an arbitrary durable file tree; uploads and outputs do not create additional persistent namespaces or a separate Artifact store.
- Authorized humans may inspect and preview Workspace content but cannot mutate it directly; all Workspace mutations come from authorized Agent Runs through Workspace Tools.
- Every Workspace mutation and cross-Workspace publication is explicit and authorized.
- Every mutable Workspace resource uses revision-checked atomic mutation; locks remain resource-scoped and cover only storage commit rather than model, Run, or surrounding Tool latency.
- Agent-Agent Workspace conflicts are resolved automatically by the executing Agent through latest-content semantic merge and bounded retry, never by silent last-write-wins or human conflict handling.
- Repeated contention preserves competing content through a non-destructive Agent-selected result rather than overwriting a newer revision or persisting unresolved conflict markers.
- Multi-file Skill installation and update publish one complete package atomically.
- Soul, Heartbeat, Announcement, product state, Runtime state, and operational metadata remain outside Workspace with their owning modules.
- Workspace authorization uses Tenant isolation, User ownership, Tenant membership for Agent Workspace, and active Group membership only; these relations grant humans preview access and authorized Runs mutation access without a relationship Workspace or fine-grained file policy.
- Workspace permission grants affect only new Runs; revocation cancels affected non-terminal Runs and their Child Runs rather than dynamically editing Context.
- Permission detail beyond the accepted minimal Tenant/RBAC model, Context precedence, and concrete file APIs remain later product or implementation decisions.

## Risks and open questions

Subagent Runs inherit their parent Main Run's resolved Workspace permissions exactly. Concrete authorization queries must implement the accepted Tenant, User-owner, Tenant-member, and Group-member rules without adding relationship Workspaces or finer ACLs.

Context must preserve source identity when same-named Skills or conflicting Memory appear in multiple authorized Workspaces. Any permission model beyond the minimal Tenant, owner, and membership rules requires a later product decision.

The implementation must choose current-revision, atomic-commit, bounded-retry, and package-publication mechanisms that preserve these semantics across every Agent process that may mutate the same Workspace. This choice must not turn model latency into lock duration or require human conflict resolution. Retained version history and accidental-deletion recovery are not part of the initial Workspace contract.
