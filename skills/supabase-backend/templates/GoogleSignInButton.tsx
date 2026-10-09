import {
  GoogleSignin,
  isErrorWithCode,
  statusCodes,
} from '@react-native-google-signin/google-signin';
import * as Linking from 'expo-linking';
import * as WebBrowser from 'expo-web-browser';
import { AppState, Platform, Text } from 'react-native';

import GoogleIcon from '../../assets/icons/google.svg';

import { Touchable } from '@/components/ui/Touchable';
import { errorAttributes, log } from '@/lib/logger';
import { AnalyticsEvents, capture } from '@/lib/posthog';
import { supabase } from '@/lib/supabase';
import { startSpan } from '@/lib/tracing';

function parseHashParams(url: string): Record<string, string> {
  const hashIndex = url.indexOf('#');
  if (hashIndex === -1) return {};
  const hash = url.slice(hashIndex + 1);
  const params = new URLSearchParams(hash);
  const out: Record<string, string> = {};
  params.forEach((value, key) => {
    out[key] = value;
  });
  return out;
}

const GOOGLE_WEB_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID;

// Android signs in natively: the system account sheet hands back an ID token
// for the web client, which Supabase already accepts. The browser flow it
// replaces dies if the user takes over five minutes on Google's pages
// (Supabase expires the OAuth state), which adding an account to the phone
// mid sign-in does, and the Custom Tab then lands on the website.
if (Platform.OS === 'android' && GOOGLE_WEB_CLIENT_ID) {
  GoogleSignin.configure({ webClientId: GOOGLE_WEB_CLIENT_ID });
}

/**
 * True when the user is signed in or backed out of the account sheet.
 * False sends them to the browser flow instead: a Play-signed build whose
 * SHA-1 is missing from the Cloud project fails here with DEVELOPER_ERROR,
 * and a reviewer locked out of sign-in is worse than a slower one.
 */
async function signInNatively(): Promise<boolean> {
  const span = startSpan('auth.google_native', { ambient: false });
  try {
    await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
    const response = await GoogleSignin.signIn();
    if (response.type === 'cancelled') {
      span.end();
      return true;
    }
    const idToken = response.data.idToken;
    if (!idToken) throw new Error('google returned no id token');
    const { error } = await supabase.auth.signInWithIdToken({ provider: 'google', token: idToken });
    if (error) throw error;
    span.end();
    return true;
  } catch (e) {
    const code = isErrorWithCode(e) ? String(e.code) : undefined;
    span.setAttributes({ 'google.error_code': code });
    span.end({ error: e });
    if (code === statusCodes.IN_PROGRESS) return true;
    log.warn('native google sign-in failed, falling back to browser', {
      ...errorAttributes(e),
      code,
    });
    return false;
  }
}

// The account sheet leaves the app paused, and it resumes about a second after
// the sheet fails. openAuthSessionAsync on Android reads any resume as the
// user closing the browser, so a session opened before then resolves
// 'dismiss' straight away and the redirect reaches no one: every fallback in
// PostHog went this way.
function untilActive(): Promise<void> {
  if (AppState.currentState === 'active') return Promise.resolve();
  return new Promise((resolve) => {
    const sub = AppState.addEventListener('change', (state) => {
      if (state !== 'active') return;
      sub.remove();
      resolve();
    });
  });
}

export function GoogleSignInButton() {
  const onPress = async () => {
    capture(AnalyticsEvents.google_sign_in_clicked);
    if (Platform.OS === 'android' && GOOGLE_WEB_CLIENT_ID && (await signInNatively())) return;
    try {
      const redirectTo = Linking.createURL('google-callback');
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo,
          skipBrowserRedirect: true,
        },
      });
      if (error) throw error;
      if (!data.url) return;

      await untilActive();
      const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
      if (result.type !== 'success' || !result.url) return;

      try {
        const url = new URL(result.url);
        const code = url.searchParams.get('code');
        if (code) {
          const { error: ex } = await supabase.auth.exchangeCodeForSession(code);
          if (ex) throw ex;
          return;
        }
      } catch {
        // non-standard URL - try fragment flow below
      }

      const params = parseHashParams(result.url);
      const access_token = params.access_token;
      const refresh_token = params.refresh_token;
      if (access_token && refresh_token) {
        await supabase.auth.setSession({ access_token, refresh_token });
      }
    } catch (e) {
      log.error('google sign-in failed', errorAttributes(e));
    }
  };

  return (
    <Touchable
      accessibilityRole="button"
      onPress={() => void onPress()}
      haptic="medium"
      pressScale={0.96}
      className="bg-white dark:bg-neutral-800 rounded-2xl border-2 border-ui-border dark:border-neutral-600 px-6 py-4 items-center justify-center flex-row gap-3"
    >
      <GoogleIcon width={20} height={20} />
      <Text className="text-base font-sans-bold text-brand-primary">Continue with Google</Text>
    </Touchable>
  );
}
