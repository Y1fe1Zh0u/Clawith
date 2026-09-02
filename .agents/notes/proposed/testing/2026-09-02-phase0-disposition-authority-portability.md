# Agent Note: Phase 0 disposition authority portability

Status: proposed — the tracked authority migration and recursive coverage gate are being implemented

## Problem

Every Phase 0 coverage row cites `backend/rewrite/disposition-evidence/endpoint-lifecycle-dispositions.json`, but that evidence document cited the ignored `.omx/plans/backend-capability-coverage-matrix.md` as decision authority. The row-level hash gate proved only that the evidence JSON had not changed. A fresh clone could not recover the ignored matrix, and the canonical coverage check did not validate the authority paths or hashes inside the evidence document.

## Proposal

Keep the accepted matrix content and decisions unchanged at `backend/rewrite/backend-capability-coverage-matrix.md`. The disposition approval generator records only repository-relative authority files that exist, are not ignored, and are known to Git. The canonical coverage validator recursively checks every authority declared by the endpoint/lifecycle disposition evidence: each path remains inside the repository, exists as a file, is not ignored, is Git-tracked, and matches its recorded SHA-256.

The `.omx` matrix may remain as a non-authoritative local mirror. It cannot be cited by generated disposition evidence or satisfy the coverage gate.

## Acceptance criteria

- The tracked matrix has byte-identical content and the same SHA-256 as the former `.omx` authority.
- Regeneration changes no coverage disposition, state, owner, planned gate, immutable reference, or evidence entry other than the deterministic disposition-evidence hash.
- All 401 coverage rows remain `disposition_approved` and cite the valid regenerated evidence hash.
- Positive tests accept tracked authority content with a matching hash.
- Negative tests reject ignored paths, untracked paths, and authority hash drift.

## Alternatives considered

Keeping `.omx/plans/backend-capability-coverage-matrix.md` as authority was rejected because `.omx/` is ignored and absent from a fresh clone. Removing the matrix citation was rejected because it would discard accepted decision evidence rather than make that evidence portable. Validating only the outer disposition-evidence hash was rejected because it does not prove that nested authorities are recoverable or unchanged.

## Risks

The coverage validator invokes Git for authority portability checks. Validation deduplicates repeated evidence artifacts so the shared disposition document is checked once rather than once per coverage row.
