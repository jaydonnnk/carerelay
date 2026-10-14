"""Offline query-contract parity. These checks do not exercise a Postgres engine."""
from contextlib import contextmanager
from datetime import timedelta
from types import SimpleNamespace

import pytest

from carerelay.demo import fixture
from carerelay.postgres_store import PostgresEpisodeStore
from test_truthfulness import make_service


class SQLiteCursor:
    """Execute the portable Postgres SELECTs over the same seeded SQLite rows."""
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, args=()):
        self.cursor = self.connection.execute(query.replace("%s", "?"), args)
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        return [dict(row) for row in self.cursor.fetchall()]


@pytest.mark.parametrize("regression", [False, True])
@pytest.mark.parametrize("record", ["escalation", "acceptance", "restatement", "attempt"])
def test_event_order_survives_equal_or_regressed_clock(tmp_path, monkeypatch, regression, record):
    import carerelay.state as state
    from carerelay.domain.models import HintLevel
    service = make_service(tmp_path / "order.sqlite")
    episode = "event-order"
    service.ensure_episode(episode, "fictional")
    service.intake(episode, fixture.BOUND_COMPLAINT)
    service.change_consent(episode, granted=True)
    ids = iter(["z" * 32, "a" * 32])
    monkeypatch.setattr(state.uuid, "uuid4", lambda: SimpleNamespace(hex=next(ids)))
    first = fixture.SCENARIO_NOW_UTC
    second = first - timedelta(seconds=1) if regression else first
    store = service._store
    if record == "escalation":
        for outcome, now in [("handed_off", first), ("failed", second)]:
            store.record_escalation(episode, human_path="nurse_line", outcome=outcome, now_utc=now)
    elif record == "acceptance":
        for owner, now in [("caregiver", first), ("patient", second)]:
            store.record_human_acceptance(episode, accepted_by=owner, scope="handoff", now_utc=now)
    elif record == "attempt":
        from carerelay.domain.models import AttemptCommand
        for purpose, now in [("one", first), ("two", second)]:
            store.open_attempt_once(AttemptCommand(episode, "fictional_provider", purpose, 1), purpose, now_utc=now)
    else:
        from carerelay.service import ScenarioClock
        service._clock = ScenarioClock(first)
        service.submit_restatement(episode, "see the doctor today before 6pm myself", HintLevel.H1)
        service._clock = ScenarioClock(second)
        service.submit_restatement(episode, "see the doctor tomorrow before 6pm myself", HintLevel.H1)
    pg = PostgresEpisodeStore.__new__(PostgresEpisodeStore)
    @contextmanager
    def read():
        yield SQLiteCursor(store._conn)
    pg._read = read
    if record == "restatement":
        expected = store.list_restatements(episode)
        actual = pg.list_restatements(episode)
        assert [r.restatement_id for r in actual] == [r.restatement_id for r in expected] == ["z" * 32, "a" * 32]
    else:
        expected = store.load_snapshot(episode)
        actual = pg._load_snapshot(SQLiteCursor(store._conn), episode)
        field = {"escalation": "escalation_id", "acceptance": "human_acceptance_id", "attempt": "attempt"}[record]
        a, b = getattr(expected, field), getattr(actual, field)
        if record == "attempt": a, b = a.attempt_id, b.attempt_id
        assert a == b == "a" * 32
    store.close()


def test_postgres_mutex_exists_before_first_transaction(monkeypatch):
    import carerelay.postgres_store as module
    monkeypatch.setattr(module.psycopg, "connect", lambda *a, **k: object())
    monkeypatch.setattr(PostgresEpisodeStore, "init_schema", lambda self: None)
    store = PostgresEpisodeStore("postgresql://offline.invalid/test")
    assert hasattr(store, "_mutex")
    original = store._mutex
    assert original.acquire(blocking=False)
    original.release()
    assert store._mutex is original


def test_postgres_nested_writer_cannot_switch_episode():
    import threading
    from carerelay.state import StateError
    store = PostgresEpisodeStore.__new__(PostgresEpisodeStore)
    store._mutex = threading.RLock()
    store._journey_tx = SimpleNamespace(episode_id="episode-a")
    store._journey_write = True
    store._journey_cursor = object()
    with pytest.raises(StateError, match="episode"):
        with store._write("episode-b"):
            pass
