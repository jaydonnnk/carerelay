"""The Postgres schema, and the append-only guarantee expressed in plpgsql.

Slice 7b, stage 1. This module is the counterpart of the `_SCHEMA_SQL` and
`_append_only_ddl()` pair in `state.py`, and it exists because the two engines
need different DDL for the same guarantee. Keeping it separate means neither
engine's schema can be accidentally edited into the other's dialect.

**The schema below is a faithful port, column for column, of `_SCHEMA_SQL` in
`state.py`.** It was written by reading that schema rather than by rewriting it
from memory, because the first draft of this file invented column names for
`restatements`, `barriers`, `escalations`, `evidence` and `human_acceptances`,
and gave three tables a `SERIAL` key the SQLite schema gives a `TEXT` one.
`tests/test_postgres_store.py::test_the_two_schemas_agree` now compares the two
engine schemas by parsing both, so that class of error fails a test instead of
looking plausible.

Two differences are deliberate and are the only two:

1. `INTEGER PRIMARY KEY` becomes `SERIAL PRIMARY KEY`, because Postgres has no
   rowid and `INTEGER PRIMARY KEY` there is not auto-incrementing.
2. `REAL` becomes `DOUBLE PRECISION` for the one column that uses it.

**The table set is now equal, not merely a superset, and a test enforces that.**
The first draft of this file carried a fifteenth table, `transcript_confirmations`,
with no counterpart in SQLite and, because it was never added to
`APPEND_ONLY_TABLES`, no append-only triggers. It could be updated, deleted and
truncated on the live instance while every test stayed green, because the parity
test asserted only `sqlite <= postgres` and both append-only lists omitted it. The
table was dead: `record_transcript_confirmation` writes `events.payload` and
`has_transcript_confirmation` reads it back, so nothing ever touched it. It has
been deleted. `test_every_table_exists_in_both_engines` now asserts set equality,
and `test_every_schema_table_is_guarded` asserts each table in `SCHEMA_SQL` is in
`APPEND_ONLY_TABLES` or is named in `UNGUARDED_TABLES` with a reason. Deleting the
table narrows the schema to what the SQLite store has always had; registering it
in both engines would instead have invented a SQLite table no code reads.

`TEXT` timestamps and `INTEGER` booleans are carried across unchanged rather than
converted to `timestamptz` and `boolean`. The domain layer reads them back through
`_parse` and its own conversions, and a type change here would quietly alter every
comparison the Closure Contract makes about a deadline.

**Why the guarantee needed re-proving rather than translating.** A port is not a
translation when the target engine has a larger surface. SQLite has no `TRUNCATE`
statement, so row-level `BEFORE DELETE` triggers covered every way the record
could be erased. Postgres does have `TRUNCATE`, and it **does not fire row-level
triggers at all**, so a two-trigger port would have shipped a record that any
caller could empty in one statement while every existing test stayed green. That
was found by probing the engine before writing the store, not by porting the code
and hoping. Three triggers per table, not two.

The `TRUNCATE` trigger must be `FOR EACH STATEMENT`; Postgres rejects
`FOR EACH ROW` for it, because there are no rows for it to fire against.
"""

from __future__ import annotations

#: The tables whose rows may never be updated or deleted. Mirrors
#: `state.APPEND_ONLY_TABLES`; `tests/test_postgres_store.py` asserts the two
#: lists agree and that `SCHEMA_SQL` holds no table outside this list and
#: `UNGUARDED_TABLES`, so a table added to one engine and not the other is a test
#: failure rather than a silent gap.
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
    "barriers",
    "escalations",
    "expiry_events",
    "restatements",
    "events",
)

#: Tables in `SCHEMA_SQL` that are deliberately **not** append-only, with the
#: reason. Empty today: every table in this schema is part of the clinical record
#: and nothing in the product has a legitimate UPDATE or DELETE. The tuple exists
#: so that `test_every_schema_table_is_guarded` can require a table to be either
#: guarded or named here, which makes an unguarded table a decision that was taken
#: on purpose rather than a table nobody noticed. A future non-record table (a
#: job queue, a session cache) goes here with its reason.
UNGUARDED_TABLES: tuple[str, ...] = ()

#: The one refusal function every trigger calls. `TG_TABLE_NAME` and `TG_OP` mean
#: one function serves all 42 triggers, so a new table inherits the wording and
#: the error code without anyone copying it.
_REFUSE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION carerelay_refuse_write() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION '% is append-only: % is refused', TG_TABLE_NAME, TG_OP
        USING ERRCODE = 'restrict_violation';
END;
$$ LANGUAGE plpgsql;
"""

SCHEMA_SQL = """
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
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS barriers (
    id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    disposition_version INTEGER NOT NULL,
    barrier_text TEXT NOT NULL,
    proposed_route_id TEXT,
    permitted_route_id TEXT,
    stopped_at_human_path INTEGER NOT NULL CHECK (stopped_at_human_path IN (0,1)),
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
    dwell_seconds DOUBLE PRECISION,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    episode_id TEXT NOT NULL REFERENCES episodes(id),
    kind TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL
);
"""


def append_only_ddl(tables: tuple[str, ...] = APPEND_ONLY_TABLES) -> str:
    """Three triggers per table: refuse UPDATE, refuse DELETE, refuse TRUNCATE.

    Generated from the table list rather than written out, so a new table cannot
    be added without inheriting all three. The SQLite generator next door emits
    two; the third is the one this engine needs and that one cannot express.

    **`DROP TRIGGER IF EXISTS` then `CREATE`, not `CREATE TRIGGER IF NOT
    EXISTS`.** Postgres has no `IF NOT EXISTS` clause on `CREATE TRIGGER`; the
    SQLite form was the first thing tried here and it is a syntax error. The
    drop-then-create pair is the portable way to make this idempotent, which it
    must be, because `PostgresEpisodeStore.__init__` runs it on every connection.

    `DROP TABLE` is deliberately not guarded. The schema has to remain
    rebuildable, and a guard that made the tables immortal would make the
    migration unrepeatable.
    """
    statements: list[str] = [_REFUSE_FUNCTION_SQL]
    for table in tables:
        statements.append(f"DROP TRIGGER IF EXISTS {table}_no_update ON {table};")
        statements.append(
            f"CREATE TRIGGER {table}_no_update\n"
            f"BEFORE UPDATE ON {table}\n"
            f"FOR EACH ROW EXECUTE FUNCTION carerelay_refuse_write();"
        )
        statements.append(f"DROP TRIGGER IF EXISTS {table}_no_delete ON {table};")
        statements.append(
            f"CREATE TRIGGER {table}_no_delete\n"
            f"BEFORE DELETE ON {table}\n"
            f"FOR EACH ROW EXECUTE FUNCTION carerelay_refuse_write();"
        )
        statements.append(f"DROP TRIGGER IF EXISTS {table}_no_truncate ON {table};")
        # Statement-level, and it has to be: Postgres raises
        # "TRUNCATE FOR EACH ROW triggers are not supported" for the other form.
        # A row-level trigger would never fire here, which is the whole defect.
        statements.append(
            f"CREATE TRIGGER {table}_no_truncate\n"
            f"BEFORE TRUNCATE ON {table}\n"
            f"FOR EACH STATEMENT EXECUTE FUNCTION carerelay_refuse_write();"
        )
    return "\n".join(statements)
