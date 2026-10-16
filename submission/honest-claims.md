# Honest claims: what CareRelay can and cannot be said to have done

This file is part of the submission. It exists because a statement of limits that is
written after the claims is easier to soften than one written beside them.

## 1. What the project is

A research demonstration of two mechanisms, built for Challenge 1. Every screen,
every provider response and every episode carries a simulated label. The label is
inside the serialized patient projection, not only in page chrome
(`src/carerelay/demo/fixture.py:50`; D11).

## 2. Claims the project makes

| Claim | Status |
|---|---|
| The four-line patient rendering is shown for all four closure states | **[verified]**, proven live with `curl` at Slice 10 (`00-status.md:409-416`) |
| Closure is derived from two independent axes and never stored | **[verified]**, with precedence tests (`03-planback-closure-contract.md:135-145`) |
| The record is append-only on both engines | **[verified]**, by trigger refusal tests on SQLite and Postgres |
| Seven seeded fault sequences hold the five invariants at both surfaces | **[verified]**, `tests/test_fault_sequences.py` |
| Domain imports no network, no model client and no clock | **[verified]**, by a scanner with a fail-capable self-test |
| The whole repository was built with WorkBuddy and CodeBuddy | **[verified]**, `docs/session-logs/` plus three redacted chat screenshots |

## 3. Claims the project does not make

**No clinical claim of any kind.** It is not clinical advice, not a medical device and
not validated for patient use. No clinician reviewed it; `approved_by` is `NULL`
(`docs/PLAN.md:257`, `:482`). The fixture was authored rather than sourced from
published guidance, so it asserts no clinical content at all
(`03-program-design.md:251-256`).

**No human-centred validation.** The comparison study was cut before a dyad ran: no
participants were recruited and no second scorer was named. There is therefore **no
Gate B result, and this is not a null result**. The cut is one the slice plan
pre-recorded (`04-slices.md` section 7, stop condition 4) and it was executed on
8 October 2026 (`00-status.md:38`). The instrument that was built is kept as design
evidence and is not a deliverable (`src/carerelay/study/`).

**No claim about how common the problem is.** The prevalence of the specific failure
CareRelay targets is **[unknown]** (`docs/PLAN.md:108`). "Users fail to act after
correct advice" is a **[hypothesis]** (`AGENTS.md:169-174`).

**No claim that AI triages anything at runtime.** Current state, 16 October 2026: Tencent ADP is off by default.
When it is explicitly configured, its only job is to copy phrases for the action, time and who acts out of words the patient confirmed, or to mark them unclear, or to refuse.
CareRelay code validates that reply, locates the phrases and compares them with the stored plan; the model does not diagnose, choose urgency, prescribe, change a deadline, grant permission, send a request or declare care complete.
Offline, a labelled local stand-in does that step, and the judge view says Tencent ADP was not contacted.
Every execution result still carries `origin = local-sim`. ADP tool execution, platform-originated failure events and session resume remain **[unknown]** (`02-architecture.md` sections 13.6 and 14).
Live evidence is a small fictional sample through the guarded local product, not general reliability (`00-status.md`).

**No clinical triage functions.** This build has no clinical symptom assessment, no warning-sign detection, no validated self-care guidance, no dynamic clinical reassessment and no fairness validation across patient subgroups.
Refusing a clinical question is a scope guard, not evidence of calibrated clinical triage.
A stopped conversation or a failed request does not mean anyone has taken over.

**No integration with any healthcare service.** Working alongside HealthHub or Health Buddy is a possible future role only. No connection, data exchange, agreement or endorsement exists.

**No measured benefit.** Patient benefit, clinical safety and superiority over existing apps are unmeasured.

**Judge-view timing is not click-to-screen.** The stage's "Checked in" chip reads server time from a check's stored claim to its stored completion. Under the fixed demo clock that time is not measured, so the chip is not shown. The 5.1 to 6.2 second figures on `/demo` are dated measurements from the 16 October live runs, not live readings.

**No claim that the platform carries the mechanism.** PlanBack and the Closure
Contract are application logic and do not require WorkBuddy
(`03-planback-closure-contract.md:19`). The platform claim is about how this
repository was produced, which is separately evidenced.

**Prohibited outright:** any cognitive-improvement claim, screening claim, risk score,
"world-first" claim, clinical validation claim, or avoided-admission claim
(`01-product.md:126-132`).

## 4. Scope limits that a judge will meet in the demo

- **Fixture-bound.** One bound complaint is recognised, by exact normalised match.
  Anything else is refused with HTTP 422. No red-flag vocabulary, no negation handling
  and no third-party-subject handling is authored (`00-status.md:524-528`).
- **Mandarin is aliases, not voice.** Mandarin forms exist in the fixture tables; the
  voice path was a gated spike that was never built, with no account access and no
  demonstrated accuracy (`AGENTS.md:453-457`).
- **Scheduler dropped (D9).** There is no timed reassessment. Expiry is evaluated on
  read, never by a background job (`02-architecture.md:35`).
- **Reassessment vocabulary is empty** by design, so a change report routes to the
  human path (`src/carerelay/demo/fixture.py:148`).

## 5. Open items, disclosed rather than deferred

| Item | State |
|---|---|
| **1 of the 5 fault assertions is falsifiable today; 4 are display only** | Measured and reported by the harness rather than folded into a coverage total (`00-status.md:474-478`) |
| **Crash atomicity (O8) is proven on SQLite only** | The deployment store is Postgres, whose `record_callback_once` no fault sequence exercises (`00-status.md:438`) |
| **The comparator card was never rendered in a browser** | It is a standalone printable HTML file, verified structurally (`00-status.md:376`) |
| **Log redaction (NF6) is unimplemented** | There is no logging to verify it against yet (`tasks/todo.md:120`) |
| **The secret scanner does not catch the credential form that actually leaked** | A bare value in prose is invisible to it. The operative control is that no value is written in a document (`tasks/todo.md:144`) |
| **A rotated database credential remains in the repository's git history** | Committed on 5 October 2026 and rotated the same day. The working tree carries no credential; the history is disclosed rather than rewritten, because rewriting it would falsify the record (`AGENTS.md:487-498`) |
| **Credential-bearing `.env.example` values remain in git history** | [verified 16 October 2026] Commits before `abd2c3f` carried non-empty `CARERELAY_API_TOKEN`, `ADP_APPKEY` and `ADP_API_SECRET` values, and that history is on the public `origin/main`. `abd2c3f` cleared them in the working tree. A hash comparison found the historical token and API secret equal to current local configuration values, so they need rotation; no rotation or history rewrite was done in Slice 23. The repository is not claimed to be credential-free. |
| **The Supabase free tier pauses after inactivity** | Accepted as handled: the project is kept warm until the submission deadline |
| **Deployment region and processor arrangements under PDPA** | **[unknown]** (`AGENTS.md:480-481`) |

## 6. Data handling

Fixture and dyad data only. No real patient data, retained for 30 days after
submission and then destroyed (`02-architecture.md:298`). One disclosure is made
rather than left for a reader to find: `events.payload` holds the raw confirmed free
text the patient typed, so the record is not anonymous at the field level
(`src/carerelay/state.py:1778-1781`). No fixture names a real facility
(`01-product.md:146`).

## 7. What we ask a judge to hold us to

Every number in `description.md` should resolve to a file, a test or a labelled
hypothesis. If one does not, that is a defect in the submission and we would rather
hear it than win with it.
