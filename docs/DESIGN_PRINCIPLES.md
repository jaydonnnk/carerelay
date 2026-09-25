# Design principles — the four tests

Companion to `PLAN.md`. Applies the four principles adopted on 21 September 2026 and reports what they actually change.

Every claim is labelled: **[verified]** supported by the cited source · **[vendor claim]** advertised, not independently validated · **[hypothesis]** our judgment · **[unknown]** not established.

---

## 1. The four tests

| # | Test | Fails when |
|---|---|---|
| **P1** | **Load-bearing** — could this be built without organiser tech? | The platform is a host, not a dependency |
| **P2** | **Earliness** — is this on the rising edge, or already mainstream? | We are rebuilding what shipped last month |
| **P3** | **Theme alignment** — does it hit the track's stated behaviours? | We have a good product that is off-theme |
| **P4** | **Ambition** — is the vision big enough to matter? | We are shipping a cautious chatbot |

---

## 2. Verdict

> **CareRelay's current one-shot scope is weak under P1 — and the proposed longitudinal reframe does not automatically pass P2.**

| Source | Statement |
|---|---|
| `PLAN.md` §2 | "PlanBack and the Closure Contract are application logic and **do not require WorkBuddy**." |
| `PLAN.md` §3 | "**Another stack could reproduce the product**; the honest claim is 'designed around WorkBuddy's operating model,' not 'impossible elsewhere.'" |

The two mechanisms that currently make CareRelay distinctive are both **portable**. Under the user's original, literal P1 rule, that would reject the project. Section 4 explains why the literal rule is too strong.

P2, P3 and P4 are **partially met**. No single scope addition repairs all four: longitudinal follow-up is already an occupied category, and added ambition creates a new feasibility problem. The viable hypothesis is narrower: combine a monitored episode with an explicit, measured failure contract, then prove it against the simplest local substitute.

---

## 3. P1 — the load-bearing audit

This is **our nine-surface taxonomy**, assembled from the handbook and linked platform documentation. It is not a nine-item organiser scorecard: it mixes eligible products, suggested Tencent services and derived WorkBuddy capabilities. Here is what `PLAN.md` actually does with each.

| Organiser surface | Role in `PLAN.md` | Carries weight? |
|---|---|---|
| WorkBuddy managed agent | Coordinator: interpret, clarify, select tools, resume | **Yes** |
| MCP tools + tool-failure events | Real external action, real failure | **Yes** |
| CodeBuddy | Development and test authoring only | Build only |
| Managed scheduler | *"Never place urgent escalation on it"* — excluded by rule | **No** |
| Agent Runtime (concurrency) | *"Only to supply a capability that is actually missing"* | **No** |
| Durable sessions across days | Mentioned; checkpoints noted as insufficient | **No** |
| TRTC ASR / TTS | *"Optional, only with measured need"* | **No** |
| ADP guardrails / human-in-the-loop | Not used; abstention is hand-rolled | **No** |
| Miora | *"Only if comprehension measurably improves"* | **No** |

**Internal count: 2 carry real weight, 6 are unused and 1 is build-only.** This is a diagnostic of our plan, not an organiser requirement or scoring rule. The handbook itself lists eight recommended rows and treats CodeBuddy/WorkBuddy usage proof—not feature counting—as the eligibility gate.

The two that do carry weight are reproducible with other agent stacks. That does not make them fake dependencies, but it makes the platform advantage weak: WorkBuddy currently supplies execution, not the differentiating clinical contract.

### Why this happened

It was a scope cut, and the cut was correct on its own terms. `PLAN.md` §7 cuts for the 16 October deadline: Mandarin voice, broad respiratory intake, caregiver orchestration, booking integration.

But look at what got cut: **every longitudinal surface.** The plan kept the one-shot conversation and dropped everything that happens *after* it. Restoring one bounded longitudinal slice would make scheduler/resume evidence meaningful, though not unique to WorkBuddy.

---

## 4. P1 corrected — a lens, not a gate

Taken literally, P1 is **dangerous**, and I do not recommend adopting it as stated.

| Problem with the literal rule | Evidence |
|---|---|
| The handbook requires "built on," not exclusivity | **[verified]** `CHALLENGE_REQUIREMENTS_JUDGING.md` §8: *"built on at least one of the products CodeBuddy or WorkBuddy."* No exclusivity clause exists. |
| No rubric dimension rewards exclusivity | **[verified]** §11 lists ten dimensions. The closest, *AI Interaction*, asks for "quality and depth of AI usage" — **depth, not impossibility.** |
| It creates a single point of failure | **[unknown]** Account entitlement, region and quotas are unverified. Gate A is unrun. A design that *only* works on unverified infrastructure may be undemonstrable. |
| Forced dependencies can cost marks | **[hypothesis]** `CareRelay.md` found the same: unnecessary enterprise dependencies could hurt *Feasibility* and *Responsible AI*. |

**The safe form of P1:**

> Is there **at least one axis** where the platform is genuinely load-bearing — where removing it degrades the **product**, not just the build? And everywhere else, is the platform doing **real work** rather than holding a logo?

That version is checkable, survivable, and it still forces the same fix.

---

## 5. P2 — earliness

What has already been taken, and what remains only a differentiation hypothesis. Product capabilities below are vendor claims unless stated otherwise; dates and papers were rechecked on 22 September 2026.

| Position | Status | Evidence |
|---|---|---|
| Chat → care navigation | **Taken** | Infermedica, Clearstep, Healthdirect pilot |
| Longitudinal reassessment | **Taken** | Clearstep offered follow-up/monitoring in 2021; Infermedica piloted Follow-up in 2023 and released the API in 2025 |
| Appointment / no-show recovery | **Taken** | Hippocratic AI, Luma and others market persistent outreach and rebooking |
| Cohort-scale monitoring and outreach | **Taken** | Hippocratic AI and Healthline AI market population workflows and cohort analytics |
| Abstention in medical ML | **Not new** | Discussed in 2021 literature; regulated tools such as Canvas Dx already return indeterminate/no-result outputs |
| **Measured fail-closed abstention in patient-facing longitudinal LLM triage** | **Immature; exact match not found in a bounded search** | A defensible hypothesis, not a world-first claim |

### The rising edge

| Newly possible | Date | Why it matters here |
|---|---|---|
| MedAbstain — conformal prediction, missing-context perturbations and explicit medical abstention | **[verified]** EACL 2026, March | Shows the evaluation frontier predates MedQAbstain |
| [MedQAbstain](https://aclanthology.org/2026.acl-long.1365/) — tested LLMs systematically overcommit in modified medical MCQA | **[verified]** ACL 2026, July | Makes refusal measurable, but does not validate triage or patient safety |
| Soniox × Tencent code-switching ASR via TRTC | **[verified]** 2 Jun 2026 | Singapore's actual speech: English–Mandarin mixing |
| ADP 4.0 — sandboxed workflows, Skills, human-in-the-loop controls | **[vendor claim]** 21 Jul 2026 | Governed clinical agents become buildable |
| Agent Runtime — ms startup, tens of thousands of concurrent instances | **[vendor claim]** | Population-scale triage becomes economically thinkable |
| Hy3 available globally | **[verified]** 5 Aug 2026 | Model access |

### The honest reading

The timely opportunity is not “invent abstention.” It is to turn recent abstention benchmarks into a product-level test: missing or contradictory evidence must produce a recorded refusal or human route, not a fluent guess.

CareRelay's current pitch — “advice that closes” — sits in a recovery/follow-up category occupied for years, not merely since August 2026. Its remaining differentiation is a hypothesis: a patient-visible episode that preserves the original deadline, separates execution from evidence, records why it abstained and beats a fixed local baseline on false closure.

---

## 6. P3 — theme alignment

Challenge 1 suggests seven behaviours **[verified — `CHALLENGE_REQUIREMENTS_JUDGING.md` §"What the Solution Should Solve"]**. They guide track fit; they are not seven mandatory pass/fail requirements. Current coverage and our chosen implementation path:

| Behaviour | Coverage now | Chosen proof path |
|---|---|---|
| Conversational assessment | Planned | Coordinator |
| Care navigation | Strong | Coordinator |
| Warning-sign detection | Rule intent, untested | Coordinator |
| **Calibrated abstention** | **No operational policy** | Explicit state, deterministic policy and human route; ADP/HITL only if access is proven |
| Self-management support | Underdeveloped | Application-owned episode plus scheduled WorkBuddy invocation |
| **Dynamic reassessment** | **Concept only, no mechanism** | **Application-owned durable state + scheduler/resume evidence** |
| Personalisation + subgroup fairness | Open | — |

Two suggested behaviours are both weakly covered and good candidates for meaningful organiser-tech evidence. That is alignment, not proof that a particular Tencent service is mandatory.

### The organiser's examples support the direction

The challenge examples are **longitudinal**, but examples are not implementation requirements.

[Open the self-contained HTML audit](organiser-tech-load-bearing-audit.html) for the nine-surface review and the challenge-text mapping.

- *"re-checks every 8 hours and automated detection of any new red-flag symptom"* — Scenario 1
- *"daily SpO₂/symptom logs for 10 days, escalating… if SpO₂ drops ≥3 points from baseline"* — Scenario 2
- *"monitor changes that warrant escalation"* — the Challenge paragraph
- Population context includes *"older adults, people with chronic conditions, caregivers, and other vulnerable groups"*; the brief explicitly allows a specific population or scenario and does not require cohort concurrency

Comparing observations to a prior baseline requires persisted state outside a single prompt. **That state must be application-owned and clinically auditable; a WorkBuddy session is not the clinical record.** WorkBuddy can be load-bearing in scheduling, invoking and resuming the episode while the application remains authoritative.

---

## 7. P4 — ambition, and the collision

The ambitious version is easy to state:

> **A monitored care episode, not a conversation.** Every enrolled older adult has a live episode with a deadline and a named owner. Reassessment runs on the platform's scheduler across days. Abstention is enforced, measured and reported. A caregiver sees the cohort.

**This collides with the deadline.** `PLAN.md` §7 estimates the full package at **180–270 person-hours** and the two new mechanisms alone at **76–124 hours**, and concludes plainly: *"This does not fit the 16 October deadline."*

So P4 and *Feasibility* are in direct tension. There is no version where both are fully satisfied. The choice is which one to be honest about.

---

## 8. The reframe worth testing against all four

**From:** advice that closes.
**To:** a monitored episode that cannot lie.

| Layer | What it is | Organiser dependence |
|---|---|---|
| **Authoritative episode state** | An application-owned episode persists across days, with provenance and timestamps | Portable governance layer; never delegated to a chat session |
| **Reassessment loop** | Scheduled re-checks invoke the episode; new red flags take the immediate emergency path | WorkBuddy scheduling/resume — **candidate load-bearing proof**, access unknown |
| **Abstention** | Refusal is a first-class outcome, enforced by deterministic policy and measured | Portable safety rule; ADP/HITL is optional until access and controls are demonstrated |
| **Closure Contract** *(kept)* | No false completion; deadline immutable to operational retry | Application logic — portable, by design |
| **PlanBack** *(kept, cuttable)* | Deterministic comprehension check | Application logic — portable, by design |

**The new Gate C answer, which the current plan fails:**

> Remove WorkBuddy from the chosen build and scheduled reassessment/resume stops; the authoritative episode and safety rules remain, but the demo loses its organiser-native execution loop.

That is checkable. It is honest. And it does not require claiming exclusivity anywhere.

**Why this boundary is defensible.** The Closure Contract, abstention policy and PlanBack stay portable *on purpose* — they are governance and must not depend on a vendor. The platform supplies the chosen scheduling, tool and resume path. If Gate A fails, the portable product core survives, but the proposed WorkBuddy-led submission and its platform-advantage claim do not.

---

## 9. What changes in the plan

| # | Change | Effort |
|---|---|---|
| 1 | Specify one multi-day episode as an **application-owned state model**, not a session | Unestimated; Gate 1 only |
| 2 | Spike one **scheduled reassessment loop**; document the five-minute floor and keep urgent escalation off it | Unestimated; depends on Gate A |
| 3 | Make **abstention** an explicit, recorded outcome with a pre-registered measure — not an error path | Unestimated; clinical review required |
| 4 | Rewrite **Gate C** around the chosen scheduling/tool/resume loop | Low |
| 5 | **Keep** the fixed-card + NurseFirst baseline; cut PlanBack itself if that baseline wins | Required kill test |

Items 1–3 restore scope the plan cut. Their effort has not been estimated, so **no net-neutral claim is justified**. Do not trade away the baseline to fund them: without the baseline, there is no evidence the added AI interaction beats the simpler substitute.

---

## 10. What could kill this

| Risk | Severity |
|---|---|
| **Gate A fails** — the WorkBuddy-led execution proof collapses; only the portable core remains | **Critical** |
| **Clinical reviewer never secured** — the hard gate; unchanged by any of this | **Critical** |
| Concurrency is not required by the brief and should not be claimed from Tencent's advertised capacity | Managed by removing the claim |
| Scheduler floor is 5 minutes **[verified for AgentOS]** — fine for 8-hour re-checks, useless for emergency routing | Managed |
| No verified Singapore-accent or Tamil ASR accuracy; code-switching is **[vendor claim]** | Medium |
| The 16 October deadline. Ambition will lose to the clock | **High** |

---

## 11. Primary sources for the reality check

- [Official hackathon handbook](https://heikesong-global-1256915710.cos.ap-hongkong.myqcloud.com/online_video/27098f4f-7e3b-4e7a-874d-d94ee8ac36ba.pdf) — eligibility, examples, suggested tools and public rubric.
- [Clearstep Smart Care Routing (2021)](https://connection.clearstep.health/clearstep-unveils-smart-care-routing), [Infermedica 2023 review](https://infermedica.com/blog/articles/infermedica-2023-year-in-review) and [current Follow-up documentation](https://developer.infermedica.com/documentation/platform-api/interview-types/follow-up/) — longitudinal reassessment predates this hackathon.
- [Hippocratic AI orchestrators](https://hippocraticai.com/orchestrator-overview/), [Luma Summer 2026](https://www.lumahealth.io/new-ai-agents-run-patient-outreach-and-book-appointments/) and [Healthline AI product](https://healthlineai.org/product) — population outreach, recovery and analytics are already marketed; claims are vendor-reported.
- [Medical-ML abstention perspective (2021)](https://www.nature.com/articles/s41746-020-00367-3), [MedAbstain (EACL 2026)](https://aclanthology.org/2026.eacl-long.291/), [MedQAbstain (ACL 2026)](https://aclanthology.org/2026.acl-long.1365/) and [Canvas Dx FDA decision](https://www.accessdata.fda.gov/cdrh_docs/pdf24/K243558.pdf) — abstention is not new; rigorous patient-facing longitudinal evaluation remains the plausible gap.

---

## 12. Status

- Principles adopted as **internal selection criteria**, not organiser requirements.
- P1 recorded as a **lens with a minimum of one load-bearing axis**, not as an absolute gate. See §4 for why the literal rule is unsafe.
- No implementation authorised. **Gate 1 (Product) was APPROVED on 25 September 2026.** Gate 2 (Architecture) is in progress; see `docs/plans/urgent-advice-accessibility/00-status.md` for the authoritative gate state.
- **Superseded by Gate 2 revision 2 (25 September 2026):** §9 item 2 (spike one scheduled reassessment loop) and the "monitored episode" layer in §8 are **not** in the approved architecture. The round-2 adversarial review found D9 unbuildable as specified, and it was dropped. The P1 load-bearing answer is therefore "execution substrate" — coordinator, real tool call, real failure event, session resume. See `02-architecture.md` §6.6.
