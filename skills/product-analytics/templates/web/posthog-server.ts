import { PostHog } from "posthog-node";

import { redact, redactAttributes } from "./redact";

function getHost(): string {
  return process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com";
}

let client: PostHog | null = null;

/**
 * One client for the lifetime of the lambda instead of one per event. flushAt 1
 * keeps the serverless behaviour the old per-call `shutdown()` gave us: a function
 * that returns before the queue drains drops whatever is still in it.
 */
export function getPostHogServer(): PostHog | null {
  const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN;
  if (!posthogKey) return null;
  if (!client) {
    client = new PostHog(posthogKey, { host: getHost(), flushAt: 1, flushInterval: 0 });
  }
  return client;
}

export async function captureServerEvent(
  distinctId: string,
  event: string,
  properties?: Record<string, unknown>,
): Promise<void> {
  const posthog = getPostHogServer();
  if (!posthog) return;
  posthog.capture({ distinctId, event, properties });
  await posthog.flush();
}

export async function captureServerException(
  error: unknown,
  distinctId?: string,
  properties?: Record<string, unknown>,
): Promise<void> {
  const posthog = getPostHogServer();
  if (!posthog) return;

  // A PostgrestError is a plain object, not an Error, so normalise before
  // redacting - otherwise a failed Supabase call skips the redaction entirely
  // and ships its JWT. Same shape as captureException in the mobile errors.ts.
  const thrown =
    error instanceof Error
      ? error
      : new Error(typeof error === "string" ? error : JSON.stringify(error));
  thrown.message = redact(thrown.message);
  // The stack's first line repeats the original message.
  if (thrown.stack) thrown.stack = redact(thrown.stack);

  await posthog.captureException(thrown, distinctId, properties && redactAttributes(properties));
  await posthog.flush();
}
