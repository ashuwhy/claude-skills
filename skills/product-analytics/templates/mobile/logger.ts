import { posthog } from './posthog';
import { currentTraceContext, errorMessage } from './tracing';

type Level = 'debug' | 'info' | 'warn' | 'error';

export type LogAttributes = Record<string, string | number | boolean | null | undefined>;

const CONSOLE: Record<Level, (message?: unknown, ...rest: unknown[]) => void> = {
  debug: console.log,
  info: console.log,
  warn: console.warn,
  error: console.error,
};

function emit(level: Level, message: string, attributes?: LogAttributes) {
  // Metro output stays as it was - PostHog is an extra sink, not a replacement.
  if (__DEV__) CONSOLE[level](message, attributes ?? '');

  const trace = currentTraceContext();
  posthog?.captureLog({
    body: message,
    level,
    attributes,
    trace_id: trace?.traceId,
    span_id: trace?.spanId,
  });
}

/**
 * Structured logging for PostHog. The message is a fixed string so records
 * group; anything variable belongs in `attributes`, never interpolated into
 * the message - a body with a user's name in it is a body we have to redact.
 */
export const log = {
  debug: (message: string, attributes?: LogAttributes) => emit('debug', message, attributes),
  info: (message: string, attributes?: LogAttributes) => emit('info', message, attributes),
  warn: (message: string, attributes?: LogAttributes) => emit('warn', message, attributes),
  error: (message: string, attributes?: LogAttributes) => emit('error', message, attributes),
};

/** Spreads a caught value into attributes without dragging a stack into the body. */
export function errorAttributes(error: unknown): LogAttributes {
  return {
    error_message: errorMessage(error),
    error_name: error instanceof Error ? error.name : typeof error,
  };
}
