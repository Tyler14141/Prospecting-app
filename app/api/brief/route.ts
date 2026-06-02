import { NextRequest } from 'next/server'
import { listLeads, pendingReviewContent, getInsightsText } from '@/lib/store'
import { LEAD_STAGES } from '@/lib/pipeline'
import { notifyOperator } from '@/lib/email'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// Daily brief — a proactive digest emailed to the operator. Reply "approve 1, 3"
// or "reject 2" (or "approve all") to act on the numbered review items; the
// inbound route applies it. Protect with CRON_SECRET (auto-sent by Vercel Cron).
function authorized(req: NextRequest): boolean {
  const secret = process.env.CRON_SECRET
  if (!secret) return process.env.NODE_ENV !== 'production' // prod: fail closed if unset
  const provided =
    req.headers.get('x-cron-secret') ||
    new URL(req.url).searchParams.get('secret') ||
    (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '')
  return provided === secret
}

async function handle(req: NextRequest) {
  if (!authorized(req)) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  const leads = await listLeads()
  const pending = await pendingReviewContent()
  const insights = await getInsightsText()

  const pipeline = LEAD_STAGES.map((s) => `${s.label}: ${leads.filter((l) => l.stage === s.key).length}`).join(
    ' · ',
  )

  const decisions = pending.length
    ? pending
        .map((c, i) => `${i + 1}. [${c.channel}] ${c.title}${c.to ? ` → ${c.to}` : ''}`)
        .join('\n')
    : '(nothing waiting)'

  const text = [
    'Good morning — here is your Agentic OS brief.',
    '',
    `PIPELINE: ${pipeline}`,
    '',
    `DECISIONS NEEDED (${pending.length} awaiting review):`,
    decisions,
    '',
    insights || '',
    '',
    'Reply to this email to act — e.g. "approve 1 and 3", "reject 2", or "approve all".',
    'Or send any other instruction and the CEO will run it.',
  ]
    .filter((l) => l !== null)
    .join('\n')

  const emailed = await notifyOperator('Agentic OS — daily brief', text)
  return Response.json({ ok: true, pending: pending.length, emailed })
}

export async function GET(req: NextRequest) {
  return handle(req)
}
export async function POST(req: NextRequest) {
  return handle(req)
}
