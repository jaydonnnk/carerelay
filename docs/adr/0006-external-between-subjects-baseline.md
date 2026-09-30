# ADR-0006: The baseline is an external card, between-subjects

- **Status:** accepted, **amended 2026-09-26** (§ Amendment)
- **Date:** 2026-09-25
- **Source:** `02-architecture.md` D6, §9; `03-program-design.md` §6.2; `clinical-review-blocker.md`
- **Supersedes:** the revision-1 in-app `arm` flag

## Context

The project rests on one untested assumption: that a fixed instruction card plus a direct booking link plus an approved human route does **not** perform equally well. If it does, the read-back mechanism is unnecessary and the reframe collapses. This is the primary kill test, not a marketing exercise.

The first revision implemented the comparison as an in-app `arm` flag: participants assigned to a "card arm" inside the application. That design **structurally could not produce the metric**, for three independent reasons:

1. **A static card has no failed handoff.** The primary outcome is whether a participant falsely believes care is arranged *after a failed handoff*. The in-app card arm never reached a handoff, so it could never be scored on the one outcome the entire reframe rests on.
2. **Wrapping the card in app chrome erased its advantage.** The card's whole case is that it is simple and low-burden. Putting it inside the application removed the property being tested.
3. **Within-subject crossover leaked comprehension.** A participant who had already done read-back in the other condition brought that comprehension into the card arm.

## Decision

**The comparator is an external artefact, delivered outside the application, and measurement is between-subjects.**

- The card is **printed or PDF** — a standalone deliverable with the same wording, the same legitimate options, a direct booking link and the approved human route. It is **not** an in-app condition.
- Dyads are assigned to **one** condition. No crossover.
- The card condition receives a **scripted post-failure question** so the same false-completion outcome is measurable in both conditions.
- Protocol is **pre-registered** before any results are seen: primary outcome, cut rule, allocation order, answer key and N are frozen first.
- Target 6 dyads per condition; **minimum 3**, else no HCD claim. **Raw counts, never percentages, below n = 10.**
- The scorer knows the answer key and the response, not the project hypothesis.

**Pre-registered cut rule — read-back is cut if any of:**

1. the card achieves equal action/deadline recall with **lower burden**; **or**
2. any critical **correct** statement is flagged as a mismatch; **or**
3. emergency guidance is delayed by read-back.

Conditions 2 and 3 are pure system properties and are tested **offline, with no participants and no reviewer** — see `03-program-design.md` §6.1.

## Consequences

**Good**

- The primary outcome becomes measurable in both conditions, which the previous design made impossible.
- The card is tested as the thing it actually is, so a genuine win for the simpler alternative is detectable.
- Between-subjects removes the comprehension leak.
- Two of the three cut conditions need **no participants** and no clinical review, so the largest available risk reduction costs almost nothing and runs first.

**Bad / accepted debt**

- Between-subjects needs more dyads for the same power than crossover would. With a target of 6 per condition this is a directional decision, not efficacy evidence.
- Recruitment is now load-bearing in a way it was not before. No dyads means no Gate B result.
- The card cannot be delivered inside the demo, so the walkthrough must show it as a separate artefact.

## Amendment — 2026-09-26: the comparator loses its clinical content

The user selected **Option A + C** from `clinical-review-blocker.md`:

- **(A) Non-clinical comparator.** Both conditions now administer a **content-neutral instruction task** of the same shape, carrying **no symptom, urgency or disposition content**. The mechanism under test — read-back improves retention, a truthful status prevents false completion — is content-independent.
- **(C) Sourced fixture.** The fixture wording is taken **verbatim from attributable published guidance** rather than authored.

**This is a Gate 2 backtrack and is recorded as one.** The *decision* in this ADR is unchanged — external artefact, between-subjects, scripted post-failure question, pre-registered cut rule. The **material** changed, and with it the claim the study can support:

> The study measures the **mechanism** — whether read-back plus truthful status changes comprehension, burden and false-completion belief. It does **not** validate clinical advice, and no claim may imply otherwise. Impact & Relevance loses weight accordingly.

**Still open:** no source has been selected. Licensing and Singapore applicability are **unchecked and precede use**. `CareRelay.md` records that wholesale copying of licensed Schmitt–Thompson protocols is out of scope. If no source can be cleared, Option B (one reviewer, time-boxed) is the recorded fallback — do **not** author clinical wording to unblock the schedule.

## Reversal

Reversible in principle, but only by returning to the reviewer dependency the Option A decision deliberately removed. Any reversal that re-imports clinical content into the comparator re-blocks the study on a reviewer.
