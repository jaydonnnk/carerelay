# The clinical-review blocker — what it actually blocks, and the three ways through

Date: **26 September 2026**. Author: Brody. Status: **decision paper. Not a gate document; it authorises nothing.**

Context: `03-program-design.md` §6 records this as `[unknown, blocking study dependency]` and states plainly that the Gate B study "cannot run as specified" without clinical and native-speaker review. This paper separates what is genuinely blocked from what only *looks* blocked, and puts three options in front of the user.

Every claim is labelled: **[verified]** read in a file or an official source · **[inferred]** reasoning from read material · **[opinion]** judgement with no file support.

---

## 1. TL;DR

**The blocker is narrower than it reads — but it is real, and it lands on the Gate B kill test.**

| Question | Answer |
|---|---|
| Does the hackathon require a clinical reviewer? | **No. [verified]** The submission requirements (`CHALLENGE_REQUIREMENTS_JUDGING.md` §8) list title, blurb, description, conversation history, cover image, three screenshots. No clinician, no sign-off, no ethics approval is mentioned anywhere |
| Does the product require one? | **Yes, for any symptom→disposition claim. [verified]** `PLAN.md` §8 and `01-product.md` already say so: without review, the build stays a labelled demonstration on injected fixtures |
| What is actually blocked? | **The participant-facing Gate B study, and only that. [inferred]** The build, the fixture, the fault harness and the ledger are not blocked |
| Why is the study blocked? | Two independent reasons: **(a)** you would be showing unreviewed clinical guidance to real older adults; **(b)** the approved comparator is a *bilingual* card, and critical Chinese strings need native-speaker plus bilingual clinical approval |
| Is the kill test therefore dead? | **No.** Two of its three cut conditions can still be evaluated, and one can be strengthened. See §4 |

**[opinion]** The honest framing: you do not have a reviewer problem, you have a **study-design problem that a reviewer would have solved.** Those have different fixes, and only one of them is "find a clinician."

---

## 2. What the sources actually say

| Source | Statement | Label |
|---|---|---|
| `CHALLENGE_REQUIREMENTS_JUDGING.md` §8 | Submission needs title, <10-word blurb, description, conversation history, 16:9 cover, ≥3 screenshots. No clinical review required | **[verified]** |
| `ADDITIONAL_CHALLENGE_INFO.md` | *"when a human healthcare professional needs to become involved"* — the challenge asks the product to involve humans; it does not require the team to employ one | **[verified]** |
| `ADDITIONAL_CHALLENGE_INFO.md` | *"whatever we build has to recognize uncertainty... and when a human healthcare professional needs to become involved"* | **[verified]** — this is a **product behaviour** requirement, not a team-credential requirement |
| `PLAN.md` §8 | *"A qualified reviewer approves the complete pathway... Without clinical review, no functioning symptom-to-disposition demonstration is presented as patient-ready."* | **[verified]** — self-imposed, and correct |
| `03-program-design.md` §6 | *"the clinical Gate B study cannot run as specified"* | **[verified]** |
| `research-workarounds.md` | Workaround accepted at Gate 1: *"Use a pre-authored, injected recommendation fixture to demonstrate comprehension, consent, barriers, failure recovery and status truthfulness."* | **[verified]** — the fixture workaround was already approved |

**The distinction that resolves most of this.** The challenge wants a *patient-facing prototype* **[verified]**. CareRelay's judged object is not a symptom-to-disposition service — it is **the honesty of an episode under failure.** The fixture supplies the recommendation; the product is judged on what it does when the recommendation cannot be carried out. **[inferred]** That reframing is already approved at Gate 1 and it does not require a clinician, because no clinical decision is being made by the system.

**What does require a clinician:** anything a real person reads as guidance, and any rule that maps a symptom to an urgency. That is a small, enumerable set. See §3.

---

## 3. The split — three tiers, only one of which is blocked

| Tier | Content | Reviewed required? | Status |
|---|---|---|---|
| **Tier 1 — Non-clinical mechanism** | PlanBack comparison, hint ladder, closure rules, deadline immutability, idempotency, the ledger, the four-line and expired renderings, the fault harness | **No. [inferred]** No clinical claim. The words are policy-owned strings, and they assert only workflow facts ("help is not arranged") | **Not blocked.** Buildable today |
| **Tier 2 — Injected fixture** | The pre-authored recommendation the demo displays, and its permitted routes | **Needs a clinical *source*, not a clinical *reviewer*.** If the wording is copied *verbatim* from published, attributable guidance, the demo is reproducing a source rather than inventing a threshold **[inferred]** | **Partially blocked.** Depends on the sourcing route chosen (§5 Option C) |
| **Tier 3 — Symptom→disposition logic** | Any rule that reads a symptom and decides urgency; the 995 branch; the reassessment branch | **Yes, genuinely. [verified]** `PLAN.md` §8 and `03-program-design.md` §8.2 | **Blocked, and correctly so.** Already excluded from the judged build |

**The consequence:** the build is blocked on Tier 3, and Tier 3 was already cut. **The only thing the reviewer actually gates is the Gate B study's participant-facing material.**

---

## 4. Is the kill test dead? No — and one condition gets stronger

`01-product.md` fixes three PlanBack cut conditions. Assessed against the blocker:

| Cut condition | Runnable without a reviewer? |
|---|---|
| The fixed card achieves **equal action/deadline recall** with **lower burden** | **Yes, with a caveat.** Recall and burden can be measured with the card only — no clinical guidance is administered, because both conditions show the *same* fixture text and the question is whether the person can repeat it. **[inferred]** The caveat is that both conditions still display the fixture, so Tier 2 sourcing matters |
| **Any critical correct statement is falsely flagged as a mismatch** | **Yes, and fully.** This is a pure system property — the test is whether `compare_plan` errs on known inputs. It needs **no participants at all** |
| **Emergency guidance is delayed by read-back** | **Yes, and fully.** Also a pure system property: assert the urgent path renders before any PlanBack call. No participants needed |

**[opinion] This is the most useful finding in this paper: two of the three kill conditions are testable today with zero participants and zero reviewer.** They are currently buried in a study that cannot run. Lifting them out *de-risks the project immediately* — if `compare_plan` falsely flags correct statements, or if the urgent path is delayed, PlanBack is cut and you have saved weeks. That test can run this week.

The third condition — the participant comparison — is the one that needs people, and therefore the one the blocker touches.

---

## 5. Three ways through

### Option A — Run the comparison non-clinically (fastest, cheapest, weakest claim)

**What:** reframe the Gate B comparison as a **comprehension and false-completion study that administers no clinical guidance.** Both conditions show a *non-clinical* instruction task — for example an appointment-administration task in the same shape as the fixture, carrying no symptom or urgency content at all. The mechanism under test (read-back improves retention; a truthful status prevents false completion) is content-independent. **[opinion]**

- **Cost:** near zero. Change the comparator material and the pre-registration.
- **Unblocks:** the comparison can run next week.
- **Loses:** the result is about the *mechanism*, not about care advice. The submission must say so, and Impact & Relevance loses some weight.
- **Honesty risk:** low, provided the submission does not imply the study validated clinical advice.
- **Gate impact:** this **changes D6's material** — it is a Gate 2 backtrack, and must be recorded as one.

### Option B — Secure one qualified reviewer (slowest, strongest, most likely to fail on the clock)

**What:** one clinician reviews the fixture and the participant-facing card.

- **Cost:** unbounded. Three weeks of chasing is realistic **[opinion]**; two people already approached and neither has responded.
- **Unblocks:** the study exactly as approved, plus the clinical-credibility language in the submission.
- **Loses:** nothing, if it works — and 20 days, if it does not.
- **Honesty risk:** none.
- **Practical note:** the ask is small and specific — *"review one pre-authored recommendation and its permitted routes for a scripted demonstration; no liability, no clinical service, credited or anonymous."* A **small ask is far more likely to get a yes than "be our clinical advisor."** **[opinion]** Worth one more attempt in parallel with A, time-boxed to 48 hours.

### Option C — Source the fixture verbatim from published guidance (cheap, strengthens Tier 2)

**What:** derive the fixture wording **word for word** from an attributable public source rather than authoring it. Then the demo *reproduces* guidance instead of inventing it.

- **Cost:** a few hours of careful sourcing and citation.
- **Unblocks:** Tier 2. It does **not** unblock Tier 3, and it does **not** make the card approve itself for participant use.
- **Loses:** nothing, but it is not a substitute for review — it is what makes the fixture **honest** rather than merely labelled.
- **Caution [verified]:** `CareRelay.md` records that wholesale copying of licensed Schmitt–Thompson protocols is out of scope, and HSA assesses intended purpose regardless of a "not diagnosis" disclaimer. Sourcing must respect both. **Which source to use is a question this paper does not answer** — that needs a check against licensing and Singapore applicability, and I have not done it.

**[opinion] My recommendation: A + C now, B in parallel on a 48-hour clock.** A gets the comparison running without exposing anyone to unreviewed guidance. C makes the fixture defensible. B is the upside case — if a clinician says yes this week, you get the strongest possible version and nothing is lost by having prepared A and C.

---

## 6. What I have deliberately not done

- **No clinician has been contacted.** That is an external action and it is yours to make.
- **No source has been selected or checked for licensing.** Flagged as an open question above.
- **No gate document has been edited.** This paper proposes a D6 backtrack; it does not apply one.
- **Nothing has been built.** Gate 3 is unapproved and Gate 4 has not been written.

---

## 7. The decision you actually need to make

One question, and it is a genuine trade rather than a technical choice:

> **Do you run a non-clinical comparison that can start immediately (A), or hold the study open for a clinician who may not arrive in time (B)?**

**[opinion]** A, with B chased in parallel and a hard 48-hour time-box. Waiting is the one option that cannot be recovered, because the study needs lead time for recruitment that you do not have. And the two reviewer-free kill conditions in §4 should be built and run **regardless of which you choose** — they are the cheapest insurance in the project.
