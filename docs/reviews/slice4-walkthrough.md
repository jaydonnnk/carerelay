# Slice 4 walkthrough, 1 October 2026

**The Check in `04-slices.md` for Slice 4 is: "Walk the user through a mismatch,
one field repaired, then a clean pass, and a third failure routing to the human
path."** This file is the record of that Check being run. It is a transcript of a
live HTTP session against a running server, not a summary of one.

**Status: run, not yet confirmed by the user.** The slice is marked shipped but
not complete until the user has been walked through this. Nothing in
`00-status.md` claims completion on the strength of this file alone.

## How it was run

```
cd C:/Users/jayd0/OneDrive/Desktop/ai-triage
PYTHONPATH=src APP_DATABASE_URL=<temp file> \
  C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe \
  -m uvicorn carerelay.api:app --host 127.0.0.1 --port 8017
```

The database was pointed at a temp file rather than left in memory so the ledger
could be read after the run. `APP_CLOCK` was left at its default, `scenario`, so
the fixture deadline stays at 18:00 SGT on the scenario day.

Baseline before the walkthrough: `pytest -o addopts="" -q` gives **383 passed,
1 warning**. The `-o addopts=""` form is required: `pyproject.toml` already sets
`addopts = "-q"`, and a second `-q` becomes `-qq`, which suppresses the summary
line and reads like "no result".

## 1. The episode, and the two intake outcomes

```
POST /api/episodes
{"episode_id":"demo-episode-001","persona":"fictional older adult",
 "policy_version":"fixture-provisional-0","simulated":true, ...}

POST /api/episodes/demo-episode-001/intake   "I have chest pain and cannot breathe"
HTTP 422 {"detail":{"detail":"the complaint is not one this fixture is bound to,
        so no disposition may be issued: stop at the human path (D7)",
        "stopped_at":"human_path"}}

POST /api/episodes/demo-episode-001/intake   "I need help sorting out my appointment"
{"disposition_version":1,"action_id":"attend_same_day_review",
 "deadline_utc":"2026-09-30T10:00:00+00:00","next_owner_id":"patient",
 "fallback_route_id":"nurse_line","simulated":true, ...}
```

The unbound complaint stops before any disposition exists. The bound one issues
the preauthored fixture plan and nothing else: no disposition is derived from free
text.

## 2. The hint ladder, and that nothing hides itself

| Call | Response |
|---|---|
| `H0 / shown` | `{"hint_level":"H0","card_visible":true}` |
| `H2 / shown`, `dwell_seconds 45.5` | `{"hint_level":"H2","card_visible":true}` |
| `H2 / shown`, `dwell_seconds 900` | `{"hint_level":"H2","card_visible":true}` |
| `H2 / patient_hid` | `{"hint_level":"H2","card_visible":false}` |

The card survives a 900 second dwell. Only `patient_hid` removes it. No response
carries `dwell_seconds`.

## 3. Transcript confirmation comes first

```
POST /transcript-confirmations
{"confirmation_id":"tc-f62348b4..."}

POST /restatements  input_mode=voice, no confirmation id
HTTP 409 "an voice restatement may not be scored before its transcript is confirmed"

POST /restatements  input_mode=voice, with the confirmation id
{"understood":true,"outcome":"recall_unaided","transcript_confirmed":true,...}
```

## 4. The mismatch, the repair, and the clean pass

```
round 0  "I will go to the clinic today before 8pm, and I will do it myself."
  understood=false  mismatches=["deadline_utc"]  outcome=not_recalled
  next_repair_field="deadline_utc"  routes_to_human_path=false

repair 1 "I will go to the clinic today before 6pm, and I will do it myself."
  understood=true   mismatches=[]  uncertain=[]  outcome=recall_unaided
  next_repair_field=null  routes_to_human_path=false
```

One field was repaired and the round became a clean pass at H0.

## 5. The third failure routes to the human path

A second ladder, where the action span cannot be resolved. An unrecognised span is
recorded `uncertain`, never `mismatched`: the product does not accuse a patient of
being wrong about a word it did not understand.

```
round 0  (H1)  uncertain=["action_id"]  next_repair_field="action_id"
repair 1 (H2)  uncertain=["action_id"]  next_repair_field="action_id"
repair 2 (H3)  uncertain=["action_id"]  next_repair_field=null
               routes_to_human_path=true  human_path_route_id="nurse_line"
               outcome=not_recalled

a fourth call  HTTP 409 "two repairs is the maximum and a third is never
               offered (C6). Route to the human path."
a repair against round 0 of that ladder
               HTTP 409 "is not the latest round ... repair the round the
               previous response named"
```

The third attempt does not fail open. It names where the patient goes.

## 6. H3 is not a pass

The same clean restatement, scored at two different rungs:

| Rung | `understood` | `outcome` |
|---|---|
| H0 | true | `recall_unaided` |
| H3 | true | `not_recalled` |

Revealing the plan is never recorded as comprehension.

## 7. The ledger side of `dwell_seconds`

Read from `events` after the run:

```
hint_event -> {"hint_level":"H0","kind":"shown","dwell_seconds":null}
hint_event -> {"hint_level":"H2","kind":"shown","dwell_seconds":45.5}
hint_event -> {"hint_level":"H2","kind":"shown","dwell_seconds":900.0}
hint_event -> {"hint_level":"H2","kind":"patient_hid","dwell_seconds":null}
```

Eight restatement rows, one per scored round, each carrying its round, hint level,
input mode, transcript-confirmed flag and outcome. One disposition row, version 1,
source `fixture`. No patient-facing response in the run contains the string
`dwell`.

## 8. The stop condition, and what this does not prove

The Slice 4 stop condition is "if H0 to H2 leak a critical field, stop". No route
in this slice returns hint text at all: `POST /hint-events` answers with the rung
and the card's visibility and nothing else, so there is no surface from which a
critical field could leak. That is structural, not yet a demonstration of the real
hint copy, which does not exist until the wording is authored.

What this transcript does not prove:

1. **The coordinator is a local simulation.** `LocalSimulationCoordinator` is a
   deterministic scanner over the policy's surface forms. `02-architecture.md` 3.3
   requires the coordinator to execute the tool through the platform with the
   failure event originating there. Nothing here exercises that, and Gate A has
   still not run.
2. **K1 is not re-proven here.** The comparator's behaviour against the paraphrase,
   alias, relative-time and code-switched corpus was proven in the Slice 0 spike.
   This run shows the wiring honours Reading A, not the corpus again.
3. **The fixture is provisional and unsourced.** No value in it is a clinical
   threshold and nothing in it has been shown to a participant.
4. **Nothing here is evidence of** WorkBuddy access, clinical safety, human
   learning or patient benefit.
