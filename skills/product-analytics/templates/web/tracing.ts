import { after } from "next/server";

import { redact, redactAttributes } from "./redact";

/**
 * Server half of the mobile app's tracing (mobile tracing.ts). The app
 * sends a W3C traceparent; this continues that trace so one waterfall covers
 * the tap on the phone and the work on Vercel. Posted as OTLP/JSON, which
 * PostHog's receiver accepts directly - no OpenTelemetry packages involved.
 */
const SERVICE_NAME = "app-web";

const TRACEPARENT = /^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/;

type Attributes = Record<string, string | number | boolean | undefined>;

export type ServerSpan = {
  traceId: string;
  setAttributes(attributes: Attributes): void;
  end(attributes?: Attributes & { error?: string }): void;
};

function randomHex(length: number): string {
  let out = "";
  for (let i = 0; i < length; i++) out += "0123456789abcdef"[Math.floor(Math.random() * 16)];
  return out;
}

function toOtlpAttributes(attributes: Attributes) {
  return Object.entries(attributes)
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => ({
      key,
      value:
        typeof value === "boolean"
          ? { boolValue: value }
          : typeof value === "number"
            ? Number.isInteger(value)
              ? { intValue: String(value) }
              : { doubleValue: value }
            : { stringValue: String(value) },
    }));
}

export function startServerSpan(
  request: Request,
  name: string,
  attributes: Attributes = {},
): ServerSpan {
  const token = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN;
  const host = process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com";

  const incoming = TRACEPARENT.exec(request.headers.get("traceparent") ?? "");
  // The app only samples in; an unsampled parent (flags 00) means don't record.
  const dropped = !token || (incoming !== null && incoming[3] === "00");

  const traceId = incoming?.[1] ?? randomHex(32);
  const parentSpanId = incoming?.[2];
  const spanId = randomHex(16);
  const startWallMs = Date.now();
  const startMonotonicMs = performance.now();
  const spanAttributes: Attributes = { ...attributes };

  return {
    traceId,
    setAttributes(next) {
      Object.assign(spanAttributes, next);
    },
    end(final) {
      if (dropped) return;
      const { error, ...rest } = final ?? {};
      Object.assign(spanAttributes, rest);
      const durationMs = performance.now() - startMonotonicMs;

      const payload = {
        resourceSpans: [
          {
            resource: { attributes: toOtlpAttributes({ "service.name": SERVICE_NAME }) },
            scopeSpans: [
              {
                scope: { name: SERVICE_NAME },
                spans: [
                  {
                    traceId,
                    spanId,
                    parentSpanId,
                    name,
                    kind: 2,
                    startTimeUnixNano: String(Math.round(startWallMs * 1e6)),
                    endTimeUnixNano: String(Math.round((startWallMs + durationMs) * 1e6)),
                    attributes: toOtlpAttributes(redactAttributes(spanAttributes)),
                    status: error ? { code: 2, message: redact(error) } : { code: 1 },
                  },
                ],
              },
            ],
          },
        ],
      };

      // After the response, so a slow PostHog never delays the response.
      after(async () => {
        try {
          await fetch(`${host}/i/v1/traces`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(payload),
          });
        } catch (err) {
          console.error("[tracing] span export failed:", err);
        }
      });
    },
  };
}
