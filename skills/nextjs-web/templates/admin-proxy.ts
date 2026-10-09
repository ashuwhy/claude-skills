import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

import { getSupabasePublicConfig } from '@/lib/env'
import { supabaseSsrCookieOptions } from '@/lib/supabase/ssrCookie'

// Lives in src/ beside app/. next build also finds this file at the
// app root, but next dev (16.2) only looks here, so a root file gated
// production while dev skipped the gate on every page and API route.
export async function proxy(request: NextRequest) {
  let supabaseUrl: string
  let anonKey: string
  try {
    const cfg = getSupabasePublicConfig()
    supabaseUrl = cfg.url
    anonKey = cfg.anonKey
  } catch {
    return new NextResponse(
      'Admin misconfigured: set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in your host (e.g. Vercel → Environment Variables) for Production and Preview, then redeploy.',
      { status: 503, headers: { 'content-type': 'text/plain; charset=utf-8' } },
    )
  }
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    supabaseUrl,
    anonKey,
    {
      ...supabaseSsrCookieOptions,
      cookies: {
        getAll: () => request.cookies.getAll(),
        setAll: (cookiesToSet: { name: string; value: string; options: CookieOptions }[]) => {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options),
          )
        },
      },
    },
  )

  // Runs on every navigation and prefetch. getClaims() verifies the JWT locally
  // against the ES256 key, where getUser() was a round trip to Supabase Auth
  // before the role lookup could even start. Same change as apps/web/src/proxy.ts.
  const { data: claimsData } = await supabase.auth.getClaims()
  const userId = claimsData?.claims.sub ?? null
  const { pathname } = request.nextUrl

  if (pathname.startsWith('/login') || pathname.startsWith('/api/auth')) {
    return supabaseResponse
  }

  // The API used to pass through here on the assumption that each route
  // checked its caller. They only checked for a session, then wrote with the
  // service-role key, and signing in with any Google account gives a session:
  // any signed-in user could write admin data. Every route below
  // /api is admin-only, so it is gated here with the pages.
  const isApi = pathname.startsWith('/api')

  if (!userId) {
    if (isApi) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    const redirectResponse = NextResponse.redirect(new URL('/login', request.url))

    supabaseResponse.headers.getSetCookie().forEach((cookieStr) => {
      redirectResponse.headers.append('Set-Cookie', cookieStr)
    })

    return redirectResponse
  }

  // Check admin role
  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', userId)
    .single()

  if (profile?.role !== 'admin') {
    if (isApi) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    const redirectResponse = NextResponse.redirect(new URL('/login', request.url))

    supabaseResponse.headers.getSetCookie().forEach((cookieStr) => {
      redirectResponse.headers.append('Set-Cookie', cookieStr)
    })

    return redirectResponse
  }

  return supabaseResponse
}

export const config = {
  // public/ files by name, so a signed-out visitor on /login gets the logo instead of a
  // redirect. Not by extension: /api/items/x.png would match a dynamic route and skip
  // the admin check, which is the only gate on the service-role API.
  matcher: ['/((?!_next/static|_next/image|favicon.ico|icon.png|brand/|google.svg|app-icon.png).*)'],
}
