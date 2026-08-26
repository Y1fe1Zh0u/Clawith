# Agent Note: Atlassian Credential and Tool-Sync Boundary

Status: implemented — Atlassian credentials and assigned tools share one fail-closed persistence contract.

## Problem

Atlassian configuration spans the owning `ChannelConfig`, discovered shared `Tool` records, per-Agent assignments, and runtime credential dispatch. Persisting plaintext credentials, accepting undecryptable values as legacy plaintext, or committing those records independently would expose a secret at rest, dispatch ciphertext as a credential, or publish configuration success without matching tool assignments.

## Decision

`ChannelConfig.app_secret` and every Atlassian `AgentTool.config["api_key"]` value are encrypted before persistence. Runtime dispatch ignores credential values merged from Tool and AgentTool records and obtains the decrypted key transiently through the strict Atlassian credential reader. Missing or corrupt ciphertext fails before provider dispatch with an explicit configuration failure.

Atlassian discovery, Tool upsert, AgentTool assignment, and ChannelConfig mutation reuse the request's `AsyncSession`. The route owns the single commit after synchronization succeeds. Missing credentials, discovery failure, empty discovery results, encryption failure, or persistence failure cannot return configuration success; the request rolls back instead. Atlassian configuration routes await this operation directly and do not create unowned background tasks.

Deleting either Atlassian configuration surface removes the owning `ChannelConfig` and that Agent's Atlassian `AgentTool` assignments in the same transaction. Shared `Tool` discovery records remain available for other Agents. Cleanup failure rolls back both sides, so configuration deletion cannot leave an enabled orphan assignment.

Deployments that may contain pre-fix AgentTool secrets use `scripts/remove_legacy_atlassian_agent_tool_secrets.py`. The out-of-band job defaults to dry-run, processes Atlassian assignments in bounded batches, and removes only `api_key` and `atlassian_api_key` from assignment config. It is idempotent and preserves unrelated config and shared Tool records. Applying the cleanup is intentionally irreversible because legacy plaintext and corrupt ciphertext cannot be distinguished or restored safely; the authoritative encrypted ChannelConfig is retained.

## Alternatives considered

- Preserve background synchronization and report eventual status separately. Rejected because no durable synchronization object or consumer currently owns that lifecycle.
- Keep AgentTool credentials in plaintext as a runtime fallback. Rejected because it duplicates the ChannelConfig authority and exposes secrets at rest.
- Treat decryption failure as legacy plaintext. Rejected because corrupt ciphertext and plaintext cannot be distinguished safely at the dispatch boundary.

## Consequences

Atlassian configuration may take as long as provider discovery, but success means the encrypted configuration and assigned tools committed together. Provider unavailability is visible as an HTTP failure and does not publish partial configuration state. Removing configuration also removes only the requesting Agent's assignments; shared Tool records and other Agents' assignments are preserved. Other MCP providers retain their existing credential contracts.

## Verification

Regression coverage verifies missing-key rejection before database work, encrypted AgentTool persistence, shared-session sync before the single commit, rollback on synchronization failure, corrupt-ciphertext rejection before MCP dispatch, atomic assignment cleanup through both deletion routes, and dry-run/idempotent/rollback behavior for legacy-row cleanup. Backend Pyright and the focused Atlassian, dynamic MCP, and LLM capability tests must remain green.
