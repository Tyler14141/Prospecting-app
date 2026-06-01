import { NextRequest } from 'next/server'
import { hasApiKey } from '@/lib/anthropic'
import { getAgent } from '@/lib/agents'
import { runConversation } from '@/lib/agentRunner'
import { addActivity, listContent, listLeads } from '@/lib/store'
import { sendEmail, extractEmail } from '@/lib/email'

export const runtime = 'nodejs'
export const maxDuration = 120
export const dynamic = 'force-dynamic'

// Inbound email → the CEO. Point an email provider's inbound webhook
// (Postmark / SendGrid Inbound Parse / Mailgun route / Cloudflare Email Worker)
// at this endpoint. It accepts the common provider JSON shapes.
//
// Security: set INBOUND_SECRET (checked via ?secret= or x-inbound-secret) and
// optionally INBOUND_ALLOWED_FROM (comma-separated allowlist of sender emails).

function authorized(req: NextRequest): boolean {
  const secret = process.env.INBOUND_SECRET
  if (!secret) return true // unset = open (dev only; set it in production)
  const provided =
    req.headers.get('x-inbound-secret') || new URL(req.url).searchParams.get('secret')
  return provided === secret
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function field(p: any, ...keys: string[]): string {
  for (const k of keys) if (p?.[k]) return String(p[k])
  return ''
}

export async function POST(req: NextRequest) {
  if (!authorized(req)) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let payload: any
  try {
    payload = await req.json()
  } catch {
    return Response.json({ error: 'Expected JSON body.' }, { status: 400 })
  }

  const from = field(payload, 'from', 'sender', 'From', 'FromFull')
  const subject = field(payload, 'subject', 'Subject')
  const bodyText = field(payload, 'text', 'body', 'plain', 'TextBody', 'stripped-text', 'body-plain')
  const task = [subject, bodyText].filter(Boolean).join('\n\n').trim()
  if (!task) return Response.json({ error: 'Empty message.' }, { status: 400 })

  // Optional sender allowlist so strangers can't run (and spend) your agents.
  const allow = process.env.INBOUND_ALLOWED_FROM
  if (allow) {
    const list = allow.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean)
    if (!list.includes(extractEmail(from).toLowerCase())) {
      return Response.json({ error: 'Sender not allowed.' }, { status: 403 })
    }
  }

  if (!hasApiKey()) {
    return Response.json({ error: 'ANTHROPIC_API_KEY is not set on the server.' }, { status: 500 })
  }

  const ceo = getAgent('ceo')!
  await addActivity({
    agentId: 'ceo',
    type: 'system',
    message: `Inbound email${from ? ` from ${extractEmail(from)}` : ''}: ${subject || bodyText.slice(0, 60)}`,
  })

  const before = {
    reviews: (await listContent()).filter((c) => c.stage === 'review').length,
    leads: (await listLeads()).length,
  }

  let buf = ''
  let usage = { input: 0, output: 0 }
  try {
    const r = await runConversation(ceo, [{ role: 'user', content: task }], (s) => {
      buf += s
    })
    usage = r.usage
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? err.message : 'Run failed.' },
      { status: 500 },
    )
  }

  const after = {
    reviews: (await listContent()).filter((c) => c.stage === 'review').length,
    leads: (await listLeads()).length,
  }
  const newLeads = Math.max(0, after.leads - before.leads)
  const newReviews = Math.max(0, after.reviews - before.reviews)

  const footer = `\n\n—\n${newLeads} new lead(s) and ${newReviews} draft(s) are waiting in your Agentic OS (Needs Review). ~${usage.input + usage.output} tokens used.`
  const replyText = (buf.trim() || 'Done.') + footer

  let emailed = false
  if (from) {
    emailed = await sendEmail({
      to: extractEmail(from),
      subject: subject ? `Re: ${subject}` : 'Re: your request',
      text: replyText,
    })
  }
  await addActivity({
    agentId: 'ceo',
    type: 'system',
    message: `Handled inbound email — ${newLeads} leads, ${newReviews} drafts${emailed ? ', replied' : ''}.`,
  })

  return Response.json({ ok: true, emailed, newLeads, newReviews, reply: replyText })
}
