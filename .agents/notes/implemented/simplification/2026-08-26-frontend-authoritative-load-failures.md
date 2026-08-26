# Agent Note: Frontend authoritative loads fail visibly

Status: implemented — configuration and platform metric reads no longer turn failures into editable defaults or empty successful data.

## Problem

Several Frontend administration views treated failed HTTP requests or invalid responses as empty data. Platform settings, tenant quotas, and company introductions could therefore appear editable with default or blank values before the Backend's authoritative state was known. Platform metric refreshes could also replace previously loaded data with empty values.

## Decision

Administration forms that can write configuration remain disabled until every required read succeeds. Read failures are visible and retryable, and save handlers independently reject writes while their authoritative load is unavailable.

Platform metric transport and response parsing belong to the service layer. The service rejects HTTP and schema failures. The dashboard reports the failure while retaining previously loaded metric data.

## Alternatives considered

**Keep silent defaults and rely on save errors.** Rejected because a valid save can overwrite authoritative values that the user never loaded.

**Clear dashboard data on every failed refresh.** Rejected because it makes a transient failure indistinguishable from a real zero-data result.

**Keep metric parsing in the page.** Rejected because authentication, transport, and external response validation belong to the service boundary.

## Consequences

Configuration pages may be temporarily read-only and show a retry action when Backend state is unavailable. Previously loaded platform metrics remain visible during a failed refresh, together with an explicit error. Response parsers reject incomplete payloads instead of partially rendering them.

Verification includes positive and negative parser tests, source-contract guards for save gating and failure retention, the complete Frontend test suite, ESLint, TypeScript, Prettier, and the production build. Browser interaction was not separately exercised.
