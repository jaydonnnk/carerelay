# ADR-0004: Closure is derived, never stored

- **Status:** accepted
- **Date:** 2026-09-25
- **Source:** `02-architecture.md` D4, §4.2
- **Supersedes:** —

## Context

The product's thesis is that no failed or unacknowledged action may ever render as resolved. The obvious implementation — an `episodes.closure` column that gets set to `resolved` when everything looks fine — is exactly the design that produces false completion. Any code path, any migration, any well-meaning bug fix can write that column.

The failure this product exists to catch is also the easiest thing to build by accident.

## Decision

**Closure is a pure function, never a stored value.** There is no `closure` column.

```
derive_closure(
    attempt_projection,      # latest transition by seq, else attempted
    evidence_axis,           # none / self_reported / documented
    clinical_deadline,
    recorded_expiry_event,   # not "is it past now"
    human_acceptance_record,
    now
) -> ClosureProjection
```

Closure states:

| State | Condition |
|---|---|
| `open` | Default. Somebody still must act. |
| `closed_with_evidence` | Evidence ≥ `documented`, **or** an explicit human acceptance is recorded |
| `escalated_to_human` | Handed to a named human path, deadline still visible |
| `expired_unresolved` | Deadline passed with no evidence — a real, reportable state |

Two inputs were **missing from the first revision** and are load-bearing: `human_acceptances` and `expiry_events`. Both now have tables and endpoints.

## Consequences

**Good**

- **There is no write path that sets `resolved`.** False completion loses its easiest mechanism.
- `attempted` + evidence `none` becomes the honest rendering of "we tried and nobody said yes" — the core of the product.
- Expiry is auditable as a recorded event rather than inferred from a clock read.
- The judge ledger and the patient screen derive from the same function, so they cannot disagree about the facts.

**Bad / accepted debt**

- Every projection recomputes. Cheap here, but it means the projection code is on the critical path for correctness.
- **Derived closure does not make false completion impossible.** Gate 2 §10 restates this honestly: false completion is still reachable through **projection bugs**. Four identified paths are closed — evidence provenance (D11), expiry stickiness (D12), the transaction boundary, and simulated-label serialisation — but the claim is "four known paths closed", not "impossible".
- A pure function needs its inputs threaded through every call. The signature is wide.

## Reversal

**Not reversible.** Restoring a stored closure value would re-open the write path for false completion and invalidate the product thesis.

**Related:** ADR-0003 (append-only record) supplies the inputs; ADR-0005 keeps retries from fabricating new ones.
