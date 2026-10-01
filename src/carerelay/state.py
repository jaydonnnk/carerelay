"""SQLite state: the append-only clinical record. Slice 3.

This is the layer the Closure Contract rests on. `02-architecture.md` D3 says the
clinical record is append-only and D4 says closure is derived, never stored. A
convention is not an enforcement, so the append-only claim is enforced here by
`BEFORE UPDATE` and `BEFORE DELETE` triggers on **every** table.
`tests/test_state.py` proves that with raw SQL that bypasses this module's Python
guards entirely, and proves it fails when the triggers are removed.

**What that enforcement covers, stated exactly (O1).** Triggers are schema-level,
but `REPLACE` conflict resolution is not. SQLite fires the implicit `DELETE` that a
`REPLACE` performs only when the connection has `recursive_triggers` enabled, and
that pragma is per-connection rather than stored in the database file. The refusal
is therefore:

* **any connection this module opens**: `UPDATE`, `DELETE` and `INSERT OR REPLACE`
  are all refused, because `__init__` enables the pragma on every one of them;
* **any other connection**: `UPDATE` and `DELETE` are refused, and
  `INSERT OR REPLACE` is refused only if that connection enables the pragma too.

The honest claim is "no update or delete path through this module, and `UPDATE` and
`DELETE` refused from any connection", not "the database has no update path at
all". A schema-level guard that would close the remaining case was measured and
rejected: a `BEFORE INSERT` trigger cannot tell `INSERT OR REPLACE` from the
harmless idempotent `INSERT OR IGNORE`, so it refuses both. See O1 in
`00-status.md`.

Five things in this file are load-bearing, and each is a deliberate reading of an
approved document rather than an accident:

1. **The callback representation (R6, the hardest item in this slice).**
   `callbacks.callback_key` is UNIQUE for the first receipt only. Every duplicate
   is *also* written, with a null unique key, `duplicate_of` pointing at the first
   receipt and `accepted = 0`. SQLite permits many nulls under a unique
   constraint, so uniqueness and "record every receipt" hold at the same time.
   `BEGIN IMMEDIATE` serialises the lookup and the insert, and the transition
   append happens in the same transaction, so a crash cannot leave a receipt
   without its consequence. The received key is kept for every receipt as a
   SHA-256 digest in `callback_key_digest`, which is the redacted audit field
   `03-program-design.md` section 3 asks for.
2. **Terminal states are absorbing.** A reordered acknowledgement arriving after a
   failure is appended as a transition and is non-winning; `domain.project_attempt`
   already implements first-terminal-in-`seq`-order wins, and this module supplies
   the monotonic `seq`.
3. **Consent is re-checked at record time.** The attempt carries the consent
   version it was opened under. A callback, or a standalone evidence record, is
   refused when the current consent is missing, revoked, or at a different
   version. The refused receipt is still written, so the failure is visible in the
   ledger instead of vanishing.
4. **Expiry is sticky and is never recorded early.** `record_expiry_once` refuses
   to write an event before the deadline has passed, because a premature expiry
   tells a patient their window is gone when it is not. Once an event exists for a
   disposition version, a backwards clock cannot remove it and a second call is a
   no-op that returns `False` (D12).
5. **The snapshot reports the expiry event for the current disposition version.**
   An expiry event names the version whose deadline passed. A reassessment inserts
   a new version with a new deadline, so the old event no longer describes the
   current plan. The event row is never deleted and stays in the ledger; it simply
   stops being the current plan's expiry. Within one version, D12 stickiness holds
   exactly as written.

Nothing here reads a clock. Every timestamp is an argument (D5): the caller owns
time, this module only records it.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from carerelay.domain import rules
from carerelay.domain.models import (
    COMPARISON_FIELDS,
    MAX_REPAIR_ROUNDS,
    TERMINAL_TRANSITIONS,
    AttemptCommand,
    AttemptSnapshot,
    AttemptTransition,
    CallbackResult,
    ClosureProjection,
    Disposition,
    DispositionSource,
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
    RecallOutcome,
)

__all__ = [
    "StateError",
    "EpisodeNotFound",
    "AttemptNotFound",
    "ConsentNotCurrent",
    "EvidenceProvenanceViolation",
    "DispositionVersionConflict",
    "NoDispositionForExpiry",
    "PrematureExpiry",
    "IdempotencyKeyCollision",
    "UnconfirmedTranscript",
    "RepairRoundOutOfRange",
    "RestatementNotFound",
    "CallbackReceipt",
    "HintEventRecord",
    "RestatementRecord",
    "derive_attempt_key",
    "transcript_confirmation_id",
    "SqliteEpisodeStore",
    "APPEND_ONLY_TABLES",
    "CLINICAL_SCOPE",
    "DEFAULT_KEY_NAMESPACE",
]

#: The one consent scope the judged fixture uses. The column supports more; the
#: snapshot carries a single `consent_version` (`03-program-design.md` section 3).
CLINICAL_SCOPE = "clinical_share"

#: Folded into the idempotency key material so a key cannot be replayed across
#: deployments. A server-held secret can be substituted at Slice 6 without
#: changing the signature (D5).
DEFAULT_KEY_NAMESPACE = "carerelay.attempt.v1"

DEFAULT_BUSY_TIMEOUT_MS = 5000

#: Every table in this schema. The clinical record is append-only, and so is
#: everything else here: nothing in the product has a legitimate UPDATE or DELETE.
APPEND_ONLY_TABLES: tuple[str, ...] = (
    "episodes",
    "policy_versions",
    "dispositions",
    "attempts",
    "attempt_transitions",
    "callbacks",
    "evidence",
    "consents",
    "human_acceptances",
    "escalations",
    "expiry_events",
    "restatements",
    "events",
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class StateError(Exception):
    """Base class for a refusal to record or to read."""


class EpisodeNotFound(StateError):
    pass


class AttemptNotFound(StateError):
    pass


class ConsentNotCurrent(StateError):
    """The stamped consent version is not the current granted consent.

    Raised on open, on callback and on standalone evidence recording. The refused
    receipt is still written by the caller path, so the failure stays visible.
    """


class EvidenceProvenanceViolation(StateError):
    """A row claiming `documented` without a non-simulated, sourced artefact (D11)."""


class DispositionVersionConflict(StateError):
    """A disposition version that already exists, or one that skips a number."""


class NoDispositionForExpiry(StateError):
    """An expiry event for a disposition version that does not exist."""


class PrematureExpiry(StateError):
    """An expiry event before the deadline passed. Refused, never recorded."""


class IdempotencyKeyCollision(StateError):
    """One key reused for two different `(episode, route, purpose)` triples."""


class UnconfirmedTranscript(StateError):
    """A voice restatement was scored before its transcript was confirmed.

    The record-level half of Gate 1's ordering rule: `domain` decides, and this
    module refuses to hold a round that was evaluated on a draft the patient
    never agreed to.
    """


class RepairRoundOutOfRange(StateError):
    """A repair round outside `0..MAX_REPAIR_ROUNDS`. Never written (C6)."""


class RestatementNotFound(StateError):
    """A restatement id the record does not hold."""


# ---------------------------------------------------------------------------
# Idempotency keys
# ---------------------------------------------------------------------------


def derive_attempt_key(
    episode_id: str,
    route_id: str,
    purpose_id: str,
    *,
    namespace: str = DEFAULT_KEY_NAMESPACE,
) -> str:
    """The server-generated attempt key (D5). The client never supplies one.

    Deterministic in `(episode, route, purpose)` so a double tap produces the
    *same* key, hits `UNIQUE`, and is recorded as a suppressed duplicate instead
    of dispatching a second tool call. If the client generated the key, a double
    tap would produce two keys, I3 would never fire, and two requests would
    dispatch.

    Each part is length-prefixed before hashing. Plain concatenation would make
    `("ab", "c")` and `("a", "bc")` collide, which is exactly the boundary a
    hostile or merely unlucky pair of ids would find.
    """
    material = "\x1f".join(
        f"{len(part)}:{part}"
        for part in (namespace, episode_id, route_id, purpose_id)
    )
    return "att-" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def transcript_confirmation_id(text: str) -> str:
    """Bind a confirmation to the text it confirmed.

    The id is a digest of the normalised text, not an opaque counter. That is
    what makes Gate 1's ordering rule enforceable: a restatement may only be
    scored when a confirmation exists whose id equals the digest of **the very
    text being scored**, so the draft cannot be swapped for a corrected version
    between confirmation and evaluation. An opaque id would let the caller name
    any confirmation and score any string.

    The text itself is not recoverable from the id, so the id is safe to carry
    in a URL and in the ledger.
    """
    return "tc-" + _digest(rules.normalise(text))


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------


def _utc(value: datetime) -> datetime:
    """Normalise to UTC, refusing a naive value.

    A naive timestamp is a bug, not a default. Guessing a timezone here would put
    the deadline, the one fact the product exists to preserve, at risk.
    """
    if value.tzinfo is None:
        raise StateError(
            "timestamps must be timezone-aware; state never guesses a timezone"
        )
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat()


def _parse(text: str) -> datetime:
    return datetime.fromisoformat(text)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS episodes (
    id TEXT PRIMARY KEY,
    persona TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policy_versions (
    version TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    provenance TEXT NOT NULL,
    approved_by TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dispositions (
    id INTEGER PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    version_no INTEGER NOT NULL,
    policy_version TEXT NOT NULL REFERENCES policy_versions(version),
    action_id TEXT NOT NULL,
    clinical_deadline_utc TEXT NOT NULL,
    next_owner_id TEXT NOT NULL,
    fallback_route_id TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('fixture','reviewer','reassessment')),
    created_at TEXT NOT NULL,
    UNIQUE (episode_id, version_no)
);

CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    route_id TEXT NOT NULL,
    purpose_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    consent_version INTEGER NOT NULL,
    opened_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempt_transitions (
    id INTEGER PRIMARY KEY,
    attempt_id TEXT NOT NULL REFERENCES attempts(id),
    seq INTEGER NOT NULL,
    transition TEXT NOT NULL
        CHECK (transition IN ('acknowledged','failed','superseded')),
    origin TEXT NOT NULL CHECK (origin IN ('platform','local-sim')),
    payload TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL,
    UNIQUE (attempt_id, seq)
);

CREATE TABLE IF NOT EXISTS callbacks (
    id INTEGER PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    route_id TEXT NOT NULL,
    attempt_id TEXT REFERENCES attempts(id),
    callback_key TEXT UNIQUE,
    callback_key_digest TEXT NOT NULL,
    duplicate_of INTEGER REFERENCES callbacks(id),
    accepted INTEGER NOT NULL CHECK (accepted IN (0,1)),
    rejection_reason TEXT,
    origin TEXT NOT NULL CHECK (origin IN ('platform','local-sim')),
    result TEXT
        CHECK (result IS NULL OR result IN ('acknowledged','failed','superseded')),
    payload TEXT NOT NULL DEFAULT '',
    received_at TEXT NOT NULL,
    CHECK (accepted = 1 OR rejection_reason IS NOT NULL),
    CHECK (accepted = 0 OR rejection_reason IS NULL),
    CHECK ((callback_key IS NULL) = (duplicate_of IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    level TEXT NOT NULL CHECK (level IN ('self_reported','documented')),
    simulated INTEGER NOT NULL CHECK (simulated IN (0,1)),
    provenance TEXT NOT NULL,
    source_ref TEXT,
    recorded_at TEXT NOT NULL,
    CHECK (level <> 'documented'
           OR (simulated = 0 AND source_ref IS NOT NULL AND trim(source_ref) <> ''))
);

CREATE TABLE IF NOT EXISTS consents (
    id INTEGER PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    scope TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('granted','revoked')),
    version INTEGER NOT NULL,
    recorded_at TEXT NOT NULL,
    UNIQUE (episode_id, scope, version)
);

CREATE TABLE IF NOT EXISTS human_acceptances (
    id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    accepted_by TEXT NOT NULL,
    scope TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS escalations (
    id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    human_path TEXT NOT NULL,
    outcome TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expiry_events (
    id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    disposition_version INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    UNIQUE (episode_id, disposition_version)
);

CREATE TABLE IF NOT EXISTS restatements (
    id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    disposition_version INTEGER NOT NULL,
    hint_level TEXT NOT NULL CHECK (hint_level IN ('H0','H1','H2','H3')),
    input_mode TEXT NOT NULL,
    transcript_confirmed INTEGER NOT NULL CHECK (transcript_confirmed IN (0,1)),
    extracted_json TEXT NOT NULL,
    mismatches TEXT NOT NULL,
    repair_round INTEGER NOT NULL,
    outcome TEXT NOT NULL CHECK (
        outcome IN ('recall_unaided','recall_scaffolded','recall_cued','not_recalled')
    ),
    dwell_seconds REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    kind TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL
);
"""


def _append_only_ddl() -> str:
    """One `BEFORE UPDATE` and one `BEFORE DELETE` trigger per table.

    Generated from `APPEND_ONLY_TABLES` so a new table cannot be added without
    inheriting the rule. A trigger is used rather than a Python guard because the
    claim being made is about the record, not about this module's callers: the
    test that proves it opens its own connection and issues raw SQL.

    The `BEFORE DELETE` half is also what refuses `INSERT OR REPLACE`: a `REPLACE`
    satisfies its uniqueness conflict by deleting the existing row, and that
    implicit delete goes through this trigger once `recursive_triggers` is on (O1).
    """
    statements: list[str] = []
    for table in APPEND_ONLY_TABLES:
        for operation in ("UPDATE", "DELETE"):
            statements.append(
                f"CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()}\n"
                f"BEFORE {operation} ON {table}\n"
                f"BEGIN\n"
                f"    SELECT RAISE(ABORT, "
                f"'{table} is append-only: {operation} is refused');\n"
                f"END;"
            )
    return "\n".join(statements)


# ---------------------------------------------------------------------------
# Read values
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CallbackReceipt:
    """One row of `callbacks`, as the ledger reads it.

    Every receipt is present, accepted or not. `accepted = False` always carries a
    `rejection_reason`, which the schema enforces, so "why was this not applied"
    is answerable from the row alone.
    """

    receipt_id: int
    route_id: str
    attempt_id: str | None
    callback_key: str | None
    callback_key_digest: str
    duplicate_of: int | None
    accepted: bool
    rejection_reason: str | None
    origin: Origin
    result: ExecutionStatus | None
    payload: str
    received_at: datetime


@dataclass(frozen=True)
class HintEventRecord:
    """One hint event, as the judge ledger reads it.

    `dwell_seconds` is judge-facing evidence and nothing more: it is recorded,
    shown in the ledger, and must never reach the patient surface
    (`PLAN.md` 5.2.1, constraint C8).
    """

    level: HintLevel
    kind: HintEventKind
    dwell_seconds: float | None
    recorded_at: datetime


@dataclass(frozen=True)
class RestatementRecord:
    """One row of `restatements`, as the judge ledger reads it.

    The columns the evaluation depends on are carried whole: the raw spans the
    coordinator returned, and the comparison `domain` produced from them. The
    row is the evidence that a recorded hint level was used for a real round,
    because a hint level that is not recorded with its outcome is a claim about
    scaffolding that cannot be audited.

    `dwell_seconds` is judge-facing evidence only: recorded, shown in the
    ledger, never shown to the patient (`PLAN.md` 5.2.1, constraint C8).
    """

    restatement_id: str
    episode_id: str
    disposition_version: int
    hint_level: HintLevel
    input_mode: InputMode
    transcript_confirmed: bool
    extracted: ExtractedPlan
    comparison: PlanComparison
    repair_round: int
    outcome: RecallOutcome
    dwell_seconds: float | None
    created_at: datetime


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------


class SqliteEpisodeStore:
    """The append-only record, behind repository methods.

    One instance is one connection. Two instances on one file are the two-writer
    case that R6 is about, and `BEGIN IMMEDIATE` plus the busy timeout is what
    makes them safe: within the timeout the second writer waits for the lock rather
    than failing, so the losing callback is recorded as a duplicate instead of being
    lost. Past the timeout it does fail, loudly, and writes nothing. That boundary
    is stated here rather than left implied; see `_write` and O2.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
        key_namespace: str = DEFAULT_KEY_NAMESPACE,
        check_same_thread: bool = True,
    ) -> None:
        """One instance is one connection.

        `check_same_thread` is `True` by default, which is SQLite's own guard
        against a connection being shared across threads. It is **not** a
        guarantee of thread safety: SQLite has no way to make one connection safe
        for concurrent use, so a caller that passes `False` owns the serialisation
        itself, and Slice 4's `api.py` does exactly that with an explicit lock.
        FastAPI serves synchronous routes from a thread pool, so one store shared
        by several requests needs the flag off and the lock on.
        """
        self.path = str(path)
        self.key_namespace = key_namespace
        self.busy_timeout_ms = busy_timeout_ms
        self._conn = sqlite3.connect(
            self.path,
            isolation_level=None,
            timeout=busy_timeout_ms / 1000,
            check_same_thread=check_same_thread,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        self._conn.execute("PRAGMA foreign_keys = ON")
        # O1. SQLite runs the implicit DELETE that a `REPLACE` performs only when
        # this connection has recursive triggers enabled, and it defaults to off.
        # Without this line `INSERT OR REPLACE` rewrites any row, including
        # `dispositions.clinical_deadline_utc`. The pragma is per-connection and is
        # not stored in the file, which is why the module docstring qualifies the
        # claim rather than making an unconditional one.
        self._conn.execute("PRAGMA recursive_triggers = ON")
        if self.path != ":memory:":
            # WAL for concurrent readers during a write, and FULL so a crash
            # between the commit and the disk write cannot lose an append.
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = FULL")
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.executescript(_append_only_ddl())

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> SqliteEpisodeStore:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- transactions ------------------------------------------------------

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        """`BEGIN IMMEDIATE` around one logical write.

        IMMEDIATE, not deferred: the write lock is taken at the start of the
        transaction rather than at the first write, which is what makes the
        callback lookup-then-insert atomic. Under a deferred transaction two
        writers could both read "no such key" and one would fail at COMMIT
        instead of being recorded as a duplicate.

        The wait is bounded, not unconditional. A second writer waits for the lock
        only for `busy_timeout_ms`; past that SQLite raises a raw
        `sqlite3.OperationalError: database is locked` and no receipt is written.
        The failure is loud rather than silent, so no receipt is lost without
        saying so. Turning it into a typed `StateError`, so a caller can tell
        "retry" from "refuse", is O2 and belongs at Slice 6, where the action path
        consumes the result.
        """
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield self._conn
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        else:
            self._conn.execute("COMMIT")

    # -- audit -------------------------------------------------------------

    def _append_event(
        self, episode_id: str, kind: str, payload: str, now_utc: datetime
    ) -> None:
        """One row of `events`. Called inside the caller's transaction, so the
        audit row and the fact it describes commit together."""
        self._conn.execute(
            "INSERT INTO events (episode_id, kind, payload, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            (episode_id, kind, payload, _iso(now_utc)),
        )

    def list_events(self, episode_id: str) -> tuple[tuple[str, str, datetime], ...]:
        rows = self._conn.execute(
            "SELECT kind, payload, recorded_at FROM events WHERE episode_id = ? "
            "ORDER BY id",
            (episode_id,),
        ).fetchall()
        return tuple((row["kind"], row["payload"], _parse(row["recorded_at"])) for row in rows)

    # -- episode, policy, disposition --------------------------------------

    def create_episode(self, episode_id: str, persona: str, *, now_utc: datetime) -> None:
        with self._write():
            self._conn.execute(
                "INSERT INTO episodes (id, persona, created_at) VALUES (?, ?, ?)",
                (episode_id, persona, _iso(now_utc)),
            )
            self._append_event(episode_id, "episode_created", persona, now_utc)

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
        """
        self._conn.execute(
            "INSERT INTO policy_versions "
            "(version, content, provenance, approved_by, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (version, content, provenance, approved_by, _iso(now_utc)),
        )

    def insert_disposition(self, disposition: Disposition, *, now_utc: datetime) -> None:
        """Append one disposition version. There is no update path (D3, I1).

        Versions must be contiguous from 1. A gap would mean a version was
        rewritten rather than appended, which is the one thing the deadline
        invariant cannot survive.
        """
        with self._write():
            current = self._conn.execute(
                "SELECT MAX(version_no) AS top FROM dispositions WHERE episode_id = ?",
                (disposition.episode_id,),
            ).fetchone()
            top = current["top"] or 0
            if disposition.version != top + 1:
                raise DispositionVersionConflict(
                    f"disposition version {disposition.version} does not follow "
                    f"version {top} for episode {disposition.episode_id!r}"
                )
            self._conn.execute(
                "INSERT INTO dispositions "
                "(episode_id, version_no, policy_version, action_id, "
                " clinical_deadline_utc, next_owner_id, fallback_route_id, source, "
                " created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                disposition.episode_id,
                "disposition_recorded",
                f"version={disposition.version} source={disposition.source.value}",
                now_utc,
            )

    def list_dispositions(self, episode_id: str) -> tuple[Disposition, ...]:
        rows = self._conn.execute(
            "SELECT * FROM dispositions WHERE episode_id = ? ORDER BY version_no",
            (episode_id,),
        ).fetchall()
        return tuple(_disposition_from_row(row) for row in rows)

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
        with self._write():
            row = self._conn.execute(
                "SELECT MAX(version) AS top FROM consents "
                "WHERE episode_id = ? AND scope = ?",
                (episode_id, scope),
            ).fetchone()
            version = (row["top"] or 0) + 1
            state = "granted" if granted else "revoked"
            self._conn.execute(
                "INSERT INTO consents (episode_id, scope, state, version, recorded_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (episode_id, scope, state, version, _iso(now_utc)),
            )
            self._append_event(
                episode_id, "consent_changed", f"scope={scope} {state} v{version}", now_utc
            )
        return version

    def _current_consent(self, episode_id: str, scope: str) -> tuple[int, str] | None:
        row = self._conn.execute(
            "SELECT version, state FROM consents WHERE episode_id = ? AND scope = ? "
            "ORDER BY version DESC LIMIT 1",
            (episode_id, scope),
        ).fetchone()
        if row is None:
            return None
        return int(row["version"]), str(row["state"])

    def _require_current_consent(self, episode_id: str, stamped_version: int) -> None:
        current = self._current_consent(episode_id, CLINICAL_SCOPE)
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

    def _require_granted_consent(self, episode_id: str) -> None:
        """For paths with no attempt to compare against, such as the MCP
        `record_evidence` tool. The rule is the same: revocation stops recording."""
        current = self._current_consent(episode_id, CLINICAL_SCOPE)
        if current is None:
            raise ConsentNotCurrent(
                f"episode {episode_id!r} has no recorded {CLINICAL_SCOPE} consent"
            )
        version, state = current
        if state != "granted":
            raise ConsentNotCurrent(
                f"{CLINICAL_SCOPE} consent is {state} at version {version}"
            )

    def _consent_rejection_reason(self, episode_id: str, stamped_version: int) -> str | None:
        """The reason a receipt is refused, or `None` when it is accepted.

        Deliberately returns a reason rather than raising: a callback is recorded
        either way, and "we received it and refused it" must be readable in the
        ledger.
        """
        current = self._current_consent(episode_id, CLINICAL_SCOPE)
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

    # -- attempts ----------------------------------------------------------

    def open_attempt_once(
        self,
        command: AttemptCommand,
        key: str,
        *,
        now_utc: datetime,
    ) -> AttemptSnapshot:
        """Open one attempt, or return the one the same key already opened.

        The attempt row and its audit event are written in one transaction, so a
        crash between them is not a representable state. A double tap reuses the
        key, hits `UNIQUE`, appends a `attempt_duplicate_suppressed` event and
        returns the original attempt: recorded, not silently discarded
        (`02-architecture.md` section 4.1).
        """
        with self._write():
            existing = self._conn.execute(
                "SELECT * FROM attempts WHERE idempotency_key = ?", (key,)
            ).fetchone()
            if existing is not None:
                triple = (
                    existing["episode_id"],
                    existing["route_id"],
                    existing["purpose_id"],
                )
                if triple != (command.episode_id, command.route_id, command.purpose_id):
                    raise IdempotencyKeyCollision(
                        f"key {key!r} already opened attempt {existing['id']!r} for "
                        f"{triple!r}, not for "
                        f"{(command.episode_id, command.route_id, command.purpose_id)!r}"
                    )
                self._append_event(
                    command.episode_id,
                    "attempt_duplicate_suppressed",
                    f"key={key} attempt={existing['id']}",
                    now_utc,
                )
                return self._attempt_snapshot(existing)

            self._require_current_consent(command.episode_id, command.consent_version)
            attempt_id = uuid.uuid4().hex
            self._conn.execute(
                "INSERT INTO attempts "
                "(id, episode_id, route_id, purpose_id, idempotency_key, "
                " consent_version, opened_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
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
            self._append_event(
                command.episode_id,
                "attempt_opened",
                f"attempt={attempt_id} route={command.route_id} key={key}",
                now_utc,
            )
            row = self._conn.execute(
                "SELECT * FROM attempts WHERE id = ?", (attempt_id,)
            ).fetchone()
            return self._attempt_snapshot(row)

    def list_attempts(self, episode_id: str) -> tuple[AttemptSnapshot, ...]:
        rows = self._conn.execute(
            "SELECT * FROM attempts WHERE episode_id = ? ORDER BY rowid", (episode_id,)
        ).fetchall()
        return tuple(self._attempt_snapshot(row) for row in rows)

    def list_transitions(self, attempt_id: str) -> tuple[AttemptTransition, ...]:
        rows = self._conn.execute(
            "SELECT * FROM attempt_transitions WHERE attempt_id = ? ORDER BY seq",
            (attempt_id,),
        ).fetchall()
        return tuple(
            AttemptTransition(
                seq=int(row["seq"]),
                kind=ExecutionStatus(row["transition"]),
                origin=Origin(row["origin"]),
                recorded_at=_parse(row["recorded_at"]),
                payload=row["payload"],
            )
            for row in rows
        )

    def _attempt_snapshot(self, row: sqlite3.Row) -> AttemptSnapshot:
        transitions = self.list_transitions(row["id"])
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
    ) -> bool:
        """Record one callback receipt. Returns True only for an applied receipt.

        Order of operations, all inside one `BEGIN IMMEDIATE`:

        1. look the key up. Present means duplicate: write the duplicate row,
           append nothing, return `False`.
        2. otherwise decide whether the receipt may be applied, by re-checking the
           current consent against the version stamped on the attempt. A refusal
           still writes the row, with `accepted = 0` and a reason.
        3. when applied, append the terminal transition (first-terminal-wins is
           `domain.project_attempt`'s job) and any evidence the callback carries.

        A duplicate makes no transition and cannot advance the episode, which is
        what makes the injected duplicate callback in the demo a visible no-op.
        """
        now_utc = _utc(now_utc)
        if result.transition is not None and result.transition not in TERMINAL_TRANSITIONS:
            raise rules.UnpermittedTransition(
                result.transition,
                sorted(member.value for member in TERMINAL_TRANSITIONS),
            )
        if origin not in (Origin.PLATFORM, Origin.LOCAL_SIM):
            raise StateError(f"unknown callback origin {origin!r}")

        with self._write():
            attempt = self._conn.execute(
                "SELECT * FROM attempts WHERE id = ?", (attempt_id,)
            ).fetchone()
            if attempt is None:
                raise AttemptNotFound(attempt_id)

            existing = self._conn.execute(
                "SELECT * FROM callbacks WHERE callback_key = ?", (callback_key,)
            ).fetchone()
            if existing is not None:
                self._insert_receipt(
                    episode_id=attempt["episode_id"],
                    route_id=attempt["route_id"],
                    attempt_id=attempt_id,
                    callback_key=None,
                    digest=_digest(callback_key),
                    duplicate_of=int(existing["id"]),
                    accepted=False,
                    rejection_reason="duplicate",
                    origin=origin,
                    result=None,
                    payload=result.payload,
                    now_utc=now_utc,
                )
                self._append_event(
                    attempt["episode_id"],
                    "callback_duplicate",
                    f"route={attempt['route_id']} first_receipt={existing['id']}",
                    now_utc,
                )
                return False

            reason = self._consent_rejection_reason(
                attempt["episode_id"], int(attempt["consent_version"])
            )
            self._insert_receipt(
                episode_id=attempt["episode_id"],
                route_id=attempt["route_id"],
                attempt_id=attempt_id,
                callback_key=callback_key,
                digest=_digest(callback_key),
                duplicate_of=None,
                accepted=reason is None,
                rejection_reason=reason,
                origin=origin,
                result=result.transition,
                payload=result.payload,
                now_utc=now_utc,
            )
            if reason is not None:
                self._append_event(
                    attempt["episode_id"],
                    "callback_rejected",
                    f"route={attempt['route_id']} reason={reason}",
                    now_utc,
                )
                return False

            if result.transition is not None:
                self._append_transition(
                    attempt_id, result.transition, origin, result.payload, now_utc
                )
            if result.evidence is not None:
                self._insert_evidence(
                    attempt["episode_id"], result.evidence, now_utc=now_utc
                )
            self._append_event(
                attempt["episode_id"],
                "callback_applied",
                f"route={attempt['route_id']} result="
                f"{result.transition.value if result.transition else 'evidence-only'}",
                now_utc,
            )
            return True

    def _insert_receipt(
        self,
        *,
        episode_id: str,
        route_id: str,
        attempt_id: str,
        callback_key: str | None,
        digest: str,
        duplicate_of: int | None,
        accepted: bool,
        rejection_reason: str | None,
        origin: Origin,
        result: ExecutionStatus | None,
        payload: str,
        now_utc: datetime,
    ) -> None:
        self._conn.execute(
            "INSERT INTO callbacks "
            "(episode_id, route_id, attempt_id, callback_key, callback_key_digest, "
            " duplicate_of, accepted, rejection_reason, origin, result, payload, "
            " received_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                episode_id,
                route_id,
                attempt_id,
                callback_key,
                digest,
                duplicate_of,
                int(accepted),
                rejection_reason,
                origin.value,
                result.value if result is not None else None,
                payload,
                _iso(now_utc),
            ),
        )

    def list_callbacks(self, episode_id: str) -> tuple[CallbackReceipt, ...]:
        """Every receipt, in arrival order. This is the ledger's dedupe surface."""
        rows = self._conn.execute(
            "SELECT * FROM callbacks WHERE episode_id = ? ORDER BY id", (episode_id,)
        ).fetchall()
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
                    ExecutionStatus(row["result"]) if row["result"] is not None else None
                ),
                payload=row["payload"],
                received_at=_parse(row["received_at"]),
            )
            for row in rows
        )

    def _append_transition(
        self,
        attempt_id: str,
        transition: ExecutionStatus,
        origin: Origin,
        payload: str,
        now_utc: datetime,
    ) -> None:
        """Append one transition with the next `seq`.

        `seq` is assigned here, monotonically, and never reused. A late
        acknowledgement therefore gets a *higher* `seq` than the failure that
        preceded it and is non-winning under first-terminal-in-order.
        """
        row = self._conn.execute(
            "SELECT MAX(seq) AS top FROM attempt_transitions WHERE attempt_id = ?",
            (attempt_id,),
        ).fetchone()
        seq = (row["top"] or 0) + 1
        self._conn.execute(
            "INSERT INTO attempt_transitions "
            "(attempt_id, seq, transition, origin, payload, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (attempt_id, seq, transition.value, origin.value, payload, _iso(now_utc)),
        )

    # -- evidence ----------------------------------------------------------

    def record_evidence(
        self, episode_id: str, record: EvidenceRecord, *, now_utc: datetime
    ) -> None:
        """Append one evidence row, with D11 enforced twice.

        Once here, and once by the `CHECK` constraint in the schema. The two are
        independent on purpose: the test that proves the constraint opens its own
        connection and issues raw SQL, so removing this guard cannot make the
        constraint test pass. They are also *equivalent*, which took a fix (O6):
        a `NULL`, empty or whitespace-only `source_ref` is refused by both, so
        "enforced twice" is a statement about one rule applied twice rather than
        two rules that happen to overlap.
        """
        with self._write():
            self._require_granted_consent(episode_id)
            self._insert_evidence(episode_id, record, now_utc=now_utc)
            self._append_event(
                episode_id,
                "evidence_recorded",
                f"level={record.level.value} simulated={record.simulated}",
                now_utc,
            )

    def _insert_evidence(
        self, episode_id: str, record: EvidenceRecord, *, now_utc: datetime
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
        self._conn.execute(
            "INSERT INTO evidence "
            "(episode_id, level, simulated, provenance, source_ref, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
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
        rows = self._conn.execute(
            "SELECT * FROM evidence WHERE episode_id = ? ORDER BY id", (episode_id,)
        ).fetchall()
        return tuple(
            EvidenceRecord(
                level=EvidenceLevel(row["level"]),
                simulated=bool(row["simulated"]),
                provenance=row["provenance"],
                source_ref=row["source_ref"],
            )
            for row in rows
        )

    # -- acceptance and escalation -----------------------------------------

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
        `care_evidenced` true. `domain.derive_closure` reads it as closing the
        handoff obligation only (`03-program-design.md` section 3).
        """
        acceptance_id = uuid.uuid4().hex
        with self._write():
            self._conn.execute(
                "INSERT INTO human_acceptances "
                "(id, episode_id, accepted_by, scope, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (acceptance_id, episode_id, accepted_by, scope, _iso(now_utc)),
            )
            self._append_event(
                episode_id,
                "human_acceptance_recorded",
                f"accepted_by={accepted_by} scope={scope}",
                now_utc,
            )
        return acceptance_id

    def record_escalation(
        self,
        episode_id: str,
        *,
        human_path: str,
        outcome: str,
        now_utc: datetime,
    ) -> str:
        escalation_id = uuid.uuid4().hex
        with self._write():
            self._conn.execute(
                "INSERT INTO escalations "
                "(id, episode_id, human_path, outcome, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (escalation_id, episode_id, human_path, outcome, _iso(now_utc)),
            )
            self._append_event(
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
           clock: after a regression the deadline is in the future, and raising
           `PrematureExpiry` there would be wrong, because the event is a fact
           that already happened.
        2. no such disposition version: there is no deadline for anything to have
           passed.
        3. the deadline has not passed: refuse. A premature expiry event tells a
           patient their window is gone while they still have time, which is a
           false statement of exactly the kind the product exists to prevent.
        """
        now_utc = _utc(now_utc)
        with self._write():
            existing = self._conn.execute(
                "SELECT id FROM expiry_events WHERE episode_id = ? AND disposition_version = ?",
                (episode_id, disposition_version),
            ).fetchone()
            if existing is not None:
                return False

            row = self._conn.execute(
                "SELECT clinical_deadline_utc FROM dispositions "
                "WHERE episode_id = ? AND version_no = ?",
                (episode_id, disposition_version),
            ).fetchone()
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
            self._conn.execute(
                "INSERT INTO expiry_events "
                "(id, episode_id, disposition_version, occurred_at) VALUES (?, ?, ?, ?)",
                (event_id, episode_id, disposition_version, _iso(now_utc)),
            )
            self._append_event(
                episode_id,
                "expiry_recorded",
                f"version={disposition_version}",
                now_utc,
            )
            return True

    def list_expiry_events(
        self, episode_id: str
    ) -> tuple[tuple[int, datetime], ...]:
        rows = self._conn.execute(
            "SELECT disposition_version, occurred_at FROM expiry_events "
            "WHERE episode_id = ? ORDER BY rowid",
            (episode_id,),
        ).fetchall()
        return tuple(
            (int(row["disposition_version"]), _parse(row["occurred_at"])) for row in rows
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

        * **an unconfirmed voice transcript cannot be scored.** Gate 1's
          ordering rule, re-checked at the moment of writing so a service-layer
          defect cannot persist a round that was evaluated on a draft;
        * **the repair cap is two.** A third round is never written (C6), so the
          record cannot hold an offer the domain says is never made;
        * **the comparison must name a disposition that exists.** A restatement
          against nothing is not a restatement.

        The extracted spans are patient free text, so the audit `events` row
        carries no span; the spans live in `restatements.extracted_json`, which
        is the clinical record the ledger reads directly.
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

        with self._write():
            episode = self._conn.execute(
                "SELECT id FROM episodes WHERE id = ?", (episode_id,)
            ).fetchone()
            if episode is None:
                raise EpisodeNotFound(episode_id)
            disposition = self._conn.execute(
                "SELECT version_no FROM dispositions WHERE episode_id = ? "
                "AND version_no = ?",
                (episode_id, disposition_version),
            ).fetchone()
            if disposition is None:
                raise NoDispositionForExpiry(
                    f"episode {episode_id!r} has no disposition version "
                    f"{disposition_version} to compare against"
                )

            restatement_id = uuid.uuid4().hex
            self._conn.execute(
                "INSERT INTO restatements "
                "(id, episode_id, disposition_version, hint_level, input_mode, "
                " transcript_confirmed, extracted_json, mismatches, repair_round, "
                " outcome, dwell_seconds, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
        rows = self._conn.execute(
            "SELECT * FROM restatements WHERE episode_id = ? ORDER BY rowid",
            (episode_id,),
        ).fetchall()
        return tuple(_restatement_from_row(row) for row in rows)

    def get_restatement(self, restatement_id: str) -> RestatementRecord:
        row = self._conn.execute(
            "SELECT * FROM restatements WHERE id = ?", (restatement_id,)
        ).fetchone()
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

        The schema has no hint-events table, and Slice 4 adds none: `events` is
        the table the judge ledger already reads. `dwell_seconds` travels here
        and nowhere else in the patient direction (`PLAN.md` 5.2.1, C8).
        """
        now_utc = _utc(now_utc)
        with self._write():
            self._append_event(
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
        rows = self._conn.execute(
            "SELECT payload, recorded_at FROM events WHERE episode_id = ? "
            "AND kind = 'hint_event' ORDER BY id",
            (episode_id,),
        ).fetchall()
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

        Returns the confirmation id, which is a digest of the text itself
        (see `transcript_confirmation_id`), so the id binds to the string rather
        than to a row number the caller cannot be made to respect.

        The confirmed text is clinical free text and lives in `events.payload`,
        which `02-architecture.md` section 8 permits for the clinical record:
        payloads are redacted from application logs, and the ledger reads the
        table directly.
        """
        now_utc = _utc(now_utc)
        confirmation_id = transcript_confirmation_id(text)
        with self._write():
            self._append_event(
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
        """Whether this confirmation was recorded for this episode."""
        row = self._conn.execute(
            "SELECT 1 FROM events WHERE episode_id = ? AND kind = "
            "'transcript_confirmed' AND json_extract(payload, '$.confirmation_id') = ?",
            (episode_id, confirmation_id),
        ).fetchone()
        return row is not None

    # -- projections -------------------------------------------------------

    def load_snapshot(self, episode_id: str) -> EpisodeSnapshot:
        """Everything `domain.derive_closure` is allowed to look at.

        Two selection readings, both documented rather than silent:

        * **The attempt is the latest one.** `EpisodeSnapshot` carries a single
          attempt, and the latest is the one the patient is waiting on.
        * **The expiry event is the one for the current disposition version.** An
          expiry event names a version. A reassessment inserts a new version with
          a new deadline, so the earlier event no longer describes the current
          plan. The row is never removed; it stops being current. Within one
          version, D12 stickiness is exactly as written.
        """
        episode = self._conn.execute(
            "SELECT id FROM episodes WHERE id = ?", (episode_id,)
        ).fetchone()
        if episode is None:
            raise EpisodeNotFound(episode_id)

        disposition_row = self._conn.execute(
            "SELECT * FROM dispositions WHERE episode_id = ? "
            "ORDER BY version_no DESC LIMIT 1",
            (episode_id,),
        ).fetchone()
        disposition = (
            _disposition_from_row(disposition_row) if disposition_row is not None else None
        )

        attempt_row = self._conn.execute(
            "SELECT * FROM attempts WHERE episode_id = ? ORDER BY rowid DESC LIMIT 1",
            (episode_id,),
        ).fetchone()
        attempt = (
            self._attempt_snapshot(attempt_row) if attempt_row is not None else None
        )

        current = self._current_consent(episode_id, CLINICAL_SCOPE)
        acceptance = self._conn.execute(
            "SELECT id FROM human_acceptances WHERE episode_id = ? "
            "ORDER BY rowid DESC LIMIT 1",
            (episode_id,),
        ).fetchone()
        escalation = self._conn.execute(
            "SELECT id FROM escalations WHERE episode_id = ? ORDER BY rowid DESC LIMIT 1",
            (episode_id,),
        ).fetchone()
        expiry = (
            self._conn.execute(
                "SELECT id FROM expiry_events WHERE episode_id = ? "
                "AND disposition_version = ? ORDER BY rowid DESC LIMIT 1",
                (episode_id, disposition.version),
            ).fetchone()
            if disposition is not None
            else None
        )

        return EpisodeSnapshot(
            disposition=disposition,
            attempt=attempt,
            evidence=self.list_evidence(episode_id),
            consent_version=current[0] if current is not None else None,
            human_acceptance_id=acceptance["id"] if acceptance is not None else None,
            escalation_id=escalation["id"] if escalation is not None else None,
            expiry_event_id=expiry["id"] if expiry is not None else None,
        )

    def derive_closure(self, episode_id: str, now_utc: datetime):
        """Convenience read: load the snapshot, then derive. Policy stays in `domain`."""
        return rules.derive_closure(self.load_snapshot(episode_id), now_utc)


def _disposition_from_row(row: sqlite3.Row) -> Disposition:
    return Disposition(
        episode_id=row["episode_id"],
        version=int(row["version_no"]),
        policy_version=row["policy_version"],
        action_id=row["action_id"],
        clinical_deadline_utc=_parse(row["clinical_deadline_utc"]),
        next_owner_id=row["next_owner_id"],
        fallback_route_id=row["fallback_route_id"],
        source=DispositionSource(row["source"]),
    )


def _restatement_from_row(row: sqlite3.Row) -> RestatementRecord:
    extracted_payload = json.loads(row["extracted_json"])
    comparison_payload = json.loads(row["mismatches"])
    return RestatementRecord(
        restatement_id=row["id"],
        episode_id=row["episode_id"],
        disposition_version=int(row["disposition_version"]),
        hint_level=HintLevel(row["hint_level"]),
        input_mode=InputMode(row["input_mode"]),
        transcript_confirmed=bool(row["transcript_confirmed"]),
        extracted=ExtractedPlan(
            action_span=extracted_payload["action_span"],
            deadline_span=extracted_payload["deadline_span"],
            next_owner_span=extracted_payload["next_owner_span"],
            uncertain_fields=frozenset(extracted_payload["uncertain_fields"]),
        ),
        comparison=PlanComparison(
            frozenset(comparison_payload["matched"]),
            frozenset(comparison_payload["mismatched"]),
            frozenset(comparison_payload["uncertain"]),
        ),
        repair_round=int(row["repair_round"]),
        outcome=RecallOutcome(row["outcome"]),
        dwell_seconds=row["dwell_seconds"],
        created_at=_parse(row["created_at"]),
    )


def open_store(path: str | Path, **kwargs: object) -> SqliteEpisodeStore:
    """Named constructor, so call sites do not repeat keyword defaults.

    Keyword arguments pass straight through, including `check_same_thread`, so
    `api.py` can open a store that survives FastAPI's thread-pool dispatch.
    """
    return SqliteEpisodeStore(path, **kwargs)  # type: ignore[arg-type]


# `Sequence` is imported for the protocol's signature parity with Gate 3.
_ = Sequence
