"""Slice 6 mutation harness. Run from the repo root:

    PYTHONPATH=src python tests/_mutate_slice6.py

Each mutation disables one guard, runs the tests that are supposed to fail, and
restores the file in a `finally`. Nothing is left patched. The control at the
end re-runs the affected suites to prove the restore was clean.

**Fixed 3 October 2026 after a verification check found the harness was unsafe.**
Two defects, both now closed:

1. The harness used `Path.read_text()` / `Path.write_text()`, which translate
   newlines. `read_text()` turns CRLF into LF in memory, so `write_text()` wrote
   a **pure-LF** file back over a CRLF file: every mutation silently converted
   its target to LF, and the "restore" was not byte-exact even when it ran. All
   file I/O is now **binary**, anchors are **bytes**, and the restore is verified
   against a pre-mutation md5.
2. An anchor that did not match was reported as `[SKIP]` and the mutation was
   silently counted as "not RED". M11's anchor did not match the CRLF file, so
   the record's "11 of 11 RED" was really 10 of 11. A skipped mutation is now a
   **hard failure**, and its anchor must match, or the run exits non-zero.

Every mutation now: snapshots bytes + md5, asserts the anchor is present and
unique, patches in memory, writes, runs, restores the exact bytes, and asserts
the md5 matches. A mismatch aborts the whole run. The final control also asserts
each mutated file's md5 equals its pre-run value.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "carerelay"


def run(selectors: list[str]) -> int:
    cmd = [
        sys.executable, "-m", "pytest", "-o", "addopts=", "-q", *selectors
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        # A `.pyc` compiled from a mutated file outlives the restore, so
        # no child process may write one.
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    tail = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    print("   ", tail[-1] if tail else "(no output)")
    return proc.returncode


def _b(text: str) -> bytes:
    """An anchor written with `\\n`, matched against a CRLF file.

    The anchors below are written naturally with `\\n`; every target file here is
    CRLF, so the literal is normalised to CRLF once, in one place, instead of
    being hand-escaped at each of the eleven call sites.
    """
    return text.replace("\n", "\r\n").encode("utf-8")


MUTATIONS: list[tuple[str, str, bytes, bytes, list[str]]] = [
    (
        "M6  tool surface does not recheck the route",
        "tools.py",
        _b(
            "            rules.validate_route(route_id, self._policy.permitted_route_ids)\n"
        ),
        _b("            None  # mutated: route no longer rechecked\n"),
        ["tests/test_coordinator.py::TestToolRechecksAuthorisationConsentAndKey"],
    ),
    (
        "M7  tool surface does not resolve the attempt key server-side",
        "tools.py",
        _b("        attempt = self._store.get_attempt_by_key(attempt_key)\n"),
        _b("        attempt = None  # mutated\n"),
        ["tests/test_coordinator.py::TestToolRechecksAuthorisationConsentAndKey"],
    ),
    (
        "M8  tool surface does not check the key opened this route",
        "tools.py",
        _b("        if attempt.route_id != route_id:\n"),
        _b("        if False:  # mutated\n"),
        ["tests/test_coordinator.py::TestToolRechecksAuthorisationConsentAndKey"],
    ),
    (
        "M9  tool surface does not recheck consent",
        "tools.py",
        _b(
            '        self._recheck_consent(episode_id, "submit_simulated_request", now_utc)\n'
        ),
        _b("        pass  # mutated: consent not rechecked\n"),
        ["tests/test_coordinator.py::TestToolRechecksAuthorisationConsentAndKey"],
    ),
    (
        "M10 the provider stops labelling itself simulated",
        "simulated_provider.py",
        _b("    simulated = True\n"),
        _b("    simulated = False\n"),
        [
            "tests/test_coordinator.py::TestTheProviderIsDeterministicAndLabelled",
            "tests/test_service.py::TestActionPath",
            "tests/test_service.py::TestCallbackReceipts",
        ],
    ),
    (
        "M11 the idempotency triple stops binding the key",
        "state.py",
        _b(
            "                if triple != (command.episode_id, command.route_id, command.purpose_id):\n"
        ),
        _b("                if False:  # mutated\n"),
        ["tests/test_state.py::TestAttemptOpenAtomicAndDoubleTap"],
    ),
    (
        "M12 lock contention stops being a typed error",
        "state.py",
        _b(
            "        except sqlite3.OperationalError as exc:\n"
            "            raise LockContention(\n"
            '                f"the write lock was not acquired within {self.busy_timeout_ms} ms, "\n'
            '                f"so nothing was written: {exc}"\n'
            "            ) from exc\n"
        ),
        _b(
            "        except sqlite3.OperationalError as exc:\n"
            "            raise  # mutated: raw error leaks\n"
        ),
        ["tests/test_state.py::TestLockContention"],
    ),
    (
        "M13 the receipt stops refusing after a consent move",
        "state.py",
        _b(
            "        if version != stamped_version:\n"
            "            return (\n"
            '                f"consent version changed from {stamped_version} to {version} "\n'
            '                "while the attempt was in flight"\n'
            "            )\n"
        ),
        _b(
            "        if False:  # mutated\n"
            "            return (\n"
            '                f"consent version changed from {stamped_version} to {version} "\n'
            '                "while the attempt was in flight"\n'
            "            )\n"
        ),
        [
            "tests/test_state.py::TestConsentRevokeInFlight",
            "tests/test_service.py::TestCallbackReceipts",
        ],
    ),
    (
        "M14 a caller-stated origin is trusted",
        "service.py",
        _b("        if stated is not self._origin:\n"),
        _b("        if False:  # mutated\n"),
        ["tests/test_service.py::TestCallbackReceipts"],
    ),
    (
        "M15 a double tap dispatches a second time",
        "service.py",
        _b("        existing = self._store.get_attempt_by_key(key)\n"),
        _b("        existing = None  # mutated\n"),
        ["tests/test_service.py::TestActionPath"],
    ),
    (
        "M16 opening an action writes the outcome itself",
        "service.py",
        _b("        tool = self._coordinator.execute_tool(\n"),
        _b(
            "        self._store.record_callback_once(\n"
            "            attempt.attempt_id,\n"
            "            'inline',\n"
            "            CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED),\n"
            "            self._origin,\n"
            "            now_utc=now_utc,\n"
            "        )\n"
            "        tool = self._coordinator.execute_tool(\n"
        ),
        ["tests/test_service.py::TestActionPath"],
    ),
]

CONTROL = [
    "tests/test_coordinator.py",
    "tests/test_service.py::TestActionPath",
    "tests/test_service.py::TestCallbackReceipts",
    "tests/test_state.py::TestLockContention",
    "tests/test_state.py::TestAttemptOpenAtomicAndDoubleTap",
    "tests/test_state.py::TestConsentRevokeInFlight",
    "tests/test_api.py::TestActionRoutes",
    "tests/test_api.py::TestCallbackRoute",
]


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


def _endings(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    lone = data.count(b"\n") - crlf
    return f"CRLF={crlf} loneLF={lone}"


def main() -> int:
    # Snapshot every file the harness can touch, before anything is patched.
    touched = sorted({filename for _, filename, _, _, _ in MUTATIONS})
    pristine: dict[pathlib.Path, bytes] = {
        SRC / name: (SRC / name).read_bytes() for name in touched
    }
    baseline = {path: _md5(data) for path, data in pristine.items()}
    for path, data in pristine.items():
        print(f"[BASE] {path.name}: md5={baseline[path]} {_endings(data)}")

    failures: list[str] = []

    for name, filename, old, new, selectors in MUTATIONS:
        path = SRC / filename
        original = path.read_bytes()

        # A skipped mutation is a failure, not a note: it means the record's
        # "seen RED" figure is wrong.
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
            code = run(selectors)
            if code == 0:
                print("    *** SURVIVED: the guard has no teeth ***")
                failures.append(f"{name} (SURVIVED)")
        finally:
            path.write_bytes(original)
            _purge_bytecode(path)
            restored = path.read_bytes()
            if _md5(restored) != _md5(original):
                print(f"    *** RESTORE MISMATCH in {filename}: ABORTING ***")
                failures.append(f"{name} (restore mismatch)")
                # Put the pristine bytes back from the pre-run snapshot.
                path.write_bytes(pristine[path])
                break

    print("\n[CONTROL] restored tree:")
    for path in pristine:
        if path.read_bytes() != pristine[path]:
            print(
                f"    *** {path.name} does not match its pre-run bytes "
                f"(now {_md5(path.read_bytes())} {_endings(path.read_bytes())}, "
                f"expected {baseline[path]} {_endings(pristine[path])}) ***"
            )
            failures.append(f"control: {path.name} not restored")
            path.write_bytes(pristine[path])
    if not failures:
        code = run(CONTROL)
        if code != 0:
            print("    *** CONTROL FAILED: a file was not restored ***")
            failures.append("control")

    print("\n=== result ===")
    if failures:
        for item in failures:
            print(f"  PROBLEM: {item}")
        return 1
    print("  every mutation was seen RED; every file restored byte-exact; tree green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
