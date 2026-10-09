// app.json is the config. This only matters with APP_VARIANT=preview, which
// builds a copy that installs beside the Play app instead of replacing it:
//
//   - its own package, so Play's install and its sign-in survive
//   - no google-services.json, which only knows the real package and fails
//     the Gradle build for any other; push is off in the copy
//   - no OTA, or the first production update for this runtime would swap the
//     code under test for whatever last shipped
//
// The scheme stays the same: Supabase only allows <scheme>://** as a redirect,
// so signing in to the copy makes Android ask which app to open, and browser
// OAuth usually lands in the Play app. For anything behind sign-in, test the
// Play-signed APK instead (play.py upload + apk).
module.exports = ({ config }) => {
  if (process.env.APP_VARIANT !== 'preview') return config;
  return {
    ...config,
    name: `${config.name} Preview`,
    updates: { ...config.updates, enabled: false },
    android: {
      ...config.android,
      package: `${config.android.package}.preview`,
      googleServicesFile: undefined,
    },
    ios: { ...config.ios, bundleIdentifier: `${config.ios.bundleIdentifier}.preview` },
  };
};
