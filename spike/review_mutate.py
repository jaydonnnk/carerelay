"""Slice 5 review mutation harness. Binary-safe: no line-ending bytes in any needle.

Usage: python spike/review_mutate.py <apply|restore> <F6|O7|K2>
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MUTATIONS = {
    "F6": (
        "src/carerelay/domain/rules.py",
        "if snapshot.escalation_id is None:",
        "if True:  # M1",
    ),
    "O7": (
        "src/carerelay/state.py",
        "if disposition.clinical_deadline_utc <= previous_deadline:",
        "if False:  # M2",
    ),
    "K2": (
        "src/carerelay/service.py",
        "        if self._bound_complaint not in rules.normalise(confirmed_text):",
        None,  # special: inserted below
    ),
    # Narrower K2 mutation: a coordinator failure moves the deadline instead of
    # abstaining. Targets only test_a_coordinator_failure_cannot_move_the_deadline.
    "K2B": ("src/carerelay/service.py", None, None),
    # Tolerated coordinator call in intake: the plan is still issued, so only the
    # call-counting assertion can see it.
    "K2C": ("src/carerelay/service.py", None, None),
}

K2C_ANCHOR = b"        if self._bound_complaint not in rules.normalise(confirmed_text):"

K2C_REPLACEMENT = (
    b"        try:\r\n"
    b"            self._coordinator.extract_plan(confirmed_text, self._allowed_values())\r\n"
    b"        except Exception:\r\n"
    b"            pass\r\n"
) + K2C_ANCHOR

K2B_ANCHOR = (
    b"        extracted = self._coordinator.extract_plan(\r\n"
    b"            confirmed_text, self._allowed_values()\r\n"
    b"        )"
)

K2B_REPLACEMENT = (
    b"        try:\r\n"
    b"            extracted = self._coordinator.extract_plan(\r\n"
    b"                confirmed_text, self._allowed_values()\r\n"
    b"            )\r\n"
    b"        except Exception:\r\n"
    b"            from datetime import timedelta as _td\r\n"
    b"            self._store.insert_disposition(\r\n"
    b"                replace(\r\n"
    b"                    snapshot.disposition,\r\n"
    b"                    version=snapshot.disposition.version + 1,\r\n"
    b"                    clinical_deadline_utc=snapshot.disposition.clinical_deadline_utc\r\n"
    b"                    + _td(hours=1),\r\n"
    b"                ),\r\n"
    b"                now_utc=now_utc,\r\n"
    b"            )\r\n"
    b"            raise\r\n"
)

BACKUP_DIR = ROOT / "spike" / ".mutation_backups"


def backup_path(rel: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR / Path(rel).name


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lone_lf(path: Path) -> int:
    b = path.read_bytes()
    return b.count(b"\n") - b.count(b"\r\n")


def save(rel: str) -> None:
    src, dst = ROOT / rel, backup_path(rel)
    if not dst.exists():
        shutil.copy2(src, dst)
        print(f"backup {rel} -> {dst.name} sha={digest(dst)[:16]} loneLF={lone_lf(dst)}")


def restore(rel: str) -> None:
    src, dst = ROOT / rel, backup_path(rel)
    shutil.copy2(dst, src)
    print(f"restored {rel} sha={digest(src)[:16]} loneLF={lone_lf(src)}")


def apply(key: str) -> None:
    rel, old, new = MUTATIONS[key]
    path = ROOT / rel
    save(rel)
    b = path.read_bytes()
    if key == "K2C":
        assert b.count(K2C_ANCHOR) == 1, f"K2C anchor count {b.count(K2C_ANCHOR)}"
        patched = b.replace(K2C_ANCHOR, K2C_REPLACEMENT)
        path.write_bytes(patched)
        print(f"applied K2C on {rel} sha={digest(path)[:16]} loneLF={lone_lf(path)}")
        return
    if key == "K2B":
        assert b.count(K2B_ANCHOR) == 1, f"K2B anchor count {b.count(K2B_ANCHOR)}"
        patched = b.replace(K2B_ANCHOR, K2B_REPLACEMENT)
        path.write_bytes(patched)
        print(f"applied K2B on {rel} sha={digest(path)[:16]} loneLF={lone_lf(path)}")
        return
    if key == "K2":
        # Gate the plan behind the coordinator: the urgent path would then wait
        # on read-back, which is exactly the defect K2 exists to catch.
        anchor = b"        if self._bound_complaint not in rules.normalise(confirmed_text):"
        assert b.count(anchor) == 1, b.count(anchor)
        injected = (
            b"        self._coordinator.extract_plan(confirmed_text, self._allowed_values())\r\n"
            + anchor
        )
        patched = b.replace(anchor, injected)
    else:
        needle = old.encode()
        assert b.count(needle) == 1, f"{key} needle count {b.count(needle)}"
        patched = b.replace(needle, new.encode())
    assert patched != b, "no change written"
    path.write_bytes(patched)
    print(f"applied {key} on {rel} sha={digest(path)[:16]} loneLF={lone_lf(path)}")


if __name__ == "__main__":
    mode, key = sys.argv[1], sys.argv[2]
    if mode == "apply":
        apply(key)
    else:
        restore(MUTATIONS[key][0])
