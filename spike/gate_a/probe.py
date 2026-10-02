"""Gate A access spike: does the ADP platform carry the section 3.3 claim?

`02-architecture.md` section 3.3 pins one normative call path. The coordinator
executes the tool, and **the platform emits the failure event with a usable
origin signal**. That is judged as load-bearing, so it has to be observed
rather than assumed. This harness observes it.

**The schema is documented, and it is not what the first draft assumed.**
The first draft of this file sent the AppKey as an HTTP header and expected a
`ConversationId` back from the platform. The ADP HTTP SSE reference
(`https://www.tencentcloud.com/document/product/1254/81449`, retrieved
2 October 2026) says otherwise on both counts:

- Authentication is the **`AppKey` request-body field**. The only documented
  header is `Content-Type: application/json`. There is no signature header and
  no second secret, so no `ADP_API_SECRET` is consumed by this API.
- `ConversationId` is an **externally supplied required field**, 32 to 64
  characters matching `^[a-zA-Z0-9_-]{32,64}$`. The caller generates it and
  replays it; the platform does not issue it.

The earlier live run is the evidence for the body model: with the AppKey in a
header and no `AppKey` field in the body, the platform answered HTTP 200 with
`event: error`, `Error.Code: 400`, `Message: 请求参数错误, 请参阅接入文档.` That is
a well-formed rejection of a malformed body, which is why question 1 is treated
as reached-by-transport and answered by body, not by header.

**What it probes, and why in this order.**

1. **Reachability and a well-formed request.** A schema-correct body is sent,
   and the stream is read for `request_ack` and `response.completed`. A body
   that is accepted is the answer to question 1.
2. **Session continuity.** Two calls share one caller-generated
   `ConversationId`, the second asking what was asked first. The claim tested
   is that the session lives on the platform side, so a client restart holding
   only the id cannot lose it. The restart is real: the two calls are issued by
   separate client objects.
3. **Failure-event origin.** A request that is well-formed at the transport
   level but invalid in content is sent, and the response is inspected for a
   structured identifier attributable to the platform rather than to this
   client. Question 3, and the only one the guide does not answer.

**It fails closed.** With no `ADP_APPKEY` in the environment it records
`BLOCKED_NO_CREDENTIAL` and exits non-zero. It never reports `PASS` from a
result it did not observe. A harness that green-lights a missing credential is
the exact dishonesty the gate exists to prevent.

**It never writes the credential.** The AppKey is read from the environment and
placed in the request body. It is not logged and not written to the result
file, and it is redacted from any captured response before that response is
persisted. Because the body is persisted in redacted form, the redaction is a
load-bearing correctness property here rather than a courtesy.

**Where the result goes.** `spike/gate_a/gate_a_result.json`, beside this file,
in the throwaway spike tree. Nothing here is product code and nothing here is
imported by `src/`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    import httpx
except ImportError:  # pragma: no cover - the environment, not the logic
    print("httpx is required to run the Gate A probe. It is a declared test "
          "dependency, so install the test extra.", file=sys.stderr)
    raise SystemExit(2)


#: The endpoint as the ADP HTTP SSE reference records it, and as the live run
#: confirmed. Overridable for a doc revision without touching the logic.
ADP_CHAT_ENDPOINT = os.environ.get(
    "ADP_CHAT_ENDPOINT", "https://wss.lke.tencentcloud.com/adp/v2/chat"
)

#: The credential, and the only one this API consumes. Read only from the
#: environment, never from a file, never echoed.
APPKEY_ENV_VAR = "ADP_APPKEY"

#: Retained because the guide names an API secret as well. The HTTP SSE
#: reference does not use it, so it is optional and only redacted if present.
#: Keeping the constant means the redaction covers a value that could still
#: appear in a captured response or exception message.
SECRET_ENV_VAR = "ADP_API_SECRET"

#: `ConversationId` and `RequestId` must match this and be 32 to 64 characters.
ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{32,64}$")

#: A stable, externally supplied visitor identity for the probe. Not a secret.
VISITOR_ID = "gate-a-probe"

RESULT_PATH = Path(__file__).with_name("gate_a_result.json")

#: A response body can echo the key back. Redact it before persisting anything.
_REDACTIONS = (APPKEY_ENV_VAR, SECRET_ENV_VAR)


@dataclass
class Observation:
    """One probe's outcome, recorded as observed rather than as intended."""

    name: str
    ran: bool = False
    ok: bool = False
    detail: str = ""
    evidence: dict = field(default_factory=dict)


@dataclass
class GateAResult:
    """The whole spike, and the verdict it supports."""

    started_utc: str = ""
    endpoint: str = ""
    credential_present: bool = False
    observations: list = field(default_factory=list)
    verdict: str = ""
    verdict_reason: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=False)


def _redact(value: str) -> str:
    """Strip any credential value out of a string before it is persisted."""
    out = value
    for name in _REDACTIONS:
        secret = os.environ.get(name)
        if secret:
            out = out.replace(secret, f"<redacted:{name}>")
    # A key can also appear in a masked or partial form in an error message.
    out = re.sub(r"(?i)(appkey[\"'=:\s]+)[A-Za-z0-9_\-]{6,}", r"\1<redacted>", out)
    return out


def _new_id() -> str:
    """A 36-character uuid4, which satisfies the documented 32 to 64 rule."""
    return str(uuid.uuid4())


def build_body(conversation_id: str, text: str, *, appkey: str,
               request_id: str | None = None, stream: str = "enable",
               incremental: bool = True) -> dict:
    """The documented request body, field for field.

    `AppKey`, `ConversationId`, `VisitorId` and `Contents` are required; the
    reference marks the rest optional. `Stream: "enable"` is set because the
    origin signal this harness is looking for arrives as an SSE event, and a
    non-streaming call has no stream to carry it.
    """
    return {
        "RequestId": request_id or _new_id(),
        "ConversationId": conversation_id,
        "AppKey": appkey,
        "VisitorId": VISITOR_ID,
        "Contents": [{"Type": "text", "Text": text}],
        "Incremental": incremental,
        "Stream": stream,
    }


def _post(client: httpx.Client, body: dict) -> tuple[int | None, str]:
    """One request. Returns (status, body). Never raises on an HTTP error."""
    headers = {"Content-Type": "application/json"}
    try:
        response = client.post(ADP_CHAT_ENDPOINT, json=body, headers=headers)
    except httpx.HTTPError as exc:
        return None, f"{type(exc).__name__}: {_redact(str(exc))}"
    return response.status_code, _redact(response.text[:8000])


def _sse_events(raw: str) -> list[tuple[str, dict]]:
    """Parse an SSE stream into (event name, decoded data) pairs.

    Returns only frames whose `data:` line is valid JSON and not the `[DONE]`
    terminator, because the terminator carries no event name and the error
    frame is the one that has to be read as data rather than as a status.
    """
    events: list[tuple[str, dict]] = []
    name = ""
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("event:"):
            name = line[len("event:"):].strip()
        elif line.startswith("data:"):
            payload = line[len("data:"):].strip()
            if payload in ("", "[DONE]"):
                continue
            try:
                events.append((name, json.loads(payload)))
            except json.JSONDecodeError:
                continue
    return events


def _event_types(events: list[tuple[str, dict]]) -> list[str]:
    """The distinct `Type` values seen, in order, for the evidence record."""
    seen: list[str] = []
    for _name, data in events:
        kind = data.get("Type")
        if isinstance(kind, str) and kind not in seen:
            seen.append(kind)
    return seen


def _error_frame(events: list[tuple[str, dict]]) -> dict | None:
    """The `error` frame, whose structure we captured live and the doc omits.

    The reference says an error event replaces `request_ack` when a request is
    blocked by security review or exceeds a concurrency limit, but it does not
    document the structure. The live run supplied it:
    `{"Type":"error","Error":{"Code":400,"Message":"...","RequestId":"",
    "TraceId":"..."},"Timestamp":"0","RecordId":""}`. That capture is better
    than the reference here, and this reads it as it actually appears.
    """
    for _name, data in events:
        if data.get("Type") == "error" and isinstance(data.get("Error"), dict):
            return data["Error"]
    return None


def probe_reachability_and_wellformed_request(
    client: httpx.Client, conversation_id: str, appkey: str
) -> Observation:
    """Q1. Is a schema-correct body accepted and streamed back?

    A transport-level success is not enough for this probe, because the earlier
    run proved the endpoint answers HTTP 200 to a malformed body as well. The
    probe passes only when the stream carries `request_ack`, which the
    reference documents as the request-confirmation event and which is absent
    when the body is rejected.
    """
    obs = Observation(name="q1_reachability_and_wellformed_request")
    body = build_body(conversation_id, "gate-a-probe: reply with the single word ready",
                      appkey=appkey)
    status, raw = _post(client, body)
    events = _sse_events(raw)
    obs.evidence = {
        "status": status,
        "event_types": _event_types(events),
        "body_excerpt": raw[:1200],
        "request_id_used": body["RequestId"],
        "conversation_id_used": conversation_id,
    }
    obs.ran = True

    if status is None:
        obs.ok = False
        obs.detail = "the request did not complete; see the evidence for the exception"
        return obs

    error = _error_frame(events)
    if error is not None:
        obs.ok = False
        obs.evidence["error_frame"] = error
        obs.detail = (f"the body was rejected: platform error {error.get('Code')} "
                      f"{error.get('Message', '')!r}")
        return obs

    if "request_ack" in _event_types(events):
        obs.ok = True
        obs.detail = ("a schema-correct body was accepted and acknowledged with "
                      "request_ack, so question 1 is answered from observation")
        return obs

    obs.ok = False
    obs.detail = ("the request returned no request_ack and no error frame, so the "
                  "body model is neither confirmed nor refuted by this response")
    return obs


def probe_session_continuity(
    conversation_id: str, appkey: str, timeout: float
) -> Observation:
    """Q2. Does a caller-supplied ConversationId carry context into a new call?

    The id is generated here, not read from a response, because the reference
    states the calling system supplies it. The two turns are issued by separate
    client objects so that no in-process state can carry the context: if the
    second answer reflects the first question, the continuity is the platform's
    and a process restart could not lose it.
    """
    obs = Observation(name="q2_session_continuity")
    turn1 = build_body(conversation_id, "gate-a-probe: remember the word lantern.",
                       appkey=appkey)
    with httpx.Client(timeout=timeout, follow_redirects=True) as c1:
        status1, raw1 = _post(c1, turn1)

    turn2 = build_body(conversation_id, "gate-a-probe: what word did I ask you to "
                                        "remember?", appkey=appkey)
    with httpx.Client(timeout=timeout, follow_redirects=True) as c2:
        status2, raw2 = _post(c2, turn2)

    obs.ran = True
    obs.evidence = {
        "conversation_id_used": conversation_id,
        "turn1": {"status": status1, "event_types": _event_types(_sse_events(raw1))},
        "turn2": {"status": status2, "event_types": _event_types(_sse_events(raw2)),
                  "body_excerpt": raw2[:1200]},
    }

    reply_text = _reply_text(raw2)
    obs.evidence["turn2_reply_text"] = reply_text[:400]

    if status1 is None or status2 is None:
        obs.ok = False
        obs.detail = "one of the two turns did not complete"
        return obs

    if _error_frame(_sse_events(raw1)) or _error_frame(_sse_events(raw2)):
        obs.ok = False
        obs.detail = ("a turn was rejected by the platform, so continuity was not "
                      "exercised")
        return obs

    if reply_text and "lantern" in reply_text.lower():
        obs.ok = True
        obs.detail = ("the second turn, issued by a separate client holding only the "
                      "ConversationId, recalled the first turn's content, so the "
                      "session lives on the platform side")
        return obs

    obs.ok = False
    obs.detail = ("both turns were accepted but the second reply did not reflect the "
                  "first turn's content, so continuity is not demonstrated by this "
                  "probe. A non-empty reply that omits the topic is still evidence "
                  "the id was honoured, and the excerpt is recorded for that read.")
    return obs


def _reply_text(raw: str) -> str:
    """Concatenate the assistant's `text.delta` fragments out of a stream."""
    parts: list[str] = []
    for _name, data in _sse_events(raw):
        if data.get("Type") == "text.delta" and isinstance(data.get("Text"), str):
            parts.append(data["Text"])
    if parts:
        return "".join(parts)
    # A non-incremental reply arrives whole inside response.completed.
    for _name, data in _sse_events(raw):
        if data.get("Type") == "response.completed":
            response = data.get("Response", {})
            for message in response.get("Messages", []) or []:
                for content in message.get("Contents", []) or []:
                    if isinstance(content.get("Text"), str):
                        parts.append(content["Text"])
    return "".join(parts)


def probe_failure_origin(client: httpx.Client, appkey: str) -> Observation:
    """Q3. Does a failing call carry a platform-attributable origin signal?

    **The load-bearing question.** Section 3.3 claims the platform, not this
    client, emits the failure event, and the ledger shows that origin so a
    reader can tell the platform path from the fallback by inspection.

    The failure is provoked by a missing required field rather than by a wrong
    header, because the transport is already known to accept anything. What
    matters is whether the error frame carries a structured identifier that
    belongs to the platform. A transport-level rejection with no identifier
    does **not** satisfy the claim, and this records that honestly rather than
    treating any error as a pass.

    The identifier read is `TraceId`, which the live run populated, and not
    `RequestId`, which the live run showed empty on this error class. `Code` is
    numeric in the captured frame, so it is read as either a number or a string.
    """
    obs = Observation(name="q3_failure_event_origin")
    body = build_body("", "gate-a-probe: deliberate failure origin check",
                      appkey=appkey)
    # ConversationId is required and must match the pattern. An empty string is
    # the minimal well-formed-at-transport, invalid-in-content request.
    status, raw = _post(client, body)
    events = _sse_events(raw)
    error = _error_frame(events)

    obs.ran = True
    obs.evidence = {
        "status": status,
        "event_types": _event_types(events),
        "body_excerpt": raw[:1200],
    }
    if error is not None:
        obs.evidence["error_frame"] = error

    has_error = error is not None
    trace_id = str(error.get("TraceId", "")) if has_error else ""
    request_id = str(error.get("RequestId", "")) if has_error else ""
    code = error.get("Code") if has_error else None
    code_is_typed = isinstance(code, (int, str)) and str(code) != ""

    obs.evidence["identifiers_found"] = {
        "trace_id": bool(trace_id),
        "request_id": bool(request_id),
        "error_code_typed": code_is_typed,
        "code_value": code,
    }

    if has_error and (trace_id or request_id) and code_is_typed:
        obs.ok = True
        obs.detail = ("the failing call returned a platform-coded error frame with "
                      "an attributable identifier, so the origin signal is the "
                      "platform's and not this client's")
    elif has_error:
        obs.ok = False
        obs.detail = ("the failing call returned an error frame carrying no trace id, "
                      "no request id and no typed code, so no origin signal was "
                      "observed")
    else:
        obs.ok = False
        obs.detail = ("the deliberately invalid request produced no error frame, so "
                      "the failure path was not exercised as expected")
    return obs


def run(timeout: float) -> GateAResult:
    appkey = os.environ.get(APPKEY_ENV_VAR, "")
    result = GateAResult(
        started_utc=datetime.now(timezone.utc).isoformat(),
        endpoint=ADP_CHAT_ENDPOINT,
        credential_present=bool(appkey),
    )

    if not result.credential_present:
        # Fail closed. Do not invent a result, do not report a pass, and make
        # the missing prerequisite the recorded outcome.
        result.observations = [
            asdict(Observation(
                name="precondition",
                ran=False,
                ok=False,
                detail=(f"{APPKEY_ENV_VAR} is not set in this environment. Gate A "
                        "cannot run without it. The AppKey is created when an "
                        "application is published, and is copied from Application "
                        "Management > the running application > Call > the AppKey "
                        "in the Call Information window."),
            ))
        ]
        result.verdict = "BLOCKED_NO_CREDENTIAL"
        result.verdict_reason = (
            "The spike did not run. A missing credential is a blocked check, not "
            "a failed platform and not a passing one. Re-run with "
            f"{APPKEY_ENV_VAR} exported."
        )
        return result

    conversation_id = _new_id()
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        first = probe_reachability_and_wellformed_request(client, conversation_id, appkey)
        third = probe_failure_origin(client, appkey)
    second = probe_session_continuity(conversation_id, appkey, timeout)

    result.observations = [asdict(o) for o in (first, second, third)]

    answered = [o for o in (first, second, third) if o.ran]
    passed = [o for o in answered if o.ok]
    if len(passed) == 3:
        result.verdict = "PASS"
        result.verdict_reason = (
            "All three Gate A questions were answered from observation. The "
            "platform path can carry the section 3.3 claim."
        )
    elif passed:
        result.verdict = "PARTIAL"
        result.verdict_reason = (
            f"{len(passed)} of 3 probes passed. The section 3.3 claim is upheld "
            "only for the probes that passed; the rest must be weakened and "
            "stated as weakened in the submission."
        )
    else:
        result.verdict = "FAIL"
        result.verdict_reason = (
            "No probe passed. Take the pre-recorded fallback: local simulation "
            "with origin = local-sim in the same field, an honest label, "
            "CodeBuddy development history carrying the usage proof, and the "
            "platform-advantage claim weakened and stated as weakened."
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate A access spike")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="per-request timeout in seconds")
    parser.add_argument("--no-write", action="store_true",
                        help="print the result without writing gate_a_result.json")
    args = parser.parse_args(argv)

    result = run(timeout=args.timeout)
    payload = result.to_json()
    print(payload)

    if not args.no_write:
        RESULT_PATH.write_text(payload + "\n", encoding="utf-8")

    # Exit code carries the verdict so a caller cannot mistake blocked for pass.
    return {"PASS": 0, "PARTIAL": 1, "FAIL": 1, "BLOCKED_NO_CREDENTIAL": 2}[result.verdict]


if __name__ == "__main__":
    time_start = time.time()
    code = main()
    print(f"\ngate_a probe finished in {time.time() - time_start:.2f}s with "
          f"exit code {code}", file=sys.stderr)
    raise SystemExit(code)
