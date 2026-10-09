---
name: mobile-performance
description: Performance for React Native and Expo apps on budget Android phones - device tiers, cold start, tab and list rendering, images, app size with R8, Android rendering quirks. Use when an app lags, starts slowly or ships large, or before building a heavy screen.
---

# Mobile performance

Every rule here is a default with its reason. React Native, Expo and Android change fast; before applying a rule, check its reason against the current version, and if the platform has since fixed the problem, drop the workaround and fix this file. *(checked 2026-10)* marks the likeliest to have aged.

Two habits outlast every specific fix:

- **Test on the cheapest phone a real user has**, running the Play build. Budget Android (2-4GB RAM, an Android version or three behind) is where users feel slowness; a flagship hides it.
- **Measure p90, split by device tier, before and after.** A fine p50 next to a bad p90 is the normal shape of "the app is slow" reports.

## Device tier

[templates/deviceTier.ts](templates/deviceTier.ts) sorts the phone once at startup into `unsupported`, `low` and `full` by RAM and API level, and exports `canAutoplayVideo`, `canAnimatePlaceholders`, `canAnimateLayout`. The thresholds in it are a starting guess; tune them from the RAM and OS spread in the app's own analytics.

Gate every expensive visual on the tier: autoplaying video, looping skeletons, layout animations. Attach the tier to analytics events so every metric splits by it.

## Cold start

A slow launch is usually a waterfall, not one slow call. Trace it first (a cold-start span with a watchdog timeout, see `product-analytics`), then look for:

- **Blocking on a token refresh.** Open a returning user from the stored session and a cached profile, render at once, refresh behind.
- **The same fetch fired from several places.** Count requests in the trace. Refetch the profile only on a real sign-in or user change, not on every auth event.
- **Serial calls that could run together.** Validate the user in parallel with the first data fetch. Sign out locally when the server says the user or session no longer exists; otherwise a deleted account keeps a working session until the token expires.
- **Offline treated as signed out.** A network error reading the session is not a sign-out. Keep the cached session.

Done when: the span shows p90 by tier, before and after, with a week of data after release.

## Tabs and lists

- **Pre-mount tabs inside a transition.** A first tab visit that mounts inside the tap's own commit is several times slower than visiting a mounted tab. Mount home first, then the rest in `startTransition` once home has data, so a tap interrupts the work instead of queueing behind it.
- **React Compiler** removes most manual memo work. Turn it on, run its lint, and read what it skips: ref reads in render and animation-value writes are typical. *(checked 2026-10: Babel-only, so enabling it ships as an OTA.)*
- **Stable props.** A memoised component handed a fresh array or object every render never skips. Hoist constant data, type props `readonly`.
- **Uncontrolled text inputs** for search. A controlled input re-renders every keystroke, and on iOS it can repeat letters.
- **One clock for every skeleton.** Each looping animation is its own UI-thread loop, and a skeleton screen can start dozens during launch, the busiest moment. Drive them all from one shared value; leave them still on the low tier.
- **No autoplay video in a feed on the low tier.** A WebView player mounting while the list lays out costs more than anything else on screen.
- **Horizontal rails show a peek of the next card**, or nobody discovers they scroll.

## Images

- A disk-and-memory caching image component (`expo-image`, `cachePolicy="memory-disk"` *(checked 2026-10)*).
- Content that never changes gets a versioned path and `cache-control: max-age=31536000, immutable`. To change it, upload under a new name and repoint the row; never overwrite a path, because a CDN you cannot purge keeps serving the old file.
- Check cache headers with GET, not HEAD. Some storage CDNs answer HEAD with different headers than GET.
- Put the storage region near the users. An edge miss to a far region costs seconds per image on a mobile network.

## App size

Turn on code and resource shrinking for release (Expo: `expo-build-properties` with `enableMinifyInReleaseBuilds` and `enableShrinkResourcesInReleaseBuilds` *(checked 2026-10)*) and add keep rules from [templates/proguard-rules.pro](templates/proguard-rules.pro) for the libraries the app uses.

- If R8 fails, look for dead native dependencies first. One unused library compiled against removed APIs blocks the whole build.
- A missing keep rule crashes on the phone and never at build time. Test the Play build through every flow touching a WebView, payments or a reflective native module.

## Android rendering

- **Safe areas from a hook, not a native padding view**, wherever the first frame matters. A natively padded view can apply its padding a frame late, so the screen draws under the status bar and then jumps. *(checked 2026-10: `SafeAreaView` from react-native-safe-area-context did this on Android; `useSafeAreaInsets()` did not.)*
- **No live blur behind scrolling content on Android.** Android blur views snapshot and blur a bitmap, so they tear and lag mid-scroll. Use a solid bar there and the system material on iOS. Same on the mobile web: a backdrop blur repaints on every scroll.
- **Round a WebView's container, never clip the WebView.** A clipped WebView gets its own hardware layer and the parent's clip cannot anti-alias against it, leaving grey corners.
- **Re-test WebView-based components on a real device after every React Native upgrade.** They are the first to break under architecture changes.
