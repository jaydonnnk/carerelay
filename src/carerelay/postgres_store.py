"""A Postgres episode store, and the append-only guarantee on a new engine.

Slice 7b, stage 1. **Scope, stated so it is not mistaken for the finished port:**
this file covers the schema, the triggers, the transaction wrapper and the
callback idempotency path. It does **not** yet cover all 45 methods of
`SqliteEpisodeStore`. Stage 1 exists to answer one question before the rest is
built: does the append-only guarantee survive the move to Postgres, and does the
duplicate-callback race still resolve correctly on an engine with no
`BEGIN IMMEDIATE`?

**Why one connection and not a pool.** `SqliteEpisodeStore` holds one connection
for the process lifetime and the service is single-worker. A pool would add a
concept the deployment does not need. The connection is opened with
`autocommit=False` so `_write()` owns every transaction boundary explicitly,
which is the Postgres counterpart of the SQLite connection's behaviour.

**`BEGIN IMMEDIATE` has no Postgres equivalent, and the difference is real.**
SQLite's IMMEDIATE takes the write lock at the *start* of the transaction, which
is what makes the callback lookup-then-insert atomic: a second writer cannot read
"no such key" and then fail at COMMIT. Postgres uses MVCC, so a plain
`BEGIN`/`SELECT` would let two writers both see no row. The equivalent is
`SELECT ... FOR UPDATE` on the row being guarded, which serialises the second
writer behind the first. Where there is no row to lock, the UNIQUE constraint is
the backstop, and its violation is translated rather than leaked, because a raw
`UniqueViolation` is indistinguishable to a caller from any other driver error.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

import psycopg
from psycopg import sql

from . import postgres_schema
from .domain.models import CallbackResult, ReceiptDisposition
from .state import (
    AttemptNotFound,
    LockContention,
    ReceiptOutcome,
    _digest,
    _iso,
    _utc,
)

#: The DSN the tests use, from the environment, with the local container default.
DEV_DSN = "postgresql://carerelay:carerelay_test@127.0.0.1:55432/carerelay"


def probe_dsn() -> str:
    """The test DSN.

    The password in `DEV_DSN` belongs to a disposable container the test session
    starts on port 55432. It is not a deployment credential and not a secret. A
    DSN for the real Supabase instance is never written into this repository.
    """
    return os.getenv("CARERELAY_TEST_DSN", DEV_DSN)


#: The DSNs whose schema has already been applied in this process. `PostgresEpisodeStore`
#: skips the schema and 42-trigger DDL when it has run once for a given DSN, because
#: the DDL is a migration step, not part of opening a store, and on Supabase it adds
#: seconds to every construction (D1, decided 4 October 2026). A fresh process
#: re-applies it, so the schema is still created on first use; `--init-schema` (or
#: `init_schema()`) is the explicit way to force it.
_SCHEMA_APPLIED: set[str] = set()


class PostgresEpisodeStore:
    """The Postgres store. Stage 1 surface only, as documented above.

    **D1, decided 4 October 2026: the connection is held, and the schema DDL runs
    once per process per DSN.** `__init__` connects and, on the first store for a
    given DSN in this process, applies `SCHEMA_SQL` and `append_only_ddl()`. The
    second and later stores for the same DSN reuse the already-migrated schema and
    skip the DDL. Measured on Supabase, the connection alone is roughly two seconds
    and the 42-trigger DDL runs on top of it, so re-running the DDL per construction
    is not survivable on a request path. A connection pool is deliberately **not**
    used: the deployment is single-worker and a pool adds a concept it does not
    need, which is the same reasoning the SQLite store applies.
    """

    def __init__(
        self,
        dsn: str,
        *,
        connect_timeout_s: int = 5,
        lock_timeout_s: float = 5.0,
    ) -> None:
        self.dsn = dsn
        self.connect_timeout_s = connect_timeout_s
        #: The per-transaction lock wait, in seconds (D2). A float so a test can
        #: set a sub-second value to reach the `LockNotAvailable` branch.
        self.lock_timeout_s = lock_timeout_s
        #: The allowed-value cache, **per instance**. It was a class attribute
        #: first, which works only because there is one database and the values
        #: are deterministic; a second DSN or an altered schema in one process
        #: would serve a stale set. `_seen_allowed` records the `(table, column)`
        #: pairs already looked up, so a missing key is not confused with a
        #: cached empty list (a column with no enumerated CHECK).
        self._allowed_cache: dict[tuple[str, str], list[str]] = {}
        self._seen_allowed: set[tuple[str, str]] = set()
        self._conn = psycopg.connect(
            dsn, autocommit=False, connect_timeout=connect_timeout_s
        )
        self.init_schema()

    # -- lifecycle ---------------------------------------------------------

    def init_schema(self, *, force: bool = False) -> None:
        """Apply the schema and the 42-trigger DDL, unless already applied.

        The explicit entry point for the DDL that `__init__` runs on the first
        store per DSN. `force=True` re-applies it, which is what a migration or a
        test that has dropped the tables needs. Idempotent either way, because
        `append_only_ddl()` emits drop-then-create for every trigger and the
        `CREATE TABLE` statements carry `IF NOT EXISTS`.
        """
        if not force and self.dsn in _SCHEMA_APPLIED:
            return
        with self._conn.cursor() as cur:
            cur.execute(postgres_schema.SCHEMA_SQL)
            cur.execute(postgres_schema.append_only_ddl())
        self._conn.commit()
        _SCHEMA_APPLIED.add(self.dsn)

    @staticmethod
    def forget_applied_schema(dsn: str | None = None) -> None:
        """Clear the per-process schema-applied marker.

        For tests that drop the tables and need the next store to rebuild them,
        and for a long-lived process that has deliberately dropped the schema.
        Passing no argument clears every DSN.
        """
        if dsn is None:
            _SCHEMA_APPLIED.clear()
        else:
            _SCHEMA_APPLIED.discard(dsn)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> PostgresEpisodeStore:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- transactions ------------------------------------------------------

    @contextmanager
    def _write(self) -> Iterator[psycopg.Cursor]:
        """One logical write, in one transaction, with a bounded lock wait.

        This wrapper owns the transaction boundary and the translation of a lock
        timeout into `LockContention`, which is the O2 contract. A `lock_timeout`
        is set per transaction so a blocked writer fails loudly after a bounded
        wait rather than hanging the request, which is what `busy_timeout` did
        for SQLite.

        **D2, decided 4 October 2026: the timeout stays at 5 s, and it is now an
        explicit parameter rather than a literal.** The number was inherited from
        the SQLite `busy_timeout` and chosen against a sub-millisecond local
        engine, but the live Supabase link measures roughly a quarter second per
        statement, so what matters is not the per-statement cost but how many
        statements a single `_write()` issues. Five seconds leaves room for a
        short queue of quarter-second statements and still fails loudly rather
        than hanging a patient-facing request. It is exposed as `lock_timeout_s`
        so stage 2 can tune it under the O2 test with a measurement rather than
        another guess, and so a test can set a short timeout to exercise the
        `LockNotAvailable` branch, which no test currently reaches.

        The row lock that makes the callback lookup atomic is applied at the call
        site by `_lock_or_absent`, because it is a row lock and the row differs
        per operation. SQLite's equivalent is a database-wide lock taken here.
        """
        cur = self._conn.cursor()
        timeout = f"{self.lock_timeout_s}s"
        try:
            # `SET LOCAL` takes no bind parameter, so the value is interpolated;
            # it is a validated number, not caller text, so this is not an
            # injection surface.
            cur.execute(f"SET LOCAL lock_timeout = '{timeout}'")
            yield cur
        except psycopg.errors.LockNotAvailable as exc:
            self._conn.rollback()
            raise LockContention(
                f"the write lock was not acquired within {timeout}, so nothing "
                f"was written: {exc}"
            ) from exc
        except BaseException:
            self._conn.rollback()
            raise
        else:
            self._conn.commit()
        finally:
            cur.close()

    @staticmethod
    def _lock_or_absent(
        cur: psycopg.Cursor, query: str, params: tuple
    ) -> tuple | None:
        """`SELECT ... FOR UPDATE`, returning None when there is no row.

        Split out so the locking rule is visible at every call site that depends
        on it rather than implied by the SQL string.
        """
        cur.execute(query, params)
        return cur.fetchone()

    # -- append-only probes, for the tests ---------------------------------

    #: Sentinel values the seeder writes into every `NOT NULL` column it has to
    #: fill. `episode_id` is deliberately the same string in every table so the
    #: one episode insert above satisfies every foreign key at once.
    SEED_EPISODE_ID = "seed-episode"

    def seed_one_row(self, table: str) -> None:
        """Write one row into `table`, and into its parents, so a row-level probe
        has something to hit.

        **Why this exists.** The first version of the UPDATE and DELETE probes
        below issued `... WHERE false`, on the theory that a refusal would be
        raised regardless of whether a row matched. It is not: a `FOR EACH ROW`
        trigger fires per row, and `WHERE false` matches no rows, so **nothing
        was raised on any of the fourteen tables**. The probe reported silence
        and the tests read that silence as "the guard is present". That is the
        same defect class as A7-1: a guard smaller than it claims, green anyway.

        A row-level guard can only be tested against a row, and the row has to
        satisfy the foreign keys, so this inserts the parents first, in FK order.
        The graph is one level deep apart from `attempt_transitions`, and it is
        small enough to walk by hand rather than topologically.

        Columns are discovered from the catalogue rather than named, so a column
        added to the schema does not silently drop out of the seed. A `NOT NULL`
        column with no default gets a type-appropriate sentinel; everything else
        is left to its default.

        `callbacks` is the one table the generic picker cannot seed, and it is
        seeded explicitly below. Its constraints span columns, which a picker
        that chooses each value independently cannot satisfy by construction.
        """
        self._seed_parents_for(table)
        if table == "callbacks":
            self._seed_callbacks_row()
            return
        columns, values = self._seed_row_for(table)
        identifiers = [sql.Identifier(name) for name in columns]
        placeholders = [sql.Placeholder() for _ in columns]
        statement = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(identifiers),
            sql.SQL(", ").join(placeholders),
        )
        with self._conn.cursor() as cur:
            self._assert_row_satisfies_checks(cur, table, columns, values)
            cur.execute(statement, values)

    def _assert_row_satisfies_checks(
        self,
        cur: psycopg.Cursor,
        table: str,
        columns: list[str],
        values: list[object],
    ) -> None:
        """Prove the value the seeder derived is one the **real** constraint accepts.

        The picker reads the allowed set out of the catalogue, which means a
        schema edit changes the picker's answer. That is the point (the seeder
        does not encode the domain twice) and the hazard (a domain-wrong widening
        is adapted to silently). This closes the hazard for the row the picker
        actually built: it inserts that row into a scratch copy of the table that
        carries the same `CHECK` constraints but none of the append-only triggers,
        so Postgres evaluates the real constraint definition against the real
        values. A `CheckViolation` here means the seeder derived a value the schema
        does not accept, which is the failure the previous version deferred to
        luck.

        The scratch table is `LIKE table INCLUDING CONSTRAINTS INCLUDING
        DEFAULTS`. `INCLUDING CONSTRAINTS` copies the `CHECK`s and the `NOT
        NULL`s, which is the whole point: a `CHECK` is what the picker reads, so
        a `CHECK` is what this verifies. `INCLUDING DEFAULTS` is load-bearing too,
        and its absence was a real defect: the seeder omits every column that has
        a default (`_seed_row_for` selects `column_default IS NULL`), relying on
        the real table to fill it, so a scratch copy without the defaults inserts
        `NULL` into an omitted `NOT NULL` column and raises `NotNullViolation`
        before any `CHECK` is evaluated. That is what happened to
        `dispositions.id`, and it failed three tests rather than guarding them.
        Neither clause copies triggers (there is no `INCLUDING TRIGGERS`), which
        is what lets the insert complete at all.

        The scratch table lives in a rolled-back subtransaction so it never
        survives this call, and it is named with a fixed prefix so a leak from a
        crashed run is recognisable rather than mysterious. The whole scratch
        dance runs inside a savepoint because a `CHECK` failure aborts the
        transaction, and every statement after that is refused until a rollback.
        Rolling back to the savepoint keeps the caller's transaction usable and
        lets the real `CheckViolation` propagate instead of being masked by an
        `InFailedSqlTransaction` raised from the cleanup.
        """
        scratch = f"_seedcheck_{table}"
        identifiers = [sql.Identifier(name) for name in columns]
        placeholders = [sql.Placeholder() for _ in columns]
        cur.execute("SAVEPOINT seed_check")
        try:
            cur.execute(
                sql.SQL("CREATE TEMP TABLE {} (LIKE {} INCLUDING CONSTRAINTS "
                        "INCLUDING DEFAULTS)").format(
                    sql.Identifier(scratch), sql.Identifier(table)
                )
            )
            cur.execute(
                sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(scratch),
                    sql.SQL(", ").join(identifiers),
                    sql.SQL(", ").join(placeholders),
                ),
                values,
            )
        except Exception:
            # The scratch insert is expected to fail when the seeder derived a
            # value the real CHECK rejects; that is the signal, not an accident.
            # Roll back to the savepoint so the outer transaction stays usable
            # and the scratch table is discarded with it; re-raise so the caller
            # sees the real violation rather than a cleanup error.
            cur.execute("ROLLBACK TO SAVEPOINT seed_check")
            cur.execute("RELEASE SAVEPOINT seed_check")
            raise
        else:
            cur.execute(
                sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(scratch))
            )
            cur.execute("RELEASE SAVEPOINT seed_check")

    def _seed_callbacks_row(self) -> None:
        """The one table whose `CHECK`s span columns, so it is written by hand.

        Three of its constraints are cross-column and pull in opposite
        directions:

        * `CHECK ((accepted = 1) OR (rejection_reason IS NOT NULL))`
        * `CHECK ((accepted = 0) OR (rejection_reason IS NULL))`
        * `CHECK ((callback_key IS NULL) = (duplicate_of IS NOT NULL))`

        Together they mean `accepted`, `rejection_reason`, `callback_key` and
        `duplicate_of` are not free: an accepted row has a key, no reason and no
        duplicate pointer; a rejected row has a reason; a duplicate row has a key
        and a duplicate pointer and no reason. The generic picker sets each
        column from its own type and constraint in isolation, which is exactly
        the shape that cannot satisfy this. `accepted = 1` with a key and no
        reason is the branch taken, matching the first accepted callback.

        Named columns rather than discovered ones, because the point of naming
        them is that the relation between them is the constraint. If a column is
        added here, the insert fails loudly rather than silently defaulting.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO callbacks (episode_id, route_id, attempt_id, "
                "callback_key, callback_key_digest, duplicate_of, accepted, "
                "rejection_reason, origin, result, payload, received_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    self.SEED_EPISODE_ID,
                    "seed-route",
                    "seed-attempt",
                    "seed-callback-key",
                    "seed-digest",
                    None,
                    1,
                    None,
                    "local-sim",
                    None,
                    "",
                    "2026-10-04T12:00:00+00:00",
                ),
            )

    def _seed_parents_for(self, table: str) -> None:
        """Insert whatever `table`'s foreign keys point at, so its own insert can
        succeed. Idempotent via `ON CONFLICT DO NOTHING`, which
        `TestOnConflictFollowsTheSqliteRule` proves is allowed by the triggers.

        The graph, read from the catalogue rather than assumed:
        `dispositions` needs `policy_versions`, everything except
        `policy_versions` needs `episodes`, and `attempt_transitions` needs
        `attempts`. `callbacks.duplicate_of` is a self-reference and is left NULL.
        """
        if table == "episodes":
            return
        if table == "policy_versions":
            return
        if table == "dispositions":
            self._seed_policy_version_row()
        self._seed_episode_row()
        if table in {"attempts", "attempt_transitions", "callbacks"}:
            self._seed_attempt_row()

    def _seed_policy_version_row(self) -> None:
        """The parent `dispositions.policy_version` points at.

        Registered before the episode because `dispositions._seed_row_for` reads
        the allowed `source` values and the FK is checked at insert time, not at
        the end of the transaction.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO policy_versions (version, content, provenance, "
                "created_at) VALUES (%s, %s, %s, %s) ON CONFLICT (version) DO NOTHING",
                (
                    "seed-policy",
                    "seed-content",
                    "local-sim",
                    "2026-10-04T12:00:00+00:00",
                ),
            )

    def _seed_episode_row(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO episodes (id, persona, created_at) VALUES (%s, %s, %s) "
                "ON CONFLICT (id) DO NOTHING",
                (self.SEED_EPISODE_ID, "self", "2026-10-04T12:00:00+00:00"),
            )

    def _seed_attempt_row(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO attempts (id, episode_id, route_id, purpose_id, "
                "idempotency_key, consent_version, opened_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                (
                    "seed-attempt",
                    self.SEED_EPISODE_ID,
                    "seed-route",
                    "seed-purpose",
                    "seed-key",
                    1,
                    "2026-10-04T12:00:00+00:00",
                ),
            )

    def _seed_row_for(self, table: str) -> tuple[list[str], list[object]]:
        """The `NOT NULL`, no-default columns of `table`, and a sentinel for each.

        Read from `information_schema` so the seeder does not encode the schema a
        second time. `SERIAL` and `DEFAULT` columns are omitted, which is what
        keeps this from having to know that `callbacks.id` is generated.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s "
                "AND is_nullable = 'NO' AND column_default IS NULL "
                "ORDER BY ordinal_position",
                (table,),
            )
            shape = cur.fetchall()
        columns: list[str] = []
        values: list[object] = []
        for name, data_type in shape:
            columns.append(name)
            values.append(self._sentinel_for(table, name, data_type))
        return columns, values

    def _sentinel_for(self, table: str, column: str, data_type: str) -> object:
        """A value the column will accept, constraints included.

        **Wherever a column is constrained to a small set, the value comes from
        that constraint rather than from the type.** The first version returned
        `1` for every integer and `seed-<table>-<column>` for every string, which
        is fine for a foreign key but violates fourteen `CHECK`s: `origin` must be
        `platform` or `local-sim`, `state` must be `granted` or `revoked`,
        `hint_level` must be `H0`..`H3`. Those six tables then raised
        `CheckViolation` **before** the append-only trigger could run, so the
        probe still did not reach the guard. Reading the allowed set from the
        catalogue is what makes the seed conform without this file encoding the
        domain a second time.

        **Foreign keys are named explicitly and checked before the type rule.**
        The generic `seed-<table>-<column>` string is the right shape for a text
        column and the wrong value for a key: `dispositions.policy_version` must
        equal the seeded policy version, not the string
        `seed-dispositions-policy_version`. Every FK column in this schema is
        listed here. A new one is caught by the seed failing, which is loud, and
        the fix is to add it to this table.

        **The limit, stated rather than implied, and what closes it.** Reading the
        allowed set from the catalogue makes the seeder *conform* to a schema
        change rather than *detect* it. Widening a text `CHECK` to a domain-wrong
        value makes the seed insert that wrong value silently, and an integer
        `CHECK (x IN (0,1))` carries no `::text` casts, so `_allowed_values`
        returns nothing and the seeder falls through to the integer default `1`,
        which happens to sit in every `0/1` set. So a schema edit does not, by
        itself, surface as a seed failure. `seed_one_row` closes that by asking
        Postgres to evaluate the **real constraint** against the row it just
        built (`_assert_row_satisfies_checks`) and raising if the row does not
        satisfy it. A schema edit that the seeder silently adapted to therefore
        fails at the next seed, which is what "fail loudly" has to mean.
        """
        allowed = self._allowed_values_cached(table, column)
        if column == "episode_id":
            return self.SEED_EPISODE_ID
        if column == "attempt_id":
            return "seed-attempt"
        if column == "policy_version":
            return "seed-policy"
        if column == "callback_key_digest":
            return "seed-digest"
        if allowed:
            # Prefer a value whose type matches the column, so an integer
            # `CHECK (x IN (0,1))` gets `0` and not `'0'`.
            for candidate in allowed:
                if self._looks_like_int(candidate) == (
                    data_type in {"integer", "bigint", "smallint"}
                ):
                    return (
                        int(candidate)
                        if self._looks_like_int(candidate)
                        else candidate
                    )
            return allowed[0]
        if data_type in {"integer", "bigint", "smallint"}:
            return 1
        if data_type in {"double precision", "real", "numeric"}:
            return 1.0
        return f"seed-{table}-{column}"

    def _allowed_values_cached(self, table: str, column: str) -> list[str]:
        """`_allowed_values`, memoised on the instance.

        The cache holds a lookup that **returned nothing** as well as one that
        returned values, which is why `_seen_allowed` is needed: an empty list is
        the legitimate answer for a column with no enumerated `CHECK`, and it must
        not be re-queried on every access nor mistaken for an unseen key.
        """
        key = (table, column)
        if key not in self._seen_allowed:
            self._seen_allowed.add(key)
            self._allowed_cache[key] = self._allowed_values(table, column)
        return self._allowed_cache[key]

    @staticmethod
    def _looks_like_int(value: str) -> bool:
        try:
            int(value)
        except ValueError:
            return False
        return True

    def _allowed_values(self, table: str, column: str) -> list[str]:
        """The values a column's `CHECK ... IN (...)` allows, as strings.

        Parsed from `pg_get_constraintdef` rather than hand-listed, because a
        hand-list is a second copy of the schema and the whole point of this
        stage is that copies of the schema drift. Returns an empty list when the
        column has no simple enumerated constraint, which is the signal to fall
        back to the type.

        A column may carry more than one `CHECK` (the `0/1` flag constraints are
        separate from the enum ones), so the first definition that actually
        enumerates this column wins.

        One awkward case the constraint text alone does not settle: `evidence`
        has `CHECK (level <> 'documented' OR (simulated = 0 AND source_ref IS NOT
        NULL AND trim(source_ref) <> ''))`. Choosing `documented` would force
        `simulated = 0` and a non-empty `source_ref`, and the generator picks
        columns independently, so it cannot satisfy a constraint spanning them.
        `self_reported` is the first allowed value anyway and satisfies the
        disjunction on its own.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT pg_get_constraintdef(c.oid) FROM pg_constraint c "
                "JOIN pg_class r ON r.oid = c.conrelid "
                "WHERE c.contype = 'c' AND r.relname = %s",
                (table,),
            )
            definitions = [row[0] for row in cur.fetchall()]
        needle = f"(({column} = ANY"
        for definition in definitions:
            if needle in definition:
                return re.findall(r"'([^']*)'::text", definition)
        return []

    def refuse_update(self, table: str) -> None:
        """Attempt an UPDATE that genuinely touches every row, and let the trigger
        refuse it.

        `SET` assigns the first column to itself for all rows. `WHERE true` is
        deliberate: the point of the probe is to reach the trigger, and a probe
        that reaches nothing proves nothing. The caller seeds a row first, so
        there is a row for the trigger to fire against.

        The probe runs through the store's own connection rather than a separate
        one. The guarantee lives in the database, so either would prove it, but
        this also proves the store's connection is not in some state that
        bypasses the trigger.
        """
        with self._conn.cursor() as cur:
            column = sql.Identifier(self._first_column(cur, table))
            cur.execute(
                sql.SQL("UPDATE {} SET {} = {} WHERE true").format(
                    sql.Identifier(table), column, column
                )
            )

    def refuse_delete(self, table: str) -> None:
        """Attempt a DELETE that matches every row, so the row-level trigger fires.

        `WHERE true` for the reason given on `refuse_update`.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                sql.SQL("DELETE FROM {} WHERE true").format(sql.Identifier(table))
            )

    @staticmethod
    def _first_column(cur: psycopg.Cursor, table: str) -> str:
        """The name of the table's first column, by ordinal position.

        Read from the catalogue rather than assumed to be `id`. The earlier probe
        hard-coded `id` and `policy_versions` does not have one (its key is
        `version`), so that table raised `UndefinedColumn` instead of a refusal,
        and the test could not have told the difference.
        """
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s "
            "ORDER BY ordinal_position LIMIT 1",
            (table,),
        )
        row = cur.fetchone()
        if row is None:
            raise LookupError(f"{table} has no columns in the public schema")
        return row[0]

    def refuse_truncate(self, table: str) -> None:
        """The statement-level probe, and the reason this engine needed a third
        trigger. A row-level DELETE trigger does not fire for TRUNCATE.

        **Why `CASCADE` and not a bare `TRUNCATE`.** A bare `TRUNCATE` on a table
        some other table references by foreign key is refused by Postgres itself,
        with `FeatureNotSupported: cannot truncate a table referenced in a foreign
        key constraint`, **before** any trigger runs. That refusal is not the
        guarantee: it is a side effect of the foreign keys, and it disappears the
        moment the referencing table is included or the row order changes.
        `TRUNCATE ... CASCADE` is the form that actually reaches the table and
        would erase the record, so it is the form the guard has to be proved
        against. Probing with a bare `TRUNCATE` would have raised a real error for
        the wrong reason and left the trigger untested.

        The `CASCADE` has a second consequence that the control test depends on:
        it also truncates every table that references this one, so each of those
        tables' own `BEFORE TRUNCATE` triggers fires too. A control that drops
        only `episodes_no_truncate` will still meet the trigger on `dispositions`
        and fail for the wrong reason. That is why the control drops every
        truncate trigger, not one.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                sql.SQL("TRUNCATE {} CASCADE").format(sql.Identifier(table))
            )

    # -- callback idempotency ----------------------------------------------

    def record_callback_once(
        self,
        attempt_id: str,
        callback_key: str,
        result: CallbackResult,
        origin: str,
        *,
        now_utc: datetime,
    ) -> ReceiptOutcome:
        """Record one callback receipt, and say what happened to it.

        The lookup-then-insert is serialised by `SELECT ... FOR UPDATE` on the
        attempt row, which stands in for `BEGIN IMMEDIATE`. Two writers on one
        callback key therefore cannot both observe "no such key": the second
        blocks on the attempt row until the first commits, then sees the
        committed receipt and records a duplicate.

        The UNIQUE index on `callback_key` is the backstop for the case where
        there is no attempt row to lock. Its violation is translated to
        `LockContention` rather than leaked, because a caller cannot tell a raw
        `UniqueViolation` apart from any other driver error and would have no way
        to decide whether to retry.

        Stage 1 does not yet re-check consent or append the terminal transition.
        Those belong to the method's full port; what is proven here is the
        transaction and the duplicate resolution, which is the part that depends
        on the engine.
        """
        now_utc = _utc(now_utc)
        try:
            with self._write() as cur:
                attempt = self._lock_or_absent(
                    cur,
                    "SELECT id, episode_id, route_id FROM attempts "
                    "WHERE id = %s FOR UPDATE",
                    (attempt_id,),
                )
                if attempt is None:
                    raise AttemptNotFound(attempt_id)
                # Named columns, not `SELECT *` read positionally. The positional
                # form was correct only while `attempts` was ordered
                # `id, episode_id, route_id, ...`, and a future column inserted
                # before `route_id` would have mis-keyed every receipt rather than
                # failing. `sqlite3.Row` gives the SQLite store named access; this
                # is the Postgres equivalent of that guarantee.
                _attempt_id, episode_id, route_id = attempt

                cur.execute(
                    "SELECT id FROM callbacks WHERE callback_key = %s", (callback_key,)
                )
                existing = cur.fetchone()
                if existing is not None:
                    self._insert_receipt(
                        cur,
                        episode_id=episode_id,
                        route_id=route_id,
                        attempt_id=attempt_id,
                        callback_key=None,
                        digest=_digest(callback_key),
                        duplicate_of=existing[0],
                        accepted=False,
                        rejection_reason="duplicate",
                        origin=origin,
                        result=None,
                        payload=result.payload,
                        now_utc=now_utc,
                    )
                    return ReceiptOutcome(
                        disposition=ReceiptDisposition.DUPLICATE,
                        receipt_id=0,
                        rejection_reason="duplicate",
                    )

                receipt_id = self._insert_receipt(
                    cur,
                    episode_id=episode_id,
                    route_id=route_id,
                    attempt_id=attempt_id,
                    callback_key=callback_key,
                    digest=_digest(callback_key),
                    duplicate_of=None,
                    accepted=True,
                    rejection_reason=None,
                    origin=origin,
                    result=(
                        result.transition.value
                        if result.transition is not None
                        else None
                    ),
                    payload=result.payload,
                    now_utc=now_utc,
                )
                return ReceiptOutcome(
                    disposition=ReceiptDisposition.APPLIED,
                    receipt_id=receipt_id,
                    rejection_reason=None,
                )
        except psycopg.errors.UniqueViolation as exc:
            raise LockContention(
                "a concurrent writer won the callback key, so nothing was "
                f"written by this one: {exc}"
            ) from exc

    @staticmethod
    def _insert_receipt(
        cur: psycopg.Cursor,
        *,
        episode_id: str,
        route_id: str,
        attempt_id: str,
        callback_key: str | None,
        digest: str,
        duplicate_of: int | None,
        accepted: bool,
        rejection_reason: str | None,
        origin: str,
        result: str | None,
        payload: str,
        now_utc: datetime,
    ) -> int:
        cur.execute(
            "INSERT INTO callbacks ("
            "  episode_id, route_id, attempt_id, callback_key, callback_key_digest,"
            "  duplicate_of, accepted, rejection_reason, origin, result, payload,"
            "  received_at"
            ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (
                episode_id,
                route_id,
                attempt_id,
                callback_key,
                digest,
                duplicate_of,
                1 if accepted else 0,
                rejection_reason,
                origin,
                result,
                payload,
                _iso(now_utc),
            ),
        )
        return cur.fetchone()[0]


def open_postgres_store(dsn: str, **kwargs: object) -> PostgresEpisodeStore:
    """The factory, mirroring `state.open_store`."""
    return PostgresEpisodeStore(dsn, **kwargs)  # type: ignore[arg-type]


__all__ = [
    "DEV_DSN",
    "PostgresEpisodeStore",
    "open_postgres_store",
    "probe_dsn",
]
