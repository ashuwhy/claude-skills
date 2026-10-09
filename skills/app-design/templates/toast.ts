import * as Burnt from 'burnt';
import { Platform, ToastAndroid } from 'react-native';

// Native toasts, not an in-app banner: ToastAndroid on Android, and on iOS
// (which has no toast API) burnt's system HUD. Haptics stay with the caller
// via lib/haptics, so burnt's own haptic is off to avoid a double buzz.
function show(preset: 'done' | 'error' | 'none', title: string, message?: string) {
  if (Platform.OS === 'android') {
    ToastAndroid.show(message ? `${title}. ${message}` : title, ToastAndroid.SHORT);
    return;
  }
  Burnt.toast({ title, message, preset, haptic: 'none' });
}

export const toast = {
  success: (title: string, message?: string) => show('done', title, message),
  error: (title: string, message?: string) => show('error', title, message),
  info: (title: string, message?: string) => show('none', title, message),
};
