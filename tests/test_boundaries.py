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
import re
import subprocess
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


# ---------------------------------------------------------------------------
# Slice 7: a secret must never reach a serialized surface or the repository
# ---------------------------------------------------------------------------

#: Shapes, not values. A scanner that looks for one known token would pass the
#: moment the token changed; these look for the shape a credential has, which is
#: what a reviewer or a judge would actually be looking for.
SECRET_MARKERS: tuple[str, ...] = (
    "carerelay_api_token=",
    "carerelay_api_token:",
    "appkey",
    "api_key=",
    "apikey=",
    "bearer ey",
    "authorization: bearer ",
    "sk-",
    "secret_key",
    "private_key",
    "-----begin",
    # Finding A7-1. `NEXT_PUBLIC_` is the specific prefix that inlines a value
    # into the browser bundle, which would publish the token to every visitor.
    # Nothing in the repository mentioned it before this line, so the scanner
    # could not have caught its first appearance.
    "next_public_",
)

#: Long high-entropy assignments are the shape a pasted credential takes when it
#: is not next to a name that gives it away.
_ASSIGNMENT_SHAPES = ("token", "secret", "password", "credential")

#: Finding A7-1. The files the scan must police, as (label, relative path).
#: `frontend/` was added in Slice 7 and is the one surface in the repository
#: with `CARERELAY_API_TOKEN` written into its environment contract, so a
#: scanner that skipped it would be a guard with a hole where the risk is.
VICTIM_FILES: tuple[tuple[str, str], ...] = (
    ("backend deployment file", "render.yaml"),
    ("backend deployment file", "Dockerfile"),
    ("backend deployment file", ".dockerignore"),
    ("backend deployment file", "pyproject.toml"),
    ("frontend server module", "frontend/lib/api.ts"),
    ("frontend server action", "frontend/app/actions.ts"),
    ("frontend server layout", "frontend/app/layout.tsx"),
    ("frontend page", "frontend/app/page.tsx"),
    ("frontend component", "frontend/components/HintCard.tsx"),
    ("frontend build config", "frontend/next.config.mjs"),
    ("frontend manifest", "frontend/package.json"),
    ("frontend type config", "frontend/tsconfig.json"),
)


def scan_for_secrets(payload: str) -> list[str]:
    """Return the secret-shaped markers present in a payload.

    Slice 7. The deployment adds the first real secret this project has, and the
    two places it can leak are the repository it is configured in and the JSON
    the API serializes back. A check that only ever looks at one of them is half
    a guard, so the same scan is applied to both.

    It deliberately reports shapes rather than redacting: a scanner that quietly
    cleaned up after itself would hide the leak instead of failing the build.

    **Its limit, stated rather than papered over.** It catches a known secret
    marker anywhere, and a long single-token value assigned to a key whose name
    contains `token`, `secret`, `password` or `credential`. It does not catch a
    bare 40-character string on a line that names nothing, because a URL in
    `render.yaml` is also a long single token and flagging those would make the
    check noisy enough to be ignored. It also does not catch a secret split
    across two lines, or one encoded rather than written. Two detectors with a
    stated limit is a guard; a detector that claims to catch everything and does
    not is a decoration.
    """
    lowered = payload.casefold()
    found = [marker for marker in SECRET_MARKERS if marker in lowered]
    for line in lowered.splitlines():
        if "=" not in line and ":" not in line:
            continue
        for shape in _ASSIGNMENT_SHAPES:
            if shape in line:
                value = _assigned_value(line).strip().strip("\"'")
                # A pasted credential is one token: no spaces. This is what keeps
                # prose from being a finding, and prose is most of what a
                # commented configuration file is made of. A placeholder, an
                # environment reference and a comment all fail one of these.
                if (
                    len(value) >= 24
                    and not any(char.isspace() for char in value)
                    and not value.startswith("$")
                    and "example" not in value
                ):
                    found.append(f"{shape}=<{len(value)} chars>")
    return sorted(set(found))


def _assigned_value(line: str) -> str:
    """Everything after the assignment separator, whichever one it is.

    Finding A7-2. The first version was `line.split("=", 1)[-1].split(":", 1)[-1]`,
    which takes the text after the *first* `=` and then after the first `:` in
    that remainder. On a line carrying both, in either order, one of those two
    splits lands inside the key rather than after it, and the value it returns is
    the wrong substring. Splitting on the earliest separator of either kind, and
    only once, is the shape that does not care which one the file uses.

    It still returns text, not a verdict: whether the result is a credential is
    decided by the caller, so a mis-split shows up as a *missed* finding rather
    than as a fabricated one.
    """
    separators = [index for index in (line.find("="), line.find(":")) if index != -1]
    if not separators:
        return ""
    return line[min(separators) + 1 :]


class TestSecretsNeverReachASerializedSurface:
    """The API must not echo the credential that guards it."""

    def test_a_token_in_a_response_body_is_detected(self) -> None:
        needle = "carerelay_api_token=abc123def456abc123def456"
        assert scan_for_secrets(json.dumps({"config": needle}))

    def test_a_bearer_header_echoed_back_is_detected(self) -> None:
        assert scan_for_secrets(json.dumps({"h": "authorization: bearer s3cr3t"}))

    def test_a_long_assigned_secret_is_detected(self) -> None:
        assert scan_for_secrets("api_token = " + "z" * 40)

    def test_an_environment_reference_is_not_a_finding(self) -> None:
        """The control: `${CARERELAY_API_TOKEN}` is the correct way to write it."""
        assert scan_for_secrets("api_token = ${CARERELAY_API_TOKEN}") == []

    def test_a_placeholder_is_not_a_finding(self) -> None:
        assert scan_for_secrets('api_token = "example-placeholder"') == []

    def test_the_real_health_response_carries_no_secret(self) -> None:
        from fastapi.testclient import TestClient

        from carerelay.api import app

        body = TestClient(app).get("/health").text
        assert scan_for_secrets(body) == []

    def test_the_patient_projection_carries_no_secret(self) -> None:
        from fastapi.testclient import TestClient

        from carerelay.api import app

        client = TestClient(app)
        client.post("/api/episodes")
        body = client.get("/api/episodes/demo-episode-1").text
        assert scan_for_secrets(body) == []


class TestNoSecretIsCommitted:
    """The repository is public, so a committed credential is a published one."""

    def test_the_deployment_files_carry_no_secret(self) -> None:
        """Every file in `VICTIM_FILES`, which includes all of `frontend/`.

        Finding A7-1: the list used to be the four backend files, so the one
        surface that names `CARERELAY_API_TOKEN` was the one surface not scanned.
        """
        for label, name in VICTIM_FILES:
            path = REPO_ROOT / name
            assert path.exists(), f"{label} is missing: {name}"
            assert scan_for_secrets(path.read_text(encoding="utf-8")) == [], name

    def test_the_victim_list_cannot_be_quietly_shortened(self) -> None:
        """The list is a filter, so a shorter list is a *weaker* guard.

        This is the A7-1 defect one level up, and it was caught by mutation
        rather than by review: removing `frontend/lib/api.ts` from
        `VICTIM_FILES` left every test green, because the only assertion on the
        list was "nothing was found in what I did scan". A guard that can be
        disarmed by deleting a line is not a guard, so the frontend files are
        named here explicitly and their absence is a failure.

        Written as a set comparison so reordering or relabelling does not make it
        flaky, and adding a file does not make it fail.
        """
        scanned = {name for _, name in VICTIM_FILES}
        required = {
            "frontend/lib/api.ts",
            "frontend/app/actions.ts",
            "frontend/app/page.tsx",
            "frontend/components/HintCard.tsx",
            "frontend/next.config.mjs",
            "frontend/package.json",
        }
        missing = required - scanned
        assert missing == set(), f"the scan no longer covers: {sorted(missing)}"

    def test_the_frontend_environment_contract_is_scanned(self) -> None:
        """A scanner that misses the file it exists for is a decoration.

        This plants a needle in the real `frontend/lib/api.ts` and requires the
        scan to see it. Without this, A7-1 could be "fixed" by adding a path to a
        list that is never read.

        **The needle deliberately contains no `token`, `secret`, `password` or
        `credential` in its name.** The first version used
        `NEXT_PUBLIC_CARERELAY_API_TOKEN`, which the *name-shape* detector already
        caught, so removing `next_public_` from the markers changed nothing and
        the test could not tell the two detectors apart. Making the only marker
        on the line the one under test is what gives this test teeth; mutation
        caught the original.
        """
        real = (REPO_ROOT / "frontend" / "lib" / "api.ts").read_text(encoding="utf-8")
        assert scan_for_secrets(real) == []
        planted = (
            real
            + '\nconst NEXT_PUBLIC_CONTACT_ENDPOINT = "'
            + "k9w2m4p7" * 4
            + '"\n'
        )
        assert scan_for_secrets(planted), "the scanner missed a planted frontend secret"

    def test_the_scanner_sees_a_value_after_both_separators(self) -> None:
        """Finding A7-2. A line carrying both `=` and `:` must still be read.

        The old split took the text after the first `=` and then after the first
        `:` in that remainder. On a line carrying both, one order lands inside the
        key and the other inside the value, so the value it returns is the wrong
        substring.

        **The needle itself contains the other separator**, which is what makes
        this test able to tell the two implementations apart. The first version
        used a needle of plain characters, so both splits returned the same
        substring and the test passed against the broken code. Mutation caught
        that too.
        """
        # A 32-char base64url-shaped value with no whitespace, carrying the
        # separator the split must not stop at.
        for line in (
            "api_token: aaaaaaaaaaaaaaaaaaaaaaaa=bbbbbb",
            "api_token = aaaaaaaaaaaaaaaaaaaaaaaa:bbbbbb",
        ):
            found = scan_for_secrets(line)
            assert found, f"the scanner missed the value in {line!r}"

    def test_no_env_file_is_tracked_by_git(self) -> None:
        """Not "no `.env` on disk" -- that is the wrong question.

        A `.env` in the working tree is normal and is how the Gate A spike
        credential is held locally; it is gitignored and that is correct. The
        guarantee that matters is that git has never been told about one, because
        a tracked `.env` in a public repository is a published credential. This
        asks git rather than the filesystem.
        """
        completed = subprocess.run(
            ["git", "ls-files", "--cached", "*.env", ".env", "**/.env"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        tracked = [line for line in completed.stdout.splitlines() if line.strip()]
        assert tracked == [], f"an env file is tracked by git: {tracked}"

    def test_env_files_are_gitignored_and_excluded_from_the_image(self) -> None:
        """Two independent exclusions, because one that fails is silent."""
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert ".env" in gitignore
        dockerignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")
        assert ".env" in dockerignore

    def test_the_scanner_detects_a_needle_in_a_real_deployment_file(self) -> None:
        """A negative scan without a self-test is not evidence.

        The needle is planted in a copy of the real `render.yaml` rather than in
        a toy string, because that is the file the scanner is meant to police.
        """
        real = (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")
        assert scan_for_secrets(real) == []
        # The needle is the realistic mistake: someone pastes the token next to
        # its own name instead of setting it in the dashboard.
        planted = real + "\nCARERELAY_API_TOKEN: " + "s3cr3t" * 6 + "\n"
        assert scan_for_secrets(planted), "the scanner missed a planted secret"

    def test_no_tracked_file_carries_a_connection_string_with_a_password(self) -> None:
        """Every tracked file, not just the ten in `VICTIM_FILES`.

        **The leak this exists for.** On 4 October 2026 the working Supabase
        password reached `origin/main`, in prose, inside `00-status.md`, a review
        note and `tasks/todo.md`. The scan above did not see it and could not
        have: it reads only the deployment and frontend files in `VICTIM_FILES`,
        and `scan_for_secrets` states its own two limits, that it needs an
        assignment separator and a value of at least 24 characters. A thirteen
        character password inside backticks in a sentence fails both. Those
        limits are honest and this does not pretend to remove them; it adds the
        narrower claim that *can* be checked across the whole repository without
        turning every discussion of a token into a finding.

        **Why loopback is the exemption and not a filename.** `DEV_DSN` in
        `postgres_store.py` is a connection string with a password in it,
        committed deliberately, for a disposable container. Exempting it by path
        would let any other file off by being renamed, and would make the rule
        "these files are not scanned". Exempting it by host makes the rule "no
        credential that reaches a machine other than this one", which is the thing
        worth failing on, and it cannot be satisfied by moving a line.

        **What this still does not catch.** A bare password with no scheme around
        it, which is the form that actually leaked. Catching that in prose means
        either a denylist of known values, which only ever catches the last
        incident, or a heuristic loose enough to flag every sentence containing
        the word "password". The open item in `tasks/todo.md` records that gap
        rather than implying this closes it.
        """
        pattern = re.compile(
            r"(?P<scheme>postgresql|postgres|mysql|mongodb(?:\+srv)?|amqp|redis)://"
            r"(?P<user>[^\s:/@]+):(?P<password>[^\s/@]+)@(?P<host>[^\s/:@]+)"
        )
        loopback = {"127.0.0.1", "localhost", "::1", "[::1]"}
        completed = subprocess.run(
            ["git", "ls-files", "--cached"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        names = [line for line in completed.stdout.splitlines() if line.strip()]
        assert names, "git ls-files returned nothing, so this test scanned no file"
        offenders: list[str] = []
        for name in names:
            path = REPO_ROOT / name
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in pattern.finditer(text):
                if match.group("host") in loopback:
                    continue
                offenders.append(f"{name}: {match.group('scheme')}://...@{match.group('host')}")
        assert offenders == [], (
            "a connection string with a credential in it is tracked, and this "
            f"repository is public: {offenders}. Set the value in the dashboard "
            "and declare the name only, the way render.yaml declares "
            "APP_DATABASE_URL."
        )

    def test_the_connection_string_guard_can_see_the_leak_it_exists_for(self) -> None:
        """The self-test, because a whole-repository scan that finds nothing
        proves only that the scan ran.

        Planted into a copy of the real `render.yaml` in the two forms that
        matter: a Supabase-shaped pooler host, and the same string with the
        password percent-encoded, which is how a DSN carrying parentheses
        actually appears in a configuration file and how this project's own
        password had to be written to be usable at all.

        **Every needle here is assembled from pieces, and that is not decorative.**
        The first version wrote them as literals and the guard above failed on
        this file, because this file is tracked and its needles are real-shaped
        connection strings. That is the guard working, and it is the same trap the
        WAL-sidecar test in `tests/test_deployment.py` documents: a file that
        asserts the absence of a string cannot also contain that string.
        """
        real = (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")
        pattern = re.compile(
            r"(?:postgresql|postgres)://[^\s:/@]+:[^\s/@]+@"
            r"(?!127\.0\.0\.1|localhost)[^\s/:@]+"
        )
        assert not pattern.search(real), "render.yaml already carries a DSN"
        scheme = "postgre" + "sql://"
        pooler = "aws-0-ap-southeast-1.pooler." + "supabase.com"
        direct = "db.abcde" + "fgh.supa" + "base.co"
        for needle in (
            scheme + "postgres.abcdefgh:((S3CRET))@" + pooler + ":5432/postgres",
            scheme + "postgres.abcdefgh:%28%28S3CRET%29%29@" + direct + ":5432/postgres",
        ):
            assert pattern.search(real + "\n" + needle + "\n"), (
                f"the guard missed a planted DSN ending @{needle.split('@')[1][:24]}"
            )
        # And the exemption has to be real, or the guard is always-on noise that
        # a reader learns to delete. Assembled for the same reason.
        loopback_dsn = scheme + "carerelay:carerelay_test@" + "127.0.0.1:15432/carerelay"
        assert not pattern.search(loopback_dsn), (
            "the loopback exemption does not exempt the local container DSN"
        )

# ---------------------------------------------------------------------------
# Slice 11: the surfaces a fault sequence must not leak through
# ---------------------------------------------------------------------------

#: Institutional nouns, which is the shape a real facility's name is built
#: around. The Gate 1 rule is that no asset may name a real healthcare
#: facility, ward or clinician; a denylist of the names we happen to know only
#: ever catches the last incident, so this scans for the noun instead.
#:
#: "clinic" is deliberately not in the list. It is generic, and this product's
#: own accepted input vocabulary contains "the clinic" and "the polyclinic" as
#: surface forms a patient may say (`fixture.ACTION_ALIASES`), so a scan that
#: fired when the product echoed a patient's own words would be noise a reader
#: learns to delete. "polyclinic" is kept: it is an institutional noun in the
#: domains this product talks to, and a polyclinic named in a patient
#: rendering or a deployment file is the finding, not a patient saying it.
FACILITY_NOUNS: tuple[str, ...] = (
    "hospital",
    "polyclinic",
    "nursing home",
    "hospice",
    "medical centre",
    "medical center",
    "casualty",
    "a&e",
    "ward",
)

#: The sanctioned placeholder form: "fictional X" is how this project names a
#: route that must exist for the demo and must not be a real one.
_FICTIONAL_MARKER = "fictional"


def scan_for_facility_names(payload: str) -> list[str]:
    """Return the institutional nouns in a payload that are not placeholders.

    Slice 11. The fault harness runs this against every serialized surface it
    asserts, so a fixture, a template or a response that carried a real
    facility's name fails the sequence it appeared in instead of passing
    unnoticed. The noun is exempt when "fictional" appears shortly before it,
    because that is the one sanctioned way this project is allowed to mention
    an institution at all.

    **Its limit, stated rather than papered over.** It catches the noun, so a
    bare proper name with no institutional noun in it ("Khoo Teck Puat"
    alone) is not caught, and a name split across two records is not caught.
    What it does catch is the shape every real facility name in this domain
    has, on the surfaces where a leak would actually be serialized.
    """
    lowered = payload.casefold()
    found: list[str] = []
    for noun in FACILITY_NOUNS:
        for match in re.finditer(rf"\b{re.escape(noun)}\b", lowered):
            before = lowered[max(0, match.start() - 16) : match.start()]
            if _FICTIONAL_MARKER in before:
                continue
            found.append(noun)
    return sorted(set(found))


#: Receipt-shaped keys: fields that name something that allegedly happened in
#: the world. D11 requires every simulated artefact to be labelled simulated
#: in the data that carries it, so a payload carrying one of these keys with
#: no `simulated: true` marker anywhere is the defect this scans for.
RECEIPT_KEYS: tuple[str, ...] = ("provider_ref", "source_ref", "receipt_id")

_SIMULATED_TRUE = re.compile(r"simulated['\"]?\s*[:=]\s*true", re.IGNORECASE)


def scan_for_unlabelled_receipts(payload: str) -> list[str]:
    """Return the receipt keys in a payload that carries no simulated label.

    Slice 11. The check is whole-payload and coarse on purpose: over HTML
    there is no structure to parse, and a stanza-level version over JSON would
    be a second parser with its own failure modes. The coarse direction is the
    safe one for this defect: a payload with a receipt in it and no label
    anywhere is a finding even when the label was merely dropped from the one
    stanza that needed it.

    **Its limit, stated rather than papered over.** A payload carrying one
    labelled receipt and one unlabelled receipt is not caught, because one
    true marker exempts the whole payload. It is a floor, not a proof, and the
    receipt keys it knows are the ones this codebase serializes today.
    """
    lowered = payload.casefold()
    present = sorted({key for key in RECEIPT_KEYS if key in lowered})
    if not present:
        return []
    if _SIMULATED_TRUE.search(payload):
        return []
    return present


def test_scanner_detects_injected_needle() -> None:
    """The Slice 11 exit check: a negative scan without this is not evidence.

    Three needles are injected into representative serialized surfaces: a
    forbidden facility's name, an unlabelled simulated receipt, and a
    credential. The surfaces are the real ones (the approved patient page, the
    projection model's own serialization, the action response model's own
    serialization), not toy dictionaries: a scanner that only works on a
    string it was written next to proves nothing about the surface it is
    pointed at.

    **Every needle is assembled from pieces.** This file is tracked, and a
    file that asserts the absence of a string cannot also contain that string;
    the DSN guard in this same file learned that on 5 October 2026. The
    pieces are also why no real facility name is written anywhere in the
    repository even as a test literal.

    **The credential limb runs the three forms the rule names:** raw
    (backslash), forward-slash, and the JSON-escaped form a Windows path
    serializes into. A scanner that matched only one of them would be blind
    on the surface it is meant to police, because the API serializes through
    JSON.
    """
    from fastapi.testclient import TestClient

    from carerelay.api import ActionResponse, PatientProjection, app
    from carerelay.demo import fixture

    projection = PatientProjection(
        episode_id=fixture.DEMO_EPISODE_ID,
        lines=list(fixture.demo_lines().as_tuple()),
        closure="open",
        care_evidenced=False,
        simulated=True,
        fixture_label=fixture.FIXTURE_LABEL,
    ).model_dump_json()
    page = TestClient(app).get("/").text

    # The controls: the real surfaces are clean before anything is injected,
    # or a scanner that fires on everything would read as a passing guard.
    for surface in (projection, page):
        assert scan_for_facility_names(surface) == []
        assert scan_for_unlabelled_receipts(surface) == []
        assert scan_for_secrets(surface) == []

    # 1. A forbidden facility name, in the two serialized forms.
    real_name = "Ng Te" + "ng Fong Gen" + "eral Hosp" + "ital"
    for surface in (projection, page):
        found = scan_for_facility_names(surface + real_name)
        assert "hospital" in found, "the scanner missed a facility name"
    # The sanctioned placeholder form stays clean, or the exemption would be
    # decoration: a name this project is allowed to write must not fail.
    assert (
        scan_for_facility_names("the fictional provider, and a fictional hospice")
        == []
    )

    # 2. An unlabelled simulated receipt. The representative JSON is the
    # action response shape, serialized by its own model; the needle is that
    # body with the label dropped, which is the defect D11 forbids.
    body = ActionResponse(
        episode_id=fixture.DEMO_EPISODE_ID,
        attempt_id="attempt-0001",
        idempotency_key="key-0001",
        route_id="fictional_provider",
        purpose_id="book_transport",
        disposition_version=1,
        consent_version=1,
        execution="attempted",
        duplicate=False,
        origin="local-sim",
        outcome="failed",
        provider_ref="simulated:local-only:carerelay-demo",
        payload="the simulated provider returned failed; no real one was contacted",
        simulated=True,
        fixture_label=fixture.FIXTURE_LABEL,
    ).model_dump_json()
    assert scan_for_unlabelled_receipts(body) == []
    unlabelled = re.sub(r'"simulated"\s*:\s*true\s*,', "", body)
    assert unlabelled != body, "the label was never in the serialized body"
    assert "provider_ref" in scan_for_unlabelled_receipts(unlabelled)
    # The HTML limb: the page carries no label marker at all, so a receipt
    # injected into it is the unlabelled case.
    assert "receipt_id" in scan_for_unlabelled_receipts(
        page + '{"receipt_id": "SIM-0001"}'
    )

    # 3. A credential inside a path, in the raw, forward-slash and
    # JSON-escaped forms.
    value = "k9w2m4p7" * 4
    marker = "carerelay_api_" + "token="
    raw = "C:\\Users\\investigator\\" + marker + value
    forward = "C:/Users/investigator/" + marker + value
    escaped = json.dumps({"path": raw})
    assert scan_for_secrets(page + raw), "the scanner missed the raw form"
    assert scan_for_secrets(projection + forward), "the scanner missed the forward form"
    assert scan_for_secrets(escaped), "the scanner missed the JSON-escaped form"
