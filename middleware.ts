import { NextRequest, NextResponse } from 'next/server'

// Best-effort in-memory rate limit (per edge isolate). For a real multi-instance
// deployment, back this with a durable store (e.g. Upstash). Caps API abuse so a
// runaway client/script can't flood the agents or spend.
const WINDOW_MS = 60_000
const MAX_PER_WINDOW = 200
const hits = new Map<string, { count: number; reset: number }>()

function rateLimited(ip: string): boolean {
  const now = Date.now()
  if (hits.size > 5000) hits.clear() // prevent unbounded growth
  const e = hits.get(ip)
  if (!e || now > e.reset) {
    hits.set(ip, { count: 1, reset: now + WINDOW_MS })
    return false
  }
  e.count++
  return e.count > MAX_PER_WINDOW
}

// Machine endpoints carry their own secrets (INBOUND_SECRET / CRON_SECRET), so
// they're exempt from the dashboard password gate but still rate-limited.
const MACHINE = ['/api/inbound', '/api/cron', '/api/brief']

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  if (pathname.startsWith('/api/')) {
    const ip = (req.headers.get('x-forwarded-for') || '').split(',')[0].trim() || 'unknown'
    if (rateLimited(ip)) {
      return new NextResponse('Too many requests', { status: 429 })
    }
  }

  const pw = process.env.APP_PASSWORD
  if (!pw) return NextResponse.next()
  if (MACHINE.some((p) => pathname.startsWith(p))) return NextResponse.next()

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
