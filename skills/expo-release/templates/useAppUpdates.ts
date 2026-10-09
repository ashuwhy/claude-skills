import { useEffect } from 'react';
import { AppState, Platform } from 'react-native';
import { errorAttributes, log } from '@/lib/logger';
import * as Updates from 'expo-updates';

/**
 * Two update paths, because they ship different things.
 *
 * A Play release carries native code, so only the store can install it. This
 * asks for Play's immediate flow, not flexible: expo-in-app-updates calls
 * completeUpdate() the moment a flexible download lands, which restarts the
 * app wherever the user is, mid-quiz included. Immediate asks at launch,
 * before anything is open. It only works on installs that came from Play, so
 * a sideloaded or dev build just logs the refusal.
 *
 * An EAS update is JS and assets only. expo-updates already checks on cold
 * launch; this also checks on return to the foreground, since Android keeps a
 * warm process around for days. Whatever it fetches applies on the next cold
 * start, never under the user's feet.
 */
const OTA_CHECK_INTERVAL_MS = 15 * 60 * 1000;
let lastOtaCheck = 0;

export function useAppUpdates() {
  useEffect(() => {
    if (__DEV__ || Platform.OS !== 'android') return;
    // Required here, not imported: the module looks up its native half on
    // load, and iOS never links it because the pod wants 16.4 against our
    // 16.0 target. A top-level import red-screens the iOS app at launch.
    const { checkAndStartUpdate } =
      require('expo-in-app-updates') as typeof import('expo-in-app-updates');
    checkAndStartUpdate(true).catch((err) => {
      log.warn('play in-app update check failed', errorAttributes(err));
    });
  }, []);

  useEffect(() => {
    if (!Updates.isEnabled) return;
    // 'active' also fires when the Play update sheet or a permission dialog
    // closes, so without the interval one launch could check three times.
    const subscription = AppState.addEventListener('change', (state) => {
      if (state !== 'active' || Date.now() - lastOtaCheck < OTA_CHECK_INTERVAL_MS) return;
      lastOtaCheck = Date.now();
      void fetchOtaUpdate();
    });
    return () => subscription.remove();
  }, []);
}

async function fetchOtaUpdate() {
  try {
    const { isAvailable } = await Updates.checkForUpdateAsync();
    if (isAvailable) await Updates.fetchUpdateAsync();
  } catch (err) {
    log.warn('ota update check failed', errorAttributes(err));
  }
}
