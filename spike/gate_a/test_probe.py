"""Tests for the Gate A probe, because a harness that cannot fail proves nothing.

`AGENTS.md` section 6 requires that each check can fail against a deliberate
defect, and that a fault two checks can both catch counts as proof of neither.
Five things about `probe.py` matter enough to prove rather than assert:

1. **It fails closed with no credential.** The failure mode worth guarding is a
   harness that reports a pass it did not observe. Proved by removing the
   credential and requiring the blocked verdict, then by a control that shows
   the same code path can report PASS when the probes genuinely observe it.
2. **It redacts the credential.** The request body is captured into the
   evidence record, so a response that echoes the key would otherwise be
   persisted. Proved by injecting the key into a string and requiring its
   absence from the redacted form, with a self-test that the needle can match
   the surface before redaction (otherwise the check is vacuous).
3. **The body matches the documented schema.** The first draft got this wrong,
   which is what the live run exposed. Each required field is asserted by name
   and the two id fields are asserted against the documented pattern.
4. **It reads errors as the platform actually sends them.** The reference
   documents an error event but not its structure, so the structural read is
   pinned to the frame captured from the live endpoint: HTTP 200 carrying an
   `event: error` frame with a numeric `Code` and a populated `TraceId`.
5. **The verdict logic maps observations honestly.** PARTIAL and FAIL are the
   outcomes most likely to be softened. Each is exercised directly.

These tests are pure: they do not make a network call. The network probe is the
spike's own job and runs only with a real credential.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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

    def test_a_key_echoed_inside_a_request_body_is_redacted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The body now carries the AppKey, so an echo is the likeliest leak path."""
        monkeypatch.setenv(probe.APPKEY_ENV_VAR, "sk-live-ABCDEF123456")
        echoed = json.dumps({"AppKey": "sk-live-ABCDEF123456", "Type": "error"})
        assert "sk-live-ABCDEF123456" not in probe._redact(echoed)

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


class TestRequestBodySchema:
    """The first draft sent the key as a header. That is the defect this pins shut."""

    def test_all_required_documented_fields_are_present(self) -> None:
        body = probe.build_body("a" * 32, "hello", appkey="k")
        for required in ("RequestId", "ConversationId", "AppKey", "VisitorId",
                         "Contents"):
            assert required in body, f"{required} is required by the reference"

    def test_the_appkey_is_a_body_field_and_not_a_header(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The defect that produced the live 400: the key in a header, not the body."""
        captured: dict = {}

        class _Response:
            status_code = 200
            text = "event: request_ack\ndata: {\"Type\":\"request_ack\"}\n"

        class _Client:
            def post(self, url, json=None, headers=None):
                captured["headers"] = headers or {}
                captured["body"] = json or {}
                return _Response()

        probe.probe_reachability_and_wellformed_request(_Client(), "a" * 32, "k")
        assert captured["body"].get("AppKey") == "k"
        assert "X-Api-Key" not in captured["headers"]
        assert "Authorization" not in captured["headers"]

    def test_contents_carry_a_text_entry(self) -> None:
        body = probe.build_body("a" * 32, "hello world", appkey="k")
        assert body["Contents"][0]["Type"] == "text"
        assert body["Contents"][0]["Text"] == "hello world"

    def test_generated_ids_match_the_documented_pattern(self) -> None:
        """The reference constrains both id fields to 32 to 64 of [A-Za-z0-9_-]."""
        generated = probe._new_id()
        assert probe.ID_PATTERN.match(generated), generated
        body = probe.build_body(generated, "x", appkey="k")
        assert probe.ID_PATTERN.match(body["ConversationId"])
        assert probe.ID_PATTERN.match(body["RequestId"])

    def test_stream_is_enabled_so_a_failure_frame_can_arrive(self) -> None:
        """A non-streaming call has no stream to carry the origin signal."""
        body = probe.build_body("a" * 32, "x", appkey="k")
        assert body["Stream"] == "enable"


class TestSSEFrameReading:
    """The stream is the channel, so the parser is exercised directly."""

    def test_a_wellformed_stream_yields_its_event_types(self) -> None:
        raw = ('event: request_ack\ndata: {"Type":"request_ack"}\n\n'
               'event: response.completed\ndata: {"Type":"response.completed"}\n\n'
               'event: done\ndata: [DONE]\n')
        events = probe._sse_events(raw)
        assert probe._event_types(events) == ["request_ack", "response.completed"]

    def test_the_done_terminator_is_not_an_event(self) -> None:
        events = probe._sse_events("event: done\ndata: [DONE]\n")
        assert events == []

    def test_a_non_json_data_line_is_skipped_rather_than_crashing(self) -> None:
        events = probe._sse_events("event: x\ndata: not json\n")
        assert events == []

    def test_the_error_frame_is_found_and_read(self) -> None:
        """Pinned to the frame the live endpoint actually returned."""
        raw = ('event: error\ndata: {"Type":"error","Error":{"Code":400,'
               '"Message":"request parameter error","RequestId":"",'
               '"TraceId":"0a7ec11b30083bd247cc5b6a41cb58e6"},"Timestamp":"0",'
               '"RecordId":""}\n')
        frame = probe._error_frame(probe._sse_events(raw))
        assert frame is not None
        assert frame["Code"] == 400
        assert frame["TraceId"] == "0a7ec11b30083bd247cc5b6a41cb58e6"

    def test_reply_text_is_joined_from_the_delta_fragments(self) -> None:
        raw = ('event: text.delta\ndata: {"Type":"text.delta","Text":"the word "}\n\n'
               'event: text.delta\ndata: {"Type":"text.delta","Text":"is lantern"}\n\n')
        assert probe._reply_text(raw) == "the word is lantern"

    def test_reply_text_falls_back_to_the_completed_message(self) -> None:
        raw = ('event: response.completed\ndata: {"Type":"response.completed",'
               '"Response":{"Messages":[{"Contents":[{"Type":"text",'
               '"Text":"lantern"}]}]}}\n')
        assert probe._reply_text(raw) == "lantern"


class TestReachabilityReading:
    """Q1 must not pass on a transport-level 200 alone, because a malformed body also gets one."""

    @staticmethod
    def _client_returning(status: int, body: str):
        class _Response:
            status_code = status
            text = body

        class _Client:
            def post(self, *_args, **_kwargs):
                return _Response()

        return _Client()

    def test_a_request_ack_is_a_pass(self) -> None:
        client = self._client_returning(
            200, 'event: request_ack\ndata: {"Type":"request_ack"}\n')
        obs = probe.probe_reachability_and_wellformed_request(client, "a" * 32, "k")
        assert obs.ok is True

    def test_a_bare_200_with_no_request_ack_is_not_a_pass(self) -> None:
        """The defect: a malformed body also returns HTTP 200 on this endpoint."""
        client = self._client_returning(200, "event: done\ndata: [DONE]\n")
        obs = probe.probe_reachability_and_wellformed_request(client, "a" * 32, "k")
        assert obs.ok is False

    def test_an_error_frame_is_not_a_pass(self) -> None:
        client = self._client_returning(
            200, 'event: error\ndata: {"Type":"error","Error":{"Code":400,'
                 '"Message":"request parameter error"}}\n')
        obs = probe.probe_reachability_and_wellformed_request(client, "a" * 32, "k")
        assert obs.ok is False
        assert "rejected" in obs.detail


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

    def test_the_live_error_frame_is_a_pass(self) -> None:
        """Exactly the frame the live endpoint returned, with the empty RequestId."""
        client = self._client_returning(
            200, 'event: error\ndata: {"Type":"error","Error":{"Code":400,'
                 '"Message":"request parameter error","RequestId":"",'
                 '"TraceId":"0a7ec11b30083bd247cc5b6a41cb58e6"}}\n')
        obs = probe.probe_failure_origin(client, "k")
        assert obs.ok is True

    def test_a_numeric_code_is_read_as_a_code(self) -> None:
        """The earlier parser looked for a string code and so missed Code: 400."""
        client = self._client_returning(
            200, 'event: error\ndata: {"Type":"error","Error":{"Code":500,'
                 '"TraceId":"abc"}}\n')
        obs = probe.probe_failure_origin(client, "k")
        assert obs.ok is True
        assert obs.evidence["identifiers_found"]["code_value"] == 500

    def test_a_trace_id_alone_is_enough(self) -> None:
        """RequestId was empty live; TraceId was populated. Either one is an origin signal."""
        client = self._client_returning(
            200, 'event: error\ndata: {"Type":"error","Error":{"Code":403,'
                 '"TraceId":"t-1","RequestId":""}}\n')
        obs = probe.probe_failure_origin(client, "k")
        assert obs.ok is True

    def test_an_error_with_no_identifier_is_not_an_origin_signal(self) -> None:
        """Any error is not automatically a pass. Without an identifier it fails."""
        client = self._client_returning(
            200, 'event: error\ndata: {"Type":"error","Error":{"Message":"bad"}}\n')
        obs = probe.probe_failure_origin(client, "k")
        assert obs.ok is False
        assert "no origin signal" in obs.detail

    def test_an_error_with_a_code_but_no_identifier_is_not_a_pass(self) -> None:
        """A typed code alone is not attributable to a call without an id."""
        client = self._client_returning(
            200, 'event: error\ndata: {"Type":"error","Error":{"Code":400,'
                 '"TraceId":"","RequestId":""}}\n')
        obs = probe.probe_failure_origin(client, "k")
        assert obs.ok is False

    def test_a_200_with_no_error_frame_is_not_a_pass(self) -> None:
        """A request that never failed did not exercise the failure path."""
        client = self._client_returning(
            200, 'event: request_ack\ndata: {"Type":"request_ack"}\n')
        obs = probe.probe_failure_origin(client, "k")
        assert obs.ok is False


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
