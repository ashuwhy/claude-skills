import * as Application from 'expo-application';
import PostHog from 'posthog-react-native';

export const posthogToken = process.env.EXPO_PUBLIC_POSTHOG_PROJECT_TOKEN;
export const posthogHost = process.env.EXPO_PUBLIC_POSTHOG_HOST ?? 'https://us.i.posthog.com';

if (__DEV__ && !posthogToken) {
  console.error(
    'EXPO_PUBLIC_POSTHOG_PROJECT_TOKEN variable required by PostHog is missing or un-configured, ' +
      'this causes events to be silently missed. This error stops appearing once ' +
      'EXPO_PUBLIC_POSTHOG_PROJECT_TOKEN is configured',
  );
}

// Logs and traces share this name, so one service row in PostHog covers both.
export const SERVICE_NAME = 'app-mobile';

// A user's name, account number or session token must never ride along in a log
// body. The third pattern is an example ID shape (digits, letters, digits);
// replace it with whatever identifiers this app's users have.
const SECRETS = [
  /\b(?:access_token|refresh_token|apikey|api_key|authorization)=\S+/gi,
  /\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+/g,
  /\b\d{4,}-?[A-Z]{0,3}\d{2,}\b/g,
];

/** Twin of redact() in the web redact.ts - keep the lists level. */
export function redact(text: string): string {
  return SECRETS.reduce((out, pattern) => out.replace(pattern, '[redacted]'), text);
}

// Optional, like on web: a build without the token runs normally and sends nothing.
export const posthog = posthogToken
  ? new PostHog(posthogToken, {
      host: posthogHost,
      captureAppLifecycleEvents: true,
      logs: {
        serviceName: SERVICE_NAME,
        serviceVersion: Application.nativeApplicationVersion ?? undefined,
        environment: __DEV__ ? 'development' : 'production',
        beforeSend: (record) => {
          if (!__DEV__ && (record.level === 'debug' || record.level === 'trace')) return null;
          return {
            ...record,
            body: redact(record.body),
          };
        },
      },
    })
  : undefined;

// One PostHog project for web and app, and these names copied verbatim into the
// web events.ts, so a user is one person with one funnel across both. Add a name
// to both files before firing it.
export const AnalyticsEvents = {
  google_sign_in_clicked: 'google_sign_in_clicked',
  email_sign_in_clicked: 'email_sign_in_clicked',
  onboarding_completed: 'onboarding_completed',
  item_opened: 'item_opened',
  theme_changed: 'theme_changed',
  rate_app_clicked: 'rate_app_clicked',
} as const;

export type AnalyticsEventName = (typeof AnalyticsEvents)[keyof typeof AnalyticsEvents];

export function capture(event: AnalyticsEventName, properties?: Record<string, string | number | boolean | null>) {
  posthog?.capture(event, properties);
}
