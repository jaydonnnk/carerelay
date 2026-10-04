"""Slice 7b, stage 2: the ported store, the rewritten proof, and D1 and D2 measured.

**What stage 1 left open.** Stage 1 proved the append-only guarantee on Postgres:
14 tables, 42 triggers, and the three statements that can erase a record. It
deliberately did **not** port the store. So the strongest claim in the product was
true on a new engine while nothing else about that engine had been exercised. This
module closes that, in four parts.

**1. The port is complete, and it is the same surface.** `EpisodeStore` is a
`runtime_checkable` Protocol in `state.py` with 32 members. `TestTheTwoStoresShareOneSurface`
compares its signatures against both classes mechanically, so a method that drifts
on one engine is a failure rather than a silent impostor. Three divergences were
found by writing that test, and they are recorded in `TestStatedLimits`.

**2. The two engines answer alike.** One scripted episode is run through SQLite and
through Postgres and the results are compared field by field. This is the part that
cannot be reasoned about from the SQLite tests: ordering, JSON extraction, and
timestamp handling are all engine-specific, and every one of them was rewritten
rather than translated.

**3. The guards came with the port.** A method that returns the right value on
Postgres but stops refusing a bad one is a port that shipped a hole. The guards are
re-proved here on the new engine rather than assumed from SQLite, which is the
discipline the F4 defect taught: a guard that has only ever fired on one engine has
not been shown to fire.

**4. D1 and D2 are decided with a measurement, not an inheritance.** D1's
connection handling and D2's `lock_timeout` were both carried over from SQLite at
stage 1. Both are measured here against the live engine.

**Requires a live Postgres.** Classes that open a connection carry
`@requires_postgres`, so they skip with a named reason rather than reporting green
without an engine. The skip is per class, never module-wide: lesson 22 in
`tasks/lessons.md` records a module-level skip that hid two tests which needed no
database at all.

**What this module does not prove.** It proves the ported store behaves like the
SQLite store on the reachable engine. It does not prove the deployment works: the
Render service has not been pointed at Postgres on a real request path, and a
pooler in transaction mode behaves differently from a session-mode connection. Both
limits are asserted in `TestStatedLimits` so they cannot be quietly deleted.
"""

from __future__ import annotations

import inspect
import pathlib
import subprocess
import sys
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psycopg
import pytest

from carerelay import state
from carerelay.domain import rules
from carerelay.domain.models import (
    AttemptCommand,
    AttemptSnapshot,
    AttemptTransition,
    CallbackResult,
    Disposition,
    DispositionSource,
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
from carerelay.postgres_store import PostgresEpisodeStore, probe_dsn
from carerelay.state import (
    EpisodeStore,
    SqliteEpisodeStore,
    is_postgres_target,
    transcript_confirmation_id,
)

# -- scenario values, shared by both engines --------------------------------

PERSONA = "fictional older adult"
POLICY_VERSION = "fixture-provisional-0"

#: One string, used by **every** call site in this module and by the remote
#: writer in `tests/test_deployment.py`.
#:
#: `policy_versions` is a **global** registry, not a per-episode one, and
#: `register_policy_version` refuses to reuse a version number for different
#: content. Two helpers in this file originally passed slightly different
#: provenance text for the same version, which worked on SQLite only because
#: every SQLite store in the test suite is a fresh file. On the shared Postgres
#: database the second registration met the first and raised
#: `PolicyVersionConflict`, failing fifteen tests at once for one reason.
POLICY_PROVENANCE = (
    "provisional non-clinical placeholder, authored rather than sourced"
)
ACTION_ID = "attend_same_day_review"
NEXT_OWNER_ID = "patient"
FALLBACK_ROUTE_ID = "nurse_line"
ROUTE_ID = "nurse_line"
PURPOSE_ID = "booking"

NOW_UTC = datetime(2026, 10, 1, 4, 0, tzinfo=UTC)
DEADLINE_UTC = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
AFTER_DEADLINE_UTC = DEADLINE_UTC + timedelta(minutes=30)
TRANSCRIPT_TEXT = "I have to see the doctor today before six"

T_OPEN = NOW_UTC
T_ATTEMPT = NOW_UTC + timedelta(minutes=5)
T_CALLBACK = NOW_UTC + timedelta(minutes=10)
T_RECORD = NOW_UTC + timedelta(minutes=15)
T_EXPIRY = AFTER_DEADLINE_UTC
T_RESTATEMENT = AFTER_DEADLINE_UTC + timedelta(minutes=5)


def _disposition(
    episode_id: str, version: int = 1, *, deadline: datetime = DEADLINE_UTC
) -> Disposition:
    """A disposition for **the episode the caller names**.

    `tests/test_state.py` can hard-code one episode id because every test there
    uses the same one. This module gives every test a fresh episode so tests
    sharing a database cannot see each other's rows, so the id has to be a
    parameter: a disposition whose `episode_id` names an episode that does not
    exist fails the foreign key, which is exactly how this was found.
    """
    return Disposition(
        episode_id=episode_id,
        version=version,
        policy_version=POLICY_VERSION,
        action_id=ACTION_ID,
        clinical_deadline_utc=deadline,
        next_owner_id=NEXT_OWNER_ID,
        fallback_route_id=FALLBACK_ROUTE_ID,
        source=(
            DispositionSource.FIXTURE if version == 1 else DispositionSource.REASSESSMENT
        ),
    )


# -- engine plumbing --------------------------------------------------------


def _reachable() -> bool:
    try:
        with psycopg.connect(probe_dsn(), connect_timeout=2):
            return True
    except Exception:
        return False


requires_postgres = pytest.mark.skipif(
    not _reachable(),
    reason=(
        "no Postgres reachable at CARERELAY_TEST_DSN. This test is deliberately "
        "not silently green: a store port that has not run against the engine is "
        "not a port, it is a claim."
    ),
)


@pytest.fixture(scope="module")
def engine() -> str:
    """One clean schema for the module, built once.

    The tables are dropped and rebuilt here rather than per test. Two reasons.
    First, the schema is `CREATE TABLE IF NOT EXISTS` plus 42 triggers, so
    rebuilding it over a network link for every test costs seconds each and buys
    nothing. Second, isolation in this module is by **episode id**, which every
    test generates fresh, and the record is append-only per episode, so tests
    cannot see each other's rows.

    `TRUNCATE` cannot be used to clean between tests: it is refused by the third
    trigger stage 1 added, which is the guarantee working as designed.
    """
    dsn = probe_dsn()
    PostgresEpisodeStore.forget_applied_schema(dsn)
    store = PostgresEpisodeStore(dsn)
    with store._conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        names = [row[0] for row in cur.fetchall()]
        if names:
            cur.execute(
                "DROP TABLE IF EXISTS "
                + ", ".join(f'"{name}"' for name in names)
                + " CASCADE"
            )
    store._conn.commit()
    store.init_schema(force=True)
    store.close()
    return dsn


@pytest.fixture()
def store(engine: str):  # type: ignore[no-untyped-def]
    """A store on the module's schema. Opens no DDL, because `engine` ran it."""
    value = PostgresEpisodeStore(engine)
    yield value
    value.close()


@pytest.fixture()
def episode_id() -> str:
    """A fresh episode per test, so tests cannot see each other's rows."""
    return f"ep-{uuid.uuid4().hex[:12]}"


@pytest.fixture()
def sqlite_store(tmp_path: Path):  # type: ignore[no-untyped-def]
    value = SqliteEpisodeStore(tmp_path / "carerelay.sqlite3")
    yield value
    value.close()


# ---------------------------------------------------------------------------
# 1. The two engines expose one surface
# ---------------------------------------------------------------------------


class TestTheTwoStoresShareOneSurface:
    """`EpisodeStore` is a promise about two classes. This holds them to it.

    **Why signature comparison and not `isinstance`.** `runtime_checkable`
    protocols only check that a name exists, so a method with the wrong
    parameters still satisfies `isinstance`. The port is only trustworthy if the
    *signatures* agree, because that is what a caller is actually written
    against.

    **The three divergences this found.** Writing this test surfaced three, all
    now fixed and all recorded in `TestStatedLimits` so the reasoning survives:

    * `list_barriers` returned `sqlite3.Row` on SQLite, a type no other engine
      has. Both now return `Mapping`.
    * `derive_closure` was unannotated on both classes, so the protocol could
      only say `object`. Both now return `ClosureProjection`.
    * `record_callback_once` accepted `Origin | str` on Postgres and `Origin` on
      SQLite. Widening one engine is how a caller starts depending on a
      permissiveness the other engine does not have, so Postgres was narrowed.
    """

    def test_every_protocol_member_exists_on_both_classes(self) -> None:
        members = sorted(n for n in dir(EpisodeStore) if not n.startswith("_"))
        assert len(members) == 32, (
            f"the protocol has {len(members)} members; this test was written "
            "against 32, so one was added or removed without revisiting it"
        )
        for cls in (SqliteEpisodeStore, PostgresEpisodeStore):
            missing = sorted(n for n in members if not hasattr(cls, n))
            assert missing == [], f"{cls.__name__} does not implement {missing}"

    def test_every_protocol_signature_matches_both_classes(self) -> None:
        members = sorted(n for n in dir(EpisodeStore) if not n.startswith("_"))
        divergences: list[str] = []
        for cls in (SqliteEpisodeStore, PostgresEpisodeStore):
            for name in members:
                declared = inspect.signature(getattr(EpisodeStore, name))
                actual = inspect.signature(getattr(cls, name))
                if str(declared) != str(actual):
                    divergences.append(
                        f"{cls.__name__}.{name}: protocol {declared} vs {actual}"
                    )
        assert divergences == [], (
            "the protocol does not describe both engines:\n"
            + "\n".join(divergences)
        )

    def test_both_classes_satisfy_the_protocol(self) -> None:
        """The weaker check, kept because it catches a missing method cheaply."""
        memory = SqliteEpisodeStore(":memory:")
        try:
            assert isinstance(memory, EpisodeStore)
        finally:
            memory.close()
        assert is_postgres_target(probe_dsn()), (
            "the test DSN is not a Postgres scheme, so `open_store` would build "
            "a SQLite store and this whole module would test the wrong engine"
        )

    def test_the_dispatch_refuses_a_keyword_the_engine_does_not_take(self) -> None:
        """A caller asking for a busy timeout it will not get must hear about it.

        Dropping the unknown keyword silently is the alternative, and it is worse:
        the caller believes it has a bounded wait and does not.
        """
        with pytest.raises(TypeError, match="busy_timeout_ms"):
            state.open_store(probe_dsn(), busy_timeout_ms=5000)
        with pytest.raises(TypeError, match="lock_timeout_s"):
            state.open_store(":memory:", lock_timeout_s=1.0)

    def test_a_sqlite_only_process_never_imports_psycopg(self) -> None:
        """The lazy import, proved across a real process boundary.

        `psycopg` is a dependency the SQLite path does not need. If it were
        imported at module scope in `state.py`, every local run and every test
        that uses `:memory:` would pay for a driver it never opens a connection
        with, and a machine without the driver installed could not run the demo
        at all. The subprocess is the only honest place to check this, because
        the test session itself has already imported `psycopg`.
        """
        program = (
            "import sys\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "from carerelay.state import open_store\n"
            "store = open_store(':memory:')\n"
            "store.close()\n"
            "print('psycopg' in sys.modules)\n"
        )
        completed = subprocess.run(
            [sys.executable, "-c", program, str(Path(__file__).resolve().parents[1] / "src")],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip().splitlines()[-1] == "False", (
            "opening a SQLite store imported psycopg, so the Postgres driver is "
            "now a hard dependency of the local path"
        )

    def test_a_bare_string_origin_is_refused_not_quietly_accepted(self) -> None:
        """The narrowing the parity test found has to hold at runtime, not only
        in the annotations.

        Comparing signatures cannot see this. Both classes declare
        `origin: Origin`, and the Postgres helpers went on accepting a bare
        string behind an `isinstance` fallback, so the parity test stayed green
        over the exact divergence it exists to prevent. Needs no database:
        `_origin_value` is a static method and the refusal is the whole
        behaviour under test.
        """
        for origin in (Origin.PLATFORM, Origin.LOCAL_SIM):
            assert PostgresEpisodeStore._origin_value(origin) == origin.value
        with pytest.raises(state.StateError):
            PostgresEpisodeStore._origin_value("local-sim")
        with pytest.raises(state.StateError):
            PostgresEpisodeStore._origin_value("anything-else")


# ---------------------------------------------------------------------------
# The scripted episode, run on both engines
# ---------------------------------------------------------------------------


def _script(store: object, episode_id: str) -> dict[str, object]:
    """One episode through the whole store surface. Engine-agnostic.

    Every call here goes through the store and nothing through raw SQL, because
    the question is whether the *product's* write path agrees across engines, not
    whether two databases can hold the same rows.

    The return value carries the handles a test needs to dig further (the attempt
    id, the restatement id). Those are generated values and differ between
    engines by design, so they are not part of the comparison below.

    **The callback key is prefixed with the episode id, and that is not cosmetic.**
    `callbacks.callback_key` is `UNIQUE` **globally**, not per episode: a provider
    callback key replayed against a different episode has to be refused, or a
    receipt could be replayed into someone else's record. The first run of this
    script on the shared test database therefore poisoned the literal
    `"callback-1"` for every later test in the session, and the second run's first
    callback came back `duplicate` on Postgres while SQLite, being a fresh
    in-memory file per test, had never seen it. That is the isolation bug it
    looks like, and it is also the constraint working.
    """
    store.create_episode(episode_id, PERSONA, now_utc=T_OPEN)  # type: ignore[attr-defined]
    store.register_policy_version(  # type: ignore[attr-defined]
        POLICY_VERSION,
        content="{}",
        provenance=POLICY_PROVENANCE,
        approved_by=None,
        now_utc=T_OPEN,
    )
    store.insert_disposition(_disposition(episode_id), now_utc=T_OPEN)  # type: ignore[attr-defined]
    consent_version = store.change_consent(  # type: ignore[attr-defined]
        episode_id, state.CLINICAL_SCOPE, granted=True, now_utc=T_OPEN
    )
    store.record_refusal(episode_id, "intake", "fixture", now_utc=T_OPEN)  # type: ignore[attr-defined]

    command = AttemptCommand(episode_id, ROUTE_ID, PURPOSE_ID, consent_version)
    key = state.derive_attempt_key(episode_id, ROUTE_ID, PURPOSE_ID)
    callback_key = f"{episode_id}-callback-1"
    first: AttemptSnapshot = store.open_attempt_once(command, key, now_utc=T_ATTEMPT)  # type: ignore[attr-defined]
    again: AttemptSnapshot = store.open_attempt_once(command, key, now_utc=T_ATTEMPT)  # type: ignore[attr-defined]

    applied = store.record_callback_once(  # type: ignore[attr-defined]
        first.attempt_id,
        callback_key,
        CallbackResult(payload="{}", transition=ExecutionStatus.ACKNOWLEDGED),
        Origin.LOCAL_SIM,
        now_utc=T_CALLBACK,
    )
    duplicate = store.record_callback_once(  # type: ignore[attr-defined]
        first.attempt_id,
        callback_key,
        CallbackResult(payload="{}", transition=ExecutionStatus.ACKNOWLEDGED),
        Origin.LOCAL_SIM,
        now_utc=T_CALLBACK,
    )
    store.record_evidence(  # type: ignore[attr-defined]
        episode_id,
        # Not the simulated one: `documented` evidence must be non-simulated
        # **and** carry a source ref, which is the provenance CHECK both engines
        # enforce. A simulated documented row is refused, and `tests/test_state.py`
        # uses it for exactly that, so the script has to use the real-shaped one.
        EvidenceRecord(
            level=EvidenceLevel.DOCUMENTED,
            simulated=False,
            provenance="fictional provider receipt",
            source_ref="receipt-0001",
        ),
        now_utc=T_RECORD,
    )
    store.record_barrier(  # type: ignore[attr-defined]
        episode_id,
        disposition_version=1,
        barrier_text="no transport today",
        proposed_route_id="nurse_line",
        permitted_route_id="nurse_line",
        stopped_at_human_path=False,
        now_utc=T_RECORD,
    )
    store.record_escalation(  # type: ignore[attr-defined]
        episode_id, human_path="nurse_line", outcome="handed_over", now_utc=T_RECORD
    )
    store.record_human_acceptance(  # type: ignore[attr-defined]
        episode_id, accepted_by="fictional daughter", scope="handoff", now_utc=T_RECORD
    )
    expired = store.record_expiry_once(episode_id, 1, T_EXPIRY)  # type: ignore[attr-defined]
    expired_again = store.record_expiry_once(episode_id, 1, T_EXPIRY)  # type: ignore[attr-defined]

    restatement_id = store.record_restatement(  # type: ignore[attr-defined]
        episode_id,
        disposition_version=1,
        hint_level=HintLevel.H2,
        input_mode=InputMode.TEXT,
        transcript_confirmed=True,
        extracted=ExtractedPlan("see the doctor", "today before 6pm", "myself"),
        comparison=PlanComparison(frozenset(), frozenset(), frozenset()),
        repair_round=0,
        outcome=RecallOutcome.RECALL_SCAFFOLDED,
        dwell_seconds=12.5,
        now_utc=T_RESTATEMENT,
    )
    store.record_hint_event(  # type: ignore[attr-defined]
        episode_id,
        hint_level=HintLevel.H2,
        kind=HintEventKind.SHOWN,
        dwell_seconds=4.0,
        now_utc=T_RESTATEMENT,
    )
    confirmation_id = store.record_transcript_confirmation(  # type: ignore[attr-defined]
        episode_id, text=TRANSCRIPT_TEXT, now_utc=T_RESTATEMENT
    )
    return {
        "consent_version": consent_version,
        "attempt": first,
        "attempt_again": again,
        "applied": applied,
        "duplicate": duplicate,
        "expired": expired,
        "expired_again": expired_again,
        "restatement_id": restatement_id,
        "confirmation_id": confirmation_id,
    }


def _projection(store: object, episode_id: str, *, now_utc: datetime) -> dict[str, object]:
    """Everything an engine can answer, with the generated ids taken out.

    **Why a projection and not the objects themselves.** Three kinds of value in
    this record are generated per write: `uuid4` handles for barriers,
    escalations, acceptances, expiry events and restatements; `SERIAL` keys for
    receipts; and the attempt id. Two engines running the same script produce
    different ones, so comparing the dataclasses directly would fail on identity
    rather than on behaviour. Everything a caller can actually depend on is here
    instead, which is the comparison that matters.

    Timestamps are normalised to ISO strings rather than compared as
    `datetime`, because SQLite hands back naive or aware values depending on the
    column and Postgres hands back aware ones; the ISO form is what both stores
    wrote.
    """
    dispositions = store.list_dispositions(episode_id)  # type: ignore[attr-defined]
    attempts = store.list_attempts(episode_id)  # type: ignore[attr-defined]
    transitions: tuple[AttemptTransition, ...] = store.list_transitions(attempts[0].attempt_id)  # type: ignore[attr-defined]
    snapshot = store.load_snapshot(episode_id)  # type: ignore[attr-defined]
    closure = rules.derive_closure(snapshot, now_utc)
    return {
        "dispositions": [
            (
                d.version,
                d.policy_version,
                d.action_id,
                state._iso(d.clinical_deadline_utc),
                d.next_owner_id,
                d.fallback_route_id,
                d.source.value,
            )
            for d in dispositions
        ],
        "attempts": [
            (a.idempotency_key, a.route_id, a.consent_version, a.execution.value)
            for a in attempts
        ],
        "transitions": [
            (t.seq, t.kind.value, t.origin.value, t.payload, state._iso(t.recorded_at))
            for t in transitions
        ],
        "receipts": [
            (
                r.route_id,
                r.callback_key,
                r.duplicate_of is not None,
                bool(r.accepted),
                r.rejection_reason,
                r.origin.value,
                r.result.value if r.result is not None else None,
                r.payload,
                state._iso(r.received_at),
            )
            for r in store.list_callbacks(episode_id)  # type: ignore[attr-defined]
        ],
        "evidence": [
            (e.level.value, bool(e.simulated), e.provenance, e.source_ref)
            for e in store.list_evidence(episode_id)  # type: ignore[attr-defined]
        ],
        "barriers": [
            tuple(sorted((k, v) for k, v in row.items() if k != "id"))
            for row in store.list_barriers(episode_id)  # type: ignore[attr-defined]
        ],
        "expiry_events": [
            (version, state._iso(at))
            for version, at in store.list_expiry_events(episode_id)  # type: ignore[attr-defined]
        ],
        "restatements": [
            (
                r.disposition_version,
                r.hint_level.value,
                r.input_mode.value,
                bool(r.transcript_confirmed),
                r.extracted.action_span,
                r.extracted.deadline_span,
                r.extracted.next_owner_span,
                r.repair_round,
                r.outcome.value,
                r.dwell_seconds,
            )
            for r in store.list_restatements(episode_id)  # type: ignore[attr-defined]
        ],
        "hint_events": [
            (h.level.value, h.kind.value, h.dwell_seconds)
            for h in store.list_hint_events(episode_id)  # type: ignore[attr-defined]
        ],
        "event_kinds": [
            kind for kind, _payload, _at in store.list_events(episode_id)  # type: ignore[attr-defined]
        ],
        "consent_version": snapshot.consent_version,
        "has_acceptance": snapshot.human_acceptance_id is not None,
        "has_escalation": snapshot.escalation_id is not None,
        "escalated_human_path": snapshot.escalated_human_path,
        "has_expiry": snapshot.expiry_event_id is not None,
        "transcript_confirmed": store.has_transcript_confirmation(  # type: ignore[attr-defined]
            episode_id, transcript_confirmation_id(TRANSCRIPT_TEXT)
        ),
        "closure": (
            closure.execution.value,
            closure.evidence.value,
            closure.closure.value,
            closure.action_owner_id,
            closure.care_evidenced,
            closure.simulated,
        ),
    }


@requires_postgres
class TestBothEnginesAnswerAlike:
    """The same script on both engines, compared field by field.

    This is the test that would have caught the three translation traps the
    migration plan names. `ORDER BY rowid` does not exist in Postgres, so the
    ordering of barriers, receipts and restatements had to be re-expressed as a
    recorded timestamp plus a key tiebreaker. `json_extract(payload, ...)` does
    not exist either, so `has_transcript_confirmation` had to be rewritten, and
    on a non-JSON payload the cast raises rather than returning NULL. Neither
    would have failed an import and neither would have failed a test written
    against SQLite.
    """

    def test_the_whole_scripted_episode_is_identical_on_both_engines(
        self, store, sqlite_store
    ) -> None:
        episode = f"ep-{uuid.uuid4().hex[:12]}"
        _script(sqlite_store, episode)
        _script(store, episode)

        expected = _projection(sqlite_store, episode, now_utc=T_RESTATEMENT)
        actual = _projection(store, episode, now_utc=T_RESTATEMENT)
        assert actual == expected, (
            "the two engines answered differently. Keys that differ: "
            f"{sorted(k for k in expected if expected[k] != actual[k])}"
        )

    def test_the_projection_is_not_empty(self, sqlite_store) -> None:
        """The control for the comparison above.

        A projection that silently produced empty tuples on both engines would
        compare equal and prove nothing. This requires the SQLite half, which is
        the half already covered by 557 tests, to be non-empty first, so an empty
        Postgres result cannot pass by agreeing with an empty baseline.
        """
        episode = f"ep-{uuid.uuid4().hex[:12]}"
        _script(sqlite_store, episode)
        baseline = _projection(sqlite_store, episode, now_utc=T_RESTATEMENT)
        nonempty = {k: v for k, v in baseline.items() if isinstance(v, (list, tuple))}
        assert nonempty, "the projection produced no collections"
        for key, value in nonempty.items():
            assert len(value) > 0, f"{key} is empty on SQLite, so comparing it proves nothing"

    def test_the_idempotent_paths_agree(
        self, store, sqlite_store
    ) -> None:
        """Idempotency is a return value, not only a row count.

        `INSERT OR REPLACE` has no Postgres equivalent, so both `open_attempt_once`
        and `record_expiry_once` were rewritten onto `ON CONFLICT DO NOTHING` plus
        a read-back. The second call has to return the *same* answer the first
        did, and on the same engine it has to be the same object identity the
        SQLite store returns.
        """
        episode = f"ep-{uuid.uuid4().hex[:12]}"
        on_sqlite = _script(sqlite_store, episode)
        on_postgres = _script(store, episode)

        assert on_sqlite["attempt"].attempt_id == on_sqlite["attempt_again"].attempt_id
        assert on_postgres["attempt"].attempt_id == on_postgres["attempt_again"].attempt_id
        assert on_sqlite["expired"] is True and on_sqlite["expired_again"] is False
        assert on_postgres["expired"] is True and on_postgres["expired_again"] is False
        assert on_sqlite["applied"].disposition is ReceiptDisposition.APPLIED
        assert on_sqlite["duplicate"].disposition is ReceiptDisposition.DUPLICATE
        assert on_postgres["applied"].disposition is ReceiptDisposition.APPLIED
        assert on_postgres["duplicate"].disposition is ReceiptDisposition.DUPLICATE
        assert (
            on_sqlite["applied"].disposition is on_postgres["applied"].disposition
        ), "a first callback was applied on one engine and not the other"
        assert (
            on_sqlite["duplicate"].disposition is on_postgres["duplicate"].disposition
        ), "a repeated callback was judged differently on the two engines"


@requires_postgres
class TestTheGuardsCameWithThePort:
    """A port that returns the right values but stops refusing the wrong ones
    has shipped a hole.

    Each of these is already proved on SQLite in `tests/test_state.py`. They are
    re-proved here because the refusal is raised by code that was **rewritten**,
    not copied: `INSERT OR REPLACE` became `ON CONFLICT`, `json_extract` became a
    guarded cast, and `BEGIN IMMEDIATE` became `SELECT ... FOR UPDATE`. A guard
    whose mechanism changed has to be shown firing again.
    """

    def _seeded(self, store, episode_id: str) -> int:
        store.create_episode(episode_id, PERSONA, now_utc=NOW_UTC)
        store.register_policy_version(
            POLICY_VERSION,
            content="{}",
            provenance=POLICY_PROVENANCE,
            approved_by=None,
            now_utc=NOW_UTC,
        )
        store.insert_disposition(_disposition(episode_id), now_utc=NOW_UTC)
        return store.change_consent(
            episode_id, state.CLINICAL_SCOPE, granted=True, now_utc=NOW_UTC
        )

    def test_an_earlier_deadline_is_refused(self, store, episode_id: str) -> None:
        """O7. The monotonicity check, on the engine that has no `rowid`."""
        self._seeded(store, episode_id)
        with pytest.raises(state.DeadlineNotMonotonic):
            store.insert_disposition(
                _disposition(
                    episode_id,
                    version=2,
                    deadline=DEADLINE_UTC - timedelta(minutes=1),
                ),
                now_utc=NOW_UTC,
            )
        assert len(store.list_dispositions(episode_id)) == 1

    def test_a_repeated_disposition_version_is_refused(
        self, store, episode_id: str
    ) -> None:
        """The UNIQUE constraint is the backstop for a pure insert, and it has to
        surface as the product's error rather than as a driver error."""
        self._seeded(store, episode_id)
        with pytest.raises(state.DispositionVersionConflict):
            store.insert_disposition(_disposition(episode_id), now_utc=NOW_UTC)

    def test_unsourced_documented_evidence_is_refused(
        self, store, episode_id: str
    ) -> None:
        """The provenance CHECK, on Postgres. A `CHECK` that ports as a trigger
        or a constraint that does not fire is the difference between a record
        that can be audited and one that cannot."""
        self._seeded(store, episode_id)
        with pytest.raises(state.EvidenceProvenanceViolation):
            store.record_evidence(
                episode_id,
                EvidenceRecord(
                    level=EvidenceLevel.DOCUMENTED,
                    simulated=False,
                    provenance="verbal",
                    source_ref=None,
                ),
                now_utc=NOW_UTC,
            )
        assert store.list_evidence(episode_id) == ()

    def test_an_expiry_before_the_deadline_is_refused(
        self, store, episode_id: str
    ) -> None:
        self._seeded(store, episode_id)
        with pytest.raises(state.PrematureExpiry):
            store.record_expiry_once(episode_id, 1, NOW_UTC)

    def test_an_expiry_for_an_unrecorded_version_is_refused(
        self, store, episode_id: str
    ) -> None:
        self._seeded(store, episode_id)
        with pytest.raises(state.NoDispositionForExpiry):
            store.record_expiry_once(episode_id, 7, AFTER_DEADLINE_UTC)

    def test_an_unconfirmed_voice_restatement_is_refused(
        self, store, episode_id: str
    ) -> None:
        """The second layer of the transcript rule. Bypassing the service guard
        must not be enough, on Postgres either."""
        self._seeded(store, episode_id)
        with pytest.raises(state.UnconfirmedTranscript):
            store.record_restatement(
                episode_id,
                disposition_version=1,
                hint_level=HintLevel.H0,
                input_mode=InputMode.VOICE,
                transcript_confirmed=False,
                extracted=ExtractedPlan("see the doctor", "today before 6pm", "myself"),
                comparison=PlanComparison(frozenset(), frozenset(), frozenset()),
                repair_round=0,
                outcome=RecallOutcome.RECALL_UNAIDED,
                dwell_seconds=None,
                now_utc=NOW_UTC,
            )

    def test_a_third_repair_round_is_refused(self, store, episode_id: str) -> None:
        self._seeded(store, episode_id)
        with pytest.raises(state.RepairRoundOutOfRange):
            store.record_restatement(
                episode_id,
                disposition_version=1,
                hint_level=HintLevel.H0,
                input_mode=InputMode.TEXT,
                transcript_confirmed=False,
                extracted=ExtractedPlan(None, None, None),
                comparison=PlanComparison(frozenset(), frozenset(), frozenset()),
                repair_round=3,
                outcome=RecallOutcome.NOT_RECALLED,
                dwell_seconds=None,
                now_utc=NOW_UTC,
            )

    def test_a_revoked_consent_stops_a_callback(
        self, store, episode_id: str
    ) -> None:
        """The consent re-check inside `record_callback_once`, on Postgres.

        On SQLite this ran inside `BEGIN IMMEDIATE`. On Postgres the same
        serialisation comes from a row lock, so the re-read has to happen inside
        the locked transaction or a revocation that lands between the read and
        the write is silently ignored.
        """
        consent_version = self._seeded(store, episode_id)
        command = AttemptCommand(episode_id, ROUTE_ID, PURPOSE_ID, consent_version)
        key = state.derive_attempt_key(episode_id, ROUTE_ID, PURPOSE_ID)
        attempt = store.open_attempt_once(command, key, now_utc=T_ATTEMPT)
        store.change_consent(
            episode_id, state.CLINICAL_SCOPE, granted=False, now_utc=T_ATTEMPT
        )
        outcome = store.record_callback_once(
            attempt.attempt_id,
            "callback-after-revoke",
            CallbackResult(payload="{}", transition=ExecutionStatus.ACKNOWLEDGED),
            Origin.LOCAL_SIM,
            now_utc=T_CALLBACK,
        )
        assert outcome.applied is False, (
            "a callback was applied after consent was revoked, so the re-check "
            "did not survive the port"
        )
        assert outcome.rejection_reason, "the refusal was not given a reason"

    def test_a_bare_string_origin_is_refused_on_a_real_call_on_both_engines(
        self, store, sqlite_store, episode_id: str
    ) -> None:
        """The same refusal through the public call, on each engine.

        `_origin_value` is an internal helper, so pinning it alone would leave a
        later refactor free to stop calling it. This drives
        `record_callback_once` end to end instead. The **error type** differs
        (SQLite reaches `origin.value` on a `str` and raises `AttributeError`;
        Postgres refuses first with a `StateError` that says why), and that
        difference is recorded rather than hidden. What must not differ is the
        answer: neither engine writes a receipt for an origin it was not given
        as an `Origin`.
        """
        sqlite_episode = f"{episode_id}-sqlite"
        pairs = (
            (store, episode_id, self._seeded(store, episode_id)),
            (sqlite_store, sqlite_episode, self._seeded(sqlite_store, sqlite_episode)),
        )
        for target, episode, consent_version in pairs:
            command = AttemptCommand(episode, ROUTE_ID, PURPOSE_ID, consent_version)
            key = state.derive_attempt_key(episode, ROUTE_ID, PURPOSE_ID)
            attempt = target.open_attempt_once(command, key, now_utc=T_ATTEMPT)
            with pytest.raises((state.StateError, AttributeError)):
                target.record_callback_once(
                    attempt.attempt_id,
                    f"{episode}-string-origin",
                    CallbackResult(
                        payload="{}", transition=ExecutionStatus.ACKNOWLEDGED
                    ),
                    "local-sim",  # type: ignore[arg-type]
                    now_utc=T_CALLBACK,
                )
            assert target.list_callbacks(episode) == (), (
                f"{type(target).__name__} wrote a receipt for an origin it was "
                "only given as a string"
            )

    def test_a_non_json_event_payload_does_not_break_the_transcript_read(
        self, store, episode_id: str
    ) -> None:
        """The `IS JSON` guard, on a row written by hand.

        The Postgres cast `payload::jsonb` **raises** on a payload that is not
        JSON, and most `events.payload` values are plain text. SQLite never had
        this problem: it evaluates `AND` left to right, so `kind = ...` filters
        the row out before `json_extract` ever sees it. Postgres promises no
        evaluation order, so the port had to be guarded with
        `CASE WHEN payload IS JSON`, and this is the row the guard exists for.

        The row is written with raw SQL on purpose. The threat model for this
        record is a writer that bypasses the store, which is the same assumption
        the triggers are built on, so "the store only ever writes JSON" is not an
        answer.
        """
        self._seeded(store, episode_id)
        with store._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO events (episode_id, kind, payload, recorded_at) "
                "VALUES (%s, %s, %s, %s)",
                (episode_id, "transcript_confirmed", "not json at all", state._iso(NOW_UTC)),
            )
        store._conn.commit()
        assert store.has_transcript_confirmation(episode_id, "any-id") is False, (
            "a hand-written non-JSON payload broke the transcript read, so the "
            "IS JSON guard is either missing or not covering this row"
        )

    def test_an_unknown_episode_is_refused(self, store) -> None:
        with pytest.raises(state.EpisodeNotFound):
            store.load_snapshot("episode-that-does-not-exist")

    def test_an_unknown_restatement_is_refused(self, store, episode_id: str) -> None:
        self._seeded(store, episode_id)
        with pytest.raises(state.RestatementNotFound):
            store.get_restatement("restatement-that-does-not-exist")

    def test_a_read_does_not_change_the_record(self, store, episode_id: str) -> None:
        """`_read()` must not leave a transaction open.

        psycopg opens a transaction on the first statement when `autocommit` is
        off, and a read that never commits pins a session. On a pooler with a
        limited number of backend sessions that is a leak, not a style problem,
        so the read path rolls back and closes rather than merely fetching.
        """
        consent_version = self._seeded(store, episode_id)
        command = AttemptCommand(episode_id, ROUTE_ID, PURPOSE_ID, consent_version)
        key = state.derive_attempt_key(episode_id, ROUTE_ID, PURPOSE_ID)
        store.open_attempt_once(command, key, now_utc=T_ATTEMPT)
        before = store.list_events(episode_id)
        store.load_snapshot(episode_id)
        store.derive_closure(episode_id, AFTER_DEADLINE_UTC)
        store.list_dispositions(episode_id)
        store.list_barriers(episode_id)
        assert store.list_events(episode_id) == before


@requires_postgres
class TestO1OnTheDispositionsTable:
    """The O1 defect, re-proved on the table it was actually about.

    Stage 1 proved `ON CONFLICT DO UPDATE` is refused on `episodes`. That was the
    mechanism, not the risk. O1 is about **dispositions**: the table that holds
    the clinical instruction and the deadline, where a silent replace would
    rewrite what the patient was told to do and when. An instruction that can be
    overwritten without a trace is the whole reason the record is append-only, so
    this is the table the guarantee has to hold on.

    `DO NOTHING` is the control, and it is load-bearing rather than incidental:
    `open_attempt_once` and `record_expiry_once` both depend on it, so a rule
    that refused every conflict would break idempotency.
    """

    def test_a_conflicting_replace_on_dispositions_is_refused(
        self, store, episode_id: str
    ) -> None:
        store.create_episode(episode_id, PERSONA, now_utc=NOW_UTC)
        store.register_policy_version(
            POLICY_VERSION,
            content="{}",
            provenance=POLICY_PROVENANCE,
            approved_by=None,
            now_utc=NOW_UTC,
        )
        store.insert_disposition(_disposition(episode_id), now_utc=NOW_UTC)
        with pytest.raises(psycopg.errors.RestrictViolation) as caught:
            with store._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO dispositions (episode_id, version_no, policy_version,"
                    " action_id, clinical_deadline_utc, next_owner_id,"
                    " fallback_route_id, source, created_at)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    " ON CONFLICT (episode_id, version_no) DO UPDATE"
                    " SET action_id = EXCLUDED.action_id",
                    (
                        episode_id,
                        1,
                        POLICY_VERSION,
                        "tampered_action",
                        state._iso(DEADLINE_UTC),
                        NEXT_OWNER_ID,
                        FALLBACK_ROUTE_ID,
                        "fixture",
                        state._iso(NOW_UTC),
                    ),
                )
        assert "UPDATE is refused" in str(caught.value), (
            "the conflict was refused, but not by the append-only trigger, so "
            "the refusal is incidental and could be another constraint"
        )
        store._conn.rollback()
        assert store.list_dispositions(episode_id)[0].action_id == ACTION_ID, (
            "the disposition was replaced"
        )

    def test_a_conflicting_do_nothing_on_dispositions_is_allowed(
        self, store, episode_id: str
    ) -> None:
        store.create_episode(episode_id, PERSONA, now_utc=NOW_UTC)
        store.register_policy_version(
            POLICY_VERSION,
            content="{}",
            provenance=POLICY_PROVENANCE,
            approved_by=None,
            now_utc=NOW_UTC,
        )
        store.insert_disposition(_disposition(episode_id), now_utc=NOW_UTC)
        with store._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dispositions (episode_id, version_no, policy_version,"
                " action_id, clinical_deadline_utc, next_owner_id,"
                " fallback_route_id, source, created_at)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                " ON CONFLICT (episode_id, version_no) DO NOTHING",
                (
                    episode_id,
                    1,
                    POLICY_VERSION,
                    "ignored_duplicate",
                    state._iso(DEADLINE_UTC),
                    NEXT_OWNER_ID,
                    FALLBACK_ROUTE_ID,
                    "fixture",
                    state._iso(NOW_UTC),
                ),
            )
        store._conn.commit()
        rows = store.list_dispositions(episode_id)
        assert len(rows) == 1, "DO NOTHING wrote a second row"
        assert rows[0].action_id == ACTION_ID, "DO NOTHING replaced the first row"

    def test_the_stores_own_idempotent_writes_go_through_do_nothing(
        self, store, episode_id: str
    ) -> None:
        """The product's own paths, not just raw SQL.

        `open_attempt_once` and `record_expiry_once` are the two places that
        write "only if not already written". They must succeed on a second call
        rather than meet the UPDATE trigger, which is what would happen if the
        port had used `DO UPDATE` to make the read-back convenient.
        """
        store.create_episode(episode_id, PERSONA, now_utc=NOW_UTC)
        store.register_policy_version(
            POLICY_VERSION,
            content="{}",
            provenance=POLICY_PROVENANCE,
            approved_by=None,
            now_utc=NOW_UTC,
        )
        store.insert_disposition(_disposition(episode_id), now_utc=NOW_UTC)
        consent_version = store.change_consent(
            episode_id, state.CLINICAL_SCOPE, granted=True, now_utc=NOW_UTC
        )
        command = AttemptCommand(episode_id, ROUTE_ID, PURPOSE_ID, consent_version)
        key = state.derive_attempt_key(episode_id, ROUTE_ID, PURPOSE_ID)
        first = store.open_attempt_once(command, key, now_utc=T_ATTEMPT)
        second = store.open_attempt_once(command, key, now_utc=T_ATTEMPT)
        assert first.attempt_id == second.attempt_id
        assert len(store.list_attempts(episode_id)) == 1

        assert store.record_expiry_once(episode_id, 1, AFTER_DEADLINE_UTC) is True
        assert store.record_expiry_once(episode_id, 1, AFTER_DEADLINE_UTC) is False
        assert len(store.list_expiry_events(episode_id)) == 1


@requires_postgres
class TestTwoWritersAtOneKey:
    """Two of the product's own writers, at one key, at the same instant.

    **Why this class exists.** `open_attempt_once` and `record_expiry_once` each
    return through a `SELECT`-based guard when the row is already there, so a
    sequential second call never reaches the `ON CONFLICT` clause or the
    `UniqueViolation` handler sitting behind it. Those two branches are reachable
    only when two connections clear the guard before either writes, which is the
    exact situation the rewrite from `INSERT OR REPLACE` was for. Before this
    class existed neither branch had a test: mutations S1 and S2 in
    `tests/_mutate_slice7b_stage2.py` survived the whole suite for that reason
    and for no other, and the guards behind them were untested rather than
    broken.

    **Two stores, therefore two connections.** One `psycopg` connection cannot be
    driven by two threads at once, and sharing one would serialise the writers
    and reproduce nothing. Each thread opens its own store, and both are already
    connected before the barrier is released, so what races is the statements
    and not connection setup.

    **Several trials, every one of which must be right.** A barrier makes two
    writers overlap; it cannot promise either will win, or that they overlap at
    all on a given run. A trial that does not overlap still has to give the
    correct answer, so asserting on every trial cannot make this flaky in the
    passing direction. Repetition buys the other direction: the more trials, the
    less a mutation can slip through by never being exercised.
    """

    TRIALS = 6

    def _race(self, dsn: str, work) -> list[tuple[str, object]]:  # type: ignore[no-untyped-def]
        """Run `work(store)` on two connections, released together."""
        stores = [PostgresEpisodeStore(dsn), PostgresEpisodeStore(dsn)]
        barrier = threading.Barrier(2)
        results: list[tuple[str, object]] = [("lost", "thread never ran")] * 2

        def run(index: int) -> None:
            try:
                barrier.wait(timeout=30)
                results[index] = ("ok", work(stores[index]))
            except BaseException as exc:  # the type is the finding, so keep it
                results[index] = ("raised", f"{type(exc).__name__}: {exc}")
            finally:
                stores[index].close()

        threads = [threading.Thread(target=run, args=(index,)) for index in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)
        return results

    def _seeded(self, dsn: str) -> tuple[str, int]:
        """A fresh episode per trial, so no trial inherits the last one's row."""
        episode = f"ep-race-{uuid.uuid4().hex[:12]}"
        seeder = PostgresEpisodeStore(dsn)
        try:
            seeder.create_episode(episode, PERSONA, now_utc=NOW_UTC)
            seeder.register_policy_version(
                POLICY_VERSION,
                content="{}",
                provenance=POLICY_PROVENANCE,
                approved_by=None,
                now_utc=NOW_UTC,
            )
            seeder.insert_disposition(_disposition(episode), now_utc=NOW_UTC)
            consent = seeder.change_consent(
                episode, state.CLINICAL_SCOPE, granted=True, now_utc=NOW_UTC
            )
        finally:
            seeder.close()
        return episode, consent

    def _rows(self, dsn: str, table: str, episode: str) -> int:
        with psycopg.connect(dsn) as check, check.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {table} WHERE episode_id = %s", (episode,))
            return int(cur.fetchone()[0])

    def test_two_writers_opening_one_attempt_agree_on_one_row(
        self, engine: str
    ) -> None:
        """The loser reads the winner's row. Neither writer is refused.

        This is the branch `ON CONFLICT DO NOTHING` exists for. Under
        `DO UPDATE` the loser meets the append-only trigger instead and the
        caller gets a driver error where the product promises a suppressed
        duplicate, which is mutation S1.
        """
        for trial in range(self.TRIALS):
            episode, consent_version = self._seeded(engine)
            command = AttemptCommand(episode, ROUTE_ID, PURPOSE_ID, consent_version)
            key = state.derive_attempt_key(episode, ROUTE_ID, PURPOSE_ID)
            results = self._race(
                engine,
                lambda store: store.open_attempt_once(command, key, now_utc=T_ATTEMPT),
            )
            raised = [value for kind, value in results if kind == "raised"]
            assert raised == [], (
                f"trial {trial}: a writer was refused instead of being given the "
                f"winner's attempt: {raised}"
            )
            ids = {value.attempt_id for kind, value in results if kind == "ok"}
            assert len(ids) == 1, (
                f"trial {trial}: two writers at one key opened {len(ids)} attempts"
            )
            assert self._rows(engine, "attempts", episode) == 1, (
                f"trial {trial}: one idempotency key left more than one attempt row"
            )

    def test_two_writers_recording_one_expiry_get_one_true_and_one_false(
        self, engine: str
    ) -> None:
        """Exactly one writer records the fact; the other is told it is recorded.

        This is the branch the `UniqueViolation` handler exists for. Re-raising
        it hands the loser a driver error where the product promises `False`,
        which is mutation S2.
        """
        for trial in range(self.TRIALS):
            episode, _ = self._seeded(engine)
            results = self._race(
                engine, lambda store: store.record_expiry_once(episode, 1, T_EXPIRY)
            )
            raised = [value for kind, value in results if kind == "raised"]
            assert raised == [], (
                f"trial {trial}: the losing writer was handed a driver error "
                f"instead of False: {raised}"
            )
            answers = sorted(value for kind, value in results if kind == "ok")
            assert answers == [False, True], (
                f"trial {trial}: exactly one writer may record the expiry, got "
                f"{answers}"
            )
            assert self._rows(engine, "expiry_events", episode) == 1, (
                f"trial {trial}: one disposition version left more than one "
                "expiry row"
            )


# ---------------------------------------------------------------------------
# 4. D1 and D2, decided with a measurement
# ---------------------------------------------------------------------------


@requires_postgres
class TestD1TheConnectionIsHeldNotPooled:
    """D1 was only half decided at stage 1.

    Stage 1 removed the per-construction DDL, which was the expensive half. What
    it did not settle is whether a **pool** is needed on top: holding one
    connection for the life of the process, versus taking one per request from a
    pool. That is decided here by measuring what each option actually costs.

    The measurement is `connect + DDL` against `connect alone`, which is exactly
    the quantity a pool would and would not save. A pool saves the connect; it
    cannot save the DDL, and D1 already removed the DDL from the request path.
    """

    #: Samples per side. Five is enough to make the minimum stable on a local
    #: engine, where the whole difference is tens of milliseconds, and cheap on
    #: a remote one, where one sample already costs seconds.
    REPEATS = 5

    def test_the_ddl_is_the_expensive_half_and_d1_removes_it(self, engine: str) -> None:
        """Best of several samples, because the difference is what is measured.

        The first version compared one sample of each and asserted
        `connect_only < with_ddl`. That is a strict inequality between two
        timing samples whose whole separation on a local engine is tens of
        milliseconds, so connection noise decided it: it failed roughly one run
        in five locally while passing reliably on Supabase, where the DDL costs
        about a second. Taking the minimum of each over repeats keeps the
        systematic cost and discards the spread, and asserting a ratio rather
        than an ordering makes the margin explicit instead of incidental.
        """
        with_ddl: list[float] = []
        connect_only: list[float] = []
        for _ in range(self.REPEATS):
            PostgresEpisodeStore.forget_applied_schema(engine)
            started = time.monotonic()
            first = PostgresEpisodeStore(engine)
            with_ddl.append(time.monotonic() - started)

            started = time.monotonic()
            second = PostgresEpisodeStore(engine)
            connect_only.append(time.monotonic() - started)
            first.close()
            second.close()

        ddl_sample, connect_sample = min(with_ddl), min(connect_only)
        ratio = ddl_sample / connect_sample if connect_sample else float("inf")
        print(
            f"\n[D1] connect + DDL {ddl_sample:.3f}s, connect alone "
            f"{connect_sample:.3f}s, DDL therefore ~{ddl_sample - connect_sample:.3f}s, "
            f"ratio {ratio:.1f}x (best of {self.REPEATS})"
        )
        assert ratio > 1.2, (
            f"over {self.REPEATS} repeats the first store took {ddl_sample:.3f}s "
            f"and the second {connect_sample:.3f}s, a ratio of {ratio:.2f}x, so "
            "the DDL is not measurably the expensive half and D1 is not removing "
            "anything from the request path"
        )

    def test_one_statement_on_a_held_connection_is_cheap(self, engine: str) -> None:
        """The other half of the pool question.

        If a statement on an already-open connection were expensive, a pool would
        be worth having for throughput reasons. Measured here so the "hold one
        connection" decision rests on a number rather than on the fact that
        `psycopg_pool` is not installed, which is a weak reason on its own.
        """
        store = PostgresEpisodeStore(engine)
        try:
            started = time.monotonic()
            rounds = 20
            with store._conn.cursor() as cur:
                for _ in range(rounds):
                    cur.execute("SELECT 1")
            elapsed = time.monotonic() - started
            store._conn.rollback()
            per_statement = elapsed / rounds
            print(f"\n[D1] {per_statement * 1000:.0f} ms per statement, held connection")
            assert per_statement < 1.0, (
                f"a single statement took {per_statement:.2f}s on a held "
                "connection, which would make the pool question live rather than "
                "settled"
            )
        finally:
            store.close()


@requires_postgres
class TestD2TheLockTimeoutIsTunedNotInherited:
    """D2's default was inherited from SQLite's `busy_timeout` at stage 1.

    That number was chosen against a local engine where a statement costs
    microseconds. This is a managed instance across a network, and `lock_timeout`
    in Postgres is **per statement, not per transaction**, so the true ceiling on
    a blocked write is the number of statements that can block multiplied by the
    value. Both facts are measured here against a real contention rather than
    reasoned about.
    """

    def test_a_real_contention_raises_lock_contention_with_the_default(
        self, store, episode_id: str
    ) -> None:
        """The production default, against a lock another connection holds.

        The assertion is that the wait is **bounded** and that the failure is the
        typed `LockContention` a caller can handle, not a raw driver error and
        not a hang. The elapsed time is printed rather than asserted to a tight
        bound, because it is a network measurement and a tight bound would make
        this test flaky without making the product safer.
        """
        store.create_episode(episode_id, PERSONA, now_utc=NOW_UTC)
        store.register_policy_version(
            POLICY_VERSION,
            content="{}",
            provenance=POLICY_PROVENANCE,
            approved_by=None,
            now_utc=NOW_UTC,
        )
        store.insert_disposition(_disposition(episode_id), now_utc=NOW_UTC)
        consent_version = store.change_consent(
            episode_id, state.CLINICAL_SCOPE, granted=True, now_utc=NOW_UTC
        )
        command = AttemptCommand(episode_id, ROUTE_ID, PURPOSE_ID, consent_version)
        key = state.derive_attempt_key(episode_id, ROUTE_ID, PURPOSE_ID)
        attempt = store.open_attempt_once(command, key, now_utc=T_ATTEMPT)

        blocker = psycopg.connect(probe_dsn(), autocommit=False)
        try:
            with blocker.cursor() as bcur:
                bcur.execute(
                    "SELECT id FROM attempts WHERE id = %s FOR UPDATE",
                    (attempt.attempt_id,),
                )
            started = time.monotonic()
            with pytest.raises(state.LockContention):
                store.record_callback_once(
                    attempt.attempt_id,
                    "callback-under-contention",
                    CallbackResult(payload="{}", transition=ExecutionStatus.ACKNOWLEDGED),
                    Origin.LOCAL_SIM,
                    now_utc=T_CALLBACK,
                )
            elapsed = time.monotonic() - started
        finally:
            blocker.rollback()
            blocker.close()

        print(
            f"\n[D2] default lock_timeout={store.lock_timeout_s}s, a real "
            f"contention raised LockContention after {elapsed:.2f}s"
        )
        assert elapsed >= 1.0, (
            f"the write failed after {elapsed:.2f}s, which is too fast to be a "
            "lock wait, so this is not the branch under test"
        )
        assert elapsed < 30.0, (
            f"a blocked write took {elapsed:.2f}s, which is not a bounded wait"
        )

    def test_the_wait_scales_with_the_parameter(self, store, episode_id: str) -> None:
        """The control that the number is the knob, on the live engine.

        A half-second timeout must produce a wait well inside the default's, so
        the bound below is absolute rather than a comparison against the sibling
        test's measurement: the two tests do not share a run, and coupling them
        would make one flaky whenever the other is. Without this the test above
        would pass for any value of `lock_timeout_s`, including one that never
        reaches the statement at all.
        """
        store.create_episode(episode_id, PERSONA, now_utc=NOW_UTC)
        store.register_policy_version(
            POLICY_VERSION,
            content="{}",
            provenance=POLICY_PROVENANCE,
            approved_by=None,
            now_utc=NOW_UTC,
        )
        store.insert_disposition(_disposition(episode_id), now_utc=NOW_UTC)
        consent_version = store.change_consent(
            episode_id, state.CLINICAL_SCOPE, granted=True, now_utc=NOW_UTC
        )
        command = AttemptCommand(episode_id, ROUTE_ID, PURPOSE_ID, consent_version)
        key = state.derive_attempt_key(episode_id, ROUTE_ID, PURPOSE_ID)
        attempt = store.open_attempt_once(command, key, now_utc=T_ATTEMPT)

        blocker = psycopg.connect(probe_dsn(), autocommit=False)
        try:
            with blocker.cursor() as bcur:
                bcur.execute(
                    "SELECT id FROM attempts WHERE id = %s FOR UPDATE",
                    (attempt.attempt_id,),
                )
            quick = PostgresEpisodeStore(probe_dsn(), lock_timeout_s=0.5)
            try:
                started = time.monotonic()
                with pytest.raises(state.LockContention):
                    quick.record_callback_once(
                        attempt.attempt_id,
                        "callback-quick-timeout",
                        CallbackResult(
                            payload="{}", transition=ExecutionStatus.ACKNOWLEDGED
                        ),
                        Origin.LOCAL_SIM,
                        now_utc=T_CALLBACK,
                    )
                elapsed = time.monotonic() - started
            finally:
                quick.close()
        finally:
            blocker.rollback()
            blocker.close()

        print(f"\n[D2] lock_timeout=0.5s raised LockContention after {elapsed:.2f}s")
        assert elapsed < 5.0, (
            f"a 0.5s lock_timeout waited {elapsed:.2f}s, so the parameter is not "
            "reaching the statement"
        )


# ---------------------------------------------------------------------------
# What this module does not prove
# ---------------------------------------------------------------------------


class TestStatedLimits:
    """Kept as tests so the limits and the decisions cannot be quietly deleted."""

    def test_the_three_signature_divergences_are_recorded(self) -> None:
        """The parity test found three divergences. Their reasons must survive."""
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        for needle in (
            "a type no other engine has",
            "so Postgres was narrowed",
            "Both now return `ClosureProjection`",
        ):
            assert needle in source, (
                f"the reason for a signature divergence is gone from this module: {needle}"
            )

    def test_the_deployment_limit_is_stated(self) -> None:
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        assert "does not prove the deployment works" in source
        assert "pooler in transaction mode" in source

    def test_this_module_is_skipped_rather_than_green_without_postgres(self) -> None:
        """The skip stays per class. A module-level skip is what let two
        database-free guards go unrun at stage 1 (lesson 22)."""
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        assert "skipif" in source
        for needs_engine in (
            "class TestBothEnginesAnswerAlike",
            "class TestTheGuardsCameWithThePort",
            "class TestO1OnTheDispositionsTable",
            "class TestTwoWritersAtOneKey",
            "class TestD1TheConnectionIsHeldNotPooled",
            "class TestD2TheLockTimeoutIsTunedNotInherited",
        ):
            index = source.index(needs_engine)
            assert "@requires_postgres" in source[max(0, index - 40) : index], (
                f"{needs_engine} opens a connection but is not marked, so it "
                "would pass or fail without a stated reason"
            )
        for no_engine in (
            "class TestTheTwoStoresShareOneSurface",
            "class TestStatedLimits",
        ):
            index = source.index(no_engine)
            assert "@requires_postgres" not in source[max(0, index - 40) : index], (
                f"{no_engine} needs no database and would be skipped needlessly"
            )
