import { posthog, redact } from './posthog';
import { currentTraceContext, errorMessage } from './tracing';

type GlobalErrorHandler = (error: unknown, isFatal?: boolean) => void;

declare const ErrorUtils:
  | {
      getGlobalHandler(): GlobalErrorHandler;
      setGlobalHandler(handler: GlobalErrorHandler): void;
    }
  | undefined;

/**
 * Play Vitals sees none of this app's crashes - it only counts testers who turned
 * on Android's usage and diagnostics sharing, and across 19 days it returned zero
 * rows while the app was in daily use. PostHog is the only crash visibility here.
 */
export function captureException(error: unknown, attributes?: Record<string, string | number | boolean>) {
  if (!posthog) return;

  const trace = currentTraceContext();
  const thrown = error instanceof Error ? error : new Error(errorMessage(error));
  thrown.message = redact(thrown.message);

  posthog.captureException(thrown, {
    ...attributes,
    ...(trace ? { trace_id: trace.traceId, span_id: trace.spanId } : {}),
  });
}

let installed = false;

export function installErrorHandlers() {
  if (installed) return;
  installed = true;

  if (typeof ErrorUtils !== 'undefined') {
    const previous = ErrorUtils.getGlobalHandler();
    ErrorUtils.setGlobalHandler((error, isFatal) => {
      // No flush here on purpose: a fatal kills the process before an upload can
      // finish, and the SDK's queue is persisted, so it goes out on next launch.
      captureException(error, { fatal: Boolean(isFatal) });
      previous(error, isFatal);
    });
  }

  // Hermes dispatches this; older JSC builds do not, hence the feature check.
  globalThis.addEventListener?.('unhandledrejection', (event) => {
    captureException((event as PromiseRejectionEvent).reason, { unhandled_rejection: true });
  });
}
