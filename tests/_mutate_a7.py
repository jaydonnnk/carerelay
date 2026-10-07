"""Mutation check for the two A7 findings from the Slice 7 review.

Run: PYTHONPATH=src python tests/_mutate_a7.py

Three mutations, each of which must be seen RED. A mutation that survives means
the guard it removes is decoration, which is precisely what finding A7-1 was
about: a scanner listing files it never reads would look identical to a working
one from the outside.

`tests/test_boundaries.py` is LF, so every anchor here is written LF and matched
against the file's real bytes. The Slice 6 harness hard-coded CRLF and silently
failed to apply a mutation; this one refuses to guess.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
TARGET = REPO / "tests" / "test_boundaries.py"
PYTHON = sys.executable


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


#: (label, anchor bytes, replacement bytes, selectors)
MUTATIONS = [
    (
        "A1  the victim list drops the frontend (A7-1 returns, invisibly)",
        b'    ("frontend server module", "frontend/lib/api.ts"),\n',
        b"",
        ["tests/test_boundaries.py::TestNoSecretIsCommitted"],
    ),
    (
        "A2  NEXT_PUBLIC_ is removed from the markers (A7-1 returns)",
        b'    "next_public_",\n',
        b"",
        ["tests/test_boundaries.py::TestNoSecretIsCommitted"],
    ),
    (
        "A3  the split reverts to the chained form (A7-2 returns)",
        b'    separators = [index for index in (line.find("="), line.find(":")) if index != -1]\n'
        b'    if not separators:\n'
        b'        return ""\n'
        b'    return line[min(separators) + 1 :]\n',
        b'    return line.split("=", 1)[-1].split(":", 1)[-1]\n',
        ["tests/test_boundaries.py::TestNoSecretIsCommitted"],
    ),
]


def main() -> int:
    original = TARGET.read_bytes()
    baseline = _md5(original)
    crlf = original.count(b"\r\n")
    lone = original.count(b"\n") - crlf
    print(f"[BASE] {TARGET.name}: md5={baseline} CRLF={crlf} loneLF={lone}")
    if crlf:
        print("[FAIL] this harness assumes an LF file; it is CRLF")
        return 1

    failures: list[str] = []
    red = 0

    for label, anchor, replacement, selectors in MUTATIONS:
        if anchor not in original:
            print(f"[FAIL] {label}: anchor not found")
            failures.append(f"{label} (anchor not found)")
            continue
        if original.count(anchor) != 1:
            print(f"[FAIL] {label}: anchor appears {original.count(anchor)} times")
            failures.append(f"{label} (anchor not unique)")
            continue

        TARGET.write_bytes(original.replace(anchor, replacement))
        try:
            env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
            env["PYTHONPATH"] = "src"
            # A `.pyc` compiled from a mutated file is a mutation that
            # outlives the restore, so no child process may write one.
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                [PYTHON, "-m", "pytest", "-o", "addopts=", "-q", *selectors],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        finally:
            TARGET.write_bytes(original)
            _purge_bytecode(TARGET)

        summary = [
            line
            for line in completed.stdout.splitlines()
            if " passed" in line or " failed" in line or " error" in line
        ]
        print(f"[RUN ] {label}")
        print(f"       {summary[-1].strip() if summary else '(no summary)'}")
        if completed.returncode != 0:
            red += 1
        else:
            print("       *** SURVIVED: the guard has no teeth ***")
            failures.append(f"{label} (SURVIVED)")

    restored = TARGET.read_bytes()
    print()
    if restored != original:
        print(f"[FAIL] restore is not byte-identical: md5={_md5(restored)}")
        return 1
    print(f"[CONTROL] restored, md5={_md5(restored)} byte-identical to baseline")

    print(f"\n=== result: {red} of {len(MUTATIONS)} mutations seen RED ===")
    if failures:
        for item in failures:
            print(f"  PROBLEM: {item}")
        return 1
    print("  every mutation was seen RED; the file was restored byte-exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
