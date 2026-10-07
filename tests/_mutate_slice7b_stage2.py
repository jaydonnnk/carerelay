"""Mutation check for the Slice 7b Postgres port, stage 2.

Run: PYTHONPATH=src python tests/_mutate_slice7b_stage2.py

Requires a live Postgres on `probe_dsn()`. When none is reachable the module
tests skip, and a skip is not a RED, so this harness reports the skip as a
SURVIVED and exits non-zero. Same rule as the stage 1 harness, same reason: a
mutation harness reporting green against a skipped suite is the failure mode it
exists to prevent.

Six mutations, each of which must be seen RED:

    S1  `open_attempt_once` goes back to `ON CONFLICT DO UPDATE`
    S2  `record_expiry_once` stops translating `UniqueViolation` into `False`
    S3  `record_callback_once` loses its consent re-check
    S4  `SqliteEpisodeStore.list_barriers` goes back to `sqlite3.Row`
    S5  `has_transcript_confirmation` loses the `IS JSON` guard
    S6  `record_expiry_once` re-broadens its handler over the audit write

**Why these five.** Stage 2 ported ~40 methods, and the risk in a port is not
that a method stops working, it is that a method keeps working while dropping the
thing it was refusing. S1 and S2 are the O1 defence: both were rewritten from
`INSERT OR REPLACE` onto `DO NOTHING`, and `DO UPDATE` is the tempting
substitution that the append-only trigger refuses. S3 is the guard whose
mechanism changed outright (`BEGIN IMMEDIATE` became `SELECT ... FOR UPDATE`), so
it is the one most likely to have been quietly lost in the rewrite. S4 is the
signature-parity finding: `list_barriers` returning `sqlite3.Row` is the state
the protocol was written against, and it is one edit away from coming back. S5 is
the JSON cast, which raises on Postgres and does not on SQLite.

The five, and what they actually returned.

**First run, 4 October 2026: 3 RED, 2 SURVIVED, and this docstring said 5 RED.**
That was false, and the adversarial review of 5 October 2026 is what caught it:
re-run on a live PostgreSQL 17.11, the harness printed `3 RED, 2 SURVIVED of 5`.
S1 and S2 survived. Neither was a broken guard. `open_attempt_once` and
`record_expiry_once` both return through a `SELECT`-based guard when the row is
already there, so a **sequential** second call never executes the mutated
statement at all: the `ON CONFLICT` clause and the `UniqueViolation` handler sit
behind a branch only two concurrent writers can reach. The defect was in the
suite, not in the store, and it was one missing test rather than two.

**After `TestTwoWritersAtOneKey`, 5 October 2026: 5 RED, 0 SURVIVED.** Both
survivors are killed by the two-writer race on the same live engine, each with
the sequential idempotency test green beside it (`progress=.F`). That pairing is
the control: it attributes the RED to the race rather than to a broken write
path.

    S1  `open_attempt_once` back to `DO UPDATE`            RED  (two-writer race)
    S2  `record_expiry_once` re-raising `UniqueViolation`  RED  (two-writer race)
    S3  `record_callback_once` loses its consent re-check  RED
    S4  `SqliteEpisodeStore.list_barriers` not a mapping   RED
    S5  `has_transcript_confirmation` loses `IS JSON`      RED

**What S4 taught, because the first version of it was wrong.** S4 originally
restored `sqlite3.Row` as the returned row type and expected the cross-engine
comparison to catch it. It did not: the module's `_projection` reads barrier rows
with `row.items()`, `sqlite3.Row` has `keys()` and indexing but **no `items()`**,
so a field-by-field comparison would have raised `AttributeError` rather than
compared a `Row` to a `dict` successfully. The mutation was changed to return an
object that still offers `items()` but is not a mapping, and the cross-engine
comparison is the test that catches it. The weaker form above is what
distinguishes "the guard works" from "the test happened to blow up".

**Three harness defects found while running this, all worth more than the
mutations.** (1) Red was read from pytest's summary line, which pytest prints
**only when more than one test ran**, so a one-test selector printed
`'.  [100%]'` and was reported SURVIVED while its exit code was 1. (2) The child
environment was built as a fresh dict instead of a copy of `os.environ`, which
dropped `CARERELAY_TEST_DSN`: every Postgres-gated test skipped, `skipif`
satisfied the run, and the skips were invisible because the summary text they
appear in was the same text being used to infer RED. (3) Found while fixing the
record on 5 October 2026: a "how many tests ran" count was added to the verdict
as `or ran == 0`, parsed from the summary line that defect (1) says does not
exist for a small selection, so **all five** mutations reported NOT PROVEN and
the harness looked broken while every mutation was in fact RED. The count is now
read off the progress characters and is display only. **Never infer a verdict
from formatted output when an exit code exists, and never let a count that
failed to parse change one.**

Line endings: the three target files are CRLF. Anchors are matched against the
file's real bytes, in CRLF or LF form, so a later conversion does not break the
harness.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
STORE = REPO / "src" / "carerelay" / "postgres_store.py"
STATE = REPO / "src" / "carerelay" / "state.py"
PYTHON = sys.executable

STAGE2 = "tests/test_postgres_stage2.py"


def _select(*tests: str) -> list[str]:
    """A pytest selector for one or more test names.

    `-k` is a substring match, so a name that is a prefix of another would
    silently select both. None of the names below is a prefix of another, and
    the harness reports how many tests the run collected so a mis-selection is
    visible rather than inferred from a colour.
    """
    return [STAGE2, "-k", " or ".join(tests), "--no-header", "-q"]


IDEMPOTENT = "test_the_stores_own_idempotent_writes_go_through_do_nothing"
RACE_ATTEMPT = "test_two_writers_opening_one_attempt_agree_on_one_row"
RACE_EXPIRY = "test_two_writers_recording_one_expiry_get_one_true_and_one_false"
REVOKED = _select("test_a_revoked_consent_stops_a_callback")
COMPARISON = _select("test_the_whole_scripted_episode_is_identical_on_both_engines")
NON_JSON = _select("test_a_non_json_event_payload_does_not_break_the_transcript_read")

#: S1 and S2 select the two-writer race **and** the sequential idempotency test.
#: The sequential one alone cannot kill either mutation: both methods return
#: through a `SELECT`-based guard before the mutated statement is reached, so on
#: a second sequential call the `ON CONFLICT` clause and the `UniqueViolation`
#: handler are never executed. That is why the first run of this harness reported
#: both as SURVIVED, and it was a coverage gap rather than a broken guard.
ATTEMPT_RACE = _select(RACE_ATTEMPT, IDEMPOTENT)
EXPIRY_RACE = _select(RACE_EXPIRY, IDEMPOTENT)

#: S6 selects the one test that pins the handler's scope. It is the only test in
#: the module that reaches `_append_event` from inside `record_expiry_once`.
SCOPE = _select(
    "test_a_duplicate_from_the_audit_write_propagates_instead_of_returning_false"
)


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _purge_bytecode(path: pathlib.Path) -> None:
    """Delete any cached bytecode compiled from `path`.

    **Why this is here.** Python validates a `.pyc` against the source's
    *mtime and size only*, never against its content, so a `.pyc` compiled
    while a mutation was live can keep being imported long after the source
    has been restored. On 5 October 2026 one did: `refuse_delete` ran
    `DELETE ... WHERE false` for a whole session against a file that read
    `WHERE true`, the statement matched no row, no row-level trigger fired,
    and the product's strongest guarantee looked broken with no defect
    anywhere in the source. Restoring the bytes is not enough; the compiled
    artefact has to go with them. `tests/_mutate_slice7b.py` carries the
    full account, and `tasks/lessons.md` records it.
    """
    cache = path.parent / "__pycache__"
    if not cache.is_dir():
        return
    for stale in cache.glob(f"{path.stem}.*.pyc"):
        stale.unlink()


def _run_pytest(args: list[str]) -> subprocess.CompletedProcess[str]:
    """One pytest run with the environment this project expects.

    **`PYTHONPATH` is rebuilt, not inherited, and a missing `CARERELAY_TEST_DSN`
    is refused rather than run.** The first version stripped `PYTHONPATH` and set
    only that one variable, which dropped `CARERELAY_TEST_DSN` with it: every
    Postgres-gated test skipped, `skipif` satisfied the run, and the harness read
    the skip as a verdict. Lesson 22 in `tasks/lessons.md` is the same defect one
    level down, which is why this now refuses up front instead of trusting the
    caller's shell.
    """
    if not os.environ.get("CARERELAY_TEST_DSN"):
        raise SystemExit(
            "CARERELAY_TEST_DSN is not set. Without it every Postgres-gated test "
            "skips and this harness would report on skips. Set it and re-run."
        )
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    # A `.pyc` compiled from a mutated file outlives the restore, so no
    # child process may write one.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [PYTHON, "-m", "pytest", "-o", "addopts=", "-q", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _local_suite_breaks() -> bool:
    """Whether the local suite is red **before** a mutation, which invalidates it.

    `state.py` is the SQLite store, so a mutation there does not only hit the
    Postgres tests: it would break hundreds of local tests in `test_state.py`,
    `test_service.py` and `test_api.py`. In that situation a RED is not evidence
    that the Postgres test caught the change, it is evidence that SQLite fell
    over. Measured 4 October 2026: the local barrier tests read `Row` with
    `row["col"]`, which a `dict` also satisfies, so S4 leaves all 107 of them
    green. That is the finding, not a reason to delete the mutation: it means no
    local test pinned the row type and the cross-engine comparison is the only
    thing that can.
    """
    return _run_pytest(["tests/test_state.py"]).returncode != 0


def _anchor(text: str, data: bytes) -> bytes | None:
    """The anchor as the file actually stores it: LF, or CRLF if the file is so.

    Tried as given first, then in the CRLF form. The Slice 7 harness had the
    reverse bug and produced `\\r\\r\\n`; this refuses to double-convert.
    """
    as_given = text.encode("utf-8")
    if as_given in data:
        return as_given
    crlf = text.replace("\n", "\r\n").encode("utf-8")
    if crlf in data:
        return crlf
    lf = text.replace("\r\n", "\n").encode("utf-8")
    if lf in data:
        return lf
    return None


#: (label, target path, anchor, replacement, selectors)
MUTATIONS = [
    (
        "S1  open_attempt_once goes back to ON CONFLICT DO UPDATE",
        STORE,
        '                "ON CONFLICT (idempotency_key) DO NOTHING",\n',
        '                "ON CONFLICT (idempotency_key) DO UPDATE SET id = EXCLUDED.id",\n',
        ATTEMPT_RACE,
    ),
    (
        "S2  record_expiry_once stops translating UniqueViolation into False",
        STORE,
        '                cur.execute("ROLLBACK TO SAVEPOINT expiry_events_insert")\n'
        "                return False\n",
        '                cur.execute("ROLLBACK TO SAVEPOINT expiry_events_insert")\n'
        "                raise\n",
        EXPIRY_RACE,
    ),
    (
        "S6  record_expiry_once re-broadens its handler over the audit write",
        STORE,
        '            cur.execute("RELEASE SAVEPOINT expiry_events_insert")\n'
        "            self._append_event(\n"
        '                cur, episode_id, "expiry_recorded", f"version={disposition_version}", now_utc\n'
        "            )\n"
        "            return True\n",
        '            cur.execute("RELEASE SAVEPOINT expiry_events_insert")\n'
        "            try:\n"
        "                self._append_event(\n"
        '                    cur, episode_id, "expiry_recorded", f"version={disposition_version}", now_utc\n'
        "                )\n"
        "            except psycopg.errors.UniqueViolation:\n"
        "                return False\n"
        "            return True\n",
        SCOPE,
    ),
    (
        "S3  record_callback_once loses its consent re-check",
        STORE,
        '                reason = self._consent_rejection_reason(\n'
        "                    cur, episode_id, int(attempt[\"consent_version\"])\n"
        "                )\n",
        "                reason = None\n",
        REVOKED,
    ),
    (
        "S4  SqliteEpisodeStore.list_barriers returns a row type that is not a mapping",
        STATE,
        "        return tuple(\n"
        "            dict(row)\n"
        "            for row in self._conn.execute(\n"
        '                "SELECT * FROM barriers WHERE episode_id = ? ORDER BY rowid",\n',
        "        return tuple(\n"
        "            type('NotAMapping', (object,), {'items': lambda self: ()})()\n"
        "            for row in self._conn.execute(\n"
        '                "SELECT * FROM barriers WHERE episode_id = ? ORDER BY rowid",\n',
        COMPARISON,
    ),
    (
        "S5  has_transcript_confirmation loses the IS JSON guard",
        STORE,
        '                "SELECT 1 FROM events WHERE episode_id = %s AND kind = "\n'
        "                \"'transcript_confirmed' AND (CASE WHEN payload IS JSON THEN \"\n"
        '                "payload::jsonb ->> \'confirmation_id\' END) = %s",\n',
        '                "SELECT 1 FROM events WHERE episode_id = %s AND kind = "\n'
        "                \"'transcript_confirmed' AND payload::jsonb ->> 'confirmation_id' = %s\",\n",
        NON_JSON,
    ),
]


def main() -> int:
    originals: dict[pathlib.Path, bytes] = {}
    for path in {STORE, STATE}:
        data = path.read_bytes()
        originals[path] = data
        crlf = data.count(b"\r\n")
        lone = data.count(b"\n") - crlf
        print(f"[BASE] {path.name}: md5={_md5(data)} CRLF={crlf} loneLF={lone}")
    print()

    #: A SURVIVED mutation and a mutation that was never actually run are
    #: different failures and are reported separately. The first version of this
    #: harness put both in one list and called both "SURVIVED", which is how a
    #: selector that matched nothing could be read as a guard with no teeth, and
    #: how a guard with no teeth could be read as a harness defect.
    survivors: list[str] = []
    harness_defects: list[str] = []
    red = 0
    survived = 0
    not_proven = 0

    for label, target, anchor_text, replacement_text, selectors in MUTATIONS:
        original = originals[target]
        anchor = _anchor(anchor_text, original)
        if anchor is None:
            print(f"[FAIL] {label}: anchor not found in {target.name}")
            harness_defects.append(f"{label} (anchor not found)")
            not_proven += 1
            continue
        if original.count(anchor) != 1:
            print(
                f"[FAIL] {label}: anchor appears {original.count(anchor)} times "
                f"in {target.name}"
            )
            harness_defects.append(f"{label} (anchor not unique)")
            not_proven += 1
            continue

        if target is STATE and _local_suite_breaks():
            print(f"[FAIL] {label}: the local suite is red before any mutation")
            harness_defects.append(f"{label} (baseline not green)")
            not_proven += 1
            continue

        replacement = _anchor(replacement_text, original)
        if replacement is None:
            replacement = replacement_text.encode("utf-8")

        target.write_bytes(original.replace(anchor, replacement))
        try:
            completed = _run_pytest(selectors)
        finally:
            target.write_bytes(original)
            _purge_bytecode(target)

        output = completed.stdout + completed.stderr
        failing = [
            line.split("::")[-1].split(" ")[0].strip()
            for line in output.splitlines()
            if line.startswith("FAILED") or line.startswith("ERROR")
        ]
        # `-q` prints **no summary line** for a small selection, only a progress
        # line like `'..  [100%]'`, so the number of tests that ran has to be
        # read off the progress characters. This is display and a sanity check
        # only: the verdict below is the exit code, and a count that fails to
        # parse must never be able to turn a RED into a NOT PROVEN. An earlier
        # revision of this harness inferred the verdict from the summary text and
        # reported a one-test RED as SURVIVED; do not reintroduce that in either
        # direction.
        progress = "".join(
            re.findall(r"^([.FsxXE]+)\s+\[\s*\d+%\]$", output, re.MULTILINE)
        )
        ran = len(progress)
        # A single test prints `'.   [100%]'` and **no summary line at all**, so
        # a missing summary is not evidence of anything on its own. Red was
        # previously inferred from the summary text, which made a one-test
        # selector look like a SURVIVED guard. The exit code is the verdict; the
        # summary is printed for the reader.
        #
        # `skipped` is only meaningful when pytest actually ran something and
        # exited 0: a run that reports skips *and* failures is a run that failed,
        # and treating it as a skip is how a broken baseline got reported as a
        # clean skip in an earlier draft.
        collected_nothing = "no tests ran" in output
        # A skip shows up as `s` in the progress line, and with `-q` there is
        # often no summary line to read the word "skipped" from, so both are
        # checked. Reading only the summary text is how a skipped suite was once
        # reported as a verdict.
        skipped = completed.returncode == 0 and ("s" in progress or "skipped" in output)

        print(f"[RUN ] {label}")
        print(
            f"       rc={completed.returncode} ran={ran or '?'} "
            f"progress={progress or '(none)'} failing={failing or '(none)'}"
        )
        if collected_nothing:
            print("       *** NOT PROVEN: the selector matched no test ***")
            harness_defects.append(f"{label} (selector matched nothing)")
            not_proven += 1
        elif skipped:
            print("       *** NOT PROVEN: the suite skipped, so nothing ran ***")
            harness_defects.append(f"{label} (suite skipped, no Postgres)")
            not_proven += 1
        elif completed.returncode != 0:
            red += 1
            print(f"       *** RED: killed by {', '.join(failing) or 'an error'} ***")
        else:
            print("       *** SURVIVED: no test in the selection can fail on it ***")
            survivors.append(f"{label} (SURVIVED)")
            survived += 1

    print()
    restored_ok = True
    for path, original in originals.items():
        restored = path.read_bytes()
        if restored != original:
            print(f"[FAIL] {path.name}: restore is not byte-identical")
            restored_ok = False
        else:
            print(f"[ OK ] {path.name}: restored byte-identical md5={_md5(restored)}")

    print()
    print(
        f"{red} RED, {survived} SURVIVED, {not_proven} NOT PROVEN, "
        f"of {len(MUTATIONS)}"
    )
    if survivors:
        print("SURVIVED (the mutation ran and no test could fail on it):")
        for item in survivors:
            print(f"  - {item}")
    if harness_defects:
        print("NOT PROVEN (a harness or environment defect, not a verdict):")
        for item in harness_defects:
            print(f"  - {item}")
    if not restored_ok:
        print("The tree was NOT restored byte-identically. Fix that by hand.")
    return 0 if (not survivors and not harness_defects and restored_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
