"""The enforcing boundary check. Slice 2, constraint C7 and decision D2.

`02-architecture.md` D2 says the trust boundary is a module boundary and that
`domain` imports no network, no LLM client and no wall clock. The round-2 review
called it the strongest decision in the architecture, and Gate 3 required that
"Gate 3 must name the enforcing check and make it fail-capable, or this is a
convention with a diagram". This file is that check.

It is a static check over the source, not a runtime observation, because the
thing being prevented is a line of code that should not exist at all.

Proving the check can fail, which is the Slice 2 exit condition, is done twice:

* `test_scanner_detects_an_injected_import_in_the_real_rules_file` takes the
  **actual** `domain/rules.py` source and prepends one forbidden import. A
  scanner that only works on toy strings proves nothing about the file it is
  supposed to police.
* `TestScannerHasTeeth` injects each forbidden form separately, so one working
  detector cannot cover for a missing one.

`AGENTS.md` section 6: an inventory describes structure, not coverage. Every
detector below is paired with the input it must catch.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay.domain import models, rules  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_ROOT = REPO_ROOT / "src" / "carerelay" / "domain"

# ---------------------------------------------------------------------------
# Forbidden module imports
# ---------------------------------------------------------------------------

FORBIDDEN_MODULES: frozenset[str] = frozenset(
    {
        # network
        "socket",
        "ssl",
        "http",
        "urllib",
        "urllib2",
        "urllib3",
        "requests",
        "httpx",
        "aiohttp",
        "websockets",
        "ftplib",
        "smtplib",
        "telnetlib",
        "xmlrpc",
        "asyncio",
        # database, filesystem, operating system
        "sqlite3",
        "dbm",
        "shelve",
        "pickle",
        "pathlib",
        "os",
        "io",
        "shutil",
        "tempfile",
        "glob",
        "subprocess",
        "ctypes",
        "multiprocessing",
        "threading",
        "winreg",
        "pty",
        "fcntl",
        "platform",
        "getpass",
        # wall clock
        "time",
        # nondeterminism
        "random",
        "secrets",
        "uuid",
        # logging and telemetry
        "logging",
        # model and platform clients
        "openai",
        "anthropic",
        "google",
        "boto3",
        "tavily",
        "workbuddy",
        "codebuddy",
        # dynamic import, interpreter internals and the builtins module
        "importlib",
        "builtins",
        "sys",
    }
)

# ---------------------------------------------------------------------------
# Forbidden calls
# ---------------------------------------------------------------------------

#: Exact dotted call targets that are always forbidden.
FORBIDDEN_CALLS: frozenset[str] = frozenset(
    {
        "open",
        "input",
        "eval",
        "exec",
        "compile",
        "__import__",
        "os.getenv",
        "os.system",
        "os.popen",
        "sqlite3.connect",
        "socket.socket",
        "socket.create_connection",
        "importlib.import_module",
    }
)

#: Dotted-suffix patterns. These catch the clock however it was imported, so
#: `from datetime import datetime` followed by `datetime.now()` is caught the
#: same way `datetime.datetime.now()` is.
FORBIDDEN_CALL_SUFFIXES: tuple[str, ...] = (
    ".now",
    ".utcnow",
    ".today",
    "time.time",
    "time.monotonic",
    "time.perf_counter",
    "time.sleep",
)

#: Words that must never appear on a patient-facing surface. `dwell_seconds` is
#: recorded for the judge ledger and never shown to the patient (`PLAN.md`
#: 5.2.1); the rest are timer vocabulary, and constraint C8 says there are no
#: timers anywhere in the product.
PATIENT_SURFACE_MARKERS: tuple[str, ...] = (
    "dwell_seconds",
    "countdown",
    "settimeout",
    "setinterval",
    "auto_hide",
    "autohide",
    "auto_hide_after",
    "auto-advance",
    "auto_advance",
    "expires_in",
    "seconds_remaining",
    "remaining_seconds",
)


def _dotted_name(node: ast.AST) -> str:
    """Build `a.b.c` from a Name/Attribute chain, else return ""."""
    parts: list[str] = []
    cursor: ast.AST | None = node
    while isinstance(cursor, ast.Attribute):
        parts.append(cursor.attr)
        cursor = cursor.value
    if isinstance(cursor, ast.Name):
        parts.append(cursor.id)
        return ".".join(reversed(parts))
    return ""


def scan_source(source: str, filename: str = "<source>") -> list[str]:
    """Return one message per forbidden import or call found in `source`."""
    violations: list[str] = []
    tree = ast.parse(source, filename=filename)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_MODULES:
                    violations.append(
                        f"{filename}:{node.lineno}: imports forbidden module "
                        f"{alias.name!r}"
                    )
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in FORBIDDEN_MODULES:
                violations.append(
                    f"{filename}:{node.lineno}: imports from forbidden module "
                    f"{node.module!r}"
                )
        elif isinstance(node, ast.Call):
            # A call whose *target* is itself produced by a call, a subscript or a
            # lambda is a dynamic call: `f()()`, `getattr(x, "y")()`, `d["k"]()`.
            # Those are exactly how `__builtins__["open"](...)` and
            # `getattr(datetime, "now")()` reach the world without importing a
            # forbidden module, so they are refused rather than skipped. A method
            # call on a literal (`" ".join(...)`) is an Attribute, not one of
            # these, which is why the check is on the shape of `func`.
            if isinstance(node.func, (ast.Call, ast.Subscript, ast.Lambda)):
                violations.append(
                    f"{filename}:{node.lineno}: calls a dynamically produced target"
                )
                continue
            dotted = _dotted_name(node.func)
            if not dotted:
                continue
            if dotted in FORBIDDEN_CALLS or any(
                dotted.endswith(suffix) for suffix in FORBIDDEN_CALL_SUFFIXES
            ):
                violations.append(
                    f"{filename}:{node.lineno}: calls forbidden target {dotted!r}"
                )

    return violations


def scan_paths(paths: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in paths:
        violations.extend(
            scan_source(path.read_text(encoding="utf-8"), filename=str(path))
        )
    return violations


def domain_sources() -> list[Path]:
    return sorted(DOMAIN_ROOT.rglob("*.py"))


def scan_patient_surface(payload: str) -> list[str]:
    """Return the timer and dwell markers present in a serialized patient payload."""
    lowered = payload.casefold()
    return [marker for marker in PATIENT_SURFACE_MARKERS if marker in lowered]


# ---------------------------------------------------------------------------
# The check itself
# ---------------------------------------------------------------------------


def test_domain_import_boundary() -> None:
    """C7 and D2: no I/O, SDK, database, filesystem or wall-clock access in `domain/`.

    Gate 4 names this test. It fails when an SDK, network, database, filesystem
    or wall-clock import or call appears anywhere under `src/carerelay/domain/`.
    """
    sources = domain_sources()
    assert sources, f"no domain sources found under {DOMAIN_ROOT}"
    assert {path.name for path in sources} >= {"__init__.py", "models.py", "rules.py"}, (
        "the boundary check must cover the whole domain package, not a subset"
    )

    violations = scan_paths(sources)
    assert violations == [], "domain purity is broken:\n" + "\n".join(violations)


def test_domain_is_reachable_and_pure_at_import_time() -> None:
    """A second, independent guard: the modules import without touching anything.

    The static scan above reads source. This one imports the package and checks
    that the two modules the boundary protects actually loaded, so a renamed
    file cannot leave the scan passing over an empty set.
    """
    assert models.__name__ == "carerelay.domain.models"
    assert rules.__name__ == "carerelay.domain.rules"
    assert callable(rules.compare_plan)
    assert callable(rules.derive_closure)


# ---------------------------------------------------------------------------
# The check can fail. This is the Slice 2 exit condition.
# ---------------------------------------------------------------------------


def test_scanner_detects_an_injected_import_in_the_real_rules_file() -> None:
    """Take the real `rules.py`, add one forbidden import, require detection.

    A green check that was never seen red is not evidence. This runs the scanner
    over the actual file the boundary protects, not a toy string.
    """
    real_source = (DOMAIN_ROOT / "rules.py").read_text(encoding="utf-8")

    clean = scan_source(real_source, filename="rules.py")
    assert clean == [], f"the real rules.py already violates the boundary: {clean}"

    injected = "import socket\n" + real_source
    detected = scan_source(injected, filename="rules.py")
    assert detected, "the scanner did not detect a forbidden import in rules.py"
    assert "socket" in detected[0]

    # And the real file on disk is still clean after the injection experiment.
    assert scan_paths(domain_sources()) == []


class TestScannerHasTeeth:
    """One detector per forbidden form. A shared detector proves nothing."""

    def test_detects_a_forbidden_module_import(self) -> None:
        assert scan_source("import sqlite3\n")

    def test_detects_a_from_import_of_a_forbidden_module(self) -> None:
        assert scan_source("from pathlib import Path\n")

    def test_detects_a_forbidden_module_import_nested_in_a_function(self) -> None:
        source = "def load():\n    import requests\n    return requests\n"
        assert scan_source(source)

    def test_detects_a_wall_clock_call_after_a_from_import(self) -> None:
        source = "from datetime import datetime\n\ndef stamp():\n    return datetime.now()\n"
        assert scan_source(source)

    def test_detects_a_wall_clock_call_through_the_module(self) -> None:
        source = "import datetime\n\ndef stamp():\n    return datetime.datetime.utcnow()\n"
        assert scan_source(source)

    def test_detects_a_time_module_call(self) -> None:
        assert scan_source("import time\n\ndef stamp():\n    return time.time()\n")

    def test_detects_a_bare_open_call(self) -> None:
        assert scan_source("def read():\n    return open('/etc/passwd')\n")

    def test_detects_a_model_client_import(self) -> None:
        assert scan_source("from openai import OpenAI\n")

    def test_accepts_the_imports_the_domain_actually_needs(self) -> None:
        """The check must not be a blanket ban that forbids the real file.

        `datetime` is imported for its *type*, and taking `now_utc` as an
        argument is the correct pattern (D5). Neither may be flagged.
        """
        allowed = (
            "from __future__ import annotations\n"
            "from collections.abc import Mapping, Sequence\n"
            "from dataclasses import dataclass\n"
            "from datetime import datetime, timedelta, tzinfo\n"
            "from enum import StrEnum\n"
            "from types import MappingProxyType\n"
            "\n"
            "def f(now_utc: datetime) -> timedelta:\n"
            "    return timedelta(seconds=1)\n"
        )
        assert scan_source(allowed) == []


class TestEveryDetectorIsPairedWithItsInput:
    """`AGENTS.md` section 6: an inventory describes structure, not coverage.

    The Slice 2 review deleted two list entries that no test input exercised and
    the suite stayed green, so "one detector per forbidden form" was a claim the
    tests did not support. These tests iterate the lists themselves, so a new
    entry arrives with its own input and a typo in one entry cannot hide behind
    another entry's passing case.
    """

    @pytest.mark.parametrize("module", sorted(FORBIDDEN_MODULES))
    def test_every_forbidden_module_is_detected_on_import(self, module: str) -> None:
        assert scan_source(f"import {module}\n"), module

    @pytest.mark.parametrize("module", sorted(FORBIDDEN_MODULES))
    def test_every_forbidden_module_is_detected_on_from_import(self, module: str) -> None:
        assert scan_source(f"from {module} import thing\n"), module

    @pytest.mark.parametrize("target", sorted(FORBIDDEN_CALLS))
    def test_every_forbidden_call_target_is_detected(self, target: str) -> None:
        assert scan_source(f"{target}()\n"), target

    @pytest.mark.parametrize("suffix", FORBIDDEN_CALL_SUFFIXES)
    def test_every_forbidden_call_suffix_is_detected(self, suffix: str) -> None:
        source = f"stamp{suffix}()\n" if suffix.startswith(".") else f"{suffix}()\n"
        assert scan_source(source), suffix


class TestScannerResistsDynamicCalls:
    """The Slice 2 review got five snippets past the scanner. These are they.

    Every one reaches a filesystem, a network, a database or the clock without
    importing a forbidden module, by producing the callable at runtime. Each
    failed before the dynamic-target check existed.
    """

    def test_detects_a_subscript_reached_builtin(self) -> None:
        """`__builtins__["open"]("/etc/passwd")` needs no import at all."""
        assert scan_source("def r():\n    return __builtins__['open']('/etc/passwd')\n")

    def test_detects_a_getattr_reached_clock(self) -> None:
        """`datetime` is a permitted import; reaching `.now` dynamically is not."""
        source = (
            "from datetime import datetime\n"
            "\n"
            "def s():\n"
            "    return getattr(datetime, 'now')()\n"
        )
        assert scan_source(source)

    def test_detects_a_call_produced_import(self) -> None:
        source = (
            "def n():\n"
            "    return globals()['__builtins__']['__import__']('socket')\n"
        )
        assert scan_source(source)

    def test_detects_a_builtins_module_import(self) -> None:
        assert scan_source("import builtins\n\ndef r():\n    return builtins.open('/x')\n")

    def test_detects_a_from_builtins_import(self) -> None:
        assert scan_source("from builtins import open as _open\n")

    def test_detects_the_sys_module(self) -> None:
        assert scan_source("import sys\n")

    def test_a_method_call_on_a_literal_is_not_a_dynamic_target(self) -> None:
        """The false positive this check must not create.

        `" ".join(...)` has an Attribute for its `func` and is ordinary code, so
        it must not be reported as a dynamically produced target.
        """
        assert scan_source("def j():\n    return ' '.join(['a', 'b'])\n") == []


class TestPatientSurfaceHasNoTimerAndNoDwell:
    """C8 on the serialized surface, not on the in-memory value.

    `AGENTS.md` section 6: for every absence or leak assertion, prove the needle
    can match the surface **as serialized**. A scan that has never detected its
    needle is not evidence, so each test below injects the needle first.
    """

    def _surface(self) -> str:
        from datetime import datetime, timezone

        from carerelay.domain.models import (
            Disposition,
            DispositionSource,
            EpisodeSnapshot,
        )

        disposition = Disposition(
            episode_id="demo-episode-001",
            version=1,
            policy_version="fixture-provisional-0",
            action_id="attend_same_day_review",
            clinical_deadline_utc=datetime(2026, 9, 30, 10, 0, tzinfo=timezone.utc),
            next_owner_id="patient",
            fallback_route_id="nurse_line",
            source=DispositionSource.FIXTURE,
        )
        snapshot = EpisodeSnapshot(
            disposition=disposition,
            attempt=None,
            evidence=(),
            consent_version=None,
            human_acceptance_id=None,
            escalation_id=None,
            expiry_event_id=None,
        )
        closure = rules.derive_closure(snapshot, disposition.clinical_deadline_utc)
        text = models.PolicyText(
            policy_version="fixture-provisional-0",
            fixture_label="SIMULATED - RESEARCH DEMONSTRATION",
            deadline_display_by_version={1: "6:00 PM on 30 September"},
            self_owner_id="patient",
            owner_display_by_id={"patient": "you", "caregiver": "your daughter"},
            route_display_by_id={"nurse_line": "the fictional nurse line"},
            simulated=True,
        )
        lines = rules.patient_lines(snapshot, closure, text)
        return json.dumps(
            {
                "lines": list(lines),
                "simulated": closure.simulated,
                "fixture_label": text.fixture_label,
            }
        )

    def test_the_patient_surface_carries_no_dwell_or_timer_marker(self) -> None:
        surface = self._surface()
        assert scan_patient_surface(surface) == [], (
            f"patient surface leaks a timer or dwell marker: {surface}"
        )

    def test_the_scan_can_detect_an_injected_dwell_field(self) -> None:
        """Without this, the assertion above is a negative result and not evidence."""
        surface = self._surface()
        injected = json.dumps({"lines": json.loads(surface)["lines"], "dwell_seconds": 4.2})
        assert scan_patient_surface(injected) == ["dwell_seconds"]

    def test_the_scan_can_detect_an_injected_countdown_field(self) -> None:
        surface = self._surface()
        injected = json.dumps({"lines": json.loads(surface)["lines"], "countdown": 5})
        assert "countdown" in scan_patient_surface(injected)

    def test_the_dwell_marker_is_a_real_string_in_the_ledger_surface(self) -> None:
        """The exclusion is only meaningful if the field exists somewhere.

        `dwell_seconds` is a field of the hint event that feeds the judge
        ledger. If it did not exist at all, its absence from the patient
        surface would prove nothing.
        """
        assert "dwell_seconds" in models.HintEvent.__dataclass_fields__
        assert "dwell_seconds" in scan_patient_surface(
            json.dumps({"dwell_seconds": 1.0})
        )
