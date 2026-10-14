"""Slice 18 uses synthetic profiles and fake auth, never a vendor or database."""
import json
from dataclasses import replace
import time

import pytest

from carerelay import adp_extraction as adp


TEXT = "🙂 go to the clinic; today before six; myself."


def object_for(text=TEXT):
    def span(words):
        start = text.index(words)
        return {"text": words, "start": start, "end": start + len(words)}
    return {"schema_version": "carerelay-readback-v1", "action_span": span("go to the clinic"),
            "deadline_span": span("today before six"), "next_owner_span": span("myself"),
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


OBJECT_CASES = ["extra", "missing", "version", "refused_type", "uncertainty_type", "unknown_field",
                "repeated_field", "null_without_uncertainty", "refused_span", "refused_uncertainty",
                "span_keys", "span_type", "text_type", "start_bool", "end_bool", "start_float",
                "negative", "empty", "overrun", "source", "utf16", "byte_offset", "canonical",
                "duplicate_root", "duplicate_nested", "two_objects", "prose", "fence", "utf8",
                "nonfinite", "word_start", "word_end", "root_type"]


def invalid_object(case):
    obj = object_for(); text = TEXT
    if case == "extra": obj["advice"] = "forbidden"
    elif case == "missing": del obj["refused"]
    elif case == "version": obj["schema_version"] = "other"
    elif case == "refused_type": obj["refused"] = 0
    elif case == "uncertainty_type": obj["uncertain_fields"] = "action_id"
    elif case == "unknown_field": obj["uncertain_fields"] = ["route"]
    elif case == "repeated_field": obj["uncertain_fields"] = ["action_id", "action_id"]
    elif case == "null_without_uncertainty": obj["action_span"] = None
    elif case == "refused_span": obj["refused"] = True; obj["uncertain_fields"] = list(adp.COMPARISON_FIELDS)
    elif case == "refused_uncertainty":
        obj.update(action_span=None, deadline_span=None, next_owner_span=None, refused=True,
                   uncertain_fields=["action_id", "deadline_utc"])
    elif case == "span_keys": obj["action_span"]["confidence"] = 1
    elif case == "span_type": obj["action_span"] = "go to the clinic"
    elif case == "text_type": obj["action_span"]["text"] = 1
    elif case == "start_bool": obj["action_span"]["start"] = True
    elif case == "end_bool": obj["action_span"]["end"] = True
    elif case == "start_float": obj["action_span"]["start"] = 2.0
    elif case == "negative": obj["action_span"].update(start=-2, end=-1, text=TEXT[-2:-1])
    elif case == "empty": obj["action_span"].update(end=2, text="")
    elif case == "overrun": obj["action_span"].update(end=len(TEXT)+1, text=TEXT[2:])
    elif case == "source": obj["action_span"]["text"] = "invented"
    elif case in {"utf16", "byte_offset"}:
        text = TEXT.replace("myself", "我自己") + "   "
        start = text.index("我自己") + (1 if case == "utf16" else 3)
        obj["next_owner_span"] = {"text": "我自己", "start": start, "end": start+3}
    elif case == "canonical":
        text = "attend_same_day_review; today before six; myself."
        obj = object_for(text.replace("attend_same_day_review", "go to the clinic"))
        obj["action_span"] = {"text": "attend_same_day_review", "start": 0, "end": len("attend_same_day_review")}
        for key, words in [("deadline_span", "today before six"), ("next_owner_span", "myself")]:
            obj[key] = {"text": words, "start": text.index(words), "end": text.index(words)+len(words)}
    elif case == "word_start": text = "x" + TEXT[2:]; obj = object_for(text)
    elif case == "word_end": text = TEXT.replace("clinic", "clinicx"); obj = object_for(text)
    payload = encode(obj)
    if case == "duplicate_root": payload = payload[:-1] + b',"refused":false}'
    elif case == "duplicate_nested": payload = payload.replace(b'"start":2', b'"start":2,"start":2')
    elif case == "two_objects": payload += payload
    elif case == "prose": payload = b"Here is the answer: " + payload
    elif case == "fence": payload = b"```json\n" + payload + b"\n```"
    elif case == "utf8": payload += b"\xff"
    elif case == "nonfinite": payload = payload.replace(b'"start":2', b'"start":NaN')
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
    obj.update(action_span=None, deadline_span=None, next_owner_span=None,
               uncertain_fields=list(adp.COMPARISON_FIELDS), refused=True)
    raw = validator()(encode(obj), confirmed_text=TEXT)
    assert raw.refused and raw.uncertain_fields == frozenset(adp.COMPARISON_FIELDS)


@pytest.mark.parametrize("identifier", ["attend_same_day_review", "call_nurse_line", "wait_and_monitor", "patient", "caregiver"])
def test_all_canonical_fixture_ids_are_not_answers(identifier):
    assert validator()(encode(object_for()), confirmed_text=TEXT).action_span.text == "go to the clinic"
    words = [identifier, "today before six", "myself"] if identifier not in {"patient", "caregiver"} else ["go to the clinic", "today before six", identifier]
    text = "; ".join(words)
    obj = object_for()
    for key, word in zip(("action_span", "deadline_span", "next_owner_span"), words):
        obj[key] = {"text": word, "start": text.index(word), "end": text.index(word)+len(word)}
    with pytest.raises(ValueError): validator()(encode(obj), confirmed_text=text)


@pytest.mark.parametrize("value,keys", [({"extra": 1}, adp._OBJECT_KEYS), ([], adp._OBJECT_KEYS),
    ({"text": "myself", "start": 0}, adp._SPAN_KEYS), ("myself", adp._SPAN_KEYS)])
def test_shape_at_first_boundary(value, keys):
    good = {key: None for key in keys}
    assert adp._exact_keys(good, keys, "shape") == good
    with pytest.raises(ValueError): adp._exact_keys(value, keys, "shape")


@pytest.mark.parametrize("start,end", [(True, 2), (0, True), (0.0, 2), (0, 2.0)])
def test_offset_types_at_first_boundary(start, end):
    assert adp._offset_types(0, 2) == (0, 2)
    with pytest.raises(ValueError): adp._offset_types(start, end)


@pytest.mark.parametrize("value", ["action_id", [1], None])
def test_uncertainty_types_at_first_boundary(value):
    assert adp._uncertainty_list(["action_id"]) == ["action_id"]
    with pytest.raises(ValueError): adp._uncertainty_list(value)


def test_nonfinite_at_json_boundary():
    assert adp._strict_json(b'{"value":1}') == {"value": 1}
    for value in [b"NaN", b"Infinity", b"-Infinity"]:
        with pytest.raises(ValueError): adp._strict_json(b'{"value":'+value+b'}')


def test_oversized_integer_is_invalid_json_not_transport_failure():
    answer = encode(object_for()).replace(b'"start":2', b'"start":' + b"1"*5000).decode()
    transport = FakeTransport([wire(events(answer=answer))])
    result = adapter(transport).extract(request())
    assert result.validation == "invalid" and result.failure_category == "json"
    assert result.raw is None and len(transport.calls) == 1


def request(text=TEXT):
    return adp.ExtractionInput(text, frozenset({"go to the clinic"}), frozenset({"today before six"}),
        frozenset({"myself"}), "fictional-correlation", "fake-instruction-v1", "carerelay-readback-v1")


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
            values.append(None if word is None else {"text": word, "start": text.index(word), "end": text.index(word)+len(word)})
        obj = {"schema_version": "carerelay-readback-v1", "action_span": values[0], "deadline_span": values[1],
               "next_owner_span": values[2], "uncertain_fields": [field for field, span in zip(adp.COMPARISON_FIELDS, values) if span is None], "refused": False}
        if self.failure == "invalid": obj["advice"] = "SYNTHETIC_SECRET_REASONING"
        elif self.failure == "refused": obj.update(action_span=None, deadline_span=None, next_owner_span=None, uncertain_fields=list(adp.COMPARISON_FIELDS), refused=True)
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
