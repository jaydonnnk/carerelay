# Supabase migration plan (Slice 7b, DRAFT)

**Status:** DRAFT. This document authorises no code. It is a plan for the user's
decision, written 4 October 2026 at the user's request after Slice 7 was built and
reviewed.

**Requested shape [verified with the user, 4 October 2026]:** Supabase as a hosted
Postgres database *behind* FastAPI. The Next.js frontend continues to call FastAPI.
FastAPI continues to hold the bearer token. Supabase is never reached from the
browser.

---

## 1. Why this is a slice and not a config change

The current store is SQLite, and the append-only guarantee is enforced by SQLite
trigger syntax. The migration replaces the storage engine under the one layer that
carries the product's strongest safety claim, so it needs its own build, its own
review and its own Check. Folding it into Slice 7 would mean the Slice 7 evidence
describes a system that no longer exists.

**Verdict: worth doing only if the Render $7.25/month is genuinely unacceptable.**
The cost is not the schema; it is re-proving append-only state on a different engine
and re-writing the persistence proof.

---

## 2. What actually has to change

### 2.1 Verified from the current source

These are the SQLite-specific facts in the repository, found by reading the code, not
assumed:

| Location | What is SQLite-specific |
|---|---|
| `state.py` line 70 | `import sqlite3` |
| `state.py` line 649 | `sqlite3.connect(...)` |
| `state.py` line 655 | `self._conn.row_factory = sqlite3.Row` |
| `state.py` lines 656-669 | `PRAGMA busy_timeout`, `foreign_keys`, `recursive_triggers`, `journal_mode = WAL`, `synchronous = FULL` |
| `state.py` line 705 | `BEGIN IMMEDIATE` inside `_write()` |
| `state.py` lines 495-518 | `_append_only_ddl()` generating `CREATE TRIGGER ... SELECT RAISE(ABORT, ...)` |
| `state.py` lines 341-491 | 13 `CREATE TABLE IF NOT EXISTS` statements |
| whole file | `?` placeholders throughout |
| `api.py` line 332 | `os.getenv("APP_DATABASE_URL") or ":memory:"` |
| `api.py` line 343 | `_STORE = open_store(_database_path(), check_same_thread=False)` |
| `state.py` line 1915 | `open_store(path: str \| Path, **kwargs)` returning `SqliteEpisodeStore` |

### 2.2 The 14 tables, all append-only

`APPEND_ONLY_TABLES` (state.py lines 143-158) is the full list:

```
episodes, policy_versions, dispositions, attempts, attempt_transitions,
callbacks, evidence, consents, human_acceptances, barriers, escalations,
expiry_events, restatements, events
```

That is **14** tables, not 13: the list above is the count. Every one carries a
`BEFORE UPDATE` and a `BEFORE DELETE` trigger in SQLite and three triggers in
Postgres (`BEFORE UPDATE`, `BEFORE DELETE`, `BEFORE TRUNCATE`, the third being the
one Postgres needs and SQLite cannot express). Nothing in the product has a
legitimate UPDATE or DELETE, so the whole schema is protected, not just the
clinical tables. The Postgres port is asserted to have **set-equal** table
coverage with SQLite, so a Postgres-only table is a test failure rather than a
silent gap (see the F2 correction below).

### 2.3 `CHECK` constraints that must survive the port

The `CHECK` clauses are SQL-standard except for the `IN (0,1)` integer booleans, which
Postgres will accept but which should become real `boolean` columns. The compound ones
matter most and must be re-verified:

- `callbacks`: `CHECK ((callback_key IS NULL) = (duplicate_of IS NOT NULL))`
- `callbacks`: `CHECK (accepted = 1 OR rejection_reason IS NOT NULL)` and its converse
- `evidence`: the `level <> 'documented'` guard
- `attempt_transitions` / `callbacks`: `origin IN ('platform','local-sim')`

---

## 3. The four hard problems

### 3.1 Append-only triggers (the real cost)

SQLite raises through `SELECT RAISE(ABORT, '...')`. Postgres has no `RAISE` in plain
SQL; a trigger body must be a `plpgsql` function:

```sql
CREATE OR REPLACE FUNCTION carerelay_refuse_write() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION '% is append-only: % is refused', TG_TABLE_NAME, TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER episodes_no_update
BEFORE UPDATE ON episodes
FOR EACH ROW EXECUTE FUNCTION carerelay_refuse_write();
```

One shared function, 26 triggers generated from `APPEND_ONLY_TABLES` the same way
`_append_only_ddl()` generates them today, so a new table cannot be added without
inheriting the rule.

**`INSERT OR REPLACE` has no Postgres equivalent and the O1 defence does not carry
over.** SQLite's `REPLACE` deletes the conflicting row, and `recursive_triggers = ON`
makes that implicit delete hit the `BEFORE DELETE` trigger (O1). Postgres uses
`ON CONFLICT ... DO UPDATE` instead, which fires the `BEFORE UPDATE` trigger, so it is
still refused, but **for a different reason and by a different path**. This needs its
own test; it cannot be assumed from the SQLite result.

### 3.2 `BEGIN IMMEDIATE` has no equivalent

`_write()` uses `BEGIN IMMEDIATE` to serialise a lookup and an insert against a
concurrent writer (O2 / `LockContention`). Postgres offers:

| Option | Trade-off |
|---|---|
| Plain transaction + unique constraint | Simplest. A race becomes a unique violation, which must map to the existing typed error rather than leaking a driver exception |
| `SELECT ... FOR UPDATE` | Locks the specific row. Works when there is a row to lock; does not help a pure insert race |
| `pg_advisory_xact_lock` | Closest to `BEGIN IMMEDIATE`. An extra concept, but it is the honest analogue |

**Recommendation:** plain transaction plus unique constraint first, and only add the
advisory lock if the concurrency test proves a real race. Adding the lock up front
without a failing test would repeat the mistake the CORS guard already made once.

### 3.3 The persistence proof must be rewritten, not ported

`tests/test_deployment.py` proves three things that are SQLite facts:

1. A record written in one interpreter is readable in a **fresh** interpreter.
2. The WAL sidecar file appears beside the database.
3. The append-only triggers still refuse an `UPDATE` after a reopen.

For Supabase, (1) becomes "a fresh backend process reads the same remote rows", (2)
becomes **meaningless and must be deleted rather than faked**, and (3) becomes a check
against a real Postgres. Copying the SQLite test across would produce a file that
passes while proving nothing, which is the A7-1 defect at larger size.

**Stage 2 outcome, 4 October 2026.** All three landed as written. (1) is now two
subprocesses: one writer interpreter, which exits, and one reader interpreter that
shares nothing with it but the DSN and an episode id. (2) is deleted, and a test
asserts the deletion so it cannot come back. (3) moved from a `sqlite3` connection
to a `psycopg` one and the probe names the episode so a row is actually matched,
because the stage 1 lesson was that a refusal test which reaches no row proves
nothing. The SQLite half is kept and relabelled: it is a claim about the local path,
not about the deployment.

### 3.4 Connection handling

SQLite opens one connection on a local file. Supabase gives a network endpoint with a
pooler. Choices that need deciding:

- **Direct connection** (port 5432) vs **transaction pooler** (port 6543). The pooler
  is required on serverless; a long-running FastAPI process can use either.
- Whether to keep one `psycopg` connection, or a pool. The current `check_same_thread`
  argument suggests a single shared connection; that does not transfer.
- Whether the free tier's connection limit is reached by the existing single-worker
  Render command.

**Stage 2 outcome, 4 October 2026: one held connection, no pool.** Measured on
Supabase in one session: connect plus the 42-trigger DDL **2.51 s**, connect alone
**1.54 s**, so the DDL costs about **0.97 s**, and a statement on a held connection
costs **185 ms**. A pool would save the 1.54 s connect, which a process holding one
connection pays once at startup rather than per request, and it cannot save the DDL,
which D1 already keeps off the request path after the first construction. It would
cost `psycopg_pool` (not installed) and a second failure mode. The third question is
answered by the first two: at one connection per process the free tier's limit is not
reached. Both pooler ports were verified working at stage 1, so the port choice is
open to the deployment rather than forced by the code.

---

## 4. Proposed shape

```
api.py
  _database_path()  ->  reads APP_DATABASE_URL
                        "postgresql://..." -> PostgresEpisodeStore
                        anything else      -> SqliteEpisodeStore (unchanged)

state.py
  EpisodeStore          a protocol, the method surface both share
  SqliteEpisodeStore    today's class, renamed, otherwise untouched
  PostgresEpisodeStore  the new one
  append_only_ddl()     dispatches on dialect
```

The domain and service layers do not change. `rules.py` and `service.py` should be
byte-identical after the slice; if either has to change, the port leaked.

---

## 5. Risks

| Risk | Severity | Note |
|---|---|---|
| **Free-tier Supabase projects pause after ~1 week of inactivity** | **High for submission** | A judge clicking the link on judging day could hit a paused project. Needs an explicit answer, such as a scheduled keep-alive or a paid tier, before this is chosen for submission |
| The append-only proof is rebuilt and is weaker than the SQLite one | High | The whole point of the slice is to keep this stronger, not equal |
| `INSERT OR REPLACE` refusal changes mechanism (3.1) | Medium | Must be re-proven, not assumed |
| Concurrency behaviour differs | Medium | `BEGIN IMMEDIATE` semantics do not transfer |
| Network latency on every write vs local file | Low | Fine on a demo; worth measuring |
| A Supabase key reaches the browser | High | The A7-1 scanner extension from the review should land first, so the guard exists before the new surface does |
| The slice takes longer than budgeted | Medium | 16 October deadline; estimate below |

**[verified]** Supabase free tier includes a Postgres database and pauses inactive
projects. **[estimate]** The pause threshold is roughly one week; confirm against the
current Supabase pricing page before relying on it.

---

## 6. Estimate

| Phase | [estimate] |
|---|---|
| Store protocol split, `SqliteEpisodeStore` renamed, suite green | 2-3 h |
| `PostgresEpisodeStore` CRUD port, all 14 tables | 4-6 h |
| `plpgsql` append-only triggers plus the `INSERT OR REPLACE` equivalent | 2-3 h |
| Concurrency: transaction + unique constraint, plus the O2 test | 2-4 h |
| Rewritten persistence proof against real Postgres | 3-4 h |
| Mutation harness for the new guards | 1-2 h |
| Check, record, authority-doc updates | 2-3 h |
| **Total** | **16-25 h** |

Against a 16 October deadline and 14 slices planned, this is roughly **two days** of
the remaining budget for a change whose only benefit is hosting cost.

---

## 7. Recommended sequence

1. **Land the A7-1 and A7-2 fixes first** (done 4 October 2026). The secret scanner
   must cover `frontend/` before Supabase adds another surface that names a credential.
2. **Run the Slice 7 Check and commit Slice 7 on its own merits.** Slice 7 is complete
   and reviewed; it should not wait on a hosting decision.
3. **Decide the hosting question on cost alone.** If Render's $7.25/month is
   acceptable, stop here and skip this plan entirely.
4. If Supabase is chosen, build it as **Slice 7b**: branch from `main` after Slice 7 is
   committed, carry the four hard problems in section 3 as the exit contract, and stop
   for "continue, or re-steer?" as with any slice.

---

## 8. What this plan does not decide

- Which Postgres driver (`psycopg` vs `asyncpg` vs SQLAlchemy).
- Whether to use Supabase's own auth instead of the bearer token. **[recommendation]** No:
  the approved architecture says a shared bearer token, and Supabase auth is end-user
  auth, which is a different thing.
- The free-tier pause mitigation. That is a submission concern and belongs with
  Slice 12.
