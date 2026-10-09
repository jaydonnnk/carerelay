"""Mutation check for the Slice 11 fault harness. Seven guards, seven sequences.

Run: PYTHONPATH=src python tests/_mutate_slice11.py

The hard requirement from `04-slices.md` is that each sequence must violate at
least one targeted assertion when its guard is independently disabled. This
script disables each guard once, runs only that sequence, and requires a real
failure. **A shared catch does not count**: the selector is pinned to the
sequence whose guard moved, so a mutation that only tripped some other test
would be recorded as NOT PROVEN.

The seven guards, and the defect each one exists to prevent:

* the empty-transition branch of `project_attempt`, so a dropped callback is
  never reported as `failed` (I5);
* the execution-time route recheck in the MCP tool, so a withdrawn route is
  refused and recorded at the last gate before the world is touched;
* the callback-key lookup in `record_callback_once`, so a redelivery cannot
  apply twice (I3). Under this mutation the `UNIQUE` constraint on
  `callbacks.callback_key` catches the insert, and that violation surfaces as
  an error rather than an assertion failure; both are counted as a RED, and
  the harness says so here rather than leaving a reader to wonder why the
  failure line reads as an error;
* the ordering rule in `project_attempt`, so a late acknowledgement cannot
  override a recorded failure;
* the single transaction in `record_callback_once`, so a crash between the
  receipt and its transition is not a representable state;
* the expiry stickiness in `derive_closure`, so a backwards clock cannot
  un-expire an episode whose deadline passed (I1, D12);
* the consent recheck inside `record_callback_once`, so a success arriving
  after revocation is refused, recorded and never applied.

Three conventions carried over from the Slice 8, Slice 9 and Slice 10
harnesses, each of which cost this project a wrong answer once:

* **A RED is read from a real test failure, never from the exit code alone.**
  pytest exits 4 for a selector that resolves to nothing, and a harness
  reading "non-zero means RED" reports a kill for a test that never ran.
* **The count of tests that ran comes off the progress characters**, and
  pytest right-pads that field, so the padding is stripped before counting.
* **The anchor is matched in the file's own newline convention.** The
  repository is CRLF, so an LF-written anchor silently fails to apply and a
  guard that was never touched is recorded as SURVIVED.

Every file is restored byte-identically and its cached bytecode purged,
because a `.pyc` compiled while a mutation was live can outlive the restore.
On top of that, this harness runs with `PYTHONDONTWRITEBYTECODE=1`, which
matters doubly here: the restart sequence spawns child interpreters against
the same tree, and a child importing a mutated `state.py` must not leave a
`.pyc` behind.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
PYTHON = sys.executable

RULES = "src/carerelay/domain/rules.py"
TOOLS = "src/carerelay/tools.py"
STATE = "src/carerelay/state.py"

TARGETS = {
    RULES: REPO / "src" / "carerelay" / "domain" / "rules.py",
    TOOLS: REPO / "src" / "carerelay" / "tools.py",
    STATE: REPO / "src" / "carerelay" / "state.py",
}

FAULT = "tests/test_fault_sequences.py"
TIMEOUT = f"{FAULT}::TestTimeoutSequence"
STALE = f"{FAULT}::TestStaleAvailabilitySequence"
DUPLICATE = f"{FAULT}::TestDuplicateCallbackSequence"
REORDERED = f"{FAULT}::TestReorderedCallbackSequence"
RESTART = f"{FAULT}::TestRestartMidEpisodeSequence"
CLOCK = f"{FAULT}::TestClockChangeSequence"
CONSENT = f"{FAULT}::TestConsentRevocationSequence"

#: (label, target, anchor, replacement, selectors)
MUTATIONS: list[tuple[str, str, bytes, bytes, list[str]]] = [
    (
        "T1  a dropped callback reads as failed",
        RULES,
        b"    if not ordered:\n        return ExecutionStatus.ATTEMPTED\n",
        b"    if not ordered:\n        return ExecutionStatus.FAILED\n",
        [TIMEOUT],
    ),
    (
        "S1  the execution-time route recheck is skipped",
        TOOLS,
        b"        try:\n"
        b"            rules.validate_route(route_id, self._policy.permitted_route_ids)\n"
        b"        except rules.PolicyViolation as exc:\n",
        b"        try:\n"
        b"            None  # MUTANT: the execution-time route recheck is skipped\n"
        b"        except rules.PolicyViolation as exc:\n",
        [STALE],
    ),
    (
        "D1  the duplicate lookup never fires",
        STATE,
        b'                "SELECT * FROM callbacks WHERE callback_key = ?", (callback_key,)\n'
        b"            ).fetchone()\n"
        b"            if existing is not None:\n",
        b'                "SELECT * FROM callbacks WHERE callback_key = ?", (callback_key,)\n'
        b"            ).fetchone()\n"
        b"            if False:  # MUTANT: the duplicate branch never fires\n",
        [DUPLICATE],
    ),
    (
        "R1  the last transition wins instead of the first",
        RULES,
        b"    return ordered[0].kind\n",
        b"    return ordered[-1].kind\n",
        [REORDERED],
    ),
    (
        "X1  the receipt commits before its transition",
        STATE,
        b"            if result.transition is not None:\n"
        b"                self._append_transition(\n"
        b"                    attempt_id, result.transition, origin, result.payload, now_utc\n"
        b"                )\n",
        b'            self._conn.execute("COMMIT")  # MUTANT: the receipt commits alone\n'
        b'            self._conn.execute("BEGIN IMMEDIATE")  # MUTANT: a second transaction\n'
        b"            if result.transition is not None:\n"
        b"                self._append_transition(\n"
        b"                    attempt_id, result.transition, origin, result.payload, now_utc\n"
        b"                )\n",
        [
            f"{RESTART}::test_a_crash_between_receipt_and_transition_leaves_neither"
        ],
    ),
    (
        "C1  a backwards clock un-expires the episode",
        RULES,
        b"    expired = snapshot.expiry_event_id is not None or (\n"
        b"        deadline_passed and not care_evidenced\n"
        b"    )\n",
        b"    expired = (\n        deadline_passed and not care_evidenced\n    )\n",
        [CLOCK],
    ),
    (
        "V1  the consent recheck inside the callback is skipped",
        STATE,
        b'            reason = self._consent_rejection_reason(\n'
        b'                attempt["episode_id"], int(attempt["consent_version"])\n'
        b"            )\n",
        b"            reason = None  # MUTANT: the consent recheck is skipped\n",
        [CONSENT],
    ),
]


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _newline(data: bytes) -> bytes:
    """The dominant newline convention of a file."""
    crlf = data.count(b"\r\n")
    lone = data.count(b"\n") - crlf
    return b"\r\n" if crlf > lone else b"\n"


def _conform(data: bytes, newline: bytes) -> bytes:
    """Rewrite an LF-written anchor or replacement in the target's convention."""
    if newline == b"\r\n":
        return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return data.replace(b"\r\n", b"\n")


def _purge_bytecode(path: pathlib.Path) -> None:
    """Delete cached bytecode compiled from `path`.

    Python validates a `.pyc` against the source's mtime and size only, never
    its content, so a `.pyc` written while a mutation was live can be imported
    long after the source is restored. Restoring bytes is not enough.
    """
    cache = path.parent / "__pycache__"
    if not cache.is_dir():
        return
    for stale in cache.glob(f"{path.stem}.*.pyc"):
        stale.unlink()


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [PYTHON, "-m", "pytest", "-o", "addopts=", "-q", *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        env=env,
    )


def _progress(stdout: str) -> tuple[int, int]:
    """(tests run, tests failed) from the progress characters, padding stripped."""
    ran = 0
    failed = 0
    for raw in stdout.splitlines():
        line = raw.strip()
        if not re.match(r"^[.FEsxX]+\s*\[", line):
            continue
        progress = line.split("[", 1)[0].rstrip()
        ran += len(progress)
        failed += progress.count("F") + progress.count("E")
    return ran, failed


def _failing_ids(stdout: str) -> list[str]:
    return [
        line.split(" - ")[0].replace("FAILED ", "").replace("ERROR ", "").strip()
        for line in stdout.splitlines()
        if line.startswith("FAILED ") or line.startswith("ERROR ")
    ]


def main() -> int:
    baselines = {name: path.read_bytes() for name, path in TARGETS.items()}
    for name, data in baselines.items():
        crlf = data.count(b"\r\n")
        lone = data.count(b"\n") - crlf
        print(f"[BASE] {name:36} md5={_md5(data)} CRLF={crlf} loneLF={lone}")

    # Pre-flight: every mutation must resolve to at least one test, or a
    # NOT PROVEN would be recorded as if the guard had been tested. This is the
    # check that a rename silently orphans (tasks/lessons.md, 5 October 2026).
    unresolved: list[str] = []
    for label, _target, _anchor, _replacement, selectors in MUTATIONS:
        collected = _run(["--collect-only", *selectors])
        ids = [
            line.strip()
            for line in collected.stdout.splitlines()
            if line.strip().startswith("tests/")
        ]
        if not ids:
            unresolved.append(f"{label}  {selectors}")
    if unresolved:
        print("\n[FAIL] mutations that resolve to no test:")
        for item in unresolved:
            print(f"  {item}")
        return 1
    print(f"[PRE ] all {len(MUTATIONS)} mutations resolve to at least one test\n")

    red = 0
    survived: list[str] = []
    not_proven: list[str] = []

    for label, target, anchor, replacement, selectors in MUTATIONS:
        path = TARGETS[target]
        original = baselines[target]
        newline = _newline(original)
        real_anchor = _conform(anchor, newline)
        real_replacement = _conform(replacement, newline)

        if real_anchor not in original:
            print(f"[FAIL] {label}: anchor not found in {target}")
            not_proven.append(f"{label} (anchor not found)")
            continue
        if original.count(real_anchor) != 1:
            print(f"[FAIL] {label}: anchor appears {original.count(real_anchor)} times")
            not_proven.append(f"{label} (anchor not unique)")
            continue

        path.write_bytes(original.replace(real_anchor, real_replacement))
        try:
            completed = _run(selectors)
        finally:
            path.write_bytes(original)
            _purge_bytecode(path)

        ran, failed = _progress(completed.stdout)
        ids = _failing_ids(completed.stdout)
        print(f"[RUN ] {label}  (ran={ran} failed={failed} exit={completed.returncode})")
        for test_id in ids:
            print(f"       RED: {test_id}")

        if completed.returncode == 0:
            print("       *** SURVIVED: the guard has no teeth ***")
            survived.append(label)
        elif ran == 0 or failed == 0:
            print("       *** NOT PROVEN: nothing actually failed ***")
            not_proven.append(f"{label} (no test failed)")
        else:
            red += 1

    print()
    damaged = [
        name for name, path in TARGETS.items() if path.read_bytes() != baselines[name]
    ]
    if damaged:
        for name in damaged:
            print(f"[FAIL] restore is not byte-identical: {name}")
        return 1
    for name, path in TARGETS.items():
        print(f"[CTRL] {name:36} restored, md5={_md5(path.read_bytes())}")

    print(f"\n=== result: {red} of {len(MUTATIONS)} mutations seen RED ===")
    print(f"    SURVIVED={len(survived)}  NOT PROVEN={len(not_proven)}")
    for item in survived:
        print(f"  SURVIVED: {item}")
    for item in not_proven:
        print(f"  NOT PROVEN: {item}")
    if survived or not_proven:
        return 1
    print("  every mutation was seen RED; every file was restored byte-exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
