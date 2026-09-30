"""State layer tests. Slice 3: append-only record, Closure Contract invariants.

The five tests Gate 4 named for this slice are here under their approved names:

* `test_attempt_open_atomic_and_double_tap`
* `test_callback_duplicate_and_reorder`
* `test_consent_revoke_in_flight`
* `test_evidence_provenance_constraint`
* `test_expiry_sticky_after_clock_regression`

Three of the claims in this file are proven against a **separate raw SQLite
connection**, not through the module under test, because a guard exercised only
through its own callers proves nothing about the record:

* the append-only rule is a trigger in the schema, so raw `UPDATE` and `DELETE`
  statements are issued directly, and a control case drops the triggers to show
  the refusal comes from them;
* the D11 `CHECK` on `evidence` is issued directly, with a control table that is
  the same minus the `CHECK`;
* the two-writer callback race uses two real connections in two real threads,
  because a race proved in one connection is not a race.

`AGENTS.md` section 6: "a fault two checks can both catch is proof of neither".
Each guard below is disabled alone in its own test, and required to break exactly
its own assertion.
"""

from __future__ import annotations

import sqlite3
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay import state  # noqa: E402
from carerelay.domain import rules  # noqa: E402
from carerelay.domain.models import (  # noqa: E402
    AttemptCommand,
    CallbackResult,
    ClosureState,
    Disposition,
    DispositionSource,
    EvidenceLevel,
    EvidenceRecord,
    ExecutionStatus,
    Origin,
    PolicyText,
)

# ---------------------------------------------------------------------------
# Scenario values
# ---------------------------------------------------------------------------

EPISODE_ID = "episode-1"
PERSONA = "fictional older adult"
POLICY_VERSION = "fixture-provisional-0"
ACTION_ID = "attend_same_day_review"
NEXT_OWNER_ID = "patient"
FALLBACK_ROUTE_ID = "nurse_line"
ROUTE_ID = "nurse_line"
PURPOSE_ID = "booking"

# 12:00 Singapore on 1 October 2026.
NOW_UTC = datetime(2026, 10, 1, 4, 0, tzinfo=timezone.utc)
# 18:00 Singapore on 1 October 2026, the disposition's deadline.
DEADLINE_UTC = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
AFTER_DEADLINE_UTC = DEADLINE_UTC + timedelta(minutes=30)
# A clock that has gone backwards, past the deadline it had already passed.
BACKWARDS_CLOCK_UTC = NOW_UTC - timedelta(days=1)

POLICY_TEXT = PolicyText(
    policy_version=POLICY_VERSION,
    fixture_label="SIMULATED - RESEARCH DEMONSTRATION. Not clinical advice.",
    deadline_display_by_version={
        1: "6:00 PM on 1 October",
        2: "6:00 PM on 2 October",
    },
    self_owner_id=NEXT_OWNER_ID,
    owner_display_by_id={"patient": "you", "caregiver": "your daughter"},
    route_display_by_id={
        "nurse_line": "the fictional nurse line",
        "fictional_provider": "the fictional provider",
    },
    simulated=True,
)

DOCUMENTED_REAL = EvidenceRecord(
    level=EvidenceLevel.DOCUMENTED,
    simulated=False,
    provenance="fictional provider receipt",
    source_ref="receipt-0001",
)
DOCUMENTED_SIMULATED = EvidenceRecord(
    level=EvidenceLevel.DOCUMENTED,
    simulated=True,
    provenance="scripted local provider",
    source_ref="receipt-0002",
)
DOCUMENTED_UNSOURCED = EvidenceRecord(
    level=EvidenceLevel.DOCUMENTED,
    simulated=False,
    provenance="verbal",
    source_ref=None,
)


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


@dataclass
class Seeded:
    store: state.SqliteEpisodeStore
    consent_version: int

    @property
    def path(self) -> str:
        return self.store.path


def disposition(version: int = 1, *, day_offset: int = 0) -> Disposition:
    return Disposition(
        episode_id=EPISODE_ID,
        version=version,
        policy_version=POLICY_VERSION,
        action_id=ACTION_ID,
        clinical_deadline_utc=DEADLINE_UTC + timedelta(days=day_offset),
        next_owner_id=NEXT_OWNER_ID,
        fallback_route_id=FALLBACK_ROUTE_ID,
        source=(
            DispositionSource.FIXTURE
            if version == 1
            else DispositionSource.REASSESSMENT
        ),
    )


def seed(path: str | Path) -> Seeded:
    """One episode, one policy version, disposition v1 and granted consent v1."""
    store = state.SqliteEpisodeStore(path)
    store.create_episode(EPISODE_ID, PERSONA, now_utc=NOW_UTC)
    store.register_policy_version(
        POLICY_VERSION,
        content="{}",
        provenance="provisional placeholder pending the Option C source check",
        approved_by=None,
        now_utc=NOW_UTC,
    )
    store.insert_disposition(disposition(), now_utc=NOW_UTC)
    version = store.change_consent(
        EPISODE_ID, state.CLINICAL_SCOPE, granted=True, now_utc=NOW_UTC
    )
    return Seeded(store=store, consent_version=version)


def open_attempt(seeded: Seeded, *, purpose: str = PURPOSE_ID):
    command = AttemptCommand(EPISODE_ID, ROUTE_ID, purpose, seeded.consent_version)
    key = state.derive_attempt_key(EPISODE_ID, ROUTE_ID, purpose)
    return seeded.store.open_attempt_once(command, key, now_utc=NOW_UTC)


@pytest.fixture
def seeded(tmp_path: Path) -> Seeded:
    value = seed(tmp_path / "carerelay.sqlite3")
    yield value
    value.store.close()


def patient_lines(store: state.SqliteEpisodeStore, now_utc: datetime):
    snapshot = store.load_snapshot(EPISODE_ID)
    return rules.patient_lines(snapshot, rules.derive_closure(snapshot, now_utc), POLICY_TEXT)


def raw(path: str | Path) -> sqlite3.Connection:
    """A connection that knows nothing about this module's guards."""
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


# ---------------------------------------------------------------------------
# Append-only, proven against the schema rather than against the callers
# ---------------------------------------------------------------------------


def _one_row_per_table(path: str | Path) -> None:
    """Seed at least one row into every table, so a per-row trigger can fire.

    A `BEFORE UPDATE` trigger fires once per row. An `UPDATE ... WHERE 1=0` would
    therefore "succeed" against an empty table and prove nothing, which is why
    this helper exists rather than a bare statement.
    """
    seeded = seed(path)
    seeded.store.close()
    stamp = NOW_UTC.isoformat()
    rows: dict[str, tuple[str, tuple[object, ...]]] = {
        "episodes": (
            "INSERT OR IGNORE INTO episodes (id, persona, created_at) VALUES (?, ?, ?)",
            ("episode-raw", PERSONA, stamp),
        ),
        "policy_versions": (
            "INSERT OR IGNORE INTO policy_versions "
            "(version, content, provenance, approved_by, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("raw-policy-0", "{}", "placeholder", None, stamp),
        ),
        "dispositions": (
            "INSERT OR IGNORE INTO dispositions "
            "(episode_id, version_no, policy_version, action_id, "
            " clinical_deadline_utc, next_owner_id, fallback_route_id, source, "
            " created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                EPISODE_ID,
                1,
                POLICY_VERSION,
                ACTION_ID,
                DEADLINE_UTC.isoformat(),
                NEXT_OWNER_ID,
                FALLBACK_ROUTE_ID,
                "fixture",
                stamp,
            ),
        ),
        "attempts": (
            "INSERT OR IGNORE INTO attempts "
            "(id, episode_id, route_id, purpose_id, idempotency_key, "
            " consent_version, opened_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("attempt-raw", EPISODE_ID, ROUTE_ID, PURPOSE_ID, "key-raw", 1, stamp),
        ),
        "attempt_transitions": (
            "INSERT OR IGNORE INTO attempt_transitions "
            "(attempt_id, seq, transition, origin, payload, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("attempt-raw", 999, "superseded", "local-sim", "", stamp),
        ),
        "callbacks": (
            "INSERT OR IGNORE INTO callbacks "
            "(episode_id, route_id, attempt_id, callback_key, callback_key_digest, "
            " duplicate_of, accepted, rejection_reason, origin, result, payload, "
            " received_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                EPISODE_ID,
                ROUTE_ID,
                "attempt-raw",
                "cb-raw",
                "digest-raw",
                None,
                1,
                None,
                "platform",
                "acknowledged",
                "",
                stamp,
            ),
        ),
        "evidence": (
            "INSERT OR IGNORE INTO evidence "
            "(episode_id, level, simulated, provenance, source_ref, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (EPISODE_ID, "self_reported", 1, "placeholder", None, stamp),
        ),
        "consents": (
            "INSERT OR IGNORE INTO consents "
            "(episode_id, scope, state, version, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (EPISODE_ID, state.CLINICAL_SCOPE, "granted", 1, stamp),
        ),
        "human_acceptances": (
            "INSERT OR IGNORE INTO human_acceptances "
            "(id, episode_id, accepted_by, scope, recorded_at) VALUES (?, ?, ?, ?, ?)",
            ("acceptance-raw", EPISODE_ID, "fictional daughter", "handoff", stamp),
        ),
        "escalations": (
            "INSERT OR IGNORE INTO escalations "
            "(id, episode_id, human_path, outcome, recorded_at) VALUES (?, ?, ?, ?, ?)",
            ("escalation-raw", EPISODE_ID, "nurse_line", "handed_over", stamp),
        ),
        "expiry_events": (
            "INSERT OR IGNORE INTO expiry_events "
            "(id, episode_id, disposition_version, occurred_at) VALUES (?, ?, ?, ?)",
            ("expiry-raw", EPISODE_ID, 1, stamp),
        ),
        "restatements": (
            "INSERT OR IGNORE INTO restatements "
            "(id, episode_id, disposition_version, hint_level, input_mode, "
            " transcript_confirmed, extracted_json, mismatches, repair_round, "
            " outcome, dwell_seconds, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "restatement-raw",
                EPISODE_ID,
                1,
                "H0",
                "text",
                1,
                "{}",
                "[]",
                0,
                "recall_unaided",
                None,
                stamp,
            ),
        ),
        "events": (
            "INSERT OR IGNORE INTO events (episode_id, kind, payload, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            (EPISODE_ID, "raw_event", "", stamp),
        ),
    }
    assert set(rows) == set(state.APPEND_ONLY_TABLES), (
        "every append-only table needs a seed row, or its trigger test proves nothing"
    )
    connection = raw(path)
    try:
        for statement, parameters in rows.values():
            connection.execute(statement, parameters)
        connection.commit()
    finally:
        connection.close()


@pytest.fixture(scope="module")
def append_only_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("append-only") / "carerelay.sqlite3"
    _one_row_per_table(path)
    return path


class TestTheRecordIsAppendOnly:
    """D3. Proven by raw SQL, so this module's own guards are irrelevant."""

    def test_every_append_only_table_has_a_row_to_attack(self, append_only_db: Path) -> None:
        connection = raw(append_only_db)
        try:
            for table in state.APPEND_ONLY_TABLES:
                count = connection.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
                assert count >= 1, f"{table} has no row, so its trigger cannot fire"
        finally:
            connection.close()

    @pytest.mark.parametrize("table", state.APPEND_ONLY_TABLES)
    def test_every_table_refuses_update(self, append_only_db: Path, table: str) -> None:
        connection = raw(append_only_db)
        try:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"UPDATE {table} SET rowid = rowid")
        finally:
            connection.close()

    @pytest.mark.parametrize("table", state.APPEND_ONLY_TABLES)
    def test_every_table_refuses_delete(self, append_only_db: Path, table: str) -> None:
        connection = raw(append_only_db)
        try:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"DELETE FROM {table}")
        finally:
            connection.close()

    def test_the_refusal_comes_from_the_triggers(self, tmp_path: Path) -> None:
        """The control case. Drop the triggers and the same statements go through.

        Without this, `test_every_table_refuses_update` could be green for some
        unrelated reason and nobody would know.
        """
        path = tmp_path / "no-triggers.sqlite3"
        _one_row_per_table(path)
        connection = raw(path)
        try:
            connection.executescript(
                "DROP TRIGGER dispositions_no_update;"
                "DROP TRIGGER dispositions_no_delete;"
            )
            connection.execute("UPDATE dispositions SET action_id = 'tampered'")
            assert (
                connection.execute(
                    "SELECT action_id FROM dispositions WHERE episode_id = ?",
                    (EPISODE_ID,),
                ).fetchone()[0]
                == "tampered"
            )
            connection.execute("DELETE FROM dispositions")
            assert (
                connection.execute(
                    "SELECT COUNT(*) FROM dispositions WHERE episode_id = ?",
                    (EPISODE_ID,),
                ).fetchone()[0]
                == 0
            )
        finally:
            connection.close()


# ---------------------------------------------------------------------------
# Dispositions: the deadline invariant, at the layer that can break it
# ---------------------------------------------------------------------------


class TestDispositionsAreAppendOnly:
    def test_a_second_version_must_follow_the_first(self, seeded: Seeded) -> None:
        with pytest.raises(state.DispositionVersionConflict):
            seeded.store.insert_disposition(disposition(version=3), now_utc=NOW_UTC)
        assert [row.version for row in seeded.store.list_dispositions(EPISODE_ID)] == [1]

    def test_a_version_cannot_be_reinserted(self, seeded: Seeded) -> None:
        with pytest.raises(state.DispositionVersionConflict):
            seeded.store.insert_disposition(disposition(version=1), now_utc=NOW_UTC)
        assert len(seeded.store.list_dispositions(EPISODE_ID)) == 1

    def test_the_first_deadline_survives_a_second_version(self, seeded: Seeded) -> None:
        """I1. Reassessment appends; it does not move the original instant."""
        seeded.store.insert_disposition(
            disposition(version=2, day_offset=1), now_utc=NOW_UTC
        )
        versions = seeded.store.list_dispositions(EPISODE_ID)
        assert [row.version for row in versions] == [1, 2]
        assert versions[0].clinical_deadline_utc == DEADLINE_UTC

    def test_a_disposition_cannot_cite_an_unrecorded_policy_version(
        self, seeded: Seeded
    ) -> None:
        unrecorded = Disposition(
            episode_id=EPISODE_ID,
            version=2,
            policy_version="a-policy-that-was-never-recorded",
            action_id=ACTION_ID,
            clinical_deadline_utc=DEADLINE_UTC,
            next_owner_id=NEXT_OWNER_ID,
            fallback_route_id=FALLBACK_ROUTE_ID,
            source=DispositionSource.REASSESSMENT,
        )
        with pytest.raises(sqlite3.IntegrityError):
            seeded.store.insert_disposition(unrecorded, now_utc=NOW_UTC)

    def test_the_deadline_is_not_reachable_by_an_update(self, seeded: Seeded) -> None:
        """I1 holds because there is no update path, and here that is a trigger."""
        connection = raw(seeded.path)
        try:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(
                    "UPDATE dispositions SET clinical_deadline_utc = ?",
                    (BACKWARDS_CLOCK_UTC.isoformat(),),
                )
        finally:
            connection.close()
        assert (
            seeded.store.list_dispositions(EPISODE_ID)[0].clinical_deadline_utc
            == DEADLINE_UTC
        )


# ---------------------------------------------------------------------------
# Attempts
# ---------------------------------------------------------------------------


class TestAttemptOpenAtomicAndDoubleTap:
    def test_attempt_open_atomic_and_double_tap(self, seeded: Seeded) -> None:
        """Gate 4's named test. One attempt and one dispatch for one triple."""
        command = AttemptCommand(EPISODE_ID, ROUTE_ID, PURPOSE_ID, seeded.consent_version)
        key = state.derive_attempt_key(EPISODE_ID, ROUTE_ID, PURPOSE_ID)

        first = seeded.store.open_attempt_once(command, key, now_utc=NOW_UTC)
        second = seeded.store.open_attempt_once(command, key, now_utc=NOW_UTC)

        assert first.attempt_id == second.attempt_id
        assert len(seeded.store.list_attempts(EPISODE_ID)) == 1
        assert first.execution is ExecutionStatus.ATTEMPTED
        kinds = [kind for kind, _, _ in seeded.store.list_events(EPISODE_ID)]
        assert kinds.count("attempt_opened") == 1
        assert kinds.count("attempt_duplicate_suppressed") == 1

    def test_the_attempt_row_and_its_audit_row_commit_together(
        self, seeded: Seeded, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A crash between the two is not a representable state."""

        def crash(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("simulated crash between the attempt and its audit row")

        monkeypatch.setattr(state.SqliteEpisodeStore, "_append_event", crash)
        command = AttemptCommand(EPISODE_ID, ROUTE_ID, PURPOSE_ID, seeded.consent_version)
        key = state.derive_attempt_key(EPISODE_ID, ROUTE_ID, PURPOSE_ID)
        with pytest.raises(RuntimeError):
            seeded.store.open_attempt_once(command, key, now_utc=NOW_UTC)

        monkeypatch.undo()
        assert seeded.store.list_attempts(EPISODE_ID) == ()
        # The key is not poisoned: the same triple opens cleanly afterwards.
        attempt = seeded.store.open_attempt_once(command, key, now_utc=NOW_UTC)
        assert attempt.idempotency_key == key

    def test_one_key_cannot_serve_a_different_triple(self, seeded: Seeded) -> None:
        command = AttemptCommand(EPISODE_ID, ROUTE_ID, PURPOSE_ID, seeded.consent_version)
        key = state.derive_attempt_key(EPISODE_ID, ROUTE_ID, PURPOSE_ID)
        seeded.store.open_attempt_once(command, key, now_utc=NOW_UTC)

        other = AttemptCommand(
            EPISODE_ID, "fictional_provider", PURPOSE_ID, seeded.consent_version
        )
        with pytest.raises(state.IdempotencyKeyCollision):
            seeded.store.open_attempt_once(other, key, now_utc=NOW_UTC)

    def test_a_new_purpose_is_an_explicit_retry_not_a_double_tap(self, seeded: Seeded) -> None:
        first = open_attempt(seeded, purpose="booking")
        second = open_attempt(seeded, purpose="booking-retry")
        assert first.attempt_id != second.attempt_id
        assert len(seeded.store.list_attempts(EPISODE_ID)) == 2

    def test_opening_under_a_superseded_consent_is_refused(self, seeded: Seeded) -> None:
        seeded.store.change_consent(
            EPISODE_ID, state.CLINICAL_SCOPE, granted=False, now_utc=NOW_UTC
        )
        with pytest.raises(state.ConsentNotCurrent):
            open_attempt(seeded)

    def test_the_key_is_derived_from_the_triple(self) -> None:
        same = state.derive_attempt_key(EPISODE_ID, ROUTE_ID, PURPOSE_ID)
        assert same == state.derive_attempt_key(EPISODE_ID, ROUTE_ID, PURPOSE_ID)
        assert same != state.derive_attempt_key(EPISODE_ID, ROUTE_ID, "other-purpose")
        assert same != state.derive_attempt_key(EPISODE_ID, "other-route", PURPOSE_ID)
        assert same != state.derive_attempt_key("other-episode", ROUTE_ID, PURPOSE_ID)

    def test_the_key_derivation_is_not_fooled_by_a_shifted_boundary(self) -> None:
        """Plain concatenation would collide here. Length prefixes are why not."""
        assert state.derive_attempt_key("ab", "c", "d") != state.derive_attempt_key(
            "a", "bc", "d"
        )
        assert state.derive_attempt_key("a", "b", "cd") != state.derive_attempt_key(
            "a", "bc", "d"
        )


# ---------------------------------------------------------------------------
# Callbacks: the hardest item in this slice (R6)
# ---------------------------------------------------------------------------


class TestCallbackDuplicateAndReorder:
    def test_callback_duplicate_and_reorder(self, seeded: Seeded) -> None:
        """Gate 4's named test. Every receipt is auditable; only the first wins."""
        attempt = open_attempt(seeded)
        failure = CallbackResult(
            transition=ExecutionStatus.FAILED, payload="scripted provider timeout"
        )
        acknowledged = CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED)

        assert (
            seeded.store.record_callback_once(
                attempt.attempt_id, "cb-1", failure, Origin.PLATFORM, now_utc=NOW_UTC
            )
            is True
        )
        # The same key again, this time claiming success. A duplicate, and it
        # cannot reverse the failure.
        assert (
            seeded.store.record_callback_once(
                attempt.attempt_id, "cb-1", acknowledged, Origin.PLATFORM, now_utc=NOW_UTC
            )
            is False
        )
        # A different key arriving late, also claiming success. Recorded, and
        # non-winning because its `seq` is higher.
        assert (
            seeded.store.record_callback_once(
                attempt.attempt_id, "cb-2", acknowledged, Origin.PLATFORM, now_utc=NOW_UTC
            )
            is True
        )

        receipts = seeded.store.list_callbacks(EPISODE_ID)
        assert len(receipts) == 3
        assert [receipt.accepted for receipt in receipts] == [True, False, True]
        assert receipts[1].duplicate_of == receipts[0].receipt_id
        assert receipts[1].callback_key is None
        assert receipts[1].rejection_reason == "duplicate"
        assert receipts[1].callback_key_digest == receipts[0].callback_key_digest

        transitions = seeded.store.list_transitions(attempt.attempt_id)
        assert [row.kind for row in transitions] == [
            ExecutionStatus.FAILED,
            ExecutionStatus.ACKNOWLEDGED,
        ]
        assert [row.seq for row in transitions] == [1, 2]
        assert rules.project_attempt(transitions) is ExecutionStatus.FAILED
        assert (
            seeded.store.list_attempts(EPISODE_ID)[0].execution
            is ExecutionStatus.FAILED
        )

    def test_a_duplicate_makes_no_transition(self, seeded: Seeded) -> None:
        attempt = open_attempt(seeded)
        first = CallbackResult(transition=ExecutionStatus.FAILED)
        assert (
            seeded.store.record_callback_once(
                attempt.attempt_id, "cb-1", first, Origin.PLATFORM, now_utc=NOW_UTC
            )
            is True
        )
        before = seeded.store.list_transitions(attempt.attempt_id)
        seeded.store.record_callback_once(
            attempt.attempt_id, "cb-1", first, Origin.PLATFORM, now_utc=NOW_UTC
        )
        assert seeded.store.list_transitions(attempt.attempt_id) == before
        assert len(seeded.store.list_callbacks(EPISODE_ID)) == 2

    def test_the_origin_survives_to_the_transition(self, seeded: Seeded) -> None:
        """A platform failure and a local simulation must be distinguishable."""
        attempt = open_attempt(seeded)
        seeded.store.record_callback_once(
            attempt.attempt_id,
            "cb-sim",
            CallbackResult(transition=ExecutionStatus.FAILED),
            Origin.LOCAL_SIM,
            now_utc=NOW_UTC,
        )
        transitions = seeded.store.list_transitions(attempt.attempt_id)
        assert transitions[0].origin is Origin.LOCAL_SIM

    def test_a_non_terminal_transition_is_refused(self, seeded: Seeded) -> None:
        attempt = open_attempt(seeded)
        with pytest.raises(rules.UnpermittedTransition):
            seeded.store.record_callback_once(
                attempt.attempt_id,
                "cb-bad",
                CallbackResult(transition=ExecutionStatus.ATTEMPTED),
                Origin.PLATFORM,
                now_utc=NOW_UTC,
            )
        assert seeded.store.list_callbacks(EPISODE_ID) == ()

    def test_a_failed_write_leaves_no_receipt_and_no_transition(
        self, seeded: Seeded, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        attempt = open_attempt(seeded)

        def crash(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("simulated crash between the receipt and its transition")

        monkeypatch.setattr(state.SqliteEpisodeStore, "_append_transition", crash)
        with pytest.raises(RuntimeError):
            seeded.store.record_callback_once(
                attempt.attempt_id,
                "cb-1",
                CallbackResult(transition=ExecutionStatus.FAILED),
                Origin.PLATFORM,
                now_utc=NOW_UTC,
            )
        monkeypatch.undo()
        assert seeded.store.list_callbacks(EPISODE_ID) == ()
        assert seeded.store.list_transitions(attempt.attempt_id) == ()

    def test_two_concurrent_writers_record_one_winning_receipt(self, seeded: Seeded) -> None:
        """R6, the acknowledged hypothesis. Two connections, two threads, one key.

        Without `BEGIN IMMEDIATE` plus the busy timeout, both writers read "no
        such key" and one receipt is lost. The assertion is not "no error": it is
        that exactly one receipt was applied and the other was recorded as a
        duplicate of it.
        """
        attempt = open_attempt(seeded)
        path = seeded.path
        barrier = threading.Barrier(2)
        outcomes: list[object] = []

        def writer() -> None:
            store = state.SqliteEpisodeStore(path)
            try:
                barrier.wait(timeout=10)
                outcomes.append(
                    store.record_callback_once(
                        attempt.attempt_id,
                        "cb-race",
                        CallbackResult(transition=ExecutionStatus.FAILED),
                        Origin.PLATFORM,
                        now_utc=NOW_UTC,
                    )
                )
            except BaseException as exc:  # noqa: BLE001 - reported, not swallowed
                outcomes.append(exc)
            finally:
                store.close()

        threads = [threading.Thread(target=writer) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        assert sorted(outcomes, key=str) == [False, True], outcomes
        receipts = seeded.store.list_callbacks(EPISODE_ID)
        assert len(receipts) == 2
        accepted = [receipt for receipt in receipts if receipt.accepted]
        duplicates = [receipt for receipt in receipts if not receipt.accepted]
        assert len(accepted) == 1
        assert len(duplicates) == 1
        assert duplicates[0].rejection_reason == "duplicate"
        assert duplicates[0].duplicate_of == accepted[0].receipt_id
        assert len(seeded.store.list_transitions(attempt.attempt_id)) == 1

    def test_an_unknown_attempt_is_refused(self, seeded: Seeded) -> None:
        with pytest.raises(state.AttemptNotFound):
            seeded.store.record_callback_once(
                "attempt-that-does-not-exist",
                "cb-1",
                CallbackResult(transition=ExecutionStatus.FAILED),
                Origin.PLATFORM,
                now_utc=NOW_UTC,
            )


# ---------------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------------


class TestConsentRevokeInFlight:
    def test_consent_revoke_in_flight(self, seeded: Seeded) -> None:
        """Gate 4's named test. Revocation blocks the success, visibly."""
        attempt = open_attempt(seeded)
        revoked_version = seeded.store.change_consent(
            EPISODE_ID, state.CLINICAL_SCOPE, granted=False, now_utc=NOW_UTC
        )
        assert revoked_version == seeded.consent_version + 1

        applied = seeded.store.record_callback_once(
            attempt.attempt_id,
            "cb-1",
            CallbackResult(
                transition=ExecutionStatus.ACKNOWLEDGED, evidence=DOCUMENTED_REAL
            ),
            Origin.PLATFORM,
            now_utc=NOW_UTC,
        )

        assert applied is False
        receipts = seeded.store.list_callbacks(EPISODE_ID)
        assert len(receipts) == 1, "a refused receipt is still recorded"
        assert receipts[0].accepted is False
        assert "revoked" in (receipts[0].rejection_reason or "")
        assert seeded.store.list_transitions(attempt.attempt_id) == ()
        assert seeded.store.list_evidence(EPISODE_ID) == ()
        assert seeded.store.list_attempts(EPISODE_ID)[0].execution is (
            ExecutionStatus.ATTEMPTED
        )
        assert seeded.store.derive_closure(EPISODE_ID, NOW_UTC).care_evidenced is False

    def test_a_changed_consent_version_also_blocks(self, seeded: Seeded) -> None:
        """Re-granted is not the same as unchanged: the stamp no longer matches."""
        attempt = open_attempt(seeded)
        seeded.store.change_consent(
            EPISODE_ID, state.CLINICAL_SCOPE, granted=False, now_utc=NOW_UTC
        )
        seeded.store.change_consent(
            EPISODE_ID, state.CLINICAL_SCOPE, granted=True, now_utc=NOW_UTC
        )
        assert (
            seeded.store.record_callback_once(
                attempt.attempt_id,
                "cb-1",
                CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED),
                Origin.PLATFORM,
                now_utc=NOW_UTC,
            )
            is False
        )
        reason = seeded.store.list_callbacks(EPISODE_ID)[0].rejection_reason or ""
        assert "changed from 1 to 3" in reason

    def test_standalone_evidence_recording_is_refused_after_revocation(
        self, seeded: Seeded
    ) -> None:
        seeded.store.change_consent(
            EPISODE_ID, state.CLINICAL_SCOPE, granted=False, now_utc=NOW_UTC
        )
        with pytest.raises(state.ConsentNotCurrent):
            seeded.store.record_evidence(EPISODE_ID, DOCUMENTED_REAL, now_utc=NOW_UTC)
        assert seeded.store.list_evidence(EPISODE_ID) == ()

    def test_an_episode_with_no_consent_records_nothing_as_success(self, tmp_path: Path) -> None:
        path = tmp_path / "no-consent.sqlite3"
        store = state.SqliteEpisodeStore(path)
        try:
            store.create_episode(EPISODE_ID, PERSONA, now_utc=NOW_UTC)
            store.register_policy_version(
                POLICY_VERSION,
                content="{}",
                provenance="placeholder",
                approved_by=None,
                now_utc=NOW_UTC,
            )
            store.insert_disposition(disposition(), now_utc=NOW_UTC)
            with pytest.raises(state.ConsentNotCurrent):
                store.open_attempt_once(
                    AttemptCommand(EPISODE_ID, ROUTE_ID, PURPOSE_ID, 1),
                    state.derive_attempt_key(EPISODE_ID, ROUTE_ID, PURPOSE_ID),
                    now_utc=NOW_UTC,
                )
            assert store.load_snapshot(EPISODE_ID).consent_version is None
        finally:
            store.close()


# ---------------------------------------------------------------------------
# Evidence provenance (D11)
# ---------------------------------------------------------------------------


class TestEvidenceProvenanceConstraint:
    def test_evidence_provenance_constraint(self, seeded: Seeded) -> None:
        """Gate 4's named test. A scripted 200 cannot close care."""
        with pytest.raises(state.EvidenceProvenanceViolation):
            seeded.store.record_evidence(EPISODE_ID, DOCUMENTED_SIMULATED, now_utc=NOW_UTC)
        with pytest.raises(state.EvidenceProvenanceViolation):
            seeded.store.record_evidence(EPISODE_ID, DOCUMENTED_UNSOURCED, now_utc=NOW_UTC)
        assert seeded.store.list_evidence(EPISODE_ID) == ()

        seeded.store.record_evidence(EPISODE_ID, DOCUMENTED_REAL, now_utc=NOW_UTC)
        assert seeded.store.derive_closure(EPISODE_ID, NOW_UTC).care_evidenced is True

    def test_the_database_check_is_independent_of_the_python_guard(
        self, seeded: Seeded
    ) -> None:
        """Raw SQL, straight past `record_evidence`. The `CHECK` still refuses."""
        connection = raw(seeded.path)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO evidence "
                    "(episode_id, level, simulated, provenance, source_ref, "
                    " recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        EPISODE_ID,
                        "documented",
                        1,
                        "scripted local provider",
                        "receipt-0002",
                        NOW_UTC.isoformat(),
                    ),
                )
            connection.rollback()
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO evidence "
                    "(episode_id, level, simulated, provenance, source_ref, "
                    " recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (EPISODE_ID, "documented", 0, "verbal", None, NOW_UTC.isoformat()),
                )
        finally:
            connection.close()

    def test_the_check_is_what_refuses_the_row(self, seeded: Seeded) -> None:
        """The control case: the same table without the `CHECK` accepts the row.

        Without this, the refusal above could come from a column type, a trigger
        or anything else, and the `CHECK` would be unproven.
        """
        connection = raw(seeded.path)
        try:
            connection.execute(
                "CREATE TABLE evidence_control ("
                " id INTEGER PRIMARY KEY,"
                " episode_id TEXT NOT NULL,"
                " level TEXT NOT NULL,"
                " simulated INTEGER NOT NULL,"
                " provenance TEXT NOT NULL,"
                " source_ref TEXT,"
                " recorded_at TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT INTO evidence_control "
                "(episode_id, level, simulated, provenance, source_ref, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    EPISODE_ID,
                    "documented",
                    1,
                    "scripted local provider",
                    "receipt-0002",
                    NOW_UTC.isoformat(),
                ),
            )
            assert (
                connection.execute("SELECT COUNT(*) FROM evidence_control").fetchone()[0]
                == 1
            )
            assert (
                connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 0
            )
        finally:
            connection.close()

    def test_a_self_reported_row_is_never_upgraded(self, seeded: Seeded) -> None:
        seeded.store.record_evidence(
            EPISODE_ID,
            EvidenceRecord(
                level=EvidenceLevel.SELF_REPORTED,
                simulated=True,
                provenance="patient said so",
                source_ref=None,
            ),
            now_utc=NOW_UTC,
        )
        projection = seeded.store.derive_closure(EPISODE_ID, NOW_UTC)
        assert projection.evidence is EvidenceLevel.SELF_REPORTED
        assert projection.care_evidenced is False
        assert projection.simulated is True


# ---------------------------------------------------------------------------
# Expiry (D12)
# ---------------------------------------------------------------------------


class TestExpiryStickyAfterClockRegression:
    def test_expiry_sticky_after_clock_regression(self, seeded: Seeded) -> None:
        """Gate 4's named test. A backwards clock cannot reopen a disposition."""
        # An attempt that recorded no terminal outcome, so the execution axis has
        # something to move: attempted plus a passed deadline is `expired`.
        open_attempt(seeded)
        assert (
            seeded.store.record_expiry_once(EPISODE_ID, 1, AFTER_DEADLINE_UTC) is True
        )
        assert seeded.store.derive_closure(EPISODE_ID, AFTER_DEADLINE_UTC).closure is (
            ClosureState.EXPIRED_UNRESOLVED
        )

        # The clock goes backwards, to before the deadline it had already passed.
        assert (
            seeded.store.record_expiry_once(EPISODE_ID, 1, BACKWARDS_CLOCK_UTC) is False
        )
        after = seeded.store.derive_closure(EPISODE_ID, BACKWARDS_CLOCK_UTC)
        assert after.closure is ClosureState.EXPIRED_UNRESOLVED
        assert after.execution is ExecutionStatus.EXPIRED
        assert after.action_owner_id == NEXT_OWNER_ID
        assert len(seeded.store.list_expiry_events(EPISODE_ID)) == 1

    def test_expiry_before_the_deadline_is_refused(self, seeded: Seeded) -> None:
        """A premature expiry tells a patient their window is gone when it is not."""
        with pytest.raises(state.PrematureExpiry):
            seeded.store.record_expiry_once(EPISODE_ID, 1, NOW_UTC)
        assert seeded.store.list_expiry_events(EPISODE_ID) == ()
        assert seeded.store.derive_closure(EPISODE_ID, NOW_UTC).closure is ClosureState.OPEN

    def test_expiry_without_a_disposition_is_refused(self, seeded: Seeded) -> None:
        with pytest.raises(state.NoDispositionForExpiry):
            seeded.store.record_expiry_once(EPISODE_ID, 7, AFTER_DEADLINE_UTC)

    def test_a_naive_timestamp_is_refused_rather_than_guessed(self, seeded: Seeded) -> None:
        with pytest.raises(state.StateError, match="timezone-aware"):
            seeded.store.record_expiry_once(
                EPISODE_ID, 1, datetime(2026, 10, 1, 10, 30)
            )

    def test_a_new_version_gets_its_own_expiry_and_the_old_row_survives(
        self, seeded: Seeded
    ) -> None:
        """The reading: an expiry event names a version, so a new version is new.

        The earlier event is not deleted and not rewritten. It simply stops being
        the current plan's expiry, because the current plan has a later deadline.
        """
        seeded.store.record_expiry_once(EPISODE_ID, 1, AFTER_DEADLINE_UTC)
        seeded.store.insert_disposition(
            disposition(version=2, day_offset=1), now_utc=AFTER_DEADLINE_UTC
        )
        snapshot = seeded.store.load_snapshot(EPISODE_ID)
        assert snapshot.disposition is not None
        assert snapshot.disposition.version == 2
        assert snapshot.expiry_event_id is None
        assert [version for version, _ in seeded.store.list_expiry_events(EPISODE_ID)] == [1]

        later = AFTER_DEADLINE_UTC + timedelta(days=1, minutes=5)
        assert seeded.store.record_expiry_once(EPISODE_ID, 2, later) is True
        assert seeded.store.derive_closure(EPISODE_ID, later).closure is (
            ClosureState.EXPIRED_UNRESOLVED
        )
        assert [version for version, _ in seeded.store.list_expiry_events(EPISODE_ID)] == [
            1,
            2,
        ]

    def test_expiry_is_written_once_under_two_writers(self, seeded: Seeded) -> None:
        path = seeded.path
        barrier = threading.Barrier(2)
        outcomes: list[object] = []

        def writer() -> None:
            store = state.SqliteEpisodeStore(path)
            try:
                barrier.wait(timeout=10)
                outcomes.append(
                    store.record_expiry_once(EPISODE_ID, 1, AFTER_DEADLINE_UTC)
                )
            except BaseException as exc:  # noqa: BLE001 - reported, not swallowed
                outcomes.append(exc)
            finally:
                store.close()

        threads = [threading.Thread(target=writer) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        assert sorted(outcomes, key=str) == [False, True], outcomes
        assert len(seeded.store.list_expiry_events(EPISODE_ID)) == 1


# ---------------------------------------------------------------------------
# Snapshot, restart, and the two-axis read path
# ---------------------------------------------------------------------------


class TestSnapshotAndRestart:
    def test_the_record_survives_a_reopen(self, seeded: Seeded) -> None:
        attempt = open_attempt(seeded)
        seeded.store.record_callback_once(
            attempt.attempt_id,
            "cb-1",
            CallbackResult(transition=ExecutionStatus.FAILED),
            Origin.PLATFORM,
            now_utc=NOW_UTC,
        )
        before = seeded.store.load_snapshot(EPISODE_ID)
        seeded.store.close()

        reopened = state.SqliteEpisodeStore(seeded.path)
        try:
            after = reopened.load_snapshot(EPISODE_ID)
            assert after == before
            assert after.attempt is not None
            assert after.attempt.execution is ExecutionStatus.FAILED
            assert after.consent_version == seeded.consent_version
        finally:
            reopened.close()

    def test_a_duplicate_callback_leaves_the_patient_projection_unchanged(
        self, seeded: Seeded
    ) -> None:
        """This slice's exit check: the duplicate is recorded, the screen is not."""
        attempt = open_attempt(seeded)
        before = patient_lines(seeded.store, NOW_UTC)

        seeded.store.record_callback_once(
            attempt.attempt_id,
            "cb-1",
            CallbackResult(transition=ExecutionStatus.FAILED),
            Origin.PLATFORM,
            now_utc=NOW_UTC,
        )
        after_first = patient_lines(seeded.store, NOW_UTC)

        seeded.store.record_callback_once(
            attempt.attempt_id,
            "cb-1",
            CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED),
            Origin.PLATFORM,
            now_utc=NOW_UTC,
        )
        after_duplicate = patient_lines(seeded.store, NOW_UTC)

        assert before == after_first == after_duplicate
        assert len(seeded.store.list_callbacks(EPISODE_ID)) == 2
        assert seeded.store.list_callbacks(EPISODE_ID)[1].rejection_reason == "duplicate"

    def test_the_expired_rendering_is_reachable_through_the_store(self, seeded: Seeded) -> None:
        seeded.store.record_expiry_once(EPISODE_ID, 1, AFTER_DEADLINE_UTC)
        lines = patient_lines(seeded.store, AFTER_DEADLINE_UTC)
        assert lines[0] == "Help still is not arranged."
        assert "6:00 PM on 1 October" in lines[2]
        assert lines[3].startswith("Call the fictional nurse line")

    def test_the_latest_attempt_is_the_one_projected(self, seeded: Seeded) -> None:
        first = open_attempt(seeded, purpose="booking")
        seeded.store.record_callback_once(
            first.attempt_id,
            "cb-1",
            CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED),
            Origin.PLATFORM,
            now_utc=NOW_UTC,
        )
        second = open_attempt(seeded, purpose="booking-retry")
        snapshot = seeded.store.load_snapshot(EPISODE_ID)
        assert snapshot.attempt is not None
        assert snapshot.attempt.attempt_id == second.attempt_id
        assert snapshot.attempt.execution is ExecutionStatus.ATTEMPTED

    def test_an_acceptance_closes_the_handoff_without_becoming_evidence(
        self, seeded: Seeded
    ) -> None:
        acceptance_id = seeded.store.record_human_acceptance(
            EPISODE_ID,
            accepted_by="fictional daughter",
            scope="handoff",
            now_utc=NOW_UTC,
        )
        snapshot = seeded.store.load_snapshot(EPISODE_ID)
        assert snapshot.human_acceptance_id == acceptance_id
        projection = rules.derive_closure(snapshot, NOW_UTC)
        assert projection.closure is ClosureState.CLOSED_WITH_EVIDENCE
        assert projection.care_evidenced is False
        assert projection.simulated is True
        assert seeded.store.list_evidence(EPISODE_ID) == ()

    def test_an_escalation_reaches_the_snapshot(self, seeded: Seeded) -> None:
        escalation_id = seeded.store.record_escalation(
            EPISODE_ID,
            human_path="nurse_line",
            outcome="handed_over",
            now_utc=NOW_UTC,
        )
        snapshot = seeded.store.load_snapshot(EPISODE_ID)
        assert snapshot.escalation_id == escalation_id
        assert rules.derive_closure(snapshot, NOW_UTC).closure is (
            ClosureState.ESCALATED_TO_HUMAN
        )

    def test_an_unknown_episode_is_refused(self, seeded: Seeded) -> None:
        with pytest.raises(state.EpisodeNotFound):
            seeded.store.load_snapshot("episode-that-does-not-exist")

    def test_a_read_does_not_change_the_record(self, seeded: Seeded) -> None:
        """Reads are not writes. The expiry event is written by the caller, not here."""
        open_attempt(seeded)
        before = seeded.store.list_events(EPISODE_ID)
        seeded.store.load_snapshot(EPISODE_ID)
        seeded.store.derive_closure(EPISODE_ID, AFTER_DEADLINE_UTC)
        assert seeded.store.list_events(EPISODE_ID) == before
