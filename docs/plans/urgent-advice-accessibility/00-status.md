# Status: CareRelay urgent-advice accessibility

- Gate 1 — Product: **APPROVED** (25 September 2026)
- Gate 2 — Architecture: in progress (draft written 25 September 2026, awaiting user review)
- Gate 3 — Program Design: pending
- Gate 4 — Slice plan: pending

## Slices

- [ ] Slice 1 — tracer bullet: pending Gate 4

## Gate 1 approval — 25 September 2026

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
| `02-architecture.md` | **Gate 2 doc** | draft written 25 Sep — decisions D1–D10, endpoints, data, flows, Gate A spike questions; awaiting user approval |
| `03-program-design.md` | **Gate 3 doc** | not yet written |
| `04-slices.md` | **Gate 4 doc** | not yet written |
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
- **Open question from `docs/DESIGN_PRINCIPLES.md` (re-verified 22 Sep):** our internal audit—not an organiser scorecard—finds the current scope weak on platform advantage, while current competitors already occupy broad follow-up and cohort monitoring. The narrower proposal is one application-owned multi-day episode, one WorkBuddy scheduled reassessment/resume path, and an explicit measured abstention outcome. It is unestimated, access is unproved, and it must face the fixed-card + NurseFirst baseline. Not approved; Gate 1 remains open.
- Mandarin and voice are accessibility modes. English text remains the auditable reference until bilingual clinical content is reviewed.
- Provisional persona: Mei, 72, Mandarin-preferring, with remote daughter support. The respiratory-symptom recommendation remains an injected fixture until clinical review.
- **No asset may name a real healthcare facility.** The fixture provider is fictional and labelled.
- No implementation code may be written before Gate 4 approval.
- Gate 2 draft (`02-architecture.md`, 25 Sep) pins D1–D10: Python+FastAPI default (reversible only at the Gate A spike), pure domain core, append-only clinical record, derived closure, baseline arm first-class, abstention deterministic, scheduler module dark until Gate A passes, voice deferred and isolated. **The Gate A access spike is due 26 Sep** with a pre-recorded fallback decision.
- The repository has commits on `main` and `care-relay-adversarial-review` (both at `9a1f332`); push to origin is blocked on missing GitHub write credentials — user must authenticate or push themselves.
