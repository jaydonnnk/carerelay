# Slice 7b stage 1: adversarial review, 4 October 2026

**Supporting note, authoritative for nothing.**

**Verdict: BLOCKER. Two of them. The append-only guarantee holds on the fourteen
tables it covers, but the ported schema carries a fifteenth table with no triggers
at all, and `00-status.md` records a mutation count that is not true. Stage 2 must
not start on this evidence.**

Reviewed on `slice-7b` at `339ad71`. Four untracked files
(`postgres_schema.py`, `postgres_store.py`, `tests/test_postgres_store.py`,
`tests/_mutate_slice7b.py`) plus edits to `00-status.md` and `tasks/todo.md`.

---

## 0. What was measured, and on what

| Item | Result |
|---|---|
| Suite, live Supabase DSN | **568 passed, 1 warning** in 189 s |
| Suite, no Postgres reachable | **551 passed, 17 skipped** in 47 s |
| Arithmetic | 551 + 17 = 568, checks out |
| Author's mutation harness | **7 of 7 RED**, files restored byte-exact (md5 match) |
| Public tables / triggers | **15 tables, 42 triggers**, 3 each on 14 tables, 42 after a second and third init |
| Truncate trigger level | 14 statement-level, **0 row-level** |
| Independent sweeps outside pytest | UPDATE **14/14**, DELETE **14/14**, TRUNCATE **14/14** refused |
| Line endings | all six files CRLF, **0 lone LF** |
| Em dashes | **0** in the four new files; **0** on added lines in both docs |

No commit, push, branch, stash, checkout or delete was performed. Every mutation
was backed up outside the repository, applied one at a time, restored, and md5
verified. The tree was confirmed byte-identical to its pre-review baseline at the
end (all six md5s match).

**Environment caveat that shapes this note.** Docker Desktop's engine would not
start on this machine (the daemon stayed unreachable after roughly seven minutes),
so there was **no local Postgres container**. Every check below was run against
the live Supabase instance instead. That is the real target, so it is not a weak
substitute, but it means **every "local" figure in the record is unverified by
this review** (see "could not verify").

---

## 1. Findings

| # | Severity | Location | What is wrong | Why it matters | Smallest fix |
|---|---|---|---|---|---|
| F1 | **BLOCKER** | `docs/plans/urgent-advice-accessibility/00-status.md:318` and `tasks/todo.md:143` | The record says "**6 of 6 mutations RED**". `tests/_mutate_slice7b.py` defines **seven** mutations (P1 to P7) and ran **7 of 7 RED**. `tasks/todo.md:147`, written the same day, says "7 of 7 RED". | A false count in `00-status.md` is blocker-grade by the project's own rule. Two documents in one tree disagree about the same number, so neither can be cited. | Change "6 of 6" to "7 of 7" in both files, and search the whole bullet: `tasks/todo.md` carried the false number twice, once as a parenthetical and once in the body sentence. |
| F2 | **BLOCKER** | `src/carerelay/postgres_schema.py:221` | `transcript_confirmations` is a Postgres-only table. It has **no counterpart in the SQLite schema** (zero occurrences in `state.py`) and **no append-only triggers**. Measured on the live instance: `UPDATE` changed `confirmed_text` from `original` to `tampered` (rowcount 1), `DELETE` removed the row (rowcount 1), `TRUNCATE` emptied the table. | This is the exact defect class stage 1 exists to prevent: a table in the clinical record that can be rewritten and erased. Nothing catches it. `tests/test_postgres_store.py:147` asserts only `sqlite <= postgres` (one-directional), so an extra Postgres table passes silently; `:170` compares the two append-only lists, and **both omit it**. It also falsifies `postgres_schema.py:17`, "Two differences are deliberate and are the only two". | Delete the table. Nothing writes it and SQLite has no counterpart. If it is intended for a later slice, add it to **both** engines and **both** append-only lists: adding it to the Postgres list alone turns `test_the_append_only_lists_are_identical` RED (measured). |
| F3 | SHOULD FIX | `00-status.md:318`, `tasks/todo.md:147` | The latency figures are quoted to three or four significant digits: connect 2,223 ms, `SELECT 1` 245 ms. My independent run measured connect median **1,744 ms** (samples 1,638 to 2,670) and `SELECT 1` median **279.9 ms** (259.98 to 536.84). | Same order of magnitude, different digits. A single median of 5 connects is not a measurement anyone can check, and these numbers are load-bearing for the D1 and D2 decisions below. | Relabel as an order-of-magnitude observation with sample size and date, or drop the digits and keep "roughly two seconds to connect, roughly a quarter second per query". |
| F4 | SHOULD FIX | `src/carerelay/postgres_store.py:376`, `:315` | The author claims a new `CHECK` makes the seed "fail loudly". Measured: adding `CHECK (persona = ANY (ARRAY['zzz'::text]))` to `episodes` made `_allowed_values` return `['zzz']`, and the seed then inserted `zzz` **successfully**. The seeder adapts to a domain-wrong value silently. Integer `CHECK`s (`IN (0,1)`) are worse: they carry no `::text` casts, so `_allowed_values` returns `[]` and the seeder falls through to the type default `1`, which happens to sit in every `0/1` set. | The seed is conformant by luck for integers and silent for text. A schema edit cannot be trusted to surface as a seed failure. | State the limit in the docstring, or assert the derived value against a known-good set and raise if it is not there. |
| F5 | NIT | `src/carerelay/postgres_store.py:366`, `:315`, `:376` | `_allowed_cache` is a mutable class attribute shared by every instance and never cleared. `_sentinel_for` is a classmethod reading `cls._allowed_cache`; `_allowed_values` is an instance method reading `self._conn`. It works only because `_seed_row_for` populates the cache in the same loop immediately before each `_sentinel_for` call. | Harmless while there is one database and the values are deterministic. It becomes a stale-cache bug the moment a second DSN or an altered schema enters one process. | Make the cache per-instance, or pass the allowed values into `_sentinel_for` explicitly. |
| F6 | NIT | `src/carerelay/postgres_store.py:528` | `episode_id, route_id = attempt[1], attempt[2]` reads `SELECT *` positionally. Correct today (`attempts` is `id, episode_id, route_id, ...`) but a silent wrong-value bug if the column order changes. The SQLite store uses named `sqlite3.Row` access. | A future column insert would mis-key receipts rather than fail. | Name the columns in the `SELECT`. |
| F7 | NIT | `tests/_mutate_slice7b.py:11`, `:68`, `:181` | The docstring says "Six mutations" while the table holds seven. Each mutation runs the whole test file, so no mutation is attributed to a specific test. `completed` is referenced after the `finally` block, so it is unbound if `subprocess.run` itself raises. | Cosmetic today, but the docstring count is the same drift that produced F1. | Fix the count; add a per-mutation selector; move the read of `completed` inside the `try`. |
| F8 | NIT | `docs/plans/urgent-advice-accessibility/supabase-migration-plan.md:49`, `:191` | The plan says "The 13 tables" (and lists 14) and "all 13 tables". There are 14 append-only tables. | Stage 2 is sequenced from this document, so its estimate is built on a wrong count. | Correct to 14 when stage 2 starts. |

---

## 2. What the slice gets right, and I could not break

These were attacked and held.

- **The port is faithful, column for column, on the fourteen shared tables.** I
  parsed both schemas independently: 0 missing columns, 0 extra columns, 0 order
  drift, 0 constraint drift (17 `CHECK` clauses in each). The only text
  differences are the 6 `INTEGER PRIMARY KEY` to `SERIAL PRIMARY KEY` conversions
  and the one `REAL` to `DOUBLE PRECISION`, which are exactly the two the
  docstring declares. [verified]
- **Three triggers per table, and the TRUNCATE diagnosis is correct.** 14
  statement-level truncate triggers, 0 row-level. `TRUNCATE episodes CASCADE` is
  refused by the truncate trigger. [verified]
- **`CASCADE` is the right probe form.** A bare `TRUNCATE episodes` is refused by
  the foreign key with `FeatureNotSupported` **before** any trigger runs;
  `TRUNCATE dispositions` (nothing references it) is refused by the trigger with
  `RestrictViolation`. Removing `CASCADE` from the probe turns
  `test_truncate_is_refused` RED (1 failed, 16 deselected). [verified]
- **`DROP TABLE` still works**, so the schema stays rebuildable. [verified]
- **The UPDATE probe genuinely reaches the trigger.** `UPDATE t SET col = col` is
  not optimised into a no-op: on a scratch table with a `BEFORE UPDATE` trigger
  that raises, the self-assignment fired it. [verified]
- **The seeding is load-bearing, and the control proves it.** Making
  `seed_one_row` a no-op turns `test_update_is_refused_on_every_table` RED
  (1 failed, 16 deselected) while `test_truncate_is_refused` stays GREEN (1 passed,
  16 deselected). The failure is attributed to the seeded path, not to a broken
  store. [verified]
- **The seeding does not depend on tuple order.** Swapping `dispositions` and
  `policy_versions` in `APPEND_ONLY_TABLES` leaves the UPDATE test GREEN, so the
  seed works by explicit parent-walking rather than by iteration order. [verified]
- **`ON CONFLICT DO UPDATE` is refused via the UPDATE trigger; `DO NOTHING`
  succeeds.** Both the refusal and the control were reproduced. [verified]
- **The mutation harness is honest.** All seven anchors resolve, all are unique,
  it uses `read_bytes`/`write_bytes` only (no newline translation), and it
  restores byte-exact. A skipped suite is reported as SURVIVED, not as a pass:
  with no Postgres it printed "0 of 7 mutations seen RED", listed all seven as
  problems, and exited 1. [verified]
- **Line endings and em dashes are clean.** CRLF with 0 lone LF on all six files;
  0 U+2014 in the four new files and 0 on added lines in both docs. [verified]
- **The boundary scanner is intact.** All five documented evasions are caught
  (`__builtins__["open"]`, `builtins.open`, `builtins.__import__` for `socket` and
  `sqlite3`, `getattr(datetime, "now")`), and both false-positive controls
  (`" ".join(...)`, `pathlib.Path(...).read_text()`) stay clean. 155 boundary
  tests pass. [verified]

---

## 3. Judgement calls

| Claim | Verdict | Basis |
|---|---|---|
| C1 "568 passed, 1 warning", 551 + 17 | **Agree** | Measured both states, arithmetic sums |
| C2 "7 of 7 RED, restored byte-exact" | **Agree** | Ran the harness; md5s match. The record's "6 of 6" (F1) is the defect, not the harness |
| C3 "15 tables, 42 triggers, idempotent re-init" | **Agree on the numbers, with F2 attached** | 15 and 42 are literally true; the phrasing implies all 15 are guarded, and one is not |
| C4 three triggers, TRUNCATE bypasses row-level | **Agree** | 14 statement-level, 0 row-level; CASCADE form refused |
| C5 "`WHERE false` reported silence" | **Agree** | P5 and P7 both RED; seeding removal RED with a GREEN control |
| C6 "asserts the row is present at mutation time" | **Agree** | The `assert _rows >= 1` between seed and mutation is what fails first when seeding is removed |
| C7 live check cleared, 14/14 UPDATE and DELETE | **Agree** | Reproduced outside pytest on the live instance |
| C8 the latency digits | **Disagree as measurement, agree as magnitude** | See F3 |
| C9 CRLF clean, 0 em dashes | **Agree** | Byte counts |
| C10 the record rows are accurate | **Disagree** | F1, plus `tasks/todo.md:143` "(6 mutations)" against `:147` "7 of 7" |
| A8 `_allowed_cache` mutable class attribute | **Latent, not a live bug** | Agree with the author's own disclosure; see F5 |
| A8 classmethod/instance split | **Works by call ordering** | Agree; see F5 |
| A8 latency is not a benchmark | **Agree, and strengthen it** | See F3 |
| A8 variance not characterised | **Agree** | My connect samples spanned 1,638 to 2,670 ms in one session |
| A8 hand-written `callbacks` insert cannot drift | **Agree** | It names 12 columns; a rename or removal raises rather than defaulting |

### A4: is P4 a legitimate RED?

**Partly. It is RED, but it is non-discriminating, and I would not count it as
evidence that the guard has teeth.**

P4 replaces `FOR EACH STATEMENT` with `FOR EACH ROW` on the truncate trigger.
Postgres rejects that at `CREATE TRIGGER` time, so the schema becomes
unbuildable: 5 passed, 12 errors, and the 5 that pass are the ones that never
touch a database. That proves the row-level form is **illegal**, not that a
row-level truncate trigger would fail to guard. Those are different claims, and
the second is the one the stage cares about.

P3 (drop the truncate trigger) is the mutation that actually proves the guard is
load-bearing, and it does so behaviourally. P4 is worth keeping as a record of
*why* the statement form is required, but it should be labelled as documenting a
constraint of the engine rather than as a red result.

**A better P4:** drop `CASCADE` from `refuse_truncate` in `postgres_store.py:487`.
That is behavioural, it goes RED (measured: 1 failed, 16 deselected), and it
proves the thing the docstring claims, namely that a bare `TRUNCATE` is stopped by
the foreign key rather than by the trigger.

---

## 4. Test-quality findings

- **`tests/test_postgres_store.py:147` is one-directional.** `assert
  sqlite_tables <= postgres_tables` cannot see an extra Postgres table. That is
  precisely the hole F2 fell through. Set equality, or an explicit allow-list
  with a stated reason, would have caught it.
- **No test asserts that every table in the Postgres schema is guarded.** The
  suite asserts 42 triggers exist nowhere; it asserts the two append-only lists
  agree, which both satisfy by omitting the same table. A test of the form "every
  table in `SCHEMA_SQL` is in `APPEND_ONLY_TABLES`, or is named as an exception"
  is the missing check.
- **`tests/test_postgres_store.py:510` and `:526` assert substrings of their own
  source.** Both are fail-capable (delete the string, the test fails) but close
  to tautological: they prove the file mentions a fact, not that the fact holds.
  The behaviour they describe was verified separately, so the risk is low.
- **P4 is destructive rather than discriminating** (section 3).
- **No mutation is attributed to a test.** The harness runs the whole file per
  mutation, so a reader cannot tell which test each mutation is meant to kill.
  My own runs used `-k` with explicit deselection counts (1 selected, 16
  deselected) for this reason.

---

## 5. Corrections applied to the record

- `00-status.md:318`: "6 of 6 mutations RED" corrected to "7 of 7", and the
  Slice 7b row now points at this note and names F2.
- `tasks/todo.md:143`: "(6 mutations)" corrected to "(7 mutations)", and the body sentence of the same bullet, "**568 pass. 6 of 6 mutations RED.**", corrected to "7 of 7". **The first pass fixed only the parenthetical and left the body sentence false.** It was caught after this note was written, while preparing the handoff, and is recorded here because a review that leaves its own blocker half-fixed is committing the drift it is reporting. Both counts in that bullet now read 7.

Both were made because `AGENTS.md` section 6 requires documentary consistency
across those two files, and the same false number sat in both.

---

## 6. What I could not verify, and why

- **Every local-container figure.** "17 pass locally", "3.4 s", "connect 28.5 ms",
  "`SELECT 1` 0.48 ms". Docker Desktop's engine would not start on this machine,
  so no local Postgres existed. I did not install one, because the review brief
  forbids installs.
- **Whether `transcript_confirmations` is deliberate scaffolding.** No document,
  plan, or line of code mentions it. [unknown] That is why F2 offers both
  remedies rather than assuming it should be deleted.
- **The exact conditions behind the author's 2,223 ms and 245 ms.** Different
  time of day, different network state. My figures are from one session on
  4 October 2026.
- **Run-to-run variance on Supabase.** Not characterised. The suite took 189 s
  once; the harness took 23 minutes for seven runs; individual mutation runs
  ranged from 2.4 s to 253 s for the same file.
- **`psycopg.errors.LockNotAvailable` translation to `LockContention`.** No test
  exercises a real lock timeout, so the branch is unproven. It is stage 2 work
  (the O2 test), which is why it is listed there.

---

## 7. Stage 2

**Not started, and not authorised by this review.** Two blockers are open.

The three decisions the brief asks to be surfaced rather than decided stay open
and unanswered here, because reaching them is stage 2 work. For the record, my
readings, labelled as judgement rather than measurement:

- **D1 connection handling.** Hold one connection for the process lifetime, and
  stop running the schema DDL on every construction. Connect plus 42-trigger DDL
  at roughly two seconds per connect is not survivable on a request path. A pool
  adds a concept a single-worker deployment does not need. [hypothesis]
- **D2 `lock_timeout`.** 5 s is generous against a quarter-second link, but the
  number of statements inside one `_write()` matters more than the per-statement
  cost. Recommend keeping 5 s for stage 2 and measuring it under the O2 test
  rather than guessing again. [hypothesis]
- **D3 the free-tier pause.** Real submission risk, not a code risk. Options are
  a keep-warm ping, a paid tier, or a recorded demo. Not for me to choose.

---

## 8. Note on the brief

The brief's branch topology was stale. Measured: `main`, `slice-7` and `slice-7b`
are all at `339ad71`, and `slice-7` **is** an ancestor of `main`. The brief said
`main` was at `06a25b2` and behind. Not a defect in the slice; the brief was
written before Slice 7 was fast-forwarded.

---

## 9. Resolution status, added 4 October 2026

**This section is a status record, not part of the review. The findings above are
as the reviewer wrote them and are not edited.** The fixes were made on
`slice-7b-stage1-fixes`, created from `slice-7b`, and are uncommitted.

| Finding | Status | What was done |
|---|---|---|
| F1 count | **CLOSED** (by the reviewer, section 5) | Both records read 7 of 7 |
| F2 unguarded table | **FIXED** | `transcript_confirmations` deleted. Parity is now **set equality**, plus a new `test_every_schema_table_is_guarded_or_named_as_unguarded` against the new `UNGUARDED_TABLES` list. Both go RED on the exact defect with no database |
| F3 latency digits | **FIXED** | Relabelled an order-of-magnitude observation with sample size and date; the review's independent figures are quoted as agreeing in magnitude and not digits |
| F4 seeder adapts silently | **FIXED** | `_assert_row_satisfies_checks` inserts the derived row into a scratch `LIKE ... INCLUDING CONSTRAINTS` table (no triggers), so the real `CHECK` is evaluated against the real values and a domain-wrong widening fails at the next seed |
| F5 mutable class cache | **FIXED** | `_allowed_cache` and `_seen_allowed` are per-instance; `_sentinel_for` is an instance method |
| F6 positional `SELECT *` | **FIXED** | Named columns `id, episode_id, route_id` |
| F7 harness nits | **FIXED** | Docstring counts seven; each store mutation runs one named test; `completed` bound in the `try`; P4 relabelled non-discriminating |
| F8 stale table count | **FIXED** | Migration plan reads 14 tables in section 2.2 and the estimate table |
| A4 P4 non-discriminating | **LABELLED** | P4 is kept and labelled as documentation of an engine constraint, not as a behavioural proof. A behavioural replacement (drop `CASCADE` from the refuse probe) was **not** added to the harness; see the unverified list |
| Section 4 test-quality findings | **PARTLY ADDRESSED** | The one-directional subset assertion is fixed (F2). The "which test does each mutation kill" finding is addressed by per-mutation selectors. The two source-substring tests at `:510` and `:526` are unchanged |

**Two decisions were taken here, the first two of the three the review surfaced.** Both are recorded in `tasks/todo.md` with their reasoning:

- **D1 connection handling: decided.** The schema DDL now runs **once per process
  per DSN**, not on every construction, and the connection is held. A pool is
  still rejected, for the review's reason. This is broader than the finding asked
  for, so it is disclosed: the review asked for the decision, and this is the
  decision.
- **D2 `lock_timeout`: decided.** It stays at 5 s but is now an explicit
  `lock_timeout_s` parameter, and a test (`test_a_short_lock_timeout_reaches_lock_contention`)
  now reaches the `LockNotAvailable` to `LockContention` branch, which the review
  listed as unproven.
- **D3 the free-tier pause: left open**, because it is a submission and budget
  decision, not an engineering one. Recorded as an open item anchored to "before
  submission".

**What this pass could not verify, and why it matters.** The credential supplied
for the Supabase instance was **rejected** by the server (`FATAL: password
authentication failed`, reproduced on the transaction pooler, the session pooler,
and with a keyword-form connection that bypasses URI parsing entirely, so it is
not a percent-encoding error). Consequently:

- **No live-instance check was run in this pass.** Every Postgres-gated test,
  including the three new D1/D2 tests, is `SKIPPED` here and was verified only by
  inspection.
- **The D1 mutation is prepared but not observed RED.** Removing the D1 guard
  leaves the 15 Postgres tests skipped, so the suite stays green and the mutation
  proves nothing yet. It must be run against a working DSN before stage 2.
- **The F2 fix is verified without a database, which is stronger than the review
  required.** The two parity tests are no longer Postgres-gated, so the mutation
  that reintroduces the extra table drives both RED on a machine with no Postgres.
  That was measured.
- **The `test_a_short_lock_timeout_reaches_lock_contention` test is unproven.**
  It written against the O2 contract but never observed to pass or fail live.

**The counts, corrected.** At the review the suite was 568 (551 + 17). This pass
is **572 collected, 557 passed, 15 skipped without a live Postgres**, and the
change is: +5 tests that were skipped purely because the skip was module-wide and
now run (the parity and stated-limits tests, which need no database), +1 new
parity guard, +3 new D1/D2 tests (Postgres-gated). 551 + 5 + 1 = 557 passed.

**What the live run changed, added 4 October 2026.** Every caveat above that a
database could close is now closed, and the live run found a defect the review
and the no-database pass had both missed.

- **`tests/test_postgres_store.py` holds 21 tests, not 17 or 18.** The live run
  on a working DSN reports **21 passed**. The figure in the review note and the
  one in `tasks/todo.md` were both wrong; the correct count is 21, of which 6 run
  without Postgres and 15 are Postgres-gated.
- **A real defect in the F4 remedy, found only on the live engine.** The F4
  scratch table was created with `LIKE table INCLUDING CONSTRAINTS`, which copies
  `CHECK`s and `NOT NULL`s but **not `DEFAULT`s**. The seeder deliberately omits
  every defaulted column (`_seed_row_for` selects `column_default IS NULL`),
  relying on the real table to fill it, so the scratch copy inserted `NULL` into
  an omitted `NOT NULL` column (`dispositions.id`) and raised `NotNullViolation`
  **before any `CHECK` was evaluated**. The aborted transaction then refused every
  further statement, so the cleanup `DROP` raised `InFailedSqlTransaction` and a
  third, unrelated test fell over on the poisoned connection. Three tests failed
  and none of them was guarding anything. This is exactly the failure the review
  could not see: it was invisible without a database, and it inverts the F4 fix's
  purpose from "prove the row satisfies the real constraint" to "fail the probe".
  Fixed by adding `INCLUDING DEFAULTS` and wrapping the scratch dance in a
  `SAVEPOINT` so the real `CheckViolation` propagates instead of being masked.
- **The D1 mutation is now observed RED.** With the `_SCHEMA_APPLIED`
  short-circuit removed, `test_the_schema_ddl_is_not_reapplied_for_a_second_store`
  fails with `AssertionError: assert 1 == 0` ("the DDL ran again for a second
  store"). The same mutation also failed
  `test_a_short_lock_timeout_reaches_lock_contention` with `QueryCanceled:
  cancelling statement due to statement timeout`, because re-applying 42 triggers
  on every connect under a 0.5 s lock timeout exceeds it. Both tests are
  load-bearing, and the mutation restores byte-identical
  (md5 `7e8b9067c3facc01d91c6292886a3098`).
- **Both pooler ports accept the credential.** The record named port `6543`; this
  pass ran on `5432`. Both work: the session pooler (`5432`) and the transaction
  pooler (`6543`) are both reachable on the project's pooler host
  with the same password. **The host was named here in full until 5 October 2026
  and is redacted:** a public repository that carries a hostname and a password in
  the same document carries a connection string in two pieces. This is stated as a verified fact measured on
  4 October 2026, not an inference.
- **The credential differs from the obvious guess by one glyph: a digit zero where
  the guess has a letter O,** and the letter-O form is rejected (`FATAL: password
  authentication failed`). **Both strings were written out here in full until
  5 October 2026 and are redacted,** because this repository is public and the
  digit-zero form authenticated successfully on 4 October 2026. The finding stands
  without the values and is the point of it: a placeholder-shaped string can be the
  real credential, so the glyph has to be checked rather than the shape.

**The F2 remedy chosen was deletion, not registration, and the reason is worth
recording.** Registering the table in both engines would have invented a SQLite
table that no code reads; deleting it narrows the Postgres schema to what SQLite
has always had. Nothing wrote the table: `record_transcript_confirmation` writes
`events.payload` and `has_transcript_confirmation` reads it back.

