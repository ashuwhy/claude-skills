/**
 * Twin of the SECRETS list in the mobile posthog.ts. The two apps share no
 * runtime, so this is a copy on purpose - a pattern added there belongs here too.
 *
 * Exception messages are the reason this exists on web: a failed Supabase call
 * carries a JWT, and a search error carries whatever the user typed.
 */
const SECRETS = [
  /\b(?:access_token|refresh_token|apikey|api_key|authorization)=\S+/gi,
  /\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+/g,
  /\b\d{4,}-?[A-Z]{0,3}\d{2,}\b/g,
  /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g,
];

export function redact(text: string): string {
  return SECRETS.reduce((out, pattern) => out.replace(pattern, "[redacted]"), text);
}

export function redactAttributes<T extends Record<string, unknown>>(attributes: T): T {
  return Object.fromEntries(
    Object.entries(attributes).map(([key, value]) => [key, typeof value === "string" ? redact(value) : value]),
  ) as T;
}
