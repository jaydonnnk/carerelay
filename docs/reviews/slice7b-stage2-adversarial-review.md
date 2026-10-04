# Slice 7b stage 2: adversarial review

**Supporting note, authoritative for nothing.** Gate and slice state live in
`docs/plans/urgent-advice-accessibility/00-status.md`; decisions live in the
approved gate documents. This note records what an independent reviewer measured
on 5 October 2026 and what was done about it.

- **Subject:** Slice 7b stage 2, the port of the remaining `EpisodeStore` methods
  into `PostgresEpisodeStore`, the rewritten persistence proof, and the D1 and D2
  decisions.
- **Branch:** `slice-7b-stage1-fixes`, base commit `d425405`, working tree dirty,
  nothing committed at review time.
- **Verdict as delivered: ISSUES FOUND.** Two blocker-grade false claims in the
  records, one flaky test, one parity claim that held only in the annotations.
  The product code itself survived every attack. All findings are now remediated
  in the same working tree; the remediation is listed at the end.

---

## 0. Engine disclosure, and one deviation to object to if you disagree

Every live result in this note ran against a **local Docker container,
`postgres:17-alpine`, PostgreSQL 17.11, `server_version_num` 170011, host port
15432**, started by the reviewer. **[verified]**

It was **not** Supabase. `CARERELAY_TEST_DSN` was absent from the shell, from the
Windows user and machine environment, and from `.env`; the Supabase project ref
is (correctly) recorded nowhere in the repository. Every Supabase-specific digit
in this note is therefore **[unverified]**.

**Deviation.** The review skill says "no live server". The brief required live
verification and the skill's own rule 3.13 says no Postgres-gated claim counts
until it has run on a real engine, so a container was started from an image
already pulled on this machine: no install, no external call, no credential, and
removed at the end. Objection closes this route and leaves the Postgres claims
inspection-only.

**An environment finding worth keeping.** `DEV_DSN` in
`src/carerelay/postgres_store.py:132` defaults to port **55432**, which sits
inside a Windows excluded port range (**55387 to 55486**, read from
`netsh interface ipv4 show excludedportrange protocol=tcp`). Binding it fails
with `An attempt was made to access a socket in a way forbidden by its access
permissions`. That is why the pre-existing `carerelay-pg` container is
`Exited (255)` and cannot be restarted. **The project's own documented local
engine path is dead on this machine.** [verified]

**Fixed at the user's instruction.** `DEV_DSN` now defaults to **15432**, below
the dynamic range where these reservations live, and the reason is recorded at
the constant. `tests/test_postgres_store.py` takes the port in its skip-reason
recipe **from `DEV_DSN`** rather than repeating it, so the documented `docker
run` command and the default cannot drift apart again; its module docstring
carries the same recipe and the `netsh` check. Measured after the change, with
**no `CARERELAY_TEST_DSN` set at all**, the suite reaches the engine through the
default and reports **607 passed, 2 skipped**, where the same run reported 567
passed and 42 skipped before it. The 2 remaining skips are
`tests/test_deployment.py`'s remote persistence tests, which read
`CARERELAY_TEST_DSN` directly and deliberately do not fall back to a default.
The dead container was renamed to `carerelay-pg-dead-55432` rather than deleted,
so its volume survives, and a working `carerelay-pg` now runs on 15432.

---

## 1. Findings

Severity: `BLOCKER` / `SHOULD FIX` / `NIT`. Every finding carries a location and
the measurement behind it.

### F1 BLOCKER. The mutation record was inverted, in two places

Measured live, twice, before any change: **`3 RED, 2 SURVIVED of 5`**.
S1 SURVIVED, S2 SURVIVED, S3 RED, S4 RED, S5 RED.

- `tests/_mutate_slice7b_stage2.py:30-36` recorded all five as RED, naming S1 and
  S2 explicitly.
- `tasks/todo.md:173` recorded "S1 ... and S2 ... are **RED**", then referred to
  S3, S4 and S5 "as classified below" where nothing was classified. The
  attribution was exactly backwards and the sentence was unfinished.
- The same line called the two survivors "2 reportable harness failures". They
  were not. The harness ran both correctly: anchors unique, exit codes read. They
  were surviving mutations, which is a test-coverage gap. The harness's own
  output conflated the two by printing both under one heading, `Failures:`.

Why it matters: a mutation record is the evidence that a guard has teeth. An
inverted one says the two untested branches were tested.

**Remediated.** The missing test was written (F5), the harness re-run to
`5 RED, 0 SURVIVED, 0 NOT PROVEN`, and both records rewritten from the measured
output. The harness now counts and prints SURVIVED and NOT PROVEN separately.

### F2 BLOCKER. `00-status.md` said stage 2 was not started

`docs/plans/urgent-advice-accessibility/00-status.md:318` was unmodified and
read "Stage 2 is AUTHORISED by the user on 4 October 2026 and is the next Slice
7b work, but it is **NOT STARTED**", while the working tree held 2110 added
lines of stage-2 work across 12 files. `AGENTS.md` makes this file the only
authority for gate and slice state and calls a stale mirror a blocking finding.

**Remediated.** The Slice 7b section now records stage 2 as BUILT, UNCOMMITTED,
reviewed and remediated, with the measured counts.

### F3 SHOULD FIX. The D1 test was flaky, on the project's own default engine

`tests/test_postgres_stage2.py:1009` asserted `connect_only < with_ddl`: a strict
inequality between two single timing samples whose entire separation on a local
engine is tens of milliseconds.

Observed: **failed once in a full-suite run** (`opening a second store took 0.03s
and the first, which also ran the DDL, took 0.03s`), then passed 3 of 3; and
**failed once in 5 isolated runs**. Roughly a 22 per cent flake rate. An
independent probe measured connect plus DDL at 0.025 to 0.052 s and connect
alone at 0.008 to 0.028 s: the margin is 10 to 40 ms and noise decides it. On
Supabase the DDL costs about 0.97 s, so the same assertion is reliable there and
unreliable locally, and `DEV_DSN` points at a local container.

**Remediated.** Best of 5 samples per side, and a ratio assertion
(`ratio > 1.2`) instead of an ordering. Measured after the fix: connect plus DDL
0.028 s against connect alone 0.010 s, **ratio 2.9x**, and **0 failures in 10
runs**. Reverting the `_SCHEMA_APPLIED` short-circuit turns it RED with a green
control, so it still detects D1 not working.

### F4 SHOULD FIX. The `Origin` narrowing was annotation-only

`tests/test_postgres_stage2.py:245-246` and `tasks/todo.md:166` recorded that
`record_callback_once` "accepted `Origin | str` on Postgres and `Origin` on
SQLite ... so Postgres was narrowed". Measured empirically, it was not:

| Engine | `record_callback_once(..., "local-sim", ...)` |
|---|---|
| SQLite | **REJECTED**, `AttributeError: 'str' object has no attribute 'value'` |
| Postgres | **ACCEPTED**, returned `applied` |

The cause was three permissive expressions, `origin.value if isinstance(origin,
Origin) else str(origin)`, at `postgres_store.py:969`, `:998` and `:1072`. The
signature-parity test compares annotations, so it could not see this. Three call
sites in `tests/test_postgres_store.py` (522, 543, 550) still passed the bare
string, so the suite depended on the permissiveness the record said had been
removed.

`_origin_value`'s own docstring was also wrong: it claimed the `isinstance` gave
a bare string `StateError`, when a bare `"local-sim"` matched the allowed values
and was written.

Mitigation: no production caller could reach it. `src/carerelay/service.py:906`
does `stated = Origin(origin)`.

**Remediated, and the real story is worth keeping.** Narrowing `_origin_value`
alone broke five tests, because `_insert_receipt` and `_append_transition` were
handed the *already-validated string*, not the enum. Their `origin: Origin`
annotations were simply wrong, and the permissive expression was load-bearing
for an internal caller rather than a widening of the public API. The fix
therefore validates once at the public boundary (`_origin_value`, now raising
`StateError` for a non-`Origin`) and annotates the two helpers as
`origin_value: str`. Two new tests pin it: a database-free one on the static
helper and a live one that drives `record_callback_once` on **both** engines and
requires each to refuse and to write no receipt. Restoring the permissive
expression turns both RED with a green control.

### F5 SHOULD FIX. A comment pointed at a concurrency test that did not exist

`tests/test_postgres_store.py:535` read "which is why the concurrency test below
exists". `grep -rn "threading\|Barrier\|Thread("` across both Postgres test files
returned nothing. There was no concurrency test anywhere in the suite, and that
absence is the sole reason S1 and S2 survived.

**Remediated.** `TestTwoWritersAtOneKey` added to `tests/test_postgres_stage2.py`
with two tests, and the comment now names it.

Both mutated statements are behind a `SELECT`-based early return, so a sequential
second call never executes them:

- `postgres_store.py:656-658` returns before the `ON CONFLICT` at `:666`.
- `postgres_store.py:1311-1312` returns before the `INSERT` at `:1334` and the
  `UniqueViolation` handler at `:1344`.

The new class drives two writers from **two separate connections** (one
`psycopg` connection cannot be shared by two threads, and sharing one would
serialise them and reproduce nothing), released together by a
`threading.Barrier`, over 6 trials, asserting every trial. Baseline behaviour on
unmutated code was already correct: 12 of 12 trials clean, one row, both callers
agreeing on the attempt id, exactly one `True` and one `False` for the expiry.
So the gap was coverage, not the port.

With the mutation applied, the failure modes are the right ones:

- S1 → `RestrictViolation: attempts is append-only: UPDATE is refused`
- S2 → `UniqueViolation: duplicate key value violates unique constraint
  "expiry_events_episode_id_disposition_version_key"`

Each race test runs beside the sequential idempotency test, which stays green
(harness `progress=.F`). That pairing is the control: it attributes the RED to
the race rather than to a broken write path.

A trial that does not overlap still has to give the correct answer, so asserting
on every trial cannot make this flaky in the passing direction; repetition only
reduces the chance a mutation slips through unexercised.

### F6 NIT. A docstring pointed at the wrong file

`src/carerelay/state.py:1942` named
`tests/test_postgres_store.py::TestTheTwoStoresShareOneSurface`. The class is at
`tests/test_postgres_stage2.py:228`. **Remediated.**

### F7 NIT, remediated at the user's instruction. Test-only surface on the production class

`PostgresEpisodeStore` exposed six public callables absent from
`SqliteEpisodeStore`: `init_schema` and `forget_applied_schema` (legitimate D1
machinery) and `seed_one_row`, `refuse_update`, `refuse_delete`,
`refuse_truncate` (test probes, then at `postgres_store.py:1679, 2048, 2070,
2100`).

There was no hole. The `refuse_*` methods *issue* the statement the trigger must
refuse; they do not disable a guard. None was referenced from `api.py`,
`tools.py` or `service.py`. But `seed_one_row(table)` wrote an arbitrary row into
any table past every store guard, from a public method on a production class, and
it uses deterministic ids so a second call raises `UniqueViolation` (which cost
the reviewer a probe round).

The review originally left this as an open item, on the grounds that moving four
methods plus their helpers is a wider refactor than a review should make
silently. The user then authorised it, and it turned out to be mechanical: the
16 methods were **fully contiguous** at lines 1690 to 2136 with nothing else
interleaved, and an AST pass showed their only external references were
`psycopg`, `sql`, `re`, `self._conn` and two per-instance cache attributes.

**Remediated.** All 16 methods plus the `SEED_EPISODE_ID` constant moved
verbatim into a new `tests/_postgres_probes.py` as `class AppendOnlyProbes`,
constructed from a connection. `postgres_store.py` went from 2149 to 1696 lines;
`import re` and `from psycopg import sql` became unused there and were removed.
`test_postgres_store.py` gained a `probes` fixture and its six call sites moved
across. The probes still run on `store._conn`, which is deliberate and was
documented as such: a refusal then also proves the store's connection is not in
some state that bypasses the trigger.

`PostgresEpisodeStore`'s public surface beyond the 32 protocol members is now
exactly `init_schema` and `forget_applied_schema`. **[verified]**

**The move broke something the review did not predict, and it is the useful
part.** `tests/_mutate_slice7b.py`, the *stage 1* harness, defines P5 and P7
against the `WHERE true` predicates inside `refuse_update` and `refuse_delete`.
After the move both reported `anchor not found` and the stage 1 harness fell from
7 of 7 to **5 of 7**. Both were repointed at `tests/_postgres_probes.py` and the
harness is back to **7 of 7 RED** with all three files restored byte-identical.
**Rule: moving code out of a module breaks every mutation harness that anchors
into it, and a harness that reports `anchor not found` is reporting its own
breakage, not a verdict. Grep the harnesses for the moved text before moving
it.**

### F8 NIT. Four tests assert their own source text, and one was near-vacuous

`tests/test_postgres_stage2.py:1187-1228` (three tests) and
`tests/test_deployment.py:451` read `__file__` and assert strings are present or
absent. They are fail-capable but prove a docstring exists, not that behaviour
holds. Kept: they are labelled as documentation guards and they do prevent a
limit being quietly deleted.

`test_the_deployment_names_a_postgres_target` asserted only
`"postgres" in text.lower()`, which would pass on a comment saying the opposite.
**Remediated**: it now parses the `APP_DATABASE_URL` block and requires exactly
one declaration, `sync: false` present, and no `value:` key. Giving the block a
value turns it RED with a green control.

### F9 NIT. D2 docstring disagreed with its code

`tests/test_postgres_stage2.py:1123` said "a quarter-second timeout"; line 1152
passed `lock_timeout_s=0.5`. The control also compared against a hard-coded
`5.0` rather than the measured default. **Remediated**: wording corrected and the
absolute bound's reason stated.

### F10 NIT, not remediated. A broad exception handler

`postgres_store.py:1344` wraps the whole `record_expiry_once` transaction in
`except psycopg.errors.UniqueViolation: return False`, including `_append_event`'s
write to `events`, so any unique violation in that block is reported as "already
recorded". Not reachable in practice: `events.id` is a uuid4 primary key.
Narrowing it needs a `SAVEPOINT`, because catching inside the `with` block would
commit an aborted transaction. Left deliberately, and recorded.

### F11 NIT. A test count was wrong

`tasks/todo.md:167` said "30 tests, 6 of them database-free". Measured without a
DSN: **8 passed, 22 skipped**, so 8 database-free, not 6. **Remediated**, and
recounted after the new tests: 34 total, 9 database-free, 25 gated.

### F12 Harness defect introduced and caught during remediation

While separating SURVIVED from NOT PROVEN, a "how many tests ran" count was
added to the verdict as `or ran == 0`, parsed from pytest's summary line. With
`-q`, a small selection prints **no summary line at all**, only `'..  [100%]'`,
so `ran` was always 0 and **all five** mutations reported NOT PROVEN while every
one of them was in fact RED. This is the same defect the harness docstring
already recorded as (1), reintroduced in a new form. Fixed by reading the count
off the progress characters and keeping it out of the verdict. Recorded in
`tasks/lessons.md`.

---

## 2. Claims verified

| Claim | Verdict | Evidence |
|---|---|---|
| All 32 `EpisodeStore` members implemented, signatures matching both classes | **[verified]** | Independent probe: count 32; 0 mismatches against the protocol; 0 cross-class drift over the full public surface; 0 members missing a return annotation; no public callable on one class absent from the other beyond F7's six |
| One scripted episode identical on both engines, field by field | **[verified]** | Passes live; its non-empty control passes; mutation S4 kills it |
| Append-only holds for UPDATE, DELETE and TRUNCATE | **[verified]** | Reviewer's own probe, own statements, committed reads on fresh connections: **42 of 42** refused-and-unchanged across all 14 tables. Independently, S1's `DO UPDATE` produced `RestrictViolation: attempts is append-only: UPDATE is refused` |
| Write paths route through `DO NOTHING`, not `DO UPDATE` | **[verified]** | All four executable `ON CONFLICT` clauses (`postgres_store.py:666, 1871, 1884, 1893`) are `DO NOTHING`; `DO UPDATE` occurs only in prose at lines 29, 645, 646 |
| Persistence proof crosses a real process boundary | **[verified]** | Two `subprocess.run` interpreters; the writer exits before the reader starts; the reader receives only the DSN and an episode id. Fail-capable: changing `_write()`'s `commit()` to `rollback()` turns both remote tests RED with a green control |
| WAL-sidecar test deleted rather than faked | **[verified]** | No `test_the_wal_sidecar_is_written_beside_the_database` and no `-wal` assertion anywhere; only the absence-guard at `tests/test_deployment.py:465`, which assembles its needle so it cannot match its own source |
| D1: one held connection, no pool | **decision agreed; Supabase digits [unverified]** | The argument does not depend on the exact digits: a pool saves a connect paid once at startup and cannot save the DDL. `psycopg_pool` is genuinely not installed **[verified]**. The *test* was the problem, not the decision (F3) |
| D2: 5 s lock timeout | **mechanism [verified] locally; digits [unverified]** | Default raised `LockContention` after **5.01 s**; `lock_timeout_s=0.5` after **0.51 s**. Clean 10-to-1 tracking proves the knob reaches the statement. Supabase's 5.99 s and 1.15 s are the same shape with about 0.65 s of link overhead |
| All changed files CRLF, zero em dashes on added lines | **[verified]** | All 12 files: lone LF 0. 2110 added lines at review time (2151 after remediation): em dashes 0. Both new files: 0 whole-file |
| Harness reports 3 of 5 RED, survivors are a coverage gap | **[verified]** | Reproduced exactly. Both mutated statements are behind an early `SELECT` return, and both are killed by a two-writer test |
| Table parity between engines | **[verified]** | Set equality, 14 = 14, no engine-only table; `APPEND_ONLY_TABLES` covers all 14. Stage 1's F2 fix holds |
| Suite arithmetic | **[verified]** | With a DSN **609 passed**; without, **567 passed + 42 skipped**, and 567 + 42 = 609. Skips split 25 stage2 + 15 store + 2 deployment = 42 |

## 3. What could not be verified, and why

- **Every Supabase digit.** connect plus DDL 2.51 s, connect alone 1.54 s, DDL
  0.97 s, one statement 185 ms, contention 5.99 s and 1.15 s. No DSN, no project
  ref. The local equivalents are 0.028 s, 0.010 s, 0.018 s and 0.5 ms, which
  agree in shape and differ by the latency to `ap-southeast-2`.
- **The cross-module schema race.** The brief reported four `UndefinedTable`
  failures when `test_postgres_store.py` and `test_postgres_stage2.py` share a
  session. **Not reproduced**: 51 passed in both orders, on a database dropped to
  an empty `public` schema before each order, and 609 passed in the full suite.
  `tests/test_postgres_store.py:80` calls `forget_applied_schema`, which looks
  like the fix already landed. This does **not** clear the claim on Supabase: the
  reviewer's engine is a direct session connection, and
  `tests/test_postgres_stage2.py:40` itself warns that a transaction-mode pooler
  behaves differently.
- **Render's behaviour with `sync: false`.** No deployment was made.
- **Startup against an unreachable database.** `src/carerelay/api.py` does
  `_STORE = _open_store()` at module scope, so a DSN that will not connect fails
  the service at import rather than degrading. Arguably correct, and untested.

## 4. Judgement calls

- **D1, one held connection and no pool: agree.** The reasoning holds without the
  unverified digits.
- **D2, keep 5 s: agree.** The mechanism is verified locally and the per-statement
  semantics are correctly documented at `postgres_store.py:271-278`.
- **Deleting the WAL-sidecar test rather than faking it: agree**, and the
  absence-guard is worth keeping even though it is self-referential.
- **Keeping the `disk:` block as dead weight for one deploy: agree** that it is
  honest. It still holds the service on `plan: starter` for a mount nothing
  writes; the open item exists in `tasks/todo.md`.
- **Narrowing `Origin`: disagree at review time.** It had not been done (F4). It
  has been done since, and the reason it broke five tests on the way is recorded
  there.

## 5. What was attacked and did not break

- Append-only across all 14 tables and all three verbs, with committed re-reads
  to distinguish a refusal from a no-op: 42 of 42.
- The `ON CONFLICT` routing in every product write path.
- Two-writer races on both idempotent methods, 12 trials, unmutated: all correct.
- The persistence proof, by removing the commit it depends on.
- The engine dispatch, by forcing `is_postgres_target` false.
- The lazy-import claim, by importing `psycopg` at module scope in `state.py`.
- The D1 short-circuit, by making the DDL run on every construction.
- The render.yaml declaration, by giving `APP_DATABASE_URL` a value.
- Signature parity, over the whole public surface rather than the protocol alone.
- Table parity, as set equality rather than a subset.
- The harness's restore discipline: every mutation run ended byte-identical, with
  `git status --short --untracked-files=all` unchanged throughout, including the
  reviewer's own three mutation rounds.

## 6. Remediation applied in this working tree

Code and tests:

1. `tests/test_postgres_stage2.py`: added `TestTwoWritersAtOneKey` (two tests,
   two connections, a barrier, 6 trials each); added a database-free
   `_origin_value` refusal test and a live cross-engine `record_callback_once`
   refusal test; rewrote the D1 assertion as best-of-5 with a ratio; corrected
   the D2 docstring; registered the new class in the skip-discipline test.
2. `src/carerelay/postgres_store.py`: `_origin_value` now requires an `Origin`
   and raises `StateError`; `_insert_receipt` and `_append_transition` take the
   validated `origin_value: str` they were always handed.
3. `tests/test_postgres_store.py`: three bare-string origins replaced with
   `Origin.LOCAL_SIM`; the false "concurrency test below" comment now names the
   real class.
4. `src/carerelay/state.py`: docstring pointer corrected.
5. `tests/test_deployment.py`: the render.yaml declaration test now parses the
   block instead of substring-matching "postgres".
6. `tests/_mutate_slice7b_stage2.py`: S1 and S2 selectors point at the race
   tests plus the sequential control; SURVIVED and NOT PROVEN are counted,
   listed and exited separately; the progress-character count replaced the
   summary-line parse; the docstring records the false 5-of-5 claim, the measured
   3-of-5, and the corrected 5-of-5 with dates.
7. `tests/_postgres_probes.py` (new): the 16 append-only probe methods moved off
   `PostgresEpisodeStore`, which is F7. `postgres_store.py` went from 2149 to
   1696 lines, and `import re` and `from psycopg import sql` were dropped there
   as newly unused.
8. `tests/test_postgres_store.py`: a `probes` fixture built on `store._conn`, six
   call sites moved across, and the skip-reason recipe now derives its port from
   `DEV_DSN` instead of repeating it.
9. `src/carerelay/postgres_store.py`: `DEV_DSN` moved off the unbindable port
   55432 to 15432, with the Windows excluded-range reason recorded at the
   constant.
10. `tests/_mutate_slice7b.py`: the stage 1 harness's P5 and P7 repointed at the
    new probe module, after the move silently broke their anchors.

Records: `00-status.md` (stage 2 built, reviewed and remediated, with counts and
the document map), `tasks/todo.md` (mutation record, test counts, F7 closed, F10
still open, the port fix), `tasks/lessons.md` (six new entries).

Measured after remediation, on the local engine (PostgreSQL 17.11):

- Full suite with a DSN: **609 passed**. With no `CARERELAY_TEST_DSN` but the
  container on the new default port: **607 passed, 2 skipped**. With no engine
  reachable at all: **567 passed, 42 skipped**.
- Stage 2 harness **5 RED, 0 SURVIVED, 0 NOT PROVEN of 5**; stage 1 harness
  **7 of 7 RED**. Both restored every file byte-identically.
- D1 test: **0 failures in 10 runs**, ratio 2.9x.
- All three code fixes pinned by a failing-on-revert test with a green control.
- Tree hygiene is re-measured at the close of remediation and recorded in
  `tasks/todo.md`; every path is CRLF-clean and no added line in the tracked diff
  or in any new file carries an em dash.
