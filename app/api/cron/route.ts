import { NextRequest } from 'next/server'
import { hasApiKey } from '@/lib/anthropic'
import { getAgent } from '@/lib/agents'
import { WORKFLOWS, getWorkflow } from '@/lib/workflows'
import { runConversation } from '@/lib/agentRunner'
import { addActivity, listContent, listLeads } from '@/lib/store'
import { notifyOperator } from '@/lib/email'

export const runtime = 'nodejs'
export const maxDuration = 300
export const dynamic = 'force-dynamic'

// Scheduled runs. Point a scheduler at this (Vercel Cron via vercel.json, GitHub
// Actions, or any cron that can curl a URL). Runs the workflows listed in
// CRON_WORKFLOWS (comma-separated ids; defaults to scan-leads) and emails the
// operator a digest. Protect with CRON_SECRET (?secret= or x-cron-secret).
function authorized(req: NextRequest): boolean {
  const secret = process.env.CRON_SECRET
  if (!secret) return process.env.NODE_ENV !== 'production' // prod: fail closed if unset // unset = open (dev only)
  const provided =
    req.headers.get('x-cron-secret') ||
    new URL(req.url).searchParams.get('secret') ||
    (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '')
  return provided === secret
}

async function handle(req: NextRequest) {
  if (!authorized(req)) return Response.json({ error: 'Unauthorized' }, { status: 401 })
  if (!hasApiKey()) {
    return Response.json({ error: 'ANTHROPIC_API_KEY is not set on the server.' }, { status: 500 })
  }

  const ids = (process.env.CRON_WORKFLOWS || 'scan-leads')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  const before = {
    reviews: (await listContent()).filter((c) => c.stage === 'review').length,
    leads: (await listLeads()).length,
  }

  const ran: string[] = []
  let tokens = 0
  for (const id of ids) {
    const wf = getWorkflow(id)
    const agent = wf && getAgent(wf.agentId)
    if (!wf || !agent) continue
    try {
      const r = await runConversation(agent, [{ role: 'user', content: wf.prompt }], () => {})
      tokens += r.usage.input + r.usage.output
      ran.push(wf.name)
      await addActivity({ agentId: agent.id, type: 'workflow', message: `Scheduled run: ${wf.name}` })
    } catch {
      await addActivity({ agentId: agent.id, type: 'system', message: `Scheduled run failed: ${wf.name}` })
    }
  }

  const after = {
    reviews: (await listContent()).filter((c) => c.stage === 'review').length,
    leads: (await listLeads()).length,
  }
  const newLeads = Math.max(0, after.leads - before.leads)
  const newReviews = Math.max(0, after.reviews - before.reviews)

  const digest =
    `Scheduled run complete.\n\nWorkflows: ${ran.join(', ') || '(none)'}\n` +
    `New leads: ${newLeads}\nNew drafts awaiting review: ${newReviews}\n` +
    `Drafts pending review (total): ${after.reviews}\n~${tokens} tokens used.`
  const emailed = await notifyOperator('Agentic OS — scheduled run digest', digest)

  return Response.json({ ok: true, ran, newLeads, newReviews, emailed, availableWorkflows: WORKFLOWS.map((w) => w.id) })
}

export async function GET(req: NextRequest) {
  return handle(req)
}
export async function POST(req: NextRequest) {
  return handle(req)
}
