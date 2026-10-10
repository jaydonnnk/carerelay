"""Mutation check for Slice 12. The ledger, the options read, and the five
fault assertions.

Run: PYTHONPATH=src python tests/_mutate_slice12.py

**Two lists, and the difference matters.** `MUTATIONS` are the claims that must
have teeth: each is disabled once, only the test that owns it is selected, and a
real failure is required. `PROBES` are the five fault assertions, which are
disabled the same way but whose outcome is *reported* rather than required. That
split exists because four of the five cannot be driven false by any sequence
this build permits, and a harness that folded them into the RED total would
record coverage that does not exist. This is the Slice 11 lesson applied to a
new list rather than to the same one.

Three conventions carried over from the Slice 8 to Slice 11 harnesses, each of
which cost this project a wrong answer once:

* **A RED is read from a real test failure, never from the exit code alone.**
  pytest exits 4 for a selector that resolves to nothing, so a harness reading
  "non-zero means RED" reports a kill for a test that never ran.
* **The count of tests that ran comes off the progress characters**, and pytest
  right-pads that field, so the padding is stripped before counting.
* **The anchor is matched in the file's own newline convention.** The repository
  is CRLF, so an LF-written anchor silently fails to apply and a guard that was
  never touched is recorded as SURVIVED.

Every file is restored byte-identically and its cached bytecode purged, because
a `.pyc` compiled while a mutation was live can outlive the restore. The run
also sets `PYTHONDONTWRITEBYTECODE=1` for the children.
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

SERVICE = "src/carerelay/service.py"
API = "src/carerelay/api.py"

TARGETS = {
    SERVICE: REPO / "src" / "carerelay" / "service.py",
    API: REPO / "src" / "carerelay" / "api.py",
}

LEDGER = "tests/test_ledger.py"
ORIGIN = f"{LEDGER}::TestLedgerCarriesTheFailureEventOrigin::test_a_transition_keeps_its_origin"
NOWRITE = f"{LEDGER}::TestTheLedgerNeverWrites::test_reading_the_ledger_does_not_record_an_expiry"
DWELL = f"{LEDGER}::TestLedgerCarriesDwellSeconds::test_a_hint_event_keeps_its_dwell_time"
FIVE = f"{LEDGER}::TestTheFaultAssertions::test_all_five_are_named_and_carry_evidence"
LABEL = f"{LEDGER}::TestLedgerCarriesTheTwoAxes::test_the_simulated_label_is_inside_the_json"
DISPLAY = f"{LEDGER}::TestPermittedOptions::test_every_route_carries_the_policy_display_text"
ROUTESET = f"{LEDGER}::TestPermittedOptions::test_the_route_set_is_exactly_the_policy_set"
NOTFOUND = f"{LEDGER}::TestLedgerCarriesTheTwoAxes::test_an_unknown_episode_is_404"
I3FALSE = f"{LEDGER}::TestTheFaultAssertions::test_i3_reports_false_when_two_terminal_transitions_exist"

ALIAS_SAME = f"{LEDGER}::TestTheLedgerAliasUnderTheGuardedPrefix::test_the_alias_serves_the_same_body_as_the_canonical_path"
ALIAS_GUARD = f"{LEDGER}::TestTheLedgerAliasUnderTheGuardedPrefix::test_the_alias_is_guarded_when_auth_is_armed"
ALIAS_404 = f"{LEDGER}::TestTheLedgerAliasUnderTheGuardedPrefix::test_the_alias_404s_for_an_unknown_episode"
ALIAS_NOTWIN = f"{LEDGER}::TestTheLedgerAliasUnderTheGuardedPrefix::test_the_permitted_route_surface_has_no_twin_outside_the_guard"

#: (label, target, anchor, replacement, selectors). Every one must be RED.
MUTATIONS: list[tuple[str, str, bytes, bytes, list[str]]] = [
    (
        "L1  a transition loses its failure-event origin",
        SERVICE,
        b'                            "kind": t.kind.value,\n'
        b'                            "origin": t.origin.value,\n'
        b'                            "recorded_at": t.recorded_at.isoformat(),\n',
        b'                            "kind": t.kind.value,\n'
        b'                            "recorded_at": t.recorded_at.isoformat(),\n',
        [ORIGIN],
    ),
    (
        "L2  the ledger runs the expiry read-path and becomes a writer",
        SERVICE,
        b"        snapshot = self._store.load_snapshot(episode_id)\n"
        b"        closure = rules.derive_closure(snapshot, now_utc)\n"
        b"\n"
        b"        origin_set: set[str] = set()\n",
        b"        snapshot = self._store.load_snapshot(episode_id)\n"
        b"        closure = rules.derive_closure(snapshot, now_utc)\n"
        b"        if (\n"
        b"            snapshot.disposition is not None\n"
        b"            and snapshot.expiry_event_id is None\n"
        b"            and closure.closure is ClosureState.EXPIRED_UNRESOLVED\n"
        b"        ):\n"
        b"            self._store.record_expiry_once(\n"
        b"                episode_id, snapshot.disposition.version, now_utc\n"
        b"            )\n"
        b"            snapshot = self._store.load_snapshot(episode_id)\n"
        b"            closure = rules.derive_closure(snapshot, now_utc)\n"
        b"\n"
        b"        origin_set: set[str] = set()\n",
        [NOWRITE],
    ),
    (
        "L3  a hint row loses its dwell time",
        SERVICE,
        b'                "hint_level": h.level.value,\n'
        b'                "kind": h.kind.value,\n'
        b'                "dwell_seconds": h.dwell_seconds,\n',
        b'                "hint_level": h.level.value,\n'
        b'                "kind": h.kind.value,\n',
        [DWELL],
    ),
    (
        "L4  the fault assertions are not reported at all",
        SERVICE,
        b"        return (i1, i2, i3, i4, i5)\n",
        b"        return ()\n",
        [FIVE],
    ),
    (
        "L5  the simulated label is dropped from the ledger",
        SERVICE,
        b"            simulated=closure.simulated,\n",
        b"            simulated=False,\n",
        [LABEL],
    ),
    (
        "L6  the options read renders the raw route id",
        SERVICE,
        b"            display = self._policy_text.route_display_by_id.get(route_id)\n",
        b"            display = route_id  # MUTANT: the raw id reaches a surface\n",
        [DISPLAY],
    ),
    (
        "L7  the options read drops all but one permitted route",
        SERVICE,
        b"        for route_id in sorted(self._policy.permitted_route_ids):\n",
        b"        for route_id in sorted(self._policy.permitted_route_ids)[:1]:\n",
        [ROUTESET],
    ),
    (
        "L8  the ledger route loses its 404 guard",
        API,
        b"    if episode_id not in _OPEN_EPISODES:\n"
        b'        raise HTTPException(status_code=404, detail="episode not found")\n'
        b"    with _DB_LOCK:\n"
        b"        return service.project_ledger(episode_id).as_dict()\n",
        b"    with _DB_LOCK:\n"
        b"        return service.project_ledger(episode_id).as_dict()\n",
        [NOTFOUND],
    ),
    (
        "L9  the /ledger alias is not registered",
        API,
        b'@app.get("/ledger/{episode_id}", tags=["ledger"])\n',
        b"",
        [ALIAS_SAME, ALIAS_GUARD, ALIAS_404],
    ),
    (
        "L10 the /ledger prefix stops being guarded",
        API,
        b'GUARDED_PREFIXES: tuple[str, ...] = ("/api", "/ledger")',
        b'GUARDED_PREFIXES: tuple[str, ...] = ("/api",)',
        [ALIAS_GUARD, ALIAS_NOTWIN],
    ),
]

#: (label, target, anchor, replacement, selectors). Reported, never required.
#: Each one forces a fault assertion to `True` and asks whether any test in the
#: suite can tell the difference. A SURVIVED probe means the assertion is a
#: display field today, not a proof, and the slice record says which are which.
PROBES: list[tuple[str, str, bytes, bytes, list[str]]] = [
    (
        "P1  I1 forced true",
        SERVICE,
        b"        monotonic = all(\n"
        b"            later >= earlier\n"
        b"            for (_, earlier), (_, later) in zip(deadlines, deadlines[1:])\n"
        b"        )\n",
        b"        monotonic = True  # PROBE\n",
        [LEDGER],
    ),
    (
        "P2  I2 forced true",
        SERVICE,
        b"            holds=(not closes) or documented_evidence > 0 or has_acceptance,\n",
        b"            holds=True,  # PROBE\n",
        [LEDGER],
    ),
    (
        "P3  I3 forced true",
        SERVICE,
        b"            holds=all(count <= 1 for count in terminal_counts.values()),\n",
        b"            holds=True,  # PROBE\n",
        [I3FALSE],
    ),
    (
        "P4  I4 forced true",
        SERVICE,
        b"            holds=(not resolved) or closure.action_owner_id is not None,\n",
        b"            holds=True,  # PROBE\n",
        [LEDGER],
    ),
    (
        "P5  I5 forced true",
        SERVICE,
        b"            holds=not failed_without_row,\n",
        b"            holds=True,  # PROBE\n",
        [LEDGER],
    ),
]


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _newline(data: bytes) -> bytes:
    crlf = data.count(b"\r\n")
    lone = data.count(b"\n") - crlf
    return b"\r\n" if crlf > lone else b"\n"


def _conform(data: bytes, newline: bytes) -> bytes:
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


def _apply(
    label: str,
    target: str,
    anchor: bytes,
    replacement: bytes,
    selectors: list[str],
    baselines: dict[str, bytes],
) -> tuple[str, int, int, list[str]]:
    """Run one mutation and return (verdict, ran, failed, failing ids)."""
    path = TARGETS[target]
    original = baselines[target]
    newline = _newline(original)
    real_anchor = _conform(anchor, newline)
    real_replacement = _conform(replacement, newline)

    if real_anchor not in original:
        print(f"[FAIL] {label}: anchor not found in {target}")
        return "NOT PROVEN", 0, 0, []
    if original.count(real_anchor) != 1:
        print(f"[FAIL] {label}: anchor appears {original.count(real_anchor)} times")
        return "NOT PROVEN", 0, 0, []

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
        return "SURVIVED", ran, failed, ids
    if ran == 0 or failed == 0:
        return "NOT PROVEN", ran, failed, ids
    return "RED", ran, failed, ids


def main() -> int:
    baselines = {name: path.read_bytes() for name, path in TARGETS.items()}
    for name, data in baselines.items():
        crlf = data.count(b"\r\n")
        lone = data.count(b"\n") - crlf
        print(f"[BASE] {name:32} md5={_md5(data)} CRLF={crlf} loneLF={lone}")

    unresolved: list[str] = []
    for label, _target, _anchor, _replacement, selectors in MUTATIONS + PROBES:
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
    print(
        f"[PRE ] all {len(MUTATIONS) + len(PROBES)} mutations resolve to at least "
        "one test\n"
    )

    red = 0
    survived: list[str] = []
    not_proven: list[str] = []
    for label, target, anchor, replacement, selectors in MUTATIONS:
        verdict, _ran, _failed, _ids = _apply(
            label, target, anchor, replacement, selectors, baselines
        )
        if verdict == "RED":
            red += 1
        elif verdict == "SURVIVED":
            print("       *** SURVIVED: the claim has no teeth ***")
            survived.append(label)
        else:
            print("       *** NOT PROVEN: nothing actually failed ***")
            not_proven.append(label)

    print("\n[PROBE] the five fault assertions, forced true one at a time:")
    falsifiable: list[str] = []
    display_only: list[str] = []
    for label, target, anchor, replacement, selectors in PROBES:
        verdict, _ran, _failed, _ids = _apply(
            label, target, anchor, replacement, selectors, baselines
        )
        if verdict == "RED":
            print("       FALSIFIABLE today: a test can tell the difference")
            falsifiable.append(label)
        else:
            print("       NOT FALSIFIABLE today: no sequence in this build drives it")
            display_only.append(label)

    print()
    damaged = [
        name for name, path in TARGETS.items() if path.read_bytes() != baselines[name]
    ]
    if damaged:
        for name in damaged:
            print(f"[FAIL] restore is not byte-identical: {name}")
        return 1
    for name, path in TARGETS.items():
        print(f"[CTRL] {name:32} restored, md5={_md5(path.read_bytes())}")

    print(f"\n=== result: {red} of {len(MUTATIONS)} mutations seen RED ===")
    print(f"    SURVIVED={len(survived)}  NOT PROVEN={len(not_proven)}")
    for item in survived:
        print(f"  SURVIVED: {item}")
    for item in not_proven:
        print(f"  NOT PROVEN: {item}")
    print(
        f"    fault assertions falsifiable today: {len(falsifiable)} of "
        f"{len(PROBES)}  ({', '.join(falsifiable) or 'none'})"
    )
    print(
        f"    fault assertions display-only:      {len(display_only)} of "
        f"{len(PROBES)}  ({', '.join(display_only) or 'none'})"
    )
    if survived or not_proven:
        return 1
    print("  every mutation was seen RED; every file was restored byte-exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
