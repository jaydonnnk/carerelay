# CareRelay — Plan (updated 21 September 2026)

Planning document for the **Tencent Cloud "AI CAN DO IT" Hackathon Singapore 2026**, Healthcare Track, **Challenge 1: "AI Grandma Knows Best: Intelligent Self-Triage and Care Navigation"**.

This replaces the 16 September session-transfer version. It consolidates two reviews: an evidence and feasibility audit, and a refactor that prioritises organiser-native capability.

**21 September revision:** PlanBack (§5.1) and the Closure Contract (§6.1) are now part of the plan, following the independent adversarial review of 21 September. The single-ladder state model in §6 has been corrected to two independent axes. See `docs/reviews/gate2-adversarial-review-round1.md` and `03-planback-closure-contract.md`.

Every claim below is labelled:

- **[verified]** — supported by the cited source as of 17 September 2026.
- **[vendor claim]** — documented or advertised by a company; not independently validated.
- **[hypothesis]** — our strategic judgment; not established.
- **[unknown]** — not established either way.

No implementation has been authorised. No accounts, credentials, clinical review, user research or external integrations exist yet.

---

## 1. Competition facts

| Item | Status | Evidence |
|---|---|---|
| Challenge | Healthcare Challenge 1, one case study only | Handbook p27 |
| Eligibility | Teams of 1–3, all participants Singapore-based, one registration per team | Handbook p37 |
| Submission | 16 October 2026; finalists 23 October; Demo Day 3 November (TBC) | Handbook p36 |
| Exact cutoff time / time zone | [unknown] | Not stated |
| Healthcare-specific judging criteria | [unknown] | Promised after registration |
| Public rubric | Ten dimensions, ten points each | Handbook p38 |
| Organiser product requirement | Original project built on CodeBuddy or WorkBuddy; proof mandatory | Handbook p35 |
| Development-chat screenshots | At least three required, listed separately from the general proof paragraph | Handbook p35 |
| Credits | 1,000 CodeBuddy/WorkBuddy credits per person offered | Handbook p39 |
| Team registration status | [unknown] | Kickoff RSVP closure is not evidence that team registration is closed |

Wording conflicts and how this plan resolves them:

- The challenge's feature list is **guidance**, and the handbook explicitly permits meaningful alternatives. It is the strongest alignment signal, not seven pass/fail gates.
- Challenge 1 lists a live walkthrough, architecture/trust-boundary diagram and GitHub source; the generic table calls challenge-specific extras optional. **We provide all three.**
- Miora appears in participation instructions but the eligibility paragraph requires CodeBuddy or WorkBuddy. **We follow the stricter requirement.**
- “16:9” and “380×216” are not identical; we submit a true 16:9 image (e.g. 1280×720).

---

## 2. Direction

**Keep CareRelay, reframed.** Not a chatbot that gives advice, and not a platform demo wearing a healthcare story.

> **CareRelay is a patient-facing self-triage service for community-dwelling older adults and their family caregivers. It assesses the problem, gives a clinician-governed recommendation, checks whether the person understood it and can actually carry it out, and keeps unresolved needs visible when recovery fails.**

### What is genuinely ours to claim

**One tested contract, not a feature bundle:** the critical action and deadline must survive read-back, retry, restart and failed handoff **without false completion**.

| Claim | Status |
|---|---|
| **PlanBack** — a confirmed restatement is compared against the approved plan by **deterministic code**, and a mismatch is repaired field by field | [hypothesis]; donor prior art is aviation read-back/hear-back |
| **Closure Contract** — an episode cannot be marked resolved without evidence, and no operational retry may move the clinical deadline | [verified as a design principle]; implementation unproven |
| Checks understanding *and* practical ability separately, and repairs the specific failure | [hypothesis] |
| Never silently downgrades clinical urgency to resolve an operational problem | [verified as a design principle]; implementation unproven |
| Separates execution status from evidence status, so “booked” never becomes “cared for” | [verified as a design principle]; FHIR Task is prior art for lifecycles |
| Exposes an unaccepted or failed handoff instead of reporting success | [hypothesis] |
| Organiser-native operation (managed runtime, sessions, tools, release configuration) | [verified capability]; account access unproven |

**Honest boundary — what the platform does and does not supply.** PlanBack and the Closure Contract are application logic and do **not** require WorkBuddy. WorkBuddy's genuine contribution is the coordinator, the real tool call, its real failure event, and session resume. We claim the platform as the **execution substrate** — not as the source of the clinical state, the deadline invariant, consent, or the closure rule. This is a provisional Gate C answer, not a pass; native access and a demonstrably central execution loop remain unproved.

See `docs/plans/urgent-advice-accessibility/03-planback-closure-contract.md` for the full specification and feasibility assessment.

### What we must NOT claim

- “World-first,” “no competitor does this,” or an empty market. [overstated]
- Clinical validation, improved health outcomes, or avoided admissions. Nothing is validated.
- **Any cognitive-improvement, cognitive-training, “keep your mind sharp” or dementia-prevention claim.** Meta-analyses of cognitive training find **no far transfer** — training improves the trained task and little else (*Perspectives on Psychological Science*, 2022). The FTC settled with Lumosity for **$2 million in 2016** over exactly this claim. The fading scaffold in §5.3 improves retention of a specific plan; it does not make anyone smarter or slow decline.
- **Any cognitive screening, risk score, or diagnostic output.** Restatement accuracy is not a cognitive assessment and must never be presented as one.
- That deterministic rules are safe by themselves. Rules can misapply a misheard fact.
- That “not diagnosis” removes medical-device considerations. HSA assesses intended purpose and function.
- That using native features of the platform is itself innovation.
- That a simulated integration proves real-world readiness.

### Criteria we now use for our own decisions

1. **Challenge and safety fit** — does it advance self-triage, appropriate next steps and knowing when humans must take over?
2. **Organiser-native advantage** — which platform capabilities materially shape the product rather than merely host it?
3. **Patient value** — does that produce a better experience or outcome than a simpler alternative?
4. **Current opportunity** — what is newly practical, and what have competitors already made ordinary?
5. **Ambition with a demonstrable slice** — a substantial vision plus a small, honest proof of its central mechanism.

These are our internal selection criteria, **not** additional organiser requirements.

**21 September, later:** the criteria above were sharpened into four tests — load-bearing, earliness, theme alignment, ambition — and applied to this plan in `docs/DESIGN_PRINCIPLES.md`.

**That audit finds this plan weak on the internal load-bearing test.** In our constructed nine-surface taxonomy—not an organiser scorecard—two capabilities carry real weight, six are unused and one is build-only. The plan's own words in §2 and §3 concede that PlanBack and the Closure Contract do not require WorkBuddy and that another stack could reproduce the product.

The audit's corrected finding is that **the scope cuts in §7 removed every longitudinal surface**. The organiser's optional examples include *"re-checks every 8 hours"* and *"daily logs for 10 days… compared to baseline"*, so one scheduled reassessment slice is strongly theme-aligned. The brief does not require WorkBuddy scheduling, session persistence or cohort concurrency. Application-owned episode state remains authoritative; WorkBuddy may schedule, invoke and resume it.

Read `DESIGN_PRINCIPLES.md` §8 before treating §6 as settled. Gate C remains open. The proposed repair must be estimated and must not replace Gate B's fixed-baseline kill test.

---

## 3. Evidence

### Singapore context

| Finding | Status |
|---|---|
| Health literacy: 42.0% limited, 20.4% marginal, 37.7% adequate among 2,327 Singaporeans aged 65+ (BRIEF instrument, 2023) | [verified] — instrument classifications, **not** triage error rates |
| One in four older adults reportedly with low eHealth literacy (361 adults ≥65, author-reported, March 2026) | [vendor claim/author-reported]; full methods not accessed |
| NCSS reports one in four caregivers needing additional services | [verified institutional report]; exact population unclear |
| Prevalence of CareRelay's specific failed-plan problem | [unknown] |
| Which failure dominates — assessment, comprehension, access, follow-through | [unknown] |
| 995 is emergencies only; ambulance does not confer priority | [verified] SCDF |
| NurseFirst: 6262 6262, 8am–11pm daily; **not 24/7** | [verified] MOH, Feb 2026 |
| 1777 non-emergency ambulance ceases 1 January 2027; not clinical triage | [verified] MOH |
| CHAS is a subsidy scheme; HealthHub is access/records, not an urgency level | [verified] |

### Medical and safety evidence

| Finding | Status |
|---|---|
| ChatGPT Health structured stress test: 60 clinician-authored vignettes, 960 responses; 52% undertriage among gold-standard emergencies | [verified] Nature Medicine, published 23 February 2026 |
| Reason2Decide T5-Large triage macro-F1 **60.58**; the ~96% figure is PubMedQA accuracy on a mixed artificial/human-labelled test set; authors require human verification | [verified] arXiv 2512.20074v2 |
| MedQAbstain: LLMs systematically overcommit and rarely abstain under medical uncertainty | [verified] ACL 2026; MCQA benchmark, not a triage validation set |
| Human teach-back improved comprehension of discharge instructions in one US ED trial (n=254); no distal outcomes | [verified]; does not validate automated comprehension scoring |
| Mount Sinai / Clearstep: deterministic rules for disposition, probabilistic language interpretation, user confirmation step, sampled clinician concordance review | [vendor claim from case study]; full figures inaccessible; author conflicts disclosed |

Reusable mechanisms (not novel claims): separate language interpretation from deterministic disposition, confirm the interpreted complaint with the user, ground explanations in the actual decision trace, measure intent before triage, and instrument follow-through carefully.

### Competitive position

Categories are occupied. [verified — vendor claims, all accessed 17 September 2026]

| Competitor | Overlap |
|---|---|
| Hippocratic AI | Barrier-sensitive orchestration, telehealth when transport blocks, caregiver coordination, escalation to triage nurses, follow-up loops |
| Luma | Missed/cancelled appointment recovery and EHR rebooking (September 2026); 2.3× is vendor-reported scheduling, not clinical outcome |
| Clearstep / Infermedica | Protocol-based triage, navigation, scheduling, linked follow-up reassessment |
| Ada | Separates clinical reasoning from the conversational layer |
| TytoCare | Device-supported guided examination |
| Lexi / NoBarrier | Medical interpretation across languages |
| Trisotech | Executable care processes, responsibility assignment, decision logic |

**No competitor was verified to provide the complete combination** of absolute clinical deadline preservation, separated execution/evidence states and truthful unresolved handoffs. Absence of public documentation is **not** proof they lack it.

### Organiser technology

[verified — public documentation, access date 17 September 2026]

| Surface | Capability | Caveat |
|---|---|---|
| WorkBuddy managed agents | Programmatic agents, runtimes, sessions, streaming | Account/region/quota access unverified |
| Agent versions | Publishing a version does not activate it; activation affects **new** sessions | Existing-episode pinning and migration are application work |
| MCP, skills, hooks | Tool/skill configuration, tool failure events | A hook is not automatically an authorisation barrier |
| Checkpoints | Runtime snapshot and restore | Not external-action rollback or exactly-once execution |
| Managed scheduler | Enterprise-owned; **5-minute minimum** recurring interval | Never place urgent escalation on it |
| CodeBuddy SDK | Embeddable host-running runtime, Preview; MCP, permissions, hooks, resumption | Filesystem settings are not loaded by default |
| TRTC speech | ASR lists 30 languages; native TTS coverage differs | No verified Singapore-accent or clinical accuracy |
| Miora | Creative studio for visual assets | No confirmed general runtime API |

**Strategic reading:** the platform supplies execution primitives. Clinical meaning, episode governance, consent and safety constraints remain our responsibility. Another stack could reproduce the product; the honest claim is “designed around WorkBuddy's operating model,” not “impossible elsewhere.”

---

## 4. Scope

### Population and scenario

- **Population:** community-dwelling older adults (65+), assisted where desired by a remote family caregiver, English text first.
- **Scenario:** one narrow, clinician-reviewed complaint pathway. The previous painful-urination example is **provisional**, pending review of which complaint gives credible home-care, primary-care and emergency branches in a frail older adult.
- **Status:** no clinical reviewer, protocol permission or approved pathway exists yet. This is a gate, not a detail.
- **Cognitive framing does not change the population.** The adaptive scaffold in §5.3 is a mechanism, not a claim. Moving toward cognitive monitoring or screening would narrow the population to MCI or subjective cognitive decline and materially raise the regulatory stakes; that is explicitly out of scope.

### North star

A patient-controlled care episode, shared with permission, in which patient, caregiver and receiving services can all see the current recommendation, what is uncertain, what action is required and by when, who accepted responsibility, what actually happened, and what remains unresolved.

**The ambition is accountable continuity — not guaranteed access to care.**

### Demonstration boundary

| Real | Explicitly simulated | Out of scope |
|---|---|---|
| Organiser runtime execution, interpretation, state, permissions, failure handling, UI, evaluation traces | Clinic availability, booking receipts, caregiver messages, clinical service acknowledgements | Real patient triage, prescribing, EHR access, emergency dispatch, continuous monitoring, autonomous clinical decisions |

Every simulated element stays labelled simulated in screenshots, video and metrics.

---

## 5. Demonstration (the five-minute story)

One patient, one clinician-reviewed pathway, one caregiver, one simulated service, one interruption, one failed action.

1. A fictional older adult describes the problem vaguely.
2. The system clarifies critical information and presents the reviewed recommendation.
3. **PlanBack** asks them to say the plan back in their own words.
4. Their restatement reveals a **timing misunderstanding**.
5. The system repairs **only the mismatched field**, without turning the interaction into a quiz.
6. They also report a **practical barrier**.
7. A permitted tool workflow runs; a **real** organiser tool call fails.
8. The session is interrupted and resumed — state continues, and the clinical deadline does **not** restart.
9. The interface distinguishes **contact attempted**, **acknowledged** and **care evidenced**.

**Urgent guidance must appear before teach-back, navigation or caregiver acknowledgement, never after.**

Failure paths that should not be crammed into the live story — unacknowledged handoff, duplicate callback, clock change, consent revocation — are shown in inspectable test evidence.

### 5.1 PlanBack — read-back with a deterministic check

The patient restates the plan; **code, not a model, decides whether it matches.**

1. Present the approved plan: action, deadline, next owner, fallback.
2. Ask for a restatement in the patient's own words.
3. **If the input was voice, confirm the transcript first.** The transcript is never evaluated before the patient has confirmed or corrected it. *(This corrects a defect in the current wireframe 2, which evaluated a draft transcript directly.)*
4. Extract the three critical fields: `action`, `deadline`, `next_owner`.
5. Compare deterministically. `deadline` compares as a **time bucket**, never as prose — “tomorrow” resolves to a date and fails. `action` compares against a **closed vocabulary of action ids**. `next_owner` compares against the named party.
6. All fields match → record `understanding_confirmed` and continue.
7. Mismatch → repair **only the differing field**, then ask again. Maximum **2** repair rounds.
8. Still mismatched → **stop** and route to the approved human/emergency path. Never continue on an unconfirmed plan.

**The model interprets. Code decides.** A model grading comprehension can err in both directions, and a false “you understood” is a safety failure while a false “you did not” is a dignity failure. A boolean over extracted fields is auditable and reproducible in a test.

### 5.2 The recall hint ladder

Older users can freeze at a blank “tell me the plan” prompt, so the prompt escalates rather than shaming the patient. **The level used is recorded**, because a hint that contains the answer turns a comprehension check into a reading test.

| Level | What the patient sees | Recorded outcome |
|---|---|---|
| **H0** | The question alone: “In your own words — what will you do, and when?” | `recall_unaided` |
| **H1** | Structural cue only: three labelled slots — **What** · **When** · **Who helps** | `recall_scaffolded` |
| **H2** | The plan card is shown again, and **stays on screen until the patient hides it**. “Now say it back.” | `recall_cued` |
| **H3** | The plan is shown and the patient confirms it by choosing | `not_recalled` |

Rules:

- **H0–H2 must not display the critical fields.** H2 re-exposes the card and then removes it: that tests retention, not reading. **The removal is always the patient's own action** — see §5.2.1.
- **Every outcome records its level.** Without this, “she remembered” and “she read it off the screen” are indistinguishable and the evaluation is worthless.
- **H3 is an honest result, not a failure.** `not_recalled` routes to the human path and is reported as such. It is never dressed up as comprehension.
- **The patient is never trapped.** A persistent “show my plan” control reveals the full card at any time, and doing so records a cued outcome.
- **Tone is warm and unmissable; content is the constraint.** Large type, high contrast, plain words — but no leaking of the deadline, the action or the owner.
- **Hint content must never name a real healthcare facility.** The demo fixture uses a fictional, clearly-labelled simulated provider. Real institution names are excluded for privacy, reputational and simulation-honesty reasons.
- **The ladder fades as well as escalates.** Support is withdrawn when competence is demonstrated. See §5.3.

### 5.2.1 H2 — the card stays until the patient hides it

**Amended 25 September 2026, reopening Gate 1.** H2 previously showed the plan card for **five seconds** and then removed it automatically. That is replaced: **the card stays on screen until the patient chooses to hide it.**

**Why the change was forced.** A five-second timer is unreadable for an older adult with reduced processing speed, unusable for a screen-reader user, and un-extendable by anyone. The target population is community-dwelling older adults — the timer penalised exactly the people the product exists for. It also silently converted a comprehension aid into a speed test, which is a dignity problem as well as an accessibility one.

| Rule | |
|---|---|
| **The patient controls removal.** A single, large "Hide the plan · 隐藏" control. No timer, no countdown, no auto-dismiss anywhere in the product. |
| **Dwell time is recorded, not enforced.** `dwell_seconds` is stored on the `restatements` row and is displayed in the judge ledger. It is **never shown to the patient** and never changes what the patient may do next. |
| **Reading the card still records `recall_cued`.** Removing the timer does not turn H2 into a recall test — the outcome label is unchanged, and the recorded level continues to distinguish recall from reading. |
| **"Show my plan" always works.** The persistent escape at any level reveals the full card and records a cued outcome. |
| **Nothing in the product auto-hides, auto-advances or times out.** This is now a stated accessibility rule, not a local fix. |

**Why `dwell_seconds` is kept.** Without it, a five-second glance and a two-minute read produce an identical `recall_cued`, and the evaluation loses the ability to describe what happened. Recording it is evidence-gathering; acting on it would be a timer by another name.

### 5.3 Adaptive scaffolding — the ladder fades

The hint ladder is not only a safety prompt. It is a **scaffold that is withdrawn as competence is demonstrated** — an established technique in cognitive rehabilitation, not a brain-training game.

**Mechanism**

- A new or changed plan starts at **H1** (structured slots), so the patient is never dropped into a blank prompt.
- A successful **unaided (H0)** restatement lowers the starting support level for the next comparable plan.
- A failed or cued restatement **restores** support to the previous level.
- Support changes only on a **trend across episodes**, never on a single round, so one bad day does not produce a visible downgrade.
- Fading is invisible to the patient. There is no score, no streak and no progress bar.

This is **vanishing cues with errorless learning and spaced retrieval** — techniques carrying Class II–III evidence for teaching specific information to people with memory impairment (*International Psychogeriatrics* literature review). A legitimate, citable mechanism. It is not a claim that anyone becomes smarter.

**What this honestly achieves**

| Claimed | Not claimed |
|---|---|
| Better retention of *this specific plan* | Improved general cognition |
| Reduced dependence on the prompt over time | Prevention or delay of cognitive decline |
| Lower prompting burden for the caregiver | Any diagnosis, screening or risk score |
| An interaction that does not shame the patient | A therapeutic or rehabilitative benefit |

**The evidence does not support the stronger version.** Meta-analyses of cognitive training find **no far transfer**; the FTC settled with Lumosity for **$2 million in 2016** over precisely the claim that its games stave off age-related cognitive decline. Decline-prevention or “keep your mind sharp” wording is therefore **prohibited** in the product, the submission, the video and the pitch. See §2.

**Why the fading version is still worth building.** It changes the patient's experience from *being tested* to *being supported*; it reduces prompt dependence rather than creating it; and it gives the caregiver a lower-burden routine. All three are real, testable, and require no cognitive-improvement claim.

**Longitudinal signal — research direction, not a demo claim.** Repeated structured restatement of real-world plans is a candidate early indicator of cognitive change, because it measures the same person on a comparable task over months. This is a **monitoring hypothesis, not a training claim**, and it is **out of scope for the judged slice**: it needs a validated comparison instrument, clinical review, subgroup analysis, and a clear answer to what a false positive does to an anxious 78-year-old. Recorded here so the ambition is not lost, and explicitly **not** presented in the submission.

**Population note.** If the product moves toward cognitive monitoring, the population narrows from community-dwelling 65+ to mild cognitive impairment or subjective cognitive decline — a more clinically serious population with materially higher regulatory and ethical stakes. The demonstration keeps the broader population and treats the cognitive framing as a **mechanism**, not a **claim**.

**Language rule.** “Cognitive rot,” “brain training,” “use it or lose it” and similar framing must never appear in any user-facing text, asset or pitch. Describe what the product does: it helps someone remember their plan, and it stops prompting once they no longer need it.

---

## 6. Architecture and stack

### Responsibilities

```
Patient / caregiver interface (accessible, text-first)
        |
Application API — authorisation boundary
        |
        +-- Clinical policy: versioned, reviewer-approved decisions
        +-- Episode record: reported facts, provenance, contradictions, timestamps
        +-- Action ledger: tasks, deadlines, consent, execution vs evidence status
        |
One organiser-powered coordinator (WorkBuddy managed agent)
        |
Typed MCP tools (allowlisted, server-side authorisation, idempotent)
        |
Labelled simulated healthcare adapters
```

| Component | Responsibility | Must not own |
|---|---|---|
| WorkBuddy coordinator | Interpret language, propose clarification, select permitted tools, resume work | Clinical authority, unconditional permissions, claims that care occurred |
| Application state | Facts, decisions, deadlines, consent, task status, evidence | Treating user confirmation as proof a measurement is accurate |
| Clinical policy | Questions, exclusions, dispositions, self-care, reassessment rules | Model-improvised thresholds |
| MCP tools | Narrow validated operations | Arbitrary browsing, unrestricted messaging, silent duplication |

### State model

Urgency and certainty are **separate**; “uncertain” is not a care destination. Understanding, feasibility and willingness are **separate** and can coexist.

**Execution status and evidence status are two independent axes and never collapse into one ladder.** A single sequence mixes “did the request get through” with “did care happen,” which is precisely how a booking confirmation becomes a false claim of care.

| Axis | Values | Question it answers |
|---|---|---|
| **Execution** | `not_started → attempted → acknowledged \| failed \| expired` | Did the request get through, and did anyone accept it? |
| **Evidence** | `none → self_reported → documented` | Do we have reason to believe care actually happened? |

Closure states:

| Closure | Condition |
|---|---|
| `open` | Default. Somebody still must act. |
| `closed_with_evidence` | Evidence ≥ `documented`, or an explicit human acceptance is recorded |
| `escalated_to_human` | Handed to a named human path, with the deadline still visible |
| `expired_unresolved` | Deadline passed with no evidence. A real, reportable state — not a UI failure to update |

`attempted` + evidence `none` is the honest rendering of “we tried and nobody said yes.” It is the core of the product.

Also retained:

- Deadline semantics are explicit: contact initiated, departure, assessment obtained and reassessment due are **different obligations**.
- Clinical revision is versioned and requires evidence; operational retry never changes it.
- Missing information is never silently converted into a negative finding.

### 6.1 The Closure Contract — invariants

The Closure Contract is the rule set that makes the two axes hold **under fault**. Each invariant is a test case, not a slogan.

| # | Invariant | Why it matters |
|---|---|---|
| **I1** | **Immutable clinical deadline.** `clinical_deadline` is set once at disposition and cannot be changed by operational code. Only a versioned, clinician-backed reassessment may change it. | Retrying a failed booking is not new clinical information. Granting extra time because our request timed out converts an operational problem into a clinical one. |
| **I2** | **No false completion.** No failed or unacknowledged action may render as resolved — in the UI, the API, or any summary. | This is the product thesis. |
| **I3** | **Idempotency.** Duplicate callbacks, replayed requests and restarts must not advance state. | Networks retry; users double-tap; restarts replay. |
| **I4** | **Named owner.** At every moment exactly one party must act — patient, named caregiver, or an explicit human service. “Nobody, and it is unresolved” is a valid and **visible** answer. | “Someone should do something” is the failure we exist to catch. |
| **I5** | **Missing is not negative.** Absent data never becomes a negative finding. | MedQAbstain: LLMs systematically overcommit under medical uncertainty. |

**Patient-facing rule.** The patient sees four lines and nothing else:

1. Help is not arranged.
2. You or *[named person]* must act now.
3. Before *[deadline]*.
4. If this route fails, call *[approved human route]*.

The two-axis ledger is **judge-facing evidence**, shown in the walkthrough and the failure-inspection view. It is not the patient's screen. Keeping that split is what stops a safety mechanism from reading as audit software.

### Proposed tech stack

**Runtime and organiser dependence**
- **WorkBuddy managed agent** — single coordinator via the managed-agent SDK. **[verified documented]**, account access [unknown]. Node or Python pinned to one version after the access spike.
- **Typed MCP tools** — `get_episode`, `list_simulated_options`, `propose_action`, `submit_simulated_request`, `notify_caregiver` (simulated), `record_evidence`. Server-side authorisation and idempotency keys.
- **Agent versioning** — one published configuration change demonstrated; existing episodes explicitly pinned in application state. **[our work, not vendor guarantee]**
- **CodeBuddy** — development and test authoring, producing the genuine usage evidence. Not the clinical authority, and not a substitute for runtime centrality.

**Application**
- **Backend (revised 30 September 2026):** one small Python 3.13 + FastAPI service owning policy versions, episode state, deadlines, consent, permissions and the action ledger, deployed on **Render** in Docker on a **paid plan with a mounted persistent disk**; the SQLite path comes from `APP_DATABASE_URL`. Kept deliberately separate from the coordinator.
- **Frontend (revised 30 September 2026):** a **Next.js clinical frontend on Vercel** calling the Render API as JSON: accessible text-first, large text, strong contrast, keyboard and screen-reader support, one question at a time, persistent action card, easy correction. The earlier server-rendered plain-HTML and vanilla-JS interface is retired (Decision D-1b). **A shared bearer token now protects every `/api` route and `/ledger`**, because the deployment is public.
- **Data:** SQLite behind a repository layer on the mounted volume; explicit contract for deadlines and consent. **Not** PostgreSQL: moving the store would rewrite `state.py` and its trigger-enforced append-only guarantees, which 91 tests currently prove.
- **Adapters:** one simulated clinic/booking adapter, labelled. No real NHG, NTU, HealthHub or booking integration exists or is claimed.

**Evaluation**
- Frozen clinician-reviewed case suite with a fixed random seed; development and evaluation cases kept separate.
- Non-LLM seeded fault-sequence tests: timeout, stale availability, duplicate and reordered callbacks, restart, clock change, expired deadline, consent revocation.
- Baselines with identical clinical content and legitimate recovery options: action card plus directory, structured checklist, and CareRelay.
- Formative sessions with 6–8 older-adult/caregiver dyads.
- Subgroup and variation analysis where numbers permit.

**Optional, only with measured need**
- **TRTC speech** — for the target population if typing is a demonstrated barrier; text confirmation and text-only fallback required.
- **Miora** — visual explanations and interface assets if comprehension measurably improves.
- **ADP (revised 30 September 2026):** a **published agent surface**, additive to WorkBuddy and never a replacement for the execution substrate (Decision D-A). It may occupy the **interpretation step only**: never the execution path, never the rendering path. Tool execution is a `[vendor claim]`; the MCP tool, the platform-originated failure event and session resume are `[unknown]`. A conditional slice, default do not run. See `02-architecture.md` D8 and `04-slices.md` Slice 13.
- **Agent Runtime:** only to supply a capability that is actually missing.

**Deliberately excluded**
- Multi-agent proliferation, a clinician authoring platform, real EHR integration, avatar/voice-first design, broad language coverage before native review, autonomous clinical decisions.

---

## 7. Judging-weighted plan

Weights shown are **our planning judgment** of what each ten-point dimension requires, since the detailed healthcare criteria are [unknown]. Effort is in person-hours and must not be mechanically summed — rows overlap.

| # | Dimension | What earns the marks | Our proof | Planned effort | Risk |
|---|---|---|---|---|---|
| 1 | **Impact & Relevance** (10) | Real problem, meaningful value | Verified Singapore health-literacy evidence; documented user episodes; honest bounded claims | 12–18 + recruitment | Exact problem frequency [unknown]; may not be the dominant failure |
| 2 | **Human-Centered Design** (10) | Designed for real users | Observed dyad sessions; revised interface after critical breakdowns | 12–20 | Participants must be recruited; small sample is formative only |
| 3 | **AI Interaction** (10) | Quality and depth of AI use | Adaptive clarification, native coordinator, MCP tools, failure recovery — and evidence it beats a simple checklist | 16–24 | If a checklist performs equally, the AI claim collapses |
| 4 | **Technical Execution** (10) | Technical quality and completeness | Versioned policy, persisted deadlines, permission enforcement, stale/duplicate handling, restart recovery, tests | 28–40 | Adapter contracts and reconciliation are substantial work |
| 5 | **Feasibility** (10) | Realistic and scalable beyond the hackathon | Access spike passed; named owners; measured cost/latency; honest simulated boundary | 8–12 early | External access and clinical sign-off can gate everything |
| 6 | **Demo & Storytelling** (10) | Presented and communicated effectively | One coherent live story plus inspectable failure evidence; no theatre | 8–12 | Branching complexity could dilute the message |
| 7 | **Innovation & Creativity** (10) | Originality and uniqueness | Specific comparison and falsification results; differentiated behaviour, not category novelty | 12–20 | All categories occupied; advantage must be measured |
| 8 | **UX & Accessibility** (10) | Usability and accessibility | Tested text-first accessible flow; dual audience; comprehension and unresolved status understood | 16–24 | Voice/language work displaces safer basics |
| 9 | **Responsible AI & Ethics** (10) | Responsible, trustworthy practice | Reviewed scope and content, abstention, provenance, consent, explicit critical-error gates | 20–35 + reviewer | No reviewer = no clinical claim; this gate is hard |
| 10 | **Overall Quality & Judge's Impression** (10) | Overall assessment | Every claim traceable to a source, trace, test or clearly-labelled hypothesis | 6–10 | Requires the other nine to exist first |

**Highest leverage:** user evidence, clinical scope, and a working organiser integration.  
**Lowest leverage now:** extra agents, avatars, broad multilingual claims and speculative EHR integration.

### The critical path changed

The **card-versus-PlanBack baseline comparison is a kill test, not a nice-to-have.** The project rests on one untested assumption: that a clear bilingual instruction card plus a direct booking link plus a NurseFirst fallback does **not** perform equally. If it does, PlanBack is cut and the reframe collapses. Run this on a clickable text prototype **before** building voice, booking or caregiver features.

**Effort for the two new mechanisms** (see `03-planback-closure-contract.md` §3):

| Work | Hours |
|---|---:|
| PlanBack — extraction, deterministic comparison, bounded repair, constrained input path, tests | 18–30 |
| Closure Contract — two-axis schema, deadline immutability, closure rules, idempotency, restart recovery | 26–40 |
| Fault harness — 7 seeded sequences | 12–19 |
| **Build subtotal** | **56–89** |
| Baseline comparison — 3–6 dyads, counterbalanced, analysis | 20–35 |
| **Total** | **76–124** |

**This does not fit the 16 October deadline alongside the current full scope.** Scope must be cut. Candidate cuts, all already deferred in the 21 September review: Mandarin voice, broad respiratory intake, patient-facing ledger detail, caregiver orchestration beyond one channel, and booking integration. None is on the critical path to a scoring submission.

**Deployment and hosting effort (added 30 September 2026).** The public deployment, the Next.js clinical frontend and auth add **20 to 34 hours [hypothesis]**, and they sit on the critical path to a public link rather than beside it. That takes the plan-level total recorded in `04-slices.md` section 5 from 102–169 hours to **122–203 hours**, against 128 hours available at 8 h/day across the 16 days from 30 September to 16 October. **The lower bound only fits with zero slack, and the upper bound does not fit at all.** The honest consequence is that the study (Slices 8 and 9, 20 to 34 hours) is the first cut if no dyad is recruited by about 5 October.

### Capacity and schedule

Total package: approximately **180–270 person-hours** including contingency, **with clinical review and recruitment secured**. Solo, text-only: **110–160 hours**, with transparently reduced research volume — never weakened safety boundaries.

| Dates | Outcome | Stop condition |
|---|---|---|
| 17–20 Sep | Confirm eligibility/capacity; secure reviewer; test native access; begin problem interviews | No clinical owner → stop claiming triage readiness; no runtime → change integration route |
| 21–24 Sep | First complete narrow slice: assessment → action → clarification → simulated failure → persisted recovery | If this fails, simplify coordination before adding features |
| 25–30 Sep | Core state/permission behaviour; baselines; freeze evaluation material | Cut voice, extra languages, extra complaints |
| 1–7 Oct | Frozen tests and formative sessions; fix critical issues | Unresolved critical error blocks that claim |
| 8–10 Oct | Feature freeze; rerun evaluation; measure latency/cost | No new architectural dependencies |
| 11–14 Oct | Screenshots, repository, diagram, description, cover, video | Completeness over polish |
| 15 Oct | Internal submission target | Verify actual cutoff time |
| 16 Oct | Official submission | — |

---

## 8. Safety and governance

Non-negotiable:

- A qualified reviewer approves the complete pathway — questions, exclusions, dispositions, self-care, failure and escalation branches — not just final labels.
- No diagnosis, dosing or “safe to wait” claim is invented for the demonstration.
- Reported warning signs cannot be erased by later missing answers.
- Poor teach-back is not proof of incapacity; new confusion may itself be clinical evidence.
- Explanations cite the actual decision basis, not generated rationales presented as causal.
- Authorisation is checked at execution, including revocation and caregiver scope.
- Failed handoff is reported as failed or unconfirmed.
- App closure and vendor outage are never presented as continuous monitoring.
- **Without clinical review, no functioning symptom-to-disposition demonstration is presented as patient-ready.** Only non-clinical navigation mock-ups with visibly absent clinical decisions may proceed.
- [verified] HSA assesses intended purpose and function; “not diagnosis” does not settle regulatory status.
- [verified] PDPA obligations cover purpose, consent/legal basis, protection, retention limits and overseas transfer. Deployment region and processor arrangements are [unknown].

**Without clinical sign-off and measured patient benefit, the product remains a research demonstration.**

---

## 9. Proof gates

**Gate A — Native access (first 48 hours).** Authenticate from the intended host; stream an interaction; invoke a typed tool; observe a tool failure; resume after restart; deny consent; handle a duplicate. Record versions, request IDs, latency and usage. Failure → reconsider platform-led approach; do not disguise build-only usage as equivalent.

**Gate B — Patient advantage (continuous).** Compare against clear instructions and structured checks using identical content and options. Measure misunderstanding, unresolved barriers, repetition burden and false beliefs about whether help is arranged. Record the **hint level** for every PlanBack outcome, or the result cannot distinguish recall from reading. Failure → simplify the interaction or change direction.

**Gate B is now the primary kill test**, with pre-registered conditions decided before results are seen:

- PlanBack is cut if the fixed card achieves equal action/deadline recall with lower burden; **or** any critical correct statement is falsely flagged as a mismatch; **or** emergency guidance is delayed by the read-back.
- The Closure Contract is cut if a failed or unacknowledged action ever renders as resolved; **or** a duplicate callback or restart advances state; **or** an operational retry changes the clinical deadline.

**Gate C — Platform advantage.** State what the native operating model supplies that ordinary model calls plus orchestration would not, including integration effort and failure behaviour. Do not credit the platform for our clinical state, consent or action guarantees. Failure → the design is organiser-dependent in name only.

**Gate D — Clinical and evaluation integrity.** Frozen suite shows zero observed emergency undertriage, unsafe self-care, invented negative findings, false completion claims or critical invariant violations. Note: zero misses in 15 independent emergency examples still implies roughly an 18% one-sided 95% upper miss-rate bound. Passing supports regression claims, not clinical safety.

Seven seeded fault sequences are explicit pass/fail cases, not narrative: timeout, stale availability, duplicate callback, reordered callback, restart mid-episode, clock change, consent revocation. Each asserts the five Closure Contract invariants in §6.1. Any violation blocks further feature work.

---

## 10. Submission readiness

**Required or treat as required**
- [ ] **Genuine CodeBuddy/WorkBuddy development history, and at least three development-chat screenshots (redacted). This is the scoring blocker, and it moves to the top of this list: capture started at Slice 4, not on the last day.** **Half met as of 1 October 2026:** the written history is published at `docs/session-logs/`, which satisfies the "written development-process description". **The three screenshots are still not captured.** Named location `submission/usage-proof/screenshots/`, named person Jaydon. `.gitignore` excludes `.codebuddy/` and `.workbuddy-ai/`, and a screenshot cannot be reconstructed later
- [ ] Confirm team eligibility, registration and healthcare-specific criteria
- [ ] Declare Challenge 1 at presentation start
- [ ] Project title
- [ ] Blurb **under ten words** (candidate: "Understand care advice. Find a feasible next step.")
- [ ] Description: users, pain-point evidence, architecture, prompt role, bounded impact
- [ ] True 16:9 cover image
- [ ] Complete GitHub source
- [ ] Live walkthrough
- [ ] Architecture and trust-boundary diagram with trade-offs
- [ ] **The production link (Decision D-C): the Render backend and the Vercel clinical frontend, behind the shared bearer token**
- [ ] **The ADP Experience URL (Decision D-B), with the agent constrained to refuse clinical advice and its knowledge base limited to the non-clinical fixture**

**Optional**
- [ ] 5–8-minute video (overview, core agent features, honest build reflection)
- [ ] ~~Live demo link~~ **now taken as a required item above**: Decisions D-B and D-C reversed the earlier local-only choice on 30 September 2026

**Supporting evidence**
- [ ] Protocol provenance and review boundaries
- [ ] Evaluation report including failures and sample limits
- [ ] Simulation labels, permission model and data-handling statement

---

## 11. Scores

No current built-project score is justified: no submission evidence exists and the mandatory usage proof is not established. If the static artifacts were scored as they stand, the 21 September review's evidence-backed estimate is **39/100** — not 78.

Working target **if** the demonstration and gates are met is a **conditional range of roughly 73–84/100**, with the largest potential gains in AI Interaction, Technical Execution and Feasibility, and the largest uncertainty in Innovation and Impact. An optimistic ceiling of 83–84 assumes unusually clean execution and does **not** include clinical validation, proven health outcomes or real national-scale integration.

These are planning hypotheses and must not be presented as an official or expected score.

---

## 12. Open items

| Area | Status |
|---|---|
| Registration, cutoff time, healthcare rubric | [unknown] |
| Account entitlement, region, quotas, billing | [unknown] |
| Clinical reviewer, permitted content, protocol rights | [unknown] — hard gate |
| Scenario confirmation | Provisional only |
| User evidence | None collected |
| Evaluation harness | Not started |
| Submission assets | None created |
| Team capacity | Assumed, not confirmed |
| Real healthcare integrations | None; all simulated |

### Next three actions

1. Confirm eligibility, cutoff and actual team hours; chase the healthcare rubric.
2. Run Gate A and the clinical-review gate in parallel — these are independent and both can block.
3. Test the product hypothesis against simple baselines before building broader capability.

Criteria for continuing: demonstrated runtime access, a secured clinical reviewer, observed user need, and tests showing no inappropriate deadline resets or false completion claims. Criteria for changing direction: the hypothesised barrier is not experienced by users, an accessible incumbent already solves it, or clinical/operational ownership cannot be secured.
