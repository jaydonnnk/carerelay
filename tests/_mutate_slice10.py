"""Mutation check for the Slice 10 guards. The Closure Contract in full.

Run: PYTHONPATH=src python tests/_mutate_slice10.py

Slice 10 builds the acceptance write, the expiry read-path and the derived
patient projection. The defects worth injecting are the ones that let the
product report something it cannot support:

* an expiry event that is never recorded, so an overdue episode is reported
  without the fact that the deadline went by;
* an expiry event recorded **before** the deadline, which tells a patient their
  window is gone while they still have time;
* an acceptance that becomes evidence of care, which is the whole product thesis
  (`03-program-design.md` section 3) failing in one line;
* an accepting party that is not checked, so the ledger carries a name no screen
  can render (I4);
* a closure rendering served with the wrong approved words, a rendering branch
  made unreachable, an unworded human path printed rather than refused, or the
  pre-assessment fallback removed;
* the simulated label dropped from the serialized patient surface (D11), or the
  expired copy losing the deadline or the named route (copy rules 4 and 5).

Three conventions carried over from the Slice 8 and Slice 9 harnesses, each of
which cost this project a wrong answer once:

* **A RED is read from a real test failure, never from the exit code alone.**
  pytest exits 4 for a selector that resolves to nothing, and a harness reading
  "non-zero means RED" reports a kill for a test that never ran.
* **The count of tests that ran comes off the progress characters**, and pytest
  right-pads that field, so the padding is stripped before counting.
* **The anchor is matched in the file's own newline convention.** The repository
  is CRLF, so an LF-written anchor silently fails to apply and a guard that was
  never touched is recorded as SURVIVED.

Every file is restored byte-identically and its cached bytecode purged, because a
`.pyc` compiled while a mutation was live can outlive the restore.

**One mutation is deliberately absent.** Removing the
`snapshot.expiry_event_id is None` short-circuit from `project_patient` SURVIVES,
and that is correct: `state.record_expiry_once` already returns `False` for a
version that has an event, so the short-circuit saves a redundant write
transaction and changes no observable value. A guard that no test can see fail is
not a guard, so it is documented here rather than counted.
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
SERVICE = "src/carerelay/service.py"
API = "src/carerelay/api.py"
PRESENTATION = "src/carerelay/presentation.py"

TARGETS = {
    RULES: REPO / "src" / "carerelay" / "domain" / "rules.py",
    SERVICE: REPO / "src" / "carerelay" / "service.py",
    API: REPO / "src" / "carerelay" / "api.py",
    PRESENTATION: REPO / "src" / "carerelay" / "presentation.py",
}

DOMAIN = "tests/test_domain.py"
APITESTS = "tests/test_api.py"

EXPIRY = f"{APITESTS}::TestExpiryReadPath"
LABELS = f"{APITESTS}::TestSerializedPatientAndLedgerLabels"
ACCEPT = f"{APITESTS}::TestAcceptanceClosesTheHandoffAndNeverEvidencesCare"
EPISODE_CONTRACT = f"{APITESTS}::TestEpisodeContract"
TRAVELS = f"{APITESTS}::TestSimulatedLabelTravelsWithTheData"
OWNER = f"{DOMAIN}::TestOwnerValidation"

#: (label, target, anchor, replacement, selectors)
MUTATIONS: list[tuple[str, str, bytes, bytes, list[str]]] = [
    (
        "E1  the expiry read-path never records the event",
        SERVICE,
        b"            and closure.closure is ClosureState.EXPIRED_UNRESOLVED\n",
        b"            and False\n",
        [
            f"{EXPIRY}"
            "::test_the_first_read_after_an_unresolved_deadline_records_expiry_once"
        ],
    ),
    (
        "E2  the expiry read-path fires before the deadline",
        SERVICE,
        b"            and closure.closure is ClosureState.EXPIRED_UNRESOLVED\n",
        b"            and True\n",
        [
            f"{EXPIRY}"
            "::test_before_the_deadline_the_read_returns_the_unresolved_screen"
        ],
    ),
    (
        "C1  an acceptance becomes evidence of care",
        RULES,
        b"    care_evidenced = evidence is EvidenceLevel.DOCUMENTED\n",
        b"    care_evidenced = (\n"
        b"        evidence is EvidenceLevel.DOCUMENTED\n"
        b"        or snapshot.human_acceptance_id is not None\n"
        b"    )\n",
        [f"{ACCEPT}::test_acceptance_is_not_care"],
    ),
    (
        "C2  the acceptance response claims care was evidenced",
        API,
        b"        care_evidenced=outcome.closure.care_evidenced,\n",
        b"        care_evidenced=True,\n",
        [f"{ACCEPT}::test_acceptance_is_not_care"],
    ),
    (
        "C3  an acceptance is taken before there is a plan to accept",
        SERVICE,
        b"        if snapshot.disposition is None:\n"
        b"            raise NoDispositionYet(\n"
        b'                f"episode {episode_id!r} has no disposition, so there is no "\n'
        b'                "handoff obligation for an acceptance to close"\n'
        b"            )\n",
        b"        if False:\n"
        b"            raise NoDispositionYet(\n"
        b'                f"episode {episode_id!r} has no disposition, so there is no "\n'
        b'                "handoff obligation for an acceptance to close"\n'
        b"            )\n",
        [f"{ACCEPT}::test_an_acceptance_before_a_plan_is_a_409"],
    ),
    (
        "O1  an unknown accepting party is not refused",
        RULES,
        b"    if owner_id not in permitted_owner_ids:\n"
        b"        raise UnpermittedOwnerId(owner_id, sorted(permitted_owner_ids))\n",
        b"    if False:\n"
        b"        raise UnpermittedOwnerId(owner_id, sorted(permitted_owner_ids))\n",
        [
            f"{OWNER}::test_an_unknown_owner_is_refused",
            f"{ACCEPT}::test_an_unknown_party_is_refused_not_recorded",
        ],
    ),
    (
        "P1  the patient projection drops the simulated label",
        PRESENTATION,
        b'            "fixture_label": self.fixture_label,\n',
        b'            "fixture_label": "",\n',
        [
            f"{LABELS}::test_serialized_patient_and_ledger_labels",
            f"{TRAVELS}::test_label_is_inside_the_serialized_projection",
        ],
    ),
    (
        "P2  the expired copy loses the deadline",
        RULES,
        b'            f"It is past {deadline_display}. Please go now.",\n',
        b'            "It is past. Please go now.",\n',
        [
            f"{EXPIRY}::test_the_expired_screen_keeps_the_deadline_and_names_the_route",
            f"{LABELS}::test_serialized_patient_and_ledger_labels",
        ],
    ),
    (
        "P3  the expired copy loses the named route",
        RULES,
        b'            f"Call {route_display}. They can help from here.",\n',
        b'            "Call someone. They can help from here.",\n',
        [f"{EXPIRY}::test_the_expired_screen_keeps_the_deadline_and_names_the_route"],
    ),
    (
        "D1  the care-documented branch renders the agreed lines",
        RULES,
        b"        if closure.care_evidenced:\n",
        b"        if False:\n",
        [
            f"{DOMAIN}::TestPatientLines"
            "::test_the_resolved_screen_renders_the_care_documented_lines"
        ],
    ),
    (
        "D2  the someone-agreed branch renders the care-documented lines",
        RULES,
        b"        if closure.care_evidenced:\n",
        b"        if True:\n",
        [
            f"{DOMAIN}::TestPatientLines"
            "::test_the_resolved_screen_renders_the_someone_agreed_lines"
        ],
    ),
    (
        "E1  the escalated rendering branch is unreachable",
        RULES,
        b"    if closure.closure is ClosureState.ESCALATED_TO_HUMAN:\n",
        b"    if False:\n",
        [
            f"{DOMAIN}::TestPatientLines"
            "::test_the_escalated_screen_names_the_human_path_and_the_deadline",
            f"{APITESTS}::TestClosureRenderingsThroughTheDerivedRoute"
            "::test_an_escalation_renders_the_handed_to_a_human_lines",
        ],
    ),
    (
        "E2  the escalated line 1 loses the human path's name",
        RULES,
        b'            f"We have passed this to {human_path_display}.",\n',
        b'            "We have passed this to someone.",\n',
        [
            f"{DOMAIN}::TestPatientLines"
            "::test_the_escalated_screen_names_the_human_path_and_the_deadline",
            f"{APITESTS}::TestClosureRenderingsThroughTheDerivedRoute"
            "::test_an_escalation_renders_the_handed_to_a_human_lines",
        ],
    ),
    (
        "H1  an unworded human path is printed rather than refused",
        RULES,
        b"        human_path_display = policy_text.route_display_by_id.get(closure.action_owner_id)\n"
        b"        if human_path_display is None:\n"
        b"            raise MissingDisplayText(closure.action_owner_id)\n",
        b'        human_path_display = closure.action_owner_id or ""\n',
        [
            f"{DOMAIN}::TestPatientLines"
            "::test_an_escalated_human_path_with_no_approved_display_is_refused"
        ],
    ),
    (
        "A1  the derived route serves the pre-assessment placeholder over a closed episode",
        API,
        b"    return PatientProjection(**surface.as_dict())\n",
        b"    return PatientProjection(\n"
        b'        **{**surface.as_dict(), "lines": list(fixture.demo_lines().as_tuple())}\n'
        b"    )\n",
        [
            f"{APITESTS}::TestClosureRenderingsThroughTheDerivedRoute"
            "::test_documented_evidence_renders_the_care_documented_lines",
            f"{APITESTS}::TestClosureRenderingsThroughTheDerivedRoute"
            "::test_an_escalation_renders_the_handed_to_a_human_lines",
        ],
    ),
    (
        "R2  the pre-assessment fallback is removed",
        API,
        b"        except NoDispositionToRender:\n"
        b"            lines = fixture.demo_lines()\n",
        b"        except NoDispositionToRender:\n"
        b'            raise HTTPException(status_code=409, detail="no plan yet")\n',
        [EPISODE_CONTRACT],
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

    Python validates a `.pyc` against the source's mtime and size only, never its
    content, so a `.pyc` written while a mutation was live can be imported long
    after the source is restored. Restoring bytes is not enough.
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
        line.split(" - ")[0].replace("FAILED ", "").strip()
        for line in stdout.splitlines()
        if line.startswith("FAILED ")
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
