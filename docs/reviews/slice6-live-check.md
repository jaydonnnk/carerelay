# Slice 6 Check: the origin marker, distinguishable by inspection

**Check run, 3 October 2026.**
**Branch:** `slice-6` at `f0c8731` (uncommitted, unpushed at the time of the run).
**Interpreter:** managed Python 3.13 (pytest 9.x, fastapi) via
`C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe`.
**Constraints honoured:** no gate document edited, no slice or gate state changed, no
commit, no push, no install, no credential, no external call. Tree left as found.

---

## 1. Verdict

**PASS, with the reasoning stated plainly.**

The Slice 6 Check (`04-slices.md`) is: *"Show the user the ledger rendering the origin
marker, once for a platform failure and once for a local simulation. They must be
distinguishable by inspection."*

Both are shown below from a live server. They are distinguishable by inspection, and by
more than inspection: one is an **HTTP 200** whose body carries `"origin": "local-sim"`
next to the applied receipt, and one is an **HTTP 422** whose body carries
`"requested_origin": "platform"` and `"wired_origin": "local-sim"`.

**The sentence that matters, and it is not a hedge.** There is no platform origin marker
that reads `"platform"` inside a 200 response, and there cannot be one in this build,
because **no platform executed anything.** Gate A (2 October 2026) proved the transport
carries an origin signal; it did not prove tool execution, and D8 forbids ADP carrying the
section 3.3 claim. So the honest rendering of "a platform failure" is the **refusal**: a
caller that states `origin: "platform"` is told, in a typed 422 body, that `platform` is
the origin it asked for and `local-sim` is the origin this deployment can actually
produce. That refusal *is* the platform-half of the Check. Anything else would be a
marker asserting a fact no observation supports.

| Claim | Verdict |
|---|---|
| **Claim 1: the local-simulation marker is live and inspectable.** | **PASS.** A 200 callback returns `"origin":"local-sim"` on the response body, not buried in a payload. |
| **Claim 2: the platform-origin path is distinguishable and refuses.** | **PASS.** A callback stating `origin:"platform"` returns 422 with `requested_origin` and `wired_origin` naming both values. |
| **Claim 3: the two are distinguishable by inspection.** | **PASS.** Different status codes, different bodies, one names `platform` as requested and `local-sim` as wired. |
| **Claim 4: the O5 receipt states are live, not only unit-tested.** | **PASS.** `applied`, `duplicate` and `refused` each observed over HTTP. |
| **Claim 5: the boundaries stay typed, not 500.** | **PASS.** Unknown episode 404, no-attempt route 409, bad enum 422, unwired origin 422. |

**No blocking finding.** Two documenting notes in section 5, neither a code defect.

---

## 2. The Check, raw

Server started, exercised and killed in one command. `APP_DATABASE_URL` points at a real
file so the record is real SQL across the run. Ports 8012 and 8013.

### 2.1 Setup (the sequence the action path requires)

```
=== POST /api/episodes ===
{"episode_id":"demo-episode-001","persona":"fictional older adult","policy_version":"fixture-provisional-0","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice.","note":"Slice 1 tracer bullet: hardcoded. ..."}
[HTTP 200]

=== POST /api/episodes/demo-episode-001/intake ===
{"episode_id":"demo-episode-001","disposition_version":1,"action_id":"attend_same_day_review","deadline_utc":"2026-09-30T10:00:00+00:00","next_owner_id":"patient","fallback_route_id":"nurse_line","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]

=== POST /api/episodes/demo-episode-001/consents {"granted": true} ===
{"episode_id":"demo-episode-001","scope":"clinical_share","version":1,"granted":true,"simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]
```

### 2.2 The open, and the origin it carries

```
=== POST /api/episodes/demo-episode-001/actions {"route_id":"fictional_provider","purpose_id":"book_appointment"} ===
{"episode_id":"demo-episode-001","attempt_id":"51326a8024c642c9aad523590beb5e82","idempotency_key":"att-ad39b79444a593a4dd49839f55242121a18910607dd4ee5922a4ef30fb55b73b","route_id":"fictional_provider","purpose_id":"book_appointment","disposition_version":1,"consent_version":1,"execution":"attempted","duplicate":false,"origin":"local-sim","outcome":"failed","provider_ref":"simulated:local-only:carerelay-demo","payload":"the simulated provider returned failed for route 'fictional_provider'; no real provider was contacted","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]
```

The open already carries `"origin":"local-sim"` and a provider ref that says
`simulated:local-only`. Nothing here reached a network.

### 2.3 The Check, case A: the platform failure (the refusal)

```
=== POST /api/episodes/demo-episode-001/callbacks/fictional_provider
    {"callback_key":"cb-platform-001","transition":"acknowledged","payload":"platform says done","origin":"platform"} ===
{"detail":{"detail":"origin 'platform' is not one this deployment can produce; the wired path reports 'local-sim'. No tool is executed through a platform in this build, so recording a platform origin would state a fact no observation supports.","requested_origin":"platform","wired_origin":"local-sim"}}
[HTTP 422]
```

**This is the platform half of the Check.** The caller said a platform answered. The
deployment refused it, and the refusal names the requested origin beside the wired one.
The marker is inspectable and it tells the truth: the platform is the origin that was
*asked for*, not the origin that *ran*.

### 2.4 The Check, case B: the local simulation (the applied receipt)

```
=== POST /api/episodes/demo-episode-001/callbacks/fictional_provider
    {"callback_key":"cb-localsim-001","transition":"acknowledged","payload":"local simulation says done"} ===
{"episode_id":"demo-episode-001","route_id":"fictional_provider","attempt_id":"51326a8024c642c9aad523590beb5e82","origin":"local-sim","receipt":"applied","applied":true,"rejection_reason":null,"execution":"acknowledged","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]
```

`"origin":"local-sim"`, `"receipt":"applied"`, `"applied":true`. The origin field is on the
response body itself, which is what section 3.3 step 6 asks for ("displayable by
inspection"), not a marker buried in `payload`.

### 2.5 Case A against case B, side by side

| | Case A: platform failure | Case B: local simulation |
|---|---|---|
| Status | **422** | **200** |
| Body field naming the origin | `requested_origin: "platform"` **and** `wired_origin: "local-sim"` | `origin: "local-sim"` |
| Verdict field | `detail` (a refusal sentence) | `receipt: "applied"`, `applied: true` |
| Which origin actuated | none | `local-sim` |

A reader sees two different codes, two different shapes, and one body that explicitly
pairs the two origin values. **Distinguishable by inspection: yes.**

### 2.6 The O5 receipt states, all three, live

```
=== duplicate of case B (same callback_key) ===
{"episode_id":"demo-episode-001","route_id":"fictional_provider","attempt_id":"51326a8024c642c9aad523590beb5e82","origin":"local-sim","receipt":"duplicate","applied":false,"rejection_reason":"duplicate","execution":"acknowledged","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]
```

A second run revoked consent at version 2 and then let a success arrive on the `nurse_line`
attempt:

```
=== POST /consents {"granted": false} ===
{"episode_id":"demo-episode-001","scope":"clinical_share","version":2,"granted":false,"simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]

=== POST /callbacks/nurse_line {"transition":"acknowledged","origin":"local-sim"} after revocation ===
{"episode_id":"demo-episode-001","route_id":"nurse_line","attempt_id":"580cf077b9e0492991186a4d0d72d487","origin":"local-sim","receipt":"refused","applied":false,"rejection_reason":"clinical_share consent is revoked at version 2","execution":"attempted","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]
```

`applied`, `duplicate` and `refused` are each a real HTTP outcome with a distinct
`receipt` value on the wire. The distinction O5 was raised for (a duplicate is a correct
no-op; a refusal is a success that was rejected) is visible without reading code.

### 2.7 The boundaries stay typed

```
=== POST /callbacks for an unknown episode ===
{"detail":"episode 'no-such-episode' not found"}
[HTTP 404]

=== POST /callbacks for a route that opened no attempt ===
{"detail":"episode 'demo-episode-001' opened no attempt on route 'fictional_provider', so a callback for it has nothing to answer"}
[HTTP 409]

=== POST /callbacks with an unknown enum transition ("succeeded") ===
{"detail":"'succeeded' is not a valid ExecutionStatus"}
[HTTP 422]
```

Each refusal is a typed code naming what was wrong. None is a 500. The `succeeded`
rejection is the one I provoked first by mistake: I sent a transition value that is not
in `ExecutionStatus` and the route answered 422 rather than crashing, which is the
behaviour NF2 will require of the rest of the surface at Slice 7.

---

## 3. Baseline, before and after

```
$ git branch --show-current && git status --short
slice-6
 M PROGRESS.md
 M docs/plans/urgent-advice-accessibility/00-status.md
 M src/carerelay/api.py
 M src/carerelay/coordinator.py
 M src/carerelay/domain/models.py
 M src/carerelay/domain/rules.py
 M src/carerelay/service.py
 M src/carerelay/state.py
 M tasks/todo.md
 M tests/test_api.py
 M tests/test_domain.py
 M tests/test_service.py
 M tests/test_state.py
?? src/carerelay/simulated_provider.py
?? src/carerelay/tools.py
?? tests/_mutate_slice6.py
?? tests/test_coordinator.py
?? tools/_fix_status_slice6.py
?? tools/_fix_todo_slice6.py

$ PYTHONPATH=src <python> -m pytest -o addopts="" -q
482 passed, 1 warning in 16.27s
```

**482 passed, 1 warning**, matching the documented Slice 6 baseline. The single warning is
the pre-existing Starlette `httpx` deprecation notice, not a Slice 6 artefact. The tree is
in the documented uncommitted Slice 6 state; this Check changed no tracked file.

---

## 4. What the Check did and did not prove

**Proved, live, on a running server:**

- The local-simulation origin marker renders on a 200 callback response body.
- The platform origin is refused, and the refusal names `requested_origin` and
  `wired_origin`.
- The three O5 receipt states (`applied` / `duplicate` / `refused`) are each reachable
  over HTTP with distinct wire shapes.
- The 404, 409 and 422 boundaries each answer with a typed body, never a 500.

**Not proved here, and not claimed:**

- **That any platform executed anything.** It did not, and D8 says it must not claim to.
  This Check is consistent with the Gate A limit, not evidence against it.
- **That the origin marker survives the ADP wiring.** No ADP call is wired into `src/`.
  When it is, the origin field is the thing that must keep telling the truth.
- **Persistence across restart.** The run wrote to a file, but restart survival is
  Slice 7's; the local demo path is in-memory by default.
- **Clinical safety.** Nothing here is reviewed clinical content and no reviewer exists.

---

## 5. Findings

### N1. [verified] note. There is no 200 marker reading `"platform"`, by design

The Check's contract phrase "once for a platform failure" might be read as expecting a 200
whose body says `platform`. Such a body does not exist in this build and should not: the
platform never ran, so a marker reading `platform` in a 200 would assert an execution that
did not happen. The honest rendering is the 422 refusal in section 2.3, which names the
platform as the requested-but-unwired origin. This is recorded rather than fixed, because
the correct behaviour is the refusal.

### N2. [verified] note. The Check exercises the callback, not a rendering surface

The Check says "the ledger rendering the origin marker". Today the marker is rendered on
the **JSON response body**, which is inspectable but is not a human-facing ledger page. A
rendered ledger view is a later slice's surface. The Slice 6 obligation, that the marker
be *displayable by inspection* rather than buried in a payload, is met by the response
field; a styled page is out of scope and is not claimed here.

### N3. [verified] note. `OriginNotWired` is the honesty mechanism, not a comment

The refusal is implemented in `service.receive_callback` by comparing the caller-stated
origin to `self._origin`, and the wiring value comes from the coordinator, not the request
(`service.py` lines 385 to 395). A caller cannot make the marker read `platform` by asking
for it. That is the property the Check depends on; it is enforced in code, not documented
in prose.

---

## 6. Disclosure: em dashes in this file

`AGENTS.md` section 6 bans em dashes in new writing.

- **This file carries 8 U+2014 in total, and none is authored prose.** Each sits inside a
  pasted response body, in the pre-existing approved `"fixture_label"` string
  (`SIMULATED - RESEARCH DEMONSTRATION. Not clinical advice.` with an em dash where the
  hyphen is shown here) that ships on every response.
- I reproduced the pasted bodies verbatim because editing quoted evidence would falsify
  it. The same disclosure pattern is used by `docs/reviews/slice5-live-check.md`.
- No other line in this file contains U+2014.

---

## 7. Artefacts

| Path | State |
|---|---|
| `docs/reviews/slice6-live-check.md` | this file, untracked, not committed |
| the live run | servers on 8012 and 8013, started and killed within single commands; no process left running |
| `APP_DATABASE_URL` files | written under the OS temp directory, outside the repo |

No gate document was edited, so no gate reopened. Nothing was committed or pushed by
this run, and the transcript above is the tree as it stood at `f0c8731`. **Superseded,
3 October 2026:** the Slice 6 work was subsequently walked through, approved for commit,
and shipped on the user's explicit instruction (five commits, tip `dc95295`,
fast-forwarded into `main`, both branches pushed to `origin`). The run itself changed
nothing; this note is added so a later reader does not read "uncommitted and unpushed"
as the current state. See `00-status.md` for the authoritative state.
