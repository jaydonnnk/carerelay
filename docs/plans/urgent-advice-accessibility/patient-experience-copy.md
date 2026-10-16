# Patient experience copy inventory: APPROVED with Slice 16 and redesign amendments


## Quick safety check: APPROVED 16 October 2026

The user answered "I approve Gates 1 to 4 for the safety check as drafted. Start the buildout". Source of truth: `SAFETY_COPY` and `QUESTIONS` in `frontend/lib/journey.ts`.

- Quick safety check / Answer for right now. / Uses the challenge's example warning signs (Scenario 2). Not clinical guidance.
- What is your oxygen reading right now? Below 90% / 90% to 93% / 94% or higher / I cannot measure it
- Are you breathing very fast, 30 or more breaths a minute? Yes / No / Not sure
- Do you have new chest pain? Yes / No / Not sure
- Are you confused, or has someone said you seem confused? Yes / No / Not sure
- Next / Back
- Get emergency help now / Call 995 for an ambulance. / Do not wait for this app. / You said: ... / Change my answers
- No warning signs from these four questions. / We could not check: ... If you get worse, call 995.

## Patient wording change: APPROVED 16 October 2026

The user answered "yea approve the gate 1 strings commit and push" to the drafted table below.
These strings supersede the matching strings in the sections that follow; `00-status.md` holds the receipt and the disclosed deviations.

- Removed: "Demo only · fictional plan · no real care" (banner), "Fictional plan. No real care." (plan slip), "Fictional" (failed-screen slip).
- Footer on every patient screen, and the dialog's own label: "Simulated demo. Not medical advice."
- Start: "Your care plan", "No plan yet.", "See how CareRelay helps you act on it.", "Start".
- Restart link: "Start again".
- Plan action: "Go to the clinic for a same-day review."
- Fallback route: "the nurse helpline", so "If that does not work, call the nurse helpline."
- Plan slip and dialog heading: "Your plan".
- Input help: "Please don't enter personal details."
- Confirm help: "This saves the words shown above and checks them against your plan."
- Applied as the same substitutions: "With the clinic, to request an appointment.", "We cannot help with that here.", "Handed to the nurse helpline".
- Judge start page credit: "Built for the NTU LKCMedicine challenge".
- Accepted words for who acts gain "I will", "I'll", "I am going" and "I'm going".

## Redesign and judge view amendment: APPROVED 16 October 2026

[verified] The user answered "Approve Gate 1 for the redesign mockups, the new judge view and copy." on 16 October 2026.
`00-status.md` owns the receipt.

### New patient strings (approved)

- Step counter: "Step 1 of 4" (plan), "Step 2 of 4" (read-back and repair), "Step 3 of 4" (barrier), "Step 4 of 4" (consent). No counter on outcome, stop, recovery or start screens.
- Folded plan: "Your plan is folded away while you say it in your words."
- Plan slip label on the request-failed screen: "Fictional".

Every other patient string in the redesign is from the inventory below, unchanged.
On the request-failed screen, "No one has agreed to help yet." and "Please act now." share one status box.

### Judge copy pinned by file (approved)

The approved judge copy is the visible text of these files, pinned by SHA-256 at approval.
Call-specific values in them (phrases, timings, request IDs) are examples; the build reads them from the ledger.

| File | SHA-256 |
|---|---|
| `design/mocks/redesign/judge-intro.html` | `14e06b3d025bd9904cd6c526526029f195f22b6e0efea068c26e8650a854d78f` |
| `design/mocks/redesign/stage-check.html` | `65af1da8436f57f44c8dd7a8c906489a904c6895ec1499b892bf77e4c315edcd` |
| `design/mocks/redesign/stage-failed.html` | `3bf9008e0ad5fa6a543627dfd0e14a7566dbf6e39f5965885d042269350d3500` |
| `design/mocks/redesign/phone-plan.html` | `6f336fe01bd87d226fc239d1d9d3a365837b43c5d24f5409767ab325b6d14180` |
| `design/mocks/redesign/phone-readback.html` | `19758b19720f161b1cebef3f1117758ed7f9a8d52487cdb94b7334aa8b7230e9` |
| `design/mocks/redesign/redesign.css` | `680b8e6def0cfcd2607950cd84fc23ac46b18cb07b4fa18360938cf96e7e28dd` |

### Judge panel copy for unmocked states: APPROVED 16 October 2026 with Gates 2 to 4

[verified] Approved with Gates 2 to 4: "including the judge panel copy and the two honesty corrections". The judge stage needs one headline and one short paragraph for every state, not only the two mocked ones.
These are drafted in the approved voice. Braces are values read from the ledger or journey, never written by a model.
Nothing here reaches the patient screen.

| State | Headline | Paragraph |
|---|---|---|
| start | Mei is about to get her plan. | Press the button on the phone. CareRelay loads one fictional plan: an action, a deadline and who must act. |
| plan | Mei has her plan. | The plan comes from a fixed fictional script, not from a model. Next, Mei says it back in her own words. |
| readback | Mei says her plan back from memory. | Her plan is folded away, so her answer is recall, not copying. Nothing goes to Tencent ADP until she saves her words. |
| pending | Tencent ADP is reading Mei's words. | One call, capped at 15 seconds, with no retry. Her plan cannot change while it runs. |
| match | Mei got all three right. | Tencent ADP copied out three phrases. CareRelay's code matched each one to the plan. |
| deadline mismatch | Mei said “{said}”. Her plan says “{plan}”. CareRelay caught it. | (approved `stage-check.html` paragraph) |
| other mismatch | Mei's answer does not match her plan. | Code found a different {field}. Mei is asked to try other words or show her plan. |
| uncertain | CareRelay could not confirm Mei's answer. | Tencent ADP marked part of it as unclear, such as a “won't”, an “or” or a changed mind. Code does not guess, so Mei is asked again. |
| check did not run | The check did not run, so nothing changed. | Tencent ADP refused, ran out of time or replied in the wrong shape. Mei sees one safe sentence and her plan stays as it was. |
| barrier | Mei says what makes it hard. | Knowing the plan is not the same as being able to do it. Her answer decides which help CareRelay can offer. |
| permission | Mei decides whether to share her plan. | Nothing is shared without her agreement. Only the action and the deadline would go to the simulated provider. |
| request sent | The simulated request is out. No reply yet. | A sent request is not care. Mei's case stays open until someone agrees. |
| request failed | The booking failed. CareRelay says so, and keeps the {deadline} deadline. | (approved `stage-failed.html` paragraph) |
| stopped | CareRelay stopped asking questions. | When the example cannot help, it stops instead of guessing. The deadline and the nurse line stay on Mei's screen. |
| expired | The deadline has passed. CareRelay still tells Mei to act. | An expired plan is never hidden or marked done. |
| accepted | Someone agreed to help. Care is still not confirmed. | The agreement is simulated and labelled as simulated. |
| handoff | Handed to the fictional nurse line. | A human route now holds the plan. CareRelay does not claim care happened. |
| documented | Simulated proof of care is recorded. | This is the only state that counts care as evidenced, and here the proof is simulated. |
| panel read failed | The judge panel cannot read this episode right now. | Nothing on this panel is a record until the read succeeds. |

Lane and chip wording, APPROVED with two honesty corrections to the mockup:

- ADP lane heading: "Tencent ADP copied {n} phrases" (n is 1 to 3), "Tencent ADP found nothing it could copy" (n is 0), "Tencent ADP refused" (refusal), "Tencent ADP did not answer in time" (timeout), "Tencent ADP replied in the wrong shape" (invalid).
- Transport chip: "Live HTTPS call", "Offline test transport" or "Local simulation", from the stored provenance.
- **Correction 1:** the timing chip reads "Checked in {s} s", not "{s} s click to screen". The stored time runs from claim to completion on the server, not from the click.
- **Correction 2:** a different value reads "Different from plan", not "Later than plan". The ledger does not record which way a time differs.
- Comparison results: "Same", "Different from plan", "Unclear".
- Simulated lane heading: "The simulated provider replied: {failed | accepted}", or "The simulated provider has not replied".
- Offline actor wording, APPROVED 16 October 2026 with the Slice 23 Check ("including the disclosed deviations and the new offline actor wording"). Used only when the stored provenance is not a live HTTPS call:
  - Actor name in place of "Tencent ADP": "The local stand-in" (local simulation) or "The offline test transport" (test transport); the relay track leg reads "Local stand-in" or "Offline test transport".
  - Note: "Offline run: a local stand-in did the reading step. Tencent ADP was not contacted for this check."
  - Note: "Offline run: a test transport did the reading step. Tencent ADP was not contacted for this check."
- Axis values: request sent "Not sent", "Sent", "Acknowledged" or "Failed"; proof of care "None" or "Simulated"; case "Still open", "Closed", "Handed to a human" or "Expired".

### Judge copy for a send the guard refused: DRAFT 16 October 2026, needs Gate 1 approval

[hypothesis] Drafted with Gate 2 section 15 and Gate 3 section 11.7 for Slice 24.
Shown only on the judge stage when the stored extraction says `not_sent`. No patient string is added or changed: the patient keeps "We could not check that answer just now. Your plan has not changed."

- Transport chip and ADP lane heading: "Not sent to Tencent ADP"
- Headline: "The check was not sent, so nothing changed."
- Paragraph when paused: "Live checks are paused after an earlier call failed, until an operator reviews it. Tencent ADP was not contacted. Mei sees one safe sentence and her plan stays as it was."
- Paragraph when another check is running: "Another live check was still running, and only one runs at a time. Tencent ADP was not contacted. Mei sees one safe sentence and her plan stays as it was."
- Paragraph at any limit: "The live-check limit set for this demo is reached. Tencent ADP was not contacted. Mei sees one safe sentence and her plan stays as it was."
- Paragraph when not set up: "Live checks are switched on but not set up safely, so nothing was sent. Tencent ADP was not contacted. Mei sees one safe sentence and her plan stays as it was."

## Slice 16 confirmation amendment: APPROVED 14 October 2026

[verified] The user explicitly answered "Approve these exact Gate 1 strings"
on 14 October 2026. Gate 1 is narrowly re-approved for these five non-clinical
strings. `00-status.md` owns the receipt. Controls remain absent until the
corresponding guarded Slice 16 behavior exists. The existing inventory below
remains approved as recorded on 12 October 2026.

[hypothesis] One explicit button confirms the exact words displayed in the local
preview, saves them, then requests their check. Editing the draft removes that
preview and invalidates its prepared token. Review remains local and unsaved.

- Confirmation button: "Save and check these words"
- Confirmation help: "This saves the words shown above and checks them against your example plan."
- Pending status: "Checking your saved words. Your plan has not changed."
- Explicit retry button: "Check these words again"
- Explicit retry help: "This ends any previous check of these saved words and starts a new check."

[hypothesis] The pending status replaces the local preview label after saving.
An unavailable check reuses "We could not check that answer just now. Your plan
has not changed." An uncertain result reuses "We could not confirm that. Try
different words, or show your plan." Retry is an explicit action, never automatic.
No specialized non-timing repair or system-date wording is proposed or approved.
No clinical rule, deadline, outcome sentence, consent or real care claim changes.

**Approval receipt:** "Approve these exact Gate 1 strings", 14 October 2026.

[hypothesis] Revised following the user's request for concise wording, fewer
boxes and visual cues. Gate 1 was explicitly approved 12 October 2026. These are exact main/dialog text
extracts, including hidden feedback. Shared visible copy: "CareRelay", "Larger
text" / "Smaller text", "Demo only · fictional plan · no real care". The footer's
"Preview controls" disclosure is for review, not the production patient journey.

[verified] Calendar, clock, person, telephone and transport icons accompany text;
none replaces an action, deadline, owner or fallback. No images name real people
or facilities. The existing fictional action and the four approved outcome
sentences remain. Surrounding non-clinical copy is approved by the user as Gate 1 design content.

## 00-start.html

- Try an example
- No plan yet.
- See what happens when a request fails.
- See the example

## 01-plan.html

- Your next step
- What to do
- Go to the fictional provider's same-day review.
- Before
- 6pm today
- Who acts
- You
- No one has agreed to help yet.
- If that does not work, call the fictional nurse line.
- Say it in your words
- Your example plan
- Fictional plan. No real care.
- What to do
- Go to the fictional provider's same-day review.
- Before
- 6pm today
- Who acts
- You
- If that does not work, call the fictional nurse line.
- Back to my answer

## 02-readback.html

- What is your plan?
- What will you do, when, and who will act?
- Show my plan
- Your words
- Demo: use made-up words only.
- Add your words, or show your plan.
- Review my answer
- Your answer
- Preview only. Not checked or saved.
- We could not check that answer just now. Your plan has not changed.
- We could not confirm that. Try different words, or show your plan.
- Your example plan
- Fictional plan. No real care.
- What to do
- Go to the fictional provider's same-day review.
- Before
- 6pm today
- Who acts
- You
- If that does not work, call the fictional nurse line.
- Back to my answer

## 03-repair.html

- Let’s check the time
- Example answer:
- tomorrow
- .
- The plan says:
- before 6pm today
- .
- When will you go?
- Demo: use made-up words only.
- Add your words, or show your plan.
- Review my answer
- Your answer
- Preview only. Not checked or saved.
- Show my plan
- Your example plan
- Fictional plan. No real care.
- What to do
- Go to the fictional provider's same-day review.
- Before
- 6pm today
- Who acts
- You
- If that does not work, call the fictional nurse line.
- Back to my answer

## 04-barrier.html

- What makes it difficult?
- Choose one.
- Finding an appointment
- Getting there
- Something else
- Choose one to continue.
- Continue
- This example cannot help with that.
- If that does not work, call the fictional nurse line.
- Show my plan
- Your example plan
- Fictional plan. No real care.
- What to do
- Go to the fictional provider's same-day review.
- Before
- 6pm today
- Who acts
- You
- If that does not work, call the fictional nurse line.
- Back to my answer

## 05-permission.html

- May we share your plan?
- With the fictional provider, to request an appointment.
- Shared: the action and deadline. No caregiver message.
- I agree to share this plan.
- Agree above, or choose “Not now”.
- Try the simulated request
- Not now
- No reply yet.
- No one has agreed to help yet.
- Please do it before 6pm today.
- Simulated request.
- Show my plan
- Your example plan
- Fictional plan. No real care.
- What to do
- Go to the fictional provider's same-day review.
- Before
- 6pm today
- Who acts
- You
- If that does not work, call the fictional nurse line.
- Back to my answer

## 06-unresolved.html

- The request did not work
- No one has agreed to help yet.
- Please act now.
- Please do it before 6pm today.
- If that does not work, call the fictional nurse line.
- Show my plan
- Your example plan
- Fictional plan. No real care.
- What to do
- Go to the fictional provider's same-day review.
- Before
- 6pm today
- Who acts
- You
- If that does not work, call the fictional nurse line.
- Back to my answer

## 07-stop.html

- Let’s stop the questions
- No one has agreed to help yet.
- Please act now.
- Please do it before 6pm today.
- If that does not work, call the fictional nurse line.
- Show my plan
- Your example plan
- Fictional plan. No real care.
- What to do
- Go to the fictional provider's same-day review.
- Before
- 6pm today
- Who acts
- You
- If that does not work, call the fictional nurse line.
- Back to my answer

## 08-recovery.html

- We cannot load your plan
- Keep the instructions you already have.
- Try again
- Loading. Nothing is confirmed yet.

## 09-expired.html

- Your plan still needs action
- No one has agreed to help yet.
- You can still do this.
- It is past 6pm today. Please go now.
- Call the fictional nurse line. They can help from here.

## 10-accepted.html

- Your daughter agreed
- Someone has agreed to help.
- You do not need to act now.
- It is set for 6pm today.
- If that does not happen, call the fictional nurse line.
- Simulated agreement. Care is not confirmed.

## 11-handoff.html

- Handed to the nurse line
- We have passed this to the fictional nurse line.
- You do not need to act now.
- It is set for 6pm today.
- If that does not work, call the fictional nurse line.
- Simulated handoff. Care is not confirmed.
