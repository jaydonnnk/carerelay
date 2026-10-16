"""Slice 24: the durable reservation guard (Gate 3 section 11.8, checks G1 to G20).

Every store here is a disposable SQLite file under pytest's tmp_path. No test opens
`APP_DATABASE_URL`, and nothing here can reach the network: HTTPSConnection is a double.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import carerelay.adp_extraction as adp
from carerelay import adp_guard
from carerelay.adp_guard import GuardCeilings, GuardRefused, LiveGuard, build_guard, parse_ceilings
from carerelay.state import SqliteEpisodeStore
from test_adp_extraction import (LIVE_CONVERSATION, LIVE_DONE, LIVE_REQUEST, https_transport,
                                 live_profile_events, live_request, wire)

NOW = datetime(2026, 10, 16, 4, 0, tzinfo=timezone.utc)  # 12:00 Singapore
STAMP = NOW.isoformat()
CEILINGS = GuardCeilings(per_episode=5, per_day=100, total=300)
ENDPOINT = "https://wss.lke.tencentcloud.com/adp/v2/chat"


def make_store(path: Path, episodes=("ep-1",)) -> SqliteEpisodeStore:
    store = SqliteEpisodeStore(path)
    for episode in episodes:
        store.create_episode(episode, "fictional", now_utc=NOW)
    return store


def claim(path: Path, operation_id: str, episode_id: str = "ep-1", kind: str = "score_words") -> None:
    """A pending scoring claim, as `score_confirmed` writes before any extraction."""
    conn = sqlite3.connect(path)
    conn.execute("INSERT INTO journey_commands (operation_id, phase, episode_id, expected_revision, claim_revision, "
                 "kind, purpose, body_sha256, scored, recorded_at) VALUES (?, 'claimed', ?, 0, 0, ?, 'p', ?, 0, ?)",
                 (operation_id, episode_id, kind, "a" * 64, STAMP))
    conn.commit()
    conn.close()


def rows(path: Path, sql: str):
    conn = sqlite3.connect(path)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def rid(n: int) -> str:
    return f"{n:032x}"


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "guard.sqlite"
    store = make_store(path, episodes=("ep-1", "ep-2"))
    yield path, store
    store.close()


def guard_for(store, ceilings=CEILINGS, now=NOW):
    return LiveGuard(store, ceilings, now=lambda: now)


def spend(path, guard, n, *, operation_prefix="op", episode="ep-1", outcome="valid", start=1):
    for i in range(start, start + n):
        claim(path, f"{operation_prefix}-{i}", episode)
        ticket = guard.reserve(rid(i), f"{operation_prefix}-{i}")
        ticket.begin_send()
        guard.finish(ticket, outcome, None)


# -- live extractor with a real guard, offline socket ---------------------------

def guarded_live(monkeypatch, store, path, *, operation="fictional-correlation", ceilings=CEILINGS, **options):
    identities = iter((LIVE_REQUEST, LIVE_CONVERSATION, "c" * 32))
    monkeypatch.setattr(adp, "uuid4", lambda: SimpleNamespace(hex=next(identities)))
    transport, calls = https_transport(monkeypatch, chunks=(wire(live_profile_events()) + LIVE_DONE,), **options)
    transport.guard = guard_for(store, ceilings)
    extractor = adp.AdpReadbackExtractor(transport=transport, profile=adp.LIVE_PROFILE, endpoint=ENDPOINT,
                                         app_key="test-key", enabled=True, monotonic=lambda: 10.0)
    if operation is not None:
        claim(path, operation)
    return extractor, calls, transport.guard


def connects(calls):
    return [call for call in calls if call[0] == "connect"]


def test_g1_reservation_is_committed_before_the_payload_is_sent(monkeypatch, db):
    path, store = db
    seen = []

    def after_request():
        # A second connection sees the committed row, with no outcome yet, while the request is out.
        seen.append(rows(path, "SELECT r.number, o.outcome FROM adp_reservations r "
                               "LEFT JOIN adp_reservation_outcomes o USING (number)"))

    extractor, calls, _ = guarded_live(monkeypatch, store, path, after_request=after_request)
    result = extractor.extract(live_request())
    assert result.validation == "valid"
    assert seen == [[(1, None)]]
    assert rows(path, "SELECT number, outcome FROM adp_reservation_outcomes") == [(1, "valid")]
    assert rows(path, "SELECT request_id, operation_id, episode_id FROM adp_reservations") == [
        (LIVE_REQUEST, "fictional-correlation", "ep-1")]


def test_transport_refuses_to_open_without_a_ticket(monkeypatch, db):
    path, store = db
    transport, calls = https_transport(monkeypatch)
    transport.guard = guard_for(store)
    with pytest.raises(GuardRefused):
        transport.open(ENDPOINT, {"RequestId": LIVE_REQUEST}, deadline_monotonic=15, allow_redirects=False)
    assert connects(calls) == []


def test_g2_halt_refuses_with_zero_connection_attempts(monkeypatch, db):
    path, store = db
    claim(path, "earlier")
    earlier = guard_for(store).reserve(rid(9), "earlier")
    earlier.begin_send()
    guard_for(store).finish(earlier, "timeout", "whole_response_budget")
    before = rows(path, "SELECT count(*) FROM adp_reservations")
    extractor, calls, _ = guarded_live(monkeypatch, store, path)
    result = extractor.extract(live_request())
    assert (result.validation, result.failure_category) == ("not_sent", "guard_halted")
    assert connects(calls) == [] and rows(path, "SELECT count(*) FROM adp_reservations") == before


def test_clear_halt_reopens_sends(db):
    path, store = db
    guard = guard_for(store)
    spend(path, guard, 1, outcome="invalid")
    claim(path, "after")
    with pytest.raises(GuardRefused, match="guard_halted"):
        guard.reserve(rid(50), "after")
    guard.clear_halt("operator reviewed the invalid reply")
    assert guard.reserve(rid(50), "after").number == 2


def test_g3_unfinished_reservation_refuses(db):
    path, store = db
    guard = guard_for(store)
    claim(path, "first")
    guard.reserve(rid(1), "first")
    claim(path, "second")
    with pytest.raises(GuardRefused, match="guard_unfinished"):
        guard.reserve(rid(2), "second")


def test_g4_episode_ceiling(db):
    path, store = db
    guard = guard_for(store, GuardCeilings(2, 100, 300))
    spend(path, guard, 2)
    claim(path, "op-3")
    with pytest.raises(GuardRefused, match="guard_episode_ceiling"):
        guard.reserve(rid(3), "op-3")
    spend(path, guard, 1, operation_prefix="other", episode="ep-2", start=4)


def test_g5_day_ceiling_reopens_on_the_next_singapore_day(db):
    path, store = db
    guard = guard_for(store, GuardCeilings(100, 2, 300))
    spend(path, guard, 2)
    claim(path, "op-3")
    with pytest.raises(GuardRefused, match="guard_day_ceiling"):
        guard.reserve(rid(3), "op-3")
    # 16:00 UTC on the 16th is 00:00 on the 17th in Singapore.
    tomorrow = guard_for(store, GuardCeilings(100, 2, 300), now=datetime(2026, 10, 16, 16, 0, tzinfo=timezone.utc))
    assert tomorrow.reserve(rid(3), "op-3").number == 3
    assert rows(path, "SELECT sgt_day FROM adp_reservations ORDER BY number") == [
        ("2026-10-16",), ("2026-10-16",), ("2026-10-17",)]


def test_g6_total_ceiling(db):
    path, store = db
    guard = guard_for(store, GuardCeilings(100, 100, 3))
    spend(path, guard, 2)
    spend(path, guard, 1, operation_prefix="other", episode="ep-2", start=3)
    claim(path, "op-4", "ep-2")
    with pytest.raises(GuardRefused, match="guard_total_ceiling"):
        guard.reserve(rid(4), "op-4")


def test_g7_two_writers_released_together_never_exceed_one(tmp_path):
    path = tmp_path / "race.sqlite"
    make_store(path).close()
    claim(path, "a")
    claim(path, "b")
    barrier = threading.Barrier(2)
    outcomes = {}

    def writer(name):
        store = SqliteEpisodeStore(path)
        try:
            guard = guard_for(store)
            barrier.wait()
            try:
                outcomes[name] = guard.reserve(rid(1 if name == "a" else 2), name).number
            except GuardRefused as refused:
                outcomes[name] = refused.reason
            except Exception as exc:  # noqa: BLE001 - recorded, then asserted absent
                outcomes[name] = type(exc).__name__
        finally:
            store.close()

    threads = [threading.Thread(target=writer, args=(name,)) for name in "ab"]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(map(str, outcomes.values())) == ["1", "guard_unfinished"], outcomes
    assert rows(path, "SELECT count(*) FROM adp_reservations") == [(1,)]


@pytest.mark.parametrize("validation", ["invalid", "timeout", "transport"])
def test_g8_failures_count_and_halt(db, validation):
    path, store = db
    guard = guard_for(store)
    spend(path, guard, 1, outcome=validation)
    assert rows(path, "SELECT kind, number FROM adp_guard_controls") == [("halt", 1)]
    assert guard.status()["halted"] is True and guard.status()["total"] == 1


def test_g8_lost_counts_and_halts(db):
    path, store = db
    guard = guard_for(store)
    claim(path, "op-1")
    guard.reserve(rid(1), "op-1")
    guard.mark_lost(1, "worker restarted mid-call")
    assert rows(path, "SELECT outcome FROM adp_reservation_outcomes") == [("lost",)]
    assert guard.status()["halted"] is True


@pytest.mark.parametrize("validation", ["valid", "refused"])
def test_g9_valid_and_refusal_do_not_halt(db, validation):
    path, store = db
    guard = guard_for(store)
    spend(path, guard, 1, outcome=validation)
    assert rows(path, "SELECT count(*) FROM adp_guard_controls") == [(0,)]


def test_g10_every_extraction_path_finishes_its_row_once(monkeypatch, db):
    path, store = db
    extractor, calls, guard = guarded_live(monkeypatch, store, path, fail=ConnectionError)
    result = extractor.extract(live_request())
    assert result.validation == "transport"
    assert rows(path, "SELECT number, outcome FROM adp_reservation_outcomes") == [(1, "transport")]
    assert guard.status()["unfinished"] == [] and guard.status()["halted"] is True


def test_g10_a_finished_ticket_cannot_be_finished_twice(db):
    path, store = db
    guard = guard_for(store)
    claim(path, "op-1")
    ticket = guard.reserve(rid(1), "op-1")
    ticket.begin_send()
    guard.finish(ticket, "valid", None)
    with pytest.raises(sqlite3.IntegrityError):
        guard.finish(ticket, "valid", None)


def test_g11_untransmitted_is_void_and_uncounted(db):
    path, store = db
    guard = guard_for(store, GuardCeilings(1, 100, 1))
    claim(path, "op-1")
    ticket = guard.reserve(rid(1), "op-1")
    assert guard.finish(ticket, "timeout", "whole_response_budget") == "void"
    assert rows(path, "SELECT count(*) FROM adp_guard_controls") == [(0,)]
    with pytest.raises(GuardRefused, match="guard_finished"):
        ticket.begin_send()  # a late producer thread can no longer send
    claim(path, "op-2")
    assert guard.reserve(rid(2), "op-2").number == 2


def test_g11_transmitted_is_never_void(db):
    path, store = db
    guard = guard_for(store)
    claim(path, "op-1")
    ticket = guard.reserve(rid(1), "op-1")
    ticket.begin_send()
    assert guard.finish(ticket, "timeout", "whole_response_budget") == "timeout"


@pytest.mark.parametrize("config", [
    {}, {"ADP_GUARD_MAX_PER_EPISODE": "5", "ADP_GUARD_MAX_PER_DAY": "100"},
    {"ADP_GUARD_MAX_PER_EPISODE": "05", "ADP_GUARD_MAX_PER_DAY": "100", "ADP_GUARD_MAX_TOTAL": "300"},
    {"ADP_GUARD_MAX_PER_EPISODE": " 5", "ADP_GUARD_MAX_PER_DAY": "100", "ADP_GUARD_MAX_TOTAL": "300"},
    {"ADP_GUARD_MAX_PER_EPISODE": "0", "ADP_GUARD_MAX_PER_DAY": "100", "ADP_GUARD_MAX_TOTAL": "300"},
    {"ADP_GUARD_MAX_PER_EPISODE": "-5", "ADP_GUARD_MAX_PER_DAY": "100", "ADP_GUARD_MAX_TOTAL": "300"},
    {"ADP_GUARD_MAX_PER_EPISODE": "10001", "ADP_GUARD_MAX_PER_DAY": "100", "ADP_GUARD_MAX_TOTAL": "300"},
    {"ADP_GUARD_MAX_PER_EPISODE": "５", "ADP_GUARD_MAX_PER_DAY": "100", "ADP_GUARD_MAX_TOTAL": "300"},
])
def test_g12_bad_ceiling_configuration_sends_nothing(monkeypatch, db, config):
    path, store = db
    assert parse_ceilings(config) is None
    extractor = adp.configured_readback_extractor({"ADP_EXTRACTION_ENABLED": "true", "ADP_CHAT_ENDPOINT": ENDPOINT,
                                                   "ADP_APPKEY": "test-key", **config}, store)
    _, calls = https_transport(monkeypatch)
    claim(path, "fictional-correlation")
    result = extractor.extract(live_request())
    assert (result.validation, result.failure_category) == ("not_sent", "guard_config")
    assert connects(calls) == [] and rows(path, "SELECT count(*) FROM adp_reservations") == [(0,)]


LIVE_CONFIG = {"ADP_EXTRACTION_ENABLED": "true", "ADP_CHAT_ENDPOINT": ENDPOINT, "ADP_APPKEY": "test-key",
               "ADP_GUARD_MAX_PER_EPISODE": "5", "ADP_GUARD_MAX_PER_DAY": "100", "ADP_GUARD_MAX_TOTAL": "300"}


def test_g12_in_memory_database_sends_nothing(monkeypatch):
    store = SqliteEpisodeStore(":memory:")
    extractor = adp.configured_readback_extractor(LIVE_CONFIG, store)
    _, calls = https_transport(monkeypatch)
    result = extractor.extract(live_request())
    assert (result.validation, result.failure_category) == ("not_sent", "guard_config") and connects(calls) == []
    assert (adp.configured_readback_extractor(LIVE_CONFIG).extract(live_request()).failure_category) == "guard_config"


def test_g12_valid_ceilings_parse():
    assert parse_ceilings(LIVE_CONFIG) == GuardCeilings(5, 100, 300)


def test_g13_live_selection_is_always_guarded(db):
    _, store = db
    extractor = adp.configured_readback_extractor(LIVE_CONFIG, store)
    assert isinstance(extractor, adp.AdpReadbackExtractor)
    assert isinstance(extractor._transport.guard, LiveGuard) and extractor._transport.guard.ceilings == CEILINGS


def test_g13_live_extractor_without_a_guard_sends_nothing(monkeypatch, db):
    path, store = db
    extractor, calls, _ = guarded_live(monkeypatch, store, path)
    extractor._transport.guard = None
    result = extractor.extract(live_request())
    assert (result.validation, result.failure_category) == ("not_sent", "guard_config") and connects(calls) == []


def test_g14_send_without_a_pending_scoring_claim_is_refused(monkeypatch, db):
    path, store = db
    extractor, calls, _ = guarded_live(monkeypatch, store, path, operation=None)
    claim(path, "fictional-correlation", kind="confirm_words")
    result = extractor.extract(live_request())
    assert (result.validation, result.failure_category) == ("not_sent", "guard_unbound") and connects(calls) == []


def test_g14_completed_claim_is_refused(db):
    path, store = db
    claim(path, "op-1")
    conn = sqlite3.connect(path)
    conn.execute("INSERT INTO journey_commands (operation_id, phase, episode_id, expected_revision, claim_revision, kind, "
                 "purpose, body_sha256, terminal_state, scored, recorded_at) VALUES ('op-1', 'completed', 'ep-1', 0, 0, "
                 "'score_words', 'p', ?, 'unavailable', 0, ?)", ("a" * 64, STAMP))
    conn.commit()
    conn.close()
    with pytest.raises(GuardRefused, match="guard_unbound"):
        guard_for(store).reserve(rid(1), "op-1")


def test_g15_second_send_for_one_operation_is_refused_by_the_engine(db):
    path, store = db
    guard = guard_for(store)
    spend(path, guard, 1)
    with pytest.raises(sqlite3.IntegrityError):
        guard.reserve(rid(2), "op-1")
    assert rows(path, "SELECT count(*) FROM adp_reservations") == [(1,)]


@pytest.mark.parametrize("table", ["adp_reservations", "adp_reservation_outcomes", "adp_guard_controls"])
def test_g16_guard_tables_are_append_only(db, table):
    path, store = db
    guard = guard_for(store)
    spend(path, guard, 1, outcome="invalid")
    conn = sqlite3.connect(path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute(f"UPDATE {table} SET rowid = rowid")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute(f"DELETE FROM {table}")
    finally:
        conn.close()


def test_g17_status_writes_nothing_and_controls_need_a_reason(db, monkeypatch, capsys):
    path, store = db
    guard = guard_for(store)
    spend(path, guard, 1, outcome="invalid")
    dump = lambda: [rows(path, f"SELECT * FROM {t}") for t in ("adp_reservations", "adp_reservation_outcomes", "adp_guard_controls")]
    before = dump()
    status = guard.status()
    assert dump() == before
    assert status["halted"] and status["total"] == 1 and status["latest"][0]["request"] == rid(1)[:8]
    for bad in ("", "   ", "x" * 201, None):
        with pytest.raises(ValueError):
            guard.clear_halt(bad)
    assert dump() == before
    monkeypatch.setenv("APP_DATABASE_URL", str(path))
    with pytest.raises(SystemExit):
        adp_guard.main(["clear-halt"])
    assert adp_guard.main(["status"]) == 0
    printed = capsys.readouterr().out
    assert rid(1) not in printed and json.loads(printed)["halted"] is True
    assert dump() == before
    assert adp_guard.main(["clear-halt", "--reason", "reviewed"]) == 0
    assert guard.status()["halted"] is False


def test_g17_cli_refuses_without_a_database(monkeypatch):
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)
    assert adp_guard.main(["status"]) == 2


@pytest.mark.parametrize("flag", [None, "", "false", "0", "False"])
def test_g19_default_stays_offline_with_no_guard(monkeypatch, flag):
    monkeypatch.setattr(adp_guard, "build_guard", lambda *a, **k: pytest.fail("guard built while offline"))
    config = {} if flag is None else {"ADP_EXTRACTION_ENABLED": flag}
    assert isinstance(adp.configured_readback_extractor(config, None), adp.OfflineReadbackExtractor)


def test_g20_test_runs_never_name_a_real_database():
    target = os.environ.get("APP_DATABASE_URL")
    assert target is None or target == ":memory:" or "pytest" in target, "tests must run with APP_DATABASE_URL unset"
    assert os.environ.get("ADP_EXTRACTION_ENABLED") in (None, "", "false", "0")


def test_g20_archived_harness_ledger_is_byte_identical():
    archive = Path.home() / "carerelay-evidence-archive/s21-live-guard-20261016"
    if not archive.is_dir():
        pytest.skip("archived harness ledger not on this machine")
    ledger = archive / "ledger/live-call-ledger.json"
    assert hashlib.sha256(ledger.read_bytes()).hexdigest() == (archive / "ledger.sha256").read_text().split()[0]


def test_guard_finish_failure_leaves_the_row_unfinished(monkeypatch, db):
    path, store = db
    extractor, calls, guard = guarded_live(monkeypatch, store, path)
    monkeypatch.setattr(guard, "_record_outcome", lambda *a: (_ for _ in ()).throw(RuntimeError("store down")))
    assert extractor.extract(live_request()).validation == "valid"
    assert guard.status()["unfinished"] == [1]
    claim(path, "next")
    with pytest.raises(GuardRefused, match="guard_unfinished"):
        guard.reserve(rid(2), "next")
