import { NextResponse, type NextRequest } from "next/server";
import { createServerClient, type CookieOptions } from "@supabase/ssr";

import { safeNextUrl } from "@/lib/safeNext";
import { SUPABASE_AUTH_STORAGE_KEY, supabaseSsrCookieOptions } from "@/lib/supabase/ssrCookie";

/**
 * Sign-out target for a full-page form POST from AuthContext.signOut.
 *
 * Revoking here instead of in the browser keeps the Supabase call next door (function and
 * database in the same region) rather than a long round trip from the user's phone, and the old
 * page stays untouched under the browser's own loading bar until the redirect lands. Scope is local so
 * signing out of the website does not also sign the user out of the app.
 *
 * Cookies go on the returned redirect, as in the OAuth callback; cookies() from next/headers
 * does not reliably reach a NextResponse.redirect.
 * POST only - avoids accidental GET prefetch logging users out.
 */
export async function POST(request: NextRequest) {
  const form = await request.formData();
  const next = form.get("next");
  const destination = safeNextUrl(typeof next === "string" ? next : null, request.url, "/");

  const pendingCookies: { name: string; value: string; options: CookieOptions }[] = [];

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      ...supabaseSsrCookieOptions,
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet: { name: string; value: string; options: CookieOptions }[]) {
          pendingCookies.push(...cookiesToSet);
        },
      },
    },
  );

  const { error } = await supabase.auth.signOut({ scope: "local" });

  const response = NextResponse.redirect(destination, 303);
  pendingCookies.forEach(({ name, value, options }) => {
    response.cookies.set(name, value, options);
  });
  if (error) {
    // supabase-js keeps the session when the revoke call fails, so drop the cookies ourselves:
    // the user pressed sign out and must land signed out even if Supabase is down.
    console.error("[signout] revoke failed:", error.message);
    request.cookies
      .getAll()
      .filter(({ name }) => name.startsWith(SUPABASE_AUTH_STORAGE_KEY))
      .forEach(({ name }) => response.cookies.delete({ name, path: "/" }));
  }
  return response;
}
