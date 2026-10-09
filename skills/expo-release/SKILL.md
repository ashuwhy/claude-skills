---
name: expo-release
description: Releasing an Expo app to Google Play - OTA versus store build, runtime versioning, testing a store build, track promotion with play.py, first-build setup. Use when shipping or building an Expo app, or setting up its release tooling.
---

# Releasing an Expo app

Every rule here is a default with its reason. Before applying one, check the reason still holds for the current Expo, EAS and Play; if something better exists now, use it and fix this file. *(checked 2026-10)* marks the facts most likely to have aged.

If the repo has its own ship skill (`.claude/skills/ship-*`), follow that: it knows the app's track, package and banned runtimes. To give a new app one, copy [templates/ship-SKILL.md](templates/ship-SKILL.md) to `<repo>/.claude/skills/ship-mobile/SKILL.md` and fill the placeholders.

Tooling: `~/claude-skills/tools/play.py` drives the Play Developer API (setup in its docstring). Copy it into the repo so the ship skill has a stable path.

## Two lanes

**OTA** for JS, JSON and assets. **Store build** for anything native: native dependencies, app config, config plugins, patches, an SDK upgrade. When unsure, store build. It is slower and always safe; a wrong OTA crashes at launch for everyone on that runtime.

- Tie the runtime version to the app version (or a fingerprint), so an OTA only reaches binaries with matching native code.
- Once main imports a native module an older runtime lacks, main can never be published to that runtime. Record each such runtime in the repo's ship skill the day it happens.
- Decide channels on day one. If closed-track and production builds share a channel, every OTA reaches every user at once and there is no tester-only lane. A separate channel for test builds buys one.
- Build the update with the same environment as the store build (EAS: `--environment production`), or the bundle ships without its backend config.

## Store build

1. Bump the version. Let EAS own the versionCode (`appVersionSource: remote` + `autoIncrement`).
2. Build. `eas build --local` skips the cloud queue. Give Gradle enough memory for R8 (`-Xmx6g -XX:MaxMetaspaceSize=2g` in `~/.gradle/gradle.properties` was enough) and watch the log for `OutOfMemoryError`, because Gradle can hang instead of exiting. Set `ANDROID_HOME` inline in the command: background shells skip the shell profile, and a build that fails early may already have used up a versionCode.
3. Write the release note: plain language, what a user will notice. I set it with play.py, never by pasting into the Console.
4. `play.py release <aab> <notes>`: upload, closed track and note in one edit.
5. After review, install from Play on my own phone and test there.
6. `play.py promote <versionCode>` sends the same build and note to production. `--rollout N` stages a risky one; promoting again with a bigger N widens it.

Done when `play.py tracks` shows the versionCode on production.

## Testing a store build before any track

Install the Play-signed APK, not a locally signed release. Anything keyed to the signing certificate (native Google sign-in, Play Integrity) only works with Play's key.

1. `play.py upload <aab>`: into the bundle library, no track.
2. `play.py apk <versionCode> out.apk`: Play's universal APK.
3. `adb install -r -i com.android.vending out.apk`. Without the installer flag, Play Protect blocks it as "get this app from Play".
4. Later, `play.py release <versionCode> <notes>` reuses the same upload.

The `APP_VARIANT=preview` config ([templates/app.config.js](templates/app.config.js)) installs a copy beside the store app. Good for screens before sign-in; it shares the URL scheme, so OAuth redirects land in the store app.

## First store build of a new app

- [templates/eas.json](templates/eas.json): remote versions, development / preview / production channels, submit track named explicitly, since EAS submit defaults to internal testing, which does not count toward production access *(checked 2026-10)*.
- R8 and resource shrinking on, with keep rules (see `mobile-performance`).
- [templates/useAppUpdates.ts](templates/useAppUpdates.ts): Play in-app update prompt plus an OTA check on foreground. Works only on installs from Play.
- [templates/postinstall.js](templates/postinstall.js): patch-package that tolerates partial workspace installs and never fails a web deploy.
- Orientation: read Play's current large-screen policy first. *(checked 2026-10: Android 16 ignores manifest orientation locks on large screens and Play flags them, so lock to portrait at runtime, and only when the shortest side is under 600dp.)*

## Traps

- A phone holding a sideloaded build (different signature) cannot take the Play install. Uninstall it first.
- While a rejected update is pending, edits must commit with `changesNotSentForReview=true` (play.py retries with it), then one "send for review" in the Console.
- The store listing icon is its own asset; a build never changes it (`play.py icon`). Store art replaces as a set (`play.py art`).
- Play vitals stays empty for a small audience, since it only counts users who share diagnostics. Ship crash reporting of your own (see `product-analytics`).
- When a new Xcode or iOS runtime breaks launch, try the previous simulator runtime before debugging the app. *(checked 2026-10: Expo apps crashed at launch on the iOS 27 runtime and ran on iOS 26.)*
