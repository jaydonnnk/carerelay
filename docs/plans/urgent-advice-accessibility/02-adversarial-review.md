# CareRelay independent adversarial review

Research cut-off: **21 September 2026**. This is a product-strategy review, not Gate 1 approval or implementation authorization. Scores are planning judgments against the public rubric; the detailed healthcare rubric remains unavailable.

## A. Brutal verdict

**REFRAME — moderate-high confidence.**

Keep the CareRelay identity, but stop presenting “truthful unresolved handoff” as the product. Make the product a **closed-loop confirmation of urgent advice**:

1. the critical action and deadline are read back in the patient’s own words;
2. a mismatch is repaired without grading the patient;
3. operational attempts never become false completion;
4. the original deadline and next responsible person stay visible until stronger evidence arrives.

The handoff ledger is supporting safety infrastructure. The human headline is: **“CareRelay catches the moment a person thinks tomorrow is safe, then refuses to pretend help is arranged when nobody accepted the case.”**

### Three strongest reasons

1. **The broad category is occupied.** [Clearstep](https://www.clearstep.health/) already combines protocol triage, navigation and booking; [Infermedica](https://infermedica.com/solutions/follow-up) links triage to reassessment and care services; [Hippocratic AI](https://hippocraticai.com/ai-front-door/) markets comprehension-sensitive conversations, caregiver coordination, barrier handling and nurse escalation; [Luma Health](https://www.lumahealth.io/newsroom/company-news/luma-expands-ai-powered-patient-outreach-giving-health-systems-more-ways-to-close-care-gaps-and-fill-schedules/) markets persistent outreach and EHR rebooking. The visible CareRelay bundle is not novel.
2. **The specific failure is plausible and measurable.** Singapore research found limited health literacy in 42.0% and marginal health literacy in 20.4% of a national sample of 2,327 older adults, but this supports a comprehension problem—not CareRelay’s specific false-completion hypothesis. A card-versus-CareRelay test can establish or kill that narrower claim. [Primary study](https://www.sciencedirect.com/science/article/pii/S1551741123000700)
3. **A narrow proof can still be built before 16 October.** A text-first read-back repair plus one simulated failed request is materially smaller than respiratory self-triage, Mandarin voice, caregiver orchestration, reassessment and booking integration combined.

### Three strongest falsifiers

1. A concise bilingual instruction card plus direct booking link and NurseFirst fallback produces equal or better action/deadline recall, completion belief and task time.
2. Three to six target older-adult/caregiver dyads do not exhibit the timing or false-completion failure, or find the read-back burdensome, shaming or confusing.
3. No clinician-approved bounded pathway, no genuine CodeBuddy/WorkBuddy proof, or no working runtime/tool-failure slice exists by the internal kill date. In that case CareRelay is a workflow mockup, not a self-triage prototype.

## Exact judging and submission requirements

- Submit by **16 October 2026**; finalists are announced **23 October**; Demo Day is **3 November, TBC**. Exact cutoff time and time zone are unknown.
- Team of **1–3**, Singapore-based; one registration per team; choose **one** case study and state it at presentation start.
- The project must be original and built on at least one of **CodeBuddy or WorkBuddy**. Usage proof is mandatory; without it, the project does not proceed to scoring.
- Required: title; blurb **under 10 words**; project description covering users/scenario/value, source of pain points, business and technical architecture, prompt role, and quantified or clearly defined impact; development conversation history; at least **three** CodeBuddy/WorkBuddy chat screenshots; cover image.
- The cover is specified as **16:9**, while 380×216 is only recommended and is not exact 16:9. Use a true 16:9 asset.
- Challenge 1 says the solution should include a **live walkthrough**, architecture/trust-boundary diagram with key trade-offs, and complete GitHub source. The generic table calls challenge-specific extras optional; submit all three rather than exploit the conflict.
- Optional: 5–8 minute video. Optional live link earns bonus points.
- Public judging: ten dimensions worth ten points each. Detailed healthcare criteria are promised after registration and remain unknown.
- Conversational assessment, navigation, warning signs, abstention, self-management, reassessment and personalization/fairness are published guidance, not seven independent pass/fail gates.

Evidence: `docs/CHALLENGE_REQUIREMENTS_JUDGING.md:26-47,124-213`, `docs/PLAN.md:16-36`, and `CareRelay.md:28-47`.

### Current submission blockers

No mandatory organiser-usage proof, executable application source, clinical review, user evidence, runtime trace, final trust-boundary diagram, cover asset or live walkthrough is present. Gate 1 remains pending and Gates 2–4 have not begun.

## Market and baseline reality

### Direct competitors

| Competitor | Verified overlap | Honest residual gap |
|---|---|---|
| Clearstep | Conversational symptom assessment, rule-based disposition, care routing and scheduling; Mount Sinai reports a deployed integrated service. | No public evidence found for an immutable clinical deadline or a patient-visible evidence hierarchy across retries. Absence is not proof. |
| Infermedica | Triage, linked follow-up, changed/new symptom reassessment, questions about whether care was scheduled/received, and booking integration capability. | Integration is client-specific; no public deadline invariant was found. |
| Hippocratic AI | Scheduling, nurse triage, education, caregiver coordination, transport-barrier alternatives, external coordination, red-flag nurse escalation and multi-call memory. | Many claims are vendor-reported; no public exact CareRelay contract was found. |
| Luma Health | Persistent outreach, cancellation/no-show recovery, conversational rebooking and EHR booking. | Strong operational overlap, but not acute self-triage; reported outcomes are scheduling rather than clinical outcomes. |
| Ada / UCSD protocol research | Hybrid conversational plus governed clinical reasoning and traceable protocol paths. | Architecture novelty is gone. CareRelay must win on a patient outcome, not “LLM plus deterministic rules.” |

The relevant “Luma” is **Luma Health (`lumahealth.io`)**, not an unrelated similarly named service.

### Singapore services and simple substitutes

- [NurseFirst](https://www.moh.gov.sg/newsroom/nation-wide-trial-to-refer-non-life-threatening-995-calls-to-the-nursefirst-helpline/) is the hardest local substitute: trained nurses with emergency-physician oversight provide free symptom triage and care guidance daily from 8am–11pm. It beats CareRelay on clinical authority and flexible human interpretation.
- [SCDF 995](https://www.scdf.gov.sg/home/about-scdf/emergency-medical-services) provides 24-hour emergency triage and dispatch. It must never be delayed by teach-back or navigation. SMS 70995 already serves registered deaf, hard-of-hearing and speech-impaired users.
- [HealthHub appointments](https://support.healthhub.sg/hc/en-us/articles/60045617129625-Book-and-Manage-Appointments-Easily) and [caregiver access](https://support.healthhub.sg/hc/en-us/articles/60563023622681-Manage-Your-Loved-Ones-Health-with-Ease) already support booking, rescheduling and authorized caregiver action for public care. These are explicitly non-urgent booking tools.
- [GPFirst](https://www.moh.gov.sg/seeking-healthcare/getting-medical-help/gpfirst/) already routes mild/non-emergency cases through GPs and onward to ED/UCC when needed.
- 1777 is non-emergency transport, not triage, and [ceases on 1 January 2027](https://www.moh.gov.sg/newsroom/1777-non-emergency-ambulance-hotline-to-cease--from-1-january-2027/). Do not hard-code it.
- A bilingual card, direct booking link, checklist, nurse callback and caregiver callback are strong baselines, not deliberately weak controls.

### What is actually differentiated

| Classification | Finding |
|---|---|
| Genuine differentiation hypothesis | One tested contract spans comprehension and execution: critical action/deadline must survive read-back, retry, restart and failed handoff without false completion. |
| Feature bundling | Triage + teach-back + multilingual voice + caregiver coordination + booking + reassessment + follow-up. Competitors already sell most or all of these pieces. |
| Prior art | Teach-back; deterministic disposition; status lifecycles; idempotent retries; caregiver delegation; linked reassessment; “acknowledged is not resolved.” |
| Untested hypotheses | Older adults commonly make this exact error; PlanBack repairs it; the ledger changes decisions; users accept the burden; the combination beats a card and human call. |
| Not demonstrable by 16 Oct | Clinical safety, avoided admissions, national scalability, real healthcare integration, reliable Mandarin clinical voice, better outcomes, regulatory readiness. |

## B. Diagnosis of the four weak dimensions

The supplied 7/7/6/7 scores are conditional forecasts, not current evidence. Strict artifact-only scores are lower.

| Dimension | Current weakness | Why weak / missing evidence | Best improvement | Expected after proof | Estimate and dependencies | Risk of making it worse |
|---|---|---|---|---:|---|---|
| Impact & Relevance | Broad health-literacy evidence substitutes for evidence of the actual failure. | No frequency, severity or observed examples of deadline misunderstanding or false completion. | Measure one decision outcome against a fixed card: correct action, deadline, next owner and whether care is arranged. Record raw dyad outcomes. | 5→7–8 | 10–16 h plus recruitment; 3 minimum, 6 target dyads. | Overfitting six scripted users or implying clinical outcomes. |
| Human-Centered Design | Fictional persona and static wireframes; no observed workflow. | Mei bundles age, Mandarin, voice, caregiver, respiratory danger and booking failure to justify features. Draft transcript is judged before confirmation in Screen 2. | Text-first PlanBack; counterbalanced card comparison; observe shame, burden, consent and caregiver role. Fix transcript order. | 4→8 | 14–24 h plus native review if Chinese remains. | Teach-back feels like a test; caregiver mode can create coercion/privacy problems. |
| Feasibility | No reviewer, approved protocol, organiser access, runtime, adapter, tests or owner. | Current scope combines several hard dependencies; state design mixes execution and evidence in one sequence. | One approved/injected recommendation, one WorkBuddy tool call, one deterministic parser, one failed simulated adapter, two-axis evidence state, restart test. | 3→6–7 | 55–85 h total slice, plus reviewer/access; evaluation overlaps. | A simulated adapter may be oversold; narrowing after disposition weakens Challenge 1 coverage. |
| Innovation & Creativity | The visible feature bundle is prior art. | “Truthful unresolved” is a state label, not a demonstrated novel behavior. | Import FAA read-back/hear-back, incident acknowledgement-versus-resolution and payment processing-versus-settlement as donors; prove the healthcare-specific invariant under failure. | 3→7 | 18–30 h of the slice for failure harness and baseline comparison. | Judges see enterprise plumbing; status complexity overwhelms the user. |

## C. Competing directions

Scores are conditional ranges for a working, tested prototype, not earned outcomes. Weak-dimension vector is **Impact / HCD / Feasibility / Innovation**.

### 1. CareRelay Closure Contract — recommended

- **Pitch:** Care advice is not closed until the critical plan is understood and the next step has the right evidence.
- **Target user:** Older adult acting alone or with a chosen caregiver after one approved self-triage recommendation.
- **Exact problem:** The patient believes a later deadline is acceptable or assumes a click/message means help is arranged.
- **Creative mechanism:** [FAA read-back/hear-back](https://www.faa.gov/air_traffic/publications/atpubs/atc_html/chap2_section_4.html) for action/deadline; [PagerDuty](https://support.pagerduty.com/main/docs/incidents) semantics where acknowledged is not resolved; [Stripe](https://docs.stripe.com/api/payment_intents) semantics where processing is not succeeded. These donor mechanisms are prior art. The possible novelty is their clinically constrained, patient-visible contract and measured advantage.
- **Why it is not already ordinary:** Competitors advertise the component capabilities, but no reviewed primary source exposed this exact invariant. That is a research gap, not a market-vacancy claim.
- **Five-minute demo:** A reviewed plan says “today before 6.” Mei says “tomorrow.” PlanBack repairs only the deadline. A simulated clinic rejects the request; the timer and next owner persist; app restart and duplicate callback do not turn failure into success.
- **Strongest substitute:** Bilingual action card + direct booking link + NurseFirst or caregiver callback.
- **Required evidence:** Clinician-reviewed reference plan; 3–6 target dyads; card comparison; fault-sequence tests; zero false critical correction; raw task time, recall and false-arranged beliefs.
- **Build estimate:** 60–90 person-hours plus 10–16 evaluation hours; WorkBuddy access and clinical review are external dependencies.
- **Why it may win:** One coherent human failure, visible AI repair and inspectable technical integrity.
- **Why it may fail / new risks:** Feels like a quiz; delays action; false paraphrase correction; technical semantics remain emotionally cold.
- **Kill test:** Kill if the fixed card performs equally with lower burden, any critical correct statement is falsely “repaired,” or emergency action is delayed.
- **Conditional score:** **72–77/100**; weak dimensions **8 / 8 / 7 / 7**.

### 2. Evidence Before Advice — assessment-side pivot

- **Pitch:** Improve the reliability of facts entering triage instead of producing a more fluent recommendation.
- **Target user:** A patient or caregiver reporting a critical measurement or vague symptom without clinical help.
- **Exact problem:** Governed rules are still unsafe if AI mishears a number, negation, time, unit, reporter or measurement method.
- **Creative mechanism:** Industrial measurement traceability: retain source, reporter, time, unit, method, confirmation and contradiction state for every critical fact; missing never becomes “no”; unresolved conflict triggers clarification or abstention.
- **Why it is not already ordinary:** [Ada](https://about.ada.com/press/patent-llm-clinical-safety-layer/), [UCSD protocol-grounded research](https://today.ucsd.edu/story/new-conversational-ai-tool-uses-trusted-medical-protocols-to-help-people-decide-when-to-seek-care) and [TytoCare](https://www.tytocare.com/consumers/) occupy conversational reasoning and guided exams. A low-tech, provenance-first observation gate is less visibly standard, but not proven unique.
- **Five-minute demo:** A stale/recalled measurement conflicts with a new report. The system refuses to resolve the conflict silently, guides a permitted re-check and abstains if evidence remains unreliable.
- **Strongest substitute:** Nurse-led scripted assessment; structured checklist; TytoCare where hardware/service access exists.
- **Required evidence:** Clinician-authored cases for units, negation, staleness, contradictions and missing facts; usability burden; zero silent critical-fact conversions.
- **Build estimate:** 45–75 hours plus immediate clinical review.
- **Why it may win:** Stronger innovation thesis and a real safety failure before disposition.
- **Why it may fail / new risks:** Higher regulatory and clinical burden; coached observations may be mistaken for clinical-grade measurements.
- **Kill test:** Kill after any silent conversion of missing/contradictory information into a negative finding or disposition, or if a checklist performs equally.
- **Conditional score:** **68–74/100**; weak dimensions **8 / 7 / 5–6 / 8**.

### 3. NurseFirst Relay — human-service reframe

- **Pitch:** AI prepares and preserves the handoff around human triage instead of claiming clinical authority.
- **Target user:** Older adults and caregivers calling NurseFirst for non-life-threatening symptoms.
- **Exact problem:** A caller may omit critical context, misunderstand the nurse’s deadline or lose the plan after the call.
- **Creative mechanism:** Before-call source-labelled brief; after-call read-back and action receipt; no recording, call interception or integration claim without permission.
- **Why it is not already ordinary:** NurseFirst supplies clinical triage, and HealthHub supplies booking/caregiver access. No public source shows a persistent patient-owned read-back-and-receipt layer between them, but a paper note may already be enough.
- **Five-minute demo:** CareRelay prepares a concise symptom brief; a simulated nurse issues a same-day plan; the patient reads it back; a booking failure stays unresolved and routes back to a human option.
- **Strongest substitute:** NurseFirst + paper notes + caregiver + HealthHub/direct GP booking.
- **Required evidence:** Nurse-reviewed script, user comprehension study, privacy/consent review, proof that the companion reduces omission or misunderstanding without extending call burden.
- **Build estimate:** 35–55 hours plus 10–16 evaluation hours; real NurseFirst integration is not assumed.
- **Why it may win:** Best feasibility and clearest responsible-AI boundary.
- **Why it may fail / new risks:** Looks like a note-taking wrapper; weaker self-triage alignment; transcription/privacy errors; no permission to integrate.
- **Kill test:** Kill if a one-page call-preparation card and human callback perform equally, or if users/nurses reject the extra workflow.
- **Conditional score:** **66–72/100**; weak dimensions **8 / 8 / 7 / 5–6**.

## Scenario verdict

The **Mei/Mandarin respiratory scenario is convenient, not justified as best**.

- It activates too many features at once and reads as a constructed persona.
- Respiratory language is clinically brittle: SCDF lists breathlessness as an emergency while cough can be non-emergency. A single interpretation error can reverse the route.
- “Suddenly confused” makes 995 obvious; a static rule can win that scene, so it does not prove valuable AI.
- Mandarin text is accessibility work, not innovation. Mandarin voice has no native clinical review, Singapore-accent evidence or working integration.

Keep Mei only as a falsification case. Let a clinician choose one bounded complaint using four criteria: a credible same-day window, more than one legitimate non-emergency route, a realistic access barrier, and no need for unvalidated device measurements or dosing. Until then, use an explicitly injected recommendation fixture. Start English text-first; restore reviewed Chinese text only if recruited users justify it.

## Emotional verdict on truthful unresolved handoff

As a state ladder, it is technically elegant and emotionally weak. “Care evidenced: NO” sounds like audit software.

The meaningful scene is false closure while time still matters:

> Mei thinks her daughter arranged care. Her daughter only received a message. The clinic rejected the request. No one owns the next step, and 45 minutes remain.

The interface should show only:

1. **Help is not arranged.**
2. **You or [named person] must act now.**
3. **Before 6:00 PM.**
4. **If this route fails, call [approved human route].**

Keep the detailed event/evidence ledger inspectable for judges, not as the patient’s main UI.

## D. Fixed-baseline comparison

| Baseline | What it already wins | What Closure Contract must prove |
|---|---|---|
| Bilingual instruction card | Lowest burden; preserves exact action, deadline, red flags and fallback. | Adaptive repair catches additional critical errors without shame or delay. |
| Direct booking link | Fastest route to a real booking confirmation when availability exists. | Handles failure, transport/caregiver barriers and preserves the deadline; never treats a click as care. |
| Checklist | Cheap, deterministic and testable for known barriers. | Natural-language repair adds value beyond fixed questions; otherwise remove AI. |
| Human nurse/caregiver callback | Best at ambiguity, emotion and flexible escalation; NurseFirst has clinical authority. | Adds durable state and scale without pretending to replace judgment. Human callback remains the safety owner. |
| Current CareRelay plan | Broad, impressive narrative and strong safety intentions. | Reframed version is narrower, working and evidenced. Current plan loses because nothing is implemented and the category bundle is crowded. |

## E. Prioritized recommendation

### Ranked by point gain, evidence, hours and dependency risk

| Rank | Change | Likely point gain | Evidence strength | Build effort | Dependency risk |
|---:|---|---:|---|---:|---|
| 1 | Run PlanBack/card comparison on a clickable text prototype before building voice or booking. | +4 to +7 across Impact/HCD/Innovation/UX | Direct user-task evidence | 20–35 h incl. prep/analysis | Medium: recruitment |
| 2 | Implement one two-axis Closure Contract and failure harness: execution state separate from evidence state; fixed deadline; restart, duplicate and rejection tests. | +5 to +9 across Tech/Feas/Demo/RAI | Executable traces | 35–55 h | Medium: runtime access |
| 3 | Secure one clinician-reviewed fixture and choose the complaint on reviewability, not drama. | +3 to +6 across Impact/Feas/RAI | Necessary safety provenance | 6–12 h internal; external lead time unknown | High: reviewer |
| 4 | Produce mandatory usage proof and submission traceability. | Avoids disqualification; +2 to +4 overall | Direct organiser evidence | 8–14 h | Medium: account/registration |
| 5 | Add reviewed Chinese text only after need is observed. | 0 to +2 UX/HCD | Native/user evidence | 8–16 h | Medium-high |

### Three changes to implement

1. **PlanBack:** action/deadline read-back with deterministic critical-field comparison and bounded repair.
2. **Closure Contract:** plain-language unresolved state backed by separate execution/evidence axes, absolute deadline and failure/restart tests.
3. **Baseline evaluation:** same clinical content and options in a clear card; counterbalanced target-user tasks; raw results and task time.

### Three things to cut

1. Mandarin voice from the judged demo.
2. Broad respiratory/COVID intake and the sudden-confusion finale from the hero story until a clinician selects it.
3. The five-state ledger exposition in the patient UI. Keep it in judge evidence; show patient, owner, action and deadline plainly.

### Three questions requiring real user or clinician evidence

1. Do target dyads actually misremember the action/deadline or falsely believe care is arranged, and does PlanBack/Closure Contract beat the card?
2. Which single complaint can a qualified reviewer approve with a meaningful same-day window, safe alternatives and clear abstention boundaries?
3. Do older adults accept read-back and caregiver sharing without shame, coercion or extra anxiety, and which language/input mode do they actually need?

## F. Final score

Mandatory organiser-usage proof is absent, so the project currently risks **not proceeding to scoring at all**. If the static artifacts were scored anyway, an evidence-backed estimate is **39/100**, not 78.

| Dimension | Current artifacts | Realistic implemented | Optimistic ceiling | Evidence required for increase |
|---|---:|---:|---:|---|
| Impact & Relevance | 5 | 7 | 8 | Observed target-user failure; fixed-baseline advantage; bounded local impact metric. |
| Human-Centered Design | 4 | 8 | 9 | 3 minimum / 6 target dyad sessions; documented changes from failures; consent and burden evidence. |
| AI Interaction | 3 | 7 | 8 | Working adaptive interpretation/repair that beats the checklist and abstains on uncertain critical facts. |
| Technical Execution | 2 | 7 | 8 | Genuine organiser runtime/tool trace; two-axis state; idempotency; restart, stale and duplicate tests. |
| Feasibility | 3 | 6 | 7 | Account/access spike; reviewer; measured latency/cost; named operating owner; honest simulation boundary. |
| Demo & Storytelling | 4 | 8 | 9 | Live non-hard-coded misunderstanding repair plus injected service failure and visible before/after baseline. |
| Innovation & Creativity | 3 | 7 | 8 | Mechanism-level competitor map plus measured advantage of the invariant, not a feature list. |
| UX & Accessibility | 5 | 8 | 9 | Task success, mobile/keyboard/screen-reader checks; reviewed language only; no false transcript interpretation. |
| Responsible AI & Ethics | 6 | 8 | 9 | Full pathway review, abstention tests, consent enforcement, data/retention statement and subgroup cases. |
| Overall Quality | 4 | 7 | 8 | Mandatory submission completeness and a traceable chain from need → behavior → evidence → bounded claim. |
| **Total** | **39** | **73** | **83** | All increases are conditional on delivered evidence. |

The optimistic ceiling assumes unusually clean execution. It does not include clinical validation, proven health outcomes or real national-scale integration. The previous **78/100** is a plausible upper-middle target only after substantive delivery; it is not a current score.

## What makes judges say the four required sentences

- **“This matters.”** A user test shows false closure or deadline misunderstanding on the fixed baseline, and CareRelay prevents it while time remains.
- **“This is designed around real people.”** Target dyads change the flow; the UI names the person, action and deadline instead of exposing a workflow engine.
- **“This could actually operate.”** One real organiser tool failure, one persisted episode, one reviewed clinical fixture, measured latency/cost, and explicit simulated boundaries.
- **“I have not seen this exact behaviour before.”** A live failure proves the same plan survives misunderstanding, service rejection, restart and duplicate callback without becoming falsely complete.

## Immediate kill dates

- **By 23 September:** registration/criteria and CodeBuddy/WorkBuddy access confirmed; reviewer outreach has a concrete answer.
- **By 26 September:** text-first PlanBack + Closure Contract tracer works end to end. Otherwise cut everything except the card comparison.
- **By 2 October:** at least three target dyad sessions completed. Otherwise make no human-centered superiority claim.
- **By 6 October:** feature freeze. No voice, additional languages, extra agents or real integrations after this date.

If the card wins, do not decorate CareRelay. Either narrow it to internal safety infrastructure or pivot to NurseFirst Relay.
