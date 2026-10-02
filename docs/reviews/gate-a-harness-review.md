# Gate A access harness: adversarial review

Reviewer: Brody. Date: 2 October 2026.
Scope: `spike/gate_a/probe.py` and `spike/gate_a/test_probe.py`, branch `slice-5`,
HEAD `f131ef2`. Read-and-report only; no file was edited.

Method: `C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe`,
`PYTHONPATH=src ... -m pytest spike/gate_a/test_probe.py -o addopts="" -q`.
The probe was never run against a real credential; none exists and none was sought.
Every mutation was applied to `probe.py` in place with a byte-identical backup and
restored, verified by md5 `37331e7a85b4d24d6325275da6482625` before and after.

---

## Verdict

**PARTIAL CREDIT: the harness is honest about what it observes, but two of its six
claims do not hold, and its central verdict logic is untested.**

- Claims 1, 4, 5, 6 hold in substance (claim 5 with two undocumented guesses).
- **Claim 2 is falsified on one path**: an uncaught exception prints the raw AppKey
  to stderr in the traceback. No realistic trigger inside the harness's own code
  was found, but the redaction boundary is real and narrower than the docstring
  implies.
- **Claim 3 is falsified for the mapping property**: three independent mutations of
  `run()`'s verdict logic all leave the suite green (0 red). The verdict mapping is
  tested only through a hand-copied duplicate that nothing compares back to the
  original.
- Additional gap not in the claim list: the harness reads the response as a single
  text body, but the guide documents the response as a stream of SSE events.

The honest summary: it fails closed and does not invent results, which is the
property that mattered most. But "the 17 tests can fail" is true only for the
fail-closed and redaction properties, not for the verdict mapping.

Baseline: **17 passed** in 0.29s, matching the claim's count.

---

## Claim 1: it fails closed, and cannot report a verdict it did not observe

**UPHELD on every path exercised.**

Command:

```
PYTHONPATH=src <python> spike/gate_a/probe.py --no-write
```

Actual output (no `ADP_APPKEY`, no `ADP_API_SECRET`):

```
"credential_present": false,
"verdict": "BLOCKED_NO_CREDENTIAL",
"verdict_reason": "The spike did not run. A missing credential is a blocked check..."
EXIT CODE=2
```

Paths attacked, each against the real `run()` with a mocked transport:

| Attack | Result | Correct? |
|---|---|---|
| No key, no secret | `BLOCKED_NO_CREDENTIAL`, exit 2 | yes |
| Secret set, key absent | `BLOCKED_NO_CREDENTIAL`, no network | yes |
| Key set to empty string `''` | `BLOCKED_NO_CREDENTIAL` (empty is falsy) | yes |
| q1 401, q2 skipped, q3 passes | `PARTIAL` | yes |
| Every call raises `ConnectError` | `FAIL` | yes |
| q3 returns a bare 200 | q3 `ok=False`, not a pass | yes |
| All three observe | `PASS` | yes |

No path was found that reports `PASS` from an observation that was not made. The
`len(passed) == 3` gate over `ran`-filtered observations is genuinely closed.

**One thing it does not check:** `credential_present` is `bool(os.environ.get(...))`,
so any non-empty string counts as a credential. A typo'd or stale key is
indistinguishable from a valid one at the precondition stage, which is correct
(it can only be told apart by a call), but it means "credential present" is not a
validity claim. The harness does not imply otherwise.

---

## Claim 2: it never persists the credential

**FALSIFIED on one path: an uncaught exception prints the full key to stderr.**

The docstring says "redacted from any captured response." `_post` catches only
`httpx.HTTPError`:

```python
    try:
        response = client.post(ADP_CHAT_ENDPOINT, json=payload, headers=header)
    except httpx.HTTPError as exc:
        return None, f"{type(exc).__name__}: {_redact(str(exc))}"
```

Any exception that is **not** an `httpx.HTTPError` propagates with `header` (which
holds the raw key) in the traceback frame.

Demonstrated: a `TypeError` raised from `client.post` propagates out of `run()` and
the traceback contains `{'X-Api-Key': 'sk-live-ABCDEF123456'}` verbatim. Confirmed
reachable in the real library: `httpx.Client().post(..., headers={'X-Api-Key': None})`
raises `TypeError`, which is **not** an `HTTPError`:

```
{'X-Api-Key': None} -> TypeError | HTTPError? False
{'X-Api-Key': 12345} -> TypeError | HTTPError? False
```

**Severity, stated honestly:** the harness's own `_headers()` always supplies a
`str` (`os.environ.get(APPKEY_ENV_VAR, "")`), so the `None`/int inputs are not
reachable through the harness's own code. A realistic trigger would need a bug
inside httpx itself, or a non-str value entering the header dict by some other
route. So the leak is real but has **no proven realistic trigger** inside this
harness. It is still a boundary narrower than the claim: the correct statement is
"redacted in every response and every `HTTPError` it catches," not "never written."

What **does** hold:

- **Result JSON**: with a server echoing the full key in every body, `KEY in
  result.to_json()` is `False`. Redacted.
- **Caught exception message**: `ConnectError: ... X-Api-Key: <redacted:ADP_APPKEY>`
  in the persisted evidence.
- **Twelve header/key forms** tried (`x-api-key:`, `api_key=`, `{"apikey":...}`,
  `Bearer`, `APIKEY=`, URL query, `'api key'`, JSON `"key"`, repr of a dict) were
  all redacted, because the full-value `replace` fires before the regex backstop.

**A form the regex misses (not a credential leak):** the masked-prefix regex
requires an `appkey` label. A bare masked fragment with no label, e.g.
`error: credential sk-live-ABCD rejected`, passes through unredacted. This leaks
only the **masked prefix**, which the console already shows publicly, so it is not
a full-value leak. The full value never survives when the regex is the only guard,
because the full-value `replace` handles it. Report it, do not inflate it.

---

## Claim 3: the 17 tests can fail

**PARTIALLY TRUE. Fail-closed and redaction are covered. The verdict mapping is
NOT covered by any test, and three mutations of it survive.**

Mutations applied one at a time to `probe.py`, targeted suite run each time,
restored after each. Blast radius reported, not a count.

| # | Property | Mutation | Red | Which tests |
|---|---|---|---|---|
| A1 | fails closed | invert `if not result.credential_present` | 3 | `test_no_credential_records_blocked`, `..._does_not_claim_a_pass`, `test_main_returns_exit_code_two_when_blocked` |
| A2 | fail-closed exit code | map `BLOCKED_NO_CREDENTIAL` to 0 | 1 | `test_main_returns_exit_code_two_when_blocked` |
| B1 | redaction | full-value `replace` made a no-op | 2 | `test_a_key_in_a_response_body_is_redacted`, `test_a_secret_in_an_exception_message_is_redacted` |
| B2 | redaction | masked-appkey regex disabled | 1 | `test_a_masked_appkey_in_a_message_is_redacted` |
| C1 | verdict mapping | `run()` PASS threshold `== 3` to `>= 1` | **0** | none |
| C2 | verdict mapping | `run()` drops the `if o.ran` filter | **0** | none |
| C3 | verdict mapping | `run()` FAIL branch emits `PASS` | **0** | none |
| Q3A | q3 reading | any 4xx counts as ok (drop identifier check) | 1 | `test_a_bare_error_with_no_identifier_is_not_an_origin_signal` |
| Q3B | q3 reading | a 200 on the invalid request counts as ok | 1 | `test_a_200_on_an_invalid_request_is_not_a_pass` |

Blast radius, per AGENTS.md section 6 ("a fault two checks can both catch counts as
proof of neither"):

- **A1 has radius 3**, but two of the three are the same property (fail-closed
  outcome) asserted twice, and the third adds the exit code. Not a clean 1:1.
- **B1 has radius 2**: `test_a_key_in_a_response_body_is_redacted` and
  `test_a_secret_in_an_exception_message_is_redacted` both depend on the single
  `replace` line. They are not independent proofs of redaction; they prove the
  same line twice.
- **C1, C2, C3 have radius 0.** This is the finding.

**Why C1–C3 survive: the tests exercise a copy, not the code.** `TestVerdictMapping`
calls `_verdict_for(...)`, defined in the test file at line 198 as a hand-written
re-implementation. `probe.run()` is called only in the two no-credential tests
(lines 63, 73), where it returns at the early `BLOCKED_NO_CREDENTIAL` branch and
**never reaches the mapping at lines 268 to 291**. So mutating the real mapping is
invisible to the suite.

The test docstring claims the duplication means "a change to `run`'s mapping shows
up as a mismatch here." That is backwards: nothing compares the two. Two copies of
a rule do not check each other; the copy is exactly why the original is untested.
This is the single most important defect in the harness.

The same structural gap applies to `probe_session_continuity`: there is no direct
test of its ok/not-ok branches, only of the q3 reader and the mapping helper.

---

## Claim 4: the verdict mapping is honest

**UPHELD as written, but undefended by tests.**

Exercised end to end through the real `run()` with a mocked transport:

| Observation shape | Verdict | Correct? |
|---|---|---|
| all three observe | `PASS` | yes |
| q3 bare error, no identifier | `PARTIAL` | yes |
| q1 ok, q2 rejected, q3 ok | `PARTIAL` | yes |
| everything 500 | `FAIL` | yes |
| q1 401, q2 skipped, q3 is a 200 | `FAIL` | yes |

`PARTIAL` and `FAIL` are not softened: a skipped probe (`ran=False`) cannot
contribute a pass, and "no pass at all" produces `FAIL`, not `PARTIAL`. The mapping
is honest. But per claim 3, none of this behaviour is protected by a failing test,
so a future edit could soften it silently.

---

## Claim 5: the endpoint and auth claims match the guide

**ENDPOINT: verified. AUTH: one verified, two undocumented guesses. SESSION: verified.**

Guide lines relied on, quoted from `docs/ADP_Hackathon_Guide_EN.pdf`:

- **Endpoint (page 8):** "Endpoint | https://wss.lke.tencentcloud.com/adp/v2/chat".
  The harness uses exactly this. **[verified]** exact match.
- **Auth (page 7):** "HTTP SSE calls need the Appkey alone, while the WebSocket API
  needs the Appkey together with the API Secret." **(page 8):** "Authentication |
  Send the AppKey with the request. HTTP SSE needs the Appkey alone". The harness
  docstring says the same. **[verified]** for the *requirement*.
- **Session (page 8):** "Session | ConversationId; reuse the same value for a
  multi-turn conversation". The harness reuses `ConversationId`. **[verified]**.
- **User (page 8):** "User | VisitorId; give each end user their own". Used.
  **[verified]**.

**Where the harness asserts something the guide does not say:**

1. **`X-Api-Key` as the first header shape is a guess. [hypothesis]** The guide
   never names a header. It says only "Send the AppKey with the request." No
   `x-api-key` string appears anywhere in the nine pages.
2. **`Authorization: Bearer <key>` as the second shape is a guess. [hypothesis]**
   "Bearer" does not appear in the guide.
3. The docstring frames these as resolving a documented conflict: "The guide's own
   docs conflict on the exact scheme." The guide does not conflict; it is silent on
   the header and defers to the ADP Chat API documentation ("For the full set of
   fields and events, refer to the ADP Chat API documentation"). The conflict is
   between the architecture document's recollection of the docs and the guide, not
   inside the guide. The harness is honest that it is guessing (it tries both and
   records whichever answers), but the justification overstates the guide.
4. **Response type [problem].** Guide page 8: "Response | A stream of SSE events,
   returned as the answer is generated." The harness reads `response.text[:4000]`
   as a single body; it never sets `stream=True` and never iterates SSE frames. The
   `ConversationId` regex *does* match inside an SSE `data:` frame when tested, so
   the design gap may not break detection, but the harness is built for a JSON body
   the guide does not promise.

**One more, not in the guide:** `ADP_CHAT_ENDPOINT` is overridable by env var and
defaults to the documented URL. That default is the only endpoint value the guide
supports. **[verified]** for the default; the override is un-grounded but harmless.

---

## Claim 6: it is genuinely a spike

**UPHELD.**

- `src/` contains **no import** of the harness. `grep -rn "import.*gate_a\|from.*gate_a"
  src/` returns nothing. The only `spike` mentions in `src/` are two comments
  (`coordinator.py`, `demo/fixture.py`), not imports.
- The output file is gitignored: `git check-ignore -v spike/gate_a/gate_a_result.json`
  returns `.gitignore:37:gate_a_result.json`.
- Under `spike/`, only the harness (`probe.py`, `test_probe.py`) is tracked; the
  result file does not exist on disk.
- The harness writes to exactly one path (`RESULT_PATH`); its only `print` emits the
  already-redacted payload and a timing line.

---

## What the harness does not check

Stated plainly:

1. **The verdict mapping** (claim 3). Three mutations survive. This is the biggest
   one.
2. **`probe_session_continuity`'s own branches** have no direct test.
3. **The SSE response shape** the guide documents (claim 5, item 4).
4. **Real reachability, auth, and the failure-origin signal** are never exercised by
   the suite, which is correct (they need a credential) but means the suite cannot
   catch a wrong endpoint, a wrong header, or a false q3 read. Those are the whole
   point of the spike, and the suite proves none of them.
5. **`ConversationId` truncation.** `probe_auth_and_reachability` stores the response
   as `body[:600]` (line 146), and `_extract_conversation_id` reads that truncated
   evidence. If the id lands past 600 characters in an SSE stream (plausible for a
   real agent reply), extraction returns `None`, q2 is silently skipped, and the
   verdict is capped at `PARTIAL`. The failure biases toward not-pass, so it is
   conservative, but a genuinely working session could be mis-recorded as
   "continuity not attempted."
6. **The exit code does not distinguish PARTIAL from FAIL** (both 1). Intentional
   per the code, but a caller cannot tell them apart from the exit code alone.
7. **A `--no-write` run that is blocked** still prints a full result to stdout. Fine,
   but stdout is a credential surface the result-file redness does not cover. The
   payload is redacted, so this is safe today.

---

## Push-back on the harness and its justification

- **"The 17 tests can fail" is not supported for the property that decides the
  verdict.** The docstring at lines 3 to 4 of the test file says "a harness that
  cannot fail proves nothing," and then leaves the verdict logic untested. Fix the
  duplicate: call `run()` with a mocked client and assert the verdict, and delete
  `_verdict_for` or keep it only as an independent oracle with a test that the two
  agree.
- **"It never writes the credential" is too broad.** Narrow it to the surfaces that
  hold: the result file, stdout, and caught `HTTPError` messages. An uncaught
  non-`HTTPError` exception is outside the guard. Cheap fix: catch `Exception` in
  `_post`, or redact the key from `repr(header)` before any request.
- **"The guide's own docs conflict on the exact scheme" is the wrong sentence.** The
  guide is silent on the header and defers to the ADP Chat API docs. Say that.
- **The response is documented as SSE; the harness reads it as text.** Either read
  the stream or state in the docstring why reading `.text` is sufficient for this
  probe.

---

## Bottom line

The harness fails closed and does not fabricate an observation. Those were the two
properties most worth having, and they hold. But the review brief's own framing
("the 17 tests can fail") is only two-thirds true: the fail-closed and redaction
properties are defended, and the **verdict mapping, which is what the whole spike
reports, is entirely undefended**. The credential claim is one exception type too
broad. The endpoint and session fields match the guide exactly; the header shape is
an honest guess presented with a slightly overstated justification.

Nothing here says the spike's live result would be wrong. It says the harness's
self-description and its test coverage are stronger than the code supports.
