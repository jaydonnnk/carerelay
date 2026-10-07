# Baseline comparison: pre-registration protocol

**Status:** frozen before the first dyad. Protocol version `protocol-v1`. Card
instrument `fixed-card-v1` (`study/fixed-card.html`).

**This document is a pre-registration, not a plan of record for the build.** It is
the protocol for the Gate B comparison (Slice 9). It authorises no participant
contact, no recruitment, no session, no deployment, no install, no credential and
no commit.

**Why it exists.** The project rests on one untested assumption: that a fixed
instruction card plus a direct booking link plus an approved human route does not
perform equally well. If it does, the read-back mechanism is unnecessary. That is
the primary kill test, and a kill test whose questions and rules are chosen after
the results is not a test. Everything in sections 3, 7, 10, 11, 13, 15 and 17 is
therefore written down here, in advance, and does not change.

---

## 1. What this study measures, and what it does not

**It measures the mechanism:** whether read-back plus a truthful status changes
comprehension, burden and false-completion belief.

**It does not validate clinical advice.** The comparator material is
content-neutral (Option A, `03-program-design.md` section 6.2). Neither condition
names a symptom, an urgency, a threshold or a real facility, and neither asserts a
clinical claim. The fixture is Tier 1 non-clinical content, and its honesty rests
on asserting no clinical claim rather than on quoting one.

**No result from this study may be described as clinical validation.** If a
submission sentence implies otherwise, it is false and must be removed.

---

## 2. Design and conditions

**Design: between-subjects.** Each dyad is assigned to exactly one condition. There
is no crossover and no within-subject arm.

| Condition | What the participant receives |
|---|---|
| **A, CareRelay** | The full assessed flow: intake, the plan, read-back of the plan, the barrier step, the action, and the truthful unresolved status on screen |
| **B, fixed card** | The standalone card, printed or exported to PDF, delivered outside the application. No application screen is shown at any point |

**Why between-subjects, and why the card is external.** An in-app card arm cannot
produce the primary outcome, because a static card has no failed handoff to score.
Wrapping the card in application chrome erases the low-burden advantage the card is
being tested for. A within-subject crossover leaks read-back comprehension from one
condition into the other. `docs/adr/0006-external-between-subjects-baseline.md`
records all three.

**Stated limitation of the design.** In condition A the truthful status arrives on
a screen; in condition B it is spoken by the facilitator from the scripted
statement in section 7. The status content is identical. The delivery channel is
not, and it cannot be, because the comparison is an application against paper. This
is a limitation of the instrument and is reported with the results.

---

## 3. Allocation

Allocation is fixed before the first session and does not change.

- A dyad takes the **next unused position** in the frozen order in section 12.
- The order alternates A and B for the first twelve positions.
- No participant chooses a condition. No dyad switches condition after assignment.
- The facilitator records the position used, so a skipped or abandoned session
  leaves a named gap rather than a silent resequencing.

---

## 4. Participants and consent

- **Dyads:** an older adult, and where present a family caregiver.
- **Target: 6 dyads per condition. Minimum: 3 dyads per condition.** Below three in
  either condition, make no human-centred validation claim; report raw outcomes
  only (`research-workarounds.md`).
- **Consent:** research-participant consent is recorded on the consent sheet before
  any task begins. It is **separate from the clinical `consents` table** and is
  never written into it. A participant may withdraw at any point; a withdrawn
  dyad's row is marked withdrawn and is excluded from the analysis.
- **What is collected:** the raw outcome sheet, task time, the burden rating, the
  answer to the scripted question, and any adverse reaction the participant
  volunteers. Nothing else.
- **What is not collected:** no audio, no video, no clinical data, no real patient
  data. The fixture is fictional.
- **Retention:** all study data is destroyed 30 days after submission.

---

## 5. Procedure, condition A (CareRelay)

1. Record consent.
2. Run the assessed flow: intake, the plan, read-back, the barrier step, the action.
3. The action fails, as scripted. The screen shows the truthful unresolved status.
4. Record the reading start and end time of the status screen.
5. Do **not** speak the scripted status statement. The screen carries it.
6. Ask the scripted post-failure question (section 7). Record the uncoached answer.
7. Ask the secondary-outcome questions (section 7). Record each raw answer.

---

## 6. Procedure, condition B (fixed card)

1. Record consent.
2. Hand the participant the card. Say nothing about its content.
3. Allow the participant to read the card once. Record the reading start and end
   time. Do not answer questions about the plan; redirect to the card.
4. Do **not** ask the participant to restate the plan. The absence of read-back is
   the variable under test. Asking for a restatement here would destroy the
   comparison.
5. Speak the scripted status statement (section 7) verbatim.
6. Ask the scripted post-failure question (section 7). Record the uncoached answer.
7. Ask the secondary-outcome questions (section 7). Record each raw answer.
8. Collect the card back.

---

## 7. The scripted statement and questions (verbatim, frozen)

**Scripted status statement, condition B only, spoken verbatim:**

> The booking link was tried. No one has agreed to help yet.

**Scripted post-failure question, both conditions, verbatim:**

> Has care been arranged for you?

The participant answers yes or no, uncoached. No prompt, no hint, no repetition of
the plan, no re-reading of the card. If the participant asks what the facilitator
thinks, the facilitator says: "I cannot answer that. Please give me your own
answer." The first answer stands.

**Secondary-outcome questions, both conditions, verbatim:**

| Field | Question |
|---|---|
| Action recall | What were you asked to do? |
| Deadline recall | By when? |
| Barrier recognition | Was there anything that would have stopped you doing it? |
| Burden | How hard was it to keep track of this plan? Answer 1 for very easy, up to 5 for very hard |

The burden item is a five-point scale, 1 (very easy) to 5 (very hard). Task time is
the recorded reading window in seconds, reported separately from burden.

---

## 8. Primary outcome

**False completion:** the participant's uncoached yes answer to the scripted
post-failure question, in a context where the status is unresolved and no care is
arranged. "Yes" is a false completion. "No" is not.

Recorded raw, per dyad, in section 12.

---

## 9. Secondary outcomes

| Outcome | Recorded as |
|---|---|
| Action recall | Correct / incorrect |
| Deadline recall | Correct / incorrect |
| Both correct | Correct / incorrect (the conjunction of the two above) |
| Hint level | H0 to H3, condition A only, read from the record |
| Barrier recognition | Recognised / not recognised |
| Task time | Seconds, from the recorded reading window |
| Burden | Integer 1 to 5 |

---

## 10. Answer key

The answer key **is the fixture's values**. It is not written independently here,
so that the card, the application and the key cannot drift apart.

| Field | Keyed value |
|---|---|
| Action | `attend_same_day_review`, rendered "Go to the fictional provider's same-day review." |
| Deadline | 18:00 SGT on the local day of the session, displayed "6pm today" |
| Owner | the participant |
| Fallback route | `nurse_line`, rendered "the fictional nurse line" |

**Deadline scoring.** Any statement of the same instant on the same local day is
correct: 18:00, 6pm, six in the evening, or 6pm today. A statement of a **different**
instant is incorrect, not uncertain. That distinction is deliberate: it is the
whole point of kill condition K1, and a wrong value must never be excused as
ambiguity.

---

## 11. Scoring rules

- The scorer sees the **answer key** and the **participant's response**. The scorer
  does not see the project hypothesis.
- Action recall is correct only if the named action is the keyed action or an
  unambiguous paraphrase of it.
- Deadline recall is correct only if the stated instant equals the keyed instant.
- Both-correct is the conjunction of the two, and is the field the cut rule reads.
- False completion is a yes to the primary question. It is scored from the
  participant's first answer and is never revised.
- A wrong value is scored **incorrect**. It is never scored uncertain.
- A response the scorer cannot classify is recorded verbatim on the sheet and
  resolved by the second scorer, not by the facilitator who ran the session.

---

## 12. Raw outcome sheet and allocation order

**Allocation order, frozen.** Position 1 takes A, position 2 takes B, and so on.

| Position | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Condition | A | B | A | B | A | B | A | B | A | B | A | B |

**Raw outcome sheet, one row per dyad.** Blank on purpose; it is filled in during
the sessions and is never summarised into a percentage below ten participants.

| Dyad | Position | Condition | Task time (s) | Action recall | Deadline recall | Both correct | False completion | Barrier recognised | Burden (1-5) | Hint level (A only) | Adverse reaction | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |

---

## 13. Cut rule (pre-registered)

**PlanBack is cut if any one of these holds:**

1. the card achieves **equal action and deadline recall with lower burden**; or
2. **any critical correct statement is flagged as a mismatch**; or
3. **emergency guidance is delayed by read-back**.

For equal-sized conditions:

- "equal action/deadline recall" means the card has **at least as many dyads with
  both fields correct** as CareRelay;
- "lower burden" means a **lower median burden rating**, with task time reported
  separately and not folded into the burden comparison.

**If the card wins on this rule, stop.** PlanBack is cut and Slices 10 to 12 are
replanned. That is the plan working as designed, not failing.

---

## 14. The two kill conditions that need no participants

Cut conditions 2 and 3 are pure system properties. They were lifted out of the
participant study and run offline at Slice 0, with no participants and no reviewer,
because no guidance is shown to anyone:

| Cut condition | Test | Result |
|---|---|---|
| False mismatch (condition 2) | a fixed adversarial corpus of correct restatements must not be flagged | PASS, 15 tests, 0 failures |
| Delayed emergency guidance (condition 3) | the fixture's urgent guidance renders before any PlanBack call is reached | PASS, same run |

They are recorded here so that conditions 2 and 3 are not read as untested, and so
that only condition 1 remains as the reason Gate B needs participants.

---

## 15. Reporting rules

- **Report raw counts for every outcome.** Counts are the result.
- **Never report a percentage below ten participants in total (n = 10).** With
  fewer than ten dyads overall, a percentage overstates what the sample can carry.
- **With fewer than three dyads in either condition, make no human-centred
  validation claim.** Report the raw outcomes and say plainly that the study did
  not reach the minimum.
- **Report adverse reactions to read-back**, including any the participant
  volunteers and any the facilitator observes.
- **Report the design limitation in section 2** wherever a result is reported.
- n=6 per condition is a **directional decision, not efficacy evidence**. Say so in
  every place the result appears.

---

## 16. Blinding

- The **scorer** sees the answer key and the participant's response. The scorer does
  not see the project hypothesis, does not know which condition the project expects
  to win, and does not run the sessions.
- The **facilitator** runs the session and does not score it.
- Where the sheet allows, the response is scored before the condition label is
  read.

---

## 17. Freeze declaration

**Frozen on 7 October 2026, before the first dyad.**

The following are frozen as of that date and do not change afterwards:

1. the card, `fixed-card-v1`, including its wording, its four lines and its offered
   routes;
2. the scripted status statement and the scripted questions in section 7;
3. the answer key in section 10 and the scoring rules in section 11;
4. the allocation order in section 12;
5. the cut rule in section 13;
6. the reporting rules in section 15.

**A change to any of these after the first session invalidates the
pre-registration.** It must be recorded as a post-hoc change, with its date and
reason, and the result must be reported as post-hoc. It must not be applied
quietly and it must not be presented as pre-registered.

---

## 18. Honest claim boundary

- The study measures the mechanism only. It does not validate clinical advice.
- The comparator carries no clinical content, so nothing here tests whether any
  care advice is understood.
- n=6 per condition supports a directional decision only.
- Recruitment is load-bearing. **No dyads means no Gate B result**, and that is
  reported as a failed recruitment, not as a null result.
- No percentages below ten participants.
- The project's own estimate of which condition wins is not evidence. It is the
  hypothesis the study exists to falsify.
