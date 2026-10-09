/**
 * Resolves a `?next=` value against our origin and returns it only if it stays there.
 *
 * Redirect to the returned URL itself. A prefix check lets "/\evil.com" through (browsers read
 * the backslash as a slash), and rebuilding a string from the pathname of "/.//evil.com"
 * yields the protocol-relative "//evil.com".
 */
export function safeNextUrl(raw: string | null, base: string, fallback: string): URL {
  const home = new URL(fallback, base);
  if (!raw) return home;
  try {
    const next = new URL(raw, base);
    return next.origin === home.origin ? next : home;
  } catch {
    // Unparseable, e.g. "http://[": a 500 on /login would be worse than the fallback.
    return home;
  }
}
