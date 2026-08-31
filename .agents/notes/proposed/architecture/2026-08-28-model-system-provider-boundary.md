# Agent Note: Model System and Provider Boundary

Status: proposed — the fixed-Model, Context-profile, Provider-adapter, and normalized-output boundaries are agreed but not implemented

## Problem

Agent Loop and Context need one model contract without branching on OpenAI, Anthropic, Gemini, or another Provider. Model selection, credentials, context limits, request encoding, cache controls, streaming, usage, errors, and Provider continuation features have different wire formats and must not leak into product, Tool, or Run semantics.

## Proposal

### Fixed Model Policy per Run

Run creation resolves and fixes one Model Policy containing the selected Model, Provider, model capability profile, and base request settings. Every Model Step in that Run, including after Waiting and resume, uses the same policy. Agent or platform configuration changes affect only new Runs.

Transient retry against the same fixed Model does not change this rule. Cross-Model or cross-Provider fallback is a separate failure-policy decision and is not part of normal resolution.

### Model Context Profile

Model System supplies Context with an immutable Model Context Profile containing the model facts required for budgeting and assembly:

```text
Model identity and Provider
context window
maximum output capability
resolved secret-free User, Agent, or Tenant behavior settings
reasoning and output settings
token counting or estimation behavior
Tool, image, file, and request-overhead rules
supported caching, compaction, streaming, and continuation capabilities
```

The Model Context Profile never contains credentials, credential references, access tokens, authorization headers, Provider endpoints, secret-store locations, or raw Provider configuration. Those facts remain private to Model System and are not model-visible Context or Run facts.

Context calculates effective input budget, source allocation, retained history, Compaction thresholds, and final model view. Model System does not choose which Session, Run, Memory, Skill, File, or Tool Result content to omit because those semantics belong to Context and their source owners.

Before sending, Model System validates the assembled request against hard model and Provider limits. It returns a normalized budget or capability error rather than silently truncating or changing Context.

### Provider Adapter

Context supplies Provider-neutral logical segments. Model System Adapter maps them to each Provider's physical request order, message roles, Tool schema format, cache hierarchy, and continuation mechanism.

```text
Context logical segments -----+
                               +----> Model System Adapter
Model System secret resolution-+        - Provider request encoding
                                        - credentials
                                        - cache controls
                                        - continuation metadata
                                        - streaming transport
```

Provider data is not one durability class. Prompt caches, KV caches, and replaceable conversation references are optional optimizations when the Adapter can reconstruct a valid request from Clawith Context and Run History. Opaque reasoning, thinking, response, signature, or continuation items are required execution state when the fixed Model cannot accept the next request without exact replay. Neither class becomes product truth or replaces Run History.

### Normalized Model Step Result

Agent Loop consumes one Provider-neutral Model Step Result:

```text
Assistant Content
Tool Calls
Finish Reason
normalized usage reference
normalized error or success
```

Tool Calls retain stable call identity and normalized input. Agent Loop forwards them to Tool System. Provider raw JSON, SDK objects, internal error text, credentials, and Provider-specific continuation items do not cross this boundary.

Other consumers receive separate narrow contracts:

```text
Agent Loop ----------> Model Step Result
Streaming observer --> Model Stream Events
Usage and quota -----> Model Usage Record
Failure handling ----> Model Error
Provider Adapter ----> internal Provider Execution Metadata store
```

No universal response object serves all consumers.

### Streaming and finality

Streaming Delta is a transport and presentation projection. Model System normalizes visible stream events for observers, but Agent Loop settles only from the complete normalized Model Step Result. Partial deltas do not become an alternate Model Output or independent Run fact.

### Provider execution metadata

Each Provider Adapter classifies returned Provider Execution Metadata as required continuation state or optional optimization according to the fixed Model's actual next-request contract. Unknown data is not assumed disposable when the Provider requires it for a supported continuation path.

Required continuation state is correlated to its Run and Model Step, stored by Model System before the normalized Model Step Result is released to Agent Loop, and replayed exactly on the next applicable Provider request. It survives ordinary Waiting and resume for that Run. Model System treats it as opaque and confidential: it does not enter model-visible Context, ordinary Run History content, Tool Results, Workspace, Frontend state, or ordinary logs.

The Model Step does not settle and its Tool Calls do not execute until required metadata has been committed. A known persistence failure or later detected missing required item returns a structured unrecoverable Model Error and the Run becomes Failed. If the execution disappears before the Model Step and required metadata are committed, Agent Runner records Interrupted under its normal execution-loss rule. Neither case permits reconstructed replay or revival of that Run; later work starts a new Run from committed product and Workspace facts.

Optional Provider metadata may be discarded whenever the Adapter can rebuild a correct request from the fixed Model Policy, Context, and Run History. Losing it may reduce cache reuse or performance but cannot change the semantic outcome or erase Clawith facts.

Model System removes Provider Execution Metadata when it is no longer required for a later Model Step or when the Run becomes terminal, subject to the platform's audit and retention policy. This narrow per-Run storage does not create a generic Checkpoint, Provider-owned Run History, cross-Worker takeover, Tool replay, or side-effect recovery protocol.

### Ownership boundaries

Model System owns Model resolution, Provider adapters, credentials, capability profiles, request parameters, physical request encoding, Provider caching, required Provider Execution Metadata persistence and cleanup, streaming transport, normalized usage, and Provider error mapping.

It does not own Platform Instruction content, Soul, Product Input, Run History, Context source selection, Tool registration or execution, Task or Goal judgment, Workspace, Session or Group output, or Channel delivery.

## Alternatives considered

### Let Agent Loop call Provider SDKs directly

This would duplicate Provider conditions throughout the execution loop and make every new Provider a Runtime refactor.

### Let Model System choose Context content

Model System knows token and request constraints but not the ownership or semantic importance of Session, Run, Memory, Skill, File, and Tool facts. It supplies the profile; Context chooses the view.

### Re-resolve Model on every step

Mid-Run configuration changes would alter context budget, Tool behavior, caching, and output semantics. Model Policy remains fixed for one Run.

### Use Provider state as Run History

Provider state is opaque and incomplete as an execution audit record. Clawith keeps its own Run History. Required Provider Execution Metadata is stored only to continue the fixed Model correctly, while optional cache state remains disposable; neither becomes Run History authority.

### Return raw Provider responses to every consumer

Agent Loop, streaming, usage, and failure handling need different narrow contracts. Raw responses stay inside the Adapter.

## Acceptance criteria

- Every Run fixes one Model Policy and uses it through Waiting and resume.
- Model configuration changes affect only new Runs.
- Context receives an immutable Model Context Profile and owns budgeting, source selection, and Compaction.
- Model Context Profile is secret-free; credentials and secret-bearing Provider configuration remain inside Model System and are applied only by Provider Adapter during request transport.
- Model System validates hard request limits and never silently truncates Context.
- Provider Adapter maps logical Context segments to Provider-specific request format and caching.
- Provider Adapter distinguishes required continuation state from optional optimization metadata; neither replaces Run History.
- Required Provider Execution Metadata is committed before Model Step settlement, survives Waiting and resume, replays exactly, and is removed when no longer needed or the Run becomes terminal.
- Missing required metadata fails the current Run without reconstructed replay; optional metadata loss may reduce performance but not correctness.
- Agent Loop consumes only a normalized Model Step Result.
- Streaming, Usage, Error, and Provider Execution Metadata use separate narrow contracts.
- Tool Calls retain normalized stable call identity before entering Tool System.
- Partial Streaming Deltas do not settle Model or Run outcome.
- Raw Provider responses, credentials, credential references, endpoints, SDK objects, and internal errors do not leave Model System.
- Retry and cross-Model fallback remain separate failure-policy design.

## Risks and open questions

Exact Model Policy fields, token estimators, request parameters, Provider capability matrices, cache controls, continuation storage representation and retention, retry classification, fallback, usage schema, and error taxonomy remain implementation decisions.
