import { NextRequest } from 'next/server'
import { hasApiKey } from '@/lib/anthropic'
import { getAgent } from '@/lib/agents'
import { runConversation } from '@/lib/agentRunner'
import { addActivity, listContent, listLeads, pendingReviewContent, findLeadByEmail } from '@/lib/store'
import { approveContent, rejectContent } from '@/lib/review'
import { sendEmail, notifyOperator, extractEmail } from '@/lib/email'

export const runtime = 'nodejs'
export const maxDuration = 120
export const dynamic = 'force-dynamic'

// Inbound email. Routes three ways:
//   1. Operator reply with "approve/reject N" → applies to the daily brief's
//      numbered review items (reply-to-approve).
//   2. Sender matches a known lead → prospect reply: logged, you're notified,
//      and the AE drafts a suggested response for review (two-way email).
//   3. Otherwise → the CEO runs it as a task.
function authorized(req: NextRequest): boolean {
  const secret = process.env.INBOUND_SECRET
  if (!secret) return true
  const provided =
    req.headers.get('x-inbound-secret') || new URL(req.url).searchParams.get('secret')
  return provided === secret
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function field(p: any, ...keys: string[]): string {
  for (const k of keys) if (p?.[k]) return String(p[k])
  return ''
}

function parseApprovalCommand(body: string): { approve: number[] | 'all'; reject: number[] | 'all' } | null {
  const lower = body.toLowerCase()
  if (!/\b(approve|reject)\b/.test(lower)) return null
  const nums = (re: RegExp): number[] => {
    const m = lower.match(re)
    if (!m) return []
    return (m[1].match(/\d+/g) ?? []).map(Number)
  }
  const approve: number[] | 'all' = /approve\s+all/.test(lower) ? 'all' : nums(/approve([\d,\sand]+)/)
  const reject: number[] | 'all' = /reject\s+all/.test(lower) ? 'all' : nums(/reject([\d,\sand]+)/)
  if (approve === 'all' || reject === 'all' || approve.length || reject.length) return { approve, reject }
  return null
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
  const fromEmail = extractEmail(from).toLowerCase()
  const task = [subject, bodyText].filter(Boolean).join('\n\n').trim()
  if (!task) return Response.json({ error: 'Empty message.' }, { status: 400 })

  const allow = process.env.INBOUND_ALLOWED_FROM
  if (allow) {
    const list = allow.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean)
    // Allowlist gates operator/general senders; known leads are always allowed to reply.
    const isLead = Boolean(await findLeadByEmail(fromEmail))
    if (!isLead && !list.includes(fromEmail)) {
      return Response.json({ error: 'Sender not allowed.' }, { status: 403 })
    }
  }

  const operator = (process.env.OPERATOR_EMAIL || '').toLowerCase()
  const isOperator = operator && fromEmail === operator

  // 1. Operator reply-to-approve.
  if (isOperator) {
    const cmd = parseApprovalCommand(bodyText)
    if (cmd) {
      const pending = await pendingReviewContent()
      const pick = (sel: number[] | 'all') =>
        sel === 'all' ? pending : (sel as number[]).map((n) => pending[n - 1]).filter(Boolean)
      const approved: string[] = []
      const rejected: string[] = []
      for (const item of pick(cmd.approve)) {
        await approveContent(item.id)
        approved.push(item.title)
      }
      for (const item of pick(cmd.reject)) {
        await rejectContent(item.id)
        rejected.push(item.title)
      }
      await addActivity({
        type: 'review',
        message: `Email reply: approved ${approved.length}, rejected ${rejected.length}.`,
      })
      const reply = `Done. Approved: ${approved.join(', ') || 'none'}. Rejected: ${rejected.join(', ') || 'none'}.`
      if (from) await sendEmail({ to: extractEmail(from), subject: 'Re: daily brief', text: reply })
      return Response.json({ ok: true, mode: 'approval', approved: approved.length, rejected: rejected.length })
    }
  }

  // 2. Prospect reply (sender is a known lead, and not the operator).
  const lead = isOperator ? null : await findLeadByEmail(fromEmail)
  if (lead) {
    await addActivity({
      agentId: 'ae',
      type: 'system',
      message: `Reply from ${lead.org}${lead.contact ? ` (${lead.contact})` : ''}: ${subject || bodyText.slice(0, 60)}`,
    })
    await notifyOperator(
      `Prospect reply — ${lead.org}`,
      `${lead.org}${lead.contact ? ` · ${lead.contact}` : ''} replied:\n\n${bodyText}\n\n(The AE is drafting a suggested response for your review.)`,
    )
    if (hasApiKey()) {
      const ae = getAgent('ae')!
      const prompt = `A prospect replied to our outreach. Org: ${lead.org}. Contact: ${lead.contact || 'unknown'} (${lead.title || 'unknown title'}). Their message:\n\n"""${bodyText}"""\n\nDraft a concise, customer-centric reply that addresses their message and moves toward a meeting. Call create_content with channel "Email", to: "${lead.email}", lead_id: "${lead.id}" so it goes to review.`
      try {
        await runConversation(ae, [{ role: 'user', content: prompt }], () => {})
      } catch {
        /* drafting failed; operator was already notified */
      }
    }
    return Response.json({ ok: true, mode: 'prospect_reply', lead: lead.id })
  }

  // 3. Otherwise: run it as a CEO task.
  if (!hasApiKey()) {
    return Response.json({ error: 'ANTHROPIC_API_KEY is not set on the server.' }, { status: 500 })
  }
  const ceo = getAgent('ceo')!
  await addActivity({
    agentId: 'ceo',
    type: 'system',
    message: `Inbound email${from ? ` from ${fromEmail}` : ''}: ${subject || bodyText.slice(0, 60)}`,
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
    return Response.json({ error: err instanceof Error ? err.message : 'Run failed.' }, { status: 500 })
  }

  const after = {
    reviews: (await listContent()).filter((c) => c.stage === 'review').length,
    leads: (await listLeads()).length,
  }
  const newLeads = Math.max(0, after.leads - before.leads)
  const newReviews = Math.max(0, after.reviews - before.reviews)

  const footer = `\n\n—\n${newLeads} new lead(s) and ${newReviews} draft(s) await review in your Agentic OS. Reply "approve 1, 3" to act. ~${usage.input + usage.output} tokens.`
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

  return Response.json({ ok: true, mode: 'ceo', emailed, newLeads, newReviews, reply: replyText })
}
