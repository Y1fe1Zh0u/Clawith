# Agent Note: Cumulative Goal Checkpoints for the Backend Rewrite

Status: proposed — the tracked checkpoint contract exists, while most Goal receipts and later E2E fixtures do not yet exist

## Problem

The clean-break Backend rewrite cannot run a complete product E2E after every intermediate change because the real Runtime and product entry paths appear only in later phases. Phase-level prose lists tests, but it does not prevent a later Goal from dropping an earlier gate, treating test collection as E2E, or replaying an approval, ledger transition, or reference-removal command whose effect already occurred. This makes “test after each Goal” ambiguous and can hide the first point at which real E2E becomes available.

## Proposal

`backend/rewrite/goal-gates.json` is the tracked G000-G009 checkpoint contract, and `backend/scripts/validate_goal_gates.py` validates its structure. The manifest is governance data, not a Runtime state machine or execution ledger. It declares repeatable validation commands, expected evidence paths, separately listed mutations, and cumulative carry-forward. A Goal passes only with fresh evidence for its own validations and every earlier Goal gate. Canonical required paths must be tracked and recoverable from Git; ignored `.omx` files may mirror the contract for live execution but cannot supply required evidence.

The E2E boundary advances monotonically. G000 is the planning gate. G001 validates Phase 0 without implementation. G002 requires architecture, static, and complete Pytest collection disposition but does not call collection E2E. G003 and G004 require schema and integration evidence. G005 is the first real-entry core Runtime E2E through a test-only Product Input owner. G006 is the first real product-input API and WebSocket E2E. G007 reruns all implemented module E2E cumulatively. G008 runs the complete Backend E2E in a fresh environment before legacy-reference removal, records removal as a mutation receipt, and reruns the fresh-environment E2E afterward. G009 reruns the complete Backend suite, deployment, final load, cleanup, and target-only recovery gates.

G003 registers the complete S0/S1 schema roster. Its dependency-ordered contract approval roster is `identity_tenant`, `credential`, Model, Agent, Permission, Audit, Workspace, Tool, Capability Market, Run, and Context. Workspace, Tool, and Capability Market are contract-only transitive prerequisites for Run and Context; their schema and services remain G004. G003's service/API implementation roster remains `identity_tenant`, `credential`, Model configuration, `agent`, `permission`, and `audit`; deferred Run and Context bring contract and schema only, and their services remain G005. G004 registers the complete S2 schema roster and adds contract approvals only for `session`, `a2a`, `group`, `trigger`, `heartbeat`, and `channel`, because the first three S2 owners carry forward from G003. Its service implementation roster remains Workspace, Tool, Capability Market, and Model execution; the six deferred product-input owners bring contract and schema only, and their services/APIs remain G006. Each new owner approval is a separate receipt-guarded mutation in dependency-safe owner-DAG order.

G001 uses repository commands to validate the actual 401-row disposition state with zero unreviewed or missing dispositions, governance, the owner DAG/wave roster, product roster and approved linkage, the strict load profile, and the immutable reference. Passing tests do not substitute for these current ledger, profile, and reference checks. Every validation ID has one exact command and artifact path. Shell composition, unknown scripts, alternate whitespace, filesystem writes, Alembic upgrade, reference binding, and build/approval/transition/release commands are outside the repeatable validation language.

G005 also requires an adversarial execution-scheduler test. After each bounded Model Step or bounded Tool batch, a still-runnable Run releases its scarce execution slot and re-enters the in-memory Tenant-then-Agent scheduler. With 50 continuously runnable, nonterminating Tenant A Runs occupying all initial slots, an eligible Tenant B Run obtains its next Model Step after at most one consecutive eligible-Tenant skip, while FIFO remains per Agent. Cancellation or failure removes the Run and releases capacity. The test does not use the initial admission queue as a substitute and does not introduce a persisted queue, checkpoint, durable scheduler state, or whole-Run limit.

Commands that build a ledger, approve a contract, transition coverage, or remove the immutable reference are mutations. Their manifest entries name a receipt and require `verify_receipt_before_execute`; operators inspect the authoritative state and receipt before deciding whether execution is still needed. Repeatable checks may be rerun freely. The validator never executes either class of command. G008 fixes the complete reference-removal mutation object: exact command, receipt, pre-removal E2E artifact, and post-removal E2E artifact. The validator binds those artifacts to the ordered before/after validation entries so removal cannot precede its fresh-environment precondition or replace the required post-removal rerun.

## Acceptance criteria

- The manifest contains exactly G000 through G009 in order and each Goal carries forward the complete earlier prefix.
- The Goal-to-phase crosswalk and E2E levels match the approved rewrite plan and never regress.
- Every canonical required authority is tracked; the validator rejects ignored `.omx` paths as required evidence.
- Validation entries contain no known build, approval, transition, or reference-removal command.
- Every mutation has a receipt path and the receipt-first replay policy.
- G003 and G004 contain the complete S0/S1 and S2 schema rosters plus their dependency-ordered new contract-approval rosters without changing service/API implementation ownership.
- G001 contains separate actual checks for disposition state, governance, owner DAG/waves, product roster/linkage, strict load profile, and immutable reference.
- Every validation ID maps to one exact non-mutating command; shell composition, unknown commands, mutation commands, Alembic upgrade, alternate whitespace, and filesystem writes fail validation.
- G005 contains the exact hostile execution-scheduler fixture and excludes admission-queue and durable-state substitutes.
- G008 names fresh-environment E2E artifacts from both sides of the reference-removal receipt.
- Positive and negative architecture tests enforce the roster, carry-forward, command separation, E2E progression, fixture paths, approval rosters, fairness fixture, and phase crosswalk.

## Alternatives considered

### Keep the checkpoint rules only in ignored OMX plans

This would preserve execution guidance but leave no tracked authority for review or CI validation. It was rejected because the rewrite gates must survive local OMX state and be enforceable from the repository.

### Store completion state in the manifest

This would combine the gate definition with mutable execution state and duplicate Ultragoal or evidence-ledger ownership. It was rejected because the repository needs a stable contract and independently produced receipts, not another lifecycle controller.

### Rerun every listed command without classifying side effects

This is safe for validation commands but unsafe for contract approvals, coverage transitions, ledger builds, and reference removal. It was rejected because those operations change authority or filesystem state and may be invalid or destructive when repeated.

## Risks and open evidence

The manifest names fixtures and receipts that later Goals must create; their presence in the contract is not evidence that those tests ran or that E2E is currently available. The tracked validator proves only governance consistency. Each Goal still needs the fresh command output, service fixtures, database state, and receipt artifacts named by its gate. The live `.omx` plans and Ultragoal files mirror this tracked authority for execution convenience but remain ignored, non-authoritative runtime artifacts.
