# Setup runbook: the two submission artefacts that are not in the repository

Two submission items cannot be produced by writing files: the **Render backend URL**
and the **ADP Experience URL**. Both are created in a console. This is the order to do
them in, and what to record once you have them.

**Read this first. Where the URLs may be written down.** Put them in
`submission/description.md` (the links table), `docs/PLAN.md` (the submission
readiness checklist) and this file. **Do not** put them in `02-architecture.md`,
`01-product.md`, `03-program-design.md` or `04-slices.md`: those are approved gate
documents, and editing one reopens that gate (`AGENTS.md` section 5).

---

## Part A: the Render backend URL

`render.yaml` already describes the service, so this is a Blueprint deploy rather than
a manual one.

1. **Sign in to Render** and choose **New, then Blueprint**. Connect
   `github.com/jaydonnnk/carerelay`. Render reads `render.yaml` and proposes one web
   service named `carerelay`, Docker runtime, Singapore region.
   - The file asks for `plan: starter` only because it still declares a disk. Slice 7b
     moved the record to Postgres, so the disk is dead weight. If you are willing to
     delete the `disk:` block and the `plan:` line from `render.yaml` first, the
     service can run on the free tier. That is a repository edit and can be done
     before the deploy.
2. **Set the two secret values in the dashboard, not in the file.** Both are declared
   with `sync: false`, so Render expects them there:
   - `APP_DATABASE_URL`: the Supabase Postgres DSN.
   - `CARERELAY_API_TOKEN`: a fresh random token. With `APP_ENV=public` set and no
     token configured, every protected route answers **503** rather than serving an
     open endpoint, so a missing token fails closed (`src/carerelay/api.py:170`).
   - **Percent-encode the password.** The Slice 7b lesson is recorded: the password
     contains parentheses, and a URI userinfo component requires them encoded. Any
     DSN assembled from a user-supplied password goes through
     `urllib.parse.quote(pw, safe="")` (`00-status.md`, Slice 7b section).
3. **Confirm the non-secret values** Render read from the file:
   `APP_ENV=public`, `CORS_ORIGINS=https://carerelay.vercel.app`, `APP_CLOCK=scenario`.
   A wildcard in `CORS_ORIGINS` is refused by the app, so leave it as the single
   origin.
4. **Deploy.** The health check path is `/health`. Render assigns the hostname, of the
   form `https://carerelay.onrender.com`. **That string is the Render URL** and it is
   not written anywhere in the repository today.
5. **Verify, in this order.**
   ```bash
   curl -s https://<render-host>/health
   # expect {"status":"ok","version":"0.1.0"}  - /health is deliberately unguarded

   curl -s -o /dev/null -w '%{http_code}\n' https://<render-host>/api/episodes
   # expect 401 or 503, never 200

   curl -s -H 'authorization: Bearer <token>' https://<render-host>/api/episodes
   # expect 200 and the fixture label
   ```
6. **Point Vercel at it.** In the Vercel project settings, set
   `CARERELAY_API_URL` to the Render URL and `CARERELAY_API_TOKEN` to the same token,
   then redeploy. The frontend reads both server-side only; the token must never reach
   a browser bundle (`frontend/lib/api.ts:1-8`).
7. **Record it.** Update the links table in `submission/description.md` and tick the
   production-link row in `docs/PLAN.md` section 10.

**Cold start.** The Render free tier spins down when idle and the first request after
that takes seconds. Warm the service before a judge opens the link.

---

## Part B: the ADP Experience URL

The ADP agent is a submission artefact. **Publishing it does not change this
repository's code**, and it must not: ADP occupies the interpretation step only, and
the slice that would wire it in (Slice 13) is conditional and was not run
(`00-status.md:551`).

1. **Sign in to Tencent Cloud ADP** and create an agent.
2. **Constrain it, in this order, and keep the constraints in the agent's own
   configuration:**
   - Knowledge base limited to the non-clinical fixture. No clinical corpus, no
     symptom lists, no guidance documents.
   - A system instruction that refuses clinical advice and returns only structured
     interpretation: which span looks like an action, a deadline, an owner.
   - No instruction that lets it write patient-facing sentences. "No model-generated
     text reaches the patient" is an approved architectural rule
     (`02-architecture.md:302`).
3. **Publish.** ADP produces two artefacts (`adp-and-deployment-impact.md` section 1):
   - the **Experience URL**, which is shareable and is the one that goes in the
     submission;
   - the **AppKey**, which is a secret.
4. **Handle the AppKey as `AGENTS.md` section 8 requires.** Environment variable only.
   Never committed, never logged, never screenshotted. The secret scanner in this
   repository cannot catch a bare value written in prose (`tasks/todo.md:144`), so the
   operative control is that no value is written down at all.
5. **Optional: the AppKey call log.** It is a **supplement** to the usage proof, not a
   substitute. The mandatory proof is CodeBuddy or WorkBuddy usage, and that is
   already complete (`submission/usage-proof.md`).
6. **Record it.** Enter the Experience URL in the links table of
   `submission/description.md` and tick the ADP row in `docs/PLAN.md` section 10.

**If you later want the agent in the actual interpretation path**, that is not a
console task. It needs Slice 13 switched on, which reopens Gate 2
(`04-slices.md`, Slice 13 row: "CONDITIONAL, default do not run").

---

## What remains after both are done

| Item | Where it goes |
|---|---|
| Render URL | `submission/description.md` links table; `docs/PLAN.md` section 10 |
| ADP Experience URL | `submission/description.md` links table; `docs/PLAN.md` section 10 |
| Neither URL | any approved gate document |
