# Slice 6 adversarial review (independent)

Supporting note. Authoritative for nothing; `00-status.md` remains the only
authority for gate and slice state.

**Provenance.** The review was run against the uncommitted Slice 6 tree on
3 October 2026 at `f0c8731`, under a brief that forbade writing to the repository, so the note
was first written to `%TEMP%`. The author then instructed "do what you deem fit"
on the same day. On that instruction the note was moved into `docs/reviews/`, both
should-fix findings were fixed in the tree, and `00-status.md` was corrected.
**Addendum, 3 October 2026:** a later verification pass the same day found four
record claims that did not hold (see `slice6-verification-check.md`), and the Slice 6
work was subsequently shipped on the user's explicit instruction (tip `dc95295`,
fast-forwarded into `main`). The findings above stand as written against `f0c8731`.
Sections 6 and 7 below carry the findings as first written; the resolution of each
is recorded in section 11, added after the fixes.

---

## 1. Verdict

**ISSUES FOUND. Not FAIL. The honesty claim HOLDS.**

Nothing blocks. No claim in the brief was falsified. Two should-fix items and three
notes, all in the record or in test coverage rather than in the product.

**The honesty claim, stated plainly: a caller cannot make the origin marker read
`platform`. [verified]** Nine injection attempts failed; every one returned
`local-sim` or a 422. The marker is written from the coordinator's wiring
(`service.py:385`, `868`, `936`), never from the request.

---

## 2. Baseline, re-derived

```
PYTHONPATH=src C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe \
  -m pytest -o addopts="" -q
482 passed, 1 warning in 24.69s
```

`[verified]` **482 passed, 1 warning.** The warning is the pre-existing Starlette
`httpx` deprecation, not a Slice 6 artefact.

Per-file, each run on its own, and they sum:

| file | count |
|---|---|
| test_domain.py | 100 |
| test_boundaries.py | 141 |
| test_api.py | 55 |
| test_state.py | 103 |
| test_service.py | 60 |
| test_coordinator.py | 23 |
| **sum** | **482** |

`[verified]` the split sums to the total. This is the first slice whose per-file
split I had to derive myself: `00-status.md` states the 482 total but carries **no
per-file split and no line-count row for Slice 6** (see section 6).

---

## 3. The mutations, re-derived

`[verified]` The harness `tests/_mutate_slice6.py` ran in full. **All 11 mutations
(M6 to M16) went RED on their own selector, and the control re-run printed
"64 passed" on the restored tree.** Raw tail:

```
[RUN ] M6  ... 1 failed, 8 passed
[RUN ] M7  ... 2 failed, 7 passed
[RUN ] M8  ... 1 failed, 8 passed
[RUN ] M9  ... 1 failed, 8 passed
[RUN ] M10 ... 2 failed, 19 passed
[RUN ] M11 ... 1 failed, 6 passed
[RUN ] M12 ... 1 failed, 2 passed
[RUN ] M13 ... 1 failed, 11 passed
[RUN ] M14 ... 3 failed, 5 passed
[RUN ] M15 ... 1 failed, 6 passed
[RUN ] M16 ... 1 failed, 6 passed
[CONTROL] restored tree: 64 passed, 1 warning
=== result === every mutation was seen RED; the tree is restored and green
```

**M12, M13 and one F5 mutation re-run by hand, one at a time, on a byte-anchored
edit with an md5 check before and after.**

- **M12 (`LockContention`).** Anchor `except sqlite3.OperationalError as exc:\n raise LockContention(`,
  count 1. Reverted to `raise`. `rc=1`, *1 failed, 2 passed*. **RED. RESTORED CLEAN.**
- **M13 (the O5 refusal branch).** This is where I almost filed a false finding
  against the author, and the correction matters. The anchor is a **three-line
  block**:
  ```
  if version != stamped_version:
      return (
          f"consent version changed from ..."
  ```
  Its first **line** appears **twice** in `state.py` (line 885 in
  `_require_current_consent`, line 923 in `_consent_rejection_reason`), but the
  **full block occurs once**, at line 923, which is the branch O5 needs. A truncated
  one-line probe of mine mutated line 885 and survived; that was my error, not the
  harness's. With the correct block anchor the harness's M13 goes RED on exactly
  `test_a_changed_consent_version_also_blocks`, while the unrelated `TestAttemptOpenAtomicAndDoubleTap`
  control stays green. **RED, control GREEN, RESTORED CLEAN.**
- **F5.** Two distinct mutations were measured because the row names one:
  - Revert `simulated=DEPLOYMENT_SIMULATED` to `simulated=not care_evidenced`
    (`rules.py:486`) gives **2 failed, 98 passed** in `test_domain.py`. `[verified]`
    this matches the `00-status.md` F5 row's claim of "exactly 2 RED".
  - Force `DEPLOYMENT_SIMULATED = False` (`models.py:142`) gives **4 failed, 96
    passed**. `[verified]` the flag is **not decorative**: it is load-bearing, and
    flipping it alone breaks four tests.

**Verdict on the mutation claim: TRUE.** 11 of 11 RED, each on its own selector,
tree restored.

---

## 4. The Check, re-derived live

`[verified]` Driven through `TestClient` against the real app and a real
`EpisodeService`, in the order `POST /api/episodes` -> `/intake` -> `/consents` ->
`/actions` -> `/callbacks/{route_id}`. **I did not start uvicorn**; the brief's
running notes describe a live server and the skill forbids starting one. The
`TestClient` path exercises the same ASGI app, so the wire shapes below are the
real ones, but I state plainly that this is not a uvicorn run.

**(a) A callback stating `origin: "platform"` -> HTTP 422:**

```json
{
  "detail": {
    "detail": "origin 'platform' is not one this deployment can produce; the wired path reports 'local-sim'. No tool is executed through a platform in this build, so recording a platform origin would state a fact no observation supports.",
    "requested_origin": "platform",
    "wired_origin": "local-sim"
  }
}
```

**(b) The default-origin callback -> HTTP 200:**

```json
{
  "episode_id": "demo-episode-001",
  "route_id": "fictional_provider",
  "attempt_id": "05222e093b574a3a8f5da2db9e5fe674",
  "origin": "local-sim",
  "receipt": "applied",
  "applied": true,
  "rejection_reason": null,
  "execution": "acknowledged",
  "simulated": true,
  "fixture_label": "SIMULATED - RESEARCH DEMONSTRATION. Not clinical advice."
}
```

**(a) and (b) are distinguishable by inspection.** One is a 422 naming both origins,
the other a 200 reading `local-sim`. There is **no 200 whose body reads `platform`**,
because no platform executed. `[verified]` this matches the brief's Claim 1 exactly.

**Boundaries, probed:**

| probe | result |
|---|---|
| unknown episode | 404 |
| route with no attempt | 409 |
| unknown enum transition | 422 |
| `origin: "PLATFORM"` (uppercase) | 422 |
| `origin: "platform "` (trailing space) | 422 |
| `origin: "platf<cyrillic er>rm"` (lookalike) | 422 |
| `origin: null` | 422 |

**Nine attempts to make the marker lie, all defeated:**

| attack | outcome |
|---|---|
| top-level `origin: "platform"` | 422 |
| `origin` inside `payload` | 200, body reads `local-sim` |
| `origin` inside `evidence` | 200, body reads `local-sim` |
| `Origin: platform` HTTP header | 200, body reads `local-sim` |
| `X-Origin: platform` HTTP header | 200, body reads `local-sim` |
| duplicate key `Origin: platform` | 200, body reads `local-sim` |
| `simulated: false` in the request | 200, body reads `simulated: true` |
| camelCase / lookalike / spaced variants | 422 |

`[verified]` `simulated` is **not a field of `CallbackRequest`** at all: the OpenAPI
schema lists only `callback_key`, `transition`, `evidence`, `payload`, `origin`. The
response `simulated` is hard-wired `True`.

**Code read, as the brief asked (`service.py`):**

- `service.py:385` `self._origin: Origin = getattr(coordinator, "origin", Origin.LOCAL_SIM)`.
  The wired origin is read **from the coordinator**, with the honest default for a
  struct stub that omits it. It is never read from a request.
- `service.py:899-907` `stated = Origin(origin); if stated is not self._origin: raise OriginNotWired(...)`.
  A caller-stated origin is **compared, never trusted**. `Origin` is a `StrEnum`, so
  `Origin("platform")` maps only to the exact string; `PLATFORM`, `platform ` and a
  Cyrillic-homoglyph spelling all raise `ValueError` before the comparison.
- `service.py:868` and `service.py:936` the two response fields are `tool.origin` and
  `stated` (already proven equal to `self._origin`). Both sites are on the reader side
  of OriginNotWired.

**Verdict on Claim 4: TRUE. A caller cannot make the origin marker read `platform`.**

---

## 5. Judgement calls

| call | verdict | document relied on |
|---|---|---|
| The platform half is a **refusal (422)**, not a 200 rendering `platform` | **Agree.** D8 forbids ADP carrying the section 3.3 claim and no platform executed, so a 200 reading `platform` would assert an execution that did not happen | `02-architecture.md` D8, section 3.3; `04-slices.md:186` |
| The Check is met by a **JSON body**, not a human-facing ledger page | **Agree, with a note.** The marker is on the response and not buried in `payload`, which is what "displayable by inspection" needs. The note is that no ledger route exists yet, and the live-check note discloses this (N2) | `04-slices.md:188`; `docs/reviews/slice6-live-check.md` N2 |
| The `style.css` 404 is a **Slice 1 surface**, not a Slice 6 defect | **Disagree with the record's silence, not with the scoping.** It is fairly a Slice 1 surface, but it is a live defect on the shipped patient page and **no document tracks it** | see F-1 |
| `DEPLOYMENT_SIMULATED = True` and `origin = local-sim` everywhere is the **pre-recorded fallback**, taken honestly | **Agree.** The fallback is `04-slices.md:186`; Gate A proved transport, not execution, and the code says so in three docstrings | `04-slices.md:185-186`; `docs/reviews/slice6-live-check.md` |
| `OriginNotWired` is the honesty mechanism and not a comment | **Agree, proven.** The signal comes from the coordinator's wiring; a request field cannot set it | `service.py:385, 899-907`; attack table above |

---

## 6. Findings

### Blocking

None.

### Should fix

**F-1. No document records the `style.css` 404, and the CSS test cannot see it.**
`[verified]`

- `src/carerelay/api.py:259` renders `<link rel="stylesheet" href="/static/style.css">`.
- Nothing mounts `/static` (`grep -n StaticFiles src/carerelay/api.py` returns nothing).
- `GET /static/style.css` -> **404** (`/` -> 200, len 840; `/static/style.css` -> 404, len 22).
- `tests/test_api.py:161-165` `test_stylesheet_has_no_animation_or_auto_hide` reads
  the file **from disk** (`Path(...).read_text()`), so it passes while the browser
  gets a 404. The test is not wrong about the CSS; it simply cannot observe the
  route.
- `grep -rn "style.css\|StaticFiles\|static mount" 00-status.md 04-slices.md` finds
  only the Slice 1 **file list**, never an open item. `tasks/todo.md` and `PROGRESS.md`
  do not carry it either.

Why it matters: it is a real, reproducible defect on a page a judge will load, and
the record is silent about it. Smallest fix: add a `StaticFiles` mount at
`/static`, or (better for the slice boundary) record it as an open item anchored to
the slice that owns the patient page, and add a route-level test asserting the CSS
is served. Do not fix it inside Slice 6.

**F-2. The O5 `refused` receipt is not exercised at the HTTP boundary.**
`[verified]`

`tests/test_api.py:720-721` `TestCallbackRoute` documents "applied, duplicate and
refused are different", but only `applied` (line 732) and `duplicate` (line 747) are
posted. No test revokes consent via `POST /consents` and then posts a callback.

Proof by mutation: with the O5 refusal branch disabled (the M13 block), the entire
`test_api.py` stays **green**:

```
test_api.py under M13: rc=0 | 55 passed, 1 warning
```

Why it matters: the state and service layers do cover all three states (M13 goes RED
there), so the product is correct; but the API route that a judge drives has no
fail-capable test for its third state, and its own docstring claims otherwise.
Smallest fix: one test in `TestCallbackRoute` that consents, opens an action,
revokes consent via `POST /consents {granted: false}`, posts a callback, and asserts
`receipt == "refused"`, `applied is False`, `rejection_reason` non-null.

### Note

**N-1. `tools/_fix_status_slice6.py` and `tools/_fix_todo_slice6.py` are one-shot
editing scripts left in the tree.** They are untracked so they will not be committed
by accident, but they are not slice deliverables and they sit next to a real tool
directory. Note only: delete them before the ship, or move them out.

**N-2. `docs/reviews/slice6-live-check.md` carries 8 U+2014, all quoted, none
disclosed.** All 8 are inside pasted raw HTTP output: the `fixture_label` string is
"SIMULATED - RESEARCH DEMONSTRATION..." from the fixture, which is approved copy. This
is imported/evidence text, not new writing, so it is not a violation of `AGENTS.md`
section 6. But the project's convention is to **disclose** the count on imported
dashes, and this note does not. Note only.

**N-3. `00-status.md`'s Slice 6 section has no line-count row and no per-file test
split,** unlike the Slice 3 and Slice 4 sections, which both carry them. The 482
total is stated (`00-status.md:289`) and is true, but the arithmetic that would let a
reader check it is absent. Note only.

---

## 7. Test-quality findings

- **Not trivial.** `test_coordinator.py` pairs every refusal with a control
  (`test_a_permitted_route_with_a_current_key_dispatches`, line 225;
  `test_record_evidence_accepts_a_simulated_self_report`, line 268). The
  `TestTheExtractionBoundarySaysWhatItHides` class is honest in an unusual way: it
  first **pins that the flattering claim is false** (line 348) before pinning the
  real one. That is the NF5 correction done properly.
- **No signature-introspection or reachability tests.** `test_a_coordinator_without_a_tool_surface_cannot_be_built`
  (line 331) asserts a real construction failure, not a signature shape.
- **`test_the_boundary_carries_no_pairing_and_no_disposition` (line 368)** asserts the
  field-name set of `AllowedPlanValues` is exactly three names. This is close to a
  structural assertion, but it is load-bearing for ADR-0007 (a fourth pairing field
  would break it) and it is paired with a behavioural control, so it stands.
- **The `refused` gap is F-2.** That is the one place a class docstring claims more
  coverage than the test has.
- **M13's anchor is safe but fragile-looking.** The full block occurs once, so the
  harness is correct; but the first line occurs twice, and a future refactor that
  reorders the two `if version != stamped_version:` sites would silently retarget the
  mutation. A comment in the harness or a longer anchor would make it robust. Note
  only; this is what nearly produced a false finding from me today.

---

## 8. False claims in `00-status.md`

**None found.** Every claim I could check held:

| claim (00-status.md) | verdict |
|---|---|
| line 289: "482 pass, 11 mutations RED" | **True.** 482 confirmed; 11 of 11 RED confirmed |
| line 376: F5 "revert ... returns exactly 2 RED" | **True.** Measured 2 failed, 98 passed |
| line 500: O2 "M12 reverts to `raise` and goes RED" | **True.** M12 RED, control green |
| line 524: O5 "M13 reverts the refusal branch and goes RED" | **True**, once the correct block anchor is used |
| line 608: NF5 "Pinned by three tests" | **True.** `TestTheExtractionBoundarySaysWhatItHides` has three tests |
| line 289: "Live curl proven" | **Not re-derived as a curl run.** I drove `TestClient`, not uvicorn |

The one gap is structural, not false: the Slice 6 section carries no per-file split
and no line-count row (N-3).

---

## 9. What I could NOT verify, and why

- **A uvicorn run.** The skill forbids starting a server and the brief's own running
  notes confirm the `TestClient`/`uvicorn` distinction. My Check is over the real
  ASGI app via `TestClient`; the status codes are the real ones but this is not
  literally a `curl` against a bound socket. `[unknown as a curl run]`
- **Whether the author's M6 to M16 each used a unique anchor.** I verified M12, M13
  and F5 by hand. I did not re-derive M6 to M11, M14 to M16 individually; I read the
  harness and confirmed each anchor's **full block** is unique where I spot-checked
  (M13), and the harness run seen RED is consistent with unique anchors. `[verified
  for M12, M13, F5; inferred for the rest]`
- **`docs/reviews/slice6-live-check.md`'s own curl transcript.** I did not re-run its
  live server; I checked that its claims are consistent with my `TestClient` results,
  and they are.
- **Anything requiring ADP, credentials or a network call.** Not attempted.
- **The two `tools/_fix_*.py` scripts' effect on `00-status.md`.** They are the
  author's one-shot editors; I read them and confirmed the anchors they target exist,
  but I did not run them (they write to the tree).

---

## 10. Answer to the closing question

**Does the honesty claim hold? Yes. [verified]** A caller cannot make the origin
marker read `platform`. The wired origin is read from the coordinator, the
caller-stated origin is compared and refused, the enum refuses every non-exact
spelling, and nine injection attempts across the body, the headers and the payload
all failed. The 200 body reads `local-sim`; the platform half is an honest 422 that
names both origins.

**Is the record true? Yes, with one structural gap (N-3) and one untracked defect
(F-1).** No false claim found in `00-status.md`.

**Was anything built that Slice 6 did not ask for?** No scope creep found. Two
one-shot editing scripts are left in `tools/` (N-1).

**Was anything the contract asked for left out or weakened?** The deliverable list
in `04-slices.md:182` is fully present: `POST /actions`, `POST /callbacks/{route_id}`,
`tools.py` with exactly three tools each rechecking authorisation, consent and the
attempt key, `simulated_provider.py` with `simulated: true` on every response. The
one weakness is the API-level test coverage of the third receipt state (F-2), which
is a test gap, not a missing feature.

---

## 11. Resolution, 3 October 2026 (after the fixes)

Applied on the author's instruction "do what you deem fit". Two code files and one
test file changed; no gate document touched, so no gate reopened.

**F-1, fixed.** `src/carerelay/api.py` now mounts the static directory next to the
`FastAPI` app:

```
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
    name="static",
)
```

`GET /static/style.css` now answers 200 (1944 bytes) where it answered 404.
`tests/test_api.py::TestNoTimerOrAutoAdvance::test_the_page_links_a_stylesheet_the_app_actually_serves`
pins it: it asserts the page links the path and that the path returns a non-empty
200.

**F-2, fixed.** `tests/test_api.py::TestCallbackRoute::test_a_success_arriving_after_revocation_is_refused_and_says_why`
revokes consent over `POST /consents` and then posts a callback, asserting
`receipt == "refused"`, `applied is False`, a non-null `rejection_reason` and an
`execution` that is not `acknowledged`.

**Both fixes mutation-checked, one at a time, byte-anchored, md5-restored.**

| revert | result | tree |
|---|---|---|
| Remove the `app.mount(...)` block | **RED**, `rc=1` | RESTORED CLEAN |
| Neutralise the revocation refusal in `_consent_rejection_reason` | **RED**, `assert 'applied' == 'refused'` | RESTORED CLEAN |

**A correction to this note worth keeping.** My first attempt to mutation-check F-2
mutated the wrong site twice. `_consent_rejection_reason` and
`_require_current_consent` both open with the same `if version != stamped_version:`
line, and the `if state != "granted":` refusal appears in both, once as a `raise`
and once as a `return`. The unique anchor for the O5 branch is the **`return`
form** at `state.py:923`, not the `raise` form at `state.py:885`. This is the same
trap the M13 near-miss describes in section 7, met twice in one day. A future
harness should anchor on the `return` form.

**Suite after the fixes: 484 passed, 1 warning** (482 baseline, +2 for the two new
tests). Per-file: 100 domain, 141 boundaries, **57** api (was 55), 103 state, 60
service, 23 coordinator. Sum 484.

**Line endings and em dashes re-verified** on every touched file: `loneLF = 0` on
`api.py`, `state.py` and `test_api.py`; the three U+2014 in `api.py` are the
pre-existing Slice 1 pair plus its Slice 4 companion, none added here.
