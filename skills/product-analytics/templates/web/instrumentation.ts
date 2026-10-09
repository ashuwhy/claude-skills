import type { Instrumentation } from "next";

/**
 * Server-side half of error tracking. The client half is capture_exceptions in
 * instrumentation-client.ts; this catches what never reaches a browser - a route
 * handler that throws, a server component that fails to render.
 */
export const onRequestError: Instrumentation.onRequestError = async (error, request) => {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;

  const { captureServerException } = await import("@/lib/analytics/posthog-server");

  // The ph_phc_* cookie holds the browser's distinct_id, so a server error lands on
  // the same person as the pageview that caused it rather than on a new anonymous one.
  let distinctId: string | undefined;
  const header = request.headers.cookie;
  const cookie = Array.isArray(header) ? header.join("; ") : header;
  if (cookie) {
    const match = cookie.match(/ph_phc_[^=]+=([^;]+)/);
    if (match) {
      try {
        distinctId = JSON.parse(decodeURIComponent(match[1]))?.distinct_id;
      } catch {
        /* cookie shape changed; an anonymous exception still beats no exception */
      }
    }
  }

  await captureServerException(error, distinctId, { path: request.path });
};
