import * as Device from 'expo-device';

/**
 * How much work this handset can be asked to do.
 *
 * Performance complaints come from budget and older devices, not flagships.
 * Guessing per model does not scale - most users are on hardware the
 * developer will never hold - so the app measures instead. Tune the
 * thresholds below from the RAM and API spread in the app's analytics.
 *
 * These are process constants. expo-device reads them from the platform once,
 * so there is nothing to memoise and no hook to write.
 */
const GB = 1024 ** 3;

const memory = Device.totalMemory;
const api = Device.platformApiLevel;

export type DeviceTier = 'unsupported' | 'low' | 'full';

/**
 * Anything unknown counts as capable.
 *
 * totalMemory is null on some OEM builds and on web. Blocking a user because
 * a vendor did not report their RAM would be a far worse bug than any jank we
 * are trying to avoid, so every check below only ever fires on a value we
 * actually read.
 */
function classify(): DeviceTier {
  // Below this the device cannot hold the JS bundle, the image cache and a
  // video decoder at the same time. minSdk is 24, so anything that can install
  // at all is Android 7+; RAM is the real floor, not the API level.
  if (memory !== null && memory < 1.5 * GB) return 'unsupported';

  // Autoplay has to earn its place rather than be assumed. It is decoration:
  // a muted clip on a card the user has not tapped. The cost of getting this
  // wrong is the whole app feeling broken, which is what testers reported, so
  // the bar is set high and everything below it simply does without.
  if (memory !== null && memory >= 6 * GB && api !== null && api >= 31) return 'full';

  return 'low';
}

export const deviceTier = classify();

/** Muted video on a card nobody tapped. First thing to go. */
export const canAutoplayVideo = deviceTier === 'full';

/**
 * HomeSkeleton mounts 14 Skeletons, and each one used to own an infinite
 * withRepeat loop - 14 concurrent UI-thread animations during the exact
 * moment the app is still loading its first screen.
 */
export const canAnimatePlaceholders = deviceTier === 'full';

/**
 * Explore glides every surviving card to its new place when a filter
 * changes. That is a layout pass plus one animation per card on the UI
 * thread at the moment of the tap, so low tier phones just snap.
 */
export const canAnimateLayout = deviceTier === 'full';
