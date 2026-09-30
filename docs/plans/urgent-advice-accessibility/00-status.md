# Status: CareRelay urgent-advice accessibility

- Gate 1 — Product: **APPROVED** (25 September 2026; reopened and re-amended the same day — see the reopening section below)
- Gate 2 — Architecture: **APPROVED** (25 September 2026, revision 2)
- Gate 3: Program Design, **APPROVED** (26 September 2026)
- Gate 4 — Slice plan: **APPROVED** (28 September 2026)

## Slices

**Gate 4 is approved. Slices proceed one at a time, each ending with a "continue, or re-steer?" check.** Slice state below is the only authority.

- [ ] Slice 0 — kill tests (**PASS** 28 Sep) + Option C source (**open**, blocks Slice 5 only)
- [x] **Slice 1 — COMPLETE 28 Sep.** Tracer bullet runs; 11 tests pass; curl-verified live
- [ ] Slice 2 — pure domain core + enforcing boundary ← **next**
- [ ] Slice 3 — state, append-only, Closure Contract invariants
- [ ] Slice 4 — PlanBack end to end, hint ladder, bounded repair
- [ ] Slice 5 — judged fixture + abstention path (**blocked on the Option C source**)
- [ ] Slice 6 — action path, simulated provider, platform call + Gate A decision
- [ ] Slice 7 — baseline instrument: the external card (C1, parallel)
- [ ] Slice 8 — Gate B: run the comparison (**kill test**)
- [ ] Slice 9 — Closure Contract in full (starts only after the kill test)
- [ ] Slice 10 — fault harness + seven sequences
- [ ] Slice 11 — judge ledger + usage proof
- [ ] Slice 12 — submission assets

## Gate 4 approval — 28 September 2026
The user approved **Gate 4 (Slice plan)** on 28 September 2026 with the instruction **"continue"**, following the approval question in this file. `04-slices.md` now records the approval.

**Approval authorises implementation code, slice by slice, in the planned order.** It does **not** authorise installs beyond the declared test dependencies, credentials, recruitment, external calls, deployment, or a push. Each slice still stops for the user's "continue, or re-steer?" before the next begins.

**Two sub-questions were open at drafting. Both resolved at approval, under the recommendation given:**

| # | Question | Resolution |
|---|---|---|
| 1 | **ADR-0007 — which layer owns canonicalisation?** | **Reading A accepted.** Canonicalisation lives in `domain`; the coordinator returns raw spans. ADR-0007 is now `accepted`, and the Gate 3 `compare_plan` signature is amended. `ExtractedPlan` carries **both** the raw span and `uncertain_fields`. |
| 2 | **The Option C source.** | **Scheduling only.** Still unselected, licensing still unchecked. Blocks Slice 5 and nothing earlier. If no source clears by 2 October → Option B; clinical wording is **not** authored to unblock the schedule. |

**If either resolution is wrong, say so** — ADR-0007 affects Slices 2 and 4, the source affects Slice 5.

## Slice 1 complete — 28 September 2026

**Tracer bullet runs end to end.** `POST /api/episodes` → `GET /api/episodes/{id}` → the four-line patient page, served from `127.0.0.1` with no database, no domain layer and no coordinator.

| Evidence | Result |
|---|---|
| `pytest tests/` | **11 passed** |
| Live `curl` on `127.0.0.1:8137` | health, create, projection and 404 all correct |
| Missing route → 404 | confirmed |
| Simulated label inside the serialized projection | confirmed (D11) |
| No `http-equiv="refresh"`, no `<script>`, no CSS animation/transition | confirmed (C8 — no timer anywhere) |

**Defect found and fixed during this slice — a real one.** The first live render produced **"You or you must act now."** on line 2. `PLAN.md` §6.1, `02-architecture.md` §7 and `01-product.md` all render line 2 as "You or *[named person]* must act now."; with a patient owner that sentence is malformed. **The test suite did not catch it — inspection of the running app did**, which is exactly why Gate 4's standing rule is "run it and show the result" rather than "the tests pass".

- **Fix applied:** line 2 now reads "Myself must act now.", with `OWNER_DISPLAY` as a named-owner constant.
- **Regression test added:** `test_line_two_does_not_render_a_doubled_owner`.
- **Flagged, not silently absorbed:** this **diverges from three approved documents.** The correction belongs in those documents at the next Gate 1 touch. Slice 9 must implement whichever form they then carry — the Slice 1 literal is not the authority.

**Files created:** `pyproject.toml`, `src/carerelay/__init__.py`, `src/carerelay/api.py`, `src/carerelay/demo/fixture.py`, `src/carerelay/demo/__init__.py`, `src/carerelay/static/style.css`, `fixtures/scripted_episode.json`, `tests/test_api.py`.

**Not yet done, and deliberately:** no database (Slice 3), no disposition is written on episode creation (`02-architecture.md` §3.1 — confirmed by `test_create_episode_returns_an_id_and_no_disposition`), and the fixture wording is still a **provisional placeholder** pending the Option C source check.

## Gate 4 draft — 28 September 2026

`04-slices.md` is written and **awaiting explicit approval**. Drafting it authorises no code. Thirteen slices, full Gate 3 scope, with constraint C1 satisfied: the external card (Slice 7) completes before the Closure Contract build (Slice 9).

**User instructions at drafting (28 September 2026):**

| # | Instruction | Consequence |
|---|---|---|
| 1 | Re-verify Gate A before planning against it | Gate A re-checked. Findings below. |
| 2 | **Keep the full scope** — do not cut to fit the schedule | No capability cut. The schedule risk is recorded as R1 in `04-slices.md` §6/§5 rather than resolved by cutting. |

**Gate A re-verification, 28 September 2026.** No `WORKBUDDY_API_KEY` or `WORKBUDDY_AGENT_ID` in the environment; no `.env`; no `workbuddy` or `codebuddy` Python package installed. **On that evidence the platform path is [unknown]-to-unavailable.** Gate A remains **overdue** since 26 September and has still not run. Slice 6 therefore plans the labelled local-simulation fallback as the default and wires the platform path only if credentials appear. The pre-recorded Gate 2 §3.3 reversal applies if Gate A has not passed by 11 October.

**Two results already in hand, before any product code:**

- **K1 and K2 PASS** — `spike/tests/test_kill_conditions.py`, 15 tests, 0 failures, Python 3.13.14, including four defect-injection tests confirming the assertions can fail. This is a **deterministic-layer spike result**, not an implementation result.
- **Slice 1's environment check passes** — the FastAPI stack installs and imports into an isolated venv; the intermittent AppControl block on stdlib venv creation did not fire.

**Open items at drafting:**

- **The Option C source is not selected.** Licensing and Singapore applicability unchecked. This blocks Slice 5 (the judged fixture) and nothing earlier. If no source can be cleared by 2 October, escalate to Option B — do not author clinical wording to unblock the schedule.
- **ADR-0007 is `proposed`.** It amends the Gate 3 `compare_plan` signature so canonicalisation lives in `domain` (Reading A). It affects what K1 can claim and needs acknowledgment at Gate 4 approval.
- **The schedule does not fit.** 102–169 h against 144 h available, solo, 18 days. Recorded as R1.

**Gate 4 approval question:** Approve Gate 4 as drafted, or what should change?

## Decision records

`docs/adr/` now holds eight Architecture Decision Records capturing the choices that outlive this feature — ADR-0001 to ADR-0008 — plus an index at `docs/adr/README.md`. They summarise decisions already approved at Gates 1–3 and the Gate 4 drafting instructions. **The gate documents remain authoritative**; where an ADR disagrees with them, the gate document wins and the ADR is corrected.


## Gate 3 approval — 26 September 2026

The user approved **Gate 3 (Program Design)** on 26 September 2026, on the same day it was drafted, with two amendments made at approval.

Approval covers: the planned file footprint, the type and method contracts, the call stacks, the failure-capable test plan, the callback dedupe representation, the Gate B protocol, and the 90–150 h build plus 20–35 h baseline estimate.

**Gate 3 approval authorises drafting Gate 4 only.** It does **not** authorise code, installs, credentials, recruitment, external calls, or a push. Gate 4 remains pending and no code may be written before Gate 4 is approved.

### Amendments made at approval

| # | Amendment | Where |
|---|---|---|
| 1 | **§6.1 added — the two reviewer-free kill conditions.** Two of the three PlanBack cut conditions (false mismatch on correct restatements; emergency guidance delayed by read-back) are pure system properties. They are lifted out of the stalled study and execute **before any participant work**, requiring no clinical review and no Gate A | `03-program-design.md` §6.1, §5 |
| 2 | **§6.2 rewritten — Option A + C selected.** The comparator is now **non-clinical** (Option A) and the fixture is **sourced verbatim from attributable published guidance** (Option C). The original text said the study "cannot run as specified"; that dependency is resolved by decision | `03-program-design.md` §6.2, §8.3 |

### Gate 2 backtrack — D6 comparator material

**Option A changes D6's comparator content, so Gate 2 D6 is formally backtracked.** The decision itself is unchanged — external artefact, between-subjects, scripted post-failure question, pre-registered cut rule. What changes is the *material*: it now carries no symptom, urgency or disposition content.

| | Before | After |
|---|---|---|
| Comparator content | Bilingual clinical card with the fixture wording | Content-neutral instruction task, same shape, **no clinical content** |
| Review required to run | Clinical + native-speaker + bilingual clinical | **None** — no guidance is administered to anyone |
| What the result supports | Understanding of care advice | Understanding of the **mechanism** only |

**Consequence the submission must state:** the study measures whether read-back plus truthful status changes comprehension, burden and false-completion belief. It does **not** validate clinical advice. Impact & Relevance loses weight accordingly, and no claim may imply otherwise.

### Open at approval

- **Source selection for Option C.** No source chosen; licensing and Singapore applicability unchecked. **This precedes use** and is a Gate 4 task. Note `CareRelay.md` records that wholesale copying of licensed Schmitt–Thompson protocols is out of scope.
- **Option B rejected but not closed.** A reviewer remains valuable for clinical-credibility language, but no longer blocks the study. Not chased on a clock.
- The two §6.1 kill tests have **not been written yet** and must precede participant work.

## Gate 3 draft: 26 September 2026 (superseded by the approval above)

`03-program-design.md` is now **APPROVED** (see the approval record above). It pins planned files, types, call stacks, failure-capable tests, the callback dedupe representation, and a 90–150 person-hour build estimate plus 20–35 hours for the baseline. Gate 4 remains pending and no implementation is authorised. Gate A, participant recruitment and the participant comparison remain unproved.

**The clinical-review blocker has a decision paper: `clinical-review-blocker.md` (26 September 2026).** Headline finding: the hackathon does **not** require a clinical reviewer, and the blocker was narrower than `03-program-design.md` §6 implied — the build, the fixture, the fault harness and the ledger were **not** blocked. Two of the three PlanBack kill conditions (false-mismatch and delayed-emergency-guidance) are **testable with no participants and no reviewer at all**; they are now lifted out of the stalled study as Gate 3 §6.1 and run first. **The user selected Option A + C on 26 September 2026**, which removed the blocking dependency and triggered the Gate 2 D6 backtrack recorded above. Option B (one reviewer) was not chased on a clock but is not closed.

The `02-architecture.md` header previously read "Not approved". Fixed 26 September 2026 — it now records the Gate 2 approval and points to this file for authority.

## Gate 2 approval — 25 September 2026

The user approved **Gate 2 (Architecture) revision 2** on 25 September 2026, following an independent round-2 adversarial review whose verdict was APPROVE WITH CHANGES and whose eleven blocking items were all applied or explicitly resolved.

Approval covers: D1–D12, the module and trust boundaries, the pinned tool-execution path (§3.3), the UI API and the three-tool MCP surface, the attempt/transition/callback schema (§4.1), the three flows, D11 evidence provenance and D12 sticky expiry, the non-functional surfaces (§8), the pre-registered baseline study (§9), the amended expired-screen rendering with its copy rules (§7), and the change log (§11).

**Gate 2 approval authorises the Gate A access spike only.** It does **not** authorise implementation code. Gates 3 and 4 remain pending, and no code may be written before Gate 4.

### Carried into Gate 3

- **A real effort estimate.** The round-2 review's 90–150 h (plus 20–35 h for the baseline) is unverified. The user has accepted it as achievable; Gate 3 must still produce its own estimate.
- **Gate 4 must sequence the baseline comparison (Gate B) before the Closure Contract build.** `PLAN.md` §7 currently schedules the sessions *after* the state machine — wrong order.
- **The Gate A spike is due 26 September.** If it fails, §3.3's fallback applies and the platform-advantage claim is weakened and stated as weakened.
- **D9 (scheduled reassessment) is not deliverable.** The P1 load-bearing answer is "execution substrate". `DESIGN_PRINCIPLES.md` §8's "monitored episode that cannot lie" is not delivered and must not be implied in the submission.

## Gate 1 reopening — 25 September 2026 (approved)

Gate 1 was **deliberately reopened** after its first approval to resolve the H2 accessibility hazard the round-2 adversarial review identified, and to approve the expired-screen wording. Both changes were approved by the user the same day.

| Change | Decision | Files |
|---|---|---|
| **H2 no longer has a timer** | The plan card at H2 **stays on screen until the patient hides it**. No countdown, no auto-dismiss, no auto-advance anywhere in the product. `dwell_seconds` is recorded for the judge ledger and never shown to the patient. Rationale: a five-second rule is unreadable for older adults, unusable with a screen reader, and un-extendable — it penalised the exact population the product exists for | `PLAN.md` §5.2 + new §5.2.1, `01-product.md`, `mockups/02` |
| **Expired-screen wording** | Approved with **softer, human-centred wording**. The first draft ("The time to go was [deadline]. It has passed." / "Call [route] now") was rejected as too blunt. Final rendering plus five copy rules: no reproach, no alarm, no false comfort, a named route, deadline stays visible | `02-architecture.md` §7 |

**Gate 1 remains APPROVED** with these amendments. Both changes were made openly in the documents, not silently at Gate 3.

## Gate 1 approval — 25 September 2026 (original)

The user explicitly approved Gate 1 on 25 September 2026. This covers the Gate 1
scope below: the reframe, PlanBack, the recall hint ladder, the Closure Contract,
the two-axis state model, the design principles and the five HTML wireframes.

Approval of the product specification does **not** authorise implementation.
Gates 2–4 remain pending and no code may be written until Gate 2 is approved.

### Carried forward as explicit, unresolved Gate 1 risks

These were surfaced by the adversarial review, accepted rather than resolved, and
must be treated as live inputs to Gate 2:

- **Mandatory organiser-usage proof is still absent.** Without it the project does
  not proceed to scoring.
- **No qualified clinical reviewer and no authorised protocol.** The prototype must
  remain a labelled research demonstration using scripted fixtures.
- **The load-bearing assumption is untested:** that a fixed bilingual card does not
  perform equally well. It should be tested before the mechanisms are built.
- **Neither mechanism requires WorkBuddy.** WorkBuddy's genuine dependency is the
  coordinator, the real tool call, its real failure event, and session resume.
- **Mandarin voice is a gated TRTC spike only.** No account access or clinical
  accuracy has been demonstrated.

## Gate 1 scope as of 21 September 2026

Gate 1 was opened with a broader product definition. It has since been narrowed by the independent adversarial review and expanded by two new mechanisms. Both changes were approved on 25 September 2026.

| Change | Where |
|---|---|
| Reframe: closed-loop confirmation of urgent advice, not the ledger | `02-adversarial-review.md` |
| PlanBack — read-back with deterministic critical-field comparison and bounded repair | `03-planback-closure-contract.md`, `PLAN.md` §5.1 |
| Recall hint ladder (H0–H3) with the level always recorded | `PLAN.md` §5.2, `01-product.md`, `mockups/02` |
| Closure Contract — two independent axes and five fault invariants | `03-planback-closure-contract.md`, `PLAN.md` §6.1 |
| Corrected single-ladder state model to two axes | `PLAN.md` §6 |
| Patient sees four lines; the ledger is judge-facing | `PLAN.md` §6.1, `mockups/03` |
| Four design principles adopted; load-bearing audit fails the current scope | `docs/DESIGN_PRINCIPLES.md` |

## Files in this folder

The skill's canonical gate filenames are reserved for Gates 2–4. Two supporting documents already occupy those numbers, so a fresh session should read the map below rather than assume by number.

| File | Kind | Purpose |
|---|---|---|
| `00-status.md` | state | this file |
| `01-product.md` | **Gate 1 doc** | problem, success metric, announcement, product rules, screens |
| `02-adversarial-review.md` | supporting note | independent review, 21 Sep — verdict, competitors, scores, kill dates |
| `03-planback-closure-contract.md` | supporting note | specification and feasibility for PlanBack and the Closure Contract |
| `02-architecture.md` | **Gate 2 doc** | **approved revision 2** (25 Sep), D1–D12, pinned tool path, attempt-transition schema, external between-subjects baseline, non-functional surfaces, change log |
| `gate2-review-prompt-thorough.md` | supporting note | the review prompt handed to the independent reviewer |
| `gate2-adversarial-review-thorough.md` | supporting note | independent round-2 review — APPROVE WITH CHANGES, three blocking defects |
| `clinical-review-blocker.md` | supporting note | decision paper, 26 Sep — what the reviewer blocker actually blocks, and three routes through |
| `03-program-design.md` | **Gate 3 doc** | **approved 26 September 2026** — files, types, call stacks, failure-capable tests, effort |
| `04-slices.md` | **Gate 4 doc** | **APPROVED 28 September 2026** — 13 slices, full scope, Gate A re-verification, R1 schedule risk |
| `clinical-review-blocker.md` | supporting note | decision paper, 26 Sep — what the reviewer blocker actually blocks, and three routes through |
| `../../adr/` | decision records | `docs/adr/` — ADR-0001 to ADR-0008 plus index; decisions that outlive this feature |
| `mockups/` | Gate 1 assets | five plain-HTML screens, throwaway by design |

## Notes for a fresh session

- Product identity: CareRelay must not stop at advice; it checks understanding and feasibility, preserves the clinical deadline, and reports failed or unconfirmed handoffs truthfully.
- **PlanBack:** the patient restates the plan; **code, not a model**, compares `action`, `deadline` and `next_owner`; a mismatch is repaired field by field, bounded to two rounds, then a human path. The model only extracts fields.
- **Hint ladder:** H0 unaided → H1 structural slots → H2 card shown then hidden → H3 plan given. The level used is **always recorded**, because a hint containing the answer turns a comprehension check into a reading test.
- **The ladder fades.** A new plan starts at H1; an unaided success lowers the starting level next time; a failure restores it; changes happen on trends, not single rounds; fading is invisible to the patient. This is **vanishing cues with errorless learning and spaced retrieval** — an established cognitive-rehabilitation technique, cited as prior art.
- **Cognitive claims are prohibited.** No cognitive improvement, “keep your mind sharp,” dementia prevention, screening, risk score or diagnostic output — in the product, submission, video or pitch. Meta-analyses find no far transfer from cognitive training; the FTC fined Lumosity $2 million in 2016 for exactly this claim. The scaffold improves retention of *this plan* and nothing more.
- **Language rule:** never “cognitive rot,” “brain training” or “use it or lose it” in anything user-facing.
- **Longitudinal cognitive signal is research, not a demo claim.** Recorded in `PLAN.md` §5.3 as an out-of-scope hypothesis so the ambition is not lost; it is not presented in the submission.
- **Closure Contract:** execution status and evidence status are two independent axes; the clinical deadline is immutable to operational retries; five invariants are test cases, not slogans.
- **The load-bearing untested assumption:** that a fixed bilingual card plus a direct booking link plus a NurseFirst fallback does *not* perform equally. This is the primary kill test and must run first.
- **Honest dependency boundary:** PlanBack and the Closure Contract are application logic and do not require WorkBuddy. WorkBuddy's genuine contribution is the coordinator, the real tool call, its real failure event and session resume.
- **Open question from `docs/DESIGN_PRINCIPLES.md` (re-verified 22 Sep, resolved 25 Sep):** the P1 load-bearing answer is **"execution substrate"**. The scheduled-reassessment module (D9 in the Gate 2 draft) was dropped after the round-2 adversarial review found it unbuildable as specified — no scenario, no ingress endpoint, no estimate. `DESIGN_PRINCIPLES.md` §8's "monitored episode that cannot lie" is **not** delivered. The submission must state this rather than imply a capability that is switched off.
- Mandarin and voice are accessibility modes. English text remains the auditable reference until bilingual clinical content is reviewed.
- Provisional persona: Mei, 72, Mandarin-preferring, with remote daughter support. The respiratory-symptom recommendation remains an injected fixture until clinical review.
- **No asset may name a real healthcare facility.** The fixture provider is fictional and labelled.
- No implementation code may be written before Gate 4 approval. **Gate 4 was approved 28 September 2026; implementation is now authorised slice by slice.**
- **Gate 4 approved 28 Sep** with the instruction "continue". Full scope was kept on the user's explicit instruction; the schedule risk is recorded as R1 in `04-slices.md`, not resolved by cutting. Constraint C1 is honoured: the external card (Slice 7) completes before the Closure Contract build (Slice 9), with the Gate B kill test (Slice 8) between them.
- **ADR-0007 accepted 28 Sep** — canonicalisation lives in `domain` (Reading A). The Gate 3 `compare_plan` signature is amended, and `ExtractedPlan` carries both the raw span and `uncertain_fields`.
- **Gate A has still not run** and is now more than a day overdue. Re-verified 28 Sep: no credentials, no `.env`, no SDK package. Plan for the labelled `local-sim` fallback; take the platform path only if access appears.
- **K1 and K2 pass** (spike, 15/15). Deterministic layer only, and dependent on Reading A (ADR-0007).
- **ADR-0007 is proposed, not accepted** — it amends the approved Gate 3 `compare_plan` signature. Needs acknowledgment at Gate 4 approval or an explicit instruction to keep the original signature and accept a weaker K1 claim.
- Gate 2 draft (`02-architecture.md` revision 2) pins D1–D12: Python+FastAPI default (reversible only before the first domain-code commit), pure domain core, append-only attempt transitions, derived closure with sticky expiry, external between-subjects baseline, deterministic abstention with a closed vocabulary, **D9 dropped**, voice deferred and isolated. **The Gate A access spike is due 26 Sep** with a pre-recorded fallback decision.
- **Two items that needed a user decision are now both resolved** (25 Sep):
  1. The **H2 timed hide is gone.** The plan card stays until the patient hides it; no timers anywhere in the product; `dwell_seconds` recorded for the ledger only. Gate 1 was reopened deliberately and re-approved.
  2. The **expired patient screen** wording is approved, softened on the user's instruction, with five copy rules in `02-architecture.md` §7.
- Round-2 review effort estimate: **90–150 h** for this architecture plus 20–35 h baseline. The user has reviewed this and **accepted the estimate as achievable** (25 Sep). Gate 3 still produces a real estimate; the acceptance is not a substitute for one.
- Recovery check on 26 September 2026: current checkout is `gate-2-architecture` at `6c65f30`. Six local commits remain unpushed; GitHub holds only the initial commit. Do not assume the remote has the approved gate work.
