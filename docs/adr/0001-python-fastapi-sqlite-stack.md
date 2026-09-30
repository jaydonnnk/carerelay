# ADR-0001: Python 3.13 + FastAPI + SQLite with a server-rendered UI

- **Status:** accepted
- **Date:** 2026-09-25
- **Source:** `02-architecture.md` D1
- **Supersedes:** —

## Context

CareRelay needs one small backend owning policy versions, episode state, clinical deadlines, consent and the action ledger, plus an accessible text-first interface for community-dwelling older adults. It is a solo build with a hard deadline. Two stacks were live: Python and Node/TypeScript. The runtime question could not be answered by the platform SDK alone, because platform access was unproven.

Three forces decided it:

1. **Testability of the safety mechanism.** The product's central claim is that a deterministic comparator, not a model, decides whether a restatement matches. That needs a test harness the author can run offline, repeatedly, with injected faults. pytest plus a pure-function core does that directly.
2. **The UI must be accessible and small.** The interface is four lines of text and one question at a time. A framework and a build step would add failure modes for no gain.
3. **SQLite fits the actual concurrency.** One local demo, one writer at a time, serialised by `BEGIN IMMEDIATE`. A network database would be unearned infrastructure.

## Decision

**Python 3.13, FastAPI, SQLite (WAL, busy timeout), server-rendered plain HTML and vanilla JS. No framework, no build step.**

Layered as: `domain` (pure) → `state` (repositories) → `service` (use cases) → `api` (FastAPI) → templates.

## Consequences

**Good**

- The deterministic core is a pure function and is testable without a server, a database or a clock.
- Fault injection is cheap: seven seam sequences can be exercised as ordinary unit tests.
- No build step means the demo cannot fail to build.
- Matches the throwaway HTML mockups already approved at Gate 1.

**Bad / accepted debt**

- FastAPI's request/response models and the domain's frozen dataclasses are two type systems held in parallel. The boundary must be tested (`tests/test_api.py`) or they drift.
- SQLite's concurrency is a single writer. The callback dedupe design depends on `BEGIN IMMEDIATE` and is an acknowledged hypothesis until proven.
- Python gives no compile-time check on the import boundary. **`test_domain_import_boundary` is the substitute and must be fail-capable** — see ADR-0002.

## Reversal

**The only reversal point is before the first domain-code commit.** After that, the choice is expensive.

Trigger for reconsidering: the Gate A access spike shows the WorkBuddy SDK is materially better from Node and the platform path cannot be reached from Python. Because Gate A has not passed, this remains a live possibility rather than a closed question.

An **environment check** (venv creation, FastAPI + pytest install) must run before Slice 1. `AGENTS.md` records an intermittent AppControl block on stdlib venv creation, which would make the stack unusable regardless of merit.
