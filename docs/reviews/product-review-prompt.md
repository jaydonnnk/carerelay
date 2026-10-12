# Independent review prompt: CareRelay, product substance only

A copy-paste prompt for a fresh reviewer agent that has not seen this project.
Scope is the **product**: does it solve the stated problem, is it differentiated,
is the AI use real, is the engineering sound, is it honest. **Visual design, UX
craft and presentation are out of scope and reviewed later.**

Written 11 October 2026.

---

## 0. Your stance

You are reviewing a hackathon submission you had no hand in. The people asking
want a **true** score, not a flattering one. A review that finds nothing wrong
has failed.

Rules for you:

- Do not accept the project's own framing as evidence. Read the artifacts and
  check the claims against them.
- The project maintains a file of its own limitations. Read it, but do **not**
  treat it as the complete list of weaknesses. Find weaknesses it did not list.
- If something cannot be verified from what you can see, say it is unverified.
  Do not fill the gap with a plausible guess.
- Be willing to give a low score. Be willing to say the differentiation is thin
  if it is.

---

## 1. What you are reviewing

Workspace root: `carerelay/`. Read these, in this order.

**The rules you are scoring against**

| File | Why |
|---|---|
| `docs/CHALLENGE_REQUIREMENTS_JUDGING.md` | Both challenge statements, submission requirements, the ten-dimension rubric |
| `docs/ADDITIONAL_CHALLENGE_INFO.md` | The organiser's spoken framing of both statements |
| `CareRelay.md` | An earlier independent review. Contains recovered handbook facts (deadlines, team rules, the one-case-study rule). Treat its scores as one reviewer's judgment, not as fact |

**What the project actually is**

| File | Why |
|---|---|
| `docs/PLAN.md` | Current direction, labelled evidence, scope |
| `docs/plans/urgent-advice-accessibility/00-status.md` | The only authority on gate and slice state |
| `docs/plans/urgent-advice-accessibility/01-product.md` | The product definition, approved patient copy, success metric |
| `docs/plans/urgent-advice-accessibility/02-architecture.md` | Architecture, trust boundaries, where AI may and may not act |
| `docs/plans/urgent-advice-accessibility/03-planback-closure-contract.md` | The closure contract |
| `docs/plans/urgent-advice-accessibility/04-slices.md` | The slice plan |
| `AGENTS.md` | Project rules, including the evidence-label convention |

**What will actually be submitted**

`submission/description.md`, `submission/honest-claims.md`,
`submission/demo-walkthrough.md`, `submission/usage-proof.md`,
`submission/adp-agent-instruction.md`, `submission/setup-runbook.md`,
`submission/cover-16x9.svg`, `submission/architecture-trust-boundaries.svg`.

**The two case studies you must differentiate against**

| File | What it is |
|---|---|
| `ai-triage_casestudy2.md` | Mount Sinai / Clearstep "Check Symptoms & Get Care", NEJM Catalyst 2026. A production AI **self-triage** system. This is the closest thing to a direct competitor |
| `medical-ai-framework_casestudy1.md` | "Reason2Decide", University of Alberta. A training framework for **faithful explanations** in medical AI |

**The running thing**

- `https://carerelay-self.vercel.app` (patient screen)
- `https://carerelay-self.vercel.app/ledger` (evidence ledger)
- `https://carerelay-dzt3.onrender.com` (API)
- `https://adp.tencentcloud.com/webim_exp/#/chat/GkTbUc` (published agent)

**Before you trust any URL, fetch it and read its title.** A URL that answers
200 is not evidence that it is this project's. There is a known trap: a
lookalike host resolves fine and is someone else's app.

---

## 2. The rubric you are scoring against

Ten dimensions, ten points each, from `docs/CHALLENGE_REQUIREMENTS_JUDGING.md`.

1. Impact and Relevance (10) - addresses a real-world problem, creates meaningful value
2. Human-Centered Design (10) - how well the solution is designed for real users
3. AI Interaction (10) - quality and depth of AI usage
4. Technical Execution (10) - technical quality and completeness
5. Feasibility (10) - realistic and scalable beyond the hackathon
6. Demo and Storytelling (10) - how effectively it is presented
7. Innovation and Creativity (10) - originality and uniqueness
8. User Experience (UX) and Accessibility (10) - usability and accessibility
9. Responsible AI and Ethics (10) - responsible and trustworthy AI practices
10. Overall Quality and Judge's Impression (10) - overall assessment

### Scope split: score six now, defer four

**Score these six now (60 points).** This is the number that matters here.

| # | Dimension |
|---|---|
| 1 | Impact and Relevance |
| 3 | AI Interaction |
| 4 | Technical Execution |
| 5 | Feasibility |
| 7 | Innovation and Creativity |
| 9 | Responsible AI and Ethics |

**Defer these four (40 points). Mark each `DEFERRED`.** A separate design and
presentation review will score them.

| # | Dimension | Why deferred |
|---|---|---|
| 2 | Human-Centered Design | Design review |
| 6 | Demo and Storytelling | Presentation review |
| 8 | UX and Accessibility | Design review |
| 10 | Overall Quality and Judge's Impression | Depends on the above |

**One hard instruction.** The patient screen is intentionally four lines of text
and one button, with no styling, no imagery and no chat interface. That is a
deliberate constraint, not an unfinished UI. **Do not let its visual plainness
leak into your score for the six substance dimensions.** If you think the
plainness is itself a product mistake, say so explicitly and score it under
Impact or Innovation, with reasoning.

---

## 3. Evidence standard

Apply the project's own labels, from `AGENTS.md`:

- `[verified]` - supported by a source you can cite
- `[vendor claim]` - advertised, not independently validated
- `[hypothesis]` - judgment
- `[unknown]` - not established

Then hold these specific tests:

- **Demos are not evidence of behaviour.** A screen that renders proves a
  renderer. Ask what the system does when the happy path fails.
- **Refusal is not capability.** If an AI component is shown refusing unsafe
  input, ask what it does on input it should handle. Something that refuses
  everything passes every refusal test.
- **Tests are not outcomes.** A passing suite proves the code matches its tests.
  Ask what the tests cannot see.
- **A claim of clinical safety needs a clinician.** If none reviewed it, the
  safety claim is unestablished regardless of how careful the code is.

---

## 4. The differentiation question

This is the part that matters most. Answer it directly.

The organiser's recovered handbook says each team selects **one** case study and
declares it at the start of the presentation. Assume that rule holds.

For each case study:

1. State in one sentence what it does.
2. State what CareRelay does that it does not, if anything.
3. State what it does that CareRelay does not.
4. Judge whether the difference is **real** (different mechanism, different
   guarantee) or **presentational** (same mechanism, different words).

Then answer the hard version: **if a judge has just read the Mount Sinai case
study, what stops them concluding that CareRelay is a smaller, unvalidated
version of the same idea?** Quote the strongest available answer from the
artifacts, and say whether you believe it.

Pay attention to one thing in particular. CareRelay's central claim is that it
refuses to show progress it cannot prove, and that this is a guarantee rather
than a preference. Check whether that is enforced by the system's structure or
merely asserted by its copy. Look for where a code path could display a
reassuring state without a record behind it.

---

## 5. What to output

Structure your answer exactly like this.

### A. What this project is, in your own words
Five sentences maximum. If you cannot do it in five, you have not understood it,
and that is itself a finding.

### B. Scorecard

| # | Dimension | Score /10 | One-line reason |
|---|---|---|---|
| 1 | Impact and Relevance | | |
| 3 | AI Interaction | | |
| 4 | Technical Execution | | |
| 5 | Feasibility | | |
| 7 | Innovation and Creativity | | |
| 9 | Responsible AI and Ethics | | |
| | **Substance subtotal** | **/60** | |
| 2 | Human-Centered Design | DEFERRED | |
| 6 | Demo and Storytelling | DEFERRED | |
| 8 | UX and Accessibility | DEFERRED | |
| 10 | Overall Quality | DEFERRED | |

Below the table, for each scored dimension, three to five sentences citing
`file:line` or a URL.

### C. Differentiation verdict
The section 4 answers. End with one sentence: is the differentiation real, and
how much of the 10 Innovation points does it earn.

### D. The three harshest fair criticisms
Not nits. The things that would cost the most points with a real judge.

### E. What you could not verify
Every claim you wanted to check and could not. Be explicit that an unverified
claim should not be scored as if it were proven.

### F. The three highest-leverage changes
Ranked by points gained per unit of effort, with the deadline in mind
(submission 16 October 2026, Demo Day 3 November).

### G. Honest total
Give the substance subtotal out of 60, and a **provisional** full-rubric
estimate out of 100 with the four deferred dimensions estimated and clearly
flagged as estimates. State your confidence in that estimate.

---

## 6. Do not do these

- Do not score effort. Twelve completed slices is not a score.
- Do not let the project's honesty about its limits earn points by itself.
  Admitting a gap is better than hiding it, but the gap is still a gap.
- Do not treat "nobody else has built this exact thing" as proof of value.
- Do not recommend adding features. The submission is five days out.
- Do not restate the project's own marketing copy as your assessment.
