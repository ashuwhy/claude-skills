---
name: supabase-backend
description: Supabase patterns - RLS write holes, SECURITY DEFINER functions, admin surfaces, pg_cron upkeep, auth hooks over triggers, native Google sign-in, OAuth debugging, storage caching. Use when writing a migration or policy, setting up auth, or debugging sign-in or a database outage.
---

# Supabase backend

Each rule below is a default with the failure that produced it. Supabase ships changes often (auth, logs API, client options); check the reason against current docs before applying a rule, and update this file when Supabase has fixed the underlying problem. *(checked 2026-10)* marks the volatile ones.

Schema, policies and catalogue content live in migrations in the repo, applied with the CLI. Content changes are database work, never an app release.

## Policies: ask what a write proves

An RLS insert policy that checks only `auth.uid() = user_id` proves who owns the row and nothing else. On a table that grants access or records money, anyone holding the public anon key can write themselves a row without opening the app.

- Writes that grant access or record money never go through a client policy. Drop those insert and update policies and route the write through a function.
- [templates/free_enrollment.sql](templates/free_enrollment.sql) is the pattern: `SECURITY DEFINER`, `set search_path`, checks `auth.uid()`, checks the target is active, inserts at amount 0, `ON CONFLICT DO NOTHING` returning the existing row so it can never overwrite a real payment, `revoke` from `public` and `anon`, `grant` to `authenticated`.
- Verify after push: anon gets `42501` from the function, and no non-service role keeps an insert policy on the table.
- Paid writes come from the server with the service role, after verifying the payment provider's signature.

Done when: for every table, I can say which roles can write and what each write proves.

## Admin surfaces

A session proves only that someone signed in; with open Google sign-in, anyone has one. An admin app writing with the service role must check the user's role on every API route, in the gate, with tests: 401 signed out, 403 wrong role. See `nextjs-web`.

## pg_cron fills the disk

pg_cron logs every run to `cron.job_run_details` and never prunes it. A per-minute job writes 1440 rows a day. On a small instance that table can become most of the database, and its write IO can drain the disk IO budget until Postgres refuses connections.

[templates/pg_cron_upkeep.sql](templates/pg_cron_upkeep.sql): a daily purge keeping a few days, scheduled alongside the first cron job, not after an outage. Pause a job with `cron.alter_job(..., active := false)` rather than unscheduling it, so its definition survives.

## Auth

- **Restrict sign-up with a before-user-created auth hook, not a trigger on `auth.users`.** The auth server inserts users in more than one statement (unconfirmed, then confirmed), so a trigger meant to refuse public sign-ups also refuses users an admin creates.
- **Deleted accounts keep a valid JWT until it expires.** Call `getUser()` on launch, in parallel with the first fetch, and sign out locally on `user_not_found` or `session_not_found`.
- **Store review account**: an email and password user made with the admin API, confirmed, onboarding done. Keep email sign-in working in every release for it.

### Google sign-in

Native on Android ([templates/GoogleSignInButton.tsx](templates/GoogleSignInButton.tsx)): the platform Google sign-in library returns an id token, then `signInWithIdToken`. Any native error other than cancel or in-progress falls back to the browser flow. Check the library's current API before copying; the template is from Oct 2026.

- Native sign-in fails after the account is picked (`DEVELOPER_ERROR`) unless an Android OAuth client exists for the package and **each** signing SHA-1: the store's app-signing key and the upload key, plus a temporary one for any debug key. Read the store key from the store-installed APK with `apksigner verify --print-certs`.
- `webClientId` is the web client Supabase already accepts.
- OAuth clients are created in the Google Cloud Console *(checked 2026-10: gcloud cannot create them)*.
- The OAuth consent screen must be "In production", or only listed test users can sign in and refresh tokens expire within days.

Browser flow (iOS, and the fallback):
- The app needs a real route for the callback path, and `<scheme>://**` in Supabase's redirect allowlist. Without the route, the router shows its not-found screen after a successful sign-in.
- After a failed native attempt, open the browser only once the app is active again. The account picker backgrounds the app, and the auth session can read the resume as the user closing the browser.
- Supabase expires a browser OAuth attempt after a few minutes *(checked 2026-10: about five)*, then redirects to the site URL, not the app. A user adding an account on Google's pages can take that long; native sign-in has no such clock.
- Sign out of the native Google client too, so a shared phone can switch accounts.

### Debugging OAuth

- `auth.flow_state` rows mark browser OAuth starts; a null `auth_code_issued_at` means Supabase never finished that attempt. No new rows during a sign-in means the native id-token path ran.
- Query it through the Management API database query endpoint with the CLI token.
- Auth logs come from the Management API's analytics endpoint. It has changed shape before *(checked 2026-10: `.../analytics/endpoints/logs` taking SQL over a `logs` table, with ISO start and end bounds; the older `logs.all` returns 410)*. Retry on a transient "Backend error".

## Content honesty

A catalogue item with nothing in it is `is_active = false`. An active empty item lets a user enrol into nothing, and store reviewers open it. Drafts stay inactive until they have content; flipping one needs no build.

## Storage

Objects that never change get versioned paths and a year-long `cacheControl`. Never upsert over a cached path when the plan cannot purge the CDN (see `mobile-performance`, Images).
