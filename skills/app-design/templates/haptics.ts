/**
 * HAPTICS
 * Thin, safe wrapper around expo-haptics.
 *
 * Rules this file enforces so callers don't have to think about them:
 *  - Never throws. Haptics are a nicety; a device without a motor, or a
 *    user who disabled system haptics, must not crash a button press.
 *  - No-ops on web, where the API doesn't exist.
 *  - Fire-and-forget. Callers never await - the vibration must not sit
 *    between the tap and the navigation.
 */

import { Platform } from 'react-native';
import * as Haptics from 'expo-haptics';

const enabled = Platform.OS === 'ios' || Platform.OS === 'android';

function fire(run: () => Promise<void>) {
  if (!enabled) return;
  // Swallow: an unsupported motor or a revoked permission is not an error
  // worth surfacing to the user mid-tap.
  void run().catch(() => {});
}

/** Card taps, list rows. The default. */
export function tapLight() {
  fire(() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light));
}

/** Primary buttons - enroll, submit, continue. Slightly weightier. */
export function tapMedium() {
  fire(() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium));
}

/**
 * A hold that opened something, like a tab's name bubble. On Android this is
 * the system's own long-press effect, the one WhatsApp's tabs play, so it
 * matches the phone rather than our other taps.
 */
export function longPress() {
  fire(() =>
    Platform.OS === 'android'
      ? Haptics.performAndroidHapticsAsync(Haptics.AndroidHaptics.Long_Press)
      : Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium),
  );
}

/**
 * Landing on another tab, by tap or by swipe. The lightest thing the phone can
 * play: Android's segment tick is the system's own effect for stepping through
 * a set of choices and follows the user's touch-feedback setting. It arrived in
 * Android 11; context click plays the same tick on older phones.
 */
export function tick() {
  fire(() =>
    Platform.OS === 'android'
      ? Haptics.performAndroidHapticsAsync(
          Number(Platform.Version) >= 30
            ? Haptics.AndroidHaptics.Segment_Tick
            : Haptics.AndroidHaptics.Context_Click,
        )
      : Haptics.selectionAsync(),
  );
}

/** Selecting an option, changing a filter. Crisp tick. */
export function select() {
  fire(() => Haptics.selectionAsync());
}

/** A right answer, a purchase complete, a task done. */
export function success() {
  fire(() => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success));
}

/** Wrong answer - paired with the shake. */
export function warning() {
  fire(() => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning));
}

/** Payment failure, network error. */
export function error() {
  fire(() => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error));
}

export const haptics = {
  tapLight,
  tapMedium,
  longPress,
  tick,
  select,
  success,
  warning,
  error,
};
