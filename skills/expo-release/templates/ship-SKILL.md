---
name: ship-mobile
description: Ship the <APP> mobile app - an EAS OTA update for JS-only changes, or a version-bumped Android build released to <TRACK>, tested on my phone, then promoted to production. Use when asked to release, ship, push an update, build, or submit the app.
---

<!-- Template. Copy to <repo>/.claude/skills/ship-mobile/SKILL.md, replace every
<ANGLE> placeholder, delete this comment. Check every command against the
current eas-cli and Play before relying on it. -->

# Ship the mobile app

Two lanes. Picking the wrong one is the expensive mistake: an OTA that lands on a binary missing the native code it calls crashes on launch for every user on that version.

Run everything from `<APP_DIR>`. Commits follow the repo style (`git log`) and carry no AI attribution.

## 1. Pick the lane

Find the last native release: `git log --format='%h %s' | grep -m1 'bump version'`. Diff `<APP_DIR>` since that commit.

- **Native lane** if anything changed in: `package.json` dependencies that ship native code, `app.json`, `app.config.js`, `eas.json`, `plugins/`, `patches/`, or an Expo SDK upgrade.
- **OTA lane** if every change is TS/TSX, JSON data, or images and fonts.

Done when you can name the lane and the files that decided it. When unsure, take the native lane: it is slower and always safe.

## 2. Verify

`npx tsc --noEmit` passes. If the change is visual, I check it on my <PHONE> before shipping.

## 3a. OTA lane

1. Commit and push to `main`.
2. `npx eas-cli update --channel production --environment production --message "<commit subject>" --non-interactive`

`--environment production` is load-bearing: the `EXPO_PUBLIC_*` values live in the EAS production environment, and a bundle published without them cannot reach the backend.

The update reaches only builds whose `version` in `app.json` equals the current one (`runtimeVersion` policy is `appVersion`). Phones fetch it on launch or on return to the foreground and apply it on their next cold start. Done when the command prints an update group id for the right runtime version.

There is no tester-only OTA. Beta and production builds share the `production` channel, so an update reaches every user on that runtime at once. Check it on my phone before publishing, not after.

<!-- List every runtime that must never take an OTA from main here, with the
reason, e.g. "never X.Y.Z: main imports a native module that build lacks". -->

## 3b. Native lane

Two stages: <TRACK>, where I update my phone from Play and test, then production. Stop between them.

1. Bump the patch `version` in `app.json`. Commit as `chore(mobile): bump version to X.Y.Z` and push. `versionCode` is managed remotely by EAS; leave it alone.
2. Build on the Mac, not the EAS cloud queue:
   ```
   ANDROID_HOME=$HOME/Library/Android/sdk EAS_SKIP_AUTO_FINGERPRINT=1 \
   ORG_GRADLE_PROJECT_reactNativeArchitectures=arm64-v8a,armeabi-v7a \
   npx eas-cli build --platform android --profile production --local --non-interactive --output <scratchpad>/app.aab
   ```
   Expect tens of minutes, since every local build recompiles native code for each ABI. Run it in the background and watch the log for `OutOfMemoryError`: Gradle can hang printing errors instead of exiting. `ANDROID_HOME` goes in the command because background shells skip the shell profile, and that failure still burns a versionCode.
3. Write the release note to the scratchpad: plain language for users, under 500 characters, about what they will notice. Beta and production show the same text.
4. `python3 tools/play.py release <aab> <notes>` uploads, puts it on <TRACK> and sets the note in one edit. Confirm with `play.py tracks` (the release shows `[notes]`), then send me the note. To fix it later, `play.py notes <versionCode> <file>` rewrites it on every track holding that build.
5. Stop and tell me it is in review (hours, at most about two days). I update my phone from Play and test it there.
6. When I say it passed: `python3 tools/play.py promote <versionCode>`. Same build and note on production. For a risky native change, `--rollout 20` stages it and a later `promote` with a higher number widens it.

Done when production shows the new versionCode and I have the note.

## Known blockers

- A Play install fails on a device carrying a sideloaded build (`expo run:android`, different signature). `adb uninstall <PACKAGE>` first.
- While a rejected update is still pending, every edit commits with `changesNotSentForReview=true` (play.py does this) and I press "Send for review" in the Console once.
