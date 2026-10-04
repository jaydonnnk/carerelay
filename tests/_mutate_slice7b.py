"""Mutation check for the Slice 7b Postgres port, stage 1.

Run: PYTHONPATH=src python tests/_mutate_slice7b.py

Requires a live Postgres on `probe_dsn()`. When none is reachable the module
tests skip, and a skip is not a RED, so this harness reports the skip as a
SURVIVED (it cannot tell "the guard held" from "no guard was run") and exits
non-zero. That is deliberate: a mutation harness reporting green against a
skipped suite is the exact failure mode it exists to prevent.

Seven mutations, each of which must be seen RED:

    P1  the UPDATE trigger is dropped from the DDL
    P2  the DELETE trigger is dropped from the DDL
    P3  the TRUNCATE trigger is dropped from the DDL (the stage's whole point)
    P4  the TRUNCATE trigger goes back to row-level, which Postgres rejects
    P5  the UPDATE probe goes back to `WHERE false` (the seeding control)
    P6  a table is dropped from APPEND_ONLY_TABLES
    P7  the DELETE probe seeds nothing (the empty-table silence returns)

P5 and P7 are the important pair. They reproduce the defect found while writing
this stage: a probe that reaches nothing looks identical to a guard that holds.

**P4 is RED but non-discriminating, and is kept as documentation.** Postgres
rejects `FOR EACH ROW` on a `TRUNCATE` trigger at `CREATE TRIGGER` time, so the
schema becomes unbuildable and every database test errors. That proves the
row-level form is *illegal*, not that it would fail to guard. It is labelled
here so "7 of 7" is not read as seven behavioural proofs.

Each mutation names the tests it is expected to kill, and the run is narrowed to
those tests so a failure is attributed rather than inferred from the whole file.
`schema` mutations break the schema itself, so their selector is the whole file
by necessity; `store` mutations name the single test they target.

Line endings: `postgres_schema.py` and `postgres_store.py` are CRLF. This
harness anchors on the file's real bytes and prefers the CRLF form only if the
file is CRLF, so a later conversion does not silently break it.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = REPO / "src" / "carerelay" / "postgres_schema.py"
STORE = REPO / "src" / "carerelay" / "postgres_store.py"
#: P5 and P7 mutate the append-only probes, which moved out of `postgres_store.py`
#: into this test module at stage 2 (finding F7: test-only surface does not belong
#: on a production class). Their anchors are unchanged, only the file is.
PROBES = REPO / "tests" / "_postgres_probes.py"
PYTHON = sys.executable

ALL_POSTGRES = ["tests/test_postgres_store.py"]

#: The single test each behavioural (`store.py`) mutation is expected to kill.
#: `-k` is a substring match, so these are the full names to avoid selecting the
#: wrong test or none. The schema mutations cannot be narrowed this way: breaking
#: the DDL breaks every test that opens a database.
UPDATE_REFUSAL_TEST = [
    "tests/test_postgres_store.py",
    "-k",
    "test_update_is_refused_on_every_table",
]
DELETE_REFUSAL_TEST = [
    "tests/test_postgres_store.py",
    "-k",
    "test_delete_is_refused_on_every_table",
]
SEED_REACH_TEST = [
    "tests/test_postgres_store.py",
    "-k",
    "test_a_seeded_row_is_visible_to_a_count",
]


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _anchor(text: str, data: bytes) -> bytes | None:
    """The anchor as the file actually stores it: LF, or CRLF if the file is so.

    Tried as given first, then in the LF form. The Slice 7 harness had the
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
        "P1  the UPDATE trigger is removed from the DDL",
        SCHEMA,
        '        statements.append(\n'
        '            f"CREATE TRIGGER {table}_no_update\\n"\n'
        '            f"BEFORE UPDATE ON {table}\\n"\n'
        '            f"FOR EACH ROW EXECUTE FUNCTION carerelay_refuse_write();"\n'
        "        )\n",
        "",
        ALL_POSTGRES,
    ),
    (
        "P2  the DELETE trigger is removed from the DDL",
        SCHEMA,
        '        statements.append(\n'
        '            f"CREATE TRIGGER {table}_no_delete\\n"\n'
        '            f"BEFORE DELETE ON {table}\\n"\n'
        '            f"FOR EACH ROW EXECUTE FUNCTION carerelay_refuse_write();"\n'
        "        )\n",
        "",
        ALL_POSTGRES,
    ),
    (
        "P3  the TRUNCATE trigger is removed from the DDL",
        SCHEMA,
        '        statements.append(\n'
        '            f"CREATE TRIGGER {table}_no_truncate\\n"\n'
        '            f"BEFORE TRUNCATE ON {table}\\n"\n'
        '            f"FOR EACH STATEMENT EXECUTE FUNCTION carerelay_refuse_write();"\n'
        "        )\n",
        "",
        ALL_POSTGRES,
    ),
    (
        "P4  the TRUNCATE trigger goes back to row-level",
        SCHEMA,
        '            f"FOR EACH STATEMENT EXECUTE FUNCTION carerelay_refuse_write();"\n',
        '            f"FOR EACH ROW EXECUTE FUNCTION carerelay_refuse_write();"\n',
        ALL_POSTGRES,
    ),
    (
        "P5  the UPDATE probe goes back to `WHERE false`",
        PROBES,
        '                sql.SQL("UPDATE {} SET {} = {} WHERE true").format(\n',
        '                sql.SQL("UPDATE {} SET {} = {} WHERE false").format(\n',
        UPDATE_REFUSAL_TEST,
    ),
    (
        "P6  a table is dropped from APPEND_ONLY_TABLES",
        SCHEMA,
        '    "events",\n',
        "",
        ALL_POSTGRES,
    ),
    (
        "P7  the DELETE probe seeds nothing (the empty-table silence returns)",
        PROBES,
        '                sql.SQL("DELETE FROM {} WHERE true").format(sql.Identifier(table))\n',
        '                sql.SQL("DELETE FROM {} WHERE false").format(sql.Identifier(table))\n',
        DELETE_REFUSAL_TEST,
    ),
]


def main() -> int:
    originals: dict[pathlib.Path, bytes] = {}
    for path in {SCHEMA, STORE, PROBES}:
        data = path.read_bytes()
        originals[path] = data
        crlf = data.count(b"\r\n")
        lone = data.count(b"\n") - crlf
        print(f"[BASE] {path.name}: md5={_md5(data)} CRLF={crlf} loneLF={lone}")
    print()

    failures: list[str] = []
    red = 0
    survived = 0

    for label, target, anchor_text, replacement_text, selectors in MUTATIONS:
        original = originals[target]
        anchor = _anchor(anchor_text, original)
        if anchor is None:
            print(f"[FAIL] {label}: anchor not found in {target.name}")
            failures.append(f"{label} (anchor not found)")
            continue
        if original.count(anchor) != 1:
            print(
                f"[FAIL] {label}: anchor appears {original.count(anchor)} times "
                f"in {target.name}"
            )
            failures.append(f"{label} (anchor not unique)")
            continue

        replacement = _anchor(replacement_text, original) if replacement_text else b""
        if replacement_text and replacement is None:
            replacement = replacement_text.encode("utf-8")

        target.write_bytes(original.replace(anchor, replacement))
        # `completed` is assigned inside the try so it is always bound: the
        # previous shape read it after the `finally`, so an exception from
        # `subprocess.run` itself left the name unbound and the harness died with
        # a NameError instead of reporting the failed mutation.
        try:
            env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
            env["PYTHONPATH"] = "src"
            completed = subprocess.run(
                [PYTHON, "-m", "pytest", "-o", "addopts=", "-q", *selectors],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        finally:
            target.write_bytes(original)

        output = completed.stdout
        summary = [
            line
            for line in output.splitlines()
            if " passed" in line or " failed" in line or " error" in line
        ]
        skipped = " skipped" in output or "no Postgres reachable" in output

        print(f"[RUN ] {label}")
        print(f"       {summary[-1].strip() if summary else '(no summary)'}")
        if skipped:
            print("       *** SURVIVED: the suite skipped, so nothing was proved ***")
            failures.append(f"{label} (suite skipped, no Postgres)")
            survived += 1
        elif completed.returncode != 0:
            red += 1
        else:
            print("       *** SURVIVED: the guard has no teeth ***")
            failures.append(f"{label} (SURVIVED)")
            survived += 1

    print()
    restored_ok = True
    for path, original in originals.items():
        restored = path.read_bytes()
        if restored != original:
            print(f"[FAIL] {path.name}: restore is not byte-identical")
            restored_ok = False
    if not restored_ok:
        return 1
    print(
        "[CONTROL] restored, md5="
        + ", ".join(f"{p.name}={_md5(d)}" for p, d in originals.items())
        + " byte-identical to baseline"
    )

    print(f"\n=== result: {red} of {len(MUTATIONS)} mutations seen RED ===")
    if failures:
        for item in failures:
            print(f"  PROBLEM: {item}")
        return 1
    print("  every mutation was seen RED; the files were restored byte-exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
