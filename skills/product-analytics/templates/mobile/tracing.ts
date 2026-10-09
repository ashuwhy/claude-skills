import { AppState } from 'react-native';

import { SERVICE_NAME, posthog, posthogHost, posthogToken } from './posthog';

/**
 * PostHog's OTLP receiver accepts OTLP/JSON over a plain POST, so the exporter
 * is a fetch call rather than the @opentelemetry stack: no protobuf, ~200KB of
 * bundle we don't ship, and nothing that breaks on an Expo SDK bump. There is
 * no React Native page in PostHog's tracing docs, so this follows the OTLP
 * spec directly: https://opentelemetry.io/docs/specs/otlp/
 */
const ENDPOINT = `${posthogHost}/i/v1/traces`;

const FLUSH_INTERVAL_MS = 10_000;
/** Beta traffic is 12 testers, so every trace is kept. Turn this down before a wider rollout. */
const SAMPLE_RATE = 1;
const MAX_BATCH = 50;
/** Spans held while offline. Oldest go first - a stale span is worth less than a fresh one. */
const MAX_BUFFER = 200;

type SpanKind = 'internal' | 'client';

const KIND_CODE: Record<SpanKind, number> = { internal: 1, client: 3 };

export type SpanAttributes = Record<string, string | number | boolean | null | undefined>;

type OtlpValue = { stringValue: string } | { intValue: string } | { doubleValue: number } | { boolValue: boolean };

type OtlpSpan = {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  name: string;
  kind: number;
  startTimeUnixNano: string;
  endTimeUnixNano: string;
  attributes: { key: string; value: OtlpValue }[];
  status: { code: number; message?: string };
};

export type Span = {
  traceId: string;
  spanId: string;
  sampled: boolean;
  /** W3C traceparent header value, for whoever handles the other end of the call. */
  traceparent: string;
  setAttributes(attributes: SpanAttributes): void;
  end(outcome?: { error?: unknown }): void;
};

const HEX = '0123456789abcdef';

function randomHex(length: number): string {
  let out = '';
  for (let i = 0; i < length; i++) out += HEX[Math.floor(Math.random() * 16)];
  return out;
}

function toOtlpValue(value: string | number | boolean): OtlpValue {
  if (typeof value === 'boolean') return { boolValue: value };
  if (typeof value === 'number') {
    return Number.isInteger(value) ? { intValue: String(value) } : { doubleValue: value };
  }
  return { stringValue: value };
}

function toOtlpAttributes(attributes: SpanAttributes): OtlpSpan['attributes'] {
  return Object.entries(attributes)
    .filter(([, value]) => value !== undefined && value !== null)
    .map(([key, value]) => ({ key, value: toOtlpValue(value as string | number | boolean) }));
}

let buffer: OtlpSpan[] = [];
let flushTimer: ReturnType<typeof setInterval> | undefined;

/**
 * React Native has no async context propagation, so "the current span" is the
 * most recently started one that has not ended. Good enough to parent a fetch
 * to the screen that triggered it; wrong if two spans overlap, which is why
 * anything that matters passes an explicit parent.
 */
const open: Span[] = [];

export function currentSpan(): Span | undefined {
  return open[open.length - 1];
}

export function currentTraceContext(): { traceId: string; spanId: string } | undefined {
  const span = currentSpan();
  return span?.sampled ? { traceId: span.traceId, spanId: span.spanId } : undefined;
}

const noopSpan: Span = {
  traceId: '',
  spanId: '',
  sampled: false,
  traceparent: '',
  setAttributes: () => {},
  end: () => {},
};

export function startSpan(
  name: string,
  options: {
    kind?: SpanKind;
    attributes?: SpanAttributes;
    parent?: Span;
    /**
     * Whether later spans parent to this one. Off for anything long-lived (a
     * video load runs for seconds), which would otherwise adopt every unrelated
     * request that happens while it is open.
     */
    ambient?: boolean;
  } = {},
): Span {
  if (!posthogToken) return noopSpan;

  const parent = options.parent ?? currentSpan();
  const sampled = parent ? parent.sampled : Math.random() < SAMPLE_RATE;
  if (!sampled) return noopSpan;

  const traceId = parent?.traceId ?? randomHex(32);
  const spanId = randomHex(16);
  const attributes: SpanAttributes = { ...options.attributes };
  // Ties the trace to the person and to the replay of the session it happened in.
  const distinctId = posthog?.getDistinctId();
  if (distinctId) attributes['distinct_id'] = distinctId;

  const startWallMs = Date.now();
  const startMonotonicMs = performance.now();
  let ended = false;

  const span: Span = {
    traceId,
    spanId,
    sampled,
    traceparent: `00-${traceId}-${spanId}-01`,
    setAttributes(next) {
      Object.assign(attributes, next);
    },
    end(outcome) {
      if (ended) return;
      ended = true;
      const index = open.indexOf(span);
      if (index >= 0) open.splice(index, 1);

      // Wall clock for the start, monotonic for the length: a clock correction
      // mid-span would otherwise produce a negative duration.
      const durationMs = performance.now() - startMonotonicMs;
      if (outcome?.error) {
        attributes['error.message'] = errorMessage(outcome.error);
      }

      buffer.push({
        traceId,
        spanId,
        parentSpanId: parent?.spanId,
        name,
        kind: KIND_CODE[options.kind ?? 'internal'],
        startTimeUnixNano: String(Math.round(startWallMs * 1e6)),
        endTimeUnixNano: String(Math.round((startWallMs + durationMs) * 1e6)),
        attributes: toOtlpAttributes(attributes),
        status: outcome?.error ? { code: 2, message: errorMessage(outcome.error) } : { code: 1 },
      });

      if (buffer.length > MAX_BUFFER) buffer = buffer.slice(-MAX_BUFFER);
      if (buffer.length >= MAX_BATCH) void flushSpans();
      else scheduleFlush();
    },
  };

  if (options.ambient !== false) open.push(span);
  return span;
}

/**
 * Launch to first usable screen. Started at module load, which is after the JS
 * bundle is parsed - it measures the JS half of the launch, not the native one.
 * Every request made during startup lands in this trace.
 */
const appStart = startSpan('app.cold_start');

// A launch that never resolves (no session, no network) would otherwise keep
// adopting spans for the life of the process.
const appStartWatchdog = setTimeout(() => {
  appStart.setAttributes({ timed_out: true });
  appStart.end();
}, 20_000);

export function endAppStart(attributes?: SpanAttributes) {
  clearTimeout(appStartWatchdog);
  appStart.setAttributes({ ...attributes });
  appStart.end();
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return typeof error === 'string' ? error : JSON.stringify(error);
}

function requeue(batch: OtlpSpan[]) {
  buffer.unshift(...batch);
  if (buffer.length > MAX_BUFFER) buffer = buffer.slice(-MAX_BUFFER);
  // The interval was cleared when the buffer drained, so without this a failed
  // send waits for the next span or for the app to background.
  scheduleFlush();
}

function scheduleFlush() {
  if (flushTimer) return;
  flushTimer = setInterval(() => {
    void flushSpans();
  }, FLUSH_INTERVAL_MS);
}

export async function flushSpans(): Promise<void> {
  if (!posthogToken || buffer.length === 0) return;

  const batch = buffer.splice(0, MAX_BATCH);
  if (buffer.length === 0 && flushTimer) {
    clearInterval(flushTimer);
    flushTimer = undefined;
  }

  const payload = {
    resourceSpans: [
      {
        resource: { attributes: toOtlpAttributes({ 'service.name': SERVICE_NAME }) },
        scopeSpans: [{ scope: { name: SERVICE_NAME }, spans: batch }],
      },
    ],
  };

  try {
    const response = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${posthogToken}` },
      body: JSON.stringify(payload),
    });
    // 4xx means PostHog rejected the shape; retrying that forever just burns battery.
    if (!response.ok && response.status >= 500) requeue(batch);
  } catch {
    requeue(batch);
  }
}

// Android kills the process from the background without warning, so this is the
// last chance to ship what is buffered.
AppState.addEventListener('change', (state) => {
  if (state !== 'active') void flushSpans();
});

const TRACEABLE_HOSTS = [process.env.EXPO_PUBLIC_SUPABASE_URL, process.env.EXPO_PUBLIC_WEB_URL].filter(
  Boolean,
) as string[];

/**
 * Drop-in fetch that times the call and hands the server a traceparent. Used as
 * the supabase-js global fetch, which covers PostgREST, Storage and
 * functions.invoke in one place.
 */
export async function tracedFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
  const method = (init?.method ?? 'GET').toUpperCase();

  // Only our own services get the header: sending a trace id to a video or
  // payment provider leaks nothing useful and can trip their CORS preflight.
  if (!TRACEABLE_HOSTS.some((host) => url.startsWith(host))) return fetch(input, init);

  const { origin, pathname } = splitUrl(url);
  const span = startSpan(`${method} ${pathname}`, {
    kind: 'client',
    // Never ambient. Supabase fires these in parallel, and a request that
    // adopted the one started just before it would draw a waterfall showing a
    // dependency that is not there.
    ambient: false,
    // The query string carries PostgREST filters, which can hold a user's
    // name on a search - path only.
    attributes: { 'http.request.method': method, 'server.address': origin, 'url.path': pathname },
  });

  const headers = new Headers(init?.headers);
  if (span.traceparent) headers.set('traceparent', span.traceparent);

  try {
    const response = await fetch(input, { ...init, headers });
    span.setAttributes({ 'http.response.status_code': response.status });
    span.end(response.ok ? undefined : { error: `HTTP ${response.status}` });
    return response;
  } catch (error) {
    span.end({ error });
    throw error;
  }
}

function splitUrl(url: string): { origin: string; pathname: string } {
  const match = /^(https?:\/\/[^/]+)(\/[^?#]*)?/.exec(url);
  return { origin: match?.[1] ?? url, pathname: match?.[2] ?? '/' };
}
