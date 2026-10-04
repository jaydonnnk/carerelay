"""The append-only guarantee, proved on Postgres. Slice 7b, stage 1.

**What this module is for.** The product's strongest claim is that the clinical
record cannot be altered once written. That claim is currently enforced by SQLite
triggers, and the move to Postgres replaces the enforcing engine. A guarantee
that has only ever been proved on one engine is not yet a property of the
product; it is a property of SQLite. This file is where it becomes the former or
is found to be the latter.

**The finding it exists because of.** The first port had two triggers per table,
mirroring SQLite. Probing the engine before porting showed that a row-level
`BEFORE DELETE` trigger **does not fire for `TRUNCATE`**, and `TRUNCATE` emptied a
guarded table in one statement while both triggers were present. SQLite has no
`TRUNCATE` statement, so this vector did not exist before the port: moving engines
would have introduced a way to erase the record, and every existing test would
have stayed green. There are now three triggers per table, and
`test_truncate_is_refused` is the one that fails without the third.

**Requires a live Postgres.** The suite skips with a named reason when one is not
reachable, rather than passing silently, because a skipped guarantee test that
looks green is worse than no test. Start the container with:

    docker run -d --name carerelay-pg \\
        -e POSTGRES_PASSWORD=carerelay_test -e POSTGRES_USER=carerelay \\
        -e POSTGRES_DB=carerelay -p 15432:5432 postgres:17-alpine

The port is **15432 and not the more obvious 55432**. Windows reserves ranges
inside the dynamic port space for Hyper-V and WSL, the reservations move between
boots, and 55432 fell inside one, so binding it failed with "An attempt was made
to access a socket in a way forbidden by its access permissions", which reads
like a Docker fault and is not one. `postgres_store.DEV_DSN` carries the detail
and the skip reason below takes its port from that constant, so the recipe and
the default cannot drift apart. If a bind ever fails, check
`netsh interface ipv4 show excludedportrange protocol=tcp` before debugging the
daemon.

**What this module does not prove.** It proves the guarantee holds on the
*local* container. It does not prove it holds on Supabase, where the connection
is pooled and the server is managed. It also does not prove the rest of the
store is ported: that is `tests/test_postgres_stage2.py`, written at stage 2.
Both limits are stated rather than implied.
"""

from __future__ import annotations

import os
import pathlib
import re
from datetime import UTC, datetime

import psycopg
import pytest

from carerelay import postgres_schema, state
from carerelay.domain.models import CallbackResult, Origin, ReceiptDisposition
from carerelay.postgres_store import DEV_DSN, PostgresEpisodeStore, probe_dsn

#: Test support, not product code. The probes were public methods on
#: `PostgresEpisodeStore` until stage 2's review (finding F7): a method that
#: writes an arbitrary row into any table, past every guard the store enforces,
#: does not belong on the public surface of a production class.
from _postgres_probes import AppendOnlyProbes

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)


def _reachable() -> bool:
    try:
        with psycopg.connect(probe_dsn(), connect_timeout=2):
            return True
    except Exception:
        return False


#: The port the default DSN names, read out of it rather than repeated, so this
#: recipe cannot drift from `DEV_DSN` and tell the next person to bind a port
#: Windows has reserved.
_DEV_PORT = DEV_DSN.rsplit(":", 1)[1].split("/")[0]

requires_postgres = pytest.mark.skipif(
    not _reachable(),
    reason=(
        "no Postgres reachable at CARERELAY_TEST_DSN. Start the container the "
        "default DSN names: docker run -d --name carerelay-pg "
        "-e POSTGRES_PASSWORD=carerelay_test -e POSTGRES_USER=carerelay "
        "-e POSTGRES_DB=carerelay -p " + _DEV_PORT + ":5432 postgres:17-alpine. "
        "This test is deliberately not silently green."
    ),
)


@pytest.fixture()
def store() -> PostgresEpisodeStore:
    """A store on a clean schema.

    The tables are dropped and rebuilt rather than truncated, because TRUNCATE is
    refused by the very triggers under test. That is not a workaround: it is the
    guarantee working, and it is why the schema has to stay droppable.

    `forget_applied_schema` is called first because D1 makes the DDL a
    once-per-process step: this fixture drops the tables, so the marker that says
    the schema is already applied has to be cleared or the next store built for
    this DSN would skip the rebuild and find nothing.
    """
    PostgresEpisodeStore.forget_applied_schema(probe_dsn())
    s = PostgresEpisodeStore(probe_dsn())
    with s._conn.cursor() as cur:
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        names = [row[0] for row in cur.fetchall()]
        if names:
            cur.execute(
                "DROP TABLE IF EXISTS "
                + ", ".join(f'"{name}"' for name in names)
                + " CASCADE"
            )
        cur.execute(postgres_schema.SCHEMA_SQL)
        cur.execute(postgres_schema.append_only_ddl())
    s._conn.commit()
    yield s
    s.close()


@pytest.fixture()
def probes(store: PostgresEpisodeStore) -> AppendOnlyProbes:
    """The append-only probes, on the store's own connection.

    `store._conn` rather than a second connection, on purpose: a refusal then
    also proves the store's connection is not in some state that bypasses the
    trigger. A separate connection would prove the guarantee lives in the
    database and nothing more.
    """
    return AppendOnlyProbes(store._conn)


def _seed_episode(store: PostgresEpisodeStore, episode_id: str = "ep-1") -> None:
    with store._conn.cursor() as cur:
        cur.execute(
            "INSERT INTO episodes (id, persona, created_at) VALUES (%s, %s, %s)",
            (episode_id, "self", "2026-10-04T12:00:00+00:00"),
        )
    store._conn.commit()


# ---------------------------------------------------------------------------
# The schema is the SQLite schema
# ---------------------------------------------------------------------------


def _columns_of(ddl: str) -> dict[str, set[str]]:
    """Parse `CREATE TABLE` blocks into {table: {column, ...}}.

    Deliberately crude and deliberately strict about the shape it expects: it
    strips the leading keyword, takes the block up to the first closing paren, and
    keeps the first word of each line unless that line opens a constraint. It
    would not survive arbitrary SQL, and it does not need to, because its only
    caller feeds it two files this project owns.
    """
    tables: dict[str, set[str]] = {}
    for match in re.finditer(
        r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.*?)\n\);", ddl, re.DOTALL
    ):
        name, body = match.group(1), match.group(2)
        columns: set[str] = set()
        for raw in body.splitlines():
            line = raw.strip().rstrip(",")
            if not line:
                continue
            head = line.split()[0].upper()
            if head in {"CHECK", "UNIQUE", "PRIMARY", "FOREIGN", "CONSTRAINT"}:
                continue
            columns.add(line.split()[0])
        tables[name] = columns
    return tables


class TestTheTwoSchemasAgree:
    """The port is a port, not a rewrite.

    The first draft of `postgres_schema.py` invented columns for `restatements`,
    `barriers`, `escalations`, `evidence` and `human_acceptances`, and gave three
    tables a `SERIAL` key that SQLite gives a `TEXT` one. Nothing caught it,
    because no test compared the two. This class is that test.
    """

    def test_every_table_exists_in_both_engines(self) -> None:
        """Set equality, not a subset. A Postgres-only table is a defect.

        **The defect this assertion was too weak to catch.** The first version
        asserted `sqlite_tables <= postgres_tables`. That is satisfied by an extra
        table on the Postgres side, and one existed: `transcript_confirmations`,
        a table with no SQLite counterpart and no append-only triggers, which the
        live instance would let a caller UPDATE, DELETE and TRUNCATE. A subset
        assertion answers "did the port lose a table", which is only half the
        question; the other half is "did the port invent one". Equality is the
        check that asks both.
        """
        sqlite_tables = set(_columns_of(state._SCHEMA_SQL))
        postgres_tables = set(_columns_of(postgres_schema.SCHEMA_SQL))
        assert sqlite_tables == postgres_tables, (
            f"missing from Postgres: {sorted(sqlite_tables - postgres_tables)}; "
            f"present only in Postgres: {sorted(postgres_tables - sqlite_tables)}"
        )

    def test_every_schema_table_is_guarded_or_named_as_unguarded(self) -> None:
        """Every table is append-only, or is declared unguarded with a reason.

        **Why the trigger count could not catch this.** "15 tables, 42 triggers"
        is literally true and still conceals an unguarded table, because 42 is 14
        times 3. The suite asserted that the two append-only lists agreed, which
        both engines satisfied by omitting the same table, so a table could sit in
        the schema with no guard and no failure. This test inverts the question:
        it starts from the schema and requires every table in it to be accounted
        for, so a table added to `SCHEMA_SQL` and forgotten in
        `APPEND_ONLY_TABLES` fails here rather than shipping unguarded.
        """
        schema_tables = set(_columns_of(postgres_schema.SCHEMA_SQL))
        guarded = set(postgres_schema.APPEND_ONLY_TABLES)
        declared = set(postgres_schema.UNGUARDED_TABLES)
        unaccounted = schema_tables - guarded - declared
        assert unaccounted == set(), (
            "these tables are in the schema but neither append-only nor declared "
            f"unguarded: {sorted(unaccounted)}"
        )
        overlap = guarded & declared
        assert overlap == set(), (
            f"tables cannot be both guarded and declared unguarded: {sorted(overlap)}"
        )
        assert guarded | declared == schema_tables, (
            "the append-only and unguarded lists must together cover the schema"
        )

    def test_every_sqlite_column_exists_in_postgres(self) -> None:
        sqlite_tables = _columns_of(state._SCHEMA_SQL)
        postgres_tables = _columns_of(postgres_schema.SCHEMA_SQL)
        problems: list[str] = []
        for table, columns in sqlite_tables.items():
            if table not in postgres_tables:
                continue
            missing = columns - postgres_tables[table]
            if missing:
                problems.append(f"{table}: {sorted(missing)}")
        assert problems == [], f"columns lost in the port: {problems}"

    def test_the_append_only_lists_are_identical(self) -> None:
        """A table guarded on one engine and not the other is the whole defect.

        Both lists are hand-maintained, so this is the check that keeps them
        honest. It is set equality, not a subset, because a table added to
        Postgres and forgotten in SQLite would be as bad as the reverse.
        """
        assert set(postgres_schema.APPEND_ONLY_TABLES) == set(state.APPEND_ONLY_TABLES)


# ---------------------------------------------------------------------------
# The guarantee
# ---------------------------------------------------------------------------


@requires_postgres
class TestTheRecordCannotBeAltered:
    """UPDATE, DELETE and TRUNCATE are all refused, on the real engine.

    **Why every probe seeds a row first.** The first version of these probes
    issued `UPDATE ... WHERE false` and `DELETE ... WHERE false`, reasoning that
    a refusal is raised regardless of whether a row matches. It is not: a
    `FOR EACH ROW` trigger fires per row, and `WHERE false` matches no rows, so
    **all fourteen tables reported silence** and the tests only passed because
    `pytest.raises` was being satisfied by the surrounding loop's rolled-back
    state. The probe now writes a row and mutates it, so the trigger has
    something to fire against. `TestTheProbesReachTheGuard` is the control that
    keeps this from regressing.
    """

    def test_update_is_refused_on_every_table(
        self, store: PostgresEpisodeStore, probes: AppendOnlyProbes
    ) -> None:
        """The row is asserted present **at mutation time**, not merely seeded.

        The seed and the mutation are in one statement pair here, and
        `store._conn.rollback()` at the end of each iteration undoes the seed as
        well as the failed mutation. That is correct for this test, but it means
        the row only exists because the seed runs immediately before, on the same
        iteration. An earlier standalone probe of mine seeded once and then ran
        UPDATE and DELETE in sequence; the UPDATE's rollback took the seed with
        it, the table was empty when DELETE ran, and DELETE reported **0 of 14
        refused**. The code was right and the probe was wrong, which is exactly
        the failure mode this class exists to prevent. The count assertion below
        makes the dependency explicit rather than implicit.
        """
        for table in postgres_schema.APPEND_ONLY_TABLES:
            probes.seed_one_row(table)
            assert self._rows(store, table) >= 1, (
                f"{table}: nothing seeded, so a row-level trigger cannot fire"
            )
            with pytest.raises(psycopg.errors.RestrictViolation) as caught:
                probes.refuse_update(table)
            assert "append-only" in str(caught.value), table
            assert "UPDATE is refused" in str(caught.value), table
            store._conn.rollback()

    def test_delete_is_refused_on_every_table(
        self, store: PostgresEpisodeStore, probes: AppendOnlyProbes
    ) -> None:
        """Seeded and asserted on the same iteration, for the reason given above.

        This test must not inherit its row from a previous test or a previous
        verb's seed. It re-seeds immediately before it mutates and asserts the
        row is there, so it would fail loudly rather than pass emptily if the
        seeding were removed or reordered.
        """
        for table in postgres_schema.APPEND_ONLY_TABLES:
            probes.seed_one_row(table)
            assert self._rows(store, table) >= 1, (
                f"{table}: nothing seeded, so a row-level trigger cannot fire"
            )
            with pytest.raises(psycopg.errors.RestrictViolation) as caught:
                probes.refuse_delete(table)
            assert "DELETE is refused" in str(caught.value), table
            store._conn.rollback()

    @staticmethod
    def _rows(store: PostgresEpisodeStore, table: str) -> int:
        with store._conn.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {table}")
            return cur.fetchone()[0]

    def test_truncate_is_refused(
        self, store: PostgresEpisodeStore, probes: AppendOnlyProbes
    ) -> None:
        """**The test this whole stage exists for.**

        Without the `BEFORE TRUNCATE` statement-level trigger this fails, and the
        table is emptied. The assertion checks the rows survived rather than only
        that an error was raised, because the failure mode being guarded against
        is silent data loss, and an error message alone would not show it.
        """
        _seed_episode(store, "ep-truncate")
        for table in postgres_schema.APPEND_ONLY_TABLES:
            with pytest.raises(psycopg.errors.RestrictViolation) as caught:
                probes.refuse_truncate(table)
            assert "TRUNCATE is refused" in str(caught.value), table
            store._conn.rollback()

        with store._conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM episodes WHERE id = %s", ("ep-truncate",))
            assert cur.fetchone()[0] == 1, "TRUNCATE erased a guarded row"

    def test_a_mutation_that_drops_the_truncate_trigger_is_caught(
        self, store: PostgresEpisodeStore
    ) -> None:
        """The control that proves `test_truncate_is_refused` is evidence.

        The truncate triggers are dropped here and the table is truncated
        successfully. That is the defect. The test above must be the thing that
        fails when this is the state of the database, and this test proves the
        fixture can reach that state at all, so a green `test_truncate_is_refused`
        means something.

        **Every truncate trigger is dropped, not just `episodes`'.** The probe
        truncates with `CASCADE`, and `TRUNCATE episodes CASCADE` reaches all
        fourteen tables that reference `episodes` (measured: the whole schema).
        Postgres fires each cascaded table's own `BEFORE TRUNCATE` trigger in
        turn, so dropping only `episodes_no_truncate` still meets
        `dispositions_no_truncate` and the control fails for a reason that has
        nothing to do with the trigger under test. `CASCADE` is also why a bare
        `TRUNCATE` cannot be used here: it would be refused by the `dispositions`
        foreign key before any trigger ran.
        """
        _seed_episode(store, "ep-control")
        with store._conn.cursor() as cur:
            for table in postgres_schema.APPEND_ONLY_TABLES:
                cur.execute(f"DROP TRIGGER {table}_no_truncate ON {table}")
        store._conn.commit()

        with store._conn.cursor() as cur:
            cur.execute("TRUNCATE episodes CASCADE")
        store._conn.commit()

        with store._conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM episodes")
            assert cur.fetchone()[0] == 0, "the control did not reproduce the defect"

    def test_drop_table_still_works(self, store: PostgresEpisodeStore) -> None:
        """The guard must not make the tables immortal, or the schema cannot be
        rebuilt and the migration cannot be repeated."""
        with store._conn.cursor() as cur:
            cur.execute("DROP TABLE episodes CASCADE")
            cur.execute(
                "SELECT to_regclass('public.episodes') IS NULL AS gone"
            )
            assert cur.fetchone()[0] is True
        store._conn.rollback()


@requires_postgres
class TestTheProbesReachTheGuard:
    """The control for the control. Without this, the seeding can regress.

    **The defect this class exists for.** The first probes used `WHERE false`.
    That matched no rows, so no `FOR EACH ROW` trigger fired, so no error was
    raised on any table. `test_update_is_refused_on_every_table` was still green
    for a while, because `pytest.raises(RestrictViolation)` was being satisfied
    by loop state rather than by the guard. A test that asserts "a refusal
    happens" cannot tell the difference between a guard that refused and a probe
    that reached nothing.

    These tests assert the positive half: **the row was genuinely there to be
    mutated**, and the statement genuinely matched it. If the seed stops writing
    rows, or a predicate goes back to `WHERE false`, the mutation silently
    affects nothing and these fail.
    """

    def test_a_seeded_row_is_visible_to_a_count(
        self, store: PostgresEpisodeStore, probes: AppendOnlyProbes
    ) -> None:
        """The seed actually writes a row into the table it is asked about.

        Trivially true, and that is the point: it is the assertion whose absence
        let `WHERE false` look healthy. The bound is "at least one", not "exactly
        one", because seeding a child also seeds its parents and a later table in
        the loop can therefore add a second row to an earlier one. What matters
        is that the target table is non-empty after the seed, because a row-level
        trigger fires per row and a table with no rows refuses nothing.
        """
        for table in postgres_schema.APPEND_ONLY_TABLES:
            before = self._count(store, table)
            probes.seed_one_row(table)
            after = self._count(store, table)
            assert after > before, f"{table}: the seed wrote no row"
            assert after >= 1, f"{table}: the table is empty, so nothing can fire"
            store._conn.rollback()

    def test_the_update_predicate_matches_the_seeded_row(
        self, store: PostgresEpisodeStore
    ) -> None:
        """`UPDATE ... WHERE true` really matches.

        Proven on a table with no append-only trigger, so the statement can
        complete: if the predicate matched nothing, `rowcount` would be 0. This
        is the measurement that `WHERE false` failed.
        """
        with store._conn.cursor() as cur:
            cur.execute("CREATE TABLE probe_control (id TEXT PRIMARY KEY)")
            cur.execute(
                "INSERT INTO probe_control (id) VALUES (%s)", ("row-1",)
            )
            cur.execute("UPDATE probe_control SET id = id WHERE true")
            assert cur.rowcount == 1, "the predicate matched no row"
            cur.execute("UPDATE probe_control SET id = id WHERE false")
            assert cur.rowcount == 0, (
                "the old predicate unexpectedly matched, so this control no "
                "longer demonstrates the defect"
            )
        store._conn.rollback()

    @staticmethod
    def _count(store: PostgresEpisodeStore, table: str) -> int:
        with store._conn.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {table}")
            return cur.fetchone()[0]


@requires_postgres
class TestOnConflictFollowsTheSqliteRule:
    """The O1 defence, re-proved rather than translated.

    SQLite refuses `INSERT OR REPLACE` because REPLACE deletes the conflicting
    row and `recursive_triggers = ON` sends that implicit delete through the
    DELETE trigger. Postgres has no REPLACE; the equivalent is
    `ON CONFLICT ... DO UPDATE`, which goes through the UPDATE trigger instead.
    Same outcome, different mechanism, so the SQLite reasoning does not carry and
    the behaviour had to be measured.
    """

    def test_on_conflict_do_update_is_refused(self, store: PostgresEpisodeStore) -> None:
        _seed_episode(store, "ep-conflict")
        with store._conn.cursor() as cur:
            with pytest.raises(psycopg.errors.RestrictViolation) as caught:
                cur.execute(
                    "INSERT INTO episodes (id, persona, created_at) "
                    "VALUES (%s, %s, %s) "
                    "ON CONFLICT (id) DO UPDATE SET persona = EXCLUDED.persona",
                    ("ep-conflict", "other", "2026-10-04T12:00:00+00:00"),
                )
        assert "UPDATE is refused" in str(caught.value)
        store._conn.rollback()

    def test_on_conflict_do_nothing_is_allowed(self, store: PostgresEpisodeStore) -> None:
        """The control. A rule that refused every conflict would also refuse the
        benign duplicate, and an idempotent re-registration depends on this
        succeeding."""
        _seed_episode(store, "ep-benign")
        with store._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO episodes (id, persona, created_at) "
                "VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                ("ep-benign", "self", "2026-10-04T12:00:00+00:00"),
            )
        store._conn.commit()
        with store._conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM episodes WHERE id = %s", ("ep-benign",))
            assert cur.fetchone()[0] == 1


# ---------------------------------------------------------------------------
# The transaction wrapper
# ---------------------------------------------------------------------------


@requires_postgres
class TestTheCallbackPathOnPostgres:
    """The duplicate-callback race, on an engine with no `BEGIN IMMEDIATE`."""

    def _open_attempt(self, store: PostgresEpisodeStore) -> str:
        """An episode, a granted consent and an attempt on it.

        **The consent row is stage 2's doing, not a bolt-on.** Stage 1's
        `record_callback_once` was a stub of the callback path; the full port
        enforces the consent re-check inside the locked transaction, which is the
        rule the product actually needs (a callback that arrives after a
        revocation must be refused, not applied). Seeding an attempt with no
        consent therefore stopped working, and it stopped working *correctly*:
        the two tests below were passing against a store that had not yet
        implemented the rule. They now seed what the rule reads.
        """
        _seed_episode(store, "ep-cb")
        with store._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO consents (episode_id, scope, state, version,"
                " recorded_at) VALUES (%s, %s, %s, %s, %s)"
                " ON CONFLICT (episode_id, scope, version) DO NOTHING",
                (
                    "ep-cb",
                    state.CLINICAL_SCOPE,
                    "granted",
                    1,
                    "2026-10-04T12:00:00+00:00",
                ),
            )
            cur.execute(
                "INSERT INTO attempts (id, episode_id, route_id, purpose_id,"
                " idempotency_key, consent_version, opened_at)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (
                    "at-1",
                    "ep-cb",
                    "route-nurse",
                    "pur-nurse",
                    "key-1",
                    1,
                    "2026-10-04T12:00:00+00:00",
                ),
            )
        store._conn.commit()
        return "at-1"

    def test_a_first_callback_is_applied(self, store: PostgresEpisodeStore) -> None:
        attempt_id = self._open_attempt(store)
        outcome = store.record_callback_once(
            attempt_id,
            "cb-key-1",
            CallbackResult(payload="{}", transition=None),
            Origin.LOCAL_SIM,
            now_utc=NOW,
        )
        assert outcome.disposition is ReceiptDisposition.APPLIED
        assert outcome.applied is True

    def test_a_repeated_callback_is_a_duplicate_and_writes_no_second_receipt(
        self, store: PostgresEpisodeStore
    ) -> None:
        """The property `BEGIN IMMEDIATE` used to provide.

        On Postgres the serialisation comes from `SELECT ... FOR UPDATE` on the
        attempt row. This test cannot distinguish the lock from a lucky ordering
        in a single-threaded run; what it does prove is that the duplicate is
        detected and recorded. The two-writer case is
        `tests/test_postgres_stage2.py::TestTwoWritersAtOneKey`, which is where a
        real race is driven from two connections.
        """
        attempt_id = self._open_attempt(store)
        first = store.record_callback_once(
            attempt_id,
            "cb-key-2",
            CallbackResult(payload="{}", transition=None),
            Origin.LOCAL_SIM,
            now_utc=NOW,
        )
        second = store.record_callback_once(
            attempt_id,
            "cb-key-2",
            CallbackResult(payload="{}", transition=None),
            Origin.LOCAL_SIM,
            now_utc=NOW,
        )
        assert first.disposition is ReceiptDisposition.APPLIED
        assert second.disposition is ReceiptDisposition.DUPLICATE
        assert second.applied is False

        with store._conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM callbacks WHERE accepted = 1 AND callback_key = %s",
                ("cb-key-2",),
            )
            assert cur.fetchone()[0] == 1

    def test_an_unknown_attempt_is_refused(self, store: PostgresEpisodeStore) -> None:
        with pytest.raises(state.AttemptNotFound):
            store.record_callback_once(
                "no-such-attempt",
                "cb-key-3",
                CallbackResult(payload="{}", transition=None),
                Origin.LOCAL_SIM,
                now_utc=NOW,
            )


# ---------------------------------------------------------------------------
# The D1 and D2 judgement calls
# ---------------------------------------------------------------------------


@requires_postgres
class TestConnectionAndLockHandling:
    """D1 (schema DDL once per process per DSN) and D2 (`lock_timeout` is a
    parameter, and its branch is reachable)."""

    def test_the_schema_ddl_is_not_reapplied_for_a_second_store(
        self, store: PostgresEpisodeStore
    ) -> None:
        """D1: the second store for a DSN skips the DDL, and proves it did.

        The proof is not "it was fast". A trigger is dropped and is still absent
        after a new store is built, which can only be true if the new store did
        not run `append_only_ddl()` (which would have recreated every trigger).
        """
        with store._conn.cursor() as cur:
            cur.execute("DROP TRIGGER episodes_no_update ON episodes")
        store._conn.commit()

        second = PostgresEpisodeStore(probe_dsn())
        try:
            with second._conn.cursor() as cur:
                cur.execute(
                    "SELECT count(*) FROM pg_trigger WHERE tgname = %s",
                    ("episodes_no_update",),
                )
                assert cur.fetchone()[0] == 0, (
                    "the DDL ran again for a second store on the same DSN, so the "
                    "once-per-process optimisation in D1 is not in force"
                )
        finally:
            second.close()

    def test_force_reapplies_the_schema(self, store: PostgresEpisodeStore) -> None:
        """The control for D1: `init_schema(force=True)` still rebuilds.

        Without this, a store that silently never applies the DDL would pass the
        test above. This one drops a trigger, forces the schema, and requires the
        trigger back.
        """
        with store._conn.cursor() as cur:
            cur.execute("DROP TRIGGER episodes_no_update ON episodes")
        store._conn.commit()
        store.init_schema(force=True)
        with store._conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM pg_trigger WHERE tgname = %s",
                ("episodes_no_update",),
            )
            assert cur.fetchone()[0] == 1, "force did not reapply the schema"

    def test_a_short_lock_timeout_reaches_lock_contention(
        self, store: PostgresEpisodeStore
    ) -> None:
        """D2: the `LockNotAvailable` to `LockContention` branch is now reachable.

        The review flagged this branch as unproven because no test ever held a
        lock against another. This opens a second connection, takes a row lock
        and holds it, then has the store try to lock the same row with a
        sub-second `lock_timeout`. It must raise the typed `LockContention`, not a
        raw driver error and not hang.
        """
        _seed_episode(store, "ep-lock")
        store._conn.commit()

        blocker = psycopg.connect(probe_dsn(), autocommit=False)
        try:
            with blocker.cursor() as bcur:
                bcur.execute("SELECT id FROM episodes WHERE id = %s FOR UPDATE", ("ep-lock",))
            starved = PostgresEpisodeStore(probe_dsn(), lock_timeout_s=0.5)
            try:
                with pytest.raises(state.LockContention):
                    with starved._write() as cur:
                        cur.execute(
                            "SELECT id FROM episodes WHERE id = %s FOR UPDATE",
                            ("ep-lock",),
                        )
            finally:
                starved.close()
        finally:
            blocker.rollback()
            blocker.close()


# ---------------------------------------------------------------------------
# What this module does not prove
# ---------------------------------------------------------------------------


class TestStatedLimits:
    """Kept as tests so the limits cannot be quietly deleted."""

    def test_the_schema_file_names_the_two_deliberate_differences(self) -> None:
        """A port with no stated differences is a port nobody checked.

        The two here are `SERIAL` for the autoincrement key and
        `DOUBLE PRECISION` for the one `REAL` column. Both are named in the
        module docstring, and this asserts the naming survives an edit.
        """
        source = (
            pathlib.Path(__file__).resolve().parents[1]
            / "src"
            / "carerelay"
            / "postgres_schema.py"
        ).read_text(encoding="utf-8")
        assert "INTEGER PRIMARY KEY` becomes `SERIAL PRIMARY KEY" in source
        assert "REAL` becomes `DOUBLE PRECISION" in source

    def test_this_module_is_skipped_rather_than_green_without_postgres(self) -> None:
        """If the skip condition were removed the suite would report green on a
        machine with no Postgres, which is the failure mode this guards.

        The skip is now per class rather than module-wide, so this also checks
        that every class that opens a connection carries the marker and that the
        two that do not are deliberately left off it.
        """
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        assert "skipif" in source
        assert "deliberately not silently green" in source
        for needs_engine in (
            "class TestTheRecordCannotBeAltered",
            "class TestTheProbesReachTheGuard",
            "class TestOnConflictFollowsTheSqliteRule",
            "class TestTheCallbackPathOnPostgres",
        ):
            marker_index = source.index(needs_engine)
            preceding = source[max(0, marker_index - 40) : marker_index]
            assert "@requires_postgres" in preceding, (
                f"{needs_engine} opens a connection but is not marked "
                "@requires_postgres, so it would run or skip without a stated reason"
            )
        for no_engine in (
            "class TestTheTwoSchemasAgree",
            "class TestStatedLimits",
        ):
            marker_index = source.index(no_engine)
            preceding = source[max(0, marker_index - 40) : marker_index]
            assert "@requires_postgres" not in preceding, (
                f"{no_engine} needs no database and would be skipped needlessly, "
                "which is how the F2 parity check went unrun on a machine with no "
                "Postgres"
            )
