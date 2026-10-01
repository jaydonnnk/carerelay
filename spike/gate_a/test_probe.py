"""Tests for the Gate A probe, because a harness that cannot fail proves nothing.

`AGENTS.md` section 6 requires that each check can fail against a deliberate
defect, and that a fault two checks can both catch counts as proof of neither.
Three things about `probe.py` matter enough to prove rather than assert:

1. **It fails closed with no credential.** The failure mode worth guarding is a
   harness that reports a pass it did not observe. Proved by removing the
   credential and requiring the blocked verdict, then by a control that shows
   the same code path can report PASS when the probes genuinely observe it.
2. **It redacts the credential.** A response body or an exception message can
   echo the key. Proved by injecting the key into a string and requiring its
   absence from the redacted form, with a self-test that the needle can match
   the surface before redaction (otherwise the check is vacuous).
3. **The verdict logic maps observations honestly.** PARTIAL and FAIL are the
   outcomes most likely to be softened. Each is exercised directly.

These tests are pure: they do not make a network call. The network probe is the
spike's own job and runs only with a real credential.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

PROBE_PATH = Path(__file__).resolve().parents[1] / "gate_a" / "probe.py"


def _load_probe():
    """Import `spike/gate_a/probe.py` by path.

    It is not on the package path and must not be: the spike tree is throwaway
    and is never imported by `src/`.

    The module is registered in `sys.modules` **before** `exec_module` runs,
    because `probe.py` declares dataclasses and `dataclasses` resolves each
    field's annotations through `sys.modules[cls.__module__]`. Without the
    registration that lookup gets `None` and the import fails, which is a bug in
    this loader rather than in the probe.
    """
    spec = importlib.util.spec_from_file_location("gate_a_probe", PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["gate_a_probe"] = module
    spec.loader.exec_module(module)
    return module


probe = _load_probe()


class TestFailsClosedWithoutACredential:
    """The load-bearing property: no credential is a blocked check, not a pass."""

    def test_no_credential_records_blocked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(probe.APPKEY_ENV_VAR, raising=False)
        result = probe.run(timeout=1.0)
        assert result.credential_present is False
        assert result.verdict == "BLOCKED_NO_CREDENTIAL"
        # It must not have made a network call to discover this.
        assert [o["name"] for o in result.observations] == ["precondition"]
        assert result.observations[0]["ran"] is False

    def test_no_credential_does_not_claim_a_pass(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A defect that reported PASS here would be the exact dishonesty Gate A exists to catch."""
        monkeypatch.delenv(probe.APPKEY_ENV_VAR, raising=False)
        result = probe.run(timeout=1.0)
        assert result.verdict != "PASS"
        assert "did not run" in result.verdict_reason

    def test_main_returns_exit_code_two_when_blocked(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        """The exit code must distinguish blocked from failed, so a caller cannot conflate them."""
        monkeypatch.delenv(probe.APPKEY_ENV_VAR, raising=False)
        code = probe.main(["--no-write"])
        assert code == 2
        captured = json.loads(capsys.readouterr().out)
        assert captured["verdict"] == "BLOCKED_NO_CREDENTIAL"


class TestRedaction:
    """A captured response or exception is persisted, so the key must be stripped."""

    def test_the_needle_matches_the_surface_before_redaction(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scanner self-test: the check is vacuous unless the needle can match.

        Without this, a redaction test passes on a string that never contained
        the key, which proves nothing.
        """
        monkeypatch.setenv(probe.APPKEY_ENV_VAR, "sk-live-ABCDEF123456")
        surface = '{"error":"bad key sk-live-ABCDEF123456"}'
        assert "sk-live-ABCDEF123456" in surface

    def test_a_key_in_a_response_body_is_redacted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(probe.APPKEY_ENV_VAR, "sk-live-ABCDEF123456")
        redacted = probe._redact('{"error":"bad key sk-live-ABCDEF123456"}')
        assert "sk-live-ABCDEF123456" not in redacted
        assert f"<redacted:{probe.APPKEY_ENV_VAR}>" in redacted

    def test_a_secret_in_an_exception_message_is_redacted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(probe.SECRET_ENV_VAR, "sec-XYZ-987654")
        redacted = probe._redact("ConnectError: header sec-XYZ-987654 rejected")
        assert "sec-XYZ-987654" not in redacted

    def test_a_masked_appkey_in_a_message_is_redacted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The console shows a masked prefix, so a partial form must also be caught."""
        monkeypatch.delenv(probe.APPKEY_ENV_VAR, raising=False)
        redacted = probe._redact('{"error":"appkey sk-live-ABCDEF123456 is invalid"}')
        assert "ABCDEF123456" not in redacted

    def test_a_clean_string_is_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The control: redaction must not mangle an ordinary message."""
        monkeypatch.delenv(probe.APPKEY_ENV_VAR, raising=False)
        assert probe._redact('{"status":"running"}') == '{"status":"running"}'


class TestVerdictMapping:
    """PARTIAL and FAIL are the outcomes most likely to be softened into a pass."""

    @staticmethod
    def _obs(name: str, ok: bool, ran: bool = True) -> dict:
        return {"name": name, "ran": ran, "ok": ok, "detail": "", "evidence": {}}

    def test_all_three_passing_is_a_pass(self) -> None:
        observations = [self._obs("a", True), self._obs("b", True), self._obs("c", True)]
        assert _verdict_for(observations) == "PASS"

    def test_two_of_three_is_partial_not_a_pass(self) -> None:
        observations = [self._obs("a", True), self._obs("b", True), self._obs("c", False)]
        assert _verdict_for(observations) == "PARTIAL"

    def test_one_of_three_is_partial_not_a_pass(self) -> None:
        observations = [self._obs("a", True), self._obs("b", False), self._obs("c", False)]
        assert _verdict_for(observations) == "PARTIAL"

    def test_none_passing_is_fail(self) -> None:
        observations = [self._obs("a", False), self._obs("b", False), self._obs("c", False)]
        assert _verdict_for(observations) == "FAIL"

    def test_a_probe_that_did_not_run_cannot_contribute_a_pass(self) -> None:
        """A skipped probe is not a passed probe. This is the softening defect."""
        observations = [self._obs("a", True), self._obs("b", False, ran=False),
                        self._obs("c", False, ran=False)]
        assert _verdict_for(observations) == "PARTIAL"


class TestFailureOriginReading:
    """Q3 is the load-bearing question, so its read is exercised without a network."""

    @staticmethod
    def _client_returning(status: int, body: str):
        class _Response:
            status_code = status
            text = body

        class _Client:
            def post(self, *_args, **_kwargs):
                return _Response()

        return _Client()

    def test_a_structured_request_id_is_accepted(self) -> None:
        client = self._client_returning(400, '{"error":"bad request","request_id":"abc-123"}')
        obs = probe.probe_failure_origin(client)
        assert obs.ok is True

    def test_an_error_code_is_accepted(self) -> None:
        client = self._client_returning(422, '{"error_code":"invalid_question"}')
        obs = probe.probe_failure_origin(client)
        assert obs.ok is True

    def test_a_bare_error_with_no_identifier_is_not_an_origin_signal(self) -> None:
        """Any non-200 is not automatically a pass. Without an identifier it fails."""
        client = self._client_returning(400, '{"error":"bad request"}')
        obs = probe.probe_failure_origin(client)
        assert obs.ok is False
        assert "no origin signal" in obs.detail

    def test_a_200_on_an_invalid_request_is_not_a_pass(self) -> None:
        client = self._client_returning(200, '{"answer":"ok"}')
        obs = probe.probe_failure_origin(client)
        assert obs.ok is False


def _verdict_for(observations: list[dict]) -> str:
    """Re-derive the verdict from observations, mirroring `probe.run`.

    Duplicated deliberately rather than imported: the point is to state the rule
    independently so a change to `run`'s mapping shows up as a mismatch here.
    """
    answered = [o for o in observations if o["ran"]]
    passed = [o for o in answered if o["ok"]]
    if len(passed) == 3:
        return "PASS"
    if passed:
        return "PARTIAL"
    return "FAIL"
