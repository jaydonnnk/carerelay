# Slice 7b F10 closure: adversarial review

**Scope.** The nine uncommitted files on `main` at `a796249`: the F10 savepoint
narrowing in `src/carerelay/postgres_store.py`, the new discriminating test in
`tests/test_postgres_stage2.py`, mutation S6 in `tests/_mutate_slice7b_stage2.py`,
the bytecode-cache hardening in the four `tests/_mutate_*.py` harnesses, and the
stale-checkbox sweep in `00-status.md` and `tasks/todo.md`.

**Verdict: SHIP WITH FIXES.** The F10 code fix is correct. Two record-integrity
defects were found; both were fixed in the tree before the ship. Nothing here
changes product behaviour.

**Provenance.** This pass resumed an adversarial review that had been stopped
part-way and handed off. The findings below were re-established by reproduction
unless labelled otherwise. The engine was local Docker PostgreSQL 17.11 on port
15432, not Supabase.

## Re-verified in this pass

| Check | Result |
|---|---|
| Full suite | **614 passed, 0 failed, 0 skipped, 0 errors, exit 0** (41.8 s) |
| `tasks/lessons.md` claim 15, Slice 6 harness | **11 of 11 RED**, control 65 passed, exit 0 |
| claim 15, Slice 7 harness | **10 RED, 0 NOT PROVEN of 10**, control **272 passed**, exit 0 |
| claim 15, A7 harness | **3 of 3 RED**, exit 0 |
| Stage 2 harness after the docstring fix | **6 RED, 0 SURVIVED, 0 NOT PROVEN of 6**, anchors intact |
| Byte-identical restore, all six mutated targets | md5s match the `[BASE]` lines |
| CRLF, all nine files | loneLF 0, no `\r\r\n` |
| U+2014 on added lines | 0 |
| `git diff --check` | clean |
| Gate documents touched | none of `01-product.md`, `02-architecture.md`, `03-program-design.md`, `04-slices.md` |

`tasks/lessons.md` claim 15 asserts that the three harnesses were re-run and report
their certified figures unchanged. **That claim is true.** Every figure reproduces.

## D1. Defect, fixed. The savepoint's stated justification was false

The docstring for `record_expiry_once` and the inline comment at its catch both
said that without the `ROLLBACK TO SAVEPOINT` "the `commit` at the end of `_write`
is the next thing to fail".

**Measured on PostgreSQL 17.11: that is false.** `COMMIT` on an aborted transaction
returns the `ROLLBACK` tag and raises nothing, and psycopg 3's `_commit_gen`
ignores the result (it short-circuits only on status IDLE). So the commit does not
fail; the whole transaction is silently discarded instead. Deleting the rollback
line and re-running the expiry race still gives **2 passed**, with the loser
receiving `False`. The savepoint is therefore **defensive, not load-bearing for any
observable behaviour today**, and no test can distinguish the two.

**Fix applied:** both the docstring and the inline comment now state the measured
mechanism, including why the savepoint still earns its place the moment a statement
is added after the INSERT. The code is unchanged.

## D2. Defect, fixed. `00-status.md` contradicted itself on F10

The Slice 7b stage 2 paragraph carried **three** F10 statements, not two: the new
"F10 CLOSED 5 October 2026", a pre-existing "F10 remains an open item in
`tasks/todo.md`", and a pre-existing "deliberately left". `tasks/todo.md` still
listed F10 in the open-findings table.

**Fix applied:** the F10 row in `tasks/todo.md` now records **CLOSED 5 October
2026** with the corrected mechanism, the intro sentence no longer says F10 remains
open, and both false clauses in `00-status.md` are removed. All three now agree with
the tree.

**A correction to the handoff.** The handoff said "`tasks/todo.md` line 143 words it
correctly". It did not: the row carried the same loose framing ("would let
`_write()` commit an aborted transaction"), so it was rewritten to the precise
mechanism too.

## D3. Minor, not a defect. `RELEASE SAVEPOINT` is hygiene

Repeated `SAVEPOINT` names are legal and `ROLLBACK TO` uses the most recent one,
verified live. The `RELEASE` is hygiene rather than correctness, which the corrected
docstring does not claim otherwise.

## Verdict claims

| Claim | Status |
|---|---|
| The F10 fix is correct | **reproduced** |
| The savepoint is necessary | **falsified** for today's behaviour (see D1); the fix is correct without it being load-bearing |
| The new test is discriminating and would have caught the old code | **reproduced** by the earlier pass (`DID NOT RAISE UniqueViolation` against the `a796249` store code); re-confirmed here that S6 is killed by that test alone |
| The checkbox changes record only what the evidence supports | **reproduced**; all seven newly ticked boxes are backed by `00-status.md` |
| No gate state was altered | **reproduced**; no gate document is among the changed files |

## Residual, disclosed and not fixed

- `docs/reviews/slice7b-stage2-adversarial-review.md` line 277 still carries the
  loose "commit an aborted transaction" phrasing as the dated stage-2 finding. It is
  a review's account of its own session and is left as written.
- `AGENTS.md` section 3 is stale (Slices 1 to 4 complete, Slice 5 in progress). It
  is a disclosed finding of this review, not this pass's to fix.
- `docs/reviews/patient-wording-pass.md` line 8 and the matching sentence in
  `00-status.md` both read "Nothing is committed and nothing is pushed" for the 2
  October 2026 pass, which later commits falsified. Both were given an explicit
  tense in the record sweep that accompanied this ship.

## State at the time of review

The nine files were uncommitted on `main` at `a796249`, nothing staged, `a796249` an
ancestor of `HEAD`. They were committed and pushed on 7 October 2026 on the user's
explicit instruction. No gate authorises either, so the ship rests on that
instruction alone.
