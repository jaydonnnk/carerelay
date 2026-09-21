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

## Screens

- `mockups/01-recommendation.html` — immediate bilingual recommendation with a fixed deadline and optional listen/speak controls.
- `mockups/02-understanding-and-barrier.html` — transcript confirmation, teach-back, and separate practical-barrier check.
- `mockups/03-unresolved-handoff.html` — failed simulated action with a truthful status ladder and unchanged deadline.
- `mockups/04-reassessment-and-abstention.html` — symptom-change reassessment that stops the conversational flow and shows an emergency/human handoff.

## Explicitly deferred

- Additional languages, dialects, or code-switching beyond a measured Mandarin spike.
- Voice-only operation.
- Real clinic booking, emergency dispatch, EHR integration, diagnosis, prescribing, or autonomous disposition.
- Claims of clinical readiness without a qualified reviewer and authorised clinical content.
