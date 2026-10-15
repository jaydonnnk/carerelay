"""Slice 18 uses synthetic profiles and fake auth, never a vendor or database."""
import copy
import json
from dataclasses import replace
import time

import pytest

from carerelay import adp_extraction as adp


TEXT = "🙂 go to the clinic; today before six; myself."


def test_offline_prompt_printer_uses_exact_adapter_text_without_credentials(monkeypatch, capsys):
    import os
    from pathlib import Path
    import runpy
    from carerelay.demo.fixture import policy

    script = Path(__file__).resolve().parents[1] / "tools/print_adp_prompt.py"
    assert script.is_file(), "credential-free production-prompt printer is missing"
    sent = []
    original = adp._timed_frames

    def capture(transport, endpoint, body, **kwargs):
        assert transport.provenance == "fake-offline"
        assert endpoint == "http://127.0.0.1/offline-prompt"
        sent.append(body["Contents"][0]["Text"])
        yield from original(transport, endpoint, body, **kwargs)

    def forbidden(*args, **kwargs):
        pytest.fail("prompt printer attempted credential lookup or HTTPS")

    monkeypatch.setattr(adp, "_timed_frames", capture)
    monkeypatch.setattr(adp, "HTTPSConnection", forbidden)
    monkeypatch.setattr(os, "getenv", forbidden)
    runpy.run_path(str(script), run_name="__main__")
    output = capsys.readouterr()
    assert len(sent) == 1 and output.out == sent[0] + "\n" and output.err == ""
    prompt = json.loads(output.out)
    assert prompt["confirmed_words"] == "Myself, today before 6pm, I'll see the doctor"
    assert prompt["instruction_version"] == "carerelay-readback-instruction-v2"
    assert prompt["correlation_id"] == "fictional-console-diagnosis-21"
    assert prompt["schema"]["version"] == "carerelay-readback-v2"
    assert prompt["schema"]["keys"] == ["action_text", "deadline_text", "next_owner_text", "refused", "schema_version", "uncertain_fields"]
    fixture = policy()
    assert prompt["vocabularies"] == {
        "action": sorted(frozenset(fixture.action_aliases) | fixture.permitted_action_ids),
        "deadline": sorted(fixture.deadline_forms),
        "owner": sorted(frozenset(fixture.owner_aliases) | fixture.permitted_owner_ids),
    }
    assert "offline-placeholder-not-a-credential" not in output.out
    assert adp.ADP_EXTRACTION_ENABLED is False


def test_offline_prompt_printer_requires_one_capture(monkeypatch):
    from pathlib import Path
    import runpy

    script = Path(__file__).resolve().parents[1] / "tools/print_adp_prompt.py"
    assert script.is_file(), "credential-free production-prompt printer is missing"
    namespace = runpy.run_path(str(script))
    monkeypatch.setattr(adp.AdpReadbackExtractor, "extract", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="exactly one prompt"):
        namespace["fictional_prompt"]()


def https_transport(monkeypatch, *, status=200, chunks=(b"first", b"second"), fail=None, now=None,
                    after_request=None, after_headers=None, after_read=None, content_type="text/event-stream", close_signal=None):
    """Offline socket double, never a captured or synthetic provider profile."""
    import ssl
    factory = getattr(adp, "HttpsReadbackTransport", None)
    assert callable(factory), "bounded HTTPS transport is missing"
    calls = []
    class Socket:
        def settimeout(self, value): calls.append(("timeout", value))
    class Response:
        def __init__(self): self.status = status; self.parts = iter(chunks)
        def getheader(self, name):
            assert name == "Content-Type"
            return content_type
        def close(self): calls.append(("response_close",))
        def read1(self, size):
            calls.append(("read", size))
            if after_read: after_read()
            return next(self.parts, b"")
    class Connection:
        def __init__(self, host, *, timeout, context):
            assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
            calls.append(("connect", host, timeout)); self.sock = Socket()
        def request(self, method, target, body, headers):
            calls.append(("request", method, target, json.loads(body), headers))
            if fail: raise fail("synthetic failure")
            if after_request: after_request()
        def getresponse(self):
            if after_headers: after_headers()
            return Response()
        def close(self):
            calls.append(("close",))
            if close_signal is not None: close_signal.set()
    monkeypatch.setattr(adp, "HTTPSConnection", Connection)
    return factory(monotonic=(lambda: now[0]) if now else lambda: 10.0), calls


def test_https_transport_preserves_response_media_type(monkeypatch):
    transport, calls = https_transport(monkeypatch, content_type="application/json; charset=utf-8")
    response = transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {}, deadline_monotonic=15, allow_redirects=False)
    list(response.frames)
    assert getattr(response, "content_type", None) == "application/json; charset=utf-8"
    assert calls[-1] == ("close",)


def test_https_transport_one_post_and_bounded_closed_response(monkeypatch):
    transport, calls = https_transport(monkeypatch)
    response = transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat",
        {"AppKey": "test-key", "Contents": [{"Type": "text", "Text": "fictional words"}]},
        deadline_monotonic=15.0, allow_redirects=False)
    assert response.status_code == 200 and list(response.frames) == [b"first", b"second"]
    assert calls[0] == ("connect", "wss.lke.tencentcloud.com", 5.0)
    requests = [call for call in calls if call[0] == "request"]
    assert requests == [("request", "POST", "/adp/v2/chat",
        {"AppKey": "test-key", "Contents": [{"Type": "text", "Text": "fictional words"}]},
        {"Content-Type": "application/json"})]
    reads = [call for call in calls if call[0] == "read"]
    assert len(reads) == 3 and all(0 < call[1] <= 16 * 1024 for call in reads)
    assert calls[-1] == ("close",)


@pytest.mark.parametrize("endpoint", ["http://wss.lke.tencentcloud.com/adp/v2/chat",
    "https://other.invalid/adp/v2/chat", "https://wss.lke.tencentcloud.com/adp/v2/chat?key=test",
    "https://user:pass@wss.lke.tencentcloud.com/adp/v2/chat",
    "https://wss.lke.tencentcloud.com/adp/v2/chat#fragment"])
def test_https_transport_refuses_unapproved_endpoint_before_auth(monkeypatch, endpoint):
    transport, calls = https_transport(monkeypatch)
    with pytest.raises(ValueError):
        transport.open(endpoint, {"AppKey": "test-key"}, deadline_monotonic=15, allow_redirects=False)
    assert calls == []


@pytest.mark.parametrize("status", [301, 302, 307, 308, 401, 500])
def test_https_transport_never_follows_redirect_or_retries(monkeypatch, status):
    transport, calls = https_transport(monkeypatch, status=status)
    response = transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {"AppKey": "test-key"},
        deadline_monotonic=15, allow_redirects=False)
    assert response.status_code == status and list(response.frames) == []
    assert len([call for call in calls if call[0] == "request"]) == 1
    assert not any(call[0] == "read" for call in calls) and calls[-1] == ("close",)


def test_https_transport_refuses_redirect_flag_and_expired_budget(monkeypatch):
    transport, calls = https_transport(monkeypatch)
    with pytest.raises(ValueError):
        transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {}, deadline_monotonic=15, allow_redirects=True)
    with pytest.raises(TimeoutError):
        transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {}, deadline_monotonic=10, allow_redirects=False)
    assert calls == []


@pytest.mark.parametrize("failure", [ConnectionError, TimeoutError])
def test_https_transport_closes_connection_after_open_failure(monkeypatch, failure):
    transport, calls = https_transport(monkeypatch, fail=failure)
    with pytest.raises(failure):
        transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {}, deadline_monotonic=15, allow_redirects=False)
    assert len([call for call in calls if call[0] == "request"]) == 1 and calls[-1] == ("close",)


def test_https_transport_checks_the_same_deadline_during_iteration(monkeypatch):
    now = [10.0]
    transport, calls = https_transport(monkeypatch, now=now)
    response = transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {}, deadline_monotonic=15, allow_redirects=False)
    assert next(response.frames) == b"first"
    now[0] = 15.0
    with pytest.raises(TimeoutError): next(response.frames)
    assert len([call for call in calls if call[0] == "read"]) == 1
    assert calls[-1] == ("close",)


def test_unobserved_https_transport_cannot_claim_a_fake_profile(monkeypatch):
    transport, calls = https_transport(monkeypatch)
    extractor = adp.AdpReadbackExtractor(transport=transport, profile="fake-incremental-v1",
        endpoint="https://wss.lke.tencentcloud.com/adp/v2/chat", app_key="test-key", enabled=True)
    request = adp.ExtractionInput(TEXT, frozenset(), frozenset(), frozenset(), "opaque-correlation",
        "carerelay-readback-instruction-v2", "carerelay-readback-v2")
    result = extractor.extract(request)
    assert result.validation == "invalid" and result.failure_category == "profile" and result.raw is None
    assert result.transport_provenance == "unknown" and calls == []


def test_https_transport_closes_late_headers_without_reading_the_body(monkeypatch):
    now = [10.0]
    transport, calls = https_transport(monkeypatch, now=now, after_headers=lambda: now.__setitem__(0, 15.0))
    with pytest.raises(TimeoutError):
        transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {}, deadline_monotonic=15, allow_redirects=False)
    assert not any(call[0] == "read" for call in calls)
    assert calls[-2:] == [("response_close",), ("close",)]


def test_https_transport_never_yields_bytes_read_after_the_deadline(monkeypatch):
    now = [10.0]
    transport, calls = https_transport(monkeypatch, now=now, after_read=lambda: now.__setitem__(0, 15.0))
    response = transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {}, deadline_monotonic=15, allow_redirects=False)
    with pytest.raises(TimeoutError): next(response.frames)
    assert calls[-2:] == [("response_close",), ("close",)]


def test_https_transport_closes_a_partially_consumed_response(monkeypatch):
    transport, calls = https_transport(monkeypatch)
    response = transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {}, deadline_monotonic=15, allow_redirects=False)
    assert next(response.frames) == b"first"
    response.frames.close()
    assert len([call for call in calls if call[0] == "read"]) == 1
    assert calls[-2:] == [("response_close",), ("close",)]


def test_https_transport_budget_shrinks_after_request_and_headers(monkeypatch):
    now = [10.0]
    transport, calls = https_transport(monkeypatch, now=now,
        after_request=lambda: now.__setitem__(0, 12.0), after_headers=lambda: now.__setitem__(0, 13.0))
    response = transport.open("https://wss.lke.tencentcloud.com/adp/v2/chat", {}, deadline_monotonic=15, allow_redirects=False)
    assert next(response.frames) == b"first"
    assert [call for call in calls if call[0] == "timeout"] == [("timeout", 3.0), ("timeout", 2.0)]
    now[0] = 14.0
    assert next(response.frames) == b"second" and calls[-2] == ("timeout", 1.0)
    response.frames.close()
    assert calls[-2:] == [("response_close",), ("close",)]


def object_for(text=TEXT):
    """Wire schema v2: exact phrase text only; code locates offsets."""
    return {"schema_version": "carerelay-readback-v2", "action_text": "go to the clinic",
            "deadline_text": "today before six", "next_owner_text": "myself",
            "uncertain_fields": [], "refused": False}


def encode(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()


def validator():
    check = getattr(adp, "validate_raw_extraction", None)
    assert callable(check), "strict ADP object validator is missing"
    return check


def test_positive_unicode_object():
    raw = validator()(encode(object_for()), confirmed_text=TEXT)
    assert (raw.action_span.text, raw.action_span.start, raw.action_span.end) == ("go to the clinic", 2, 18)
    assert (raw.deadline_span.start, raw.deadline_span.end) == (20, 36)
    assert (raw.next_owner_span.start, raw.next_owner_span.end) == (38, 44)
    assert raw.uncertain_fields == frozenset() and raw.refused is False


OBJECT_CASES = ["extra", "missing", "version", "v1_keys", "refused_type", "uncertainty_type", "unknown_field",
                "repeated_field", "null_without_uncertainty", "refused_span", "refused_uncertainty",
                "span_object", "text_type", "empty", "canonical", "duplicate_root", "two_objects", "prose",
                "fence", "utf8", "nonfinite", "root_type"]


def invalid_object(case):
    obj = object_for(); text = TEXT
    if case == "extra": obj["advice"] = "forbidden"
    elif case == "missing": del obj["refused"]
    elif case == "version": obj["schema_version"] = "carerelay-readback-v1"
    elif case == "v1_keys":
        obj = {"schema_version": "carerelay-readback-v2", "action_span": {"text": "go to the clinic", "start": 2, "end": 18},
               "deadline_span": None, "next_owner_span": None, "uncertain_fields": ["deadline_utc", "next_owner_id"], "refused": False}
    elif case == "refused_type": obj["refused"] = 0
    elif case == "uncertainty_type": obj["uncertain_fields"] = "action_id"
    elif case == "unknown_field": obj["uncertain_fields"] = ["route"]
    elif case == "repeated_field": obj["uncertain_fields"] = ["action_id", "action_id"]
    elif case == "null_without_uncertainty": obj["action_text"] = None
    elif case == "refused_span": obj["refused"] = True; obj["uncertain_fields"] = list(adp.COMPARISON_FIELDS)
    elif case == "refused_uncertainty":
        obj.update(action_text=None, deadline_text=None, next_owner_text=None, refused=True,
                   uncertain_fields=["action_id", "deadline_utc"])
    elif case == "span_object": obj["action_text"] = {"text": "go to the clinic", "start": 2, "end": 18}
    elif case == "text_type": obj["action_text"] = 1
    elif case == "empty": obj["action_text"] = ""
    elif case == "canonical":
        text = "attend_same_day_review; today before six; myself."
        obj["action_text"] = "attend_same_day_review"
    payload = encode(obj)
    if case == "duplicate_root": payload = payload[:-1] + b',"refused":false}'
    elif case == "two_objects": payload += payload
    elif case == "prose": payload = b"Here is the answer: " + payload
    elif case == "fence": payload = b"```json\n" + payload + b"\n```"
    elif case == "utf8": payload += b"\xff"
    elif case == "nonfinite": payload = payload.replace(b'"refused":false', b'"refused":NaN')
    elif case == "root_type": payload = b"[]"
    return payload, text


@pytest.mark.parametrize("case", OBJECT_CASES)
def test_strict_object(case):
    check = validator()
    assert check(encode(object_for()), confirmed_text=TEXT).action_span.text == "go to the clinic"
    payload, text = invalid_object(case)
    with pytest.raises(ValueError):
        check(payload, confirmed_text=text)


def test_explicit_refusal_and_grounded_uncertainty():
    obj = object_for(); obj["uncertain_fields"] = ["deadline_utc"]
    assert validator()(encode(obj), confirmed_text=TEXT).deadline_span.text == "today before six"
    obj.update(action_text=None, deadline_text=None, next_owner_text=None,
               uncertain_fields=list(adp.COMPARISON_FIELDS), refused=True)
    raw = validator()(encode(obj), confirmed_text=TEXT)
    assert raw.refused and raw.uncertain_fields == frozenset(adp.COMPARISON_FIELDS)


@pytest.mark.parametrize("identifier", ["attend_same_day_review", "call_nurse_line", "wait_and_monitor", "patient", "caregiver"])
def test_all_canonical_fixture_ids_are_not_answers(identifier):
    assert validator()(encode(object_for()), confirmed_text=TEXT).action_span.text == "go to the clinic"
    words = [identifier, "today before six", "myself"] if identifier not in {"patient", "caregiver"} else ["go to the clinic", "today before six", identifier]
    text = "; ".join(words)
    obj = object_for()
    for key, word in zip(("action_text", "deadline_text", "next_owner_text"), words):
        obj[key] = word
    with pytest.raises(ValueError): validator()(encode(obj), confirmed_text=text)


@pytest.mark.parametrize("value,keys", [({"extra": 1}, adp._OBJECT_KEYS), ([], adp._OBJECT_KEYS)])
def test_shape_at_first_boundary(value, keys):
    good = {key: None for key in keys}
    assert adp._exact_keys(good, keys, "shape") == good
    with pytest.raises(ValueError): adp._exact_keys(value, keys, "shape")


@pytest.mark.parametrize("value", ["action_id", [1], None])
def test_uncertainty_types_at_first_boundary(value):
    assert adp._uncertainty_list(["action_id"]) == ["action_id"]
    with pytest.raises(ValueError): adp._uncertainty_list(value)


def test_nonfinite_at_json_boundary():
    assert adp._strict_json(b'{"value":1}') == {"value": 1}
    for value in [b"NaN", b"Infinity", b"-Infinity"]:
        with pytest.raises(ValueError): adp._strict_json(b'{"value":'+value+b'}')


def test_oversized_integer_is_invalid_json_not_transport_failure():
    answer = encode(object_for()).replace(b'"refused":false', b'"refused":' + b"1"*5000).decode()
    transport = FakeTransport([wire(events(answer=answer))])
    result = adapter(transport).extract(request())
    assert result.validation == "invalid" and result.failure_category == "json"
    assert result.raw is None and len(transport.calls) == 1


def request(text=TEXT):
    return adp.ExtractionInput(text, frozenset({"go to the clinic"}), frozenset({"today before six"}),
        frozenset({"myself"}), "fictional-correlation", "fake-instruction-v1", "carerelay-readback-v2")


LIVE_REQUEST = "a" * 32
LIVE_CONVERSATION = "b" * 32
LIVE_DONE = b"event: done\ndata: [DONE]\n\n"


def live_profile_events():
    """Offline redacted shape controls derived from calls 9 onward, never raw reasoning."""
    def event(kind, **values): return {"Type": kind, "Timestamp": 1, "RecordId": "", **values}
    def message(kind, status, *, final=False):
        result = {"Type": kind, "MessageId": kind + "-message", "Name": kind, "Status": status}
        if final:
            result["Contents"] = [{"Type": "text", "Text": encode(object_for()).decode() if kind == "reply" else "OFFLINE_PRIVATE_REASONING_CONTROL"}]
        return result
    def response(status):
        return {"Role": "assistant", "RecordId": "assistant-record", "RelatedRecordId": "user-record",
            "ConversationId": LIVE_CONVERSATION, "Status": status,
            "ExtraInfo": {"RequestId": LIVE_REQUEST, "TraceId": "trace / assistant-record"}}
    done = response("success")
    done.update(Messages=[message("thought", "success", final=True), message("reply", "success", final=True)],
        Procedures=[], StatInfo={})
    rows = [event("request_ack", RequestAck={"Role": "user", "RecordId": "user-record",
        "ConversationId": LIVE_CONVERSATION, "Status": "success", "ExtraInfo": {"RequestId": LIVE_REQUEST}}),
        event("response.created", Response=response("processing"))]
    for kind in ("thought", "reply"):
        identity = {"MessageId": kind + "-message", "ContentIndex": 0}
        rows += [event("message.added", Message=message(kind, "processing")),
            event("content.added", **identity, Content={"Type": "text"}),
            event("text.delta", **identity, Text="OFFLINE_PRIVATE_REASONING_CONTROL" if kind == "thought" else "not a final object"),
            event("message.processing", MessageId=kind + "-message", Message=message(kind, "processing")),
            event("message.done", MessageId=kind + "-message", Message=message(kind, "success", final=True))]
    return rows + [event("response.completed", Response=done)]


def parse_live(rows=None, *, tail=LIVE_DONE, chunks=None, monotonic=lambda: 0):
    parse = getattr(adp, "_assemble_live_answer", None)
    assert callable(parse), "observed live complete-answer parser is missing"
    return parse(chunks if chunks is not None else [wire(rows if rows is not None else live_profile_events()) + tail],
        request_id=LIVE_REQUEST, conversation_id=LIVE_CONVERSATION, deadline_monotonic=15,
        monotonic=monotonic)


def test_live_profile_uses_only_the_matching_complete_reply():
    answer = parse_live()
    assert answer.payload == encode(object_for())
    assert answer.trace_id == "trace / assistant-record" and answer.model_version is None
    assert b"OFFLINE_PRIVATE_REASONING_CONTROL" not in answer.payload


LIVE_CASES = ["ack_request", "ack_conversation", "ack_role", "ack_status", "missing_ack", "duplicate_ack",
    "response_id", "response_request", "response_conversation", "response_role", "response_status", "related_record",
    "unknown_event", "tool_message", "content_message", "content_index", "content_type", "unknown_channel",
    "text_type", "processing_id", "processing_inner_id", "missing_content", "duplicate_done", "multiple_final", "missing_done",
    "terminal_payload", "terminal_message", "missing_terminal", "missing_sentinel", "early_sentinel", "after_terminal", "after_sentinel",
    "after_sentinel_done", "provider_error"]


@pytest.mark.parametrize("case", LIVE_CASES)
def test_live_profile_refuses_each_unrecognised_or_incomplete_shape(case):
    assert parse_live().payload == encode(object_for())
    rows = copy.deepcopy(live_profile_events()); tail = LIVE_DONE
    if case == "ack_request": rows[0]["RequestAck"]["ExtraInfo"]["RequestId"] = "other"
    elif case == "ack_conversation": rows[0]["RequestAck"]["ConversationId"] = "other"
    elif case == "ack_role": rows[0]["RequestAck"]["Role"] = "assistant"
    elif case == "ack_status": rows[0]["RequestAck"]["Status"] = "processing"
    elif case == "missing_ack": rows.pop(0)
    elif case == "duplicate_ack": rows.insert(1, copy.deepcopy(rows[0]))
    elif case == "response_id": rows[-1]["Response"]["RecordId"] = "other"
    elif case == "response_request": rows[-1]["Response"]["ExtraInfo"]["RequestId"] = "other"
    elif case == "response_conversation": rows[-1]["Response"]["ConversationId"] = "other"
    elif case == "response_role": rows[-1]["Response"]["Role"] = "user"
    elif case == "response_status": rows[-1]["Response"]["Status"] = "processing"
    elif case == "related_record": rows[-1]["Response"]["RelatedRecordId"] = "other"
    elif case == "unknown_event": rows.insert(3, {"Type": "new-provider-event", "Timestamp": 1, "RecordId": ""})
    elif case == "tool_message":
        # Rename the whole thought message consistently, so only the channel allowlist can refuse it.
        for row in rows:
            for message in [row.get("Message")] + row.get("Response", {}).get("Messages", []):
                if message and message["MessageId"] == "thought-message": message["Type"] = "tool_call"
    elif case == "content_message": rows[3]["MessageId"] = "other"
    elif case == "content_index": rows[3]["ContentIndex"] = True
    elif case == "content_type": rows[3]["Content"]["Type"] = "image"
    elif case == "unknown_channel": rows[3]["Channel"] = "unknown"
    elif case == "text_type": rows[4]["Text"] = 7
    elif case == "processing_id": rows[5]["MessageId"] = "other"
    elif case == "processing_inner_id": rows[5]["Message"]["MessageId"] = "other"
    elif case == "missing_content": rows.pop(3)
    elif case == "duplicate_done": rows.insert(7, copy.deepcopy(rows[6]))
    elif case == "multiple_final":
        extra = copy.deepcopy(rows[7]); extra["Message"]["MessageId"] = "second-final"; rows.insert(8, extra)
    elif case == "missing_done": rows.pop(-2)
    elif case == "terminal_payload": rows[-1]["Response"]["Messages"][-1]["Contents"][0]["Text"] = "{}"
    elif case == "terminal_message": rows[-1]["Response"]["Messages"][-1]["MessageId"] = "other"
    elif case == "missing_terminal": rows.pop()
    elif case == "missing_sentinel": tail = b""
    elif case == "early_sentinel":
        with pytest.raises(ValueError): parse_live(chunks=[wire(rows[:1]) + tail])
        return
    elif case == "after_terminal": tail = wire([{"Type": "response.processing", "Response": rows[-1]["Response"]}]) + tail
    elif case == "after_sentinel": tail += wire([{"Type": "heartbeat"}])
    elif case == "after_sentinel_done": tail += LIVE_DONE
    elif case == "provider_error": rows.insert(2, {"Type": "error", "Timestamp": 1, "RecordId": ""})
    with pytest.raises(ValueError): parse_live(rows, tail=tail)


def test_live_profile_terminal_after_the_single_deadline_is_unavailable():
    now = [0.0]
    rows = live_profile_events()
    def chunks():
        yield wire(rows[:-1])
        now[0] = 15.0
        yield wire(rows[-1:]) + LIVE_DONE
    with pytest.raises(TimeoutError): parse_live(chunks=chunks(), monotonic=lambda: now[0])


def live_adapter(monkeypatch, **transport_options):
    from types import SimpleNamespace
    identities = iter((LIVE_REQUEST, LIVE_CONVERSATION, "c" * 32))
    monkeypatch.setattr(adp, "uuid4", lambda: SimpleNamespace(hex=next(identities)))
    transport, calls = https_transport(monkeypatch,
        chunks=(wire(live_profile_events()) + LIVE_DONE,), **transport_options)
    extractor = adp.AdpReadbackExtractor(transport=transport, profile="adp-sse-final-throttle100-v1",
        endpoint="https://wss.lke.tencentcloud.com/adp/v2/chat", app_key="test-key", enabled=True,
        monotonic=lambda: 10.0)
    return extractor, calls


def live_request():
    return replace(request(), instruction_version="carerelay-readback-instruction-v2")


@pytest.mark.parametrize("required", [
    "with exactly these six keys: schema_version, action_text, deadline_text, next_owner_text, uncertain_fields, refused.",
    'schema_version must be the string "carerelay-readback-v2".',
    "Never use an object, array, number or boolean for those three text fields.",
    "uncertain_fields must be an array containing only the field names action_id, deadline_utc and next_owner_id, with no duplicates.",
    "refused must be a JSON boolean.",
    "No advice, prose, markdown, code fences or trailing punctuation outside the JSON.",
    "Do not echo instruction, instruction_version, schema, correlation_id, confirmed_words or vocabularies as output keys.",
], ids=["keys", "version", "text_types", "uncertainty", "refusal", "json_only", "metadata"])
def test_live_request_explicitly_instructs_the_approved_output_shape(monkeypatch, required):
    # Deleting a constraint from the actual outbound request must fail here.
    # This proves prompt delivery, not the vendor model's compliance.
    extractor, calls = live_adapter(monkeypatch)
    result = extractor.extract(live_request())
    assert result.validation == "valid"
    sent = [call for call in calls if call[0] == "request"]
    assert len(sent) == 1
    prompt = json.loads(sent[0][3]["Contents"][0]["Text"])
    assert required in prompt["instruction"]
    assert set(prompt) == {"instruction", "instruction_version", "schema", "correlation_id", "confirmed_words", "vocabularies"}
    assert prompt["confirmed_words"] == TEXT
    assert prompt["instruction_version"] == "carerelay-readback-instruction-v2"
    assert prompt["schema"]["keys"] == ["action_text", "deadline_text", "next_owner_text", "refused", "schema_version", "uncertain_fields"]


@pytest.mark.parametrize("budget,expected", [(None, 15.0), (30, 15.0), (3, 3.0)])
def test_live_adapter_uses_pinned_request_profile_and_single_budget(monkeypatch, budget, expected):
    extractor, calls = live_adapter(monkeypatch)
    result = extractor.extract(live_request(), **({} if budget is None else {"budget_seconds": budget}))
    assert result.validation == "valid" and result.raw.action_span.text == "go to the clinic"
    assert result.transport_profile == "adp-sse-final-throttle100-v1" and result.transport_provenance == "https"
    assert result.model_version is None and adp.trusted_adp_result(result)
    assert extractor.instruction_version == "carerelay-readback-instruction-v2"
    requests = [call for call in calls if call[0] == "request"]
    assert len(requests) == 1 and calls[0] == ("connect", "wss.lke.tencentcloud.com", expected)
    body = requests[0][3]
    assert body["Stream"] == "enable" and body["Incremental"] is True and body.get("StreamingThrottle") == 100
    assert (body["RequestId"], body["ConversationId"], body["VisitorId"]) == (LIVE_REQUEST, LIVE_CONVERSATION, "c" * 32)
    assert "test-key" not in body["Contents"][0]["Text"]


def test_live_adapter_refuses_a_forged_https_transport_before_auth(monkeypatch):
    extractor, _ = live_adapter(monkeypatch)
    assert extractor.extract(live_request()).validation == "valid"
    from uuid import uuid4 as real_uuid4
    monkeypatch.setattr(adp, "uuid4", real_uuid4)
    transport = FakeTransport(); transport.provenance = "https"
    fake = adp.AdpReadbackExtractor(transport=transport, profile="adp-sse-final-throttle100-v1",
        endpoint="https://wss.lke.tencentcloud.com/adp/v2/chat", app_key="test-key", enabled=True)
    assert fake.extract(live_request()).validation == "invalid" and transport.calls == []


def test_live_adapter_rejects_wrong_media_without_fallback(monkeypatch):
    extractor, calls = live_adapter(monkeypatch, content_type="text/html")
    result = extractor.extract(live_request())
    assert result.validation == "invalid" and result.failure_category == "response_media_type" and result.raw is None
    assert len([call for call in calls if call[0] == "request"]) == 1


def test_wrong_response_media_closes_before_any_body_is_read(monkeypatch):
    from threading import Event
    closed = Event()
    transport, calls = https_transport(monkeypatch, content_type="text/html", close_signal=closed)
    with pytest.raises(adp.ExtractionInvalid, match="response_media_type"):
        list(adp._timed_frames(transport, "https://wss.lke.tencentcloud.com/adp/v2/chat", {},
            deadline_monotonic=15, monotonic=lambda: 10.0, expected_media_type="text/event-stream"))
    assert closed.wait(1) and not any(call[0] == "read" for call in calls)


def test_live_adapter_rejects_instruction_mismatch_before_call(monkeypatch):
    extractor, calls = live_adapter(monkeypatch)
    result = extractor.extract(request())
    assert result.validation == "invalid" and result.failure_category == "instruction_version" and calls == []


@pytest.mark.parametrize("flag,want_mode,want_validation", [(None, "local-sim", "valid"),
    ("false", "local-sim", "valid"), ("true", "adp", "invalid"), ("ture", "adp", "disabled")])
def test_backend_configuration_is_default_off_and_never_falls_back(flag, want_mode, want_validation):
    factory = getattr(adp, "configured_readback_extractor", None)
    assert callable(factory), "backend extraction configuration is missing"
    config = {} if flag is None else {"ADP_EXTRACTION_ENABLED": flag}
    extractor = factory(config)
    result = extractor.extract(live_request())
    assert (result.mode, result.validation) == (want_mode, want_validation)
    if want_mode == "adp": assert result.raw is None


def envelope(kind, **values):
    return {"Type": kind, "CorrelationId": "fictional-correlation", **values}


def events(*, complete=False, answer=None):
    identity = {"MessageId": "assistant-1", "ContentId": "answer-1", "Channel": "final_answer"}
    answer = encode(object_for()).decode() if answer is None else answer
    frames = [envelope("request_ack"), envelope("response.created"),
              envelope("message.added", MessageId="assistant-1", Role="assistant"),
              envelope("content.added", **identity)]
    if complete:
        frames.append(envelope("text.final", **identity, Text=answer))
    else:
        frames.append(envelope("text.delta", **identity, Sequence=0, Text=answer))
    frames.extend([envelope("message.done", MessageId="assistant-1"), envelope("response.done")])
    return frames


def wire(frames, *, multiline=False):
    output = b""
    for item in frames:
        data = json.dumps(item, ensure_ascii=False, indent=2 if multiline else None)
        output += b"event: " + item["Type"].encode() + b"\n"
        output += b"\n".join(b"data: " + line.encode() for line in data.split("\n")) + b"\n\n"
    return output


class FakeTransport:
    provenance = "fake-offline"

    def __init__(self, frames=None, *, status=200, wait=0, explode=False):
        self.frames = [wire(events())] if frames is None else frames
        self.status, self.wait, self.explode = status, wait, explode
        self.calls = []

    def open(self, endpoint, body, *, deadline_monotonic, allow_redirects):
        self.calls.append((endpoint, body, deadline_monotonic, allow_redirects))
        if self.wait: time.sleep(self.wait)
        if self.explode: raise RuntimeError("SYNTHETIC_SECRET_REASONING")
        return adp.TransportResponse(self.status, self.frames)


def adapter(transport=None, *, profile="fake-incremental-v1", enabled=True, **kwargs):
    cls = getattr(adp, "AdpReadbackExtractor", None)
    assert callable(cls), "strict fake ADP adapter is missing"
    return cls(transport=transport or FakeTransport(), profile=profile, enabled=enabled,
               endpoint="https://fake.invalid/readback", app_key="synthetic-app-key", **kwargs)


@pytest.mark.parametrize("complete", [False, True])
def test_positive_fake_profiles(complete):
    transport = FakeTransport([wire(events(complete=complete), multiline=True)])
    result = adapter(transport, profile="fake-complete-v1" if complete else "fake-incremental-v1").extract(request())
    assert (result.mode, result.validation) == ("adp", "valid")
    assert result.raw is not None and result.raw.action_span is not None
    assert result.raw.action_span.text == "go to the clinic" and len(transport.calls) == 1
    assert result.transport_profile == ("fake-complete-v1" if complete else "fake-incremental-v1")
    assert result.transport_provenance == "fake-offline" and result.model_version is None


def test_stateless_request_and_disabled_zero_calls():
    transport = FakeTransport(); extractor = adapter(transport)
    a, b = extractor.extract(request()), extractor.extract(request())
    assert a.validation == b.validation == "valid"
    import re
    identities = []
    for endpoint, body, deadline, redirects in transport.calls:
        assert endpoint == "https://fake.invalid/readback" and redirects is False
        assert set(body) == {"AppKey", "Contents", "Stream", "Incremental", "ConversationId", "RequestId", "VisitorId"}
        assert body["AppKey"] == "synthetic-app-key" and body["Stream"] is True and body["Incremental"] is True
        assert re.fullmatch(r"[A-Za-z0-9_-]{32,64}", body["ConversationId"])
        assert re.fullmatch(r"[A-Za-z0-9_-]{32,64}", body["RequestId"])
        assert body["AppKey"] not in body["Contents"][0]["Text"]
        prompt = json.loads(body["Contents"][0]["Text"])
        assert set(prompt) == {"instruction", "instruction_version", "schema", "correlation_id", "confirmed_words", "vocabularies"}
        assert prompt["confirmed_words"] == TEXT and prompt["vocabularies"]["action"] == ["go to the clinic"]
        identities.extend([body["ConversationId"], body["RequestId"], body["VisitorId"]])
    assert len(set(identities)) == 6
    before = len(transport.calls)
    assert adapter(transport, enabled=False).extract(request()).validation == "disabled"
    assert len(transport.calls) == before and adp.ADP_EXTRACTION_ENABLED is False


def test_utf8_chunk_boundaries_and_crlf_multiline():
    payload = wire(events(), multiline=True).replace(b"\n", b"\r\n")
    result = adapter(FakeTransport([bytes([value]) for value in payload])).extract(request())
    assert result.validation == "valid" and result.raw.action_span.start == 2


def test_sse_unicode_separators_are_data_and_cr_is_a_line_end():
    frames = events()
    frames.insert(4, envelope("content.added", MessageId="assistant-1", ContentId="reason-1", Channel="reasoning"))
    frames.insert(5, envelope("text.delta", MessageId="assistant-1", ContentId="reason-1", Channel="reasoning", Sequence=0, Text="reason\u2028line\u2029line"))
    for payload in [wire(frames), wire(frames).replace(b"\n", b"\r")]:
        result = adapter(FakeTransport([bytes([value]) for value in payload])).extract(request())
        assert result.validation == "valid" and result.raw.action_span.text == "go to the clinic"


def test_scoring_refuses_nested_transactions_before_claim_or_transport(tmp_path):
    from test_field_repair import make_service, start_readback, confirm, KEY, verify_operation
    from carerelay.state import StateError
    service = make_service(tmp_path / "nested.sqlite"); transport = ScenarioTransport()
    service._readback_extractor = adapter(transport)
    try:
        ep = start_readback(service); confirm(service, ep, "go to the clinic today before six myself")
        token = next(o.operation_token for o in service.project_journey(ep).commands if o.kind == "score_words")
        binding = verify_operation(token, signing_key=KEY)
        with service._store.journey_transaction(ep, write=True):
            with pytest.raises(StateError): service.score_confirmed(binding)
        assert transport.calls == [] and service._store.list_restatements(ep) == ()
        assert service.score_confirmed(binding).receipt.scored and len(transport.calls) == 1
        assert service.score_confirmed(binding).receipt.replayed and len(transport.calls) == 1
    finally:
        service._store.close()


def test_final_score_requires_its_own_committing_transaction(tmp_path):
    from test_field_repair import make_service, start_readback, confirm, score
    from carerelay.state import StateError
    service = make_service(tmp_path / "nested-final.sqlite"); transport = ScenarioTransport()
    strict = adapter(transport)
    outer = []

    class OpensOuterAfterExtraction:
        instruction_version = strict.instruction_version
        schema_version = strict.schema_version
        def extract(self, req, **kwargs):
            result = strict.extract(req, **kwargs)
            assert result.validation == "valid"
            scope = service._store.journey_transaction(ep, write=True)
            scope.__enter__(); outer.append(scope)
            return result
    service._readback_extractor = OpensOuterAfterExtraction()
    try:
        ep = start_readback(service); confirm(service, ep, "go to the clinic today before six myself")
        with pytest.raises(StateError): score(service, ep)
        assert len(transport.calls) == 1 and service._store.list_restatements(ep) == ()
    finally:
        for scope in outer: scope.__exit__(None, None, None)
        service._store.close()


@pytest.mark.parametrize("repair,matched", [("today before six", True), ("today before six. Actually I won't.", False)])
def test_fake_timing_repair_retention_and_whole_answer_doubt(tmp_path, repair, matched):
    from test_field_repair import make_service, start_readback, confirm, score
    service = make_service(tmp_path / "fake-repair.sqlite"); transport = ScenarioTransport()
    service._readback_extractor = adapter(transport)
    try:
        ep = start_readback(service); confirm(service, ep, "go to the clinic tomorrow before 6pm myself")
        assert score(service, ep)[1].journey.step == "repair"
        confirm(service, ep, repair); result = score(service, ep)[1]
        assert result.receipt.scored and result.journey.flow.completed_repairs == 1
        rows = service._store.list_restatements(ep)
        assert rows[-1].comparison.is_clean() is matched and len(rows) == 2
        assert rows[-1].comparison.uncertain == (frozenset() if matched else frozenset(adp.COMPARISON_FIELDS))
        assert len(rows[-1].provenance["retained"]) == (2 if matched else 0)
        assert len(transport.calls) == 2 and service._store.list_attempts(ep) == ()
    finally:
        service._store.close()


SSE_CASES = ["error", "correlation", "role", "message", "content", "channel", "unknown_event", "order",
             "missing_terminal", "early_terminal", "duplicate_final", "delta_final", "duplicate_sequence",
             "sequence_gap", "sequence_type", "truncated", "invalid_utf8", "duplicate_json", "unknown_sse",
             "event_mismatch", "after_terminal", "missing_done", "empty_answer"]


def bad_stream(case):
    frames = events()
    if case == "error": frames.insert(1, envelope("error"))
    elif case == "correlation": frames[4]["CorrelationId"] = "other"
    elif case == "role": frames[2]["Role"] = "user"
    elif case == "message": frames[4]["MessageId"] = "other"
    elif case == "content": frames[4]["ContentId"] = "other"
    elif case == "channel": frames[4]["Channel"] = "unknown"
    elif case == "unknown_event": frames[4]["Type"] = "unverified.vendor.event"
    elif case == "order": frames[0], frames[1] = frames[1], frames[0]
    elif case == "missing_terminal": frames.pop()
    elif case == "early_terminal": frames.insert(4, frames.pop())
    elif case == "duplicate_final": frames.insert(5, envelope("text.final", MessageId="assistant-1", ContentId="answer-1", Channel="final_answer", Text="{}"))
    elif case == "delta_final": frames[4]["Type"] = "text.final"; del frames[4]["Sequence"]
    elif case == "duplicate_sequence": frames.insert(5, {**frames[4], "Text": "different"})
    elif case == "sequence_gap": frames[4]["Sequence"] = 1
    elif case == "sequence_type": frames[4]["Sequence"] = False
    elif case == "after_terminal": frames.append(envelope("heartbeat"))
    elif case == "missing_done": del frames[5]
    elif case == "empty_answer": frames[4]["Text"] = ""
    payload = wire(frames)
    if case == "truncated": payload = payload[:-1]
    elif case == "invalid_utf8": payload = payload.replace(b'"go to', b'"\xffgo to')
    elif case == "duplicate_json": payload = payload.replace(b'"Type": "request_ack"', b'"Type": "request_ack", "Type": "request_ack"')
    elif case == "unknown_sse": payload = b"retry: 0\n" + payload
    elif case == "event_mismatch": payload = payload.replace(b"event: request_ack", b"event: message.done")
    return payload


@pytest.mark.parametrize("case", SSE_CASES)
def test_sse_envelope(case):
    assert adapter().extract(request()).validation == "valid"
    transport = FakeTransport([bad_stream(case)])
    result = adapter(transport).extract(request())
    assert result.validation == "invalid" and result.raw is None
    assert len(transport.calls) == 1


def test_identical_sequence_is_deduped_and_reasoning_discarded():
    frames = events()
    frames.insert(4, envelope("content.added", MessageId="assistant-1", ContentId="reason-1", Channel="reasoning"))
    frames.insert(5, envelope("text.delta", MessageId="assistant-1", ContentId="reason-1", Channel="reasoning", Sequence=0, Text="SYNTHETIC_SECRET_REASONING"))
    frames.insert(7, dict(frames[6]))
    result = adapter(FakeTransport([wire(frames)])).extract(request())
    assert result.validation == "valid" and "SYNTHETIC_SECRET_REASONING" not in repr(result)


def test_whole_budget_covers_connect_and_blocked_iterator():
    for transport in [FakeTransport(wait=.1), FakeTransport(iter([wire(events())]))]:
        if not transport.wait:
            def delayed():
                yield wire(events()[:-1]); time.sleep(.1); yield wire(events()[-1:])
            transport.frames = delayed()
        started = time.monotonic()
        result = adapter(transport).extract(request(), budget_seconds=.025)
        assert result.validation == "timeout" and result.raw is None
        assert time.monotonic() - started < .09 and len(transport.calls) == 1


@pytest.mark.parametrize("status", [301, 401, 500, 200.0])
def test_no_redirect_or_retry(status):
    transport = FakeTransport(status=status)
    result = adapter(transport).extract(request())
    assert result.validation == "transport" and result.raw is None and len(transport.calls) == 1


def test_transport_failure_is_bounded_and_never_falls_back():
    transport = FakeTransport(explode=True)
    result = adapter(transport).extract(request())
    assert result.validation == "transport" and result.raw is None and len(transport.calls) == 1
    assert "SYNTHETIC_SECRET_REASONING" not in repr(result)


class ScenarioTransport(FakeTransport):
    """Explicit scripted fictional answers, not a production lexical fallback."""
    def __init__(self, *, failure=None):
        super().__init__(); self.failure = failure

    def open(self, endpoint, body, *, deadline_monotonic, allow_redirects):
        self.calls.append((endpoint, body, deadline_monotonic, allow_redirects))
        prompt = json.loads(body["Contents"][0]["Text"])
        text = prompt["confirmed_words"]
        values = []
        for words in [("go to the clinic",), ("today before six", "tomorrow before 6pm"), ("myself",)]:
            word = next((value for value in words if value in text), None)
            values.append(word)
        obj = {"schema_version": "carerelay-readback-v2", "action_text": values[0], "deadline_text": values[1],
               "next_owner_text": values[2], "uncertain_fields": [field for field, span in zip(adp.COMPARISON_FIELDS, values) if span is None], "refused": False}
        if self.failure == "invalid": obj["advice"] = "SYNTHETIC_SECRET_REASONING"
        elif self.failure == "refused": obj.update(action_text=None, deadline_text=None, next_owner_text=None, uncertain_fields=list(adp.COMPARISON_FIELDS), refused=True)
        frames = events(answer=encode(obj).decode())
        for item in frames: item["CorrelationId"] = prompt["correlation_id"]
        return adp.TransportResponse(200, [wire(frames)])


@pytest.mark.parametrize("text,step,matched,mismatched,uncertain", [
    ("go to the clinic today before six myself", "barrier", set(adp.COMPARISON_FIELDS), set(), set()),
    ("go to the clinic tomorrow before 6pm myself", "repair", {"action_id", "next_owner_id"}, {"deadline_utc"}, set()),
    ("go to the clinic myself", "readback", {"action_id", "next_owner_id"}, set(), {"deadline_utc"}),
    ("I won't go to the clinic today before six myself", "readback", set(), set(), set(adp.COMPARISON_FIELDS)),
])
def test_service_positive_negative_independent_controls(tmp_path, text, step, matched, mismatched, uncertain):
    from test_field_repair import make_service, start_readback, confirm, score
    service = make_service(tmp_path / "adp.sqlite"); transport = ScenarioTransport()
    service._readback_extractor = adapter(transport)
    try:
        ep = start_readback(service); confirm(service, ep, text)
        binding, result = score(service, ep)
        assert result.receipt.scored and result.journey.step == step
        rows = service._store.list_restatements(ep)
        assert len(rows) == 1
        assert rows[0].comparison.matched == frozenset(matched)
        assert rows[0].comparison.mismatched == frozenset(mismatched)
        assert rows[0].comparison.uncertain == frozenset(uncertain)
        assert rows[0].provenance["mode"] == "adp"
        assert rows[0].provenance["interpreter"]["transport_profile"] == "fake-incremental-v1"
        assert rows[0].provenance["transport_provenance"] == "fake-offline"
        assert len(transport.calls) == 1 and service._store.list_attempts(ep) == ()
        replay = service.score_confirmed(binding)
        assert replay.receipt.replayed and len(transport.calls) == 1
        assert result.journey.outcome.care_evidenced is False
    finally:
        service._store.close()


@pytest.mark.parametrize("failure", ["invalid", "refused", "disabled"])
def test_unavailable_preserves_saved_plan_and_no_round(tmp_path, failure):
    from test_field_repair import make_service, start_readback, confirm, score
    service = make_service(tmp_path / "unavailable.sqlite"); transport = ScenarioTransport(failure=failure)
    service._readback_extractor = adapter(transport, enabled=failure != "disabled")
    try:
        ep = start_readback(service); saved = confirm(service, ep, "go to the clinic today before six myself")
        before = service._store.load_snapshot(ep)
        binding, result = score(service, ep)
        assert result.receipt.state == "unavailable" and not result.receipt.scored
        assert result.journey.flow.completed_repairs == 0 and not result.journey.flow.stopped
        assert result.journey.question == saved.journey.question
        assert result.journey.text["feedback"] == "We could not check that answer just now. Your plan has not changed."
        after = service._store.load_snapshot(ep)
        assert after.disposition == before.disposition and after.flow_stop_reason == before.flow_stop_reason
        assert service._store.list_restatements(ep) == () and service._store.list_attempts(ep) == ()
        stored = service._store.load_journey_bundle(ep).commands[-1]
        assert stored["transport_profile"] == "fake-incremental-v1" and stored["interpreter_mode"] == "adp"
        assert stored["model_version"] is None and stored["validation"] == failure
        entries = service.project_ledger(ep).as_dict().get("extractions")
        assert isinstance(entries, list) and len(entries) == 1
        entry = entries[-1]
        assert entry.get("transport_provenance") == "fake-offline"
        assert entry.get("correlation_id") == binding.operation_id and entry.get("validation") == failure
        assert "SYNTHETIC_SECRET_REASONING" not in json.dumps(service.project_ledger(ep).as_dict())
        assert len(transport.calls) == (0 if failure == "disabled" else 1)
    finally:
        service._store.close()


def incremental_payload(answer):
    frames = events()
    identity = {key: frames[4][key] for key in ("MessageId", "ContentId", "Channel")}
    chunks = [envelope("text.delta", **identity, Sequence=index, Text=answer[offset:offset+1000])
              for index, offset in enumerate(range(0, len(answer), 1000))]
    return wire(frames[:4] + chunks + frames[5:])


@pytest.mark.parametrize("case", ["input", "answer", "frame", "wire"])
def test_limits_exact_and_independent_plus_one(case):
    if case == "input":
        text = TEXT + " " * (2048-len(TEXT)); transport = FakeTransport()
        good = adapter(transport).extract(request(text))
        assert good.validation == "valid" and len(transport.calls) == 1
        bad = adapter(transport).extract(request(text + " "))
        assert bad.validation == "invalid" and bad.failure_category == "input_limit" and len(transport.calls) == 1
        return
    if case == "answer":
        answer = encode(object_for()).decode()
        answer += " " * (16384 - len(answer.encode()))
        good_wire, bad_wire = incremental_payload(answer), incremental_payload(answer + " ")
    elif case == "frame":
        base = wire(events()[:1])[:-2]
        padded = b":" + b"x" * (16384 - len(base) - 2) + b"\n" + base
        assert len(padded) == 16384
        good_wire = padded + b"\n\n" + wire(events()[1:])
        bad_wire = b":" + b"x" + padded[1:] + b"\n\n" + wire(events()[1:])
    else:
        base = wire(events())
        padding = bytearray()
        remaining = 65536-len(base)
        while remaining:
            heartbeat = wire([envelope("heartbeat")])
            size = min(remaining, 16000)
            assert size >= len(heartbeat)+2
            padding.extend(b":" + b"x" * (size-len(heartbeat)-2) + b"\n" + heartbeat)
            remaining -= size
        good_wire = bytes(padding) + base
        assert len(good_wire) == 65536
        bad_wire = b":" + b"x" + good_wire[1:]
    assert adapter(FakeTransport([good_wire])).extract(request()).validation == "valid"
    result = adapter(FakeTransport([bad_wire])).extract(request())
    assert result.validation == "invalid" and result.failure_category == case + "_limit"


def test_terminal_at_five_seconds_refuses_without_reset():
    class Clock:
        value = 0
        def __call__(self): return self.value
    for terminal_time, passes in [(4.999, True), (5, False), (5.001, False)]:
        clock = Clock()
        def chunks():
            clock.value = .1; yield wire(events()[:-1])
            clock.value = terminal_time; yield wire(events()[-1:])
        if passes:
            assert adp.assemble_answer(chunks(), correlation_id="fictional-correlation", deadline_monotonic=5, monotonic=clock) == encode(object_for())
        else:
            with pytest.raises(TimeoutError):
                adp.assemble_answer(chunks(), correlation_id="fictional-correlation", deadline_monotonic=5, monotonic=clock)


def test_unknown_profile_and_transport_never_call():
    transport = FakeTransport()
    assert adapter(transport, profile="observed-live-unverified").extract(request()).validation == "invalid"
    assert transport.calls == []
    transport.provenance = "unverified-live"
    assert adapter(transport).extract(request()).validation == "invalid" and transport.calls == []


def test_forged_adp_result_and_tampered_grounding_are_ineligible():
    raw = validator()(encode(object_for()), confirmed_text=TEXT)
    forged = adp.ExtractionResult("adp", "valid", raw, "fake", None, "fake", adp.SCHEMA_VERSION, None, None,
        transport_profile="fake-incremental-v1", transport_provenance="fake-offline")
    assert adp.eligible_adp_output(forged, confirmed_text=TEXT) is None
    valid = adapter().extract(request())
    assert adp.eligible_adp_output(valid, confirmed_text=TEXT) == raw
    assert adp.eligible_adp_output(replace(valid, transport_profile="unverified-live"), confirmed_text=TEXT) is None
    assert adp.eligible_adp_output(replace(valid, transport_provenance="unverified-live"), confirmed_text=TEXT) is None
    assert adp.eligible_adp_output(replace(valid, mode="local-sim"), confirmed_text=TEXT) is None
    assert adp.eligible_adp_output(replace(valid, validation="invalid"), confirmed_text=TEXT) is None
    assert adp.eligible_adp_output(valid, confirmed_text=TEXT, correlation_id="different-operation") is None
    assert adp.eligible_offline_output(valid, confirmed_text=TEXT) is None
    assert adp.eligible_adp_output(replace(valid, raw=replace(raw, action_span=adp.SourceSpan("invented", 2, 18))), confirmed_text=TEXT) is None


@pytest.mark.parametrize("location", ["prompt", "trace", "model", "input_utf8"])
def test_auth_and_invalid_input_never_persist(location):
    transport = FakeTransport()
    req = request()
    if location == "prompt": req = request(TEXT + " synthetic-app-key")
    elif location == "input_utf8": req = request(TEXT + "\ud800")
    else:
        frames = events()
        frames[0 if location == "trace" else 1]["TraceId" if location == "trace" else "ModelVersion"] = "synthetic-app-key"
        transport.frames = [wire(frames)]
    result = adapter(transport).extract(req)
    assert result.validation == "invalid" and result.raw is None
    assert "synthetic-app-key" not in repr(result)
    assert len(transport.calls) == (0 if location in {"prompt", "input_utf8"} else 1)


@pytest.mark.parametrize("key,value", [("TraceId", "fake-trace-v1"), ("ModelVersion", "fake-model-v1")])
def test_pinned_fake_metadata_and_marker_refusal(key, value):
    frames = events(); index = 0 if key == "TraceId" else 1
    frames[index][key] = value
    result = adapter(FakeTransport([wire(frames)])).extract(request())
    assert result.validation == "valid"
    assert (result.trace_id if key == "TraceId" else result.model_version) == value
    frames[index][key] = "SYNTHETIC_SECRET_REASONING"
    result = adapter(FakeTransport([wire(frames)])).extract(request())
    assert result.validation == "invalid" and "SYNTHETIC_SECRET_REASONING" not in repr(result)


@pytest.mark.parametrize("key,value", [("TraceId", "fake-trace-v1"), ("ModelVersion", "fake-model-v1")])
def test_configured_auth_cannot_be_echoed_as_pinned_metadata(key, value):
    frames = events(); frames[0 if key == "TraceId" else 1][key] = value
    assert adapter(FakeTransport([wire(frames)])).extract(request()).validation == "valid"
    extractor = adp.AdpReadbackExtractor(transport=FakeTransport([wire(frames)]), profile="fake-incremental-v1",
        enabled=True, endpoint="https://fake.invalid/readback", app_key=value)
    result = extractor.extract(request())
    assert result.validation == "invalid" and result.failure_category == "metadata_auth"
    assert result.trace_id is result.model_version is None


def test_default_disabled_and_single_five_second_deadline():
    transport = FakeTransport()
    default = adp.AdpReadbackExtractor(transport=transport, profile="fake-incremental-v1",
        endpoint="https://fake.invalid/readback", app_key="synthetic-app-key")
    assert default.extract(request()).validation == "disabled" and transport.calls == []
    extractor = adapter(transport, monotonic=lambda: 10)
    assert extractor.extract(request(), budget_seconds=500).validation == "valid"
    assert len(transport.calls) == 1 and transport.calls[0][2] == 15


def test_transport_failure_logs_nothing_and_does_not_use_lexical_port(monkeypatch, capsys, caplog):
    def forbidden_fallback(*args, **kwargs): raise AssertionError("lexical fallback called")
    monkeypatch.setattr(adp.OfflineReadbackExtractor, "extract", forbidden_fallback)
    transport = FakeTransport(explode=True)
    result = adapter(transport).extract(request())
    assert result.validation == "transport" and result.raw is None and len(transport.calls) == 1
    captured = capsys.readouterr()
    assert "SYNTHETIC_SECRET_REASONING" not in captured.out + captured.err + caplog.text


PROFILE_CASES = ["ack_duplicate", "response_duplicate", "message_duplicate", "content_early", "final_channel_unknown",
                 "final_content_twice", "text_extra", "done_early", "terminal_early", "complete_twice", "reasoning_final",
                 "message_id_type", "content_id_type", "heartbeat_extra", "wire_type", "trace_unknown", "model_unknown",
                 "duplicate_reasoning_content", "unknown_extra_event", "empty_text"]


@pytest.mark.parametrize("case", PROFILE_CASES)
def test_profile_guard_at_first_boundary(case):
    assert adp.assemble_answer([wire(events())], correlation_id="fictional-correlation", deadline_monotonic=time.monotonic()+5) == encode(object_for())
    frames = events()
    profile = "fake-incremental-v1"
    if case == "ack_duplicate": frames.insert(1, dict(frames[0]))
    elif case == "response_duplicate": frames.insert(2, dict(frames[1]))
    elif case == "message_duplicate": frames.insert(3, dict(frames[2]))
    elif case == "content_early": frames.insert(2, frames.pop(3))
    elif case == "final_channel_unknown":
        frames[3]["Channel"] = frames[4]["Channel"] = "unknown"
    elif case == "final_content_twice":
        extra = {**frames[3], "ContentId": "answer-2"}; frames.insert(4, extra)
    elif case == "text_extra": frames[4]["Advice"] = "forbidden"
    elif case == "done_early": frames = frames[:4] + frames[5:]
    elif case == "terminal_early": frames = frames[:1] + [frames[-1]]
    elif case == "complete_twice":
        profile = "fake-complete-v1"; frames = events(complete=True); frames.insert(5, dict(frames[4]))
    elif case == "reasoning_final":
        frames.insert(4, envelope("content.added", MessageId="assistant-1", ContentId="reason-1", Channel="reasoning"))
        frames.insert(5, envelope("text.final", MessageId="assistant-1", ContentId="reason-1", Channel="reasoning", Text="SYNTHETIC_SECRET_REASONING"))
    elif case == "message_id_type":
        for item in frames:
            if "MessageId" in item: item["MessageId"] = 1
    elif case == "content_id_type":
        for item in frames:
            if "ContentId" in item: item["ContentId"] = 1
    elif case == "heartbeat_extra": frames.insert(1, envelope("heartbeat", extra=1))
    elif case == "trace_unknown": frames[0]["TraceId"] = "SYNTHETIC_SECRET_REASONING"
    elif case == "model_unknown": frames[1]["ModelVersion"] = "SYNTHETIC_SECRET_REASONING"
    elif case == "duplicate_reasoning_content":
        reasoning = envelope("content.added", MessageId="assistant-1", ContentId="reason-1", Channel="reasoning")
        frames[4:4] = [reasoning, dict(reasoning)]
    elif case == "unknown_extra_event": frames.insert(1, envelope("not_profiled"))
    elif case == "empty_text": frames[4]["Text"] = ""
    payload = [bytearray(wire(frames))] if case == "wire_type" else [wire(frames)]
    with pytest.raises(ValueError):
        adp.assemble_answer(payload, correlation_id="fictional-correlation", deadline_monotonic=time.monotonic()+5, profile=profile)


def test_sse_unknown_line_and_event_key_first_boundary():
    frame = wire(events()[:1])[:-2].decode()
    assert adp._sse_object(frame)["Type"] == "request_ack"
    with pytest.raises(ValueError): adp._sse_object("retry: 0\n" + frame)
    with pytest.raises(ValueError): adp._sse_object(frame.replace("event: request_ack", "event: wrong"))
    with pytest.raises(ValueError): adp._sse_object("event: request_ack\n" + frame)


@pytest.mark.parametrize("value", [None, 1, True, "", "with space", "x"*129])
def test_profile_id_at_first_boundary(value):
    assert adp._profile_id("assistant-1", "identifier") == "assistant-1"
    with pytest.raises(ValueError): adp._profile_id(value, "identifier")


@pytest.mark.parametrize("value", [None, 1, True, []])
def test_string_type_at_first_boundary(value):
    assert adp._string_type("myself", "text") == "myself"
    with pytest.raises(ValueError): adp._string_type(value, "text")


def test_truncated_frame_at_first_boundary():
    kwargs = {"deadline_monotonic": time.monotonic()+5, "monotonic": time.monotonic}
    assert len(list(adp._sse_frames([wire(events())], **kwargs))) == 7
    with pytest.raises(ValueError): list(adp._sse_frames([wire(events())[:-1]], **kwargs))


def test_ledger_component_renders_fake_and_unscored_provenance(tmp_path):
    from pathlib import Path
    import subprocess
    from test_field_repair import make_service, start_readback, confirm, score
    service = make_service(tmp_path / "render.sqlite")
    service._readback_extractor = adapter(ScenarioTransport(failure="invalid"))
    try:
        ep = start_readback(service); confirm(service, ep, "go to the clinic today before six myself"); score(service, ep)
        root = Path(__file__).resolve().parents[1]
        payload = tmp_path / "ledger.json"; payload.write_text(json.dumps(service.project_ledger(ep).as_dict()))
        script = tmp_path / "render.cjs"
        script.write_text('''const fs=require('fs');
const root=process.argv[2], data=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const ts=require(root+'/frontend/node_modules/typescript');
const ReactDom=require(root+'/frontend/node_modules/react-dom/server');
const source=fs.readFileSync(root+'/frontend/app/ledger/page.tsx','utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
const mod={exports:{}};
function imports(name){
 if(name==='@/lib/api')return {getLedger:async()=>({ok:true,value:data})};
 if(name==='next/headers')return {cookies:async()=>({get:()=>({value:'fixture'})})};
 if(name==='@/lib/episode-locator')return {decodeLocator:()=>({episode_id:data.episode_id}),LOCATOR_COOKIE:'fixture'};
 if(name==='react/jsx-runtime')return require(root+'/frontend/node_modules/react/jsx-runtime');
 throw Error('unexpected import '+name);
}
new Function('require','module','exports',compiled)(imports,mod,mod.exports);
mod.exports.default().then(page=>process.stdout.write(ReactDom.renderToStaticMarkup(page))).catch(err=>{process.stderr.write(String(err));process.exitCode=1});
''')
        rendered = subprocess.run(["node", str(script), str(root), str(payload)], capture_output=True, text=True)
        assert rendered.returncode == 0, rendered.stderr
        assert "fake-offline" in rendered.stdout and "fake-incremental-v1" in rendered.stdout
        assert "unscored" in rendered.stdout and "unknown" in rendered.stdout
        assert "Live ADP and model correctness are unverified" in rendered.stdout
        assert "SYNTHETIC_SECRET_REASONING" not in rendered.stdout
    finally:
        service._store.close()


def test_service_utf8_refusal_precedes_claim_digest_and_transport(tmp_path):
    from test_field_repair import make_service, start_readback, KEY, verify_operation
    from carerelay.journey_commands import CommandInvalid
    service = make_service(tmp_path / "input-utf8.sqlite"); transport = ScenarioTransport()
    service._readback_extractor = adapter(transport)
    try:
        ep = start_readback(service)
        token = service.prepare_command(ep, kind="confirm_words", body_sha256="1"*64, parent_id=None)
        before = service._store.load_journey_bundle(ep)
        with pytest.raises(CommandInvalid): service.confirm_words(verify_operation(token, signing_key=KEY), text="\ud800")
        assert service._store.load_journey_bundle(ep) == before and transport.calls == []
    finally:
        service._store.close()


@pytest.mark.parametrize("tampered", [False, True])
def test_unvalidated_port_metadata_never_reaches_storage_or_ledger(tmp_path, tampered):
    from test_field_repair import make_service, start_readback, confirm, score
    service = make_service(tmp_path / "forged-provenance.sqlite")
    strict = adapter(ScenarioTransport())
    marker = "SYNTHETIC_SECRET_REASONING"
    class UnvalidatedPort:
        instruction_version = strict.instruction_version
        schema_version = strict.schema_version
        def extract(self, req, **kwargs):
            result = strict.extract(req, **kwargs)
            assert result.validation == "valid"
            return replace(result, request_id=marker, trace_id=marker, model_version=marker,
                boundary_proof=result.boundary_proof if tampered else None)
    service._readback_extractor = UnvalidatedPort()
    try:
        ep = start_readback(service); saved = confirm(service, ep, "go to the clinic today before six myself")
        binding, result = score(service, ep)
        assert result.receipt.state == "unavailable" and not result.receipt.scored
        assert result.journey.question == saved.journey.question and not result.journey.flow.stopped
        assert result.journey.flow.completed_repairs == 0 and service._store.list_restatements(ep) == ()
        bundle = service._store.load_journey_bundle(ep)
        assert marker not in json.dumps(list(bundle.commands))
        assert marker not in json.dumps(service.project_ledger(ep).as_dict())
        assert service.project_ledger(ep).as_dict()["extractions"][-1]["failure_category"] == "unvalidated_port_result"
    finally:
        service._store.close()


def test_adapter_proof_checks_origin_and_immutable_metadata():
    valid = adapter().extract(request())
    assert adp.trusted_adp_result(valid)
    assert not adp.trusted_adp_result(replace(valid, request_id="SYNTHETIC_SECRET_REASONING"))
    original = replace(valid, boundary_proof=None)
    forged = replace(original, boundary_proof=adp._AdpProof(object(), original))
    assert not adp.trusted_adp_result(forged)


@pytest.mark.parametrize("action", ["duplicate", "supersede", "cue", "stop", "deadline", "revision"])
def test_fake_transport_outside_locks_and_late_result_fenced(tmp_path, action, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from datetime import timedelta
    from threading import Event
    from test_field_repair import make_service, start_readback, confirm, event, KEY, verify_operation
    from carerelay.demo import fixture
    from carerelay.service import ScenarioClock
    entered, release = Event(), Event()

    class Paused(ScenarioTransport):
        def open(self, endpoint, body, **kwargs):
            entered.set()
            assert release.wait(3)
            return super().open(endpoint, body, **kwargs)

    path = tmp_path / "race.sqlite"
    service, other = make_service(path), make_service(path)
    transport = Paused(); service._readback_extractor = adapter(transport)
    try:
        ep = start_readback(service); confirm(service, ep, "go to the clinic today before six myself")
        token = next(o.operation_token for o in service.project_journey(ep).commands if o.kind == "score_words")
        binding = verify_operation(token, signing_key=KEY)
        with ThreadPoolExecutor(2) as workers:
            future = workers.submit(service.score_confirmed, binding)
            assert entered.wait(1)
            try:
                duplicate = workers.submit(other.score_confirmed, binding).result(1)
                assert duplicate.receipt.state == "pending" and duplicate.receipt.replayed
                if action == "supersede":
                    offer = next(o for o in duplicate.journey.commands if o.kind == "supersede_extraction")
                    other.supersede_extraction(verify_operation(offer.operation_token, signing_key=KEY), old_operation_id=binding.operation_id)
                    from carerelay.domain import rules
                    def no_late_evaluation(*args, **kwargs):
                        raise AssertionError("superseded output was evaluated again")
                    monkeypatch.setattr(rules, "readback_context_current", no_late_evaluation)
                elif action == "cue": event(other, ep, "show_plan")
                elif action == "stop": other._store.record_flow_stop(ep, 1, "fixture-stop", "nurse_line", now_utc=fixture.SCENARIO_NOW_UTC)
                elif action == "deadline": service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC + timedelta(hours=10))
                elif action == "revision":
                    with other._store.journey_transaction(ep, write=True) as tx:
                        tx._event("fixture-audit", {}, fixture.SCENARIO_NOW_UTC)
            finally:
                release.set()
            result = future.result(2)
        assert len(transport.calls) == 1
        assert result.receipt.state == ("applied" if action == "duplicate" else "superseded" if action == "supersede" else "refused")
        assert result.receipt.scored is (action == "duplicate")
        assert len(service._store.list_restatements(ep)) == (1 if action == "duplicate" else 0)
        assert service._store.list_attempts(ep) == ()
        entries = service.project_ledger(ep).as_dict()["extractions"]
        assert len(entries) == 1 and entries[0]["transport_provenance"] == "fake-offline"
        assert entries[0]["validation"] == "valid" and entries[0]["terminal_state"] == result.receipt.state
        assert service._store.load_snapshot(ep).disposition.clinical_deadline_utc.isoformat() == "2026-09-30T10:00:00+00:00"
    finally:
        release.set(); service._store.close(); other._store.close()


@pytest.mark.parametrize("outcome", ["applied", "unavailable"])
def test_live_https_rows_report_https_transport_in_the_judge_ledger(tmp_path, monkeypatch, outcome):
    # Found through the actual local product on 15 October 2026: live rows read "unknown".
    from test_field_repair import make_service, start_readback, confirm, score
    if outcome == "applied":
        extractor, calls = live_adapter(monkeypatch)
    else:
        transport, calls = https_transport(monkeypatch, fail=OSError)
        extractor = adp.AdpReadbackExtractor(transport=transport, profile="adp-sse-final-throttle100-v1",
            endpoint="https://wss.lke.tencentcloud.com/adp/v2/chat", app_key="test-key", enabled=True,
            monotonic=lambda: 10.0)
    service = make_service(tmp_path / "live-ledger.sqlite"); service._readback_extractor = extractor
    try:
        ep = start_readback(service); confirm(service, ep, TEXT)
        _, result = score(service, ep)
        assert result.receipt.state == outcome
        entries = service.project_ledger(ep).as_dict()["extractions"]
        assert [(e["transport_profile"], e["transport_provenance"], e["interpreter_mode"]) for e in entries] == [
            ("adp-sse-final-throttle100-v1", "https", "adp")]
        assert len([call for call in calls if call[0] == "request"]) == 1
    finally:
        service._store.close()


# Gate 3 section 9.7 grounding rows, amended 15 October 2026: the model sends phrase text only.
GROUNDING = {
    # case: (confirmed words, action text, expected action span start or outcome)
    "located": ("🙂 go to the clinic; today before six; myself.", "go to the clinic", 2),
    "not_found": ("🙂 go to the clinic; today before six; myself.", "attend the clinic", "not_found"),
    "two_occurrences": ("go to the clinic, go to the clinic; today before six; myself.", "go to the clinic", "ambiguous"),
    "overlapping": ("go go go; today before six; myself.", "go go", "ambiguous"),
    "inside_longer_word": ("ungo to the clinic; today before six; myself.", "go to the clinic", "not_found"),
    "one_bounded_one_embedded": ("go to the clinicx, go to the clinic; today before six; myself.", "go to the clinic", 19),
    "case": ("Go to the clinic; today before six; myself.", "go to the clinic", "not_found"),
    "whitespace": ("go to the\u00a0clinic; today before six; myself.", "go to the clinic", "not_found"),
    "nfc": ("go to the cafe\u0301; today before six; myself.", "go to the caf\u00e9", "not_found"),
}


@pytest.mark.parametrize("case", sorted(GROUNDING))
def test_grounding(case):
    text, phrase, expected = GROUNDING[case]
    obj = object_for(); obj["action_text"] = phrase
    raw, locations = adp._validate_wire(encode(obj), confirmed_text=text)
    assert raw.schema_version == "carerelay-readback-v2" and raw.refused is False
    assert raw.deadline_span is not None and raw.next_owner_span is not None
    if isinstance(expected, int):
        assert raw.action_span is not None, dict(locations)
        assert (raw.action_span.text, raw.action_span.start, raw.action_span.end) == (phrase, expected, expected + len(phrase))
        assert text[raw.action_span.start:raw.action_span.end] == phrase
        assert raw.uncertain_fields == frozenset() and dict(locations)["action_id"] == "located"
    else:
        assert raw.action_span is None and raw.uncertain_fields == frozenset({"action_id"})
        assert dict(locations) == {"action_id": expected, "deadline_utc": "located", "next_owner_id": "located"}
    assert validator()(encode(obj), confirmed_text=text) == raw


def test_located_span_survives_the_adp_eligibility_boundary_and_other_words_do_not():
    transport = FakeTransport([wire(events())])
    result = adapter(transport).extract(request())
    assert result.validation == "valid" and result.schema_version == "carerelay-readback-v2"
    assert dict(result.span_locations) == {"action_id": "located", "deadline_utc": "located", "next_owner_id": "located"}
    raw = adp.eligible_adp_output(result, confirmed_text=TEXT)
    assert raw is not None and (raw.action_span.start, raw.action_span.end) == (2, 18)
    # A trusted result is still checked against the words the service is scoring.
    assert adp.eligible_adp_output(result, confirmed_text="x" + TEXT) is None


def test_not_found_phrase_is_uncertain_and_recorded_in_the_ledger(tmp_path):
    from test_field_repair import make_service, start_readback, confirm, score
    class NotFound(ScenarioTransport):
        def open(self, endpoint, body, *, deadline_monotonic, allow_redirects):
            response = super().open(endpoint, body, deadline_monotonic=deadline_monotonic, allow_redirects=allow_redirects)
            response = adp.TransportResponse(200, [chunk.replace(b"go to the clinic", b"go to the clinics") for chunk in response.frames])
            return response
    service = make_service(tmp_path / "not-found.sqlite"); transport = NotFound()
    service._readback_extractor = adapter(transport)
    try:
        ep = start_readback(service); confirm(service, ep, "go to the clinic today before six myself")
        _, result = score(service, ep)
        assert result.receipt.state == "applied" and result.receipt.scored
        assert "action_id" not in service._store.list_restatements(ep)[-1].comparison.matched
        entries = service.project_ledger(ep).as_dict()["extractions"]
        assert [e["span_locations"] for e in entries] == [{"action_id": "not_found", "deadline_utc": "located", "next_owner_id": "located"}]
        assert entries[0]["schema_version"] == "carerelay-readback-v2" and len(transport.calls) == 1
        assert "go to the clinics" not in json.dumps(service.project_ledger(ep).as_dict())
    finally:
        service._store.close()


# Bounded diagnostic, 15 October 2026: which field and which JSON type, never the value.
@pytest.mark.parametrize("key,field,value,json_type", [
    ("action_text", "action_id", {"text": "SECRET_VALUE_MARKER", "start": 2, "end": 18}, "object"),
    ("deadline_text", "deadline_utc", ["SECRET_VALUE_MARKER"], "array"),
    ("next_owner_text", "next_owner_id", 7, "number"),
    ("action_text", "action_id", 7.5, "number"),
    ("deadline_text", "deadline_utc", True, "boolean"),
], ids=["object", "array", "integer", "float", "boolean"])
def test_non_text_field_reports_field_and_json_type_only(key, field, value, json_type):
    assert validator()(encode(object_for()), confirmed_text=TEXT).action_span.text == "go to the clinic"
    obj = object_for(); obj[key] = value
    with pytest.raises(adp.ExtractionInvalid) as refused:
        validator()(encode(obj), confirmed_text=TEXT)
    assert str(refused.value) == f"span_text_type:{field}:{json_type}"
    result = adapter(FakeTransport([wire(events(answer=encode(obj).decode()))])).extract(request())
    assert (result.validation, result.failure_category, result.raw) == ("invalid", f"span_text_type:{field}:{json_type}", None)
    assert "SECRET_VALUE_MARKER" not in repr(result)
