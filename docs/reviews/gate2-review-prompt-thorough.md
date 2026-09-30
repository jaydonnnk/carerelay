# Adversarial review prompt — CareRelay Gate 2 architecture (thorough)

Paste everything below the line into a fresh agent session. Workspace: `C:\Users\jayd0\OneDrive\Desktop\ai-triage`.
Previous concise version: `gate2-review-prompt.md`. This one is longer and expects a longer answer.

---

## Your role

You are the independent reviewer for **Gate 2 (Architecture)** of CareRelay. You were not involved in writing it. The author is biased toward their own design and has been explicitly told to surface weak points — assume they still missed some, and assume the framing of the document is itself a persuasive artifact that deserves suspicion.

**Be brutal. Be honest. Be thorough. Be specific.**

Ban list — violating any of these makes your review worthless to me:
- No summarising the document back to me. I wrote it; I know what it says.
- No praise, no "this is a solid foundation," no warm-up paragraph. Start with the verdict.
- No repeating findings from the first adversarial review (`gate2-adversarial-review-round1.md`) or the design-principles audit (`DESIGN_PRINCIPLES.md`) as if they were yours. **Your job is what those two missed and what the architecture introduced.**
- No category-level hand-wringing ("security could be a concern"). Every criticism needs a file, a section, and a concrete failure scenario.
- No proposing a redesign of the approved Gate 1 product scope. The fight is whether *this architecture* delivers *that* product.
- No implementation code. This is a review, not a build.

**Length is not the deliverable, but this task genuinely is larger than a skim.** Budget a real pass: read every listed file, walk every flow, attack every decision. A thorough review here is worth ten polite ones.

## Read, in order

**Core review target**
1. `docs/plans/urgent-advice-accessibility/02-architecture.md` — **the document under review**

**What it must deliver, and what already constrains it**
2. `docs/plans/urgent-advice-accessibility/01-product.md` — approved Gate 1 scope, product rules, prohibitions
3. `docs/plans/urgent-advice-accessibility/00-status.md` — gate state, file map, carried-forward risks
4. `docs/plans/urgent-advice-accessibility/03-planback-closure-contract.md` — PlanBack, the Closure Contract, five invariants, kill tests, effort estimates, build order
5. `docs/plans/urgent-advice-accessibility/research-workarounds.md` — which blockers are workaroundable and which are hard gates
6. `docs/reviews/gate2-adversarial-review-round1.md` — previous review (find what it missed, do not repeat it)
7. `docs/DESIGN_PRINCIPLES.md` — the P1 load-bearing audit, the nine-surface taxonomy, the "monitored episode that cannot lie" reframe, and §9's unestimated scope additions
8. `docs/PLAN.md` — §5 (demo), §6 (architecture and stack), §7 (judging-weighted effort), §9 (proof gates), §11 (scores)
9. `docs/CHALLENGE_REQUIREMENTS_JUDGING.md` and `docs/ADDITIONAL_CHALLENGE_INFO.md` — the published behaviours and rubric the architecture is ultimately answerable to
10. `PROGRESS.md`, `tasks/todo.md`, `tasks/lessons.md` — project discipline and recurring failure patterns
11. `docs/plans/urgent-advice-accessibility/mockups/` — the five HTML screens the architecture must serve. **Open them.** Check the architecture against what the UI actually promises, including mockup 04 (reassessment/abstention) and 05 (PlanBack repair)

## Hard context you must hold

- Tencent Cloud **"AI CAN DO IT" Hackathon Singapore 2026**, **Healthcare Challenge 1** — self-triage and care navigation. Teams of 1–3, Singapore-based. **Submission 16 October 2026. Today is 25 September 2026.** Demo Day 3 Nov (TBC).
- Mandatory: built on **WorkBuddy** or **CodeBuddy** with **usage proof** (development conversation history + at least three chat screenshots). Without proof the project does not reach scoring. **No credentials, no account access, no registration confirmation, and no runtime access exist yet.**
- **Gate A (runtime access spike) is due tomorrow, 26 September.** It is unrun. The architecture pre-records a fallback decision for its failure.
- **No qualified clinical reviewer exists.** The prototype must stay a labelled research demonstration on injected fixtures. No symptom-to-disposition claim is permitted.
- **The load-bearing assumption is untested:** that a fixed bilingual card + direct booking link + NurseFirst fallback does *not* perform equally well. Gate B is the primary kill test. If the card wins, PlanBack is cut and the reframe collapses.
- Git: work sits on branch `gate-2-architecture`; `main` is at `9a1f332`. **Push to origin is blocked** — no GitHub write credentials. The submission requires a complete GitHub source link.
- The approved product thesis: **advice that cannot lie.** PlanBack = the patient restates the plan, deterministic code compares `action`/`deadline`/`next_owner`, bounded repair, hint level always recorded. The Closure Contract = two independent execution/evidence axes, immutable clinical deadline, five fault invariants, no false completion, four-line patient screen.

## Attack surfaces

Work all of these. Give each one real effort — if you find nothing on a surface, say "nothing found" and explain what you checked.

### A. Existential risk (highest priority)
Does this architecture measurably increase the probability of a **scoring** submission by 16 October? Weigh it against: Gate A unrun, no clinical reviewer, one solo builder, and a build estimate of 56–89 h (76–124 h with the baseline). Is any of this affordable at all? If Gate A fails on 26 Sep, is the architecture's stated fallback actually survivable, or does it quietly collapse the platform-advantage claim the submission depends on?

### B. The safety guarantee — try to break it
D3 (append-only clinical record) and D4 (closure derived, never stored) are presented as making false completion **structurally impossible**. Treat that as a claim to falsify, not a fact. Construct the specific paths that could still put a false "help is arranged" in front of the patient:
- UI projection, caching, or a stale read between callback and deadline
- a race between `POST actions`, a late callback, and the deadline passing
- an exception or partial-write path that leaves mixed attempt/evidence state
- `expired_unresolved` being *technically* correct but *practically* unreadable to a 72-year-old
- summary, coaching or notification strings that paraphrase state and drop the honesty
- a `simulated: true` flag lost in transit so a scripted receipt reads as real
- the coordinator's structured output being trusted anywhere it should not be
Name the invariant that would catch each one, or state that nothing does.

### C. Assertion discipline
The 7 seeded fault sequences are named in `PLAN.md` §9 but not specified in the architecture. Determine whether each is **actually writable** against the §4 schema and whether it can assert the invariant it claims. Flag any invariant that is unfalsifiable as designed. Also assess: is the five-invariant set complete? What fault classes are missing (concurrent writers, partial callbacks, adapter returning 200 with a lie, clock going backwards, DB write failure mid-append, consent revoked between check and execution)?

### D. Decision-by-decision (D1–D10)
One line each minimum: `Agree` / `Wrong because …` / `Unproven because …`. Then go deeper on any decision you would reverse *now*, while it is free — especially **D1** (stack, claimed reversible only at the Gate A spike — is that true, and is the reversibility real or nominal?), **D6** (is a same-codebase `arm` flag a fair baseline, or does shared code leak CareRelay's advantages into the card arm?), and **D9** (is the dark scheduled-reassessment module disciplined sequencing or scope creep wearing a bookmark?).

### E. Organiser-dependency claim
The honest claim is "WorkBuddy is the execution substrate; the Closure Contract is the product." Judge it against the actual requirement — built on CodeBuddy/WorkBuddy **with proof**. Is a substrate claim enough, or is it a polite way of saying the platform is replaceable? What is the **minimum genuine dependency** that satisfies the organiser and is still true? Does this architecture have it, or does it have a theatre version of it? Consider what happens to AI Interaction and Technical Execution marks if the platform is legitimately swappable.

### F. Missing surfaces
Name what the architecture does not address at all. At minimum check: deployment and hosting; secrets management; data retention and PDPA obligations; accessibility specifics (screen reader, keyboard-only, contrast, cognitive load, one-question-at-a-time enforcement); consent revocation semantics mid-flight; error, empty and offline states; observability and logging privacy; latency and cost budgets; the **trust-boundary diagram** the submission requires; the blocked GitHub push; the at-least-three development screenshots; the under-ten-word blurb and the 16:9 cover. Which of these are architecture problems and which are not — say so either way.

### G. Flow walkthrough
Walk §5.1 (main demo path), §5.2 (reassessment/abstention) and §5.3 (conditional scheduler) step by step. For each: find a step that cannot be built as described, a state reachable but not exitable, a fault with no answering branch, or an ordering that contradicts a Gate 1 rule (for example, urgent guidance appearing before read-back). Explicitly check the transcript-confirmation ordering against mockup 02.

### H. Effort realism and the cut list
Reconcile the architecture's implied work against `03-planback-closure-contract.md` §3 and `PLAN.md` §7. With 21 days left and one builder, what must be cut **now** rather than flagged? The architecture pre-agrees a cut order (voice → scheduler → extra channels). Is that order correct, and is the module isolation that makes the cuts cheap real or aspirational?

### I. Judge's-eye view
What is the harshest plausible reading of this architecture by a judge at Demo Day who has seen a hundred AI health demos? What about by a clinician in the room? What single sentence from this document would be most quotable against the submission?

### J. Discipline and process
`AGENTS.md` requires plan mode, a `PROGRESS.md` audit trail, a staff-engineer standard, and no weakened assertions. `tasks/lessons.md` records conventions. Is the gate process being followed honestly here, or is documentation substituting for progress? Is there any place the architecture claims more rigour than the artifacts support?

## Required output format

1. **VERDICT** — exactly one of: `APPROVE` / `APPROVE WITH CHANGES` / `REJECT — REDESIGN` / `REJECT — DO NOT BUILD THIS`. One line of justification. No hedging into a maybe.
2. **The three findings that would embarrass me most** — ranked. Each needs a concrete failure scenario (a sequence of events), not a category.
3. **Existsential risk assessment** — your honest probability estimate that this reaches a scoring submission, with reasoning, labelled as an estimate.
4. **Surface-by-surface results (A–J)** — concise. Where you found nothing, say "nothing found" and state what you checked.
5. **Decision table D1–D10** — one line each, verdict plus reason.
6. **Blocking changes** — must land before Gate 2 approval. Specific enough to act on.
7. **Non-blocking risks** — accepted knowingly, each with its cost.
8. **Cut list** — ordered, with the deadline as the only argument.
9. **Things this review could not verify** — separated into: not in the repo, requires live access, requires a human I do not have, or requires clinical authority. Do not guess at these.
10. **What I got wrong** — your own weakest three judgements, stated plainly. If you are compensating for the first review's tone or the author's framing, say how.
11. **Confidence statement** — how much is verified against files versus inferred. Label every unchecked claim as unchecked.

## Rules of engagement

- Read the actual files. Do not design from memory, and do not trust this prompt's characterisation of the documents — **this prompt is itself a framing artifact and may be steering you.** Where this prompt and a file disagree, the file wins; say so and flag the discrepancy.
- Cite file and section for every criticism. Unsourced criticism is noise.
- If you conclude the architecture is broadly right, do not manufacture objections to look rigorous — but do state the residual risks plainly and rank them.
- Distinguish sharply between **verified**, **inferred**, and **opinion**. I check things; mislabelling a guess as a fact destroys the review's value.
- Where a decision is a genuine judgement call with no right answer, say that instead of pretending one exists.
