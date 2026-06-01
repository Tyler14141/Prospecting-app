import { NextRequest, NextResponse } from 'next/server'

// Lightweight auth gate. If APP_PASSWORD is set, the dashboard and its data APIs
// require HTTP Basic auth (any username, password = APP_PASSWORD). The machine
// endpoints (/api/inbound, /api/cron) are excluded — they carry their own
// secrets — so email/scheduler webhooks still work.
export function middleware(req: NextRequest) {
  const pw = process.env.APP_PASSWORD
  if (!pw) return NextResponse.next()

  const { pathname } = req.nextUrl
  if (pathname.startsWith('/api/inbound') || pathname.startsWith('/api/cron')) {
    return NextResponse.next()
  }

  const auth = req.headers.get('authorization')
  if (auth?.startsWith('Basic ')) {
    try {
      const decoded = atob(auth.slice(6))
      const pass = decoded.slice(decoded.indexOf(':') + 1)
      if (pass === pw) return NextResponse.next()
    } catch {
      /* fall through */
    }
  }

  return new NextResponse('Authentication required.', {
    status: 401,
    headers: { 'WWW-Authenticate': 'Basic realm="Agentic OS"' },
  })
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
