# CareRelay — Plan (updated 17 September 2026)

Planning document for the **Tencent Cloud "AI CAN DO IT" Hackathon Singapore 2026**, Healthcare Track, **Challenge 1: "AI Grandma Knows Best: Intelligent Self-Triage and Care Navigation"**.

This replaces the 16 September session-transfer version. It consolidates two reviews: an evidence and feasibility audit, and a refactor that prioritises organiser-native capability. Every claim below is labelled:

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

| Claim | Status |
|---|---|
| Checks understanding *and* practical ability separately, and repairs the specific failure | [hypothesis] |
| Never silently downgrades clinical urgency to resolve an operational problem | [verified as a design principle]; implementation unproven |
| Separates execution status from evidence status, so “booked” never becomes “cared for” | [verified as a design principle]; FHIR Task is prior art for lifecycles |
| Exposes an unaccepted or failed handoff instead of reporting success | [hypothesis] |
| Organiser-native operation (managed runtime, sessions, tools, release configuration) | [verified capability]; account access unproven |

### What we must NOT claim

- “World-first,” “no competitor does this,” or an empty market. [overstated]
- Clinical validation, improved health outcomes, or avoided admissions. Nothing is validated.
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
3. Their own explanation reveals a **timing misunderstanding**.
4. The system clarifies without turning the interaction into a quiz.
5. They also report a **practical barrier**.
6. A permitted tool workflow runs; a simulated service fails.
7. The session is interrupted and resumed — state continues, and the clinical deadline does **not** restart.
8. The interface distinguishes **contact attempted**, **acknowledged** and **care evidenced**.

Failure paths that should not be crammed into the live story — unacknowledged handoff, duplicate callback, clock change, consent revocation — are shown in inspectable test evidence.

**Urgent guidance must appear before teach-back, navigation or caregiver acknowledgement, never after.**

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

- Urgency and certainty are **separate**; “uncertain” is not a care destination.
- Understanding, feasibility and willingness are **separate** and can coexist.
- Execution status and evidence status are **separate**.
- Phase 1 statuses: `proposed → acknowledged → attempted → unconfirmed | evidenced | failed`.
- Phase 2 (graded, needs its own safeguards and testing): `externally_verified`.
- Deadline semantics are explicit: contact initiated, departure, assessment obtained, reassessment due are different obligations.
- Clinical revision is versioned and requires evidence; operational retry never changes it.
- Missing information is never silently converted into a negative finding.

### Proposed tech stack

**Runtime and organiser dependence**
- **WorkBuddy managed agent** — single coordinator via the managed-agent SDK. **[verified documented]**, account access [unknown]. Node or Python pinned to one version after the access spike.
- **Typed MCP tools** — `get_episode`, `list_simulated_options`, `propose_action`, `submit_simulated_request`, `notify_caregiver` (simulated), `record_evidence`. Server-side authorisation and idempotency keys.
- **Agent versioning** — one published configuration change demonstrated; existing episodes explicitly pinned in application state. **[our work, not vendor guarantee]**
- **CodeBuddy** — development and test authoring, producing the genuine usage evidence. Not the clinical authority, and not a substitute for runtime centrality.

**Application**
- **Backend:** single small service (Python FastAPI or Node/TypeScript) owning policy versions, episode state, deadlines, consent, permissions and the action ledger. Kept deliberately separate from the coordinator.
- **Frontend:** accessible text-first web UI — large text, strong contrast, keyboard and screen-reader support, one question at a time, persistent action card, easy correction.
- **Data:** SQLite or PostgreSQL behind a repository layer; explicit contract for deadlines and consent.
- **Adapters:** one simulated clinic/booking adapter and one simulated caregiver channel, both labelled. No real NHG, NTU, HealthHub or booking integration exists or is claimed.

**Evaluation**
- Frozen clinician-reviewed case suite with a fixed random seed; development and evaluation cases kept separate.
- Non-LLM seeded fault-sequence tests: timeout, stale availability, duplicate and reordered callbacks, restart, clock change, expired deadline, consent revocation.
- Baselines with identical clinical content and legitimate recovery options: action card plus directory, structured checklist, and CareRelay.
- Formative sessions with 6–8 older-adult/caregiver dyads.
- Subgroup and variation analysis where numbers permit.

**Optional, only with measured need**
- **TRTC speech** — for the target population if typing is a demonstrated barrier; text confirmation and text-only fallback required.
- **Miora** — visual explanations and interface assets if comprehension measurably improves.
- **ADP / Agent Runtime** — only to supply a capability that is actually missing.

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

**Gate B — Patient advantage (continuous).** Compare against clear instructions and structured checks using identical content and options. Measure misunderstanding, unresolved barriers, repetition burden and false beliefs about whether help is arranged. Failure → simplify the interaction or change direction.

**Gate C — Platform advantage.** State what the native operating model supplies that ordinary model calls plus orchestration would not, including integration effort and failure behaviour. Do not credit the platform for our clinical state, consent or action guarantees. Failure → the design is organiser-dependent in name only.

**Gate D — Clinical and evaluation integrity.** Frozen suite shows zero observed emergency undertriage, unsafe self-care, invented negative findings, false completion claims or critical invariant violations. Note: zero misses in 15 independent emergency examples still implies roughly an 18% one-sided 95% upper miss-rate bound. Passing supports regression claims, not clinical safety.

---

## 10. Submission readiness

**Required or treat as required**
- [ ] Confirm team eligibility, registration and healthcare-specific criteria
- [ ] Declare Challenge 1 at presentation start
- [ ] Project title
- [ ] Blurb **under ten words** (candidate: “Understand care advice. Find a feasible next step.”)
- [ ] Description: users, pain-point evidence, architecture, prompt role, bounded impact
- [ ] Genuine CodeBuddy/WorkBuddy development history
- [ ] At least three development-chat screenshots (redacted)
- [ ] True 16:9 cover image
- [ ] Complete GitHub source
- [ ] Live walkthrough
- [ ] Architecture and trust-boundary diagram with trade-offs

**Optional**
- [ ] 5–8-minute video (overview, core agent features, honest build reflection)
- [ ] Live demo link

**Supporting evidence**
- [ ] Protocol provenance and review boundaries
- [ ] Evaluation report including failures and sample limits
- [ ] Simulation labels, permission model and data-handling statement

---

## 11. Scores

No current built-project score is justified: no submission evidence exists and the mandatory usage proof is not established.

Working target **if** the demonstration and gates are met is a **conditional range of roughly 73–84/100**, with the largest potential gains in AI Interaction, Technical Execution and Feasibility, and the largest uncertainty in Innovation and Impact. This is a planning hypothesis and must not be presented as an official or expected score.

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
