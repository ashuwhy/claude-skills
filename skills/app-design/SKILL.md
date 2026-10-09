---
name: app-design
description: Making a React Native app feel finished - motion, press feedback, haptics, spacing symmetry, dark mode, tab bars, splash handover, components and copy. Use when designing or polishing a screen, adding animation or feedback, or fixing something that looks off.
---

# App design

These are taste defaults with their reasons. Platform conventions move (new system materials, new haptic APIs, new edge-to-edge rules); when the platform now offers a native way to do something below, prefer it and fix this file. *(checked 2026-10)* marks the platform-bound ones.

Three files go into a new app on day one: [templates/motion.ts](templates/motion.ts) (shared springs, press scale, reduced motion), [templates/haptics.ts](templates/haptics.ts), [templates/toast.ts](templates/toast.ts). They are reference code from Oct 2026; check their imports against current Reanimated and Expo docs before copying.

## Motion answers a touch

**Movement responds to a finger, never to content arriving.** Content is there when the screen opens. Entrance fades, slides and staggers make a user wait for something already loaded, and on budget phones they read as slowness.

- Animate under a finger, or where motion carries meaning colour cannot (a wrong-answer shake doubles as the colour-blind cue).
- Nothing overshoots. Near-critically damped springs; overshoot reads as a toy.
- Press scale around 0.98 for cards and buttons, and a short press delay (~70ms) so a scroll that starts on a card does not depress it.
- Respect the system reduce-motion setting once, in the shared configs, not per call.
- The one arrival animation allowed is the splash handover, because it stands in for the native splash.

## Haptics

- Fire on press, not press-in. Press-in fires at the start of every scroll.
- For a pager or tab switch, tick when the index commits, so a half swipe that springs back stays silent.
- Prefer the platform's own feedback constants where they exist; Android's follow the user's touch-feedback setting.

## Symmetry, measured to the ink

Equal spacing matters more than any other polish. A section label has the same gap above its ink as below it, measured on a screenshot, not read off class names.

- Class names lie: the styling library's rem and the font's line box both add space the code does not show. Screenshot at device scale, scan pixel rows for ink, compare gaps in points, report the numbers.
- One gutter constant and one top-gap constant, exported from the screen wrapper and used everywhere. Screens drift apart the moment each sets its own.
- Cards in a rail stretch to the tallest, with the bottom row pinned.
- When a spacing request is ambiguous, find which gap the screenshot is about before changing anything.

## Dark mode

- Surfaces come in pairs: page and card are different values. A card given the page colour vanishes.
- Set the native window background per scheme as well as the React tree, or the system bars and overscroll show the wrong colour.
- Apply a stored theme choice before the splash lifts, so the first frame is never in the wrong scheme.
- Test switching back to "System" after a trip to another app. *(checked 2026-10: React Native kept a stale scheme after an override was cleared, because a phone already in that scheme announces no change. Push the current scheme to listeners yourself.)*
- Dark brand colours (navy, deep green) disappear on a dark ground; swap in a light variant.

## Tab bar

- Height from the item (padding, icon, gap, label) plus the bottom inset, never a fixed constant. With Android edge-to-edge the bar spans the navigation strip, and a fixed height puts labels behind the nav buttons.
- Solid on Android, system blur material on iOS (see `mobile-performance`).
- Check inactive label contrast at its real size; light greys fail at small sizes.
- Swipe between tabs only where no tab scrolls sideways. A horizontal rail fights the pager on quick flicks however the gesture is arbitrated.
- A long-press hint on icon-only tabs, counted in analytics: it tells you which icons people cannot read.

## Splash handover

Draw the JS overlay identical to the native splash, then hand over with no fade.

- The native splash sizes the image inside a square, so a non-square logo renders smaller than the configured width. Size the overlay from the rendered glyph, measured, not from the config number.
- Hold the overlay until the first screen has its data (with a cap), so the splash is not traded for a screen of skeletons.
- Exit in order: the mark leaves, then the ground lifts. Fading both together leaves a ghost of the mark over the app.

## Components

- One button component with primary, secondary and disabled states, and every hand-rolled button replaced by it. Disabled is grey, never white on the brand colour.
- Native toasts (`ToastAndroid`, the iOS system HUD) over a JS banner, which looks foreign on both platforms.
- Media at its real aspect ratio everywhere and skeletons the same size, so nothing jumps when it loads. Badges on artwork get a thin light ring so they do not read as part of the image.
- A translucent inner stroke over an image card, not a solid border round it.
- No emoji in product UI. An icon set carries meaning, and every icon-only control gets an accessibility label.

## Copy

Say only what the app does today. An empty category is hidden, not "coming soon". A number on screen needs a source I could show a reviewer.
