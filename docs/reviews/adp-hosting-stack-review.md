# Independent review: ADP, hosting, tech stack, and the slice plan

**Kind:** adversarial review, read only at the time of writing. **Written:** 30 September 2026.
**Brief:** `docs/reviews/adp-hosting-stack-review-prompt.md`.
**Scope:** the three new facts (the ADP guide, the Vercel plus Render request, the laeria.ai
precedent) and their effect on `docs/plans/urgent-advice-accessibility/04-slices.md`.
**Ground rules at the time of the review:** no file created, edited or deleted; no commit;
no push; no gate reopened. The review was written to this file afterwards, on the user's
instruction, as documentation only.

---

## 0. Verification actually run (30 September 2026)

| Check | Result | Label |
|---|---|---|
| `git status --short` | 3 modified (`PROGRESS.md`, `00-status.md`, `src/carerelay/demo/fixture.py`), 3 untracked (`ADP_Hackathon_Guide_EN.pdf`, `adp-and-deployment-impact.md`, `docs/reviews/adp-hosting-stack-review-prompt.md`) | `[verified]` |
| `git log --oneline -8` | HEAD `82df9ee`; the Slice 3 remediation series is the tip | `[verified]` |
| `git log -1 slice-4` | `82df9ee`, identical to `main`; `slice-4` holds nothing new | `[verified]` |
| `wc -l src/carerelay/**` | 2,617 total; `state.py` 1,323; `domain/` is models 429 plus rules 610, which is 1,039, plus `__init__` 16 | `[verified]` |
| `pytest tests/ -q` (Python311) | **332 passed**, 1 warning | `[verified]` |
| `src/carerelay/templates/` | does not exist | `[verified]` |
| `jinja2` | declared `pyproject.toml:12`, imported nowhere under `src/` | `[verified]` |
| `study/`, `submission/` | do not exist | `[verified]` |
| ADP PDF | 9 pages; sections 4, 5, 6.2, 7 and 8 read in full | `[verified]` |

Two brief-level corrections before the answers. The brief says "two untracked" files and the
tree holds **three**. The brief says three files reference laeria's Vercel URL and there are
**two** (see section 8).

---

## 1. Verdict

No gate needs to reopen for the three new facts as they stand: publishing an ADP agent for
its Experience URL and AppKey, capturing AppKey call logs, and adding a static landing page
are all submission artefacts that touch no approved code, so the slice plan should **not**
change for hosting. The one thing that must change is not in the plan at all: effort should
move from the hosting question to the **mandatory organiser-usage proof**, which is absent
and blocks scoring, and second to two organiser questions that decide whether ADP is worth
anything at all. If a public deployment of the clinical API, or an ADP call path inside the
product, is actually wanted, that is a Gate 2 reopen, and this review stops at that point
rather than designing it.

---

## 2. Answers to the eight questions

### Q1. Which slices change?

**Verdict: none, on the three facts as they stand, provided ADP stays out of the call path
and hosting stays local-only.**

The three new facts map to *submission artefacts*, not slices. Publishing an ADP agent is
console work. A landing page touches no approved code. AppKey call logs are evidence
collection, already an obligation under `02-architecture.md` section 6.5. None of that
belongs in a vertical slice.

Conditional changes, if the user later decides differently:

| Slice | Would it move? | Trigger |
|---|---|---|
| Slice 4 | No | Unless `static/app.js` is dropped or the presentation target is corrected (Q4) |
| Slice 5 | No | Still blocked on the Option C source |
| Slice 6 | No | Unless ADP enters the call path (Gate 2 reopen) |
| Slices 7, 8 | No | Hosting-independent |
| Slice 9 | No | File list names `templates/patient.html`, which does not exist (Q4) |
| Slice 11 | Optionally | Add "capture the ADP AppKey call log" to the usage-proof capture. Minutes |
| Slice 12 | Optionally | Add the landing page and the ADP Experience URL as submission assets. Hours |
| Newly required | None | Auth only if a public clinical deployment is taken (Q2) |

Specific file lists that name non-existent or drifting files, from `04-slices.md`: Slice 1
`Files` and Slice 9 `Files` both name `src/carerelay/templates/patient.html`; Slice 11
`Files` names `src/carerelay/templates/ledger.html`; Slices 5 and 9 name
`src/carerelay/presentation.py`. `[verified]` against the file system.

**Gate implication:** any edit to `04-slices.md` reopens Gate 4 (`AGENTS.md` section 5:
"Editing an approved gate document reopens that gate"). So even a one-line file-list
correction is a gate change, not a tidy-up.

### Q2. Does auth need a slice?

**Verdict: no auth slice is needed for the current approved path. It is needed only if the
clinical API becomes public.**

| Scenario | Auth required? | Why |
|---|---|---|
| Local-only demo (approved) | No | `02-architecture.md` section 8 approved local-only; no public endpoint exists |
| Landing page linking to the ADP Experience URL and a video | No | Nothing clinical is public; the ADP agent is a separate surface (but see Q6) |
| Landing page linking to a **live Render build of CareRelay** | **Yes** | Section 8: "If a live link is ever added, auth is a precondition, not a follow-up" |

**Minimum viable auth for a judged demo:** one shared bearer token (or HTTP Basic) enforced
by a single FastAPI dependency applied to every `/api` route and to `/ledger`, plus CORS
locked to the Vercel origin, plus `allow_credentials=False`. laeria's `backend/api/main.py`
lines 44 to 63 show exactly this shape (bearer, not cookies, `allow_credentials=False`,
wildcard origin in dev only). `[verified]` Cost: a few hours, but it is cross-cutting, so it
must land **before** any public exposure, not after. Placement: a small slice immediately
preceding the deployment, or folded into it. Gate: Gate 2, because section 8 makes auth a
precondition.

### Q3. Does ADP need a slice, and where?

**Verdict: no slice for the stated intent. And ADP must not go before Slice 6.**

The user's stated intent is "I just want to utilize the experience url and appkey for marks."
Registering, building and publishing an ADP agent is console work, not repository work. The
Experience URL and AppKey are submission artefacts, like the cover image. They belong in
Slice 11 or 12 as evidence, at zero gate cost. `[hypothesis]`

Argue against ADP before Slice 6:

1. **ADP cannot carry the execution-substrate claim.** Tool execution, platform-originated
   failure events and session resume are all absent from the guide. `[verified]` as absence.
   `02-architecture.md` section 3.3 pins **one** normative call path, and section 6.6 states
   the P1 load-bearing answer rests on exactly those three things. Putting ADP before Slice 6
   would delay the one slice that carries the load-bearing claim and the Gate A decision, in
   exchange for a capability that is `[unknown]`.
2. **It is a Gate 2 change.** D8 pins one call path. Adding a second coordinator surface
   changes an approved decision.
3. **Reading A already fixes where extraction lives.** Gate 4 section 1.1 adopted Reading A:
   canonicalisation lives in `domain`, the coordinator returns raw spans. An ADP integration
   must return structured values and be validated in `domain`, or it breaks the section 8
   model-text boundary.

If ADP is pursued as a second interpretation surface, it is an **additive** slice **after**
Slice 6, gated by Gate 2, with the structured-output boundary written into the design before
any code.

### Q4. Does the presentation target change?

**Facts:** `templates/patient.html` does not exist; `jinja2` is declared but imported
nowhere; `api.py` renders HTML with f-strings inside the route. `[verified]`

Under each hosting option:

| Option | Presentation target should be | Effect on Slices 4 to 9 file lists |
|---|---|---|
| Local-only (approved) | What the code actually uses. Pick one: (a) adopt `jinja2` for real and create `templates/patient.html` and `templates/ledger.html`, or (b) make `presentation.py` own rendering and correct the plan's file list | (a) Slice 4 `static/app.js`, Slice 5 `presentation.py`, Slice 9 `templates/patient.html` plus `presentation.py`, Slice 11 `templates/ledger.html` all stay, and the files must be created; (b) all four change |
| Variant A (landing page) | Unchanged; the landing page is a separate static asset, for example `submission/landing/index.html` | None |
| Variant B (SPA) | A Next.js app; the patient screen leaves Python | Slices 4, 5 and 9 change materially; Gate 2 plus Gate 3 reopen |

**Recommendation:** pick (a) or (b) and correct the plan. A plan that names a file that does
not exist is a stale mirror, and `AGENTS.md` section 5 makes a stale mirror a **blocking
finding**. This requires a Gate 4 edit. Note that Slice 1 already shipped without templates,
so the drift is live, not theoretical.

### Q5. Is the schedule arithmetic survivable?

**Verdict: no. The full scope cannot ship by 16 October. Say that plainly.**

| Quantity | Value | Source |
|---|---|---|
| Remaining effort, Slices 4 to 13 | **73 to 122 h** | Computed from `04-slices.md` section 5 `[verified]` |
| Capacity, 16 days at 8 h/day | 128 h | Arithmetic |
| Capacity, 16 days at a realistic 6 h/day | 96 h | Arithmetic |
| Slice 12's own window | 17 to 18 Oct, **past the deadline** | `04-slices.md` `[verified]` |

The central estimate (about 97 h) fits only at a sustained 8 h/day with zero slack and no
lost days. The upper bound (122 h) does not fit at 8 h/day at all. On top of the slices sit
Gate A (unrun), the Option C source (unselected), recruitment (0 dyads), submission assets,
and the usage proof. `[verified]` from `00-status.md` and `04-slices.md`.

**Cut order, first to last:**

1. **Slice 8 (Gate B participant run, 15 to 25 h)** if recruitment is not secured by about
   5 October. It frees the largest single block, and the plan already pre-records the
   consequence (R3: no HCD validation claim, raw counts only). This is the honest cut.
2. **Slice 7 (external card, 5 to 9 h)** drops with Slice 8.
3. **Variant B SPA: never adopt.**
4. **Merge Slice 12 into Slice 11** and move both before 16 October, because Slice 12 is
   currently dated past the deadline.
5. **Do not cut Slices 9 or 10.** The Closure Contract and the fault harness carry the demo's
   honesty and the Technical Execution and Responsible AI dimensions.

### Q6. Does a public deployment create a clinical claim?

The audit's test: "no deployment claim without an authorised protocol and qualified
reviewer." `[verified]`, `organiser-tech-load-bearing-audit.html`, kill test D.

| Surface | Is it a deployment claim? |
|---|---|
| Landing page with the research-demonstration label, linking to a scripted demo or video, making no clinical claim | **No.** The wording decides it, not the URL |
| Landing page presenting the demo as a working triage service for older adults | **Yes** |
| The ADP Experience URL | **Higher risk than the note implies** `[hypothesis]` |

The Experience URL opens a chat with a **published, public, shareable** ADP agent. An
unconstrained agent answers whatever it is asked, including clinical questions, with no
reviewer. If that happens on an organiser-sanctioned public surface, it is a deployment claim
in substance even when the page wording is careful. The note's claim that the Experience URL
"avoids exposing the clinical API" is true of CareRelay's API, but it **relocates** the
public-surface risk rather than removing it. **Mitigation:** constrain the agent (knowledge
base limited to the non-clinical fixture, guardrails refusing clinical advice) before the URL
is shared. This is a real requirement, not a nicety.

### Q7. Does the persistent-disk requirement change the code?

**Verdict: the code change is small; the environment assumption is the real risk.**

| Concern | Finding | Label |
|---|---|---|
| Database path | `SqliteEpisodeStore.__init__(path, ...)` takes the path as a parameter (`state.py:466-480`) | `[verified]` |
| What changes | A call-site wiring change (an env var, for example `APP_DATABASE_URL` per `02-architecture.md` section 6). No change to `state.py`'s logic | `[verified]` |
| When | The API is not wired to the store yet (`api.py:29-33`), so this happens at the slice that wires the API, not as a separate change | `[verified]` |
| WAL | Enabled whenever `path != ":memory:"` (`state.py:491-494`). On a mounted volume, WAL needs `-wal` and `-shm` beside the DB and mmap support. If the volume lacks mmap or advisory locks, WAL may fail or degrade | `[hypothesis]`, needs a test on the actual disk |
| busy_timeout | Matters only with concurrent writers. One uvicorn worker keeps this low risk; multiple workers on a network volume is genuinely unsafe | `[hypothesis]` |
| Append-only guarantees | Enforced by schema triggers plus per-connection `recursive_triggers` (`state.py:490, 496-497`). **Neither depends on the path** | `[verified]` |
| `synchronous = FULL` | `state.py:495`; only as strong as the volume's durability semantics | `[unknown]` on a network disk |

Net: moving the file to a mount does **not** weaken the append-only guarantees, provided
every connection goes through this class (the O1 caveat at `state.py:484-489`). The cost is
about 1 to 2 hours plus a test on the real disk. Fallback if WAL misbehaves:
`journal_mode = DELETE`, at a throughput cost.

### Q8. Is the ADP Experience URL sufficient for the "project link" bonus?

Rubric line: "Project link | Optional | A live URL or demo link for **your project**.
Optional, but earns bonus points." `[verified]`, `CHALLENGE_REQUIREMENTS_JUDGING.md` section
8.

The rubric asks for a link to **your project**. An ADP Experience URL is a live URL to the
*agent*, hosted on ADP, not to CareRelay. `[hypothesis]` It probably counts as a "demo link"
because the ADP guide explicitly recommends it for judges, but the guide is a **vendor
document**, not the rubric, and the rubric's wording is "your project". `[unknown]` pending
organiser confirmation. **Recommendation:** if the bonus matters, the safest single artefact
is a landing page linking to both the ADP Experience URL **and** a recording or hosted build
of the actual product. Or ask the organiser, which is cheap and settles it.

---

## 3. Slice impact table

| Slice | Current scope | What changes | Why | Cost | Gate implication |
|---|---|---|---|---|---|
| 4 | PlanBack end to end, ladder, bounded repair | Nothing required. Optional: drop `static/app.js` if the ladder is server-rendered forms (Slice 1's hide control is already a no-JS form) | Presentation-target drift; no JS exists in the product today `[verified]` | 0 to 2 h | Gate 4 if edited |
| 5 | Judged fixture, abstention path | Nothing required | Still blocked on the Option C source | 0 | None |
| 6 | Action path, simulated provider, platform call, Gate A | Nothing, unless ADP enters the call path | D8 pins one call path | 0, or days | **Gate 2** if ADP is added |
| 7 | External card (C1) | Nothing required | Hosting-independent | 0 | None |
| 8 | Gate B run (kill test) | Nothing required, but it is the first cut candidate | Recruitment is unsecured | -15 to -25 h if cut | None |
| 9 | Closure Contract in full | Nothing required; file list names `templates/patient.html` (absent) | Drift | 0 | Gate 4 if edited |
| 10 | Fault harness, seven sequences | Nothing required | Hosting-independent | 0 | None |
| 11 | Judge ledger, submission surface | Optional: add ADP AppKey call-log capture to the usage-proof obligation | The mandatory proof is the scoring blocker | Minutes | None |
| 12 | Submission assets | Optional: add the landing page and the ADP Experience URL. Move it **before** 16 Oct | Its window is currently past the deadline | 4 to 8 h | None |
| New | Auth, only if a public clinical deployment is taken | One shared bearer token on `/api` and `/ledger`, CORS locked | Section 8: auth is a precondition | Hours | **Gate 2** |

---

## 4. Recommended sequence

1. **Start the mandatory usage proof now.** WorkBuddy or CodeBuddy development history plus at
   least three redacted chat screenshots, captured deliberately into a named location. It
   blocks scoring and costs nothing but discipline. `[verified]` obligation,
   `02-architecture.md` section 6.5.
2. **Ask the organiser two questions.** (a) Does an ADP-based project satisfy "built on at
   least one of the products CodeBuddy or WorkBuddy"? (b) Does an ADP Experience URL count as
   the optional "project link"? Both are cheap and both change the value of everything else.
3. **Do not change the slice plan for hosting.** Keep local-only, as approved. Do **not** take
   Variant B. The rubric does not gate on hosting, and the schedule cannot absorb it.
4. **Publish one ADP agent** and take the Experience URL and AppKey. Constrain the agent so it
   refuses clinical advice. This is a submission artefact, not a slice, and it gives the bonus
   surface and a usage-proof supplement at zero gate cost.
5. **Resolve the templates drift before Slice 4**, by choosing jinja2 or `presentation.py`, and
   correct the plan. This reopens Gate 4, so put it to the user.
6. **Re-sequence Slices 9 to 12:** merge 12 into 11 and pull both before 16 October.
7. **Treat Slices 7 and 8 (the study) as the first to drop** if no dyad is recruited by about
   5 October. The plan already pre-records the consequence.
8. **Only if a public clinical deployment is genuinely wanted:** add the small auth slice, take
   a Gate 2 decision, and mount a paid persistent disk with the SQLite path pointed at it.

**Reasoning:** the rubric does not gate on hosting, so hosting is not where the remaining
points are. The usage proof does gate on scoring, and it is absent. ADP gives the cheapest
reachable bonus without touching approved code. The schedule cannot absorb new scope, so the
plan should shrink, not grow.

---

## 5. The strongest counter-argument to this recommendation

Stated fairly, and it is strong.

The user has asked for the hosting split repeatedly, and laeria.ai proves it is a few hours of
configuration, not a rewrite. My recommendation tells him to keep a submission with **no live
product link at all**, and to lean on a vendor surface (the ADP Experience URL) that a judge
who clicks it will not recognise as CareRelay. "The rubric does not gate on hosting" is true
but incomplete: Demo and Storytelling (10 points) and Technical Execution (10 points) both
reward a product a judge can actually reach, and a link to an ADP chat is not that. A judge who
cannot open the product may reasonably mark it down on two dimensions to save a handful of
hours.

Worse, my headline recommendation may be answering a question the user has already answered. He
stated he will handle the usage proof separately. Re-raising the obligation as though he had not
heard it is exactly the failure mode where the reviewer substitutes his own priority for the
user's, and it is the failure mode this brief explicitly warns about from the other direction.
There is a real chance that the correct answer is: do the hosting split, it is cheap, it is what
the user wants, and stop moralising about the usage proof.

And on the substance: an ADP Experience URL is a `[vendor claim]` path to bonus points. A real
Render plus Vercel deployment of CareRelay is a **verified** path to them. Betting the bonus on
the vendor surface is the riskier of the two, and I should not present it as the safe default.

---

## 6. What I could not determine, and what would settle it

| Unknown | What would determine it |
|---|---|
| Whether ADP executes MCP tools, emits platform-originated failure events, or resumes sessions | The ADP Chat API documentation, or a spike (register, publish, one call) |
| Whether an ADP Experience URL satisfies the "project link" bonus | Organiser confirmation |
| Whether ADP discharges the CodeBuddy or WorkBuddy requirement | Organiser confirmation |
| Whether the ADP free allowance lasts to 16 October | The console, under Platform Management |
| Whether Gate A ran | The environment (credentials, `.env`, SDK package), or running the spike |
| Whether recruitment is secured | The user |
| Whether Render's persistent disk supports WAL (mmap and `-shm`) | A test on the actual disk |
| Whether the mandatory usage proof exists | The user |
| Whether `synchronous = FULL` semantics hold on a network-mounted volume | A durability test on the real disk |

---

## 7. Every place the section 8 questions presupposed something false

One, and it is a citation error:

- **Q5** cites "the round-2 estimate recorded in `02-architecture.md` **section 5**". The 90 to
  150 hour estimate is in **section 12** ("What this architecture still does not decide"), not
  section 5, which is "Flow". `[verified]` The estimate and the phrase "not affordable in 21
  days" are both in section 12.

Everything else in section 8 checks out: Q4's line-78 drift reference, Q6's audit quote, and
Q8's rubric quote are all accurate. `[verified]`

Not a section 8 question, but the brief's section 2 miscounts the working tree: it says "three
modified files and two untracked", and the tree holds three modified and **three** untracked.
`[verified]`

---

## 8. Errors found in `adp-and-deployment-impact.md`

It is a draft and it does contain errors, as expected. Five, in descending severity.

| # | Location | Error | Correction |
|---|---|---|---|
| 1 | Section 5.5, the laeria table and the sentence naming "`extension/config.js`, `extension/content.js` and `backend/.auth/storage_state.prod.json`" | Claims **three** files reference the live Vercel URL | **Two.** `extension/config.js` line 10 holds the Render backend URL (`https://laeria-ai-backend.onrender.com`), not the Vercel URL. Only `extension/content.js` (two refs) and `backend/.auth/storage_state.prod.json` (one ref) contain `https://laeria-ai.vercel.app`. `[verified]` The brief's section 4.3 repeats the same error |
| 2 | Sections 1 and 3 | Treats ADP tool execution as wholly `[unknown]`, quoting only the guide | `CHALLENGE_REQUIREMENTS_JUDGING.md` section 7 describes ADP as offering "model orchestration, sandboxed runtime environments, **tool-calling frameworks**, and extensible plugin ecosystems ... with guardrails, RAG, and human-in-the-loop controls". So there is a `[vendor claim]` for tool-calling in the project's **own rubric**. The correct labels: "ADP can execute tools" is `[vendor claim]`; "ADP can execute an MCP tool and emit a platform-originated failure event with an origin signal" is `[unknown]`. P2's conclusion may still hold, but its stated reason is partly wrong |
| 3 | Section 2 versus section 3 | Internal contradiction. Section 2 says "ADP **can occupy the coordinator slot**"; section 3 says "ADP is **not** a drop-in replacement for the WorkBuddy coordinator" and "the correct posture is additive" | Section 2 means the *interpretation step* inside the coordinator, not the whole coordinator including tool execution. As written, the two sections grant and deny the same slot |
| 4 | Section 4.1 | Says the Experience URL avoids the public-surface risk | It relocates it. A published ADP agent is a public, shareable surface that will answer clinical questions unless constrained (see Q6) |
| 5 | Section 4.2 | Calls an AppKey call log "directly usable as 'API call logs' under section 8" | The rubric's mandatory proof is proof of **CodeBuddy or WorkBuddy** usage. An ADP call log proves ADP usage. The note does say it "supplements, and does not replace" the mandatory history, so this is a misreading risk rather than a false statement, but the phrasing invites the misreading |

Two minor nits: section 5.3 gives `domain/` as "1,039 lines", which is `models.py` plus
`rules.py` and excludes `domain/__init__.py` (16 lines); and the laeria cache defect in section
5.5 is real, but the note's framing ("On Render that claim is false") is imprecise. The claim
is false on any container recreate (a redeploy rebuilds the image), and true for an in-place
process restart. The defect stands; the wording should name container recreation, not Render
specifically.

One thing the note gets **right** and worth preserving: the research_cache defect is a genuine,
concrete precedent for why the persistent disk is not optional. The path is inside the
container image, with no mount and no `render.yaml` anywhere in laeria. `[verified]`

---

## 9. Closing note

The single most important thing is the usage proof, and the hosting question is the one the
user keeps asking. Both are true at once. The honest position is that they are not in
competition: the usage proof is hours of discipline that blocks scoring, and the hosting split
is hours of configuration that earns an unquantified bonus. Do the first because it is
mandatory, and decide the second on its merits rather than by default. If the user wants the
split, take it, and mount the disk.
