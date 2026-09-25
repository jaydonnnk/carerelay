# Adversarial review, round 2: CareRelay Gate 2 architecture

Date: 25 September 2026. Reviewer: independent session, no involvement in writing
`02-architecture.md`. Document under review: `docs/plans/urgent-advice-accessibility/02-architecture.md`
at commit `1cb05c8` plus the working tree (AGENTS.md modified, `gate2-review-prompt-thorough.md`
untracked). Scope: whether this architecture delivers the approved Gate 1 product, not whether
that product is a good idea.

Labels used as in `PLAN.md` §0: **[verified]** read in a file, **[inferred]** my reasoning from
read material, **[opinion]** my judgement with no file support. Probability and effort figures are
estimates unless marked otherwise.

---

## 1. VERDICT

**APPROVE WITH CHANGES.**

The module split and the decision frame are the right shape for the approved product, but three
defects make the architecture's own headline claims unimplementable as written: the §4 data model
cannot record an attempt's state transition, the tool execution path that constitutes the
organiser-dependency proof is contradicted by five separate sections, and the D6 baseline arm
cannot measure the Gate B kill test the project depends on. Fix those in the document before
approval; do not carry them into Gate 3 as "the implementer will resolve it".

---

## 2. The three findings that would embarrass me most

### Finding 1 (highest): the §4 schema cannot record the demo it claims, and the failure is silent

`02-architecture.md` D3 (§1, row D3) states attempts are INSERT-only. §4 declares
`attempts.idempotency_key UNIQUE` and gives the attempt a `status` enum
(`attempted | acknowledged | failed | expired`), and §4's query list defines the execution
projection and closure as pure functions over attempts plus evidence. These three statements
cannot all hold.

Sequence of events that breaks it:
1. Patient taps Execute. `POST /api/episodes/{id}/actions` (§3.1) inserts
   `attempts(route_id=clinic-sim-01, idempotency_key=K, status=attempted)` and dispatches the tool call.
2. The adapter acknowledges. `POST /api/episodes/{id}/callbacks/{route_id}` (§3.1) arrives and must
   move that attempt to `acknowledged`.
3. That write is either (a) an UPDATE, which violates D3's INSERT-only claim, or (b) an INSERT of a
   second row for the same attempt, which `UNIQUE(idempotency_key)` blocks or, with the
   `INSERT ... ON CONFLICT DO NOTHING` prescribed in §4, discards with no error and no record.

Under (b) the acknowledgement is lost, the projection keeps showing `attempted`, and the patient's
screen shows the four lines of an unresolved episode while the clinic has in fact accepted. That is
a false *negative* completion, which the product has no rule for at all. The demo's own step 4
(§5.1, "attempt `failed`") has the same problem: `failed` cannot be written to an INSERT-only,
uniquely-keyed row.

Consequence for Gate 2's purpose: the assertion-discipline surface collapses. The seven seeded
fault sequences in `PLAN.md` §9 are meant to assert the five invariants; duplicate callback,
reordered callback, timeout and stale availability all require a writable per-attempt state
history. As specified, four of the seven are unwritable. Nothing catches this. I3 (idempotency) is
*satisfied* while the state is wrong, which is the worst possible failure mode for this product.

### Finding 2: the organiser-dependency proof is unpinned, and its fallback is observationally identical

The submission's central claim is that a real platform tool call produces a real platform failure
event (`02-architecture.md` §3.3: "The demo's failed booking must be a *real* platform tool-failure
event, not a thrown exception we scripted locally, that distinction is the dependency proof").
Five sections describe this call differently:

| Section | Who executes the tool |
|---|---|
| §2 boundary rules | Coordinator "reaches the world only through `tools/`" |
| D8 (§1) | "MCP tools are executed server-side by our backend with authorisation + consent checked at execution" |
| §3.2 | "All six: server-side authorisation" |
| §3.3 | "Backend → WorkBuddy managed agent via cloud-agent SDK ... receive tool-call requests and tool-failure events" |
| §5.1 step 4 | "coordinator invokes `submit_simulated_request` → adapter fails as scripted → the failure returns through the platform" |

If the coordinator invokes the tool, the failure event is the platform's, and the backend is the MCP
server enforcing authorisation. If the backend invokes the adapter directly, the platform is not in
the path and the demo looks *identical* on screen. Gate 3 can wire either reading from this document
without contradicting it.

Failure scenario, on the deadline: Gate 3 wires a direct backend call for speed (fewer moving
parts, no session to manage in a demo), the ledger shows a failed attempt, the demo still tells the
story, and the "real platform failure event" claim in the submission is unsupported. The fallback
in §6 item 5 makes this worse rather than better: on Gate A failure the architecture reverts to
local simulation "with honest labels" and "platform-advantage claim weakened", but nothing in the
architecture requires the local failure to be *distinguishable* in the ledger from the platform
one. A judge who asks "how do I know that failure was real?" has no artefact to inspect.

### Finding 3: D6's baseline arm cannot measure the kill test

`01-product.md` defines the success metric: six dyads, a **deliberately failed simulated handoff**,
and 0 of 6 incorrectly reporting that care has been arranged, compared against a fixed
instruction-card baseline. `research-workarounds.md` (Blocker responses, "Baseline is too weak")
requires the comparator to carry identical clinical wording, legitimate options and a direct
booking link. D6 implements the comparator as `episodes.arm ∈ {carerelay, card}` in the same
backend, "PlanBack and the ledger disabled".

That arm cannot produce the outcome the metric measures. A fixed card plus a booking link has no
action execution, therefore no failed handoff, therefore no opportunity to believe a failed handoff
succeeded. The comparison is asymmetric by construction: the card arm can only be scored on recall
and burden, while the CareRelay arm is scored on recall, burden *and* false completion, and the
false-completion half is where the reframe's whole claim lives.

Two secondary validity problems in the same decision: (a) "counterbalanced dyads" (D6) means
within-subject cross-over on the same fixture, and comprehension carry-over from PlanBack to the
card arm is severe and unaddressed; (b) serving the card inside the same accessible app chrome
erases the card's real advantage (lowest burden, `02-adversarial-review.md` §D), which is precisely
the advantage the kill test is supposed to measure.

Failure scenario: the study runs, both arms show 0/6 false completion, the headline is "no
difference", and either PlanBack is cut on an invalid test (losing the product) or kept on an
invalid test (losing the evidence). This is the project's primary kill test, and the architecture
does not operationalise it.

---

## 3. Existential risk estimate

**[opinion, estimate]** Probability this reaches a *scoring* submission by 16 October: **45 to 60
percent.** Probability of a *competitive* submission in the `PLAN.md` §11 conditional band
(73 to 84) : **20 to 30 percent.**

Reasoning:

- Eligibility is the cheap half and is probably winnable. The handbook requires "built on at least
  one of CodeBuddy or WorkBuddy" with proof, and accepts "a written development-process
  description" (`CHALLENGE_REQUIREMENTS_JUDGING.md` §8, lines 126-129). Genuine CodeBuddy
  development history plus three screenshots satisfies the letter even if Gate A fails, as
  `research-workarounds.md` already concedes.
- Schedule is the expensive half. Today the repository is documentation-only (27 tracked files, no
  code, `[verified]`). Two more gates need writing and approval after this one, plus the baseline
  comparison (20-35 h, `03-planback-closure-contract.md` §3.1), plus the build, plus 3-6 dyad
  sessions, plus submission assets (8-14 h, §6 of the same file), plus the mandatory proof capture.
  `PLAN.md` §7 puts the solo text-only package at 110-160 h across 21 days, which is 5 to 8 hours
  every single day including the days lost to gate review and clinical/recruitment chasing.
- The kill test has not run and has no date. `03-planback-closure-contract.md` §6 puts it at step 2,
  correctly before the contract build, but `PLAN.md` §7 schedules "frozen tests and formative
  sessions" for 1-7 October, after the state machine is built. If Gate 4 does not place the
  comparison first, the project funds a mechanism that may be cut.
- Gate A is due tomorrow, 26 September, and Gate 2 is unapproved today. The pre-recorded decision
  point arrives before the document that owns it is approved. If approval slips two days, the spike
  slips, and the D9 activation question (Gate A plus a Gate 3 estimate) pushes into the week the
  build should start.

If Gate A fails, the fallback is survivable for product integrity and **not** survivable for the
platform-advantage claim, and the architecture says the second part honestly in §6 item 5. What it
does not say is the consequence: the five-minute demo's most quotable moment ("a real organiser
tool call fails") becomes a scripted local failure, and Technical Execution and AI Interaction lose
their strongest evidence, exactly as `03-planback-closure-contract.md` §5 admits. The fallback
preserves eligibility, not marks.

---

## 4. Surface-by-surface results (A to J)

### A. Existential risk

Covered in §3 above. Two additions the architecture introduces and does not own:

- It commits an unestimated amount of new work (§6 below) on top of the 56-89 h figure it inherits,
  before any slice exists.
- Approving Gate 2 pins the stack (D1) and the two-arm design (D6) before Gate B has run, so the
  design decision precedes its own falsifier. That is defensible only if Gate 4 sequences the kill
  test first. That requirement is not stated anywhere in the architecture.

### B. Breaking the safety guarantee

Path by path, with the invariant that catches it:

1. **Stale read or cache between callback and deadline.** Closure is derived at read time (D4), so
   it is as correct as the read. No cache policy is stated. Nothing catches a 30-second page cache
   rendering `open` as `closed_with_evidence` or the reverse. I2 is a rendering rule, not an
   observable assertion.
2. **Race: `POST actions`, late callback, deadline passes.** Partially covered by I2 and I3, and
   fully broken by Finding 1 above. Also undefined: what an `acknowledged` callback does when the
   closure is already `expired_unresolved`. Nothing catches it.
3. **Exception or partial write mid-append.** Nothing catches it. No transaction boundary is stated.
   `attempts`, `events`, `evidence` are separate INSERTs in §4; a crash between them yields a ledger
   that disagrees with itself with no invariant covering referential consistency.
4. **`expired_unresolved` readable to a 72-year-old.** Nothing catches it, and there is a
   contradiction: `01-product.md` fixes the patient screen at four lines whose third line is
   "Before [deadline]" and whose wording presumes a future deadline
   (`03-planback-closure-contract.md` §2.5). After expiry that line is false, and no expired
   rendering exists in the architecture, the product rules or the mockups. The one state the product
   exists to report has no approved words.
5. **Paraphrase in a summary or notification string.** Currently no such string exists: the
   architecture defines no summaries, coaching text or notifications. The risk is therefore absent
   by omission, not caught. The architecture should state explicitly whether any model-generated
   text can ever reach the patient, because that property is currently a side effect of a missing
   feature rather than a design rule. One exception exists: `/api/episodes/{id}/barriers` returns a
   route "proposed from policy content only" by the coordinator, and "policy content only" is a
   prompt instruction, not an enforcement.
6. **`simulated: true` lost in transit.** Schema carries `evidence.simulated` (§4) and §2 asserts
   "Nothing can launder a simulated receipt into a real one". Nothing enforces it: no constraint, no
   assertion, no test is named, and the patient projection has no simulated field at all
   (the label lives in mockup page chrome, `mockups/03-unresolved-handoff.html` lines 36 and 79,
   outside the four-line block). Given `AGENTS.md`'s rule that an absence assertion must prove the
   needle can match the serialised surface, this claim is currently unproven and untestable.
7. **Coordinator output trusted where it should not be.** §2's boundary (coordinator never writes to
   the DB, never sees credentials, returns structured outputs) is the right control and I could not
   find a hole in it. One residual: a coordinator-proposed route id must be validated against the
   policy's permitted set in `domain` before execution. That closed-vocabulary check is specified
   for PlanBack's `action` comparison (`03-planback-closure-contract.md` §1.4) but not for
   coordinator proposals. Without it, a hallucinated route reaches the tool layer, and nothing
   catches it.

### C. Assertion discipline: can the seven fault sequences actually be written?

| Seeded fault (`PLAN.md` §9) | Writable against §4 as specified? | Assertion |
|---|---|---|
| Timeout | No. Requires a `failed` or `expired` transition on an INSERT-only, uniquely-keyed attempt. | I1 and I2 would apply, but the write path does not exist. |
| Stale availability | Partially. The adapter is scripted so the event can be injected, but no table records an availability observation or its age, so "staleness did not produce an acknowledgement" has no evidence surface. | Weak I5 only. |
| Duplicate callback | No. No callback record exists. §5.1 step 6 requires the ledger to "show the dedupe", but the only dedupe target is the attempt's own key, which would swallow the legitimate first acknowledgement. | I3 asserted over a surface that cannot hold it. |
| Reordered callback | No. No per-route transition ordering is defined. An `acknowledged` arriving after a `failed` for the same route has no defined winner. | Nothing catches it. |
| Restart mid-episode | Yes on the application half (state in SQLite, `Clock` injected). The WorkBuddy session-resume half needs live access. | I1, I3, I4 assertable. |
| Clock change | Partially. `APP_CLOCK=scenario` makes it injectable, but expiry is derived at read time, so a backwards clock un-expires an expired episode. No expiry event is written. | I1 assertable. Expiry stickiness is not. |
| Consent revocation | Partially. `consents` rows support revocation, but the in-flight window is unasserted (see the missing fault classes below). | No invariant covers it. |

**Invariant set completeness.** I1 to I5 are necessary but not sufficient. Missing classes, each
with a concrete scenario:

- **Concurrent writers / double-tap.** Two Execute taps 300 ms apart. If the client generates a new
  idempotency key per request (nothing in D5 or §3.1 says otherwise), I3 does not fire, two tool
  calls dispatch, one succeeds, one fails, and the episode holds mixed attempt state. I3 catches
  this only if key derivation is specified as stable per route attempt and server-generated.
- **Adapter returns 200 with a lie.** A scripted "receipt" with no evidence. Needs an evidence
  provenance invariant: level `documented` requires a non-simulated, sourced artefact; a simulated
  receipt can never reach `documented`. Nothing covers it today, and D4's closure rule
  (`closed_with_evidence`) would accept the lie.
- **Clock going backwards.** See the table above.
- **Write failure mid-append.** Atomicity of (attempt, event, evidence) is unstated.
- **Consent revoked between authorisation and execution.** The consent check happens at execution
  (§3.1, `/actions`), but the tool call is a network round trip. A revocation landing inside that
  window does not stop the dispatch, and the resulting attempt and evidence exist without valid
  consent. This is a PDPA-relevant window, not a theoretical one.
- **Expiry with nobody watching.** `expired_unresolved` is derived, and nothing runs at the
  deadline. There is no notification path to the patient or caregiver anywhere in the architecture,
  and the only scheduler is dark (D9). At 18:01 the system does nothing and no record says it
  should have.

### D. Decision-by-decision

| # | Verdict | Reason |
|---|---|---|
| **D1** | Agree, restate the trigger | Python/FastAPI/SQLite is the right solo default. But "reversible only at the Gate A spike" is nominal: with no code in the repository, any switch is free until the first domain commit, and the spike cannot answer "is the SDK materially better from Node" without access. Say "before the first domain commit" and add an environment check (Python 3.13, venv, dependency install) before Slice 1. |
| **D2** | Agree, strongest decision in the document | Import rules and no-I/O domain beat discipline-based boundaries. Gate 3 must name the enforcing check and make it fail-capable, or it is a convention with a diagram. |
| **D3** | Agree in intent, broken as specified | Deadline on the disposition row and versioned reassessment is right. The INSERT-only attempt is self-contradictory (Finding 1). |
| **D4** | Agree, incomplete | Derived closure removes the write path for "resolved" and that is a real gain. But the closure function's inputs include "human acceptance", which has no table and no endpoint; `escalated_to_human` has no recording path; read-time expiry is not sticky. |
| **D5** | Agree, under-specified | Ports for clock and idempotency are the right call. Key derivation, callback dedupe semantics and the conflict with §4 are unstated. |
| **D6** | Unproven, revise before Gate 3 | The arm flag does not implement the kill test (Finding 3). |
| **D7** | Agree in intent, unproven in mechanism | Deterministic abstention with the urgent path rendering synchronously is right. "The urgent path never passes through the coordinator" holds for rendering, not for detecting free-text symptom change: turning "I feel much worse and I am suddenly confused" (`mockups/04`) into a policy input is either model work (contradicting D7) or a keyword rule (contradicting "the model interprets"). Neither is chosen. |
| **D8** | Agree, with one condition | The honest dependency is stated correctly and it is what Gate A must prove. Condition: pin who executes the tool (Finding 2) and define the degraded branch when the coordinator is unavailable, because it sits on PlanBack's critical path. |
| **D9** | Wrong as written, cut now | It has no scenario, no trigger, no recheck content, no ingress endpoint, no estimate, and an 8-hour cadence that contradicts the same-day demo. It is also the only place the P1 load-bearing claim could be proven, which makes it a Gate A and planning question, not a module in this architecture. |
| **D10** | Agree | Voice isolated behind the transcript-confirmation rule and the release gate is the right containment. |
| **Cut order** (voice → scheduler → extra channels) | Wrong order | Voice is already deferred, so cutting it first frees nothing: the order is decorative. Scheduler should go first today. The real relief is D9 plus the second adapter plus the in-app baseline arm, none of which appear in the order. |

### E. Organiser dependency

The requirement is "built on at least one of CodeBuddy or WorkBuddy" with proof
(`CHALLENGE_REQUIREMENTS_JUDGING.md` §8). The architecture's substrate claim is honest and, on the
letter of the rule, more than sufficient. Three findings on the gap between the claim and what the
document pins:

1. **The tool-execution ambiguity (Finding 2)** is the difference between a real platform event and
   theatre, and it is currently unresolved.
2. **§7's carried-risk mapping is wrong on the first row.** It maps "Organiser-usage proof absent" to
   "D8 + Gate A spike questions; CodeBuddy fallback pre-recorded". D8 does not produce usage proof:
   proof is *development* history (`CHALLENGE_REQUIREMENTS_JUDGING.md` §8, and minimum three
   screenshots, line 164), which is a capture obligation from the first CodeBuddy session onward.
   No owner, format, or date exists for it anywhere, and `.gitignore` correctly excludes
   `.codebuddy/` and `.workbuddy-ai/`, so the proof must be captured deliberately. This is the one
   artefact whose absence blocks scoring entirely, and the architecture does not mention it.
3. **Minimum genuine dependency that is both true and sufficient:** one WorkBuddy session that
   interprets, one tool executed through the platform whose failure event originates there, one
   session resumed across a real process restart, plus genuine CodeBuddy development history. D8
   describes exactly that; D9 is the only deeper candidate and is conditional. So the architecture
   has the real version of the minimum dependency, provided Finding 2 is pinned. If the platform is
   legitimately swappable, AI Interaction and Technical Execution fall back on the quality of the
   interpretation and the honesty of the state machine, which is a weaker but survivable position.

### F. Missing surfaces

Architecture problems, in priority order:

- **Assessment intake.** §3.1 has no route for the patient's initial description or the
  coordinator's clarifying questions, while `PLAN.md` §5 steps 1-2 and Challenge 1's first listed
  behaviour ("Conversational assessment") require both. §5.1 step 1 writes disposition v1 directly
  from the fixture at episode creation. As written, the product has no assessment conversation.
- **Option listing.** `list_simulated_options` is an MCP tool (§3.2); the UI-facing API has no GET
  for the options the patient chooses from, although mockups 03 and 02 both present choices.
- **Human acceptance and escalation records.** Required by D4's closure inputs and by
  `escalated_to_human`, absent from §3.1 and §4.
- **Degraded and error states.** No branch for coordinator unavailable or slow, adapter timeout, no
  permitted route, or deadline passed with no action.
- **Deployment and hosting.** Nothing. Whether the demo is local-only (uvicorn on 127.0.0.1) or has
  a live link (the submission's optional bonus) is undecided, and it changes the security picture.
- **Data retention and PDPA.** Append-only clinical-shaped tables plus study responses, with no
  retention rule, no erasure path and no overseas-transfer statement, against `PLAN.md` §8's
  explicit PDPA obligations. Note the tension: append-only and erasure must be reconciled
  deliberately, not by default.
- **Observability and logging privacy.** `events.payload` (§4) will contain clinical text. No
  redaction rule, no logging policy, no statement that payloads stay out of application logs.
- **Latency and cost budgets.** None. The five-minute demo's most dramatic moment is a platform call
  whose latency is uncontrolled, and Feasibility is a scored dimension that explicitly asks for
  measured cost and latency (`PLAN.md` §7 row 5).
- **Research-participant consent.** `study_sessions`/`study_responses` (§4) record human
  participants, but the `consents` table is clinical-scope consent, not research participation.
- **Secrets.** Handled well at the level of principle (env var names only, §6; `.env` gitignored,
  `[verified]`). Missing: how they are held for the demo.
- **Consent revocation mid-flight.** See surface C.

Not architecture problems (delivery artefacts, must still be scheduled):

- The trust-boundary diagram the submission requires. §2's ASCII stack is a module view; it is not
  a trust-boundary diagram with trade-offs. `03-planback-closure-contract.md` §6 already budgets it
  at 6-10 h, so it is planned, just not architectural.
- The blocked GitHub push. `[verified]` origin has only `refs/heads/care-relay-adversarial-review` at
  `2d7ec71`; local has three unpushed commits including the Gate 1 approval, and the Gate 2 branch
  has no upstream. The submission requires a complete GitHub source link. I did not attempt a push.
- The three development screenshots, the under-ten-word blurb and the 16:9 cover. `PLAN.md` §10
  tracks them; neither architecture nor trivia.
- The accessibility items the prompt lists (screen reader, keyboard, contrast, one question at a
  time) are UI commitments, not module decisions, with two exceptions that *are* architectural: the
  H2 timed hide (below) and the requirement that one-question-at-a-time be enforced by the patient
  projection rather than by page layout.

One accessibility conflict the architecture must decide rather than inherit: `PLAN.md` §5.2 and
`mockups/02` line 74 specify that H2 shows the plan card for **five seconds** then hides it. For a
screen-reader user, or a slow reader, that is an unreadable, un-extendable timer, and it conflicts
with the same document's accessibility commitments. Changing it reopens Gate 1, so the decision
belongs to the user, not to Gate 3.

### G. Flow walkthrough

**§5.1 main path.** Step 1 cannot be built as the approved product describes it (no intake
endpoint, F above). Step 2 is buildable but its extraction contract is undefined (field
vocabularies, mismatch semantics for "not sure" at H0). Step 4 has the ownership ambiguity
(Finding 2). Step 5 ("resume = WorkBuddy session restore + reload of application-owned state")
is the one step that is clean, because `PLAN.md` §6 already put state in the application. Step 6 is
unwritable (Finding 1). Step 7 renders "fault assertions" from a harness whose assertions cannot
currently be expressed. Ordering against Gate 1 rules: correct. No urgent guidance is placed after
read-back, and the emergency path is synchronous by D7. `mockups/02` Step A (transcript
confirmation first) matches `PLAN.md` §5.1 item 3 and `01-product.md`; that specific defect is
fixed.

**§5.2 reassessment/abstention.** A state reachable but not exitable: after the emergency stop of
`mockups/04` there is no defined post-stop state, no record of the escalation and no resume rule.
The interpretation gap from D7 applies: free text becomes a policy input by an unspecified
mechanism. The reassessment is also the only path allowed to set a new deadline (D3), and it is the
same path that bypasses the coordinator, so the most safety-critical clinical write in the system
sits on the least specified code path in the document.

**§5.3 conditional scheduler.** Not walkable. There is no ingress endpoint for the scheduler to
invoke, no definition of what a "recheck" asks, no clinical content authority, no estimate, and no
scenario: a same-day deadline of 18:00 makes an 8-hour recheck arrive after the deadline. The
multi-day "monitored episode" of `DESIGN_PRINCIPLES.md` §8 has no episode in which to live.

### H. Effort realism and the cut list

The architecture does not contain hours, and it inherits 56-89 h for the two mechanisms plus 20-35 h
for the baseline (`03-planback-closure-contract.md` §3.1, `PLAN.md` §7). What it adds on top of that
estimate is: a coordinator client with session create/resume/streaming, tool-call handling and
failure-event handling; a six-tool MCP surface with authorisation and idempotency; two scripted
adapters with callbacks; a fault harness of seven sequences; a judge-facing ledger view; dual-arm
study tooling and endpoints; and a full accessible UI replacing throwaway mockups. **[opinion,
estimate]** That is 90-150 h of build, not 56-89 h, and the baseline's 20-35 h on top of it. Against
21 days, that is not affordable with Gate 3, Gate 4, recruitment, the clinical chase and submission
assets still to come. Either the estimate or the scope has to change at Gate 3, and the document
should say which.

Cut list, deadline as the only argument:

1. **D9 and its multi-day persistence.** No scenario, no estimate, no endpoint, unproven access.
   Cost of cutting: the P1 load-bearing answer reverts to "execution substrate", which must then be
   stated plainly in the submission rather than deferred.
2. **The in-app `card` arm, replaced by a real card plus a scripted post-failure question.** Cheaper
   and fairer (Finding 3). Deletes the `arm` column, one projection and the study session tooling.
3. **The second simulated adapter and `notify_caregiver`.** The caregiver is a named owner string on
   the four-line screen, not a channel. Keep three MCP tools: `get_episode`,
   `submit_simulated_request`, `record_evidence`.
4. **Chinese UI strings, if no native reviewer is secured by mid-October.** The release gate in
   `research-workarounds.md` applies to critical Chinese *strings*, not only voice: native-speaker
   review plus bilingual clinical approval. The mockups are bilingual; the judged build need not be.
5. **Anything beyond one route, one adapter, one caregiver name.** Feature freeze stands.

The module isolation that makes cuts cheap is currently aspirational, because the modules are named
in §2 and not defined anywhere; it becomes real at Gate 3 when file and import boundaries exist.
Two of my five cuts are cheap today precisely because no code exists, which is an argument for
making them now rather than at Gate 3.

### I. Judge's-eye view

The harshest reading at Demo Day: "A status machine with a chat wrapper. The AI extracts three
fields, the booking failure is scripted, the baseline they beat is their own app with a flag
flipped, and the platform-advantage module is switched off in the architecture they submitted."

A clinician in the room would ask three things this document cannot answer: who actually answers
when the screen says "call 6262 6262" at 17:50; whether a read-back loop administered to a
72-year-old with a repair bound and a timed card display is a comprehension check or an informal
capacity test; and who reviewed the rule that turns "suddenly confused" into a 995 instruction
(`mockups/04`), given that no clinical reviewer exists.

Most quotable sentence against the submission, from §1 row D9: "the WorkBuddy scheduled recheck loop
... is a **defined but inactive** module". It tells a judge, in the authors' own words, that the
platform-specific part of the design is off by default.

### J. Discipline and process

The gate process itself is being followed honestly. No artifact claims an approval it does not have,
`00-status.md` line 3 and the approval section agree, PROGRESS.md does not imply a gate approval,
and the architecture correctly refuses to write Gate 3 and Gate 4 content (§8). Nothing found on
falsified gate state; I checked `00-status.md`, `PROGRESS.md`, `tasks/todo.md` and the gate documents.

Where documentation is substituting for progress, three concrete places:

1. **Stale mirrors of the Gate 1 approval.** `DESIGN_PRINCIPLES.md` §12 says "Gate 1 remains open and
   unapproved"; `03-planback-closure-contract.md` line 3 says "proposal, not Gate 1 approval" and
   line 7 says "Gate 1 is still pending"; `tasks/todo.md` lines 9-16 say approval is pending; and
   `00-status.md`'s own fresh-session notes (line 78) say "Not approved; Gate 1 remains open" while
   line 3 of the same file says APPROVED. `AGENTS.md` treats a stale mirror as a blocking finding.
2. **Unestimated scope presented as a pin.** D9 and the DESIGN_PRINCIPLES §9 items 1-3 were
   unestimated when Gate 1 was approved and remain unestimated, yet D9 appears as an architectural
   decision with a described loop.
3. **Claims of rigour beyond the artefacts.** D3 says I1 holds "by construction" when the enforcement
   is that no retry code path writes a disposition, which is a Gate 3 code-review property, not a
   structural one. §2 says "Nothing can launder a simulated receipt into a real one" while no
   mechanism, constraint or test exists, and `AGENTS.md` explicitly requires a scanner self-test for
   claims of this shape.

Smaller items: mockup numbering is stale after screens 04 and 05 were added (`01` says "Wireframe 1
of 4", `04` says "4 of 4", while `02`, `03`, `05` say "of 5"); the prompt file references
`gate2-review-prompt.md`, which does not exist in the repository; `docs/adr/` is an empty directory;
`PROGRESS.md`'s Result section still says "Gate 1 user approval remains pending". None of these is
individually serious; together they are the kind of drift that makes a fresh session misread the gate
state, which is the exact failure the file map in `00-status.md` was written to prevent.

---

## 5. Blocking changes before Gate 2 approval

1. **Make state transitions representable (§4).** Choose one model and write it: either attempts
   become per-attempt transition events (an `attempt_opened` row carrying the unique idempotency key,
   plus append-only transition rows), or a separate `callbacks` table with its own unique constraint
   and a defined "latest transition wins" projection. State the transaction boundary (the attempt,
   its event and the evidence write are atomic). Without this, I1, I2 and I3 cannot be asserted and
   four of the seven seeded faults cannot be written.
2. **Pin who executes the tool (§2, D8, §3.2, §3.3, §5.1).** State the call path in one place, and
   require that the failure event's origin is recorded in the ledger and visible in the judge view, so
   the fallback path is distinguishable from the platform path by inspection.
3. **Re-specify D6 against the success metric in `01-product.md`.** Define the card arm as the
   artefact the kill test names (card plus booking link, delivered outside the app), define what is
   asked after the scripted failed handoff, state the carry-over control or switch to a
   between-subjects design, and pre-register the primary outcome and cut rule.
4. **Add the missing endpoints and tables the flows require:** assessment intake and clarification,
   option listing, human acceptance, escalation/handoff, research-participant consent, and the
   scheduler ingress if D9 survives. If assessment is deliberately out of the judged slice, say so
   and state the consequence for Challenge 1 coverage.
5. **Decide D9 in this document:** delete it, or give it a scenario, a trigger, recheck content with
   a named authority, an estimate, an ingress endpoint and a dated activation decision.
6. **Define the degraded branch and the text boundary.** What the patient sees when the coordinator
   is unavailable or slow, and an explicit statement that no model-generated text reaches the
   patient (or the guard if it does). Add the closed-vocabulary validation of
   coordinator-proposed routes in `domain`.
7. **Add two invariants and one rule:** evidence provenance (`documented` requires a non-simulated,
   sourced artefact; a simulated receipt can never reach it), expiry stickiness (expiry is recorded
   as an event and survives clock regression), and consent handling across the in-flight window
   (stamp the consent version on the attempt and re-check at record time, or state the accepted
   window).
8. **Restate the safety claims at the level they hold** (D3 "by construction", §2 "nothing can
   launder") and state that the patient projection carries the simulated label inside the serialised
   surface, not only in page chrome.
9. **Give the expired patient screen words.** `expired_unresolved` needs an approved rendering; today
   the four-line template (`01-product.md`) states a deadline that has passed.
10. **Fix the stale mirrors and the mockup numbering** (`DESIGN_PRINCIPLES.md` §12,
    `03-planback-closure-contract.md` lines 3 and 7, `tasks/todo.md`, `00-status.md` line 78,
    mockups 01 and 04).
11. **Resolve the H2 timed hide with the user.** It is a Gate 1 rule with an accessibility hazard;
    the fix requires reopening Gate 1 deliberately or defining "until dismissed". Do not silently
    change it at Gate 3.

---

## 6. Non-blocking risks, accepted with their cost

| Risk | Cost if accepted |
|---|---|
| Shared app chrome across arms (if D6 stays as written) | The baseline's lowest-burden advantage is erased; the kill test tends to "no difference". |
| No auth on `/api`, including `/ledger` | Fine locally; becomes a public clinical-shaped data endpoint if a live link is added for the optional bonus. |
| SQLite under concurrent harness writers | Default journal mode raises "database is locked"; set WAL and a busy timeout, or serialise the harness. |
| Coordinator on the PlanBack critical path | Competition wifi plus an unmeasured model call can stall the five-minute demo; needs timeouts, a pre-warmed session and a labelled fallback. |
| "Route to a human path" with no human | Three flows end there; in a demo it is a button and a phone number. Say so in the walkthrough rather than implying a service. |
| Python environment on this machine | `AGENTS.md` records an intermittent AppControl block on stdlib venv creation, not reproduced on a later re-test. Re-probe (create a venv, install FastAPI and pytest) before Slice 1 rather than discovering it there. |
| Substrate-only platform claim | Costs AI Interaction and Technical Execution marks relative to a deeper integration; partially offset by MCP wiring, tool-failure events and session resume. |
| Judged-slice narrowness | Cutting Chinese strings and the caregiver channel weakens HCD and UX coverage against a rubric that scores both, in exchange for hitting the deadline. |
| Uncommitted AGENTS.md change (430 insertions) and untracked prompt in the working tree | Not mine to judge; flagged so the next commit does not sweep them up implicitly. |

---

## 7. Cut list (ordered)

1. D9 scheduled reassessment and multi-day persistence.
2. The in-app card arm, replaced by a real card plus a scripted post-failure question.
3. The second adapter, `notify_caregiver`, and three of the six MCP tools.
4. Chinese UI strings unless a native reviewer is secured.
5. Everything beyond one route, one adapter, one caregiver name.

Keep: PlanBack, the Closure Contract, the fault harness, the four-line patient screen, the
judge-facing ledger, the baseline comparison. Those five are the submission.

---

## 8. What this review could not verify

**Not in the repository:** no application code or tests (27 tracked files, documentation only
`[verified]`); no study protocol, questionnaire or pre-registration; no judge-ledger mockup; no
trust-boundary diagram; no usage proof or account; `gate2-review-prompt.md` referenced by the
prompt is absent; `docs/adr/` is empty.

**Requires live access:** the WorkBuddy auth scheme, region, quota and billing; whether session
create/resume survives a real process restart; whether tool-failure events arrive as described; the
managed scheduler's availability to a non-enterprise account; whether the SDK is materially better
from Node than Python (D1's stated trigger); TRTC behaviour and accuracy; real latency and cost.

**Requires a human I do not have:** whether 3-6 dyads can be recruited by early October; whether
older adults experience the false-completion failure at all; whether the read-back is accepted
without shame or a sense of being tested; whether any Mandarin native speaker will review strings;
whether a qualified clinical reviewer can be secured.

**Requires clinical authority:** the fixture content and every symptom-to-disposition path
including the 995 branch in `mockups/04`; whether the H2 retention test is acceptable practice;
whether telling a 72-year-old "help is not arranged" with a phone number as fallback is safe
without a live human route.

**Unchecked in this review:** I did not attempt a push to origin, did not open the mockups in a
browser (I read the HTML source, so I verified structure and copy, not rendering), did not run any
link check, and did not re-verify the external competitor or benchmark citations of the round 1
review.

---

## 9. What I got wrong

1. **My effort estimate is inferred, not measured.** The 90-150 h figure comes from enumerating the
   modules and endpoints in §2 and §3.1. If the WorkBuddy SDK makes sessions, streaming and resume
   near-trivial, the coordinator client is much cheaper than I assumed and my finding shrinks to the
   harness and UI work. The direction (the architecture implies more than the 56-89 h it inherits)
   is probably right; the magnitude could be off by a third.
2. **Finding 1's severity depends on a literal reading of §4.** A competent implementer will notice
   the conflict and resolve it in Gate 3, so the practical damage may be zero. I am still ranking it
   first because Gate 3 inherits this document as its specification, and the fault harness is the
   evidence base for the whole submission: an ambiguity here is inherited by every test the project
   claims.
3. **I may be under-weighting the possibility that the card arm is deliberately modest.** Reading D6
   charitably, an in-app card arm makes the comparison cheap and controllable at a stage when
   nothing else exists. That is a real defence. It does not fix the fact that the arm cannot produce
   the measured outcome.

On compensation: the prompt banned praise, and I kept the ban, which means D2's import-rule boundary
and D4's removal of the "resolved" write path are better than this review's tone implies. Both are
marked Agree in the decision table and neither needed a paragraph. I also checked whether I was
absorbing the author's framing: the three headline findings are all internal-contradiction or
measurement-validity findings that the document's own sections supply, not inherited from
`02-adversarial-review.md` or `DESIGN_PRINCIPLES.md`.

---

## 10. Confidence statement

**Verified against files (read in full):** every citation above to `02-architecture.md`,
`01-product.md`, `00-status.md`, `03-planback-closure-contract.md`, `02-adversarial-review.md`,
`research-workarounds.md`, `DESIGN_PRINCIPLES.md`, `PLAN.md`, `CHALLENGE_REQUIREMENTS_JUDGING.md`,
`ADDITIONAL_CHALLENGE_INFO.md`, `PROGRESS.md`, `tasks/todo.md`, `tasks/lessons.md`, `AGENTS.md`, the
five mockups and `mockups/index.html`. Git state verified by direct command: branch
`gate-2-architecture` at `1cb05c8`, `main` at `9a1f332`, origin holding only
`refs/heads/care-relay-adversarial-review` at `2d7ec71`, AGENTS.md modified, the thorough prompt
untracked, and the pasted prompt byte-identical to the repo copy apart from line endings.

**Inferred:** the per-fault writability table in surface C; the effort range in surface H; the
failure scenarios in Findings 1 to 3 (constructed from the document's own rules, not observed);
every statement about what Gate 3 or an implementer would do.

**Opinion:** the probability estimates in §3; the cut list; the judge's-eye and clinician readings.

**Unchecked, and labelled as such wherever the reviewer's own prompt asked about it:** everything in
§8. No claim in this review rests on running code, because no code exists.
