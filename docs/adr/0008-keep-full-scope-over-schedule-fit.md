# ADR-0008: Keep the full scope and record the schedule risk, rather than cut

- **Status:** accepted
- **Date:** 2026-09-28
- **Source:** user instruction, 28 September 2026; `03-program-design.md` §7; `04-slices.md` §5
- **Supersedes:** —
- **Related:** `DESIGN_PRINCIPLES.md` §4 (scope and ambition)

## Context

On 28 September 2026 the remaining work was estimated at **102–169 person-hours** for a full-scope slice plan, plus the Gate A spike, recruitment, the Option C source check and submission assets.

The constraint:

- Submission deadline: **16 October 2026**.
- Time available: **18 calendar days**, solo.
- At 8 h/day that is **144 hours total** — assuming no lost days, no retries, no recruitment slippage and no rest.

The estimate's central value sits near **135 h**. The upper end does not fit at all.

`03-program-design.md` §7 predicted exactly this and set a rule for Gate 4: the plan

> "must sequence the baseline first and assign explicit dates and stop conditions; it must not silently remove the Closure Contract tests to make the schedule look green."

`02-architecture.md` §12 was blunter: "**Either the estimate or the scope changes at Gate 3, and this document does not pretend otherwise.**"

The two available responses were genuinely in conflict:

1. **Cut scope** to fit the deadline, protecting the submission.
2. **Keep the full scope** and accept that the schedule may not fit.

## Decision

**Keep the full scope. Record the schedule risk explicitly as the plan's primary risk (R1) rather than resolving it by cutting.**

Nothing was cut. No Closure Contract test was removed. The plan states the honest arithmetic in `04-slices.md` §5 — 102–169 h against 144 h available — and names the failure mode instead of hiding it.

Three design choices make a partial build still coherent if the schedule fails:

1. **The kill tests run first (Slice 0).** The largest available risk reduction costs almost nothing and precedes all participant work.
2. **The baseline kill test runs before the Closure Contract build (Slices 7–8 before Slice 9).** Constraint C1 from the round-2 review is satisfied, not deferred.
3. **Slices 0–6 alone are a demonstrable product** with the headline mechanism working end to end. If the build stops there, the submission is smaller and honest rather than six half-built layers.

## Consequences

**Good**

- The largest risk reduction in the project — the two reviewer-free kill conditions — is cheap, runs first, and is unaffected by the schedule.
- The scope the user chose is preserved rather than quietly trimmed to make a plan look achievable.
- The kill test lands before the mechanism it might falsify, so a negative result costs almost nothing.
- A partial build is a coherent submission, not a wreck.

**Bad / accepted debt — stated plainly**

- **The deadline is genuinely at risk.** The plan fits only if almost nothing goes wrong. This is recorded as R1, not mitigated away.
- Submission assets (Slice 12) fall on 17–18 October, **past** the 16 October deadline, unless earlier slices compress.
- Running recruitment, the source check and Gate A in parallel with the build increases coordination load at exactly the point attention is scarcest.
- The honest record now carries a visible tension between an accepted scope and an unaccepted schedule. That is the intended outcome: the tension is real, and hiding it would be worse.

**What this does not do**

- It does not authorise code. Gate 4 is still a draft until the user approves it.
- It does not remove the R1 replan trigger: **any slice overrunning its window by more than 50% means telling the user and replanning** — not absorbing the overrun by quietly dropping tests.

## Reversal

Fully reversible, at any point, by the user choosing to cut scope. The recorded cut order in `02-architecture.md` §1 already exists and is pre-agreed: D9 (already cut), the second simulated adapter and caregiver channel, Chinese UI strings, then TRTC voice.

**If the user reverses this decision, the plan is replanned against the cut order — and the front-loaded kill tests remain, because they are cheap and independent of scope.**
