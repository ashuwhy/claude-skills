---
name: nextjs-web
description: Next.js sites and admin panels on Vercel with Supabase - the auth gate, static rendering with an anon client, local JWT checks, safe ?next= redirects, sign-out, fetch timeouts, loading boundaries, fonts, latency for far-away users. Use when building, securing or speeding up a Next.js app.
---

# Next.js on Vercel with Supabase

Every rule here is a default with its reason. Next.js renames and moves things between majors; check each against the current docs, and when the framework now handles something itself, drop the workaround and fix this file. *(checked 2026-10)* marks the volatile ones.

## The auth gate

**Put the gate file where the current Next docs say, then prove it runs under both `next dev` and `next build` with a signed-out test.** A gate that silently does not run fails open: the page serves real data and nothing errors.

*(checked 2026-10: Next 16 renamed `middleware` to `proxy`; the file is `proxy.ts` exporting `proxy`, beside `app/`, so `src/proxy.ts` when the app lives in `src/app`. A file at the repo root ran under `next build` but not `next dev`, so production was gated and local dev was not.)*

[templates/admin-proxy.ts](templates/admin-proxy.ts) is a working gate:
- Pages: signed out goes to the login page.
- API routes: 401 signed out, 403 wrong role, the OAuth callback left open. Every route that writes with the service role sits behind it, because a session alone proves nothing when anyone can sign in with Google.
- Open paths match whole segments (`/login` or `/login/...`), never a bare `startsWith('/login')`, which also opens any later route whose name begins that way.
- The role it checks has to be one the user cannot write. A `profiles.role` under an "update own profile" policy is self-service admin; `supabase-backend` has the fix.
- Verify the JWT locally (`getClaims()` against the project's signing keys) rather than a round trip to the auth server on every navigation and prefetch. Keep the round trip (`getUser()`) for writes.
- The matcher excludes public files **by name**. Matching everything sends a signed-out request for the login page's own logo to the login page.

Tests: signed out 401, each wrong role 403, the right role through, public paths open, and a look-alike path such as `/login-x` gated. Write them so they fail against a gate that does not run.

Done when: the gate tests pass and a signed-out `curl` against `next dev` gets the redirect.

## Rendering

- **Public pages use an anon Supabase client that never reads cookies.** Reading cookies opts the route out of static rendering, so a public page re-runs its queries on every view.
- **Give supabase-js a fetch timeout.** It sets none, and a serverless function can wake holding a dead keep-alive socket, so a query waits minutes for the HTTP client's own timeout. [templates/timedFetch.ts](templates/timedFetch.ts): a few seconds, one retry for GET and HEAD only so writes never apply twice. When the retry fails too, show a retry screen in place rather than the global error page.
- **A `loading.tsx` per route that has child pages.** Next shows the nearest boundary above the segment that changes, so without one a click shows nothing until the server answers. Build the skeleton from the page's own components so text wraps the same, and animate opacity only.
- **Prefetch whole tabs in persistent navigation** (`prefetch={true}`). Dynamic pages otherwise prefetch only up to their loading boundary, so each switch waits a round trip. Every write then calls `router.refresh()` or `revalidatePath` so a cached tab is never stale.

## Security

- **`?next=` redirects** through [templates/safeNext.ts](templates/safeNext.ts): resolve once against the origin, keep it only if the origin matches, redirect to that URL object. Prefix checks fail: browsers read `/\evil.com` as another host, and rebuilding from a pathname re-opens `//evil.com` after normalisation.
- **Sign out** is a form POST to [templates/signout-route.ts](templates/signout-route.ts): revoke with local scope on the server, clear cookies on the 303, delete them by hand if the revoke fails. Global scope also signs the user out of the mobile app.
- **Every entry point gets the same auth, validation and limits**: API routes, server actions, route handlers and the gate, checked together.

## Front end

- **Self-host fonts** (see `brand-identity`). A build-time font download is a network dependency that can fail a deploy.
- **Text inputs at 16px on phones.** iOS Safari zooms into any focused field below 16px and never zooms back.
- **Video embeds load on intent**: build the player on pointer enter or focus, never on mount, and never for touch pointers.
- **No backdrop blur on a fixed bar**; it repaints under every scroll on budget phones.
- **A custom 404 that fires a `page_not_found` event with the path**, so broken shared links show up as a list.

## Latency for far-away users

Measure from where the users are, with curl from that region or a real phone, and keep the numbers in the app's repo as the baseline every web performance change is compared against.

- Place functions in the same region as the database, then judge distance to users from measurements.
- At low traffic most first visits hit a cold function; measure the first request after idle, not only warm TTFB.
- When a gap is unexplained, take a DevTools Performance trace of a real first load before forming a theory.
