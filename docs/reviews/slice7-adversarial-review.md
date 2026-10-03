# Slice 7 adversarial review

**Date:** 3 October 2026
**Branch:** `slice-7`, HEAD `06a25b2` (uncommitted work in the tree)
**Reviewer:** independent pass with no prior context on the tree
**Scope:** the eleven modified files and six untracked paths listed in the handover

---

## Verdict

**The slice is honest and its evidence is real.** Every claim the handover makes was
re-derived here rather than taken on trust, and each one held. One gap is worth
naming and one limitation is worth stating more loudly than the code currently
states it. Neither is a blocker, and neither is a defect in the guards themselves.

| Claim under test | Re-derived result |
|---|---|
| "548 pass" | **Confirmed.** 548 passed, 1 warning, 109.65s |
| "10/10 mutations RED" | **Confirmed.** Ran the harness. 10 of 10 RED, tree restored byte-exact, control green (262 passed) |
| Em dashes banned in new writing | **Confirmed.** 0 in every changed and new file, added lines included |
| CRLF everywhere, `test_boundaries.py` LF by design | **Confirmed.** 0 lone LF in every CRLF file; `test_boundaries.py` is 663 LF / 0 CRLF as designed |
| "Server actions keep the bearer token server-side" | **Confirmed.** `lib/api.ts` is imported only from server files; the one `"use client"` component imports `@/app/actions`, not `@/lib/api` |

---

## What is strong

**The auth guard is correct in the ways that matter.** Fail-closed on three arming
paths, `hmac.compare_digest` rather than `==`, `WWW-Authenticate` on 401 with a
detail that names what is missing rather than what would have been accepted, and a
503-not-open branch when armed with no token. The blanket
`dependencies=[Depends(require_api_token)]` on the `FastAPI(...)` constructor with a
`guarded_path` prefix test is the right shape: a route added later under `/api` is
covered without anyone remembering to annotate it, and `test_api.py` walks the real
route table to prove the blanket is still a blanket.

**The CORS decision to drop `CORSMiddleware` is correct and the reasoning is
sound.** Taking origins at construction means taking them at import, which makes the
guard untestable against a changed environment. The per-request `BaseHTTPMiddleware`
dispatcher costs one string split and buys a mutation the harness can see (M4). The
refusal to ever set `Access-Control-Allow-Credentials` is right: the credential is a
bearer header, so cookie credentials are neither needed nor wanted.

**The persistence proof proves the right thing.** Running the reopen in a fresh
interpreter subprocess through the product's own write path, then asserting the
triggers still *refuse* an UPDATE rather than merely exist, is the strong form. The
`_REOPEN` comment about `IntegrityError` being a subclass of `DatabaseError` not
`OperationalError` is exactly the kind of detail that decides whether a test can
fail for the right reason, and catching the narrow one would have made it lie.

**The honesty labels hold.** `render.yaml` states plainly that the disk is why the
paid instance is paid for, and `test_deployment.py` closes with an explicit
"[hypothesis] ... measured on the deployment, not here" boundary for R8. That is the
right shape. The `test_boundaries.py` docstring limit on the secret scanner ("does
not catch a bare 40-character string on a line that names nothing") is honest and
preferable to a scanner that claims total coverage.

---

## Finding A7-1 (advisory, not a blocker): the secret scanner does not cover `frontend/`

`test_boundaries.py::TestNoSecretIsCommitted` scans four paths (`render.yaml`,
`Dockerfile`, `.dockerignore`, `pyproject.toml`). Nothing scans `frontend/`. Slice 7
is the slice that introduced `frontend/`, and that is the one new surface in the
whole repository which has `CARERELAY_API_TOKEN` written into its environment
contract (`lib/api.ts` line 18). The file is correct today, and the reviewer checked
it by hand: the token is read from `process.env` on the server, the `Authorization`
header is attached only on the server, and the one client component does not import
the module. But the guard does not cover the file, so a future edit that pastes a
token into `frontend/lib/api.ts` or into a `NEXT_PUBLIC_*` variable would not be
caught by the scanner that exists to catch exactly that.

The narrower sub-point: `NEXT_PUBLIC_` is the specific prefix that inlines a value
into the browser bundle. Nothing in the repository currently mentions it, so the
scanner cannot catch its first appearance.

**Suggested fix, small:** add `frontend/lib/api.ts`, `frontend/app/actions.ts`,
`frontend/app/page.tsx`, `frontend/components/HintCard.tsx`, `frontend/next.config.mjs`
and `frontend/package.json` to the victim list in `TestNoSecretIsCommitted`, and add
`NEXT_PUBLIC_` to `SECRET_MARKERS` so a client-inlined variable is a finding rather
than a convention. Both are additive and need the same planted-needle self-test the
existing scanner has.

## Finding A7-2 (advisory): the scanner's stated limit is wider than the tests show

`scan_for_secrets` splits on `=` then on `:`, taking `line.split("=", 1)[-1]`. For a
YAML line like `CARERELAY_API_TOKEN: <40 chars>` there is no `=`, so the value is the
text after the first `:`, which is correct. But for a line that contains an `=` before
the `:`, the split lands in the wrong place. This is not exploitable against the four
files currently scanned (none of them has that shape), and the docstring already
disclaims completeness, so this is a note for the next scanner change rather than a
defect now. It belongs in the same pass as A7-1 so the scanner is re-tested once.

## Withdrawn: no finding on NF1's conflict branch

Considered and **withdrawn.** The conflict path is pinned on both axes:
`test_a_version_reused_with_different_content_is_refused` and
`test_a_version_reused_with_different_provenance_is_refused` both assert
`PolicyVersionConflict`. The no-op side is covered by M5 in the harness. NF1 is
closed with real coverage on both branches. Recorded here rather than deleted, so
the next reviewer does not re-raise it.

---

## What remains open, stated plainly

- **R8** stays open and is correctly labelled. The local proof is about SQLite and
  this schema; it is not a proof about Render's disk until a record is read back on
  Render after a restart *and* after a redeploy.
- **R9** stays open. The public surface becoming a clinical claim is a judged
  question and no local test can close it.
- **NF6** stays open with no logging to redact against yet. Correct.
- **The Check** is outstanding. This review is not a substitute for it.
- **No commit or push instruction has been given.** None was made.

---

## Recommendation

**Proceed to the Check.** The tree is green, the mutations bite, the deployment
artefacts are honest, and the two findings above are additive hardening rather than
corrections to what is there. Fix A7-1 in the same pass as the Check if convenient;
it is a ten-line change to one test file plus its self-test.
