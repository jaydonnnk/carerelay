# CareRelay workaround and feasibility audit

This file separates honest workarounds from gates that cannot be replaced. It supports Gate 1 but does not approve an architecture or implementation.

## Blocker responses

| Blocker | Response | Honest claim boundary |
|---|---|---|
| No clinical reviewer or protocol rights | Use a pre-authored, injected recommendation fixture to demonstrate comprehension, consent, barriers, failure recovery and status truthfulness. Continue seeking one qualified reviewer for one original, cited pathway. | Without reviewer approval, do not claim the symptom-to-disposition path is clinically safe or patient-ready. A fixture proves workflow behaviour only. |
| Cannot recruit 6–8 target dyads quickly | Keep six as the target. Minimum fallback is three older-adult/caregiver dyads in short remote think-aloud sessions, plus scripted accessibility cases. Report raw outcomes, not percentages or significance. | Fewer than three target dyads means no human-centred validation claim. Caregiver or general-adult proxies may find usability bugs but cannot validate older-adult suitability. |
| Ledger states are vague | Define narrow milestones: `proposed` = option displayed; `acknowledged` = named actor confirms receipt; `attempted` = authorised request dispatched with timestamp and request ID; `unconfirmed` = no valid acceptance or outcome; `failed` = explicit terminal rejection/error; `evidenced` = evidence for a named milestone such as `booking_confirmed`. | Never use a generic “handled” or “care complete” state. Simulated evidence remains labelled simulated. |
| Reassessment and abstention are missing | Add one symptom-change checkpoint that creates a new assessment version without rewriting the earlier decision or deadline. Missing critical facts, contradictions, unsupported measurements and out-of-scope complaints stop the flow and request human help. | Operational retry cannot change clinical urgency. A new clinical decision needs new evidence and a version. |
| Baseline is too weak | Compare CareRelay with a concise bilingual action card containing identical clinical wording, legitimate options and a direct booking link. Measure deadline recall, next-action recall, unresolved-barrier recognition, completion belief and task time. | CareRelay must win through repair and truthful recovery, not through receiving better clinical content. |
| WorkBuddy value is unproved | Time-box an access spike: one typed tool call, one real tool failure, one permission-gated alternative and one resumed episode. If managed access fails, use genuine CodeBuddy development history to satisfy the stated product requirement and remove WorkBuddy-runtime claims. | At least CodeBuddy or WorkBuddy usage proof is mandatory. WorkBuddy irreplaceability is not. |
| Original schedule is overdue | Rebaseline immediately with hard fallback dates below. | Missed kill dates activate scope reduction; they do not justify hiding the blocker. |

## Rebaselined schedule

The provisional fixture uses a fictional 72-year-old Mandarin-preferring adult in a bounded respiratory-symptom journey inspired by the organiser's adult COVID example. Its clinical thresholds are not treated as validated Singapore guidance.

| Date | Outcome | Fallback trigger |
|---|---|---|
| 21–22 Sep | Approve product scope; confirm registration; attempt reviewer and organiser access | No reviewer: use injected clinical fixture. No WorkBuddy: prepare CodeBuddy-led route. |
| 23–26 Sep | English text tracer and truthful failure path | Cut voice and additional scenarios if the core path is not end-to-end. |
| 27–29 Sep | Ledger, reassessment, abstention and fixed-card baseline | No new features until invariant tests pass. |
| 30 Sep–2 Oct | Simplified Chinese text and Mandarin TRTC spike | TRTC unavailable or unsafe: ship bilingual text only and hide voice. |
| 3–5 Oct | Three-to-six dyad sessions and fixed utterance tests | No target users: downgrade HCD claim; do not invent percentages. |
| 6 Oct | Feature freeze | No new integrations. |
| 7–10 Oct | Critical fixes and complete evaluation rerun | Any critical meaning reversal removes Mandarin voice. |
| 11–14 Oct | Submission assets, usage proof, source, diagram and walkthrough | Completeness before polish. |
| 15 Oct | Internal submission target | Preserve one day for submission problems. |

## Mandarin and voice feasibility

Verdict: **Simplified Chinese text is feasible. Mandarin voice is feasible as a controlled spike, not yet safe as a core clinical channel.**

Official Tencent documentation supports the technical primitives:

- [TRTC built-in speech recognition](https://trtc.io/document/79672) accepts Mandarin Chinese with language code `zh`.
- [TRTC TextToSpeech](https://trtc.io/document/80010) supports Chinese and documents the international API in `ap-singapore`.
- [TRTC conversational TTS](https://trtc.io/document/81360) documents streaming Chinese output.
- [WorkBuddy enterprise agents](https://www.codebuddy.cn/docs/enterprise/adminguide/CloudAgent) support MCP and external APIs, but no built-in TRTC voice connector was verified.

Provisional route to test at Gate 2, not approved architecture:

1. Push-to-talk Mandarin input only; no continuous listening.
2. The app sends audio directly to TRTC rather than streaming audio through WorkBuddy.
3. The transcript appears beside the original audio turn and must be corrected or confirmed.
4. Critical facts—numbers, negation, onset, identity, worsening and deadlines—always receive explicit confirmation.
5. TTS reads the exact reviewed on-screen text; it never creates new clinical advice.
6. Emergency text appears immediately and never waits for speech synthesis.
7. Any uncertainty, failed recognition or meaning conflict falls back to text or abstention.
8. Raw audio is not retained by default; consent, retention and processor terms require review.

## Mandarin release gate

- All critical Chinese strings require native-speaker review; clinical strings require bilingual clinical approval.
- Test at least 30 fixed utterances covering numbers, negation, duration, symptom change, elderly speech and Singapore code-switching.
- Zero silent critical-fact errors are allowed. An ambiguous fact must trigger confirmation or abstention.
- If the runtime/account spike fails, retain bilingual text and remove the microphone control from the judged demo.

Language availability is not evidence of clinical accuracy, accessibility or Singapore regulatory readiness.
