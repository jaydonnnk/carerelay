# ADR-0005: Server-generated idempotency keys

- **Status:** accepted
- **Date:** 2026-09-25
- **Source:** `02-architecture.md` D5, §4.1
- **Supersedes:** the revision-1 design where the client supplied the key

## Context

Invariant I3 says duplicate callbacks, replayed requests and restarts must not advance state. Networks retry, users double-tap, restarts replay.

The first revision had the **client** generate an idempotency key per request. This is a common pattern and it fails in exactly the case the invariant exists for:

> A double-tap produces **two** requests and therefore **two different keys**. The UNIQUE constraint is never hit. Two tool calls dispatch. The episode ends up holding mixed attempt state.

The invariant was declared and structurally unreachable. The round-2 review called this "surface C": the rule was satisfied on paper and violated in the only scenario that mattered.

## Decision

**The server generates one idempotency key per `(episode_id, route_id, purpose_id)`**, under a server-held secret or a collision-resistant server namespace. Clients never supply a key.

- A double-tap produces the **same** key, hits `UNIQUE`, and becomes a **no-op that is recorded** — not silently discarded.
- A **new `purpose_id` is an explicit authorised retry**, not a double-tap. This is the only way to legitimately dispatch a second request.
- The key is generated under the same check that reads the current consent version, so an attempt cannot be opened against a stale consent.
- `open_attempt_once` writes the attempt row and its audit event **atomically**.
- `consent_version` is **stamped on the attempt** and re-checked at record time. Revocation prevents further recording as success.

## Consequences

**Good**

- I3 becomes reachable. The invariant now has a mechanism rather than a declaration.
- "Retry" becomes an explicit, authorised, auditable act instead of an accident.
- The consent race is closed at the same point the key is minted.
- Distinguishing double-tap from intentional retry is a **product** decision the user makes, not a side effect of network behaviour.

**Bad / accepted debt**

- Retries are slightly less convenient: a legitimate second attempt needs a new purpose id rather than a fresh client key.
- Key derivation depends on a server-held secret or namespace, which is one more thing the demo environment must hold correctly. Misconfiguration could collapse two distinct attempts into one.
- The atomicity of `open_attempt_once` is asserted, not yet proven under concurrency.

## Reversal

**Not reversible after Slice 2.** Reverting to client-supplied keys re-creates the double-tap hole and would require reopening Gate 2's I3 discussion.
