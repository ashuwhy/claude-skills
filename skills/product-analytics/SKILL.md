---
name: product-analytics
description: Product analytics, logs, traces and crash capture across a mobile app and its website as one PostHog project - shared event names, PII redaction, and SQL to verify wiring and measure. Use when adding analytics, logging, tracing or crash reporting, or counting testers and cold start.
---

# Product analytics

The shape is the durable part: **one project for app and web, keyed on the backend's user id, carrying events, logs, traces and exceptions, with no personal data in any of them.** The tool is PostHog *(checked 2026-10)*. SDK options, endpoints and table names change between versions; check the templates against current PostHog docs before copying, and if a better tool fits a new app, keep the shape and swap the plumbing.

Why one project: a user on both app and web is then one person with one funnel. Why own crash capture from the first tester build: store vitals only count users who opt into sharing diagnostics, so with a small audience they stay empty, and your own device data is also what a store reviewer will want as evidence.

## The four signals

- **Events**: product analytics through one `capture()` wrapper, names from one list per side, identical across app and web. Add a name to both lists before firing it.
- **Logs**: a logger whose message is a fixed string, so records group, with everything variable in an attributes object. Debug levels drop in production.
- **Traces**: OTLP spans. A span around each multi-step user action, a traced fetch on every cross-service call, and the server continues the app's `traceparent`.
- **Exceptions**: captured on both sides from every entry point, redacted.

## Wiring a new app

Templates are reference code from Oct 2026. Rename `SERVICE_NAME` per app.

Mobile ([templates/mobile/](templates/mobile/)):
- [posthog.ts](templates/mobile/posthog.ts): client, `redact()`, the event list, `capture()`. A build without the token runs and sends nothing; a dev build prints a loud error so the gap is noticed.
- [logger.ts](templates/mobile/logger.ts): `log.warn('push token save failed', errorAttributes(err))`.
- [tracing.ts](templates/mobile/tracing.ts): OTLP/JSON over fetch. `startSpan` and `tracedFetch`, restricted to an allowlist of hosts so no third party receives a `traceparent`. Path only in span attributes, never the query string. Long-lived spans pass `ambient: false` so they do not adopt unrelated children. The cold-start span has a watchdog so a hung launch still reports. Requeue on 5xx, flush on background.
- [errors.ts](templates/mobile/errors.ts): installed before the first render, with three entry points because none catches everything: the global JS error handler, an unhandled-rejection listener, and the router's error boundary for render errors React swallows.

Web ([templates/web/](templates/web/)):
- [events.ts](templates/web/events.ts): the shared names plus web-only ones.
- [instrumentation-client.ts](templates/web/instrumentation-client.ts): exception capture on, and session replay masking **text as well as inputs**. Input masking covers only what is typed; a name rendered in a sidebar lands in every recording.
- [instrumentation.ts](templates/web/instrumentation.ts): the framework's server error hook, reading the distinct id from the PostHog cookie.
- A global error boundary for render errors.
- [posthog-server.ts](templates/web/posthog-server.ts): one client per serverless instance, flushing each event; `captureServerException` for catch blocks that log and return, which the framework hook never sees. It normalises plain-object errors (Supabase's `PostgrestError` is one) before redacting, or they skip redaction.
- [tracing.ts](templates/web/tracing.ts): continues the app's `traceparent` and sends after the response.
- [redact.ts](templates/web/redact.ts): twin of the mobile `redact()`; keep the two lists level.

Done when: a test event, a log line, a span and a thrown error from each app all appear in the project, confirmed with SQL ([queries.md](queries.md)), not with the browser.

## No personal data

No name, email, phone or account identifier leaves the device, in any signal. Internal ids, coarse categories and a device tier are fine. Redaction in `beforeSend` is the backstop for mistakes, not permission to send identifiers.

- **Person properties never expire.** Events and replays age out; person records stay. `identify()` sends the user id and coarse properties only, and the app and web calls reference each other so they stay in step.
- An event needs to know that a thing happened and which kind, not who did it.
- Exception messages carry whatever the user typed and sometimes tokens. Redact every string that leaves, on both sides: log bodies and attributes, span attributes and status messages, exception messages, stacks (the first line repeats the message) and properties. Attributes are where variable data is told to go, so they leak more than messages do. Paths go without the query string.

## Verifying

Query the project; the browser lies.

- An in-app browser's network panel may record same-origin requests only, so a missing analytics row there proves nothing.
- An SDK imported as a module need not attach to `window`, so `window.posthog === undefined` proves nothing.
- Read what a project-level setting does before assuming it gates a client option. *(checked 2026-10: PostHog's `autocapture_exceptions_opt_in` is an off switch; `capture_exceptions: true` works with it unset.)*
- In the Next.js App Router, a throwaway probe route cannot start with an underscore; underscore folders are private and 404.
