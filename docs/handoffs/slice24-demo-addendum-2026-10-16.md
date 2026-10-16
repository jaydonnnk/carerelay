# Slice 24 addendum: demo-first entry and a complete four-step walkthrough

Paste everything below the line into the agent that is about to start Slice 24.

---

Addendum from the user for Slice 24, the final build before the 16 October 2026 deadline.
The user said: "the emphasis is on the demo so Mei has until 6pm screen should start first -> https://carerelay-self.vercel.app/demo/stage -> more demo pages to show how the whole process works".
This adds scope on top of the hosted ADP reservation guard. It does not replace the guard, and it grants no approval by itself.

## First, before any build

1. Ask the user one question: is `ADP_EXTRACTION_ENABLED` already set on Render?
   The user wrote "ive updated the render values". If the flag is on, production sends unmetered live ADP calls right now. Ask them to remove it until your Check passes.
2. Do not treat "the agent is about to start slice 24" as approval.
   Your four open questions still need explicit answers: the limit values, the disposable Postgres DSN, the Gate 1 not-sent wording, and Gates 2/3/4.
   The user has set limit values on Render. Ask them to tell you the numbers, so the records and tests match.
3. Fold the demo scope below into your Gate 1, 2 and 4 drafts, then ask exactly: `Approve Gates 1, 2, 3 and 4 as drafted, or what should change?`

## Demo scope to add

Priority order, because time is short. Ship A and B with the guard. C only if time remains.

### A. The bare domain opens the judge page

- Today `/` is the patient journey, and `/demo` ("Mei has until 6pm.") is reachable only by typing the URL.
- Goal: opening `https://carerelay-self.vercel.app/` shows the `/demo` judge start page first, whose button leads to `/demo/stage`.
- Trap: the judge stage frames the patient route itself. `frontend/components/judge/StageFrame.tsx:31` has `<iframe src="/">`. A plain redirect of `/` to `/demo` would put the judge page inside the phone.
- Suggested design (yours to confirm in Gate 2): move the patient journey to its own path, for example `/patient`, and make `/` redirect to `/demo`. Every reference to `/` as the patient route must move with it:
  - the iframe `src` in `StageFrame.tsx`
  - the "Patient only" link in `frontend/app/demo/stage/page.tsx:57`
  - `Location: "/"` and `"/?recovery=1"` in `frontend/app/example/route.ts`
  - the retry link `href="/"` in `frontend/components/PatientJourney.tsx:411`
  - the middleware matcher `["/"]` in `frontend/middleware.ts`, which issues the locator cookie on first visit
  - the `frame-ancestors 'self'` header in `next.config.mjs`, which must still allow the stage to frame the new path
  - every test that renders or requests `/`
- The cookie path must still cover both `/demo/stage` and the patient path.
- A visitor with a stale or foreign locator cookie currently gets stuck on "We cannot load your plan", and "Try again" does not clear it; only `/example` does. Make the judge entry recover from that, for example by having "Start the demo" issue a fresh locator, so a judge never sees the stuck state.

### B. Step 4, "The booking fails", must happen on screen

- The `/demo` page promises four steps; step 4 is "The booking fails".
- Today the simulated provider's failed reply arrives only as a separate callback, `POST /api/episodes/{id}/callbacks/fictional_provider` with `{"callback_key": ..., "transition": "failed"}`. Nothing in the UI sends it, so the patient waits at "No reply yet." and the judge stage never reaches the request-failed screen.
- Goal: after "Try the simulated request", the judge can reach the failed outcome without a terminal.
- Design options for Gate 2. Pick one and justify it:
  - A judge-stage control that sends the `local-sim` failed callback through a Next.js server action. The bearer token stays on the server, and the control is labelled simulated.
  - The local simulated provider delivers its scripted `failed` reply as the callback by itself, after the attempt is recorded. That keeps the separate-callback sequence approved in Slice 17.
- Either way: origin stays `local-sim`, evidence stays `none`, the 6pm deadline and owner do not change, closure stays open, and the patient sees "The request did not work" with the plan and the nurse helpline.
- This is a new write reachable from the public site. Prove it cannot be used to send any other transition or evidence, and that a repeat is recorded as a duplicate.

### C. Explanation pages, if time remains

- The user wants "more demo pages to show how the whole process works", following the four steps on `/demo`:
  1. **Mei** reads her plan.
  2. **Tencent ADP** copies out what she said.
  3. **CareRelay code** checks it.
  4. **The simulated provider** fails, and CareRelay keeps the deadline.
- The judge stage already has a step rail ("1 Plan" to "6 Outcome") and a per-step panel. Extend that, for example with a "Next step" guide or one short explanation per step, rather than adding a separate site.
- With ADP live, the step 2 panel must say truthfully which reader ran:
  - Tencent ADP, with its request time.
  - The local stand-in.
  - "Not sent to Tencent ADP", using your not-sent wording.
- Every new string needs Gate 1 approval, drafted as exact wording.

## Keep

- The approved patient wording from today: "Simulated demo. Not medical advice." footer, "Go to the clinic for a same-day review.", "the nurse helpline".
- Judge pages may say "fictional". NTU appears only in the credit "Built for the NTU LKCMedicine challenge", never as a provider.
- The baseline is 2,200 passed, 233 skips, one existing warning. Run the frontend typecheck and production build too.
- Verify in a browser:
  - the bare domain opens `/demo`
  - the stage frames the patient view
  - a full walk-through reaches "The request did not work"
  - views at 1440px and 375px
  - with ADP live after the Check, one fictional walkthrough on production using `I will go to the clinic today before 6pm`
- Vercel's build is currently skipped by `exit 0`. Tell the user when a Vercel redeploy is needed. Render auto-deploy is off, so the user redeploys Render after the push.
- Ask for commit, merge and push authority as one question at the end.
