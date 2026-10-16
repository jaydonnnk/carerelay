"""Slice 24: the durable reservation guard for live ADP read-back (Gate 2 section 15).

Every live HTTPS send is reserved in the application database, on the calling
thread, before the transport may open its socket. The transport refuses to open
without the matching ticket, and refuses to hand the payload to the socket once
the ticket is finished, so a send is always either reserved and counted or void.

Ceilings, a durable halt and one-call-at-a-time bound every send. Any missing
piece refuses with nothing sent. Tables are append-only on both engines.
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

CEILING_NAMES = ("ADP_GUARD_MAX_PER_EPISODE", "ADP_GUARD_MAX_PER_DAY", "ADP_GUARD_MAX_TOTAL")
CEILING_MAX = 10_000
SGT = ZoneInfo("Asia/Singapore")
HALTING_OUTCOMES = frozenset({"invalid", "timeout", "transport", "lost"})
_OUTCOMES = frozenset({"valid", "refused", "invalid", "timeout", "transport"})


class GuardRefused(RuntimeError):
    """A bounded reason only; nothing was sent."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class GuardCeilings:
    per_episode: int
    per_day: int
    total: int


def parse_ceilings(config) -> GuardCeilings | None:
    """Digits only, 1 to 10,000; anything else is None, which refuses every send."""
    values = []
    for name in CEILING_NAMES:
        raw = config.get(name)
        if type(raw) is not str or not raw.isascii() or not raw.isdigit() or raw.startswith("0"):
            return None
        value = int(raw)
        if not 1 <= value <= CEILING_MAX:
            return None
        values.append(value)
    return GuardCeilings(*values)


@dataclass
class Ticket:
    number: int
    request_id: str
    started: float
    transmitted: bool = False
    finished: bool = False
    opened: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def begin_send(self) -> None:
        """Called by the transport immediately before the payload reaches the socket."""
        with self.lock:
            if self.finished:
                raise GuardRefused("guard_finished")
            self.transmitted = True


def _iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).isoformat()


_UNFINISHED = ("SELECT count(*) FROM adp_reservations r WHERE NOT EXISTS "
               "(SELECT 1 FROM adp_reservation_outcomes o WHERE o.number = r.number)")
_COUNTED = ("SELECT count(*) FROM adp_reservations r LEFT JOIN adp_reservation_outcomes o "
            "ON o.number = r.number WHERE (o.outcome IS NULL OR o.outcome <> 'void')")


class LiveGuard:
    """Reservation, finish and operator controls over one store."""

    def __init__(self, store, ceilings: GuardCeilings | None, *, config_error: str | None = None,
                 now=lambda: datetime.now(timezone.utc), monotonic=time.monotonic):
        self._store, self.ceilings = store, ceilings
        self._config_error = config_error if config_error is not None else (None if ceilings else "guard_config")
        self._now, self._monotonic = now, monotonic
        self._tickets: dict[str, Ticket] = {}
        self._tickets_lock = threading.Lock()

    # -- send path ------------------------------------------------------------

    def reserve(self, request_id: str, operation_id: str) -> Ticket:
        if self._config_error is not None or self._store is None:
            raise GuardRefused("guard_config")
        if type(request_id) is not str or type(operation_id) is not str or not operation_id:
            raise GuardRefused("guard_unbound")
        now = self._now()
        with self._store.adp_guard_transaction(write=True) as run:
            latest = run("SELECT kind FROM adp_guard_controls ORDER BY seq DESC LIMIT 1")
            if latest and latest[0][0] == "halt":
                raise GuardRefused("guard_halted")
            if run(_UNFINISHED)[0][0]:
                raise GuardRefused("guard_unfinished")
            claim = run("SELECT c.episode_id FROM journey_commands c WHERE c.operation_id = ? AND c.phase = 'claimed' "
                        "AND c.kind IN ('score_words', 'repair_words') AND NOT EXISTS (SELECT 1 FROM journey_commands d "
                        "WHERE d.operation_id = c.operation_id AND d.phase = 'completed')", (operation_id,))
            if len(claim) != 1:
                raise GuardRefused("guard_unbound")
            episode_id = claim[0][0]
            day = now.astimezone(SGT).date().isoformat()
            if run(_COUNTED + " AND r.episode_id = ?", (episode_id,))[0][0] >= self.ceilings.per_episode:
                raise GuardRefused("guard_episode_ceiling")
            if run(_COUNTED + " AND r.sgt_day = ?", (day,))[0][0] >= self.ceilings.per_day:
                raise GuardRefused("guard_day_ceiling")
            if run(_COUNTED)[0][0] >= self.ceilings.total:
                raise GuardRefused("guard_total_ceiling")
            number = run("SELECT coalesce(max(number), 0) + 1 FROM adp_reservations")[0][0]
            run("INSERT INTO adp_reservations (number, request_id, operation_id, episode_id, sgt_day, reserved_at) "
                "VALUES (?, ?, ?, ?, ?, ?)", (number, request_id, operation_id, episode_id, day, _iso(now)))
        ticket = Ticket(int(number), request_id, self._monotonic())
        with self._tickets_lock:
            self._tickets[request_id] = ticket
        return ticket

    def claim(self, request_id) -> Ticket:
        """The transport's check: one committed, unopened ticket for exactly this RequestId."""
        with self._tickets_lock:
            ticket = self._tickets.get(request_id) if type(request_id) is str else None
            if ticket is None or ticket.opened or ticket.finished:
                raise GuardRefused("guard_unbound")
            ticket.opened = True
            return ticket

    def finish(self, ticket: Ticket, validation: str | None, failure_category: str | None) -> str:
        """Exactly one outcome row; a halting outcome writes its halt in the same transaction."""
        with ticket.lock:
            ticket.finished = True
            transmitted = ticket.transmitted
        with self._tickets_lock:
            self._tickets.pop(ticket.request_id, None)
        outcome = "void" if not transmitted else validation if validation in _OUTCOMES else "transport"
        elapsed = max(0, round((self._monotonic() - ticket.started) * 1000))
        category = failure_category if type(failure_category) is str and len(failure_category) <= 64 else None
        self._record_outcome(ticket.number, outcome, category, elapsed)
        return outcome

    def _record_outcome(self, number, outcome, category, elapsed):
        now = _iso(self._now())
        with self._store.adp_guard_transaction(write=True) as run:
            run("INSERT INTO adp_reservation_outcomes (number, outcome, failure_category, elapsed_ms, finished_at) "
                "VALUES (?, ?, ?, ?, ?)", (number, outcome, category, elapsed, now))
            if outcome in HALTING_OUTCOMES:
                run("INSERT INTO adp_guard_controls (kind, number, reason, recorded_at) VALUES ('halt', ?, ?, ?)",
                    (number, f"{outcome} {category or ''}".strip()[:200], now))

    # -- operator -------------------------------------------------------------

    def status(self) -> dict:
        now = self._now()
        day = now.astimezone(SGT).date().isoformat()
        with self._store.adp_guard_transaction(write=False) as run:
            latest = run("SELECT kind, number, reason FROM adp_guard_controls ORDER BY seq DESC LIMIT 1")
            unfinished = run("SELECT r.number FROM adp_reservations r WHERE NOT EXISTS "
                             "(SELECT 1 FROM adp_reservation_outcomes o WHERE o.number = r.number) ORDER BY r.number")
            per_episode = run("SELECT coalesce(max(n), 0) FROM (SELECT count(*) AS n FROM adp_reservations r "
                              "LEFT JOIN adp_reservation_outcomes o ON o.number = r.number "
                              "WHERE (o.outcome IS NULL OR o.outcome <> 'void') GROUP BY r.episode_id) AS per")[0][0]
            today = run(_COUNTED + " AND r.sgt_day = ?", (day,))[0][0]
            total = run(_COUNTED)[0][0]
            rows = run("SELECT r.number, o.outcome, o.failure_category, o.elapsed_ms, r.request_id FROM adp_reservations r "
                       "LEFT JOIN adp_reservation_outcomes o ON o.number = r.number ORDER BY r.number DESC LIMIT 10")
        halted = bool(latest) and latest[0][0] == "halt"
        return {"ceilings": None if self.ceilings is None else vars(self.ceilings), "config_ok": self._config_error is None,
                "halted": halted, "halt_reason": latest[0][2] if halted else None,
                "unfinished": [row[0] for row in unfinished], "episode_max": per_episode, "today": today,
                "sgt_day": day, "total": total,
                "latest": [{"number": n, "outcome": o, "category": c, "elapsed_ms": e, "request": r[:8]}
                           for n, o, c, e, r in rows]}

    def clear_halt(self, reason: str) -> None:
        reason = _reason(reason)
        with self._store.adp_guard_transaction(write=True) as run:
            run("INSERT INTO adp_guard_controls (kind, number, reason, recorded_at) VALUES ('clear', NULL, ?, ?)",
                (reason, _iso(self._now())))

    def mark_lost(self, number: int, reason: str) -> None:
        reason = _reason(reason)
        with self._store.adp_guard_transaction(write=False) as run:
            known = run("SELECT r.number FROM adp_reservations r WHERE r.number = ? AND NOT EXISTS "
                        "(SELECT 1 FROM adp_reservation_outcomes o WHERE o.number = r.number)", (number,))
        if not known:
            raise ValueError("no unfinished reservation with that number")
        self._record_outcome(number, "lost", reason[:64], None)


def _reason(reason) -> str:
    if type(reason) is not str or not 1 <= len(reason.strip()) <= 200:
        raise ValueError("a reason of 1 to 200 characters is required")
    return reason.strip()


def build_guard(config, store) -> LiveGuard:
    """Never raises: an unusable configuration gives a guard that refuses every send."""
    ceilings = parse_ceilings(config)
    durable = store is not None and getattr(store, "path", None) != ":memory:"
    return LiveGuard(store if durable else None, ceilings,
                     config_error=None if ceilings is not None and durable else "guard_config")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m carerelay.adp_guard")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    clear = sub.add_parser("clear-halt")
    clear.add_argument("--reason", required=True)
    lost = sub.add_parser("mark-lost")
    lost.add_argument("number", type=int)
    lost.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    target = os.environ.get("APP_DATABASE_URL")
    if not target:
        print("APP_DATABASE_URL is not set", file=sys.stderr)
        return 2
    from carerelay.state import open_store
    store = open_store(target)
    try:
        guard = LiveGuard(store, parse_ceilings(os.environ))
        if args.command == "status":
            import json
            print(json.dumps(guard.status(), indent=2))
        elif args.command == "clear-halt":
            guard.clear_halt(args.reason)
            print("halt cleared")
        else:
            guard.mark_lost(args.number, args.reason)
            print(f"reservation {args.number} recorded lost; sends are halted")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
