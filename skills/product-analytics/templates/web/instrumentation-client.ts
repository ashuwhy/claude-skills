import posthog from "posthog-js";

import { redact } from "@/lib/analytics/redact";

const key = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN;
const host = process.env.NEXT_PUBLIC_POSTHOG_HOST;

if (typeof window !== "undefined" && key) {
  posthog.init(key, {
    api_host: host,
    defaults: "2026-01-30",
    capture_pageview: false,
    capture_pageleave: true,
    capture_exceptions: true,
    session_recording: {
      // maskAllInputs only covers what is typed into an <input>; rendered text
      // stays visible unless maskTextSelector is set, and a sidebar that shows
      // the user's name puts it in every recording.
      maskTextSelector: "*",
      maskAllInputs: true,
    },
    before_send: (event) => {
      if (!event) return event;
      const exceptions = event.properties?.$exception_list;
      if (Array.isArray(exceptions)) {
        for (const exception of exceptions) {
          if (typeof exception?.value === "string") exception.value = redact(exception.value);
        }
      }
      return event;
    },
  });
}
