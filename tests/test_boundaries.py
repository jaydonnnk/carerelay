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
