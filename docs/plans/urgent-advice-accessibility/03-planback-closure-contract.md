# PlanBack and the Closure Contract — specification and feasibility

Date: **21 September 2026**. Author: Brody. Status: **specification; the mechanisms were carried into the approved Gate 1 product scope on 25 September 2026.** This document itself is not a gate approval — the authoritative gate state is in `00-status.md`.
Source: `docs/reviews/gate2-adversarial-review-round1.md` §E ranks both as the top two changes. This document turns them into something buildable and checks whether they actually are.

Nothing here authorises implementation. Gate 1 (Product) was approved on 25 September 2026; Gate 2 (Architecture) is in progress and no code may be written before Gate 4.

---

## TL;DR

| Mechanism | What it is | Feasibility | Effort | Biggest risk |
|---|---|---|---|---|
| **PlanBack** | Read-back loop with **deterministic** critical-field comparison and bounded repair | **High** | 18–30 h | A paper card performs equally |
| **Closure Contract** | Episode cannot close without evidence; deadline is immutable; retries never fake success | **Medium** | 38–59 h | Reads as enterprise plumbing, not care |

Neither needs exotic technology. Both are **ordinary engineering with unusual discipline**. That is the good news and the bad news: nothing here is technically hard, so nothing here is defensible as "we built something difficult." The defensibility comes from *measuring* that it works better than a card.

**Honest dependency finding:** PlanBack and the Closure Contract are **application logic**. They do **not** require WorkBuddy. WorkBuddy earns its place in the *coordinator, the real tool call, and the real tool-failure event* — not in these two mechanisms. Do not claim otherwise. See §5.

---

## 1. PlanBack — what it actually is

### 1.1 One-line definition

> **PlanBack: the patient restates the plan in their own words; code — not a model — checks the critical fields against the approved recommendation; a mismatch is repaired field by field before anything else proceeds.**

### 1.2 Where it comes from

Aviation read-back / hear-back. A controller issues a clearance, the pilot reads it back, the controller verifies the readback before the aircraft moves. `docs/reviews/gate2-adversarial-review-round1.md` §C names this as the donor mechanism. It is **prior art**, openly documented by the FAA. It is not our invention, and we must not present it as one. What may be ours is the *clinically constrained, patient-visible* version and a measured advantage.

### 1.3 The loop

1. **Present** the approved plan card: action, deadline, next owner, fallback route.
2. **Ask for restatement** — "tell us what you need to do and when," in the patient's own words. Text or voice.
3. **Confirm the transcript first.** If input was voice, show the transcript and let the patient correct it. *(The current `mockups/02-understanding-and-barrier.html` skips this and evaluates the draft transcript directly — that is a defect, see §1.5.)*
4. **Extract** critical fields from the confirmed restatement.
5. **Compare deterministically** against the recommendation. Field-scoped, boolean.
6. **Branch:**
   - all fields match → record `understanding_confirmed`, continue to feasibility.
   - mismatch → **repair**: name only the differing field, restate that field, ask again. Max **2** repair rounds.
   - still mismatched after 2 → **stop**. Route to the human/emergency path. Never continue on an unconfirmed plan.

### 1.4 The one rule that makes it safe

**The model interprets. Code decides.**

```
CRITICAL_FIELDS = ("action", "deadline", "next_owner")

def planback(expected, confirmed_restatement, llm):
    # the LLM is only allowed to produce a dict of extracted values
    got = llm.extract_fields(confirmed_restatement, fields=CRITICAL_FIELDS)

    mismatches = [
        f for f in CRITICAL_FIELDS
        if not equivalent(f, expected[f], got.get(f))
    ]
    return mismatches          # [] means the plan was understood
```

`equivalent()` is **plain code with no model in it**:

- `deadline` → compare as a **time bucket** (`2026-09-21T18:00`), never as prose. "Tomorrow" resolves to a date and fails the comparison. Exact, explainable, testable.
- `action` → compare against a **closed vocabulary of action ids**. "Go to the clinic" and "visit the polyclinic" can be declared equivalent by a lookup table; "wait and see" cannot.
- `next_owner` → compare against the named party in the recommendation.

This matters because a model grading comprehension can be wrong in both directions, and a wrong "you understood" is a safety failure while a wrong "you didn't understand" is a dignity failure. A boolean over extracted fields is auditable and reproducible in a test.

### 1.5 Defects in the current wireframe

`mockups/02-understanding-and-barrier.html` needs three changes before it can carry PlanBack:

| Line | Problem | Fix |
|---|---|---|
| 37 | The draft transcript is evaluated before the patient confirms it | Insert a confirmation step: show transcript → patient confirms/corrects → then compare |
| 38 | "That timing does not match the plan" — this is the repair, but it is triggered off an unconfirmed transcript | Move after confirmation |
| 29–33 | Free-text or voice is the only input | Add a constrained path (chips: "today before 6pm" / "tomorrow" / "not sure") so PlanBack works even with no voice and no ASR |

The third one is a feasibility unlock, not a downgrade: a constrained input path means **PlanBack can be built and tested before any speech work exists**, and it gives the baseline comparison a fair, low-burden comparator.

### 1.6 What PlanBack is NOT

- Not a comprehension score, quiz, or grade for the patient.
- Not an LLM judging whether the patient “understood.”
- Not proof of capacity. Poor restatement is not incapacity; new confusion may itself be clinical evidence (`PLAN.md` §8).
- Not a gate that blocks emergency guidance. **Urgent guidance appears before read-back, always** (`PLAN.md` §5).
- Not brain training. See §1.7.

### 1.7 The fading scaffold, and the cognitive claim we must not make

The hint ladder is bidirectional: it escalates when the patient needs help, and **fades when competence is demonstrated**. A new plan starts at H1; an unaided success lowers the starting level next time; a failure restores it; changes follow trends, not single rounds; and fading is invisible — no score, no streak, no progress bar.

**The mechanism is legitimate and citable.** Vanishing cues, errorless learning and spaced retrieval carry Class II–III evidence for teaching specific information to people with memory impairment (*International Psychogeriatrics*, 2013). Using them here is prior art, honestly described.

**The claim that would destroy the project is not.**

| Source | Finding |
|---|---|
| *Perspectives on Psychological Science*, 2022 | Meta-analyses show cognitive training produces **no far transfer** — improvement is confined to the trained task. |
| FTC, January 2016 | Lumos Labs (Lumosity) paid **$2 million** to settle deceptive-advertising charges for suggesting its games could "stave off" age-related cognitive decline. |

So the permitted and prohibited framings are:

| Permitted | Prohibited |
|---|---|
| "Helps you remember your plan." | "Keeps your mind sharp." |
| "Stops prompting you once you no longer need it." | "Helps prevent cognitive decline." |
| "Less burden on the caregiver." | "Trains your brain." |
| "You said it back correctly — here is your plan." | Any cognition score, risk level or screening result. |

**Why this matters more than it looks.** Responsible AI & Ethics is currently the project's **highest-scoring dimension at 6/10**, and Impact is 5/10. An unsupported decline-prevention claim would not merely fail to add points — it would undermine the one dimension the project is already strongest on, and it would be the single most quotable thing a judge could use against the submission.

**The ambitious version is preserved as research, not as a demo claim.** Repeated structured restatement of real-world plans measures the same person on a comparable task over months, which makes it a candidate early indicator of cognitive change. That is a **monitoring hypothesis**, not a training claim. It is out of scope for the judged slice: it needs a validated comparison instrument, clinical review, subgroup analysis, and an answer to what a false positive does to an anxious 78-year-old. It is recorded in `PLAN.md` §5.3 so the ambition is not lost, and it is not presented in the submission.

**Population consequence.** Pursuing cognitive monitoring would narrow the population from community-dwelling 65+ to MCI or subjective cognitive decline, with materially higher regulatory and ethical stakes. The demonstration keeps the broader population and treats the cognitive framing as a **mechanism**, not a **claim**.

---

## 2. The Closure Contract — what it actually is

### 2.1 One-line definition

> **Closure Contract: an episode cannot be shown as resolved until the next step has the required evidence — and no operational failure, retry, restart or duplicate may ever move the clinical deadline or manufacture success.**

### 2.2 Part A — two independent axes

The current `PLAN.md` §6 state model is a **single ladder**: `proposed → acknowledged → attempted → unconfirmed | evidenced | failed`. That mixes execution and evidence into one sequence, which is exactly the defect `CareRelay.md:150` flags: *"booking confirmation proves booking, not attendance; caregiver acceptance proves agreement, not care."*

Replace with **two axes that never collapse**:

| Axis | Values | Meaning |
|---|---|---|
| **Execution** | `not_started → attempted → acknowledged \| failed \| expired` | Did the request get through, and did anyone accept it? |
| **Evidence** | `none → self_reported → documented` | Do we have reason to believe care actually happened? |

Episode closure:

| Closure state | Condition |
|---|---|
| `open` | Default. Somebody still must act. |
| `closed_with_evidence` | Evidence ≥ `documented`, or an explicit human acceptance is recorded |
| `escalated_to_human` | Handed to a named human path, with the deadline still visible |
| `expired_unresolved` | Deadline passed with no evidence. **This is a real, reportable state — not a failure of the UI to update.** |

`attempted` + evidence `none` is the honest rendering of "we tried and nobody said yes." It is the core of the product.

### 2.3 Part B — five invariants

These are the rules that must hold under fault. They are what makes the contract a *contract* and not a status widget.

| # | Invariant | Why it matters |
|---|---|---|
| **I1** | **Absolute deadline.** `clinical_deadline` is set once at disposition and is immutable to operational code. Only a versioned, clinician-backed reassessment may change it. | Retrying a failed booking is not new clinical information. Giving the patient "more time" because our request timed out converts an operational problem into a clinical one. |
| **I2** | **No false completion.** No failed or unacknowledged action may render as resolved, in the UI, the API, or the summary. | This is the whole product thesis. |
| **I3** | **Idempotency.** Duplicate callbacks, replayed requests, and restarts must not advance state. | Networks retry. Users double-tap. Restarts replay. |
| **I4** | **Named owner.** At every moment exactly one party must act — patient, named caregiver, or an explicit human service. "Nobody, and it is unresolved" is a valid and *visible* answer. | "Someone should do something" is the failure mode we exist to catch. |
| **I5** | **Missing is not negative.** Absent data never becomes a negative finding. | Directly from `PLAN.md` §6 and the MedQAbstain finding. |

### 2.4 The schema shape

```
Episode
  clinical_deadline   datetime     # set once at disposition; immutable to retries
  policy_version      str          # set once; changes only via versioned reassessment
  attempts            Attempt[]    # append-only
  consent             Consent      # checked at execution, supports revocation
  evidence            Evidence     # axis B, never derived from axis A
  closure             enum(open | closed_with_evidence | escalated_to_human | expired_unresolved)

Attempt
  route_id            str
  idempotency_key     str          # dedupe on this, not on timestamp
  started_at          datetime
  status              enum(attempted | acknowledged | failed | expired)
```

And the anti-pattern, written down so nobody does it:

```python
# FORBIDDEN — "give them a bit more time because our request failed"
episode.clinical_deadline = now() + timedelta(hours=4)

# CORRECT — record the attempt, leave the deadline alone
episode.attempts.append(Attempt(route_id=r, idempotency_key=k, status="attempted"))
```

### 2.5 What the patient sees

The review is blunt that the full ladder is emotionally cold (`docs/reviews/gate2-adversarial-review-round1.md` §"Emotional verdict"). The patient UI shows **four lines and nothing else**:

1. No one has agreed to help yet.
2. Please act now: you, or [named person].
3. Please do it before 6:00 PM.
4. If that does not work, call [approved human route].

**Reworded 2 October 2026** to read like a person rather than an agent. The
normative table, the five copy rules and the change record live in
`02-architecture.md` section 7; this list mirrors them and is not the authority.

The two-axis ledger is **judge-facing evidence**, shown in the walkthrough and the failure-inspection view. It is not the patient's screen. This split is the single highest-leverage design decision in the reframe: it keeps the technical integrity visible to judges without turning the product into audit software.

---

## 3. Feasibility

### 3.1 Effort and dependencies

| Work item | Hours | External dependency | Confidence |
|---|---:|---|---|
| PlanBack: field extraction, comparison, repair loop, constrained input path | 12–20 | none | High |
| PlanBack: test suite (matched, mismatched, ambiguous, adversarial restatements) | 6–10 | none | High |
| Closure Contract: two-axis schema, closure rules, deadline immutability | 14–22 | none | High |
| Closure Contract: idempotency keys, callback dedupe, restart recovery | 12–18 | runtime access for the resume demo | Medium |
| Fault harness: 7 seeded sequences (timeout, stale availability, duplicate, reorder, restart, clock change, consent revocation) | 12–19 | none | High |
| Baseline: fixed card, counterbalanced dyad tasks, analysis | 20–35 | 3–6 recruited dyads | Medium |
| **Total** | **76–124** | | |

The build-only portion (excluding the baseline) is **56–89 hours**, which brackets the review's 60–90 estimate. Solo at 25 h/week that is roughly 3 weeks — which does not fit a 16 October submission alongside everything else. **Scope has to be cut somewhere.** See §6.

### 3.2 What is genuinely easy

- **Deadline immutability.** A schema decision plus discipline. Maybe 20 lines.
- **Two-axis state.** A schema and an enum change. The work is in the UI, not the model.
- **PlanBack comparison.** A parser and a lookup table.
- **Restart recovery.** Already implied by `PLAN.md` §6: the app owns state, the agent is a stateless coordinator. As long as that boundary holds, restart is a non-event.

### 3.3 What is genuinely risky

| Risk | Severity | Mitigation |
|---|---|---|
| **Baseline wins.** A clear bilingual card plus a booking link plus NurseFirst may be as good or better. | **High — this kills the project's premise** | Run the comparison *first*, on a clickable prototype, before building voice, booking or caregiver features. Review §E ranks this #1 for exactly this reason. |
| **PlanBack feels like a test.** Shame, burden, or a sense of being graded. | High | Explicit copy rules; never "incorrect"; bounded to 2 repairs; a visible "I'd rather not, just show me again" escape. Must be observed with real dyads, not assumed. |
| **Closure Contract reads as enterprise plumbing.** Status ladders are boring and judges have seen incident dashboards. | Medium | Lead with the human scene, not the ladder. The ledger is evidence, not the pitch. |
| **Simulated adapter oversold as integration.** | Medium | Every simulated element stays labelled in UI, screenshots, video and metrics (`PLAN.md` §4). |
| **Scope creep into a general workflow engine.** The two-axis model generalises beautifully and that is a trap. | Medium | One complaint pathway, one adapter, one caregiver channel. Feature freeze 6 Oct. |
| **No runtime access → the tool-failure demo is a mock of a mock.** | Medium | See §5. Falls back to a locally-simulated tool with an honest label, but then the organiser-dependency claim weakens materially. |

### 3.4 The kill tests

Adopt these verbatim, from `docs/reviews/gate2-adversarial-review-round1.md` §C, as **pre-registered** decision rules. Write them down now, before seeing results, so the result cannot be rationalised afterwards.

| Mechanism | Killed if |
|---|---|
| PlanBack | The fixed card achieves equal action/deadline recall with lower burden; **or** any critical correct statement is falsely flagged as a mismatch; **or** emergency guidance is delayed by the read-back |
| Closure Contract | A failed or unacknowledged action ever renders as resolved; **or** a duplicate callback or restart advances state; **or** an operational retry changes the clinical deadline |

---

## 4. Where these slot into the existing plan

Proposed edits to `docs/PLAN.md`. **Not applied** — the standing working agreement is that `PLAN.md` is not silently replaced.

| Plan location | Current | Proposed |
|---|---|---|
| §2 "What is genuinely ours to claim" | Two rows, `[hypothesis]` | Replace with the single tested contract from review §C: *one contract spans comprehension and execution; critical action/deadline survive read-back, retry, restart and failed handoff without false completion* |
| §5 demo story, steps 3–8 | Timing misunderstanding → barrier → failed service → interruption → status | Rewrite around **PlanBack repair** (step 3 becomes a field-scoped mismatch and repair) and **the four invariants under injection** (steps 6–7 become the fault sequence) |
| §6 state model | Single ladder (line 215) | Replace with the two-axis model in §2.2 above. **This is a correctness fix, not a preference** — `CareRelay.md:150` already flags the current model as mixing dimensions |
| §6 responsibilities | "Application state: … execution vs evidence" | Already correct. No change — the architecture was right; only the state enum was wrong |
| §7 effort table | Dimension-weighted | Add a PlanBack + Contract row; note the baseline comparison is on the critical path, not a nice-to-have |
| §9 Gate B | "Compare against clear instructions and structured checks" | Add: **this gate is now the primary kill test.** If it fails, the project pivots or narrows rather than decorating |
| §9 Gate D | Frozen suite, zero critical violations | Add the 7 seeded fault sequences as explicit pass/fail cases |
| §11 scores | Conditional 73–84 | Unchanged. But note the 39/100 artifact-only floor from the 21 Sep review |
| `mockups/02` | Transcript evaluated before confirmation | Fix the ordering; add the constrained input path (§1.5) |
| New `mockups/05` | — | `05-planback-repair.html` — the repair loop, showing a field-scoped mismatch and a bounded retry |

### The revised five-minute demo

1. Reviewed recommendation appears: **"Be seen today, before 6:00 PM."** Fallback named.
2. Patient restates: *"I can wait until tomorrow when my daughter is free."*
3. **PlanBack:** the transcript is confirmed, then compared. `deadline` mismatches. Only the deadline is repaired. *"The plan says today, before 6pm. What time will you go?"*
4. Patient: *"Today before 6."* Match recorded.
5. **Barrier check** — separate from comprehension. *"I can't get there."* A permitted alternative route is proposed.
6. **A real organiser tool call runs and fails.** Not a mock. The failure event is the platform's.
7. **Closure Contract under injection:** restart, duplicate callback. The deadline holds. Execution stays `failed`. Evidence stays `none`.
8. **Patient screen:** four lines. *No one has agreed to help yet. Please act now: you, or [name]. Please do it before 6:00 PM. If that does not work, call [route].*
9. **Judge view:** the two-axis ledger, with the fault sequence and its assertions visible.

---

## 5. The honest WorkBuddy dependency finding

This is the part that needs care, because it is easy to overclaim.

| Capability | Needs WorkBuddy? |
|---|---|
| PlanBack comparison and repair logic | **No.** Application code. |
| Deadline immutability, two-axis state, closure rules | **No.** Application code. |
| Idempotency and callback dedupe | **No.** Application code. |
| Adaptive clarification of a vague description | **Yes** — this is genuine language work |
| The real tool call and its real failure event | **Yes** — this is the strongest dependency proof available |
| Episode resume across a genuine session boundary | **Yes** |

So the honest claim is: **WorkBuddy is the execution substrate; the Closure Contract is the product.** The platform supplies coordinator, tools, failure events and session continuity. It does not supply — and must not be credited with — the clinical state, the deadline invariant, consent, or the honest closure rule.

That is a *better* claim than "impossible without WorkBuddy," because it is true and it is checkable. `PLAN.md` §9 Gate C already asks exactly this question. The answer above is the one to defend.

**Corollary for feasibility:** if runtime access never materialises, PlanBack and the Contract can still be built and tested. You lose the dependency proof and most of the Technical Execution and AI Interaction marks, but you do not lose the product. That is a meaningful hedge, and it is worth knowing deliberately rather than discovering in October.

---

## 6. Suggested build order

Ordered by risk-first and by what kills the project soonest. Each step is independently verifiable.

| # | Step | Hours | Gate | Stop condition |
|---|---|---:|---|---|
| 1 | Clickable text prototype: plan card, constrained restatement, deterministic comparison | 8–12 | — | If the card baseline is obviously as good, stop and reconsider the whole reframe |
| 2 | **Baseline comparison with 3+ dyads** — card vs PlanBack, counterbalanced, raw results | 12–20 | **Gate B** | Card wins → cut PlanBack, keep the card, narrow to the contract only |
| 3 | Two-axis state + immutable deadline + closure rules | 14–22 | — | — |
| 4 | One real WorkBuddy tool call, one real failure event | 8–14 | **Gate A** | No access by 26 Sep → local simulation, honest label, weakened dependency claim |
| 5 | Fault harness: restart, duplicate, stale, reorder, clock change, consent revocation | 12–19 | **Gate D** | Any invariant violation → fix before any further feature work |
| 6 | Judge-facing ledger view + trust-boundary diagram | 6–10 | — | — |
| 7 | Submission assets | 8–14 | — | — |

**Cut now, not later:** Mandarin voice, broad respiratory intake, patient-facing ledger detail, caregiver orchestration beyond one channel, booking integration. Every one of these is deferred in `docs/reviews/gate2-adversarial-review-round1.md` §E and none of them is on the critical path to a scoring submission.

**The 26 September decision point.** If step 4 has not produced a working end-to-end tracer, cut everything except steps 1–2 and submit the narrow comparison. A small honest result beats a large unbuilt claim.

---

## 7. Open questions this document does not answer

1. Does the fixed card actually lose? **Unknown until step 2 runs.** This is the project's load-bearing assumption and it is currently untested.
2. Which single complaint can a clinician approve with a same-day window, more than one legitimate non-emergency route, a realistic access barrier, and no unvalidated measurements or dosing? **No reviewer engaged.**
3. Do older adults accept read-back without shame or coercion, and do they accept the caregiver role? **No dyads recruited.**
4. Is the agent/application state boundary achievable in the managed runtime, or does session state leak into the coordinator? **Untested.**
5. Does WorkBuddy access exist at all? **Unconfirmed, and it gates scoring.**
