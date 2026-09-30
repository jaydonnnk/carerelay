# ADR-0003: An append-only clinical record with no mutable status column

- **Status:** accepted
- **Date:** 2026-09-25
- **Source:** `02-architecture.md` D3, §4.1 (revision 2)
- **Supersedes:** the revision-1 `attempts` table with a mutable `status` enum

## Context

The first architecture revision declared `attempts` **INSERT-only** and gave it a mutable `status` enum, deduped on a `UNIQUE` idempotency key.

Those two facts cannot both be true. When a clinic acknowledged a request, the acknowledgement had nowhere to go:

- An `UPDATE` violated the append-only claim.
- An `INSERT` of a second row was swallowed silently by `ON CONFLICT DO NOTHING`.

The acknowledgement would be **lost**. The patient would continue to see "help is not arranged" while the clinic had in fact accepted — a **false negative completion**, a state the product had no rule for. Four of the seven seeded fault sequences were unwritable as a direct result.

Separately, the immutable clinical deadline (invariant I1) rests on the claim that no retry path can move it.

## Decision

**Split attempt state into an immutable identity row plus append-only transitions.**

| Table | Shape |
|---|---|
| `attempts` | Immutable identity. One row per attempt, written once. id, episode_id, route_id, `idempotency_key` UNIQUE, consent_version, opened_at. **No status column.** |
| `attempt_transitions` | Append-only. id, attempt_id, monotonic `seq`, transition (`acknowledged`/`failed`/`superseded`), origin (`platform`/`local-sim`), payload, recorded_at. |
| `callbacks` | Records **every** callback received, including rejected duplicates. `callback_key` UNIQUE for the first receipt; duplicates written with a **null** unique key, `duplicate_of` set, `accepted = false`. |

Supporting rules:

- **Current status** = the latest transition by `seq`, else `attempted`.
- **First terminal wins.** Terminal states are absorbing. An `acknowledged` arriving after a `failed` is **retained and non-winning** — recorded, visible, and unable to change the outcome.
- **Transaction boundary:** the `attempt_opened` row, its initial `events` row and any `evidence` row from the same logical step are written **in one transaction**. A crash between them is not a representable state.
- Dispositions, evidence and consents are likewise INSERT-only. The deadline changes only by inserting a new disposition version.

## Consequences

**Good**

- An acknowledgement has a legal place to land. The false-negative completion is closed.
- All seven fault sequences become writable, because all four tables they read now exist.
- A duplicate callback is **recorded and visible** rather than silently discarded.
- The judge ledger can show a contradiction (a late acknowledgement after a failure) as evidence rather than as a lost state.
- I1 holds because **no retry code path writes to `dispositions`** — restated honestly at Gate 2 §10 as a property to test, not a structural impossibility.

**Bad / accepted debt**

- Every read is a projection over append-only rows. Queries are heavier and the projection code carries real logic.
- The nullable-unique-key trick is subtle: SQLite permits multiple nulls under a UNIQUE constraint, and the design depends on that. It needs a comment and a dedicated test.
- The atomicity claim is a **hypothesis**. It must be proven under two concurrent writers and a crash. If it cannot be made atomic, **backtrack Gate 2 rather than silently losing receipts.**

## Reversal

**Not reversible — this is the Closure Contract.** Relaxing it would permit a state transition to be lost, which is the failure the product exists to detect.
