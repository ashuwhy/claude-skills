// A Vercel function is frozen between requests and can wake holding a dead
// keep-alive socket. A query sent on it gets no error, just silence until
// undici's 300s headers timeout, and the user sits on a tab skeleton the
// whole time. Reads give up at 6s and go again once on a fresh connection;
// writes only give up, since a retried POST could apply twice.
const TIMEOUT_MS = 6000;

export const timedFetch: typeof fetch = async (input, init) => {
  const method = (init?.method ?? (input instanceof Request ? input.method : "GET")).toUpperCase();
  const attempt = () => {
    const timeout = AbortSignal.timeout(TIMEOUT_MS);
    return fetch(input, {
      ...init,
      signal: init?.signal ? AbortSignal.any([init.signal, timeout]) : timeout,
    });
  };
  if (method !== "GET" && method !== "HEAD") return attempt();
  try {
    return await attempt();
  } catch (err) {
    if (init?.signal?.aborted) throw err;
    return attempt();
  }
};
