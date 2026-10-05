"""Slice 7 mutation harness. Run from the repo root:

    PYTHONPATH=src python tests/_mutate_slice7.py

Each mutation disables one guard added in Slice 7, runs the tests that are
supposed to fail, and restores the file in a `finally`. Nothing is left patched,
and the control re-runs the affected suites to prove the restore was clean.

It inherits the two safety fixes that the Slice 6 harness needed:

1. **Binary I/O only.** `read_text`/`write_text` translate newlines and silently
   turned CRLF files into LF, which made every "restore" a lie. Anchors are bytes
   and the restore is verified against a pre-mutation md5.
2. **A missing or non-unique anchor is a hard failure.** A skipped mutation was
   once counted as evidence, which is how the Slice 6 record came to claim 11 of
   11 when it was 10 of 11.

And it has a third of its own, added 5 October 2026 after it was caught reporting
two kills that never happened:

3. **A kill is a failed test, and any other non-zero exit is NOT PROVEN.** The
   harness used to read the exit code alone, which admits two failures that both
   look like evidence, and both were live here:

   * **M9 ran nothing.** Slice 7b stage 2 split
     `TestTheRecordSurvivesAProcessRestart` into `...OnTheLocalFile` and
     `...OnTheServer` and left M9 pointing at the old name. pytest answered
     `ERROR: not found` and exited 4, which counted as RED.
   * **M6 never parsed.** Its anchor covered the opening line of a three-line
     call, so the replacement left two lines dangling and `service.py` became a
     `SyntaxError`. `test_service.py` failed to collect, pytest printed
     `1 error`, and that also counted as RED.

   So the record said 10 of 10 while two of the ten had never been tested. A
   syntax-breaking mutation is the worse of the two, because it looks like a
   vigorous failure rather than a missing one. Anchors were already checked for
   existence and uniqueness; the verdict now requires a test to have actually
   failed, which catches a stale selector and a broken file at once.

Two mutations here target **test files**, which is unusual and deliberate: the
secret scanner is itself a guard, and a guard that cannot be seen failing is not
one. Disabling it must turn its own self-test red.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "carerelay"
TESTS = ROOT / "tests"


def run(selectors: list[str]) -> tuple[int, str]:
    """One pytest run, returning the exit code and everything it printed.

    **The output is returned as well as the code, because the code alone cannot
    tell a killed mutation from a selector that matched nothing.** pytest exits
    **4** for a usage error, which includes a node id it cannot find, and a
    harness that reads any non-zero as RED reports that as a kill. That is not a
    hypothetical: M9 below was renamed out from under by Slice 7b stage 2 and
    reported RED for two days on the strength of `ERROR: not found`.
    """
    cmd = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", *selectors]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tail = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    print("   ", tail[-1] if tail else "(no output)")
    return proc.returncode, proc.stdout + proc.stderr


def _b(text: str) -> bytes:
    """An anchor written with `\\n`, matched against a CRLF file.

    Kept for the `src/` files, which are all CRLF. Test files are not: at least
    one predates the convention and is LF, so an anchor for a test file has to be
    resolved against what the file actually is. `resolve_anchor` does that.
    """
    return text.replace("\n", "\r\n").encode("utf-8")


def resolve_anchor(text: bytes, data: bytes) -> bytes:
    """The form that actually exists in the file.

    Anchors are written with `_b(...)` which converts `\\n` to `\\r\\n` for
    the CRLF source files.  When the target file is LF (e.g. an older test
    file), the CRLF form will not match, so we fall back to the LF form.
    """
    if text in data:
        return text
    lf = text.replace(b"\r\n", b"\n")
    if lf in data:
        return lf
    return text


#: (label, filename, anchor text, replacement text, selectors). Anchors are
#: written as text and resolved against the file's real line endings by
#: `resolve_anchor`, not hard-coded to CRLF.
MUTATIONS: list[tuple[str, str, str, str, list[str]]] = [
    (
        "M1  the bearer-token dependency is bypassed entirely",
        "api.py",
        _b("    if not auth_is_armed():\n        return\n"),
        _b("    return  # mutated: no credential is ever checked\n"),
        [
            "tests/test_api.py::TestAuthIsFailClosed",
            "tests/test_api.py::TestEveryApiRouteIsGuarded",
        ],
    ),
    (
        "M2  armed with no token serves the route instead of refusing",
        "api.py",
        _b("    if not token:\n        raise _misconfigured()\n"),
        _b("    if not token:\n        return  # mutated: no token, no guard\n"),
        ["tests/test_api.py::TestAuthIsFailClosed"],
    ),
    (
        "M3  a wildcard CORS origin is honoured",
        "api.py",
        _b('    return [origin for origin in origins if origin != "*"]\n'),
        _b("    return origins  # mutated: wildcard accepted\n"),
        ["tests/test_api.py::TestCorsIsLocked"],
    ),
    (
        "M4  CORS is decided once at import instead of per request",
        "api.py",
        _b("    origin = request.headers.get(\"origin\", \"\").strip()\n"),
        _b("    origin = \"https://carerelay.vercel.app\"  # mutated: allow-list ignored\n"),
        ["tests/test_api.py::TestCorsIsLocked"],
    ),
    (
        "M5  policy version registration goes back to a plain INSERT",
        "state.py",
        _b("        ).fetchone()\n        if existing is not None:\n"),
        _b("        ).fetchone()\n        if False:  # mutated: NF1 returns\n"),
        ["tests/test_state.py::TestPolicyVersionRegistrationIsIdempotent"],
    ),
    (
        "M6  transcript_confirmed is asserted from any supplied id (NF4 returns)",
        "service.py",
        # The anchor spans the **whole call expression**, and the first version of
        # it did not. It matched only the opening line, so the replacement left
        # `episode_id, transcript_confirmation_id, confirmed_text` and the closing
        # `),` dangling, which is a SyntaxError. `test_service.py` then failed to
        # collect, pytest printed `1 error`, and a harness reading any non-zero
        # exit as a kill reported M6 RED. It had never run a test. Found on
        # 5 October 2026 only because the verdict rule changed to require an
        # actual failed test; see the docstring's third safety fix.
        _b(
            "            transcript_confirmed=self._verified_confirmation(\n"
            "                episode_id, transcript_confirmation_id, confirmed_text\n"
            "            ),\n"
        ),
        _b(
            "            transcript_confirmed=transcript_confirmation_id is not None,  # mutated\n"
        ),
        ["tests/test_service.py::TestTranscriptConfirmedIsVerified"],
    ),
    (
        "M7  the hint route constructs its enums directly again (NF2 returns)",
        "service.py",
        _b(
            "        level = rules.require_hint_level(hint_level)\n"
            "        event_kind = rules.require_hint_event_kind(kind)\n"
        ),
        _b("        level = HintLevel(hint_level)\n        event_kind = HintEventKind(kind)\n"),
        [
            "tests/test_api.py::TestMalformedEnumsAreTypedRefusals",
            "tests/test_domain.py::TestCallersuppliedEnumsAreRefusedNotConstructed",
        ],
    ),
    (
        "M8  the restatement path constructs its mode directly again",
        "service.py",
        _b(
            "        level = rules.require_hint_level(hint_level)\n"
            "        mode = rules.require_input_mode(input_mode)\n"
        ),
        _b("        level = HintLevel(hint_level)\n        mode = InputMode(input_mode)\n"),
        ["tests/test_api.py::TestMalformedEnumsAreTypedRefusals"],
    ),
    (
        "M9  the append-only triggers are never created",
        "state.py",
        _b("    for table in APPEND_ONLY_TABLES:\n"),
        _b("    for table in ():  # mutated: no triggers\n"),
        # The local-file class only, and that is a correction rather than a
        # narrowing. M9 mutates `state.py`, which is the SQLite schema; the
        # Postgres store builds its own triggers from `postgres_schema.py` and
        # would stay green. Naming both classes would have made this mutation
        # look weaker than it is and the green half would have been noise.
        #
        # This selector read `::TestTheRecordSurvivesAProcessRestart` until
        # 5 October 2026. Slice 7b stage 2 split that one class into
        # `...OnTheLocalFile` and `...OnTheServer` and did not update this line,
        # so pytest answered `ERROR: not found` and exited 4, and the harness
        # counted that as RED. M9 was therefore unverified from the moment stage
        # 2 landed, while the record still said 10 of 10.
        ["tests/test_deployment.py::TestTheRecordSurvivesAProcessRestartOnTheLocalFile"],
    ),
    (
        "M10 the secret scanner reports nothing",
        "test_boundaries.py",
        _b("    return sorted(set(found))\n"),
        _b("    return []  # mutated: the scanner is blind\n"),
        [
            "tests/test_boundaries.py::TestSecretsNeverReachASerializedSurface",
            "tests/test_boundaries.py::TestNoSecretIsCommitted",
            "tests/test_deployment.py::TestTheDeploymentArtefactsAreHonest",
        ],
    ),
]

CONTROL = [
    "tests/test_api.py",
    "tests/test_service.py::TestTranscriptConfirmedIsVerified",
    "tests/test_state.py::TestPolicyVersionRegistrationIsIdempotent",
    "tests/test_domain.py::TestCallersuppliedEnumsAreRefusedNotConstructed",
    "tests/test_deployment.py",
    "tests/test_boundaries.py",
]


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _endings(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    lone = data.count(b"\n") - crlf
    return f"CRLF={crlf} loneLF={lone}"


def _resolve(filename: str) -> pathlib.Path:
    return TESTS / filename if filename.startswith("test_") else SRC / filename


def main() -> int:
    touched = sorted({_resolve(name) for _, name, _, _, _ in MUTATIONS})
    pristine: dict[pathlib.Path, bytes] = {path: path.read_bytes() for path in touched}
    baseline = {path: _md5(data) for path, data in pristine.items()}
    for path, data in pristine.items():
        print(f"[BASE] {path.name}: md5={baseline[path]} {_endings(data)}")

    failures: list[str] = []
    red = 0
    not_proven = 0

    for name, filename, old_text, new_text, selectors in MUTATIONS:
        path = _resolve(filename)
        original = path.read_bytes()
        old = resolve_anchor(old_text, original)
        new = resolve_anchor(new_text, original)

        if old not in original:
            print(f"[FAIL] {name}: anchor not found in {filename}")
            failures.append(f"{name} (anchor not found, mutation NOT applied)")
            continue
        if original.count(old) != 1:
            print(
                f"[FAIL] {name}: anchor appears {original.count(old)} times in "
                f"{filename}; a mutation must be unambiguous"
            )
            failures.append(f"{name} (anchor not unique, mutation NOT applied)")
            continue

        try:
            path.write_bytes(original.replace(old, new, 1))
            print(f"[RUN ] {name}")
            code, output = run(selectors)
            # **A kill is a failed test, and nothing else counts as one.** Reading
            # any non-zero exit as a kill admits two failures that both look like
            # evidence. pytest exits 4 on a node id it cannot find, so a renamed
            # test class reports RED while running nothing at all: that was M9,
            # orphaned when Slice 7b stage 2 split its class in two. And a
            # mutation that breaks the target file's syntax produces a collection
            # *error*, which is also non-zero and also says nothing about the
            # guard: that was M6, whose anchor covered one line of a three-line
            # call. Both were live in this harness and both reported RED.
            if re.search(r"\d+ failed", output):
                red += 1
            elif code == 0:
                print("    *** SURVIVED: the guard has no teeth ***")
                failures.append(f"{name} (SURVIVED)")
            else:
                not_proven += 1
                reason = (
                    "the selector matched no test"
                    if code == 4 or "no tests ran" in output
                    else f"exit {code} with no test failing, so a collection error"
                )
                print(f"    *** NOT PROVEN: {reason} ***")
                failures.append(f"{name} ({reason}, NOT PROVEN)")
        finally:
            path.write_bytes(original)
            if _md5(path.read_bytes()) != _md5(original):
                print(f"    *** RESTORE MISMATCH in {filename}: ABORTING ***")
                failures.append(f"{name} (restore mismatch)")
                path.write_bytes(pristine[path])
                break

    print("\n[CONTROL] restored tree:")
    for path in pristine:
        if path.read_bytes() != pristine[path]:
            print(
                f"    *** {path.name} does not match its pre-run bytes "
                f"(now {_md5(path.read_bytes())}, expected {baseline[path]}) ***"
            )
            failures.append(f"control: {path.name} not restored")
            path.write_bytes(pristine[path])
    if not failures:
        code, _ = run(CONTROL)
        if code != 0:
            print("    *** CONTROL FAILED: a file was not restored ***")
            failures.append("control")

    print(
        f"\n=== result: {red} RED, {not_proven} NOT PROVEN, "
        f"of {len(MUTATIONS)} mutations ==="
    )
    if failures:
        for item in failures:
            print(f"  PROBLEM: {item}")
        return 1
    print("  every mutation was seen RED; every file restored byte-exact; tree green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
