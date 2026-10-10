# Slice 12 adversarial review (supporting note, authoritative for nothing)

**Reviewed 10 October 2026.** Branch `slice-12-ledger`, commits `b87d402` to
`ce40bf0` (nine). Scope: the judge ledger read projection, `GET /options`, the
Next.js ledger view, the `/ledger` alias added the same day,
`tests/test_ledger.py` (29 tests) and `tests/_mutate_slice12.py` (10 mutations plus
5 probes).

**The submission-asset half of Slice 12 is not built.** That is declared out of
scope for this review and is not reported as a gap.

---

## Verdict

**SOUND, with four blocker-grade findings, all of them against `00-status.md` and
none of them against the code.** Every claim the code makes was attacked and held.
The record does not currently describe the code: it still states the pre-alias
numbers.

---

## 1. Findings

| # | Grade | Location | What is wrong | Why it matters | Smallest fix |
|---|---|---|---|---|---|
| F1 | **BLOCKER** | `00-status.md:468` | "927 passed, 0 skipped" and "the slice adds exactly its own 25 tests". Measured: `tests/test_ledger.py` holds **29** tests, and 927 cannot be reproduced on this machine | A false count in the state authority is how a later slice inherits a claim nobody checked. 927 was measured 9 October, before the alias and before `psycopg` stopped importing | State 29 tests in `test_ledger.py`, and state 927 as a dated measurement with its conditions rather than as a current fact |
| F2 | **BLOCKER** | `00-status.md:469` | "8 of 8 mutations RED". Measured: **10 of 10**, L9 and L10 were added with the alias | The record understates the evidence, which is the safe direction, but it is still false | Restate as 10 of 10 and name L9 and L10 |
| F3 | **BLOCKER** | `00-status.md:484` | "25 tests and an 8-of-8 mutation harness" | Same two errors, in the paragraph a fresh session reads first | Same two corrections |
| F4 | **BLOCKER** | `00-status.md:550` | "927 passed ... harness 8 of 8 RED" and "five commits (`b87d402` to `66ee4d4`)". Measured: **nine** commits, `b87d402` to `ce40bf0` | The checklist row is the one that survives into the next slice's sweep | Restate both |
| F5 | SHOULD FIX | `00-status.md:455` | "Committed 10 October 2026 in five commits ... and fast-forwarded into `main` the same day". Six were; `860d9f6`, `6937c1a` and `ce40bf0` are not on `main` yet | True when written, false after the alias work. It resolves itself at the next merge, but today it is a false statement about the repository | Say which commits are on `main`, or make the sentence conditional on the merge |
| F6 | SHOULD FIX | `00-status.md:468` | The 927 figure is stated with no measurement conditions | A count that cannot be reproduced on the machine that ships the slice is not evidence. `psycopg` 3.3.5 is blocked by Windows Application Control, so 75 tests in three modules do not collect | Add the date, the engine and the caveat to the sentence, next to the number |
| F7 | NIT | `tests/test_ledger.py` `test_all_five_hold_on_a_clean_unresolved_episode` | Asserts all five fault assertions hold. Four of the five are unfalsifiable by construction, so in practice only I3 can break it | The name promises more than the test can deliver. It is not wrong, but a reader will read it as five independent guarantees | Note beside the test that four are display-only, pointing at the harness ratio |
| F8 | NIT | `tests/test_boundaries.py` `VICTIM_FILES` docstring | Claims the list "includes all of `frontend/`". It does, for source: the only project files absent are `frontend/next-env.d.ts` and `frontend/tsconfig.tsbuildinfo`, both generated | True in substance, false literally. This project's own bar is the literal one | Add "(generated files excepted)" |

**No finding against the code.** Nothing in `presentation.py`, `service.py`,
`api.py`, `frontend/app/ledger/page.tsx` or `tests/test_ledger.py` was found
defective.

---

## 2. Judgement calls, one line each

| Call | Verdict | Relied on |
|---|---|---|
| The ledger never writes; the patient read is the expiry trigger and a judge read is not | **Agree.** Mutation L2 turns `TestTheLedgerNeverWrites` RED while an unrelated axis test stays GREEN, so the failure is attributed to the write and not to a broken read path | `04-slices.md` Slice 12; the test's own docstring |
| Registering the same handler at `/ledger/{episode_id}` to make the architecture's auth row true | **Agree.** Stacked decorators on one function is the right shape: a second handler would be a second thing to keep in step | `02-architecture.md` section 12 |
| `/options` gets no top-level twin | **Agree.** `/options` is not a guarded prefix, so a copy would be open. The asymmetry is asserted against the real route table, not only explained | `src/carerelay/api.py:103` |
| Only 1 of the 5 fault assertions is falsifiable today | **Agree, reproduced.** P3 goes RED; P1, P2, P4 and P5 do not. The harness reports the ratio rather than folding it into the RED total | `tests/_mutate_slice12.py` |
| Amending `02-architecture.md` was declined in favour of adding the route | **Agree.** Editing an approved gate document reopens Gate 2 (`AGENTS.md` section 5), and adding the route made both sentences true without the edit | `AGENTS.md` section 5 |

---

## 3. Mutation evidence, independently re-run

Three of the ten were re-run by hand, one at a time, backed up outside the repo,
restored with a retry loop and verified by md5. Each carries a control.

| Mutation | Target | Control | Restore |
|---|---|---|---|
| L2 the ledger becomes a writer | RED | GREEN (`test_the_three_axis_values_are_present`) | CLEAN |
| L9 the `/ledger` alias is removed | RED | GREEN (same control) | CLEAN |
| L10 `/ledger` stops being guarded | RED | GREEN (`test_the_route_set_is_exactly_the_policy_set`) | CLEAN |

**The harness itself was audited before its "10 of 10" was trusted.** It uses
`read_bytes` / `write_bytes` throughout and never `read_text` / `write_text`, so
the newline-translation bug that silently re-encoded Slice 6's targets is not
present here. All 15 entries (10 mutations and 5 probes) resolve to exactly one
anchor once the harness's own `_conform` is applied; a first check that skipped
`_conform` reported 14 false failures and was wrong. The `ran` counter is not
padding-inflated the way Slice 8's was: it reports 1 for a one-test selection.

---

## 4. Test-quality findings

- **No redundant mutations.** The ten map to ten distinct claims; none is the same
  edit run twice under two names.
- **No tautologies found**, with the F7 caveat above.
- **No skipped mutation, no silent anchor failure.** All 15 resolve.
- The absence assertions in `TestTheLedgerAliasUnderTheGuardedPrefix` are
  fail-capable rather than decorative: L10 puts two of them RED.

## 5. Scanner evasion, re-tested

All eight forms are flagged: `__builtins__["open"](...)`, `builtins.open(...)`,
`builtins.__import__("socket")`, `builtins.__import__("sqlite3").connect(x)`,
`getattr(datetime, "now")()`, a call used as `func`, a lambda used as `func`, and
plain `open(...)`. The false-positive boundary holds: `" ".join(...)`, `d.get(k)`
and `len(items)` are all clean.

## 6. What I tried to break and failed to break

- Made the ledger write, with a control. RED for the right reason.
- Removed the alias and removed its guard, each with a control. RED for the right reason.
- Drove `dwell_seconds` onto the patient surface. It is absent: it appears only in
  `LedgerSurface` (`src/carerelay/presentation.py:196`, `:218`).
- Found a link from the patient screen to the ledger. There is none; `frontend/app/page.tsx:13` says so and `frontend/components/` carries no reference.
- Got a secret, an idempotency key or clinical free text into the ledger body. The secret scan is clean and the idempotency test holds.
- Evaded the boundary scanner in eight ways. All flagged.
- Broke the frontend types. `tsc --noEmit` exits 0.

## 7. Could not be verified

- **Anything Postgres-gated.** 75 tests across `test_deployment.py`,
  `test_postgres_stage2.py` and `test_postgres_store.py` do not collect: Windows
  Application Control blocks the `pq` extension of `psycopg` 3.3.5, and no local
  Postgres container is running. No claim in this slice is Postgres-gated, so
  nothing here is unverified as a result, but no such claim was tested either.
- **`next build`.** It cannot complete in this sandbox. `tsc --noEmit` is the check
  that ran.
- **Deployed behaviour on Render or Vercel.** No deployment, no credentials, no
  external calls were made, per the review brief.
- **The submission-asset half.** Declared out of scope.

## 8. Corrections still outstanding

F1 to F4 are blocker-grade and were corrected in the same session; F5 resolves at
the next merge. F7 and F8 are nits and were left as recorded.
