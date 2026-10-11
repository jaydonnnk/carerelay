# Demo walkthrough

**What this is.** A script for the live demonstration required by Challenge 1, with
the real responses captured underneath each step. Every response in this file was
taken from a running server on 11 October 2026, not written from memory.

**Captured against:** `uvicorn carerelay.api:app` on `127.0.0.1:8137`, SQLite store,
`APP_CLOCK=scenario`, Python 3.13.12, repository at the Slice 12 tip. The scenario
clock is why the deadline reads "6pm today" rather than drifting with the date.

**One em dash (U+2014) appears below**, inside the `fixture_label` JSON, imported
verbatim from `src/carerelay/demo/fixture.py:FIXTURE_LABEL`. The project's own
writing rule bans em dashes in new content; the label is an approved wire-format
string and is shown exactly as the server returns it. The Slice 8 comparator card
carried the same em dash with the same disclosure.

**Two ways to show it.** Either open `https://carerelay.vercel.app` and drive the
patient screen, or run the commands below and show the JSON. The JSON is the stronger
evidence, because it is the same surface the tests assert against.

---

## 0. Start the server (local option)

```bash
cd carerelay
pip install -e ".[test]"
export PYTHONPATH=src APP_CLOCK=scenario APP_DATABASE_URL=/tmp/carerelay-demo.db
python -m uvicorn carerelay.api:app --host 127.0.0.1 --port 8137
curl -s http://127.0.0.1:8137/health
# {"status":"ok","version":"0.1.0"}
```

Auth is off in this configuration. On the deployed service, every `/api` and
`/ledger` route requires the shared bearer token, and a protected route with no token
configured answers 503 rather than opening (`src/carerelay/api.py:170`).

---

## 1. The episode, and the refusal that proves the scope

```bash
curl -s -X POST http://127.0.0.1:8137/api/episodes
```

```json
{"episode_id":"demo-episode-001","persona":"fictional older adult",
 "policy_version":"fixture-provisional-0","simulated":true,
 "fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
```

**Say this:** one fictional episode, one bound complaint, everything labelled.

```bash
curl -s -X POST http://127.0.0.1:8137/api/episodes/demo-episode-001/intake \
  -H 'content-type: application/json' \
  -d '{"confirmed_text":"I have chest pain and cannot breathe"}'
```

```json
HTTP 422
{"detail":{"detail":"the complaint is not the one this fixture is bound to, so no
 disposition may be issued: stop at the human path (D7)","stopped_at":"human_path"}}
```

**Say this:** the system does not triage free text. Anything outside the bound phrase
stops at a named human path. That is the honest boundary of a research demo
(`00-status.md:524-528`).

```bash
curl -s -X POST http://127.0.0.1:8137/api/episodes/demo-episode-001/intake \
  -H 'content-type: application/json' \
  -d '{"confirmed_text":"help sorting out my appointment"}'
```

```json
{"episode_id":"demo-episode-001","disposition_version":1,
 "action_id":"attend_same_day_review","deadline_utc":"2026-09-30T10:00:00+00:00",
 "next_owner_id":"patient","fallback_route_id":"nurse_line","simulated":true,...}
```

---

## 2. PlanBack: the patient restates the plan, and code checks it

```bash
curl -s -X POST .../restatements -H 'content-type: application/json' \
  -d '{"text":"see the doctor tomorrow before 6pm myself","hint_level":"H0","transcript_confirmation_id":"<id>"}'
```

```json
{"understood":false,"mismatches":["deadline_utc"],"uncertain":[],
 "outcome":"not_recalled","repair_round":0,"next_repair_field":"deadline_utc",
 "routes_to_human_path":false,...}
```

**Say this:** the mismatch is named, single, and repairable. The comparison is
deterministic: the deadline compares as a time bucket, the action against a closed
vocabulary of ids, the owner against the named party
(`03-planback-closure-contract.md:65-67`).

```bash
curl -s -X POST .../restatements/<id>/repairs -H 'content-type: application/json' \
  -d '{"text":"see the doctor today before 6pm myself","hint_level":"H1","transcript_confirmation_id":"<id>"}'
```

```json
{"understood":true,"mismatches":[],"uncertain":[],
 "outcome":"recall_scaffolded","repair_round":1,"next_repair_field":null,...}
```

**Say this:** one repair, of a cap of two. The third failure goes to the human path
rather than looping (`docs/PLAN.md:216`).

---

## 3. The four lines, and what they refuse to say

```bash
curl -s http://127.0.0.1:8137/api/episodes/demo-episode-001
```

```json
{"lines":["No one has agreed to help yet.","Please act now.",
 "Please do it before 6pm today.",
 "If that does not work, call the fictional nurse line."],
 "closure":"open","care_evidenced":false,"simulated":true,...}
```

**Say this:** four lines. No score, no probability, no symptom list. When nobody has
agreed, it says so.

---

## 4. An attempt that fails, and the words that do not change

```bash
curl -s -X POST .../consents -d '{"granted":true}'
curl -s -X POST .../actions -d '{"route_id":"fictional_provider","purpose_id":"book_transport"}'
```

```json
{"execution":"attempted","origin":"local-sim","outcome":"failed",
 "provider_ref":"simulated:local-only:carerelay-demo",
 "payload":"the simulated provider returned failed for route 'fictional_provider'; no real provider was contacted",...}
```

```bash
curl -s -X POST .../callbacks/fictional_provider \
  -d '{"callback_key":"walk-1","transition":"failed","origin":"local-sim"}'
# {"receipt":"applied","applied":true,"execution":"failed","origin":"local-sim"}

curl -s -X POST .../callbacks/fictional_provider \
  -d '{"callback_key":"walk-1","transition":"failed","origin":"local-sim"}'
# {"receipt":"duplicate","applied":false,"rejection_reason":"duplicate"}
```

```bash
curl -s http://127.0.0.1:8137/api/episodes/demo-episode-001
```

```json
{"lines":["No one has agreed to help yet.","Please act now.",
 "Please do it before 6pm today.",
 "If that does not work, call the fictional nurse line."],
 "closure":"open","care_evidenced":false,...}
```

**Say this, and it is the whole point:** the attempt failed and the screen did not
change. A click is not care. The duplicate callback was refused rather than counted
twice. The simulated provider fails on every route by default, so the demo can never
manufacture a success (`src/carerelay/simulated_provider.py:91`).

---

## 5. Closure changes only when the evidence axis moves

```bash
curl -s -X POST .../acceptances -d '{"accepted_by":"caregiver"}'
```

```json
{"accepted_by":"caregiver","scope":"handoff",
 "closure":"closed_with_evidence","care_evidenced":false,...}
```

```json
{"lines":["Someone has agreed to help.","You do not need to act now.",
 "It is set for 6pm today.",
 "If that does not happen, call the fictional nurse line."],
 "closure":"closed_with_evidence","care_evidenced":false,...}
```

**Say this:** line 1 says "agreed", not "arranged", and `care_evidenced` is still
false. A recorded acceptance is a promise, not evidence that care happened (F4,
`03-planback-closure-contract.md` section 2.2). The other two closure renderings,
`escalated_to_human` and `expired_unresolved`, were proven live at Slice 10 and their
approved words are in `01-product.md:66-89`.

---

## 6. The judge ledger

```bash
curl -s http://127.0.0.1:8137/api/episodes/demo-episode-001/ledger
```

```json
{"axes":{"execution":"failed","evidence":"none","closure":"closed_with_evidence",
 "action_owner_id":"patient","care_evidenced":false,"simulated":true},
 "disposition_version":1,
 "attempts":[{"route_id":"fictional_provider","execution":"failed",
   "transitions":[{"seq":1,"kind":"failed","origin":"local-sim",
   "recorded_at":"2026-09-30T01:00:00+00:00"}]}],...}
```

**Say this:** the two axes are visible and independent. `execution` is `failed` while
`closure` is `closed_with_evidence`, and that is exactly the distinction the product
exists to keep. Every transition carries its origin, and in this build the origin is
`local-sim` by design. An unknown episode answers 404.

One measured caveat, stated rather than skipped: of the five fault assertions the
ledger displays, one is falsifiable today and four are display only, because the
states that would falsify them are unreachable in this build
(`00-status.md:474-478`).

---

## 7. Suggested timing

| Step | Minutes |
|---|---|
| The refusal, and why the scope is one complaint | 1 |
| PlanBack: the mismatch, the repair, the cap | 2 |
| The four lines | 1 |
| The failed attempt that changes nothing | 2 |
| Acceptance, and "agreed" versus "arranged" | 1 |
| The ledger: two axes, one origin | 2 |
| Honest limits from `honest-claims.md` | 2 |

Roughly 11 minutes, of which the last two are the ones that earn the Responsible AI
score.
