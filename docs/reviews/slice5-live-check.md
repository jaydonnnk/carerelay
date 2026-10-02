# Slice 5 live check: the judged fixture and the abstention path

**Independent adversarial review, 2 October 2026.**
**Reviewed:** branch `main` at `d5efdc5`. Interpreter: managed Python 3.13.14.
**Constraints honoured:** no gate document edited, no slice or gate state changed, no
commit and no push, B3 untouched, F6's rendering half not authored.

---

## 1. Verdict

**PASS WITH CONCERNS.**

| Claim | Verdict |
|---|---|
| **Claim 1: the abstention path is real.** With no reviewer the product must stop at the human path and must not write a secondary disposition. | **PASS.** I tried and failed to construct an input where it guesses. I also proved structurally why: only two production call sites can write a disposition, and both are gated. |
| **Claim 2: the fail-capable tests actually fail.** | **PASS, after one fix made during this pass (S2).** F6, O7 and K2 are each independently proven. At the first reading K2 was one third proven; a new assertion added during this pass closes the gap, and mutation M4 proves it alone. |

**No blocking finding in the code.** Two should-fix findings, both documentary or evidential, and **both closed during this pass**: S1, a false statement in the authority file about the slice's Git state, and S2, an evidence gap in K2. See section 5 and mutation M4.

---

## 2. What I verified, and how

### 2.1 Baseline, before reading any code

```
$ git status --porcelain && git log --oneline -1 && git rev-parse --abbrev-ref HEAD
?? docs/reviews/gate-a-harness-review.md
d5efdc5 Rebuild the Gate A probe against the real ADP schema, and record the pass
main

$ PYTHONPATH=src <python> -m pytest -o addopts="" -q
419 passed, 1 warning in 14.64s
```

Baseline confirmed: **419 passed, 1 warning**. Tree clean apart from one pre-existing
untracked review file that is not mine.

### 2.2 The two claims, attacked

**Claim 1, structurally.** Every production call site of `insert_disposition`:

```
$ grep -rn "insert_disposition" src/ tests/ --include=*.py | grep -v "def insert_disposition"
src/carerelay/service.py:333:        self._store.insert_disposition(disposition, now_utc=now_utc)
src/carerelay/service.py:615:            self._store.insert_disposition(authorised, now_utc=self._clock.now_utc())
```

- Line 333 is `intake`, and it is refused on a second call (`EpisodeAlreadyAssessed`).
- Line 615 is `reassess`, and it fires only when
  `decision.outcome is ReassessmentOutcome.INSERT_DISPOSITION_VERSION`, which requires
  the code to be in `policy.permitted_change_codes` **and** to have a branch in
  `policy.authorised_reassessments`. Both are empty (`demo/fixture.py` line 147 and
  `policy()` line 202).

So no HTTP path can write a version 2 today, and O7 is a guard on a door that is
currently locked for a separate reason (see N2).

**Claim 1, by hostile input.** I tried, over a live server:

| Input | Result |
|---|---|
| `POST /reassessments` `{}` | 200, `outcome: stop_at_human_path`, `disposition_version: null` |
| `POST /reassessments` `{"confirmed_change_code": "chest_pain_now"}` | 200, stop, `reason: outside policy` |
| `POST /reassessments` `{"confirmed_change_code": ""}` | 200, stop, `reason: change code '' is outside policy` |
| `POST /reassessments` `{"confirmed_change_code": "worse"}` **after an escalation** | 200, stop |
| `POST /barriers` with `proposed_route_id: "teleport_clinic"` | 422, `stopped_at: human_path`, `barrier_recorded: true` |
| `POST /escalations` with `human_path: "dr-smith-mobile"` | 422 |
| Second `POST /intake` | 409, "already carries disposition version 1" |

**I could not construct an input where the product guesses.** Every refusal names the
human path and every one leaves the disposition count at 1.

### 2.3 The live run, raw

Server started, exercised and killed in one command, with `APP_DATABASE_URL` pointed at
a real file so I could inspect the rows afterwards.

```
=== 1. POST /api/episodes ===
{"episode_id":"demo-episode-001","persona":"fictional older adult","policy_version":"fixture-provisional-0","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice.","note":"Slice 1 tracer bullet: hardcoded. No disposition is written, no database exists on this path, and the fixture wording is a provisional non-clinical placeholder, authored rather than sourced. Option C was dropped on 1 October 2026; the wording asserts no clinical claim."}
[HTTP 200]

=== 2. POST /intake (confirmed_text) ===
{"episode_id":"demo-episode-001","disposition_version":1,"action_id":"attend_same_day_review","deadline_utc":"2026-09-30T10:00:00+00:00","next_owner_id":"patient","fallback_route_id":"nurse_line","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]

=== 3. POST /barriers (permitted route) ===
{"episode_id":"demo-episode-001","barrier_id":"3dcf112c2b05426ab05b2a60c48678a8","disposition_version":1,"proposed_route_id":"nurse_line","permitted_route_id":"nurse_line","stopped_at_human_path":false,"human_path_route_id":"nurse_line","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]

=== 4. POST /barriers (hallucinated route) ===
{"detail":{"detail":"'teleport_clinic' is not in the permitted set ['fictional_provider', 'nurse_line']","stopped_at":"human_path","barrier_recorded":true}}
[HTTP 422]

=== 5. POST /escalations (permitted) ===
{"episode_id":"demo-episode-001","escalation_id":"2ad7e6970b2c4a7cac59bbb850d004b5","human_path":"nurse_line","outcome":"handed_off","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]

=== 6. POST /escalations (unpermitted) ===
{"detail":"'dr-smith-mobile' is not in the permitted set ['fictional_provider', 'nurse_line']"}
[HTTP 422]

=== 7. POST /reassessments (no code) ===
{"episode_id":"demo-episode-001","outcome":"stop_at_human_path","reason":"no confirmed change code: absence is not a negative finding (I5)","disposition_version":null,"routes_to_human_path":true,"human_path_route_id":"nurse_line","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]

=== 8. POST /reassessments (unknown code) ===
{"episode_id":"demo-episode-001","outcome":"stop_at_human_path","reason":"change code 'chest_pain_now' is outside policy fixture-provisional-0: fail closed to the human path (D7)","disposition_version":null,"routes_to_human_path":true,"human_path_route_id":"nurse_line","simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]

=== 9. GET /api/episodes/{id} (after the escalation) ===
{"episode_id":"demo-episode-001","lines":["Help is not arranged.","You must act now.","Before 6pm today.","If this route fails, call the fictional nurse line."],"simulated":true,"fixture_label":"SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."}
[HTTP 200]
```

### 2.4 Wire payload against the internal record

```
--- dispositions
  cols: ['id','episode_id','version_no','policy_version','action_id','clinical_deadline_utc','next_owner_id','fallback_route_id','source','created_at']
   (1,'demo-episode-001',1,'fixture-provisional-0','attend_same_day_review','2026-09-30T10:00:00+00:00','patient','nurse_line','fixture','2026-09-30T01:00:00+00:00')
--- barriers
  cols: ['id','episode_id','disposition_version','barrier_text','proposed_route_id','permitted_route_id','stopped_at_human_path','recorded_at']
   ('60063afe...','demo-episode-001',1,'cannot get a taxi',None,None,0,'2026-09-30T01:00:00+00:00')
   ('367a9643...','demo-episode-001',1,'no transport','teleport_clinic',None,1,'2026-09-30T01:00:00+00:00')
--- escalations
  cols: ['id','episode_id','human_path','outcome','recorded_at']
   ('6e529405...','demo-episode-001','nurse_line','handed_off','2026-09-30T01:00:00+00:00')
--- triggers on barriers/escalations
   barriers_no_update, barriers_no_delete, escalations_no_update, escalations_no_delete
--- dispositions count after every reassessment: 1
```

The wire matches the record. Specifically:

- The refused barrier **is** persisted with `stopped_at_human_path = 1` and
  `permitted_route_id = NULL`, even though the HTTP response was a 422. The "recorded as
  a stop and then refused" claim is true on disk, not only in the response.
- `human_path_route_id` on the wire equals the disposition's own `fallback_route_id`
  (`nurse_line`), so neither endpoint invents a route.
- Exactly one disposition exists after every reassessment.

### 2.5 Append-only on the two new tables, probed directly

I did not take "a new append-only barriers table" on trust. Against a raw
`sqlite3.connect()` on the live file:

```
recursive_triggers=False  UPDATE: refused (IntegrityError: barriers is append-only: UPDATE is refused)
                          DELETE: refused (IntegrityError: barriers is append-only: DELETE is refused)
                          INSERT OR REPLACE: ACCEPTED   -> barrier_text rewritten to 'MUTATED BY REPLACE'
recursive_triggers=True   UPDATE: refused
                          DELETE: refused
                          INSERT OR REPLACE: refused (IntegrityError: barriers is append-only: DELETE is refused)
```

This is **O1's documented, scoped guarantee, not a new defect.** `state.py` lines 10 to
26 state the scope exactly ("any connection this module opens" versus "any other
connection"), and `test_every_table_refuses_replace` is parametrized over
`state.APPEND_ONLY_TABLES`, which now includes `barriers` and `escalations`, so both new
tables are covered on the store's own connection. I reproduced the open half myself to
confirm the claim in `00-status.md` is scoped rather than absolute. See N3.

### 2.6 Writing conventions

```
$ git diff -U0 ff22ed3 f95cea4   (the six Slice 5 commits)
added lines: 1487 | added lines containing U+2014: 0
```

**Zero em dashes in the slice's added lines.** See the disclosure in section 7 about the
pasted wire payloads above.

### 2.7 Tree state before and after

| Check | Before | After |
|---|---|---|
| `git status --porcelain` | `?? docs/reviews/gate-a-harness-review.md` | same, plus my two untracked files |
| `git diff --stat` | empty | empty |
| Full suite | 419 passed, 1 warning | 419 passed, 1 warning |
| `spike/.mutation_backups/` | absent | deleted after the restores |

---

## 3. Mutations

Harness: `spike/review_mutate.py` (untracked). It reads and writes in binary, so no
line-ending damage is possible, and it asserts a needle count of exactly 1 before
patching. Every mutation was followed by the **full suite**, not only the targeted test,
so a red set wider than intended would show.

Baseline SHA-256 (first 16 hex) of the three files I touched:

| File | Baseline | After final restore |
|---|---|---|
| `src/carerelay/domain/rules.py` | `098dd314e4359336` | `098dd314e4359336` |
| `src/carerelay/state.py` | `4308e1cf94166a9c` | `4308e1cf94166a9c` |
| `src/carerelay/service.py` | `f2343e3f4a313be2` | `f2343e3f4a313be2` |

All three identical. `loneLF = 0` on each at every checkpoint, so CRLF survived.

| # | Mutation | Targeted test(s) | Observed | Restore |
|---|---|---|---|---|
| **M1** | **F6.** `rules.py`, `_action_owner`: `if snapshot.escalation_id is None:` to `if True:`. An escalation no longer moves the owner, and the "names no human path" branch becomes dead. | `test_the_handoff_moves_the_acting_party`, `test_an_escalation_before_the_deadline_is_escalated_to_human`, `test_an_escalation_with_no_human_path_is_refused`, `test_the_escalation_moves_the_owner_in_the_derived_state` | **4 RED, 415 green.** Exactly the four F6 tests, and nothing else. | verified, `098dd314e4359336` |
| **M2** | **O7.** `state.py`, `insert_disposition`: `if disposition.clinical_deadline_utc <= previous_deadline:` to `if False:`. | `test_an_earlier_deadline_is_refused`, `test_an_equal_deadline_is_refused` | **2 RED, 417 green.** Exactly the two refusal tests. The later-deadline control, `test_a_later_deadline_is_accepted`, stayed green, so the check refuses the defect and not the feature. | verified, `4308e1cf94166a9c` |
| **M3a** | **K2, broad.** `service.py`, `intake`: a `self._coordinator.extract_plan(...)` call injected before the complaint check, so the plan can only be issued if read-back machinery answers. | the three `TestPlanPrecedesReadBack` tests | **5 RED, 414 green.** The three K2 tests **plus** `TestCoordinatorUnavailable::test_the_flow_stops_with_a_text_fallback_and_scored_false` and `::test_the_fallback_is_never_a_200_with_empty_mismatches`. **Shared catch.** | verified, `f2343e3f4a313be2` |
| **M3b** | **K2, narrow.** `service.py`, `_score`: the `extract_plan` call wrapped so that on failure it inserts a version 2 with `clinical_deadline_utc + 1 hour` and then re-raises. The deadline moves instead of abstaining. | `test_a_coordinator_failure_cannot_move_the_deadline` | **1 RED, 418 green.** Exactly the intended test, and nothing else. | verified, `f2343e3f4a313be2` |
| **M4** | **K2, ordering half.** `service.py`, `intake`: a coordinator call injected before the complaint check and wrapped in `except Exception: pass`, so the plan is still issued and only the call itself is observable. | `test_intake_never_reaches_the_coordinator` (added during this pass) | **1 RED, 419 green.** Exactly the intended test, and nothing else. **This closes S2.** | verified, `f2343e3f4a313be2` |

**What M3a means, stated plainly.** `TestCoordinatorUnavailable` runs its intake through
a dead coordinator too, so *any* defect that makes plan issuance depend on the
coordinator breaks both classes at once. There is no narrower defect available: I looked
for one and could not construct it. By `AGENTS.md` section 6 ("treat a fault two checks
can both catch as proof of neither"), the two K2 assertions that the plan is **issued**
and **renderable** before the coordinator is reached are therefore **not independently
mutation-proven**. The third assertion, that a coordinator failure cannot move the
deadline, **is** independently proven by M3b.

The underlying behaviour was also verifiable by inspection: `service.intake` never
touched `self._coordinator`, and `patient_lines` is a pure domain function. So this
was an evidence gap, not a code defect.

**Closed during this pass.** M4 is the mutation that M3a could not be: because the
injected call is tolerated, the plan is still issued, so `TestCoordinatorUnavailable`
and the other two K2 tests all stay green and only the call count changes. The new
assertion `test_intake_never_reaches_the_coordinator` fails alone, 1 RED in 420.

---

## 4. What I could not verify

| Item | Why not |
|---|---|
| **K2's ordering half, independently.** See section 3, M3a. Not falsifiable alone in this codebase. | No narrower mutation exists. |
| **That B3's intake rule is clinically right.** | Out of scope by instruction. It still needs a clinical reviewer. |
| **That Gate A closes the platform-integration question.** | Out of scope by instruction. Gate A proves the transport; it does not prove CareRelay's own code uses the platform. |
| **`/ledger`.** It returns 404. | The judge ledger is Slice 12's, not Slice 5's. Not a Slice 5 finding. |
| **Restart persistence of the new tables.** | The local demo runs on `:memory:` (`api.py` line 94). The mounted-disk proof is Slice 7's. |
| **That the two new tables survive a deploy with triggers intact.** | Same reason. |

---

## 5. Findings

### S1. [verified] should-fix. CLOSED 2 October 2026. `00-status.md` stated a falsehood about the slice's Git state

`00-status.md` line 144 says Slice 5 was "fast-forwarded into `main` and `main` pushed
to `origin` at `f131ef2`". Line 187, in the slice checklist, says Slice 5 is "**not
merged into `main` and not pushed**". Both cannot be true.

```
$ git rev-parse origin/main   -> d5efdc5409c3a76d6c583c758d82825ad5ee5ea5
$ git rev-parse main          -> d5efdc5409c3a76d6c583c758d82825ad5ee5ea5
$ git merge-base --is-ancestor f95cea4 origin/main  -> YES
$ git branch --list slice-5   -> f131ef28332848bc63b7dad55312c454d29adea8
```

`origin/main` and `main` are the same commit, and `f95cea4`, the tip commit of Slice 5,
is an ancestor of it. **Slice 5 is merged and pushed. Line 187 is false.**

This matters because `00-status.md` is the only authority for slice state, and this is a
fresh-session file. A next session reading that row would believe Slice 5's work is
unpublished.

**Closed 2 October 2026, on the user's instruction to do the fixes.** The row now states
that the slice was fast-forwarded into `main` and pushed, names the verification
(`origin/main` and `main` both at `d5efdc5`, `f95cea4` an ancestor of it) and records that
the earlier line was false and is corrected. No gate document was touched, so no gate
reopened.

### S2. [verified] should-fix. CLOSED 2 October 2026. Two of K2's three assertions were not independently proven

Full detail in section 3. `04-slices.md` names K2 as one of Slice 5's two required
tests, and the slice's goal is "the urgent path is provably first". One third of that is
currently backed by a unique mutation; two thirds are backed only jointly with
`TestCoordinatorUnavailable`.

**Closed 2 October 2026.** `tests/test_service.py` gained
`test_intake_never_reaches_the_coordinator`, inside `TestPlanPrecedesReadBack`. It builds
the service with the existing `StubCoordinator`, which answers rather than raising, runs
intake, and asserts the coordinator's call list is empty. Because the stub answers, the
plan is issued either way, so `TestCoordinatorUnavailable` and the other two K2 tests
cannot move. Mutation M4 turns exactly this one test RED: 1 failed, 419 passed.

K2 is now fully backed by unique mutations: M3b for the deadline, M4 for the ordering.
Suite is 420 passed, 1 warning.

### N1. [verified] note. F6's rendering half is live-visible, exactly as deferred

After `POST /escalations` with `nurse_line`, `GET /api/episodes/{id}` still returns
line 2 as "You must act now." while the ledger's owner is `nurse_line`. I observed this
in the live run above, response 9.

The cause is precisely as recorded: `patient_lines` line 538 reads
`disposition.next_owner_id`, not `closure.action_owner_id`, so even the derived path
contradicts F6. It is latent today only because `GET /api/episodes/{id}` renders the
hardcoded `demo_lines()` and no HTTP route renders derived lines. **Not authored here,
per instruction.** Anchored to Slice 10.

### N2. [verified] note. O7 is real but currently unreachable from any HTTP path

`insert_disposition` version 2 requires `reassessment_decision` to return
`INSERT_DISPOSITION_VERSION`, which requires a non-empty `permitted_change_codes`. It is
empty by design. So O7 is a genuine store invariant with genuine tests, and no product
path can violate it or exercise it until a reviewer authorises a branch.

That is not a defect, but the honest sentence is "O7 is closed at the store layer and
proven there", not "the product cannot move a deadline backwards", because the product
cannot move a deadline at all yet.

### N3. [verified] note. The two new tables inherit O1's scoped, not absolute, guarantee

`INSERT OR REPLACE` rewrites a `barriers` row from any connection that has not set
`PRAGMA recursive_triggers = ON`. I reproduced it. `UPDATE` and `DELETE` are refused
from any connection. Both new tables are inside the parametrized
`test_every_table_refuses_replace`, and `state.py` lines 10 to 26 already state this
scope honestly. Nothing to fix; the claim should keep being stated with its scope.

### N4. [verified] note. `rules.validate_change` is dead in production

Defined at `rules.py` line 171 and unit-tested at `test_domain.py` lines 593 to 609, but
called by no production path. `reassessment_decision` does its own
`classified_change not in policy.permitted_change_codes` check instead. Harmless, and
the behaviour is identical, but it is a contracted function that nothing contracts with.

### N5. [verified] note. The classification step of the reassessment call stack is not wired

`03-program-design.md` section 4 says: "Confirmed symptom-change text to coordinator
returns one closed-vocabulary value, domain validates it." `CoordinatorPort.classify_change`
is declared (`coordinator.py`) and called nowhere. `POST /reassessments` accepts
`confirmed_change_code` directly from the caller.

This is consistent with `record_barrier`'s own docstring, which defers the coordinator
proposal to Slice 6, and it is moot today because every input stops regardless. It is
still a partial delivery of the section 4 row and should be recorded rather than
forgotten.

### N6. [verified] note. The 422 and 200 barrier payloads name the same concept differently

The 200 body carries `stopped_at_human_path`. The 422 body carries `stopped_at:
"human_path"` and `barrier_recorded: true`. A frontend has to know two shapes for one
fact. Cosmetic, but it is a wire-shape inconsistency and it is cheap to align at the
next API touch.

### Not raised, per instruction

The fixture wording as an authored non-clinical placeholder. `PERMITTED_CHANGE_CODES`
being empty by design. `04-slices.md`'s stale Slice 5 gate line. Gate A not closing the
platform-integration question. B3.

---

## 6. What this review does not prove

- **It does not prove clinical safety.** Nothing here is reviewed clinical content, and
  no reviewer exists.
- **It does not prove the fixture is fit to show a participant.** `demo/fixture.py` says
  in its own docstring that nothing in it may be shown to a participant. I did not test
  that boundary and it remains binding.
- **It does not prove K2's ordering property independently.** See S2.
- **It does not prove the abstention path survives coordinator wiring.** Slice 6 adds the
  real coordinator and a `propose_route` call into `record_barrier`. Every mutation here
  was against the current code, where no system route is ever proposed.
- **It does not prove persistence.** The live run wrote to a file, but restart and
  redeploy survival is Slice 7's, and the local demo is in-memory.
- **Mutation testing proves the tests can catch the defects I chose.** It says nothing
  about defects I did not think of. Four mutations is not exhaustive.
- **It does not authorise anything.** No gate, no commit, no push.

---

## 7. The Check: the fixture wording and the provenance record

`04-slices.md` sets Slice 5's Check as "the user reads the fixture wording and the
provenance record". Both are reproduced here verbatim so the read can happen in one
place. **The Check completes when Jaydon confirms he has read them.**

### 7.1 The fixture wording

`fixtures/scripted_episode.json`, in full:

```json
{
  "fixture_label": "SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice.",
  "policy_version": "fixture-provisional-0",
  "episode_id": "demo-episode-001",
  "persona": "fictional older adult",
  "action_id": "attend_same_day_review",
  "action_text": "Go to the fictional provider's same-day review.",
  "deadline_display": "6pm today",
  "next_owner_id": "patient",
  "next_owner_text": "you",
  "fallback_route_id": "nurse_line",
  "fallback_route_text": "the fictional nurse line",
  "note": "PROVISIONAL non-clinical placeholder wording, authored rather than sourced. Option C was dropped on 1 October 2026: the source check cleared no source, because MOH clause 11 and HealthHub clause 12.1 both require prior written permission and the UK Open Government Licence route fails Singapore applicability. Option C also contradicted Option A, because a fixture built from fictional entities cannot be quoted verbatim from any published guidance. This wording names no symptom, urgency, threshold or real facility and asserts no clinical claim. It is a research demonstration and is not clinical advice. Slice 1 hardcoded these values; Slice 2 moved the same shape into domain models."
}
```

The four patient lines, captured live from `GET /api/episodes/demo-episode-001`:

```
"lines":["Help is not arranged.","You must act now.","Before 6pm today.","If this route fails, call the fictional nurse line."]
```

What is absent is the point. There is no symptom, no urgency, no threshold and no real
facility. The two entities are "the fictional provider" and "the fictional nurse line",
and the one complaint the fixture is bound to is "help sorting out my appointment".

### 7.2 The provenance record

Written to `policy_versions` at intake and read back from the live database:

```
version      : fixture-provisional-0
content      : provisional fixture policy fixture-provisional-0
provenance   : PROVISIONAL: non-clinical placeholder, authored rather than sourced. Option C was dropped on 1 October 2026 after the source check cleared no source; the wording names no symptom, urgency, threshold or real facility and asserts no clinical claim (03-program-design.md 6.2).
approved_by  : None
created_at   : 2026-09-30T01:00:00+00:00
```

`approved_by` is NULL. That is the honest state and it is the one fact worth reading
twice: **no reviewer has authorised anything in this fixture.** The honesty rests on the
absence of a clinical claim, not on the presence of a citation.

## 8. Disclosure: em dashes in this file

`AGENTS.md` section 6 bans em dashes in new writing.

- **My own prose in this file: 0 U+2014.** Added lines across every file I changed today: 50, containing 0 U+2014.
- **Eight quoted lines carry U+2014, all inside `"fixture_label"`.** Seven are the pasted
  wire payloads in section 2.3; the eighth is that same field inside the verbatim
  `fixtures/scripted_episode.json` in section 7.1. That string is
  `fixture.FIXTURE_LABEL`, pre-existing approved fixture text that ships on every
  response. I reproduced it verbatim because editing quoted evidence would falsify it.
  The same disclosure pattern is used by `submission/usage-proof.md` for the imported
  session logs.
- The slice's own added lines carry **0** U+2014 across 1487 lines (section 2.6).

## 9. Artefacts

| Path | State |
|---|---|
| `docs/reviews/slice5-live-check.md` | this review, untracked, not committed |
| `spike/review_mutate.py` | the mutation harness, untracked, not committed |
| `docs/plans/urgent-advice-accessibility/00-status.md` | **modified** (S1 correction and the Slice 5 live-check section), not committed |
| `tests/test_service.py` | **modified** (the new K2 assertion), not committed |
| `docs/reviews/gate-a-harness-review.md` | pre-existing untracked, not mine |

No gate document was edited, so no gate reopened. Nothing is committed or pushed.
