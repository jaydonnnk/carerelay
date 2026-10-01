# Product: CareRelay urgent-advice accessibility

## Problem

An older adult may receive the right care advice and still fail to act because the timing was misunderstood, the next step is impractical, or a booking or handoff attempt failed. Current interfaces can make a recommendation or click look like progress even when nobody has accepted responsibility and no care has occurred. Language and typing barriers can make that failure worse.

CareRelay must help the patient and their chosen caregiver answer three questions without hiding uncertainty:

1. What do I need to do, and by when?
2. Can I actually do it?
3. Has help really been arranged, or is it still unresolved?

Mandarin text and optional Mandarin speech are accessibility modes. The critical action, deadline, and unresolved status must always remain visible as text. Draft Mandarin in the wireframes is for layout testing only and is not clinically reviewed.

## Provisional demonstration persona

Mei is a fictional 72-year-old Mandarin-preferring adult, assisted remotely by her daughter, in a bounded respiratory-symptom scenario derived only as a product fixture from the organiser's adult COVID example. Until a qualified reviewer approves the clinical content, the demo receives a pre-authored recommendation and proves only understanding, feasibility, consent, failure recovery, reassessment and truthful status. It does not accept arbitrary symptoms or present the organiser's example thresholds as validated Singapore guidance.

## Success metric

In a six-dyad formative test using a deliberately failed simulated handoff, **0 of 6 dyads incorrectly report that care has been arranged** after viewing the final CareRelay state. Record each dyad's answer before explanation and compare it with a fixed instruction-card baseline.

For PlanBack, record **both** the restatement accuracy and the **hint level** at which it was achieved. A restatement produced at H2 or H3 is not evidence of recall, and reporting it as such would make the result worthless.

## Announcement — the blog post before the feature

CareRelay now helps older adults move from care advice to an honest next step. It checks whether the timing was understood, asks what may prevent action, and keeps the original deadline visible when a plan fails. Patients may read or speak in English or Mandarin, while every critical instruction remains on screen for confirmation. CareRelay never labels a booking attempt, caregiver message, or click as completed care.

## Product rules

- A clinician-governed recommendation appears before navigation, voice conversation, or caregiver coordination.
- Urgency fixes the deadline; an access barrier may change the route but never silently extends the deadline.
- The patient confirms the critical text, including any speech transcript, before it becomes a reported fact.
- Voice is optional. Text input, text output, correction, and replay remain available.
- Mandarin is a bounded accessibility mode, not an automatic expansion of clinical scope.
- If the system cannot safely interpret a critical fact, it abstains and directs the user to an appropriate human or emergency path.
- CareRelay distinguishes attempted, acknowledged, unconfirmed, evidenced, and failed actions.
- A simulated service or caregiver response is visibly labelled simulated.

### PlanBack rules

- The restatement prompt **escalates through four levels** rather than shaming the patient: H0 unaided, H1 structural cue, H2 card shown and hidden **when the patient says so**, H3 plan shown and confirmed by choosing.
- **The level used is always recorded.** Without it, “she remembered” and “she read it off the screen” are indistinguishable.
- **H0–H2 never reveal the critical fields** — the action, the deadline, or the owner. H2 re-exposes the card and lets the patient hide it **in their own time**: that tests retention, not reading. **No timer.** A five-second rule was rejected on 25 September 2026 as unreadable for older adults and unusable with a screen reader (see `PLAN.md` §5.2.1).
- **The patient is never trapped.** A persistent “show my plan” control reveals the full card at any time and records a cued outcome.
- **H3 is an honest result, not a failure.** `not_recalled` routes to the human path and is never dressed up as comprehension.
- The restatement is compared **field by field by deterministic code**, never graded by a model.
- Repair is **bounded to two rounds**, after which the flow stops and routes to a human path.

### Approved patient-facing copy

Patient-facing strings are Gate 1 content. A string that no wireframe carries must
be approved here before it ships, because a flow that stops has to stop with words
rather than with a blank screen.

- **Coordinator unavailable, the PlanBack degraded state:** "We could not check that answer just now. Your plan has not changed." Approved at the Gate 1 touch of 1 October 2026, which Slice 4 raised as an open item. It names no symptom, urgency, route or deadline, and asserts only that the check did not happen. The round is not scored and no restatement row is written, so this sentence must never imply that an answer was accepted.

### Adaptive scaffolding rules

The ladder fades as well as escalates: support is withdrawn when competence is demonstrated.

- A new or changed plan starts at **H1**, so the patient is never dropped into a blank prompt.
- A successful **unaided** restatement lowers the starting support level for the next comparable plan.
- A failed or cued restatement **restores** the previous level.
- Support changes on a **trend across episodes**, never on a single round.
- **Fading is invisible.** No score, no streak, no progress bar, no level shown to the patient.
- The technique is **vanishing cues with errorless learning and spaced retrieval** — an established cognitive-rehabilitation mechanism, cited as prior art, not invented here.

## What this product does not claim

These are prohibitions, not preferences. Any of them appearing in the product, the submission, the video or the pitch is a defect.

- **No cognitive improvement, cognitive training, “keep your mind sharp” or dementia-prevention claim.** Meta-analyses of cognitive training find no far transfer, and the FTC settled with Lumosity for $2 million in 2016 over exactly this claim. The scaffold improves retention of *this specific plan*; it does not make anyone smarter or slow decline.
- **No cognitive screening, risk score or diagnostic output.** Restatement accuracy is not a cognitive assessment.
- **No clinical validation, improved health outcome or avoided-admission claim.**
- **No “world-first” or empty-market claim.**
- **No user-facing language** such as “cognitive rot,” “brain training,” “use it or lose it,” or any framing that implies the patient's mind is decaying. The product helps someone remember their plan and stops prompting once they no longer need it. That is the whole description.

### Closure Contract rules

- An episode **cannot be marked resolved without evidence**.
- Execution status and evidence status are **two independent axes** and never collapse into one ladder.
- **A failed or unacknowledged action is never rendered as resolved** — not in the UI, the API, or any summary.
- **No operational retry may move the clinical deadline.** Only a versioned, clinician-backed reassessment may.
- Duplicate callbacks, replayed requests and restarts must not advance state.
- At every moment exactly one named party must act, or the screen says plainly that nobody does and it is unresolved.
- **The patient sees four lines**, not the ledger: help is not arranged / who must act now / by when / the fallback route. The two-axis ledger is judge-facing evidence.

### Fixture and asset rules

- **No fixture, hint, screenshot, mockup, diagram or demo asset names a real healthcare facility**, real ward, or real clinician. The demonstration uses a fictional, clearly-labelled simulated provider. Real institution names are excluded for privacy, reputational and simulation-honesty reasons.
- Simulated availability, receipts, caregiver replies and service acknowledgements stay visibly labelled in every asset, including the video.

## Screens

- `mockups/01-recommendation.html` — immediate bilingual recommendation with a fixed deadline and optional listen/speak controls.
- `mockups/02-understanding-and-barrier.html` — transcript confirmation **first**, then the PlanBack restatement with the hint ladder, then a separate practical-barrier check.
- `mockups/03-unresolved-handoff.html` — failed simulated action with a truthful status and unchanged deadline.
- `mockups/04-reassessment-and-abstention.html` — symptom-change reassessment that stops the conversational flow and shows an emergency/human handoff.
- `mockups/05-planback-repair.html` — the field-scoped repair loop: one mismatched field named, repaired, and re-checked, with the recorded hint level visible.

## Explicitly deferred

- Additional languages, dialects, or code-switching beyond a measured Mandarin spike.
- Voice-only operation.
- Real clinic booking, emergency dispatch, EHR integration, diagnosis, prescribing, or autonomous disposition.
- Claims of clinical readiness without a qualified reviewer and authorised clinical content.
