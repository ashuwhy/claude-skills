// Every event both apps fire uses the same name as in the mobile posthog.ts:
// one PostHog project for web and app, so a name that differs splits one
// funnel into two. Add a name to both files before firing it.
export const AnalyticsEvents = {
  pageview_manual: "$pageview",
  page_not_found: "page_not_found",
  google_sign_in_clicked: "google_sign_in_clicked",
  email_sign_in_clicked: "email_sign_in_clicked",
  onboarding_completed: "onboarding_completed",
  item_opened: "item_opened",

  // Mobile only, listed so the two files stay identical.
  theme_changed: "theme_changed",
  rate_app_clicked: "rate_app_clicked",
} as const;

export type AnalyticsEventName = (typeof AnalyticsEvents)[keyof typeof AnalyticsEvents];
