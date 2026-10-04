"""A Postgres episode store, and the append-only guarantee on a new engine.

Slice 7b. **Stage 1** proved the guarantee survives the move to Postgres: 14
tables, 42 triggers, and no `UPDATE`, `DELETE` or `TRUNCATE` path. **Stage 2 is
the rest of the port**: every method `SqliteEpisodeStore` exposes, so the
service, the MCP tools and the API run on either engine behind one surface.

**The claim stage 2 makes, stated exactly.** `tests/test_postgres_store.py`
runs one scripted episode through both engines and compares the results field by
field, rather than asserting that each store satisfies its own tests. Two stores
that each pass their own suite can still disagree about what the product does.
That comparison is the port's evidence; everything else in this file is
mechanism.

Four things are genuinely different here and none of them is a translation:

1. **`postgres_schema` has no `rowid`, and SQLite's `ORDER BY rowid` is what
   "the latest attempt" means.** Three reads in `load_snapshot` and two in the
   `list_*` methods used `rowid` as insertion order. Postgres has no equivalent
   that survives a `VACUUM` (`ctid` is physical and moves), so the ordering is
   now the recorded timestamp with the primary key as a stated tiebreaker. The
   columns used are `opened_at`, `recorded_at` and `occurred_at`, which are
   ISO-8601 text and sort lexicographically. Where a `UNIQUE` constraint already
   makes the row unique (`expiry_events`), the ordering is irrelevant and is
   kept only for determinism.
2. **`INSERT OR REPLACE` does not exist, and the O1 defence changes path.**
   SQLite's `REPLACE` deletes the conflicting row and `recursive_triggers = ON`
   sends that implicit delete through the `BEFORE DELETE` trigger. Postgres has
   `ON CONFLICT ... DO UPDATE`, which fires the `BEFORE UPDATE` trigger instead.
   Same refusal, different mechanism, re-proved rather than assumed: see
   `TestOnConflictFollowsTheSqliteRule` and the dispositions case the O1 defect
   was actually about.
3. **`json_extract(payload, '$.confirmation_id')` is SQLite syntax.** Postgres
   spells it `payload::jsonb ->> 'confirmation_id'`, and that cast **raises** on
   a payload that is not JSON. Most `events.payload` values are plain text
   (`version=1 source=fixture`), so the cast has to be guarded. It is guarded
   with `CASE WHEN payload IS JSON`, because a `WHERE` clause gives no
   evaluation-order guarantee and an unguarded `AND` is free to try the cast on
   a row of another kind. PostgreSQL 17 supports `IS JSON`.
4. **`lastrowid` does not exist.** Every insert that needs its new key uses
   `RETURNING id`, which is also atomic in a way `lastrowid` is not.

**Why one connection and not a pool (D1, closed at stage 2).** Stage 1 removed
the per-construction DDL. Stage 2 measured the rest of the connect cost: see
`docs/plans/urgent-advice-accessibility/supabase-migration-plan.md` and the D1
entry in `00-status.md`. The connection is held for the process lifetime, which
is the same shape `SqliteEpisodeStore` has and the shape a single-worker
deployment needs. A pool is still not used.

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

import json
import os
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from . import postgres_schema
from .domain import rules
from .domain.models import (
    MAX_REPAIR_ROUNDS,
    TERMINAL_TRANSITIONS,
    AttemptCommand,
    AttemptSnapshot,
    ClosureProjection,
    AttemptTransition,
    CallbackResult,
    Disposition,
    EpisodeSnapshot,
    EvidenceLevel,
    EvidenceRecord,
    ExecutionStatus,
    ExtractedPlan,
    HintEventKind,
    HintLevel,
    InputMode,
    Origin,
    PlanComparison,
    ReceiptDisposition,
    RecallOutcome,
)
from .state import (
    DEFAULT_KEY_NAMESPACE,
    CLINICAL_SCOPE,
    AttemptNotFound,
    CallbackReceipt,
    ConsentNotCurrent,
    DeadlineNotMonotonic,
    DispositionVersionConflict,
    EpisodeNotFound,
    EvidenceProvenanceViolation,
    HintEventRecord,
    IdempotencyKeyCollision,
    LockContention,
    NoDispositionForExpiry,
    PolicyVersionConflict,
    PrematureExpiry,
    ReceiptOutcome,
    RepairRoundOutOfRange,
    RestatementNotFound,
    RestatementRecord,
    StateError,
    UnconfirmedTranscript,
    _disposition_from_row,
    _digest,
    _iso,
    _parse,
    _restatement_from_row,
    _utc,
    transcript_confirmation_id,
)

#: The DSN the tests use, from the environment, with the local container default.
#:
#: **The port is 15432, moved off 55432 on 5 October 2026 because 55432 cannot be
#: bound on Windows.** Hyper-V and WSL reserve ranges inside the dynamic port
#: space and the reservations move between boots; `55387-55486` covered 55432, so
#: `docker run -p 55432:5432` failed with "An attempt was made to access a socket
#: in a way forbidden by its access permissions", which reads like a Docker fault
#: and is not one. Check with
#: `netsh interface ipv4 show excludedportrange protocol=tcp` before debugging the
#: daemon. 15432 sits below the dynamic range, so it is far less likely to be
#: reserved. `tests/test_postgres_store.py` derives the port in its skip reason
#: from this constant rather than repeating it, so the recipe cannot drift from
#: the default.
DEV_DSN = "postgresql://carerelay:carerelay_test@127.0.0.1:15432/carerelay"


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
    """The Postgres store.

    **D1, settled at stage 2 with a measurement: the connection is held, the
    schema DDL runs once per process per DSN, and there is no pool.** `__init__`
    connects and, on the first store for a given DSN in this process, applies
    `SCHEMA_SQL` and `append_only_ddl()`. The second and later stores for the same
    DSN reuse the already-migrated schema and skip the DDL.

    Measured on Supabase, 4 October 2026, one session: connect plus DDL **2.51 s**,
    connect alone **1.54 s**, so the 42-trigger DDL costs about **0.97 s**, and one
    statement on a held connection costs **185 ms**. Those three numbers are the
    whole argument. A pool would save the 1.54 s connect, which a process that
    holds one connection pays **once at startup rather than per request**; it
    cannot save the DDL, which D1 already removes from every construction after
    the first. So a pool buys nothing a single-worker deployment needs, and it
    costs a dependency (`psycopg_pool`, not installed) plus a second failure mode
    (a stale or exhausted pool). Re-running the DDL per construction, the thing
    the pool would not have fixed, is what made this a problem in the first place:
    roughly a second on top of every store construction, including on a request
    path.

    **Rows are read as dictionaries.** `sqlite3.Row` gives the SQLite store named
    access, and `dict_row` is the Postgres equivalent. It is set on the two cursor
    factories this class owns (`_write` and `_read`) rather than on the connection,
    so the seeding and probe machinery below, which reads single columns
    positionally, is untouched.
    """

    def __init__(
        self,
        dsn: str,
        *,
        connect_timeout_s: int = 5,
        lock_timeout_s: float = 5.0,
        key_namespace: str = DEFAULT_KEY_NAMESPACE,
    ) -> None:
        self.dsn = dsn
        self.connect_timeout_s = connect_timeout_s
        #: The per-transaction lock wait, in seconds (D2). A float so a test can
        #: set a sub-second value to reach the `LockNotAvailable` branch.
        self.lock_timeout_s = lock_timeout_s
        self.key_namespace = key_namespace
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

        **D2, tuned at stage 2 against a real contention on the live engine, not
        inherited.** The 5 s came from SQLite's `busy_timeout`, which was chosen
        against a sub-millisecond engine. Measured on Supabase, 4 October 2026: a
        blocked `record_callback_once` raised `LockContention` after **5.99 s**
        with the default and after **1.15 s** with `lock_timeout_s=0.5`. The wait
        therefore tracks the parameter one for one on top of roughly **0.65 s** of
        other work in this path, so **one** statement blocks.

        `lock_timeout` is **per statement, not per transaction**, so the ceiling
        is the number of statements that can block multiplied by this value. That
        count is 1 in this path today; a second blocking statement added here
        would double the ceiling without changing this line, which is the fact a
        future edit needs and the reason it is written down. 5 s is kept: the
        measured ceiling is about a fifth of a 30 s request budget, lowering it
        turns a transient lock into a patient-visible failure, and the
        deployment writes from one worker so a long wait is unlikely.

        The row lock that makes the callback lookup atomic is applied at the call
        site by `_lock_or_absent`, because it is a row lock and the row differs
        per operation. SQLite's equivalent is a database-wide lock taken here.
        """
        cur = self._conn.cursor(row_factory=dict_row)
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

    @contextmanager
    def _read(self) -> Iterator[psycopg.Cursor]:
        """One read, on a cursor that leaves no transaction behind.

        psycopg opens a transaction on the first statement of a connection with
        `autocommit=False`, and a read that is never committed holds that
        transaction open: on a pooled server that is a session pinned for no
        reason, and a `SELECT ... FOR UPDATE` inside one would hold its locks
        until the process ended. A read has nothing to commit, so the cursor is
        closed and the transaction rolled back.

        **This must not be used inside `_write()`.** Every read helper below
        therefore takes the caller's cursor; the public `list_*` methods are the
        only ones that open their own.
        """
        cur = self._conn.cursor(row_factory=dict_row)
        try:
            yield cur
        finally:
            self._conn.rollback()
            cur.close()

    @staticmethod
    def _lock_or_absent(
        cur: psycopg.Cursor, query: str, params: tuple
    ) -> dict[str, Any] | None:
        """`SELECT ... FOR UPDATE`, returning None when there is no row.

        Split out so the locking rule is visible at every call site that depends
        on it rather than implied by the SQL string.
        """
        cur.execute(query, params)
        return cur.fetchone()

    # -- audit -------------------------------------------------------------

    def _append_event(
        self,
        cur: psycopg.Cursor,
        episode_id: str,
        kind: str,
        payload: str,
        now_utc: datetime,
    ) -> None:
        """One row of `events`. Called inside the caller's transaction, so the
        audit row and the fact it describes commit together."""
        cur.execute(
            "INSERT INTO events (episode_id, kind, payload, recorded_at) "
            "VALUES (%s, %s, %s, %s)",
            (episode_id, kind, payload, _iso(now_utc)),
        )

    def list_events(self, episode_id: str) -> tuple[tuple[str, str, datetime], ...]:
        with self._read() as cur:
            cur.execute(
                "SELECT kind, payload, recorded_at FROM events WHERE episode_id = %s "
                "ORDER BY id",
                (episode_id,),
            )
            return tuple(
                (row["kind"], row["payload"], _parse(row["recorded_at"]))
                for row in cur.fetchall()
            )

    # -- episode, policy, disposition --------------------------------------

    def create_episode(self, episode_id: str, persona: str, *, now_utc: datetime) -> None:
        with self._write() as cur:
            cur.execute(
                "INSERT INTO episodes (id, persona, created_at) VALUES (%s, %s, %s)",
                (episode_id, persona, _iso(now_utc)),
            )
            self._append_event(cur, episode_id, "episode_created", persona, now_utc)

    def register_policy_version(
        self,
        version: str,
        *,
        content: str,
        provenance: str,
        approved_by: str | None,
        now_utc: datetime,
    ) -> None:
        """A policy version must be recorded before a disposition may cite it.

        The foreign key is the point: a disposition cannot name a policy version
        the system never recorded, so the fixture's provenance is auditable
        rather than asserted.

        **Idempotent, and deliberately not silent about a conflict.** A repeat of
        the *same* policy is a no-op, which is what a second episode needs. A
        repeat that disagrees on content, provenance or approver raises: two
        different policies claiming one version number is exactly the unauditable
        state the foreign key exists to prevent.

        The SQLite store performs this read-then-insert outside an explicit
        transaction; here it is inside one, because Postgres has no autocommit
        mode switched on and a bare `SELECT` would otherwise leave the
        transaction open across the caller's next statement.
        """
        with self._write() as cur:
            cur.execute(
                "SELECT content, provenance, approved_by FROM policy_versions "
                "WHERE version = %s",
                (version,),
            )
            existing = cur.fetchone()
            if existing is not None:
                if (
                    existing["content"] != content
                    or existing["provenance"] != provenance
                    or existing["approved_by"] != approved_by
                ):
                    raise PolicyVersionConflict(
                        f"policy version {version!r} is already recorded with "
                        "different content, provenance or approver; a version "
                        "number may not be reused for a different policy"
                    )
                return
            cur.execute(
                "INSERT INTO policy_versions "
                "(version, content, provenance, approved_by, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (version, content, provenance, approved_by, _iso(now_utc)),
            )

    def insert_disposition(self, disposition: Disposition, *, now_utc: datetime) -> None:
        """Append one disposition version. There is no update path (D3, I1).

        Versions must be contiguous from 1 and a reassessment may move the
        deadline forward only (O7, I2). Both rules are re-implemented here rather
        than inherited, because the record has to refuse to hold their violation
        and the SQLite triggers cannot do that for a different engine.
        """
        with self._write() as cur:
            cur.execute(
                "SELECT MAX(version_no) AS top FROM dispositions WHERE episode_id = %s",
                (disposition.episode_id,),
            )
            top = cur.fetchone()["top"] or 0
            if disposition.version != top + 1:
                raise DispositionVersionConflict(
                    f"disposition version {disposition.version} does not follow "
                    f"version {top} for episode {disposition.episode_id!r}"
                )
            if top > 0:
                cur.execute(
                    "SELECT clinical_deadline_utc AS deadline FROM dispositions "
                    "WHERE episode_id = %s AND version_no = %s",
                    (disposition.episode_id, top),
                )
                previous_deadline = _parse(cur.fetchone()["deadline"])
                if disposition.clinical_deadline_utc <= previous_deadline:
                    raise DeadlineNotMonotonic(
                        f"disposition version {disposition.version} deadline "
                        f"{_iso(disposition.clinical_deadline_utc)} is not later "
                        f"than version {top} deadline {_iso(previous_deadline)}: "
                        "a reassessment may move a deadline forward only (O7, I2)"
                    )
            cur.execute(
                "INSERT INTO dispositions "
                "(episode_id, version_no, policy_version, action_id, "
                " clinical_deadline_utc, next_owner_id, fallback_route_id, source, "
                " created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    disposition.episode_id,
                    disposition.version,
                    disposition.policy_version,
                    disposition.action_id,
                    _iso(disposition.clinical_deadline_utc),
                    disposition.next_owner_id,
                    disposition.fallback_route_id,
                    disposition.source.value,
                    _iso(now_utc),
                ),
            )
            self._append_event(
                cur,
                disposition.episode_id,
                "disposition_recorded",
                f"version={disposition.version} source={disposition.source.value}",
                now_utc,
            )

    def list_dispositions(self, episode_id: str) -> tuple[Disposition, ...]:
        with self._read() as cur:
            cur.execute(
                "SELECT * FROM dispositions WHERE episode_id = %s ORDER BY version_no",
                (episode_id,),
            )
            return tuple(_disposition_from_row(row) for row in cur.fetchall())

    # -- consent -----------------------------------------------------------

    def change_consent(
        self,
        episode_id: str,
        scope: str,
        *,
        granted: bool,
        now_utc: datetime,
    ) -> int:
        """Append a consent version and return its number.

        Revocation is a new row with a new version, never an edit. An attempt
        opened under version 1 therefore stays stamped 1 forever, and the
        mismatch against version 2 is what refuses its in-flight callback.
        """
        with self._write() as cur:
            cur.execute(
                "SELECT MAX(version) AS top FROM consents "
                "WHERE episode_id = %s AND scope = %s",
                (episode_id, scope),
            )
            version = (cur.fetchone()["top"] or 0) + 1
            state = "granted" if granted else "revoked"
            cur.execute(
                "INSERT INTO consents (episode_id, scope, state, version, recorded_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (episode_id, scope, state, version, _iso(now_utc)),
            )
            self._append_event(
                cur,
                episode_id,
                "consent_changed",
                f"scope={scope} {state} v{version}",
                now_utc,
            )
        return version

    @staticmethod
    def _fetch_consent(
        cur: psycopg.Cursor, episode_id: str, scope: str
    ) -> tuple[int, str] | None:
        cur.execute(
            "SELECT version, state FROM consents WHERE episode_id = %s AND scope = %s "
            "ORDER BY version DESC LIMIT 1",
            (episode_id, scope),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return int(row["version"]), str(row["state"])

    @staticmethod
    def _require_current_consent(
        cur: psycopg.Cursor, episode_id: str, stamped_version: int
    ) -> None:
        current = PostgresEpisodeStore._fetch_consent(cur, episode_id, CLINICAL_SCOPE)
        if current is None:
            raise ConsentNotCurrent(
                f"episode {episode_id!r} has no recorded {CLINICAL_SCOPE} consent"
            )
        version, state = current
        if state != "granted":
            raise ConsentNotCurrent(
                f"{CLINICAL_SCOPE} consent is {state} at version {version}"
            )
        if version != stamped_version:
            raise ConsentNotCurrent(
                f"consent version changed from {stamped_version} to {version} "
                "while the attempt was in flight"
            )

    @staticmethod
    def _require_granted_consent(cur: psycopg.Cursor, episode_id: str) -> None:
        """The rule for a path with no attempt to compare against: revocation
        stops recording. Same rule as an in-flight check, no version to match."""
        current = PostgresEpisodeStore._fetch_consent(cur, episode_id, CLINICAL_SCOPE)
        if current is None:
            raise ConsentNotCurrent(
                f"episode {episode_id!r} has no recorded {CLINICAL_SCOPE} consent"
            )
        version, state = current
        if state != "granted":
            raise ConsentNotCurrent(
                f"{CLINICAL_SCOPE} consent is {state} at version {version}"
            )

    def require_granted_consent(self, episode_id: str) -> None:
        """Public since Slice 6, because the MCP `record_evidence` tool lives in
        another module and has to apply this rule rather than a copy of it."""
        with self._read() as cur:
            self._require_granted_consent(cur, episode_id)

    @staticmethod
    def _consent_rejection_reason(
        cur: psycopg.Cursor, episode_id: str, stamped_version: int
    ) -> str | None:
        """The reason a receipt is refused, or `None` when it is accepted.

        Deliberately returns a reason rather than raising: a callback is recorded
        either way, and "we received it and refused it" must be readable in the
        ledger.
        """
        current = PostgresEpisodeStore._fetch_consent(cur, episode_id, CLINICAL_SCOPE)
        if current is None:
            return f"no recorded {CLINICAL_SCOPE} consent"
        version, state = current
        if state != "granted":
            return f"{CLINICAL_SCOPE} consent is {state} at version {version}"
        if version != stamped_version:
            return (
                f"consent version changed from {stamped_version} to {version} "
                "while the attempt was in flight"
            )
        return None

    def record_refusal(
        self, episode_id: str, surface: str, reason: str, *, now_utc: datetime
    ) -> None:
        """Record that a surface refused something, and let the caller then raise.

        A refusal that is only raised leaves the ledger unable to say the episode
        stopped. Writing first and raising second keeps both facts.
        """
        with self._write() as cur:
            self._append_event(
                cur, episode_id, "refused", f"surface={surface} {reason}", now_utc
            )

    # -- attempts ----------------------------------------------------------

    def open_attempt_once(
        self,
        command: AttemptCommand,
        key: str,
        *,
        now_utc: datetime,
    ) -> AttemptSnapshot:
        """Open one attempt, or return the one the same key already opened.

        **The one place the port could not reuse SQLite's shape.** SQLite relies
        on `BEGIN IMMEDIATE` to stop two writers both reading "no such key" for
        the same idempotency key. Postgres has no database-wide write lock, so
        the insert is `ON CONFLICT (idempotency_key) DO NOTHING`: a concurrent
        writer that commits first simply wins, and this writer then reads the
        winner's row and returns it as a suppressed duplicate, which is the
        documented behaviour for a double tap. `DO NOTHING` and not `DO UPDATE`
        because `DO UPDATE` is refused by the append-only trigger, and because
        there is nothing to update.
        """
        with self._write() as cur:
            cur.execute(
                "SELECT id, episode_id, route_id, purpose_id, idempotency_key, "
                "consent_version FROM attempts WHERE idempotency_key = %s FOR UPDATE",
                (key,),
            )
            existing = cur.fetchone()
            if existing is not None:
                self._return_existing_attempt(cur, existing, command, key, now_utc)
                return self._attempt_snapshot(cur, existing)

            self._require_current_consent(cur, command.episode_id, command.consent_version)
            attempt_id = uuid.uuid4().hex
            cur.execute(
                "INSERT INTO attempts "
                "(id, episode_id, route_id, purpose_id, idempotency_key, "
                " consent_version, opened_at) VALUES (%s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (idempotency_key) DO NOTHING",
                (
                    attempt_id,
                    command.episode_id,
                    command.route_id,
                    command.purpose_id,
                    key,
                    command.consent_version,
                    _iso(now_utc),
                ),
            )
            cur.execute(
                "SELECT id, episode_id, route_id, purpose_id, idempotency_key, "
                "consent_version FROM attempts WHERE idempotency_key = %s",
                (key,),
            )
            row = cur.fetchone()
            assert row is not None, "the attempt row vanished between insert and select"
            if row["id"] == attempt_id:
                self._append_event(
                    cur,
                    command.episode_id,
                    "attempt_opened",
                    f"attempt={attempt_id} route={command.route_id} key={key}",
                    now_utc,
                )
            else:
                self._return_existing_attempt(cur, row, command, key, now_utc)
            return self._attempt_snapshot(cur, row)

    def _return_existing_attempt(
        self,
        cur: psycopg.Cursor,
        existing: Mapping[str, Any],
        command: AttemptCommand,
        key: str,
        now_utc: datetime,
    ) -> None:
        """Record a suppressed duplicate and return, raising on a key collision.

        Shared by the two paths in `open_attempt_once`: the key was already there
        before the insert, or a concurrent writer won it during the insert. Both
        are the same fact from the caller's point of view.
        """
        triple = (existing["episode_id"], existing["route_id"], existing["purpose_id"])
        if triple != (command.episode_id, command.route_id, command.purpose_id):
            raise IdempotencyKeyCollision(
                f"key {key!r} already opened attempt {existing['id']!r} for "
                f"{triple!r}, not for "
                f"{(command.episode_id, command.route_id, command.purpose_id)!r}"
            )
        self._append_event(
            cur,
            command.episode_id,
            "attempt_duplicate_suppressed",
            f"key={key} attempt={existing['id']}",
            now_utc,
        )

    def list_attempts(self, episode_id: str) -> tuple[AttemptSnapshot, ...]:
        """Oldest first, matching the SQLite store.

        SQLite ordered by `rowid`, which is insertion order. Postgres has no
        `rowid`, so the order is `opened_at` with the primary key as a stated
        tiebreaker; see the module docstring.
        """
        with self._read() as cur:
            cur.execute(
                "SELECT id, episode_id, route_id, purpose_id, idempotency_key, "
                "consent_version FROM attempts WHERE episode_id = %s "
                "ORDER BY opened_at, id",
                (episode_id,),
            )
            return tuple(self._attempt_snapshot(cur, row) for row in cur.fetchall())

    def get_attempt_by_key(self, key: str) -> AttemptSnapshot | None:
        """The attempt one idempotency key opened, or `None`. Slice 6.

        The MCP tool surface rechecks the attempt key server-side, against the
        store rather than against a value the caller also supplied.
        """
        with self._read() as cur:
            cur.execute(
                "SELECT id, episode_id, route_id, purpose_id, idempotency_key, "
                "consent_version FROM attempts WHERE idempotency_key = %s",
                (key,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return self._attempt_snapshot(cur, row)

    def list_transitions(self, attempt_id: str) -> tuple[AttemptTransition, ...]:
        with self._read() as cur:
            return self._list_transitions(cur, attempt_id)

    @staticmethod
    def _list_transitions(
        cur: psycopg.Cursor, attempt_id: str
    ) -> tuple[AttemptTransition, ...]:
        cur.execute(
            "SELECT seq, transition, origin, payload, recorded_at "
            "FROM attempt_transitions WHERE attempt_id = %s ORDER BY seq",
            (attempt_id,),
        )
        return tuple(
            AttemptTransition(
                seq=int(row["seq"]),
                kind=ExecutionStatus(row["transition"]),
                origin=Origin(row["origin"]),
                recorded_at=_parse(row["recorded_at"]),
                payload=row["payload"],
            )
            for row in cur.fetchall()
        )

    def _attempt_snapshot(
        self, cur: psycopg.Cursor, row: Mapping[str, Any]
    ) -> AttemptSnapshot:
        """Built from the caller's cursor, never from a new one.

        `_attempt_snapshot` is called inside `open_attempt_once`'s transaction,
        and a read that opened its own cursor there would roll back the write it
        is describing.
        """
        transitions = self._list_transitions(cur, row["id"])
        return AttemptSnapshot(
            attempt_id=row["id"],
            idempotency_key=row["idempotency_key"],
            route_id=row["route_id"],
            consent_version=int(row["consent_version"]),
            execution=rules.project_attempt(transitions),
        )

    # -- callbacks ---------------------------------------------------------

    def record_callback_once(
        self,
        attempt_id: str,
        callback_key: str,
        result: CallbackResult,
        origin: Origin,
        *,
        now_utc: datetime,
    ) -> ReceiptOutcome:
        """Record one callback receipt, and say what happened to it.

        **Slice 3 wrote this as a bool; Slice 6 turned it into `ReceiptOutcome`;
        stage 2 of Slice 7b makes the Postgres path do everything the SQLite one
        does.** Stage 1's version proved the transaction and the duplicate
        resolution but skipped the consent re-check and the transition append,
        because those depend on the rest of the store that did not exist yet.
        They are here now, so the two engines agree on what a refused receipt is.

        Order of operations, all inside one transaction:

        1. lock the attempt row with `SELECT ... FOR UPDATE`, which is the
           Postgres counterpart of `BEGIN IMMEDIATE`;
        2. an existing key means duplicate: write the duplicate row, append a
           `callback_duplicate` event, return `DUPLICATE`;
        3. otherwise decide whether the receipt may be applied, by re-checking the
           current consent against the version stamped on the attempt. A refusal
           still writes the row, with `accepted = 0` and a reason, and returns
           `REFUSED`;
        4. when applied, append the terminal transition and any evidence the
           callback carries, append a `callback_applied` event and return
           `APPLIED`.

        `origin` is accepted as an `Origin` or as its string value, and is
        validated: the SQLite store refuses an origin it does not recognise, and
        a store that silently accepted one would record an unauditable receipt.
        """
        now_utc = _utc(now_utc)
        origin_value = self._origin_value(origin)
        if result.transition is not None and result.transition not in TERMINAL_TRANSITIONS:
            raise rules.UnpermittedTransition(
                result.transition,
                sorted(member.value for member in TERMINAL_TRANSITIONS),
            )
        try:
            with self._write() as cur:
                attempt = self._lock_or_absent(
                    cur,
                    "SELECT id, episode_id, route_id, consent_version FROM attempts "
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
                episode_id = attempt["episode_id"]
                route_id = attempt["route_id"]

                cur.execute(
                    "SELECT id FROM callbacks WHERE callback_key = %s", (callback_key,)
                )
                existing = cur.fetchone()
                if existing is not None:
                    receipt_id = self._insert_receipt(
                        cur,
                        episode_id=episode_id,
                        route_id=route_id,
                        attempt_id=attempt_id,
                        callback_key=None,
                        digest=_digest(callback_key),
                        duplicate_of=existing["id"],
                        accepted=False,
                        rejection_reason="duplicate",
                        origin_value=origin_value,
                        result=None,
                        payload=result.payload,
                        now_utc=now_utc,
                    )
                    self._append_event(
                        cur,
                        episode_id,
                        "callback_duplicate",
                        f"route={route_id} first_receipt={existing['id']}",
                        now_utc,
                    )
                    return ReceiptOutcome(
                        disposition=ReceiptDisposition.DUPLICATE,
                        receipt_id=receipt_id,
                        rejection_reason="duplicate",
                    )

                reason = self._consent_rejection_reason(
                    cur, episode_id, int(attempt["consent_version"])
                )
                receipt_id = self._insert_receipt(
                    cur,
                    episode_id=episode_id,
                    route_id=route_id,
                    attempt_id=attempt_id,
                    callback_key=callback_key,
                    digest=_digest(callback_key),
                    duplicate_of=None,
                    accepted=reason is None,
                    rejection_reason=reason,
                    origin_value=origin_value,
                    result=result.transition,
                    payload=result.payload,
                    now_utc=now_utc,
                )
                if reason is not None:
                    self._append_event(
                        cur,
                        episode_id,
                        "callback_rejected",
                        f"route={route_id} reason={reason}",
                        now_utc,
                    )
                    return ReceiptOutcome(
                        disposition=ReceiptDisposition.REFUSED,
                        receipt_id=receipt_id,
                        rejection_reason=reason,
                    )

                if result.transition is not None:
                    self._append_transition(
                        cur, attempt_id, result.transition, origin_value, result.payload, now_utc
                    )
                if result.evidence is not None:
                    self._insert_evidence(
                        cur, episode_id, result.evidence, now_utc=now_utc
                    )
                self._append_event(
                    cur,
                    episode_id,
                    "callback_applied",
                    f"route={route_id} result="
                    f"{result.transition.value if result.transition else 'evidence-only'}",
                    now_utc,
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
    def _origin_value(origin: Origin) -> str:
        """The stored origin, validated.

        `Origin` is a caller-facing enum and the column is text. The enum is
        **required at runtime, not merely annotated**: the SQLite store reads
        `origin.value` directly, so a bare string is refused there, and a
        Postgres path that quietly accepted one would be exactly the
        permissiveness `EpisodeStore` exists to prevent. The previous
        `isinstance` fallback did not do what its docstring claimed either: a
        bare `"local-sim"` matched the allowed values and was written, so the
        fallback widened the engine rather than guarding it. A refusal is
        `StateError` rather than the `AttributeError` SQLite happens to raise,
        because both refuse and only one of them says why. The validation is
        the SQLite store's: an origin outside the two the schema permits is
        refused rather than written, because the whole point of the column is
        that a reader can tell a platform receipt from a simulated one.
        """
        if not isinstance(origin, Origin):
            raise StateError(
                "a callback origin must be an Origin, not "
                f"{type(origin).__name__}: the SQLite store refuses a bare "
                "string and the two engines may not differ in what they accept"
            )
        candidate = origin.value
        if candidate not in (Origin.PLATFORM.value, Origin.LOCAL_SIM.value):
            raise StateError(f"unknown callback origin {origin!r}")
        return candidate

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
        origin_value: str,
        result: ExecutionStatus | None,
        payload: str,
        now_utc: datetime,
    ) -> int:
        """Returns the new row's id, so the caller can say which receipt it wrote.

        `origin_value` is the already-validated string `_origin_value` returned
        at the public boundary, not the enum: validating once, where the caller's
        value arrives, is what keeps the refusal and the write in agreement.

        `RETURNING id`, not a follow-up `SELECT`: SQLite's `lastrowid` has no
        Postgres equivalent, and `RETURNING` is the same fact read back inside
        the same statement instead of after it.
        """
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
                origin_value,
                result.value if result is not None else None,
                payload,
                _iso(now_utc),
            ),
        )
        return int(cur.fetchone()["id"])

    def list_callbacks(self, episode_id: str) -> tuple[CallbackReceipt, ...]:
        """Every receipt, in arrival order. This is the ledger's dedupe surface."""
        with self._read() as cur:
            cur.execute(
                "SELECT id, route_id, attempt_id, callback_key, callback_key_digest, "
                "duplicate_of, accepted, rejection_reason, origin, result, payload, "
                "received_at FROM callbacks WHERE episode_id = %s ORDER BY id",
                (episode_id,),
            )
            return tuple(
                CallbackReceipt(
                    receipt_id=int(row["id"]),
                    route_id=row["route_id"],
                    attempt_id=row["attempt_id"],
                    callback_key=row["callback_key"],
                    callback_key_digest=row["callback_key_digest"],
                    duplicate_of=row["duplicate_of"],
                    accepted=bool(row["accepted"]),
                    rejection_reason=row["rejection_reason"],
                    origin=Origin(row["origin"]),
                    result=(
                        ExecutionStatus(row["result"])
                        if row["result"] is not None
                        else None
                    ),
                    payload=row["payload"],
                    received_at=_parse(row["received_at"]),
                )
                for row in cur.fetchall()
            )

    @staticmethod
    def _append_transition(
        cur: psycopg.Cursor,
        attempt_id: str,
        transition: ExecutionStatus,
        origin_value: str,
        payload: str,
        now_utc: datetime,
    ) -> None:
        """Append one transition with the next `seq`.

        `seq` is assigned here, monotonically, and never reused. A late
        acknowledgement therefore gets a *higher* `seq` than the failure that
        preceded it and is non-winning under first-terminal-in-order. The
        `UNIQUE (attempt_id, seq)` constraint is what makes two concurrent
        appends a translated `LockContention` rather than a duplicated sequence
        number.
        """
        cur.execute(
            "SELECT MAX(seq) AS top FROM attempt_transitions WHERE attempt_id = %s",
            (attempt_id,),
        )
        seq = (cur.fetchone()["top"] or 0) + 1
        cur.execute(
            "INSERT INTO attempt_transitions "
            "(attempt_id, seq, transition, origin, payload, recorded_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (attempt_id, seq, transition.value, origin_value, payload, _iso(now_utc)),
        )

    # -- evidence ----------------------------------------------------------

    def record_evidence(
        self, episode_id: str, record: EvidenceRecord, *, now_utc: datetime
    ) -> None:
        """Append one evidence row, with D11 enforced twice.

        Once here, and once by the `CHECK` constraint in the schema. The two are
        independent on purpose: a test that proves the constraint issues raw SQL,
        so removing this guard cannot make the constraint test pass.
        """
        with self._write() as cur:
            self._require_granted_consent(cur, episode_id)
            self._insert_evidence(cur, episode_id, record, now_utc=now_utc)
            self._append_event(
                cur,
                episode_id,
                "evidence_recorded",
                f"level={record.level.value} simulated={record.simulated}",
                now_utc,
            )

    @staticmethod
    def _insert_evidence(
        cur: psycopg.Cursor,
        episode_id: str,
        record: EvidenceRecord,
        *,
        now_utc: datetime,
    ) -> None:
        if record.level is EvidenceLevel.DOCUMENTED and (
            record.simulated
            or record.source_ref is None
            or not record.source_ref.strip()
        ):
            raise EvidenceProvenanceViolation(
                "level='documented' requires a non-simulated row with a source_ref "
                f"(simulated={record.simulated}, source_ref={record.source_ref!r})"
            )
        cur.execute(
            "INSERT INTO evidence "
            "(episode_id, level, simulated, provenance, source_ref, recorded_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                episode_id,
                record.level.value,
                int(record.simulated),
                record.provenance,
                record.source_ref,
                _iso(now_utc),
            ),
        )

    def list_evidence(self, episode_id: str) -> tuple[EvidenceRecord, ...]:
        with self._read() as cur:
            return self._list_evidence(cur, episode_id)

    @staticmethod
    def _list_evidence(
        cur: psycopg.Cursor, episode_id: str
    ) -> tuple[EvidenceRecord, ...]:
        cur.execute(
            "SELECT level, simulated, provenance, source_ref FROM evidence "
            "WHERE episode_id = %s ORDER BY id",
            (episode_id,),
        )
        return tuple(
            EvidenceRecord(
                level=EvidenceLevel(row["level"]),
                simulated=bool(row["simulated"]),
                provenance=row["provenance"],
                source_ref=row["source_ref"],
            )
            for row in cur.fetchall()
        )

    # -- acceptance, barriers, escalation ----------------------------------

    def record_human_acceptance(
        self,
        episode_id: str,
        *,
        accepted_by: str,
        scope: str,
        now_utc: datetime,
    ) -> str:
        """Append a named human acceptance. A D4 closure input, not evidence.

        The acceptance is never written to `evidence`, so it cannot make
        `care_evidenced` true.
        """
        acceptance_id = uuid.uuid4().hex
        with self._write() as cur:
            cur.execute(
                "INSERT INTO human_acceptances "
                "(id, episode_id, accepted_by, scope, recorded_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (acceptance_id, episode_id, accepted_by, scope, _iso(now_utc)),
            )
            self._append_event(
                cur,
                episode_id,
                "human_acceptance_recorded",
                f"accepted_by={accepted_by} scope={scope}",
                now_utc,
            )
        return acceptance_id

    def record_barrier(
        self,
        episode_id: str,
        *,
        disposition_version: int,
        barrier_text: str,
        proposed_route_id: str | None,
        permitted_route_id: str | None,
        stopped_at_human_path: bool,
        now_utc: datetime,
    ) -> str:
        """Record a practical barrier, and the route decision it produced.

        Both the proposal and the permitted result are stored, so the ledger can
        show *why* an episode stopped.
        """
        barrier_id = uuid.uuid4().hex
        with self._write() as cur:
            cur.execute(
                "INSERT INTO barriers "
                "(id, episode_id, disposition_version, barrier_text, "
                " proposed_route_id, permitted_route_id, stopped_at_human_path, "
                " recorded_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    barrier_id,
                    episode_id,
                    disposition_version,
                    barrier_text,
                    proposed_route_id,
                    permitted_route_id,
                    1 if stopped_at_human_path else 0,
                    _iso(now_utc),
                ),
            )
            self._append_event(
                cur,
                episode_id,
                "barrier_recorded",
                f"version={disposition_version} "
                f"permitted_route={permitted_route_id or 'none'} "
                f"stopped_at_human_path={int(stopped_at_human_path)}",
                now_utc,
            )
        return barrier_id

    def list_barriers(self, episode_id: str) -> tuple[Mapping[str, Any], ...]:
        """Every barrier recorded for an episode, oldest first.

        The rows are returned as mappings rather than as `sqlite3.Row`, which is
        what the SQLite store returns. Both support `row["name"]`, so every
        caller and every existing assertion reads the same way; the annotation
        says "mapping" because that is the surface the two engines actually
        share.
        """
        with self._read() as cur:
            cur.execute(
                "SELECT * FROM barriers WHERE episode_id = %s ORDER BY recorded_at, id",
                (episode_id,),
            )
            return tuple(cur.fetchall())

    def record_escalation(
        self,
        episode_id: str,
        *,
        human_path: str,
        outcome: str,
        now_utc: datetime,
    ) -> str:
        escalation_id = uuid.uuid4().hex
        with self._write() as cur:
            cur.execute(
                "INSERT INTO escalations "
                "(id, episode_id, human_path, outcome, recorded_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (escalation_id, episode_id, human_path, outcome, _iso(now_utc)),
            )
            self._append_event(
                cur,
                episode_id,
                "escalation_recorded",
                f"human_path={human_path} outcome={outcome}",
                now_utc,
            )
        return escalation_id

    # -- expiry ------------------------------------------------------------

    def record_expiry_once(
        self,
        episode_id: str,
        disposition_version: int,
        now_utc: datetime,
    ) -> bool:
        """Record "the deadline passed unresolved", once. Returns True if written.

        Three refusals, in this order, and the order matters:

        1. an existing event for this version returns `False` **before** the
           overdue check. That is what makes D12 stickiness survive a backwards
           clock.
        2. no such disposition version: there is no deadline for anything to have
           passed.
        3. the deadline has not passed: refuse.

        The `UNIQUE (episode_id, disposition_version)` constraint is the second
        line of defence behind check 1, and a violation is returned as `False`
        rather than raised: a concurrent writer recorded the same fact, and
        "already recorded" is the answer either way.
        """
        now_utc = _utc(now_utc)
        try:
            with self._write() as cur:
                cur.execute(
                    "SELECT id FROM expiry_events WHERE episode_id = %s "
                    "AND disposition_version = %s",
                    (episode_id, disposition_version),
                )
                if cur.fetchone() is not None:
                    return False

                cur.execute(
                    "SELECT clinical_deadline_utc FROM dispositions "
                    "WHERE episode_id = %s AND version_no = %s",
                    (episode_id, disposition_version),
                )
                row = cur.fetchone()
                if row is None:
                    raise NoDispositionForExpiry(
                        f"episode {episode_id!r} has no disposition version "
                        f"{disposition_version}"
                    )
                deadline = _parse(row["clinical_deadline_utc"])
                if now_utc < deadline:
                    raise PrematureExpiry(
                        f"the deadline for version {disposition_version} is "
                        f"{deadline.isoformat()}, which has not passed at "
                        f"{now_utc.isoformat()}"
                    )

                event_id = uuid.uuid4().hex
                cur.execute(
                    "INSERT INTO expiry_events "
                    "(id, episode_id, disposition_version, occurred_at) "
                    "VALUES (%s, %s, %s, %s)",
                    (event_id, episode_id, disposition_version, _iso(now_utc)),
                )
                self._append_event(
                    cur, episode_id, "expiry_recorded", f"version={disposition_version}", now_utc
                )
                return True
        except psycopg.errors.UniqueViolation:
            return False

    def list_expiry_events(
        self, episode_id: str
    ) -> tuple[tuple[int, datetime], ...]:
        with self._read() as cur:
            cur.execute(
                "SELECT disposition_version, occurred_at FROM expiry_events "
                "WHERE episode_id = %s ORDER BY occurred_at, id",
                (episode_id,),
            )
            return tuple(
                (int(row["disposition_version"]), _parse(row["occurred_at"]))
                for row in cur.fetchall()
            )

    # -- restatements ------------------------------------------------------

    def record_restatement(
        self,
        episode_id: str,
        *,
        disposition_version: int,
        hint_level: HintLevel,
        input_mode: InputMode,
        transcript_confirmed: bool,
        extracted: ExtractedPlan,
        comparison: PlanComparison,
        repair_round: int,
        outcome: RecallOutcome,
        dwell_seconds: float | None,
        now_utc: datetime,
    ) -> str:
        """Append one scored restatement. Returns the new row's id.

        Three refusals, each the record-level half of a rule `domain` already
        owns, enforced here as well because D11 sets the precedent that an
        invariant is not real until the record refuses to hold its violation:
        an unconfirmed voice transcript cannot be scored; the repair cap is two;
        the comparison must name a disposition that exists.
        """
        now_utc = _utc(now_utc)
        if input_mode is InputMode.VOICE and not transcript_confirmed:
            raise UnconfirmedTranscript(
                "a voice restatement may not be scored before its transcript "
                "is confirmed (Gate 1 ordering rule)"
            )
        if not 0 <= repair_round <= MAX_REPAIR_ROUNDS:
            raise RepairRoundOutOfRange(
                f"repair_round {repair_round} is outside 0..{MAX_REPAIR_ROUNDS} "
                "(two repairs maximum, a third is never offered: C6)"
            )

        with self._write() as cur:
            cur.execute("SELECT id FROM episodes WHERE id = %s", (episode_id,))
            if cur.fetchone() is None:
                raise EpisodeNotFound(episode_id)
            cur.execute(
                "SELECT version_no FROM dispositions WHERE episode_id = %s "
                "AND version_no = %s",
                (episode_id, disposition_version),
            )
            if cur.fetchone() is None:
                raise NoDispositionForExpiry(
                    f"episode {episode_id!r} has no disposition version "
                    f"{disposition_version} to compare against"
                )

            restatement_id = uuid.uuid4().hex
            cur.execute(
                "INSERT INTO restatements "
                "(id, episode_id, disposition_version, hint_level, input_mode, "
                " transcript_confirmed, extracted_json, mismatches, repair_round, "
                " outcome, dwell_seconds, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    restatement_id,
                    episode_id,
                    disposition_version,
                    hint_level.value,
                    input_mode.value,
                    1 if transcript_confirmed else 0,
                    json.dumps(
                        {
                            "action_span": extracted.action_span,
                            "deadline_span": extracted.deadline_span,
                            "next_owner_span": extracted.next_owner_span,
                            "uncertain_fields": sorted(extracted.uncertain_fields),
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "matched": sorted(comparison.matched),
                            "mismatched": sorted(comparison.mismatched),
                            "uncertain": sorted(comparison.uncertain),
                        },
                        ensure_ascii=False,
                    ),
                    repair_round,
                    outcome.value,
                    dwell_seconds,
                    _iso(now_utc),
                ),
            )
            self._append_event(
                cur,
                episode_id,
                "restatement_recorded",
                f"hint={hint_level.value} round={repair_round} "
                f"outcome={outcome.value}",
                now_utc,
            )
            return restatement_id

    def list_restatements(
        self, episode_id: str
    ) -> tuple[RestatementRecord, ...]:
        with self._read() as cur:
            cur.execute(
                "SELECT * FROM restatements WHERE episode_id = %s "
                "ORDER BY created_at, id",
                (episode_id,),
            )
            return tuple(_restatement_from_row(row) for row in cur.fetchall())

    def get_restatement(self, restatement_id: str) -> RestatementRecord:
        with self._read() as cur:
            cur.execute(
                "SELECT * FROM restatements WHERE id = %s", (restatement_id,)
            )
            row = cur.fetchone()
            if row is None:
                raise RestatementNotFound(restatement_id)
            return _restatement_from_row(row)

    def record_hint_event(
        self,
        episode_id: str,
        *,
        hint_level: HintLevel,
        kind: HintEventKind,
        dwell_seconds: float | None,
        now_utc: datetime,
    ) -> None:
        """Append one hint event to the audit log.

        There is no hint-events table; `events` is the table the judge ledger
        already reads. `dwell_seconds` travels here and nowhere else in the
        patient direction (`PLAN.md` 5.2.1, C8).
        """
        now_utc = _utc(now_utc)
        with self._write() as cur:
            self._append_event(
                cur,
                episode_id,
                "hint_event",
                json.dumps(
                    {
                        "hint_level": hint_level.value,
                        "kind": kind.value,
                        "dwell_seconds": dwell_seconds,
                    }
                ),
                now_utc,
            )

    def list_hint_events(self, episode_id: str) -> tuple[HintEventRecord, ...]:
        with self._read() as cur:
            cur.execute(
                "SELECT payload, recorded_at FROM events WHERE episode_id = %s "
                "AND kind = 'hint_event' ORDER BY id",
                (episode_id,),
            )
            rows = cur.fetchall()
        records: list[HintEventRecord] = []
        for row in rows:
            payload = json.loads(row["payload"])
            records.append(
                HintEventRecord(
                    level=HintLevel(payload["hint_level"]),
                    kind=HintEventKind(payload["kind"]),
                    dwell_seconds=payload["dwell_seconds"],
                    recorded_at=_parse(row["recorded_at"]),
                )
            )
        return tuple(records)

    def record_transcript_confirmation(
        self, episode_id: str, *, text: str, now_utc: datetime
    ) -> str:
        """Record that the patient confirmed or corrected this transcript.

        Returns the confirmation id, which is a digest of the text itself, so the
        id binds to the string rather than to a row number the caller cannot be
        made to respect.
        """
        now_utc = _utc(now_utc)
        confirmation_id = transcript_confirmation_id(text)
        with self._write() as cur:
            self._append_event(
                cur,
                episode_id,
                "transcript_confirmed",
                json.dumps(
                    {
                        "confirmation_id": confirmation_id,
                        "text": text,
                    },
                    ensure_ascii=False,
                ),
                now_utc,
            )
            return confirmation_id

    def has_transcript_confirmation(
        self, episode_id: str, confirmation_id: str
    ) -> bool:
        """Whether this confirmation was recorded for this episode.

        **The one read that needed a real translation, not a substitution.**
        SQLite spells this `json_extract(payload, '$.confirmation_id')`. Postgres
        spells it `payload::jsonb ->> 'confirmation_id'`, and that cast raises on
        a payload that is not JSON. Most `events.payload` values are plain text,
        so the cast is wrapped in `CASE WHEN payload IS JSON THEN ... END`, which
        is the only construct with a guaranteed evaluation order. A plain
        `AND payload IS JSON` would leave Postgres free to attempt the cast on a
        row of another kind first.
        """
        with self._read() as cur:
            cur.execute(
                "SELECT 1 FROM events WHERE episode_id = %s AND kind = "
                "'transcript_confirmed' AND (CASE WHEN payload IS JSON THEN "
                "payload::jsonb ->> 'confirmation_id' END) = %s",
                (episode_id, confirmation_id),
            )
            return cur.fetchone() is not None

    # -- projections -------------------------------------------------------

    def load_snapshot(self, episode_id: str) -> EpisodeSnapshot:
        """Everything `domain.derive_closure` is allowed to look at.

        Two selection readings, both documented rather than silent: **the attempt
        is the latest one**, and **the expiry event is the one for the current
        disposition version**.

        **"Latest" had to be re-expressed, and the difference is recorded
        rather than papered over.** The SQLite store orders by `rowid`, which is
        insertion order and is exactly right there. Postgres has no `rowid`;
        `ctid` looks like one but is a physical address that a `VACUUM` moves, so
        it is not a safe substitute. The ordering here is the recorded timestamp
        with the primary key as a tiebreaker. `expiry_events` is unaffected in
        substance because `UNIQUE (episode_id, disposition_version)` already
        makes at most one row match.
        """
        with self._read() as cur:
            cur.execute("SELECT id FROM episodes WHERE id = %s", (episode_id,))
            if cur.fetchone() is None:
                raise EpisodeNotFound(episode_id)

            cur.execute(
                "SELECT * FROM dispositions WHERE episode_id = %s "
                "ORDER BY version_no DESC LIMIT 1",
                (episode_id,),
            )
            disposition_row = cur.fetchone()
            disposition = (
                _disposition_from_row(disposition_row)
                if disposition_row is not None
                else None
            )

            cur.execute(
                "SELECT id, episode_id, route_id, purpose_id, idempotency_key, "
                "consent_version FROM attempts WHERE episode_id = %s "
                "ORDER BY opened_at DESC, id DESC LIMIT 1",
                (episode_id,),
            )
            attempt_row = cur.fetchone()
            attempt = (
                self._attempt_snapshot(cur, attempt_row)
                if attempt_row is not None
                else None
            )

            consent = self._fetch_consent(cur, episode_id, CLINICAL_SCOPE)
            cur.execute(
                "SELECT id FROM human_acceptances WHERE episode_id = %s "
                "ORDER BY recorded_at DESC, id DESC LIMIT 1",
                (episode_id,),
            )
            acceptance = cur.fetchone()
            cur.execute(
                "SELECT id, human_path FROM escalations WHERE episode_id = %s "
                "ORDER BY recorded_at DESC, id DESC LIMIT 1",
                (episode_id,),
            )
            escalation = cur.fetchone()
            expiry = None
            if disposition is not None:
                cur.execute(
                    "SELECT id FROM expiry_events WHERE episode_id = %s "
                    "AND disposition_version = %s "
                    "ORDER BY occurred_at DESC, id DESC LIMIT 1",
                    (episode_id, disposition.version),
                )
                expiry = cur.fetchone()
            evidence = self._list_evidence(cur, episode_id)

        return EpisodeSnapshot(
            disposition=disposition,
            attempt=attempt,
            evidence=evidence,
            consent_version=consent[0] if consent is not None else None,
            human_acceptance_id=acceptance["id"] if acceptance is not None else None,
            escalation_id=escalation["id"] if escalation is not None else None,
            escalated_human_path=(
                escalation["human_path"] if escalation is not None else None
            ),
            expiry_event_id=expiry["id"] if expiry is not None else None,
        )

    def derive_closure(self, episode_id: str, now_utc: datetime) -> ClosureProjection:
        """Convenience read: load the snapshot, then derive. Policy stays in `domain`."""
        return rules.derive_closure(self.load_snapshot(episode_id), now_utc)


def open_postgres_store(dsn: str, **kwargs: object) -> PostgresEpisodeStore:
    """The factory, mirroring `state.open_store`."""
    return PostgresEpisodeStore(dsn, **kwargs)  # type: ignore[arg-type]


__all__ = [
    "DEV_DSN",
    "PostgresEpisodeStore",
    "open_postgres_store",
    "probe_dsn",
]
