# Agent Note: Agent Runner Lifecycle and Run History

Status: proposed — the Agent Runner boundary is agreed but not implemented

## Problem

Main Runs and Subagent Runs use the same Agent Loop but need one execution boundary for identity, non-blocking start, waiting, resume, cancellation, status, parent-child relationships, and isolated history. Agent Runner must remain narrower than a conventional durable Runtime and must not absorb product routing, parent-requirement judgment, Context, Model, Tool, Memory, Workspace, or delivery ownership.

## Proposal

### Agent Runner

Agent Runner is the common execution and lifecycle entry for every Run. It may be an application module and does not require a separately deployed service.

```text
Product capability ----> Agent Runner ----> Main Run

Main Run Task Tool ----> Agent Runner ----> Subagent Run
```

Agent Runner creates Run identity, invokes Agent Loop, owns Run Status and Run History, records parent-child Run relationships, routes Main Run outcomes to the initiating product capability, routes Subagent outcomes to the responsible Main Run as correlated Child Result Inputs, and releases execution resources. It does not interpret product input or delegated work descriptions, judge parent-requirement or Goal completion, assemble Context, select a model, register or execute Tools, manage Workspace facts, or deliver product messages.

### Initiation and creation

The owning product capability initiates a Main Run and supplies Run Input. A Main Agent may call Task Tool; its concrete Executor requests Agent Runner to create one Subagent Run per accepted delegated work description. Each Child Run Input contains that description, and its resolved authorization scope exactly matches the parent Main Run. Agent Runner remains the only Run creator.

Product source and output ownership follow [Product Input, Main Run, and Output Boundaries](2026-08-28-product-input-main-run-and-output-boundaries.md); Agent Runner consumes only the shared execution contract.

```text
Human or Goal continuation
  └── Session initiates Main Run
        └── Agent Runner creates Main Run

Group, Heartbeat, Trigger, A2A, or other product input
  └── owning product capability initiates Main Run
        └── Agent Runner creates Main Run

Main Run calls Task Tool
  └── Task Tool Executor requests Subagent Run
        └── Agent Runner creates Subagent Run related to parent Main Run
```

No external or product input enters a Subagent Run directly. Task is only the Run-scoped delegated work description carried by Task Tool into Child Run Input; it is not an initiator, record, identifier, or lifecycle actor.

Only Main Runs may request Subagent Runs through Task Tool. Agent Runner rejects a Subagent-originated recursive creation request even if ordinary business authorization is otherwise inherited.

### Minimal operations and non-blocking execution

Agent Runner supports three conceptual operations:

```text
start
resume
cancel
```

`start` creates a Run for one initiator-owned source identity and returns its reference without waiting for Agent Loop to finish. Repeating `start` with the same initiator and source identity returns the existing Run reference rather than creating another Run. `resume` submits one explicitly related input with its owner-issued source identity to an existing non-terminal Run; the input may be a human reply, correlated Child Result or Need Input, correlated A2A Result Input, Approval result, or another authorized product input. If the Run is Waiting, Agent Runner records the input, changes it to Running, and schedules Agent Loop. If the Run is already Running, Agent Runner records the input without changing status, and Context includes it in the next Model Step Delta. `cancel` applies one authorized cancellation request from a product owner, User, administrator, permission owner, or other valid caller to the target Run.

Agent Runner atomically serializes related-input commits per Run and appends concurrent inputs in commit order. For one target Run, the same source identity is accepted at most once; a duplicate submission returns the already-accepted outcome without another History entry, status transition, or scheduling action. Run History and the existing model-view cursor are the pending-input and deduplication record; there is no separate input queue, idempotency table, or event bus. A terminal Run rejects new input for execution. The source owner retains a late result according to its own product contract, but the result cannot revive the Run.

One product owner may start multiple Main Runs independently. One Main Run may have multiple active Subagent Runs created through Task Tool. Product code or a Tool Executor may subscribe to output, wait for an outcome, or acknowledge start immediately without changing Run lifecycle ownership.

### Run Status

Run Status contains only execution lifecycle:

```text
Running
Waiting
Completed
Failed
Cancelled
Interrupted
```

```text
Running
   +---- Main Run Need Input ----------> Waiting ---- resume ----> Running
   +---- Subagent Need Input ----------> Waiting ---- resume ----> Running
   +---- child Result received --------> Running
   +---- Final Output -----------------> Completed
   +---- unrecoverable error ----------> Failed
   +---- explicit cancel --------------> Cancelled
   +---- execution lost ---------------> Interrupted
```

Waiting is non-terminal. Completed, Failed, Cancelled, and Interrupted are terminal. Task, Todo, and Goal do not add lifecycle states to Run Status.

Agent Runner also serializes input commit with terminal outcome commit. Completed cannot commit from a Final Output produced before an already-committed related input was included in a Model Step; Agent Loop continues with that input instead. If Completed, Failed, Cancelled, or Interrupted commits first, a later input cannot change the terminal status. Explicit cancellation and unrecoverable failure may terminate a Run even when unconsumed inputs remain.

A Subagent uses Waiting for missing human or product input and preserves its Run History. Agent Runner submits a correlated Child Need Input to the responsible Main Run without completing the Child. Main may answer immediately or enter its own Waiting state while obtaining human input.

Agent Runner is the only Run Status writer. It records structured Agent Loop events and explicit cancellation or execution-loss facts. Ordinary Tool errors return Tool Results to Agent Loop and do not directly fail the Run.

### Run History

Agent Runner uniquely owns Run History:

```text
Run Input
model-visible messages
Tool Calls
Tool Results
Waiting requests and related input
Run outcome
```

Delegated work descriptions appear in the parent Task Tool Call and Child Run Input. Task Tool acceptance appears as the immediate Tool Result. Later Subagent outcomes remain in Child Run History and enter Parent Run History as correlated Child Inputs whether Parent is Running or Waiting. Task and Todo do not create separate execution histories.

Agent Loop submits execution events; Agent Runner writes them. Context reads the exact Run History it is assembling. Product capabilities and delegated-work UI views may reference or project Run outcomes but do not become alternative Run History writers.

Run History is an execution and audit record, not a Checkpoint of process, coroutine, network connection, model request, or in-flight Tool implementation state.

### Isolation and explicit Context access

Every Run has isolated history. Context receives an explicit Run identity and authorized source set; it never queries a global current Run or implicitly merges concurrent histories.

A Subagent Run receives its delegated work description, its own history, and the complete resolved authorization and Workspace access of its parent Main Run. Inheriting authorization does not copy model-visible context: the Subagent Run does not automatically read its parent or sibling Run History.

The parent Main Run receives a Child outcome only as a correlated Child Result Input. An A2A source Main Run receives target output only as a correlated A2A Result Input owned by A2A. Another Run's private history becomes visible only through an explicit Run Result, Session fact, Workspace file, or another authorized source.

The initiating Session supplies the fixed history cutoff defined by [Direct Session Input, History, and Concurrency](2026-08-27-direct-session-input-history-and-concurrency.md). Context may rebuild from that cutoff but cannot enlarge it implicitly.

### Waiting, parent termination, and interruption

Waiting pauses only one Run and releases its execution resources. A Main Run may wait for one or more Subagent Run outcomes without blocking Session or unrelated Runs.

When a Subagent Run completes, Agent Runner uses its parent-child relation to submit a Child Result Input containing the Child Run reference and outcome to the responsible Main Run. It resumes a Waiting Main Run or remains ordered in a Running Main Run's History for the next Model Step. The originating Task Tool Call was already settled by acceptance; no Task record routes or stores the outcome.

When a Child Need Input event occurs, Agent Runner submits it to the responsible Main Run while leaving the Child Waiting. A later Task Tool resume operation supplies the answer to the exact Child Run, which continues with its existing History. Any terminal Parent outcome still cancels the Waiting Child.

If a parent Main Run becomes Completed, Failed, Cancelled, or Interrupted, Agent Runner cancels its still-active Subagent Runs. Completed does not wait for Child completion and adds no completion gate; if Main finishes prematurely, that execution error is accepted and its abandoned Child work is cancelled. A late Child outcome may remain recorded but cannot revive the parent or settle new work.

When the permission owner revokes authorization required by a Running or Waiting Run, it requests cancellation through Agent Runner. Agent Runner cancels that Run and propagates cancellation to its active Child Runs. Permission grant never resumes or expands an existing Run; later work starts a new Run with newly resolved authorization.

An A2A target Main Run is not a Child Run of its source. Source Main Run failure, cancellation, interruption, or completion therefore does not cancel the target. A2A may submit a correlated result only to the exact non-terminal source Main Run; Agent Runner resumes it if Waiting or appends the result for its next Model Step if Running. Agent Runner rejects attempts to resume a terminal source Run.

Failed means Agent Runner received a structured unrecoverable execution error while the execution boundary remained alive. Interrupted means the execution process disappeared without a normal outcome. Agent Runner does not replay or reconstruct lost model requests, Tool Calls, process state, or code execution points.

A structured Model Error reporting missing or uncommitted required Provider continuation metadata makes the Run Failed. If execution disappears before a Model Step and its required metadata are committed, the Run becomes Interrupted. Agent Runner does not reconstruct either case from Run History because Provider execution metadata is owned by Model System and is not a replayable Checkpoint.

### No durable execution layer

Agent Runner does not implement a Durable Coordinator, cross-Worker takeover, arbitrary-execution-point Checkpoint recovery, Lease ownership, or generic side-effect reconciliation. A future Run may use committed facts from prior work without reviving that execution.

## Alternatives considered

### Let product capabilities or Tool Executors invoke Agent Loop directly

They would duplicate Run creation, waiting, cancellation, status, and history protocols. All execution enters through Agent Runner.

### Let Task own Subagent Run lifecycle

Task is only a Run-scoped work description. Main Agent decides delegation and parent-requirement completion through ordinary model behavior; Agent Runner owns every Run lifecycle.

### Put Run lifecycle inside Agent Loop

This would couple the model-and-Tool loop to scheduling, persistence, product ownership, and Run management.

### Give Main and Subagent Runs separate history stores

This would split one execution contract and make Context depend on role-specific persistence. Both use one Run History contract.

### Use a conventional durable Agent Runtime

That would reintroduce takeover, arbitrary Checkpoints, Leases, and recovery policy excluded by the accepted failure model.

## Acceptance criteria

- Product capabilities initiate Main Runs, Task Tool Executor requests Subagent Runs on behalf of Main Runs, and Agent Runner is the only Run creator.
- External and product inputs enter only Main Runs; Subagent Runs start only through Task Tool.
- Only Main Runs may invoke Task Tool; Subagent Runs are leaf executions and cannot create descendant Runs recursively.
- Delegated Task descriptions are carried by Tool Calls and Child Run Input and do not create another ID, persistent record, execution history, result object, or lifecycle state machine.
- A Subagent Run inherits its parent Main Run's complete resolved authorization and Workspace access without inheriting parent or sibling Run History.
- Main Runs and Subagent Runs use the same Agent Runner, Agent Loop, Status, and History contracts.
- Agent Runner exposes conceptual start, resume, and cancel operations.
- Start is non-blocking and returns a Run reference before execution completes.
- Start is idempotent for one initiator-owned source identity and returns the existing Run reference on duplicate submission.
- Resume atomically records related input for any non-terminal Run; Waiting becomes Running, while Running keeps its status and consumes the input in a later Model Step.
- Related input is idempotent per target Run and owner-issued source identity; duplicates do not append History or schedule execution again.
- Concurrent related inputs retain Agent Runner commit order in Run History without a separate pending-input queue.
- Completed cannot commit over already-recorded input that was absent from its producing Model Step; terminal status committed first cannot be revived by later input.
- Run Status is limited to Running, Waiting, Completed, Failed, Cancelled, and Interrupted until a real execution consumer requires another state.
- Agent Runner is the only Run Status and Run History writer.
- Run Histories are isolated and Context receives an explicit Run identity and authorized source set.
- Task Tool Calls settle immediately with acceptance; later Child outcomes become correlated Child Inputs for Parent Main Runs without a Task object or another lifecycle owner.
- Subagent Need Input is a non-terminal correlated Child event; Main may wait for human input and later resume the exact same Waiting Child through Task Tool.
- Every terminal Parent outcome, including Completed, cancels active Child Runs without a completion gate, replay, or revival.
- Permission revocation cancels affected Running and Waiting Runs and their Child Runs; permission grant changes only newly started Runs.
- Agent Runner contains no Goal or Task state machine, Durable Coordinator, cross-Worker takeover, arbitrary Checkpoint recovery, Lease, or generic reconciliation protocol.
- Agent Runner does not own Session, parent-requirement judgment, Goal continuation policy, Context, Model, Tool, Workspace, or product-delivery facts.

## Risks and open questions

Exact APIs, storage schema, parent-child correlation fields, Task Tool settlement, cancellation propagation, streaming subscription, admission limits, and future queue behavior remain implementation decisions.

Concurrent Main Runs intentionally observe fixed Session cutoffs supplied by their initiating inputs. Context must preserve those cutoffs and source attribution without merging private Run histories implicitly.
