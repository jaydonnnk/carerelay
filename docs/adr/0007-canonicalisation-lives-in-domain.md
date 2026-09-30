# ADR-0007: PlanBack canonicalisation lives in `domain`, not in the model

- **Status:** **accepted** — 28 September 2026, at Gate 4 approval
- **Date:** proposed 2026-09-28; accepted 2026-09-28
- **Source:** `03-program-design.md` §3; `spike/kill_spike/planback.py`; `04-slices.md` §1.1
- **Supersedes:** —
- **Amends:** the Gate 3 `compare_plan` signature (amendment accepted at Gate 4)

## Context

PlanBack asks the patient to restate their plan and decides whether it matches. Comparing raw text would be useless: "today before six", "by 6 today", "今天六点前" and "today before 18:00" are the same instruction. Some layer must **canonicalise** the restatement into policy values before comparison.

The Gate 3 contract says:

```python
def compare_plan(expected: Disposition, extracted: ExtractedPlan,
                 action_aliases: Mapping[str, str]) -> PlanComparison: ...
```

with `ExtractedPlan.action_id: str | None`. **That signature does not say where canonicalisation happens**, and the two readings give materially different results:

| Reading | What the coordinator returns | Consequence |
|---|---|---|
| **A** — canonicalisation in `domain` | Raw spans: `"today before six"` | The paraphrase / alias / relative-time / code-switched corpus is testable as **ordinary deterministic code**. K1 closable offline. |
| **B** — canonicalisation in the model | An already-canonical `action_id` | The corpus only reaches the model. **K1 cannot be closed without a live coordinator.** |

Building the kill-test spike surfaced this. The spike was written under Reading A, and its result depends entirely on that choice — which means shipping Slice 1 without pinning this would make the K1 evidence ambiguous.

## Decision

**Canonicalisation lives in `domain`.** Reading A.

`compare_plan` is widened with the policy's resolution tables passed as explicit data:

```python
def compare_plan(
    expected: Disposition,
    extracted: ExtractedPlan,
    *,
    action_aliases: Mapping[str, str],
    owner_aliases: Mapping[str, str],
    allowed_actions: frozenset[str],
    allowed_owners: frozenset[str],
    deadline_forms: Mapping[str, tuple[int, str]],   # relative phrase -> (day offset, local HH:MM)
    now_utc: datetime,
    display_tz: tzinfo,
) -> PlanComparison: ...
```

The coordinator returns **raw spans**. `domain` resolves each span against the policy tables and then compares canonical values.

Two rules that must survive the change:

- **`ExtractedPlan` carries both the raw span and `uncertain_fields`.** A span the extractor is unsure about is not the same as a span it did not produce. Collapsing the two re-creates the "unknown becomes an accusation" defect that K1 exists to catch. The Gate 3 draft's `uncertain_fields: frozenset[str]` and the spike's nullable spans are **both** required.
- **Unknown is `uncertain`.** Never a mismatch, never a match. Only a known, different canonical value is a mismatch.

## Consequences

**Good**

- The K1 corpus — paraphrase, alias, relative time, code-switched Mandarin — becomes testable offline, with no model, no network and no credentials. Confirmed on 2026-09-28: 15 tests, 0 failures, including four defect-injection tests.
- A false mismatch caused by bad alias coverage is a **policy data** bug, fixable without touching the model.
- The rule "the model interprets, code decides" (ADR-0002) is preserved literally. Under Reading B the model would be making the decision, which contradicts the architecture's headline claim.
- Silence about an uncertain field stays distinguishable from a wrong answer.

**Bad / accepted debt**

- `domain` now needs the policy tables. Its signature is wider, and every caller must pass them.
- Alias and relative-time coverage becomes a **maintenance obligation**. A missing alias is a false mismatch, which is one of the pre-registered cut conditions. The policy table needs its own test, not just the comparator.
- Relative-time resolution needs `now` and a display timezone inside `domain`. That is not a wall-clock read — the value is injected, so the import boundary holds — but it does mean `domain` functions are not purely value-in/result-out without a clock argument.
- **The residual under Reading B is real and must be stated:** if the coordinator cannot return raw spans, K1 weakens to "the deterministic layer is correct **given** correct extraction", and the claim must be made at that strength.

## Reversal

Reversible at Slice 4 boundary, and the reversal is stated rather than silent. Under Reading B, the offline K1 result no longer supports the cut rule on its own and the claim is weakened accordingly.

**Accepted 28 September 2026 at Gate 4 approval.** The amendment to the approved Gate 3 `compare_plan` signature is now part of the approved plan. Implementations from Slice 2 onward use the widened signature above, and `ExtractedPlan` carries both the raw span and `uncertain_fields`.
