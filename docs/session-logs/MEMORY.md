# MEMORY (project-scoped, written deliberately)

## Conventions

- AGENTS.md is the source of truth for process and rules. Read it before
  reasoning about a slice.
- Evidence labels: `[verified]`, `[vendor claim]`, `[hypothesis]`, `[unknown]`.
- Em dashes (U+2014) are banned in new writing; the only exception is verbatim
  quoted approved content (e.g. `FIXTURE_LABEL`), which is disclosed.
- Repo line endings for Markdown are LF.
- Editing an approved gate document (`01-`, `02-`, `03-`, `04-` in
  `docs/plans/urgent-advice-accessibility/`) reopens that gate. Substantive
  text edits in submission/ and PLAN.md do not.

## Environment quirks on this development machine (macOS)

- Sandbox blocks `mkdir` on the default macOS tmp dir for tests; pass
  `--basetemp=/tmp/cr-basetemp` to pytest.
- No SVG rasterizers (`rsvg-convert`, `magick`, `inkscape`, `chromium`);
  `qlmanage` is blocked by the sandbox. The managed node workspace installs
  `@resvg/resvg-js`, which renders SVG to PNG with system fonts.
- `grep -n "^def |^def |grep -n "@app.post"` and similar can return empty in
  this shell because BSD `grep` does not honour `\b`; the ripgrep-backed
  `Grep` tool is more accurate.

## The live deployment (verified 11 Oct 2026)

- **Render API:** `https://carerelay-dzt3.onrender.com`. Free plan, so it spins
  down after 15 idle minutes and takes about a minute to answer again.
- **Vercel frontend:** `https://carerelay-self.vercel.app`.
- **`carerelay.vercel.app` is a STRANGER's project, not this one.** It resolves
  with HTTP 200 and its title is `CareRelay` plus `Hospital Staff Portal`. Never
  treat a 200 as evidence of ownership; fetch the host and read the title.
- The frontend calls the API server-side only, so `CORS_ORIGINS` has no effect on
  the app working. It is defence in depth, not a functional requirement.
- The Vercel patient page calls `createEpisode()` before `getEpisode()`, which is
  what covers the in-memory `_OPEN_EPISODES` reset after a redeploy (`api.py:312`).

## The ADP guide (`docs/ADP_Hackathon_Guide_EN.pdf`, 9 pages)

Extracted 11 Oct 2026 with `pypdf` (installed into the managed venv; no
`pdftotext`, `mutool` or `qpdf` on this machine). What it actually documents:

- **Console path to create an agent:** open **App Dev** (section 3, step 4).
- **Publish flow:** open the application, confirm answers in the **debug panel**,
  publish, then **Publish tab > Service status tab**. The **Experience URL** is at
  the top; the **AppKey** is further down in the **API management** section, shown
  only as a masked prefix with a Copy action.
- **What it does NOT document:** where the agent's instruction / prompt field
  lives, and how to configure a knowledge base. The guide covers account setup,
  publishing and the two credentials, not agent authoring internals. Do not invent
  UI steps for those; describe the field by function instead.
- Section 7 recommends: Experience URL for judges and the demo video, AppKey for
  software calls.
- FAQ: an unavailable link means the application is not published or not running;
  a lost conversation context means the `ConversationId` was not reused; the free
  allowance is time-limited and is checked under **Platform Management**.

## Render deployment facts (verified against Render docs, 11 Oct 2026)

- Omitting `plan` from a `render.yaml` web service does **not** give the free
  tier. Render defaults to `0.5c-512mb`, which is the **$7/month** tier. The free
  plan must be named explicitly as `plan: free` (0.1 CPU, 512 MB, $0/month).
  Source: `render.com/docs/blueprint-spec`, section "If you omit this field".
- Render retains the existing compute plan for an already-created service, so
  this only bites on a fresh Blueprint deploy.
- Blueprints themselves cost nothing; only the instance type does.
- Free web service limits: spins down after 15 min idle (about 1 min to spin
  back up), 750 free instance hours per workspace per month, ephemeral
  filesystem, no persistent disks, no private network traffic, outbound blocked
  on ports 25/465/587 only, `/robots.txt` answers disallow-all while spun down.
- The free plan is a legal combination with `runtime: docker` and with
  `healthCheckPath`, since `plan` only sets compute resources.

## Tested checklist of the submission asset half of Slice 12 (done 2026-10-11)

- `submission/description.md`, `submission/honest-claims.md`,
  `submission/demo-walkthrough.md`, `submission/setup-runbook.md`,
  `submission/cover-16x9.svg` + `.png`,
  `submission/architecture-trust-boundaries.svg` + `.png`.
- `submission/usage-proof.md` rewritten to completed state with reserved slots.
- Suite: **888 passed, 43 skipped, 0 failed** on macOS 11 Oct 2026 (collected
  931); Windows figure 10 Oct 2026 was 856 passed, 0 skipped.
- Out of scope for the agent: pushing to `origin` (user instructs push).
## 15 October 2026: Slice 20 publication prerequisite

[verified] F6 is separately accepted. Scoped Slice 20 publication and named
Slice 21 operator/live-fictional work are authorised; 00-status.md owns scope.
Slice 20 closure does not pass deferred accessibility/named/truthfulness proof.
Use the six-field read-back instruction, never the old seven-field schema.
Local credential rotation, active compatible version and processing/settings
facts remain live prerequisites. No secret values, desktop control, Slice 21
Git publication or CareRelay deployment are authorised by this record.
